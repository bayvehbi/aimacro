import tkinter as tk
from tkinter import Toplevel, Entry, Label, Button, ttk
import pyautogui
import base64
from io import BytesIO
from PIL import Image, ImageTk
from misc import send_to_grok_ocr
import traceback
from pynput import keyboard, mouse

class RegionCapture:
    def __init__(self):
        self.coords = []
        self.listener = keyboard.Listener(on_press=self.on_key)
        self.mouse_controller = mouse.Controller()

    def on_key(self, key):
        if key == keyboard.Key.f8:
            pos = self.mouse_controller.position
            print(f"📌 Point recorded: {pos}")
            self.coords.append(pos)
            if len(self.coords) == 2:
                self.listener.stop()

    def capture(self):
        print("⌨️  Press F8 twice to define region...")
        self.listener.start()
        self.listener.join()

        (x1, y1), (x2, y2) = self.coords
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        width = x2 - x1
        height = y2 - y1

        print(f"📸 Capturing region: ({x1}, {y1}, {width}, {height})")
        img = pyautogui.screenshot(region=(x1, y1, width, height))
        return img, {"start": (x1, y1), "end": (x2, y2)}


def open_ocr_window(parent, coords_callback, variables):
    """Open the OCR settings window."""
    ocr_window = Toplevel(parent)
    ocr_window.title("OCR Settings")
    screen_width = ocr_window.winfo_screenwidth()
    screen_height = ocr_window.winfo_screenheight()
    window_width = int(screen_width * 0.4)
    window_height = int(screen_height * 0.4)
    ocr_window.geometry(f"{window_width}x{window_height}")
    ocr_window.attributes("-topmost", True)

    Label(ocr_window, text="Define OCR Area").pack(pady=5)
    preview_label = Label(ocr_window, text="No area selected yet")
    Button(ocr_window, text="Select Area (F8 x2)", command=lambda: start_ocr_selection_f8(ocr_window, preview_label)).pack(pady=5)
    preview_label.pack(pady=5)

    Label(ocr_window, text="Wait Time (seconds):").pack(pady=5)
    wait_time_entry = Entry(ocr_window)
    wait_time_entry.insert(0, "5")
    wait_time_entry.pack(pady=5)

    Label(ocr_window, text="Variable Name:").pack(pady=5)
    variable_entry = Entry(ocr_window)
    variable_entry.pack(pady=5)

    Button(ocr_window, text="OK", command=lambda: save_ocr_event(ocr_window, wait_time_entry, variable_entry, coords_callback, variables)).pack(pady=10)


def start_ocr_selection_f8(ocr_window, preview_label):
    """Use F8RegionCapture to select OCR area."""
    capture_tool = RegionCapture()
    img, coords = capture_tool.capture()
    update_ocr_preview(img, preview_label)
    ocr_window.coords = coords


def update_ocr_preview(img, preview_label):
    """Update the preview of the selected OCR area."""
    screenshot = img.resize((300, 200), Image.LANCZOS)
    preview_image = ImageTk.PhotoImage(screenshot)
    preview_label.config(image=preview_image, text="")
    preview_label.image = preview_image


def save_ocr_event(window, wait_time_entry, variable_entry, coords_callback, variables):
    """Save the OCR event without processing it immediately."""
    try:
        wait_time = float(wait_time_entry.get())
        variable_name = variable_entry.get().strip()
        if hasattr(window, 'coords'):
            coords = window.coords
            event = f"OCR Search - Area: {coords}, Wait: {wait_time}s, Variable: {variable_name}"
            coords_callback(event)
            print(f"✅ Added OCR event: {event}")
        window.destroy()
    except ValueError:
        print("❌ Invalid wait time, please enter a number")
        
