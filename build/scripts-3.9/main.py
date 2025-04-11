import tkinter as tk
from tkinter import ttk, filedialog
import json
from page1 import Page1
import os
from page2 import Page2

def load_api_settings():
    """Load API settings from storage/settings.json."""
    settings_file = os.path.join("storage", "settings.json")
    default_settings = {
        "start_macro_record_shortcut": "r",
        "stop_macro_record_shortcut": "s",
        "start_macro_run_shortcut": "p",
        "stop_macro_run_shortcut": "q"
    }

    # Create storage directory if it doesn’t exist
    os.makedirs("storage", exist_ok=True)

    # Load existing settings or create default ones
    try:
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                settings = json.load(f)
                print(f"Settings loaded from {settings_file}: {settings}")
                return settings
        else:
            with open(settings_file, "w") as f:
                json.dump(default_settings, f, indent=4)
            print(f"Default settings created at {settings_file}: {default_settings}")
            return default_settings
    except Exception as e:
        print(f"Error loading settings: {e}, using default settings")
        return default_settings

class MainApplication(tk.Tk):
    """Main application class for the macro automation tool."""
    def __init__(self):
        super().__init__()
        self.settings = load_api_settings()
        self.title("Modular UI")

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
        self.notebook.add(self.page1, text="Page 1")

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
        """Open the shortcut settings dialog."""
        dialog = tk.Toplevel(self)
        dialog.title("Shortcut Settings")
        dialog.geometry("300x200")

        self.shortcut_entries = {}
        actions = ["start_recording", "stop_recording", "start_macro", "stop_macro"]
        for i, action in enumerate(actions):
            tk.Label(dialog, text=f"{action.replace('_', ' ').title()} Shortcut:").grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(dialog)
            entry.grid(row=i, column=1, padx=5, pady=5)
            default_key = {
                "start_recording": self.settings.get("start_macro_record_shortcut", "r"),
                "stop_recording": self.settings.get("stop_macro_record_shortcut", "s"),
                "start_macro": self.settings.get("start_macro_run_shortcut", "p"),
                "stop_macro": self.settings.get("stop_macro_run_shortcut", "q")
            }[action]
            entry.insert(0, default_key)
            self.shortcut_entries[action] = entry

        tk.Button(dialog, text="Save", command=lambda: self.save_shortcuts(dialog)).grid(row=len(actions), column=0, columnspan=2, pady=10)

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