# search_pattern.py
from functools import partial
import base64, io
import tkinter as tk
from tkinter import Toplevel, Label, Button, Entry, ttk
from PIL import Image, ImageTk

# ✅ CHANGE THESE IMPORTS to where your helpers actually are
# from your_module import select_area, update_image_from_coords
from image_utils import select_area, update_image_from_coords  # example

def open_pattern_window(
    parent,
    coords_callback,
    initial_values=None,
    checkpoints=None,
    notifications=None,
):
    """
    Open the 'Search Pattern' window.

    - parent: Tk or Toplevel
    - coords_callback: function(event_text, values=tuple, item_id=optional)
    - initial_values: dict for prefill
    - checkpoints: iterable for succeed/fail comboboxes (optional)
    - notifications: iterable for notification comboboxes (optional)
    """

    def set_bool_var(var, value):
        if value is None:
            return
        if isinstance(value, str):
            value = value.lower() in ("true", "1")
        var.set(bool(value))

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
            preview_img = image.copy().resize((300, 200), Image.LANCZOS)
            photo = ImageTk.PhotoImage(preview_img)
            label.config(image=photo)
            label.image = photo
        except Exception as e:
            print("Failed to render image:", e)

    pattern_window = Toplevel(parent)
    pattern_window.title("Search for Pattern")

    # state carried on the window instance
    pattern_window.pattern_coords = None
    pattern_window.search_coords = None
    pattern_window.pattern_image_base64 = None
    pattern_window.search_image_base64 = None

    screen_width = pattern_window.winfo_screenwidth()
    screen_height = pattern_window.winfo_screenheight()
    window_width = int(screen_width * 0.4)
    pattern_window.geometry(f"{window_width}x{screen_height}")
    pattern_window.attributes("-topmost", True)

    # scrollable, centered content
    canvas = tk.Canvas(pattern_window)
    v_scrollbar = tk.Scrollbar(pattern_window, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=v_scrollbar.set)
    v_scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    container = tk.Frame(canvas)
    canvas.create_window((0, 0), window=container, anchor="nw", tags="container")
    scrollable_frame = tk.Frame(container)
    scrollable_frame.pack(anchor="center", pady=20)

    def on_frame_configure(_):
        canvas.configure(scrollregion=canvas.bbox("all"))
    container.bind("<Configure>", on_frame_configure)

    def on_canvas_resize(event):
        canvas.itemconfig("container", width=event.width)
    canvas.bind("<Configure>", on_canvas_resize)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # UI
    Label(scrollable_frame, text="Define Search Area").pack(pady=5)
    search_preview_label = Label(scrollable_frame, text="No search area selected yet")
    Button(scrollable_frame, text="Select Search Area",
           command=partial(select_area, pattern_window, search_preview_label, "search")).pack(pady=5)
    search_preview_label.pack(pady=5)

    pattern_preview_label = Label(scrollable_frame, text="No pattern selected yet")
    Button(scrollable_frame, text="Select Pattern",
           command=partial(select_area, pattern_window, pattern_preview_label, "pattern")).pack(pady=5)
    Button(scrollable_frame, text="Recapture Pattern Image",
           command=lambda: update_image_from_coords(pattern_window, pattern_window.pattern_coords, pattern_preview_label, "pattern")).pack(pady=5)
    pattern_preview_label.pack(pady=5)

    copy_to_pattern = tk.BooleanVar()
    tk.Checkbutton(scrollable_frame, text="Copy search to pattern",
                   variable=copy_to_pattern, command=on_copy_search_to_pattern).pack(pady=5)

    # derive checkpoints/notifications if not passed
    if checkpoints is None:
        try:
            checkpoints = list(parent.checkpoints.keys())
        except Exception:
            checkpoints = []
    if notifications is None:
        try:
            notifications = list(parent.master.master.page2.notifications.keys())
        except Exception:
            notifications = []

    Label(scrollable_frame, text="If Found, Succeed Go To:").pack(pady=5)
    succeed_frame = tk.Frame(scrollable_frame)
    succeed_frame.pack(pady=5)
    succeed_send_var = tk.BooleanVar()
    tk.Checkbutton(succeed_frame, text="Send Notification",
                   variable=succeed_send_var, command=lambda: toggle_notification('succeed')).grid(row=0, column=0, padx=5)
    succeed_checkpoint_dropdown = ttk.Combobox(succeed_frame,
        values=["Next", "Wait"] + list(checkpoints), state="readonly")
    succeed_checkpoint_dropdown.set("Next")
    succeed_checkpoint_dropdown.grid(row=0, column=1, padx=5)
    succeed_notification_dropdown = ttk.Combobox(succeed_frame,
        values=["None"] + list(notifications), state="disabled")
    succeed_notification_dropdown.set("None")
    succeed_notification_dropdown.grid(row=0, column=2, padx=5)

    Label(scrollable_frame, text="If Not Found, Fail Go To:").pack(pady=5)
    fail_frame = tk.Frame(scrollable_frame)
    fail_frame.pack(pady=5)
    fail_send_var = tk.BooleanVar()
    tk.Checkbutton(fail_frame, text="Send Notification",
                   variable=fail_send_var, command=lambda: toggle_notification('fail')).grid(row=0, column=0, padx=5)
    fail_checkpoint_dropdown = ttk.Combobox(fail_frame,
        values=["Next", "Wait"] + list(checkpoints), state="readonly")
    fail_checkpoint_dropdown.set("Next")
    fail_checkpoint_dropdown.grid(row=0, column=1, padx=5)
    fail_notification_dropdown = ttk.Combobox(fail_frame,
        values=["None"] + list(notifications), state="disabled")
    fail_notification_dropdown.set("None")
    fail_notification_dropdown.grid(row=0, column=2, padx=5)

    make_change_detect = tk.BooleanVar()
    tk.Checkbutton(scrollable_frame, text="Search change at area",
                   variable=make_change_detect).pack(pady=5)

    click_var = tk.BooleanVar()
    tk.Checkbutton(scrollable_frame, text="Click if Found",
                   variable=click_var).pack(pady=5)

    Label(scrollable_frame, text="Wait Time (seconds):").pack(pady=5)
    wait_time_entry = Entry(scrollable_frame)
    wait_time_entry.insert(0, "5")
    wait_time_entry.pack(pady=5)

    Label(scrollable_frame, text="Threshold:").pack(pady=5)
    threshold_entry = Entry(scrollable_frame)
    threshold_entry.insert(0, "0.7")
    threshold_entry.pack(pady=5)

    def populate_fields_from_initial_values():
        iv = initial_values or {}
        if iv.get('pattern_image_base64'):
            render_image(pattern_preview_label, iv['pattern_image_base64'])
            pattern_window.pattern_image_base64 = iv['pattern_image_base64']
        if iv.get('search_coords'):
            update_image_from_coords(pattern_window, iv['search_coords'], search_preview_label, "search")
            pattern_window.search_coords = iv['search_coords']
        if iv.get('search_image_base64'):
            render_image(search_preview_label, iv['search_image_base64'])
            pattern_window.search_image_base64 = iv['search_image_base64']
        if iv.get('pattern_coords'):
            pattern_window.pattern_coords = iv['pattern_coords']
        if iv.get('wait_time') is not None:
            wait_time_entry.delete(0, tk.END); wait_time_entry.insert(0, str(iv['wait_time']))
        if iv.get('threshold') is not None:
            threshold_entry.delete(0, tk.END); threshold_entry.insert(0, str(iv['threshold']))
        if iv.get('succeed_checkpoint'):
            succeed_checkpoint_dropdown.set(iv['succeed_checkpoint'])
        if iv.get('fail_checkpoint'):
            fail_checkpoint_dropdown.set(iv['fail_checkpoint'])
        set_bool_var(click_var, iv.get('click'))
        set_bool_var(make_change_detect, iv.get('scene_change'))
        set_bool_var(succeed_send_var, iv.get('succeed_send'))
        if iv.get('succeed_notification'):
            succeed_notification_dropdown.set(iv['succeed_notification'])
        set_bool_var(fail_send_var, iv.get('fail_send'))
        if iv.get('fail_notification'):
            fail_notification_dropdown.set(iv['fail_notification'])

    if initial_values:
        populate_fields_from_initial_values()

    def save_pattern_event():
        try:
            print("Saving pattern event with values:")
            # item_id = initial_values.get("Item ID")
            iv = initial_values or {}
            item_id = iv.get("item_id")
            print(f"Item ID: {item_id}")
            wait_time = float(wait_time_entry.get())
            threshold = float(threshold_entry.get())
            succeed_checkpoint = succeed_checkpoint_dropdown.get()
            fail_checkpoint = fail_checkpoint_dropdown.get()
            click = click_var.get()
            scene_change = make_change_detect.get()
            succeed_send = succeed_send_var.get()
            succeed_notification = succeed_notification_dropdown.get()
            fail_send = fail_send_var.get()
            fail_notification = fail_notification_dropdown.get()
            pattern_window.search_coords
            pattern_window.wait_time = wait_time
            pattern_window.threshold = threshold
            pattern_window.succeed_checkpoint = succeed_checkpoint
            pattern_window.fail_checkpoint = fail_checkpoint
            pattern_window.click = click
            pattern_window.scene_change = scene_change
            pattern_window.succeed_send = succeed_send
            pattern_window.succeed_notification = succeed_notification
            pattern_window.fail_send = fail_send
            pattern_window.fail_notification = fail_notification

            if  not pattern_window.pattern_image_base64:
                print("Pattern area or image not set.")
                pattern_window.destroy()
                return

            event = (f"Search Pattern - Image: {pattern_window.pattern_image_base64}, "
                     f"Search Area: {pattern_window.search_coords or 'Full Screen'}, "
                     f"Succeed Go To: {succeed_checkpoint}, Fail Go To: {fail_checkpoint}, "
                     f"Click: {click}, Wait: {wait_time}s, Threshold: {threshold}, "
                     f"Scene Change: {scene_change}")

            if succeed_send and succeed_notification != "None":
                event += f", Succeed Notification: {succeed_notification}"
            if fail_send and fail_notification != "None":
                event += f", Fail Notification: {fail_notification}"

            values = (
                pattern_window.pattern_image_base64,
                pattern_window.search_coords or 'Full Screen',
                succeed_checkpoint,
                fail_checkpoint,
                str(click),
                str(wait_time),
                str(threshold),
                str(scene_change),
                str(succeed_send),
                succeed_notification,
                str(fail_send),
                fail_notification
            )

            if item_id:
                print(f"edit mode active for item_id: {pattern_window.item_id}")
                coords_callback(event, item_id=pattern_window.item_id, values=values)
            else:
                print("edit mode not active, calling coords_callback without item_id")
                coords_callback(event, values=values)

            # print(f"Added Pattern event: {event}")
            pattern_window.destroy()

        except ValueError as e:
            print(f"Invalid input: {e}")
            pattern_window.destroy()

    Button(scrollable_frame, text="OK", command=save_pattern_event).pack(pady=10)
