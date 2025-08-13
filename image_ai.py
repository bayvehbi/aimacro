# image_ai.py
import tkinter as tk
from tkinter import Toplevel
import tkinter.messagebox as messagebox
from image_utils import select_area, parse_coords, update_image_from_coords

def open_image_ai_window(parent, coords_callback, variables=None, initial_values=None):
    """Open Image AI window. Edit mode auto-detected from initial_values['item_id'/'item_number'].""" 
    iv = initial_values or {}
    item_id = iv.get("item_id") or iv.get("item_number")

    win = Toplevel(parent)
    win.title("Image AI")
    screen_width, screen_height = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{int(screen_width*0.4)}x{int(screen_height*0.6)}")  # a bit taller since it's scrollable
    win.attributes("-topmost", True)

    # -------- Scrollable root (Canvas + Scrollbar) --------
    canvas = tk.Canvas(win, highlightthickness=0)
    v_scroll = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=v_scroll.set)

    v_scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    container = tk.Frame(canvas)
    canvas.create_window((0, 0), window=container, anchor="nw", tags="container")

    scrollable = tk.Frame(container)
    scrollable.pack(anchor="center", pady=20)

    def on_frame_configure(_):
        canvas.configure(scrollregion=canvas.bbox("all"))
    container.bind("<Configure>", on_frame_configure)

    def on_canvas_resize(event):
        canvas.itemconfig("container", width=event.width)
    canvas.bind("<Configure>", on_canvas_resize)

    # Mouse wheel (Win/macOS/Linux)
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)      # Windows/macOS
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux up
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux down
    # ------------------------------------------------------

    # -------- UI in scrollable frame --------
    tk.Label(scrollable, text="Define Area").pack(pady=5)
    preview_label = tk.Label(scrollable, text="No area selected yet")
    tk.Button(
        scrollable, text="Select Area",
        command=lambda: select_area(win, preview_label, "image_ai")
    ).pack(pady=5)
    preview_label.pack(pady=5)

    tk.Label(scrollable, text="Image AI content (prompt / expected text)").pack(pady=5)
    variable_message = tk.Entry(scrollable)
    variable_message.pack(pady=5)

    tk.Label(scrollable, text="Wait Time (seconds):").pack(pady=5)
    wait_time_entry = tk.Entry(scrollable); wait_time_entry.insert(0, "5"); wait_time_entry.pack(pady=5)

    tk.Label(scrollable, text="Output Variable Name:").pack(pady=5)
    variable_entry = tk.Entry(scrollable); variable_entry.pack(pady=5)
    # ---------------------------------------

    # ---- Populate for edit ----
    if iv:
        parsed = parse_coords(iv.get("coords"))
        if parsed:
            update_image_from_coords(win, parsed, preview_label, "image_ai")
        if "wait_time" in iv:
            wait_time_entry.delete(0, tk.END); wait_time_entry.insert(0, str(iv["wait_time"]))
        if "variable_name" in iv:
            variable_entry.delete(0, tk.END); variable_entry.insert(0, iv["variable_name"] or "")
        if "variable_content" in iv:
            variable_message.delete(0, tk.END); variable_message.insert(0, iv["variable_content"] or "")

    def save_image_ai_event():
        try:
            wait_time = float(wait_time_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for wait time.")
            return

        variable_name = variable_entry.get().strip()
        variable_content = variable_message.get()

        if not variable_name:
            messagebox.showerror("Missing Variable Name", "Please provide a variable name before saving.")
            return
        if not hasattr(win, "image_ai_coords"):
            messagebox.showerror("Missing Area", "Please select an area first.")
            return

        coords = win.image_ai_coords
        event = (f"Image AI - Area: {coords}, "
                 f"Wait: {wait_time}s, "
                 f"Variable: {variable_name}, "
                 f"Variable Content: {variable_content}")
        values = (coords, wait_time, variable_name, variable_content)

        if item_id is not None:
            coords_callback(event, item_id=item_id, values=values)
        else:
            coords_callback(event, values=values)

        print(f"{'Updated' if item_id is not None else 'Added'} Image AI event: {event}")
        win.destroy()

    tk.Button(scrollable, text="OK", command=save_image_ai_event).pack(pady=10)
