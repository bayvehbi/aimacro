import tkinter as tk
from tkinter import ttk, filedialog
import json
from aimacro.ui.pages.page1 import Page1
import os
from aimacro.ui.pages.page2 import Page2

from aimacro.config.settings import load_api_settings
from aimacro.utils.logger import init_logger

class MainApplication(tk.Tk):
    """Main application class for the macro automation tool."""
    def __init__(self):
        super().__init__()
        self.settings = load_api_settings()
        # Initialize logger with verbose mode from settings
        init_logger(verbose=self.settings.get("verbose_mode", False))
        self.title("aimacro")

        # Set up the menu bar
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # File menu setup
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New", command=self.new_macro)
        self.file_menu.add_command(label="Save", command=self.save_macro)
        self.file_menu.add_command(label="Load", command=self.load_macro)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # Settings menu setup
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.settings_menu.add_command(label="Shortcut settings", command=self.show_settings_dialog)
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)

        # Initialize notebook for tabbed interface
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.shortcut_entries = {}

        # Create and add Page1 to notebook
        self.page1 = Page1(self.notebook)
        self.notebook.add(self.page1, text="Macro Builder")

        # Create and add Page2 to notebook
        self.page2 = Page2(self.notebook, self.page1)
        self.notebook.add(self.page2, text="Notifications & Variables")

        # Connect Page1 and Page2
        self.page1.page2 = self.page2
        self.page2.setup_ui()  # Set up Page2 UI after Page1 is defined

        # Always on Top checkbox
        self.always_on_top_var = tk.BooleanVar(value=False)
        self.always_on_top_check = tk.Checkbutton(
            self, text="Always on Top", variable=self.always_on_top_var, command=self.toggle_always_on_top
        )
        self.always_on_top_check.pack(side=tk.TOP, padx=5, pady=5)

    def toggle_always_on_top(self):
        """Toggle the Always on Top feature."""
        if self.always_on_top_var.get():
            self.attributes("-topmost", True)
            print("Always on Top enabled")
        else:
            self.attributes("-topmost", False)
            print("Always on Top disabled")

    def show_settings_dialog(self):
        """Show a dialog for editing shortcuts and API keys."""
        dialog = tk.Toplevel(self)
        dialog.title("Shortcut & API Settings")
        dialog.geometry("500x380")
        dialog.attributes("-topmost", True)

        entries = {}
        row = 0

        shortcut_keys = {
            "start_macro_record_shortcut",
            "stop_macro_record_shortcut",
            "start_macro_run_shortcut",
            "stop_macro_run_shortcut",
        }

        settings_keys = [
            ("start_macro_record_shortcut", "Start Macro Record Shortcut"),
            ("stop_macro_record_shortcut", "Stop Macro Record Shortcut"),
            ("start_macro_run_shortcut", "Start Macro Run Shortcut"),
            ("stop_macro_run_shortcut", "Stop Macro Run Shortcut"),
            ("chatgpt_api_key", "OpenAI API Key"),
            ("grok_api_key", "Grok API Key"),
            ("azure_api_key", "Azure API Key"),  # Added Azure API Key setting
            ("azure_endpoint", "Azure Endpoint"),  # Added Azure Endpoint setting
            ("azure_subscription_key", "Azure Subscription Key"),  # Added Azure Subscription Key setting
        ]

        # Map tkinter keysyms to pynput key names for special keys
        KEYSYM_TO_PYNPUT = {
            "prior": "page_up",
            "next": "page_down",
            "home": "home",
            "end": "end",
            "insert": "insert",
            "delete": "delete",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "return": "enter",
            "escape": "esc",
            "tab": "tab",
            "backspace": "backspace",
            "space": "space",
            "f1": "f1", "f2": "f2", "f3": "f3", "f4": "f4",
            "f5": "f5", "f6": "f6", "f7": "f7", "f8": "f8",
            "f9": "f9", "f10": "f10", "f11": "f11", "f12": "f12",
        }

        capturing = [False]

        def start_capture(entry, btn):
            if capturing[0]:
                return
            capturing[0] = True
            btn.config(text="Press key...")
            dialog.focus_set()

            def on_key(event):
                # Ignore standalone modifier key presses
                if event.keysym in ('Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Shift_L', 'Shift_R', 'Super_L', 'Super_R'):
                    return
                dialog.unbind("<KeyPress>")
                capturing[0] = False
                ctrl = bool(event.state & 0x4)
                sym = event.keysym.lower()
                if event.char and event.char.isprintable() and len(event.char) == 1:
                    char = event.char
                else:
                    char = KEYSYM_TO_PYNPUT.get(sym, sym)
                shortcut = f"ctrl+{char}" if ctrl else char
                entry.delete(0, tk.END)
                entry.insert(0, shortcut)
                btn.config(text="Capture")

            dialog.bind("<KeyPress>", on_key)

        for key, label in settings_keys:
            tk.Label(dialog, text=label + ":").grid(row=row, column=0, sticky="e", padx=5, pady=5)

            entry = tk.Entry(dialog, width=25, show="")
            entry.insert(0, self.settings.get(key, ""))
            entry.grid(row=row, column=1, padx=5, pady=5)
            entries[key] = entry

            if key in shortcut_keys:
                btn = tk.Button(dialog, text="Capture", width=10)
                btn.grid(row=row, column=2, padx=5, pady=5)
                btn.config(command=lambda e=entry, b=btn: start_capture(e, b))

            row += 1

        # Add verbose mode checkbox
        verbose_var = tk.BooleanVar(value=self.settings.get("verbose_mode", False))
        verbose_check = tk.Checkbutton(dialog, text="Verbose Mode (Enable debug logging)", variable=verbose_var)
        verbose_check.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        row += 1

        def save_and_close():
            for key, entry in entries.items():
                self.settings[key] = entry.get().strip()
            # Save verbose mode
            self.settings["verbose_mode"] = verbose_var.get()
            # Update logger
            from aimacro.utils.logger import get_logger
            get_logger().set_verbose(self.settings["verbose_mode"])
            with open(os.path.join("storage", "settings.json"), "w") as f:
                json.dump(self.settings, f, indent=4)
            # Apply shortcut keys immediately to page1
            self.page1.start_recording_key = self.settings.get("start_macro_record_shortcut", "r")
            self.page1.stop_recording_key = self.settings.get("stop_macro_record_shortcut", "s")
            self.page1.start_macro_key = self.settings.get("start_macro_run_shortcut", "p")
            self.page1.stop_macro_key = self.settings.get("stop_macro_run_shortcut", "q")
            print("Settings saved.")
            dialog.destroy()

        tk.Button(dialog, text="Save", command=save_and_close).grid(row=row, column=0, columnspan=2, pady=15)
        


    def save_shortcuts(self, dialog):
        """Save shortcut settings and apply them to Page1."""
        for action, entry in self.shortcut_entries.items():
            key = entry.get().strip()
            if key:
                self.settings[f"{action.replace('_', '_macro_')}_shortcut"] = key
                setattr(self.page1, f"{action}_key", key)
        dialog.destroy()

    def new_macro(self):
        """Create a new macro, clearing Treeview, variables, and notifications."""
        self.page1.left_treeview.delete(*self.page1.left_treeview.get_children())
        self.page1.variables.clear()
        self.page1.checkpoints.clear()
        self.page2.notifications.clear()
        print("New macro created, Treeview and variables cleared")

    def save_macro(self):
        """Save the macro and its data to a file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            data = {
                "events": [self.page1.left_treeview.item(child, "text") for child in self.page1.left_treeview.get_children()],
                "variables": self.page1.variables,
                "checkpoints": self.page1.checkpoints,
                "notifications": self.page2.notifications
            }
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Macro saved to {file_path}")
            # Save settings to storage/settings.json
            with open(os.path.join("storage", "settings.json"), "w") as f:
                json.dump(self.settings, f, indent=4)

    def load_macro(self):
        """Load a macro and its data from a file."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            self.page1.left_treeview.delete(*self.page1.left_treeview.get_children())
            for event in data["events"]:
                self.page1.add_event_to_treeview(event)
            
            self.page1.variables.clear()
            self.page1.variables.update(data["variables"])
            
            self.page1.checkpoints.clear()
            self.page1.checkpoints.update(data["checkpoints"])
            self.page2.notifications.clear()
            self.page2.notifications.update(data.get("notifications", {}))
            self.page2.update_notifications_list()
            print(f"Loaded notifications: {self.page2.notifications}")
            print(f"Macro loaded from {file_path}")
            print(f"Loaded variables: {self.page1.variables}")
            print(f"Loaded checkpoints: {self.page1.checkpoints}")

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()