def open_if_window(parent, coords_callback, variables):
    """Open the If condition settings window."""
    if_window = Toplevel(parent)
    if_window.title("If Condition")
    
    screen_width = if_window.winfo_screenwidth()
    screen_height = if_window.winfo_screenheight()
    window_width = int(screen_width * 0.4)
    window_height = int(screen_height * 0.5)
    if_window.geometry(f"{window_width}x{window_height}")
    if_window.attributes("-topmost", True)

    Label(if_window, text="Define If Condition").pack(pady=5)

    Label(if_window, text="Select Variable:").pack(pady=5)
    variable_names = list(variables.keys()) if variables else ["None"]
    print(f"Available variables for If: {variable_names}")
    variable_dropdown = ttk.Combobox(if_window, values=variable_names, state="readonly")
    variable_dropdown.set(variable_names[0])
    variable_dropdown.pack(pady=5)

    Label(if_window, text="Condition:").pack(pady=5)
    condition_dropdown = ttk.Combobox(if_window, values=["==", ">", "<", ">=", "<=", "!=", "Contains"], state="readonly")
    condition_dropdown.set("==")
    condition_dropdown.pack(pady=5)

    Label(if_window, text="Value (string or number):").pack(pady=5)
    value_entry = Entry(if_window)
    value_entry.pack(pady=5)

    # Succeed section: Label above, Checkbox, Checkpoint, Notification side by side
    Label(if_window, text="If Succeed, Go To:").pack(pady=5)
    succeed_frame = tk.Frame(if_window)
    succeed_frame.pack(pady=5)
    succeed_send_var = tk.BooleanVar(value=False)
    succeed_check = tk.Checkbutton(succeed_frame, text="Send Notification", variable=succeed_send_var, command=lambda: toggle_notification('succeed'))
    succeed_check.grid(row=0, column=0, padx=5)
    succeed_checkpoint_dropdown = ttk.Combobox(succeed_frame, values=["Next"] + list(parent.checkpoints.keys()), state="readonly")
    succeed_checkpoint_dropdown.set("Next")
    succeed_checkpoint_dropdown.grid(row=0, column=1, padx=5)
    succeed_notification_dropdown = ttk.Combobox(succeed_frame, values=["None"] + list(parent.master.master.page2.notifications.keys()), state="disabled")
    succeed_notification_dropdown.set("None")
    succeed_notification_dropdown.grid(row=0, column=2, padx=5)
    succeed_frame.grid_columnconfigure(0, weight=1)
    succeed_frame.grid_columnconfigure(1, weight=1)
    succeed_frame.grid_columnconfigure(2, weight=1)

    # Fail section: Label above, Checkbox, Checkpoint, Notification side by side
    Label(if_window, text="If Failed, Go To:").pack(pady=5)
    fail_frame = tk.Frame(if_window)
    fail_frame.pack(pady=5)
    fail_send_var = tk.BooleanVar(value=False)
    fail_check = tk.Checkbutton(fail_frame, text="Send Notification", variable=fail_send_var, command=lambda: toggle_notification('fail'))
    fail_check.grid(row=0, column=0, padx=5)
    fail_checkpoint_dropdown = ttk.Combobox(fail_frame, values=["Next"] + list(parent.checkpoints.keys()), state="readonly")
    fail_checkpoint_dropdown.set("Next")
    fail_checkpoint_dropdown.grid(row=0, column=1, padx=5)
    fail_notification_dropdown = ttk.Combobox(fail_frame, values=["None"] + list(parent.master.master.page2.notifications.keys()), state="disabled")
    fail_notification_dropdown.set("None")
    fail_notification_dropdown.grid(row=0, column=2, padx=5)
    fail_frame.grid_columnconfigure(0, weight=1)
    fail_frame.grid_columnconfigure(1, weight=1)
    fail_frame.grid_columnconfigure(2, weight=1)

    Label(if_window, text="Wait Time if Failed (seconds):").pack(pady=5)
    wait_time_entry = Entry(if_window)
    wait_time_entry.insert(0, "5")
    wait_time_entry.pack(pady=5)

    def toggle_notification(mode):
        """Toggle the notification dropdown state."""
        if mode == 'succeed' and succeed_send_var.get():
            succeed_notification_dropdown.config(state="readonly")
        elif mode == 'succeed':
            succeed_notification_dropdown.config(state="disabled")
        elif mode == 'fail' and fail_send_var.get():
            fail_notification_dropdown.config(state="readonly")
        elif mode == 'fail':
            fail_notification_dropdown.config(state="disabled")

    def save_if_event():
        """Save the If condition event."""
        try:
            variable_name = variable_dropdown.get()
            condition = condition_dropdown.get()
            value = value_entry.get().strip()
            succeed_checkpoint = succeed_checkpoint_dropdown.get()
            fail_checkpoint = fail_checkpoint_dropdown.get()
            succeed_send = succeed_send_var.get()
            succeed_notification = succeed_notification_dropdown.get()
            fail_send = fail_send_var.get()
            fail_notification = fail_notification_dropdown.get()
            wait_time = float(wait_time_entry.get())

            if variable_name == "None":
                print("No variable selected, cannot create If condition.")
                if_window.destroy()
                return

            event = f"If {variable_name} {condition} {value}, Succeed Go To: {succeed_checkpoint}, Fail Go To: {fail_checkpoint}, Wait: {wait_time}s"
            if succeed_send and succeed_notification != "None":
                event += f", Succeed Notification: {succeed_notification}"
            if fail_send and fail_notification != "None":
                event += f", Fail Notification: {fail_notification}"
            
            coords_callback(event)
            print(f"Added If event: {event}")
            if_window.destroy()
        except ValueError:
            print("Invalid wait time, please enter a number")
        except Exception as e:
            print(f"Error saving if event: {type(e).__name__}: {e}")

    Button(if_window, text="OK", command=save_if_event).pack(pady=10)

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

