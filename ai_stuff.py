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


def open_ocr_window(parent, coords_callback, variables, edit_mode=False, initial_values=None):
    ocr_window = Toplevel(parent)
    ocr_window.title("OCR Settings")
    screen_width = ocr_window.winfo_screenwidth()
    screen_height = ocr_window.winfo_screenheight()
    window_width = int(screen_width * 0.4)
    window_height = int(screen_height * 0.4)
    ocr_window.geometry(f"{window_width}x{window_height}")
    ocr_window.attributes("-topmost", True)

    tk.Label(ocr_window, text="Define OCR Area").pack(pady=5)
    preview_label = tk.Label(ocr_window, text="No area selected yet")
    tk.Button(ocr_window, text="Select Area", command=lambda: select_area(ocr_window, preview_label, "ocr")).pack(pady=5)
    preview_label.pack(pady=5)

    tk.Label(ocr_window, text="Define OCR content").pack(pady=5)
    variable_message = tk.Entry(ocr_window)
    variable_message.pack(pady=5)

    tk.Label(ocr_window, text="Wait Time (seconds):").pack(pady=5)
    wait_time_entry = tk.Entry(ocr_window)
    wait_time_entry.insert(0, "5")
    wait_time_entry.pack(pady=5)

    tk.Label(ocr_window, text="Variable Name:").pack(pady=5)
    variable_entry = tk.Entry(ocr_window)
    variable_entry.pack(pady=5)

    if edit_mode and initial_values:
        preview_label.config(text=f"Selected: {initial_values['coords']}")
        try:
            # Allow passing either a tuple or a string representation
            ocr_window.ocr_coords = (
                initial_values["coords"]
                if isinstance(initial_values["coords"], tuple)
                else eval(initial_values["coords"])
            )
        except Exception as e:
            print(f"Failed to parse coords: {e}")
            ocr_window.ocr_coords = (0, 0, 0, 0)

        wait_time_entry.delete(0, tk.END)
        wait_time_entry.insert(0, str(initial_values["wait_time"]))

        variable_entry.delete(0, tk.END)
        variable_entry.insert(0, initial_values["variable_name"])

        variable_message.delete(0, tk.END)
        variable_message.insert(0, initial_values["variable_content"])

    def save_ocr_event():
        try:
            wait_time = float(wait_time_entry.get())
            variable_name = variable_entry.get().strip()
            variable_content = variable_message.get()

            if not variable_name:
                print("Variable name cannot be empty!")
                tk.messagebox.showerror("Missing Variable Name", "Please provide a variable name before saving.")
                return

            if not hasattr(ocr_window, 'ocr_coords'):
                print("No OCR area selected.")
                tk.messagebox.showerror("Missing Area", "Please select an OCR area first.")
                return

            coords = ocr_window.ocr_coords
            event = f"OCR Search - Area: {coords}, Wait: {wait_time}s, Variable: {variable_name}, Variable Content: {variable_content}"
            values = (coords, wait_time, variable_name, variable_content)

            if edit_mode and initial_values and "item_id" in initial_values:
                coords_callback(event, item_id=initial_values["item_id"], values=values)
            else:
                coords_callback(event, values=values)

            print(f"{'Updated' if edit_mode else 'Added'} OCR event: {event}")
            ocr_window.destroy()

        except ValueError:
            print("Invalid wait time, please enter a number")
            tk.messagebox.showerror("Invalid Input", "Please enter a valid number for wait time.")

    tk.Button(ocr_window, text="OK", command=save_ocr_event).pack(pady=10)

        
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
    time_variables = ["time_hour", "time_minute", "time_second", "time_weekday", "time_day", "time_month", "time_year"]
    variable_names = time_variables + list(variables.keys())
    print(f"Available variables for If: {variable_names}")
    variable_dropdown = ttk.Combobox(if_window, values=variable_names, state="readonly")
    variable_dropdown.set(variable_names[0])
    variable_dropdown.pack(pady=5)

    Label(if_window, text="Condition:").pack(pady=5)
    condition_dropdown = ttk.Combobox(if_window, values=["==", ">", "<", ">=", "<=", "!=", "Contains", "%"], state="readonly")
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


