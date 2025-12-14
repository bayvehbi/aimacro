"""
Wait dialog for adding wait events to macros.
"""
import tkinter as tk
from tkinter import Toplevel, Entry, Label, Button


def open_wait_window(parent, coords_callback):
    """Open the wait event settings window."""
    wait_window = tk.Toplevel(parent)
    wait_window.title("Add Wait")
    
    screen_width = wait_window.winfo_screenwidth()
    screen_height = wait_window.winfo_screenheight()
    window_width = int(screen_width * 0.2)
    window_height = int(screen_height * 0.15)
    wait_window.geometry(f"{window_width}x{window_height}")
    wait_window.attributes("-topmost", True)

    tk.Label(wait_window, text="Wait Time (seconds):").pack(pady=5)
    wait_time_entry = tk.Entry(wait_window)
    wait_time_entry.insert(0, "1.0")  # Default value of 1 second
    wait_time_entry.pack(pady=5)

    def save_wait_event():
        """Save the wait event."""
        try:
            wait_time = float(wait_time_entry.get())
            if wait_time < 0:
                print("Wait time cannot be negative.")
                return
            event = f"Wait: {wait_time}s"
            coords_callback(event)
            print(f"Added Wait event: {event}")
            wait_window.destroy()
        except ValueError:
            print("Invalid wait time, please enter a number.")

    tk.Button(wait_window, text="OK", command=save_wait_event).pack(pady=10)