def update_pattern_preview(coords, preview_label):
    """Update the preview of the selected pattern area."""
    x1, y1 = coords["start"]
    x2, y2 = coords["end"]
    width, height = x2 - x1, y2 - y1
    screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
    screenshot = screenshot.resize((300, 200), Image.LANCZOS)
    preview_image = ImageTk.PhotoImage(screenshot)
    preview_label.config(image=preview_image, text="")
    preview_label.image = preview_image

def open_pattern_window(parent, coords_callback):
    """Open the pattern search settings window."""
    pattern_window = Toplevel(parent)
    pattern_window.title("Search for Pattern")
    
    screen_width = pattern_window.winfo_screenwidth()
    screen_height = pattern_window.winfo_screenheight()
    window_width = int(screen_width * 0.4)
    window_height = int(screen_height * 0.5)
    pattern_window.geometry(f"{window_width}x{window_height}")
    pattern_window.attributes("-topmost", True)

    Label(pattern_window, text="Define Search Area").pack(pady=5)
    search_preview_label = Label(pattern_window, text="No search area selected yet (default: full screen)")
    Button(pattern_window, text="Select Search Area", command=lambda: start_search_area_selection(pattern_window, search_preview_label)).pack(pady=5)
    search_preview_label.pack(pady=5)

    Label(pattern_window, text="Define Pattern to Search").pack(pady=5)
    pattern_preview_label = Label(pattern_window, text="No pattern selected yet")
    Button(pattern_window, text="Select Pattern", command=lambda: start_pattern_selection(pattern_window, pattern_preview_label)).pack(pady=5)
    pattern_preview_label.pack(pady=5)

    # Succeed section: Label above, Checkbox, Checkpoint, Notification side by side
    Label(pattern_window, text="If Found, Succeed Go To:").pack(pady=5)
    succeed_frame = tk.Frame(pattern_window)
    succeed_frame.pack(pady=5)
    succeed_send_var = tk.BooleanVar(value=False)
    succeed_check = tk.Checkbutton(succeed_frame, text="Send Notification", variable=succeed_send_var, command=lambda: toggle_notification('succeed'))
    succeed_check.grid(row=0, column=0, padx=5)
    succeed_checkpoint_dropdown = ttk.Combobox(succeed_frame, values=["Next"] + list(parent.checkpoints.keys()), state="readonly")
    succeed_checkpoint_dropdown.set("Next")
    succeed_checkpoint_dropdown.grid(row=0, column=1, padx=5)
    succeed_notification_dropdown = ttk.Combobox(succeed_frame, values=["None"] + list(parent.master.master.page2.notifications.keys()), state="disabled")
    succeed_notification_dropdown.set("None")
    succeed_notification_dropdown.grid(row=0, column=2, padx=5)
    succeed_frame.grid_columnconfigure(0, weight=1)
    succeed_frame.grid_columnconfigure(1, weight=1)
    succeed_frame.grid_columnconfigure(2, weight=1)

    # Fail section: Label above, Checkbox, Checkpoint, Notification side by side
    Label(pattern_window, text="If Not Found, Fail Go To:").pack(pady=5)
    fail_frame = tk.Frame(pattern_window)
    fail_frame.pack(pady=5)
    fail_send_var = tk.BooleanVar(value=False)
    fail_check = tk.Checkbutton(fail_frame, text="Send Notification", variable=fail_send_var, command=lambda: toggle_notification('fail'))
    fail_check.grid(row=0, column=0, padx=5)
    fail_checkpoint_dropdown = ttk.Combobox(fail_frame, values=["Next"] + list(parent.checkpoints.keys()), state="readonly")
    fail_checkpoint_dropdown.set("Next")
    fail_checkpoint_dropdown.grid(row=0, column=1, padx=5)
    fail_notification_dropdown = ttk.Combobox(fail_frame, values=["None"] + list(parent.master.master.page2.notifications.keys()), state="disabled")
    fail_notification_dropdown.set("None")
    fail_notification_dropdown.grid(row=0, column=2, padx=5)
    fail_frame.grid_columnconfigure(0, weight=1)
    fail_frame.grid_columnconfigure(1, weight=1)
    fail_frame.grid_columnconfigure(2, weight=1)

    Label(pattern_window, text="Click if Found:").pack(pady=5)
    click_var = tk.BooleanVar(value=False)
    tk.Checkbutton(pattern_window, text="Click if Found", variable=click_var).pack(pady=5)

    Label(pattern_window, text="Wait Time (seconds):").pack(pady=5)
    wait_time_entry = Entry(pattern_window)
    wait_time_entry.insert(0, "5")
    wait_time_entry.pack(pady=5)

    Label(pattern_window, text="Threshold:").pack(pady=5)
    threshold_entry = Entry(pattern_window)
    threshold_entry.insert(0, "0.7")
    threshold_entry.pack(pady=5)

    def toggle_notification(mode):
        """Toggle the notification dropdown state."""
        if mode == 'succeed' and succeed_send_var.get():
            succeed_notification_dropdown.config(state="readonly")
        elif mode == 'succeed':
            succeed_notification_dropdown.config(state="disabled")
        elif mode == 'fail' and fail_send_var.get():
            fail_notification_dropdown.config(state="readonly")
        elif mode == 'fail':
            fail_notification_dropdown.config(state="disabled")

    def save_pattern_event():
        """Save the pattern search event."""
        try:
            wait_time = float(wait_time_entry.get())
            succeed_checkpoint = succeed_checkpoint_dropdown.get()
            fail_checkpoint = fail_checkpoint_dropdown.get()
            click_if_found = click_var.get()
            threshold = float(threshold_entry.get())

            if not hasattr(pattern_window, 'pattern_coords') or pattern_window.pattern_coords is None:
                print("Error: No pattern area selected or pattern_coords is None")
                pattern_window.destroy()
                return

            pattern_coords = pattern_window.pattern_coords
            x1, y1 = pattern_coords["start"]
            x2, y2 = pattern_coords["end"]
            if x2 <= x1 or y2 <= y1:
                print(f"Error: Invalid pattern coordinates - start: ({x1}, {y1}), end: ({x2}, {y2})")
                pattern_window.destroy()
                return

            screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            search_coords = getattr(pattern_window, 'search_coords', None)
            event = f"Search Pattern - Image: {img_str}, Search Area: {search_coords or 'Full Screen'}, Succeed Go To: {succeed_checkpoint}, Fail Go To: {fail_checkpoint}, Click: {click_if_found}, Wait: {wait_time}s, Threshold: {threshold}"
            if succeed_send_var.get() and succeed_notification_dropdown.get() != "None":
                event += f", Succeed Notification: {succeed_notification_dropdown.get()}"
            if fail_send_var.get() and fail_notification_dropdown.get() != "None":
                event += f", Fail Notification: {fail_notification_dropdown.get()}"
            
            coords_callback(event)
            print(f"Added Pattern event: {event}")
            pattern_window.destroy()

        except ValueError as e:
            print(f"Invalid input: {e}. Please enter valid numbers for wait time and threshold.")
        except Exception as e:
            print(f"Error saving pattern event: {type(e).__name__}: {e}")
            traceback.print_exc()
            pattern_window.destroy()

    Button(pattern_window, text="OK", command=save_pattern_event).pack(pady=10)
    
def start_pattern_selection(pattern_window, preview_label):
    """Enable pattern area selection using F8 keys."""
    capture_tool = RegionCapture()
    img, coords = capture_tool.capture()
    update_pattern_preview_image(img, preview_label)
    pattern_window.pattern_coords = coords
    print(f"Set pattern_window.pattern_coords: {coords}")


def start_search_area_selection(pattern_window, preview_label):
    """Enable search area selection using F8 keys."""
    capture_tool = RegionCapture()
    img, coords = capture_tool.capture()
    update_pattern_preview_image(img, preview_label)
    pattern_window.search_coords = coords
    print(f"Set pattern_window.search_coords: {coords}")

def update_pattern_preview_image(img, preview_label):
    """Update the preview label with an image."""
    resized = img.resize((300, 200), Image.LANCZOS)
    preview_image = ImageTk.PhotoImage(resized)
    preview_label.config(image=preview_image, text="")
    preview_label.image = preview_image

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