def open_pattern_window(parent, coords_callback):
    from functools import partial
    import base64
    from PIL import Image, ImageTk
    import io
    import ast

    def toggle_notification(mode):
        dropdown = succeed_notification_dropdown if mode == 'succeed' else fail_notification_dropdown
        var = succeed_send_var if mode == 'succeed' else fail_send_var
        dropdown.config(state="readonly" if var.get() else "disabled")

    def on_copy_search_to_pattern():
        if copy_to_pattern.get() and pattern_window.search_coords:
            update_image_from_coords(pattern_window, pattern_window.search_coords, pattern_preview_label, "pattern")
            threshold_entry.delete(0, tk.END)
            threshold_entry.insert(0, "0.99")

    def render_image(label, image_base64):
        try:
            decoded_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(decoded_data))
            image.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(image)
            label.config(image=photo)
            label.image = photo
        except Exception as e:
            print("Failed to render image:", e)

    def restore_previous_images():
        if pattern_window.pattern_image_base64:
            render_image(pattern_preview_label, pattern_window.pattern_image_base64)
        if pattern_window.search_image_base64:
            render_image(search_preview_label, pattern_window.search_image_base64)

    pattern_window = Toplevel(parent)
    pattern_window.title("Search for Pattern")

    pattern_window.pattern_coords = None
    pattern_window.search_coords = None
    pattern_window.pattern_image_base64 = None
    pattern_window.search_image_base64 = None

    screen_width = pattern_window.winfo_screenwidth()
    screen_height = pattern_window.winfo_screenheight()
    window_width = int(screen_width * 0.4)
    pattern_window.geometry(f"{window_width}x{screen_height}")
    pattern_window.attributes("-topmost", True)

    Label(pattern_window, text="Define Search Area").pack(pady=5)
    search_preview_label = Label(pattern_window, text="No search area selected yet")
    Button(pattern_window, text="Select Search Area", command=partial(select_area, pattern_window, search_preview_label, "search")).pack(pady=5)
    search_preview_label.pack(pady=5)

    pattern_preview_label = Label(pattern_window, text="No pattern selected yet")
    Button(pattern_window, text="Select Pattern", command=partial(select_area, pattern_window, pattern_preview_label, "pattern")).pack(pady=5)
    Button(pattern_window, text="Recapture Pattern Image", command=lambda: update_image_from_coords(pattern_window, pattern_window.pattern_coords, pattern_preview_label, "pattern")).pack(pady=5)
    pattern_preview_label.pack(pady=5)

    copy_to_pattern = tk.BooleanVar()
    tk.Checkbutton(pattern_window, text="Copy search to pattern", variable=copy_to_pattern, command=on_copy_search_to_pattern).pack(pady=5)

    Label(pattern_window, text="If Found, Succeed Go To:").pack(pady=5)
    succeed_frame = tk.Frame(pattern_window)
    succeed_frame.pack(pady=5)
    succeed_send_var = tk.BooleanVar()
    tk.Checkbutton(succeed_frame, text="Send Notification", variable=succeed_send_var, command=lambda: toggle_notification('succeed')).grid(row=0, column=0, padx=5)
    succeed_checkpoint_dropdown = ttk.Combobox(succeed_frame, values=["Next", "Wait"] + list(parent.checkpoints.keys()), state="readonly")
    succeed_checkpoint_dropdown.set("Next")
    succeed_checkpoint_dropdown.grid(row=0, column=1, padx=5)
    succeed_notification_dropdown = ttk.Combobox(succeed_frame, values=["None"] + list(parent.master.master.page2.notifications.keys()), state="disabled")
    succeed_notification_dropdown.set("None")
    succeed_notification_dropdown.grid(row=0, column=2, padx=5)

    Label(pattern_window, text="If Not Found, Fail Go To:").pack(pady=5)
    fail_frame = tk.Frame(pattern_window)
    fail_frame.pack(pady=5)
    fail_send_var = tk.BooleanVar()
    tk.Checkbutton(fail_frame, text="Send Notification", variable=fail_send_var, command=lambda: toggle_notification('fail')).grid(row=0, column=0, padx=5)
    fail_checkpoint_dropdown = ttk.Combobox(fail_frame, values=["Next", "Wait"] + list(parent.checkpoints.keys()), state="readonly")
    fail_checkpoint_dropdown.set("Next")
    fail_checkpoint_dropdown.grid(row=0, column=1, padx=5)
    fail_notification_dropdown = ttk.Combobox(fail_frame, values=["None"] + list(parent.master.master.page2.notifications.keys()), state="disabled")
    fail_notification_dropdown.set("None")
    fail_notification_dropdown.grid(row=0, column=2, padx=5)

    make_change_detect = tk.BooleanVar()
    tk.Checkbutton(pattern_window, text="Search change at area", variable=make_change_detect).pack(pady=5)

    click_var = tk.BooleanVar()
    tk.Checkbutton(pattern_window, text="Click if Found", variable=click_var).pack(pady=5)

    Label(pattern_window, text="Wait Time (seconds):").pack(pady=5)
    wait_time_entry = Entry(pattern_window)
    wait_time_entry.insert(0, "5")
    wait_time_entry.pack(pady=5)

    Label(pattern_window, text="Threshold:").pack(pady=5)
    threshold_entry = Entry(pattern_window)
    threshold_entry.insert(0, "0.7")
    threshold_entry.pack(pady=5)

    if hasattr(parent, "editing_pattern_context"):
        ctx = parent.editing_pattern_context

        pattern_window.edit_mode = True
        pattern_window.item_id = ctx.get("item_id")
        pattern_window.pattern_image_base64 = ctx.get("pattern_image_base64")
        print(f"1: {ctx.get('pattern_image_base64')}")
        pattern_window.pattern_coords = ctx.get("pattern_coords")
        pattern_window.search_coords = ctx.get("search_coords")
        import ast
        search_coords_parsed = ast.literal_eval(pattern_window.search_coords)
        start = search_coords_parsed['start']
        end = search_coords_parsed['end']
        x1, y1 = min(start[0], end[0]), min(start[1], end[1])
        width = abs(end[0] - start[0])
        height = abs(end[1] - start[1])
        img = pyautogui.screenshot(region=(x1, y1, width, height))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        search_image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        pattern_window.search_image_base64 = search_image_base64
        print(f"2: {ctx.get('search_coords')}")

        wait_time_entry.delete(0, tk.END)
        wait_time_entry.insert(0, str(ctx.get("wait_time", "5")))

        threshold_entry.delete(0, tk.END)
        threshold_entry.insert(0, str(ctx.get("threshold", "0.7")))

        click_var.set(ctx.get("click", False))
        make_change_detect.set(ctx.get("scene_change", False))

        succeed_checkpoint_dropdown.set(ctx.get("succeed_goto", "Next"))
        fail_checkpoint_dropdown.set(ctx.get("fail_goto", "Next"))

        succeed_send_var.set(ctx.get("succeed_notify", False))
        succeed_notification_dropdown.set(ctx.get("succeed_notify_value", "None"))
        succeed_notification_dropdown.config(state="readonly" if succeed_send_var.get() else "disabled")

        fail_send_var.set(ctx.get("fail_notify", False))
        fail_notification_dropdown.set(ctx.get("fail_notify_value", "None"))
        fail_notification_dropdown.config(state="readonly" if fail_send_var.get() else "disabled")

        # Ensure search image is updated from coordinates if available
        coords_for_update = None
        if pattern_window.search_coords:
            if pattern_window.search_coords == 'Full Screen':
                coords_for_update = (0, 0, screen_width, screen_height)
            elif isinstance(pattern_window.search_coords, dict):
                start = pattern_window.search_coords.get('start')
                end = pattern_window.search_coords.get('end')
                if start and end:
                    x1, y1 = start
                    x2, y2 = end
                    coords_for_update = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            elif isinstance(pattern_window.search_coords, str):
                try:
                    parsed = ast.literal_eval(pattern_window.search_coords)
                    if isinstance(parsed, tuple) and len(parsed) == 4:
                        coords_for_update = parsed
                except Exception as e:
                    print("Failed to parse search_coords:", e)
            elif isinstance(pattern_window.search_coords, tuple) and len(pattern_window.search_coords) == 4:
                coords_for_update = pattern_window.search_coords

            if coords_for_update:
                try:
                    update_image_from_coords(pattern_window, coords_for_update, search_preview_label, "search")
                except Exception as e:
                    print("Failed to update search image from coords:", e)

        restore_previous_images()

    def save_pattern_event():
        try:
            wait_time = float(wait_time_entry.get())
            threshold = float(threshold_entry.get())

            if not pattern_window.pattern_coords or not pattern_window.pattern_image_base64:
                print("Pattern area or image not set.")
                pattern_window.destroy()
                return

            event = f"Search Pattern - Image: {pattern_window.pattern_image_base64}, " \
                    f"Search Area: {pattern_window.search_coords or 'Full Screen'}, " \
                    f"Succeed Go To: {succeed_checkpoint_dropdown.get()}, Fail Go To: {fail_checkpoint_dropdown.get()}, " \
                    f"Click: {click_var.get()}, Wait: {wait_time}s, Threshold: {threshold}, Scene Change: {make_change_detect.get()}"

            if succeed_send_var.get() and succeed_notification_dropdown.get() != "None":
                event += f", Succeed Notification: {succeed_notification_dropdown.get()}"
            if fail_send_var.get() and fail_notification_dropdown.get() != "None":
                event += f", Fail Notification: {fail_notification_dropdown.get()}"

            values = (
                pattern_window.pattern_image_base64,
                pattern_window.search_coords or 'Full Screen',
                succeed_checkpoint_dropdown.get(),
                fail_checkpoint_dropdown.get(),
                str(click_var.get()),
                str(wait_time),
                str(threshold),
                str(make_change_detect.get()),
                str(succeed_send_var.get()),
                succeed_notification_dropdown.get(),
                str(fail_send_var.get()),
                fail_notification_dropdown.get()
            )

            if hasattr(pattern_window, "edit_mode") and pattern_window.edit_mode and hasattr(pattern_window, "item_id"):
                coords_callback(event, item_id=pattern_window.item_id, values=values)
            else:
                coords_callback(event, values=values)

            print(f"Added Pattern event: {event}")
            pattern_window.destroy()

        except ValueError as e:
            print(f"Invalid input: {e}")
            pattern_window.destroy()

    Button(pattern_window, text="OK", command=save_pattern_event).pack(pady=10)
    
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