import tkinter as tk
from tkinter import Toplevel, Entry, Label, Button, ttk
import pyautogui
import base64
from io import BytesIO
from PIL import Image, ImageTk
import traceback
from pynput import keyboard, mouse

class RegionCapture:
    def __init__(self):
        self.coords = []
        self.listener = keyboard.Listener(on_press=self.on_key)

    def on_key(self, key):
        if key == keyboard.Key.f8:
            pos = pyautogui.position()
            print(f"Point recorded: {pos}")
            self.coords.append(pos)
            if len(self.coords) == 2:
                self.listener.stop()

    def capture(self):
        print("Press F8 twice to define region...")
        self.listener.start()
        self.listener.join()

        (x1, y1), (x2, y2) = self.coords
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        width = x2 - x1
        height = y2 - y1

        print(f"Capturing region: ({x1}, {y1}, {width}, {height})")
        img = pyautogui.screenshot(region=(x1, y1, width, height))
        return img, {"start": (x1, y1), "end": (x2, y2)}
        
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

    
def update_pattern_preview_image(img, preview_label):
    resized = img.resize((300, 200), Image.LANCZOS)
    preview_image = ImageTk.PhotoImage(resized)
    preview_label.config(image=preview_image, text="")
    preview_label.image = preview_image

def update_image_from_coords(window, coords, label, target):
    if not coords:
        print(f"No coordinates for {target}")
        return
    import ast
    if isinstance(coords, str):
        coords = ast.literal_eval(coords)
    x1, y1 = coords["start"]
    x2, y2 = coords["end"]
    if x2 <= x1 or y2 <= y1:
        print("Invalid coordinates")
        return
    screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
    buffered = BytesIO()
    screenshot.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    update_pattern_preview_image(screenshot, label)
    setattr(window, f"{target}_coords", coords)
    setattr(window, f"{target}_image_base64", img_str)
    print(f"{target.title()} image updated.")


def select_area(window, label, target):
    capture_tool = RegionCapture()
    img, coords = capture_tool.capture()
    update_image_from_coords(window, coords, label, target)


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