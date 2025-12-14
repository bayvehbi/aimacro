"""
Pattern search utilities for macro automation.
Functions for searching patterns on screen, loading images, and coordinate handling.
"""
import time
import base64
from io import BytesIO
import pyautogui
from PIL import Image
import traceback
import os
from .logger import verbose, error


def load_image(pattern_img_str):
    """Load an image from a base64 string."""
    verbose("Decoding base64 pattern image...")
    pattern_data = base64.b64decode(pattern_img_str)
    pattern_buffer = BytesIO(pattern_data)
    pattern_img = Image.open(pattern_buffer)
    verbose(f"Pattern image loaded successfully, size: {pattern_img.size}")
    return pattern_img


def unpack_coords(search_coords):
    """Unpack coordinate dictionary into individual values."""
    x1, y1 = search_coords['start']
    x2, y2 = search_coords['end']
    width, height = x2 - x1, y2 - y1
    if width <= 0 or height <= 0:
        error(f"Invalid search area dimensions: width={width}, height={height}")
        return False
    return {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "width": width, "height": height}


def image_to_base64(screenshot):
    """Convert a PIL Image screenshot to base64 string."""
    buffered = BytesIO()
    screenshot.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def search_for_pattern(pattern_img_str, search_coords, settings, page1=None, click_if_found=False, wait_time=0, threshold=0.7):
    """
    Search for a pattern in the specified screen area.
    
    Args:
        pattern_img_str: Base64 encoded pattern image
        search_coords: Coordinates dict or 'Full Screen'
        settings: Application settings (not used but kept for compatibility)
        page1: Page1 instance for checking running state
        click_if_found: Whether to click if pattern is found
        wait_time: Maximum time to search (seconds)
        threshold: Confidence threshold for pattern matching
        
    Returns:
        True if pattern found, False otherwise
    """
    verbose(f"Search coordinates: {search_coords}")
    start_time = time.time()
    while (page1 is None or page1.running) and time.time() - start_time < wait_time:
        try:
            pattern_img = load_image(pattern_img_str)
            if search_coords and search_coords != 'Full Screen':
                x1, y1, x2, y2, width, height = unpack_coords(search_coords).values()
                verbose(f"Capturing screenshot in area: {search_coords}")
                screen = pyautogui.screenshot(region=(x1, y1, width, height))
                search_offset_x, search_offset_y = x1, y1
            else:
                verbose("Capturing full screen screenshot...")
                screen = pyautogui.screenshot()
                search_offset_x, search_offset_y = 0, 0
            verbose(f"Screen image captured, size: {screen.size}")
            verbose(f"Searching for pattern with confidence={threshold}, grayscale=True...")
            os.makedirs("./logs", exist_ok=True)
            screen.save("./logs/pattern_a.png")
            pattern_img.save("./logs/patter.png")
            location = pyautogui.locate(pattern_img, screen, grayscale=True, confidence=threshold)
            if location:
                verbose(f"Pattern found at {location}")
                if click_if_found:
                    center_x = search_offset_x + location.left + location.width // 2
                    center_y = search_offset_y + location.top + location.height // 2
                    verbose(f"Preparing to click at center: ({center_x}, {center_y})")
                    time.sleep(0.5)
                    pyautogui.click(center_x, center_y)
                    verbose(f"Clicked at pattern center: ({center_x}, {center_y})")
                return True
            else:
                if page1 and not page1.running:
                    verbose("Macro has been stopped. Exiting pattern search early.")
                    return False
                verbose(f"Pattern not found, retrying in 1 second... (Elapsed: {time.time() - start_time:.1f}s of {wait_time}s)")
                time.sleep(1)

        except pyautogui.ImageNotFoundException:
            verbose(f"Pattern not found (ImageNotFoundException), retrying in 1 second... (Elapsed: {time.time() - start_time:.1f}s of {wait_time}s)")
            time.sleep(1)
        except ValueError as ve:
            error(f"ValueError during pattern search: {ve} - Possibly invalid base64 data or coordinates")
            return False
        except Exception as e:
            error_trace = traceback.format_exc()
            error(f"Unexpected error during pattern search: {type(e).__name__}: {e}\nStack trace:\n{error_trace}")
            return False

    verbose(f"Pattern not found after {wait_time}s of retries")
    return False

