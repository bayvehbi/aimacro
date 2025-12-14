"""
Checkpoint dialog for adding checkpoint events to macros.
"""
import tkinter as tk
from tkinter import Toplevel, Entry, Label, Button


def open_checkpoint_window(parent, coords_callback):
    """Open the checkpoint settings window."""
    checkpoint_window = Toplevel(parent)
    checkpoint_window.title("Add Checkpoint")
    
    screen_width = checkpoint_window.winfo_screenwidth()
    screen_height = checkpoint_window.winfo_screenheight()
    window_width = int(screen_width * 0.3)
    window_height = int(screen_height * 0.2)
    checkpoint_window.geometry(f"{window_width}x{window_height}")
    checkpoint_window.attributes("-topmost", True)

    Label(checkpoint_window, text="Checkpoint Name:").pack(pady=5)
    name_entry = Entry(checkpoint_window)
    name_entry.pack(pady=5)

    def save_checkpoint():
        """Save the checkpoint event."""
        name = name_entry.get().strip()
        if name:
            event = f"Checkpoint: {name}"
            coords_callback(event)
            print(f"Added Checkpoint: {name}")
        checkpoint_window.destroy()

    Button(checkpoint_window, text="OK", command=save_checkpoint).pack(pady=10)

