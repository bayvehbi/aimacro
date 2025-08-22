# image_utils.py
from io import BytesIO
import base64
import ast
from collections.abc import Mapping
from PIL import Image, ImageTk
import pyautogui
from pynput import keyboard  # for RegionCapture


class RegionCapture:
    """Interactive region capture using F8 twice to set start/end points (ESC to cancel)."""
    def __init__(self):
        self.coords = []
        self.listener = keyboard.Listener(on_press=self.on_key)
        self.cancelled = False

    def on_key(self, key):
        if key == keyboard.Key.esc:
            self.coords.clear()
            self.cancelled = True
            self.listener.stop()
            print("Capture cancelled.")
            return
        if key == keyboard.Key.f8:
            pos = pyautogui.position()
            print(f"Point recorded: {pos}")
            self.coords.append(pos)
            if len(self.coords) == 2:
                self.listener.stop()

    def capture(self):
        print("Press F8 twice to define region (ESC to cancel)...")
        self.listener.start()
        self.listener.join()
        if self.cancelled or len(self.coords) < 2:
            return None, None

        (x1, y1), (x2, y2) = self.coords
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        width = x2 - x1
        height = y2 - y1

        print(f"Capturing region: ({x1}, {y1}, {width}, {height})")
        img = pyautogui.screenshot(region=(x1, y1, width, height))
        return img, {"start": (x1, y1), "end": (x2, y2)}


def upscale_min_size(image_base64: str, min_size=(50, 50)) -> str:
    """
    Take a base64 PNG/JPG string, ensure it's at least min_size (w,h),
    upscale while keeping aspect ratio, and return a new base64 PNG string.
    """
    raw = base64.b64decode(image_base64)
    img = Image.open(BytesIO(raw))

    w, h = img.size
    min_w, min_h = min_size
    if w < min_w or h < min_h:
        scale = max(min_w / w, min_h / h)
        new_w = int(round(w * scale))
        new_h = int(round(h * scale))
        img = img.resize((new_w, new_h), Image.BICUBIC)

    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def parse_coords(c):
    if not c:
        return None

    # Accept any mapping-like object
    if isinstance(c, Mapping):
        try:
            x1, y1 = c["start"]
            x2, y2 = c["end"]
            return {"start": (int(x1), int(y1)), "end": (int(x2), int(y2))}
        except Exception:
            return None

    # String → safe-eval then recurse
    if isinstance(c, str):
        try:
            return parse_coords(ast.literal_eval(c))
        except Exception:
            return None

    # Accept ((x1,y1),(x2,y2)) or [[x1,y1],[x2,y2]]
    if isinstance(c, (list, tuple)) and len(c) == 2:
        s, e = c
        if isinstance(s, (list, tuple)) and isinstance(e, (list, tuple)) and len(s) == len(e) == 2:
            x1, y1 = s; x2, y2 = e
            return {"start": (int(x1), int(y1)), "end": (int(x2), int(y2))}

    return None


def encode_image_to_base64(img: Image.Image) -> str:
    """Encode a PIL Image to base64 PNG."""
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def render_base64_on_label(label, image_base64: str, size=(300, 200)):
    """Render a base64 PNG onto a Tkinter Label (resized for preview)."""
    try:
        decoded = base64.b64decode(image_base64)
        img = Image.open(BytesIO(decoded))
        prev = img.copy().resize(size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(prev)
        label.config(image=photo, text="")
        label.image = photo  # prevent GC
    except Exception as e:
        print("Failed to render base64 image:", e)


def screenshot_from_coords(coords):
    """
    Take a screenshot from coords dict {'start':(x,y), 'end':(x,y)}.
    Returns (PIL.Image, base64_str) or (None, None) on failure.
    """
    print(f"Taking screenshot from coords: {coords}")
    coords = parse_coords(coords)
    if not coords:
        print("Invalid coords.")
        return None, None
    try:
        x1, y1 = coords["start"]
        x2, y2 = coords["end"]
    except Exception:
        print("Invalid coords format; expected {'start':(x,y), 'end':(x,y)}")
        return None, None
    if x2 <= x1 or y2 <= y1:
        print("Invalid coordinates (non-positive width/height).")
        return None, None

    img = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
    return img, encode_image_to_base64(img)



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
    print(f"Updating {target} image from coords: {coords}")
    img, img_b64 = screenshot_from_coords(coords)
    if img is None:
        return
    update_pattern_preview_image(img, label)
    setattr(window, f"{target}_coords", parse_coords(coords))
    setattr(window, f"{target}_image_base64", img_b64)
    print(f"{target.title()} image updated.")


def select_area(window, label, target: str):
    """Capture a region interactively and update window + preview."""
    capture_tool = RegionCapture()
    img, coords = capture_tool.capture()
    if not coords:
        print("Capture aborted.")
        return
    update_image_from_coords(window, coords, label, target)
