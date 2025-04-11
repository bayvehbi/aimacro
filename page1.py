import tkinter as tk
from tkinter import ttk, Checkbutton
import os
from monitor_utils import MacroRecorder, ShortcutHandler
import time
from PIL import Image, ImageTk
from draggable_treeview import DraggableTreeview
from ai_stuff import open_ocr_window, open_if_window, open_checkpoint_window, open_pattern_window, open_wait_window

class Page1(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.recording = False
        self.running = False
        self.current_profile = None
        self.run_continuously = tk.BooleanVar(value=False)
        self.variables = {}  # Dictionary to store OCR values
        self.checkpoints = {}  # Dictionary to store checkpoints (name: index)
        self.start_recording_key = master.master.settings.get("start_macro_record_shortcut", "r")
        self.stop_recording_key = master.master.settings.get("stop_macro_record_shortcut", "s")
        self.start_macro_key = master.master.settings.get("start_macro_run_shortcut", "p")
        self.stop_macro_key = master.master.settings.get("stop_macro_run_shortcut", "q")
        self.macro_recorder = MacroRecorder(self)
        self.shortcut_handler = ShortcutHandler(self)
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI elements for Page1."""
        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack(side=tk.TOP, padx=10, pady=5, fill=tk.X)

        # Configure button style
        style = ttk.Style()
        style.configure("Custom.TButton", padding=2)
        style.map("Custom.TButton",
                  background=[("active", "#d9e6f2"), ("disabled", "#cccccc")],
                  foreground=[("active", "#0056b3"), ("disabled", "#666666")])

        # Create icon directory if it doesn’t exist
        icon_dir = os.path.join("storage", "icons")
        os.makedirs(icon_dir, exist_ok=True)
        
        def resize_icon(file_path):
            """Resize an icon image to 12x12 pixels."""
            img = Image.open(file_path)
            img = img.resize((12, 12), Image.LANCZOS)
            return ImageTk.PhotoImage(img)

        self.run_icon = resize_icon(os.path.join(icon_dir, "play.png"))
        self.stop_icon = resize_icon(os.path.join(icon_dir, "stop.png"))
        self.record_icon = resize_icon(os.path.join(icon_dir, "start_rcd.png"))
        self.stop_record_icon = resize_icon(os.path.join(icon_dir, "stop_rcd.png"))
        self.ocr_icon = resize_icon(os.path.join(icon_dir, "ocr.png"))
        self.if_icon = resize_icon(os.path.join(icon_dir, "if.png"))
        self.checkpoint_icon = resize_icon(os.path.join(icon_dir, "checkpoint.png"))
        self.pattern_icon = resize_icon(os.path.join(icon_dir, "pattern.png"))
        self.wait_icon = resize_icon(os.path.join(icon_dir, "wait.png"))

        self.run_button = ttk.Button(button_frame, image=self.run_icon, style="Custom.TButton", command=self.start_macro)
        self.run_button.pack(side=tk.LEFT, padx=5)

        self.stop_run_button = ttk.Button(button_frame, image=self.stop_icon, style="Custom.TButton", command=self.stop_macro, state="disabled")
        self.stop_run_button.pack(side=tk.LEFT, padx=5)

        self.start_button = ttk.Button(button_frame, image=self.record_icon, style="Custom.TButton", command=self.start_recording)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, image=self.stop_record_icon, style="Custom.TButton", command=self.stop_recording, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.ocr_button = ttk.Button(button_frame, image=self.ocr_icon, style="Custom.TButton", command=self.open_ocr_window_wrapper)
        self.ocr_button.pack(side=tk.LEFT, padx=5)

        self.if_button = ttk.Button(button_frame, image=self.if_icon, style="Custom.TButton", command=self.open_if_window_wrapper)
        self.if_button.pack(side=tk.LEFT, padx=5)

        self.checkpoint_button = ttk.Button(button_frame, image=self.checkpoint_icon, style="Custom.TButton", command=self.open_checkpoint_window_wrapper)
        self.checkpoint_button.pack(side=tk.LEFT, padx=5)

        self.pattern_button = ttk.Button(button_frame, image=self.pattern_icon, style="Custom.TButton", command=self.open_pattern_window_wrapper)
        self.pattern_button.pack(side=tk.LEFT, padx=5)

        self.wait_button = ttk.Button(button_frame, image=self.wait_icon, style="Custom.TButton", command=self.open_wait_window_wrapper)
        self.wait_button.pack(side=tk.LEFT, padx=5)

        self.run_continuously_check = Checkbutton(button_frame, text="Run Continuously", variable=self.run_continuously)
        self.run_continuously_check.pack(side=tk.LEFT, padx=5)

        # Set up Treeview frame
        treeview_frame = tk.Frame(self)
        treeview_frame.pack(side=tk.TOP, padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.left_treeview = DraggableTreeview(treeview_frame, accepted_sources=None, allow_drop=True, allow_self_drag=True, height=15)
        scrollbar = ttk.Scrollbar(treeview_frame, orient="vertical", command=self.left_treeview.yview)
        self.left_treeview.configure(yscrollcommand=scrollbar.set)
        self.left_treeview.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        treeview_frame.grid_rowconfigure(0, weight=1)
        treeview_frame.grid_columnconfigure(0, weight=1)

        # Remove empty rows at startup
        for item in self.left_treeview.get_children():
            if not self.left_treeview.item(item, "text").strip():
                self.left_treeview.delete(item)
                print("Empty row removed at startup:", item)
        print("Initial Treeview content:", [self.left_treeview.item(child, "text") for child in self.left_treeview.get_children()])

    def start_macro(self):
        """Start the macro execution."""
        self.macro_recorder.start_macro()
        print("Treeview content before macro starts:", [self.left_treeview.item(child, "text") for child in self.left_treeview.get_children()])

    def open_wait_window_wrapper(self):
        """Open the wait event window."""
        open_wait_window(self, self.add_event_to_treeview)

    def open_pattern_window_wrapper(self):
        """Open the pattern search window."""
        open_pattern_window(self, self.add_event_to_treeview)

    def start_recording(self):
        """Start recording a new macro."""
        self.current_profile = "macro_" + str(int(time.time()))
        self.macro_recorder.start_recording()

    def stop_recording(self):
        """Stop macro recording."""
        self.macro_recorder.stop_recording()

    def stop_macro(self):
        """Stop macro execution."""
        self.macro_recorder.stop_macro()

    def add_event_to_treeview(self, event):
        """Add an event to the Treeview."""
        if not event or not event.strip():
            print("Empty event attempted to be added, skipping.")
            return
        
        # Log Treeview content and remove empty rows before adding
        print("Treeview content before adding:", [self.left_treeview.item(child, "text") for child in self.left_treeview.get_children()])
        for item in self.left_treeview.get_children():
            if not self.left_treeview.item(item, "text").strip():
                self.left_treeview.delete(item)
                print("Empty row removed:", item)
        
        item = self.left_treeview.insert("", tk.END, text=event)
        if "Checkpoint" in event:
            checkpoint_name = event.split("Checkpoint: ")[1]
            self.checkpoints[checkpoint_name] = self.left_treeview.index(item)
            print(f"Checkpoint '{checkpoint_name}' added at index {self.checkpoints[checkpoint_name]}")
        print("Treeview content after adding:", [self.left_treeview.item(child, "text") for child in self.left_treeview.get_children()])

    def open_ocr_window_wrapper(self):
        """Open the OCR event window."""
        open_ocr_window(self, self.add_event_to_treeview, self.variables)

    def open_if_window_wrapper(self):
        """Open the If condition window with updated variables."""
        open_if_window(self, self.add_event_to_treeview, self.variables)

    def open_checkpoint_window_wrapper(self):
        """Open the checkpoint window."""
        open_checkpoint_window(self, self.add_event_to_treeview)

    def get_variable(self, name):
        """Retrieve a variable value by name."""
        return self.variables.get(name, None)

    def get_checkpoint_index(self, name):
        """Retrieve the index of a checkpoint by name."""
        return self.checkpoints.get(name, None)
    
    def open_wait_window_wrapper(self):
        """Open the wait event window (duplicate method, kept for compatibility)."""
        open_wait_window(self, self.add_event_to_treeview)