# image_utils.py
from io import BytesIO
import base64
import ast

from PIL import Image, ImageTk
import pyautogui
from pynput import keyboard  # for RegionCapture


class RegionCapture:
    """Interactive region capture using F8 key twice to set start/end points."""
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


def update_pattern_preview_image(img: Image.Image, preview_label):
    """Resize for preview and update a Tkinter Label with a PhotoImage."""
    resized = img.resize((300, 200), Image.LANCZOS)
    preview_image = ImageTk.PhotoImage(resized)
    preview_label.config(image=preview_image, text="")
    preview_label.image = preview_image  # prevent GC


def update_image_from_coords(window, coords, label, target: str):
    """
    Take a screen region screenshot, update preview label, and store:
      - window.<target>_coords
      - window.<target>_image_base64
    """
    if not coords:
        print(f"No coordinates for {target}")
        return

    # Support stringified dict input
    if isinstance(coords, str):
        coords = ast.literal_eval(coords)

    try:
        x1, y1 = coords["start"]
        x2, y2 = coords["end"]
    except Exception:
        print("Invalid coords format; expected {'start': (x,y), 'end': (x,y)}")
        return

    if x2 <= x1 or y2 <= y1:
        print("Invalid coordinates (non-positive width/height).")
        return

    screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
    buffered = BytesIO()
    screenshot.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    update_pattern_preview_image(screenshot, label)
    setattr(window, f"{target}_coords", coords)
    setattr(window, f"{target}_image_base64", img_str)
    print(f"{target.title()} image updated.")


def select_area(window, label, target: str):
    """Capture a region interactively and update window + preview."""
    capture_tool = RegionCapture()
    img, coords = capture_tool.capture()
    update_image_from_coords(window, coords, label, target)
