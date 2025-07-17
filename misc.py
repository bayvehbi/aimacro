import time
import re
from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse
import pyautogui
import base64
from io import BytesIO
import requests
from PIL import Image
import traceback
import http.client
import urllib.parse
import datetime
import os 

def send_notification(notification_name, page1):
    """Send a notification via Pushover API."""
    if not notification_name:
        return
    notification = page1.master.master.page2.notifications.get(notification_name)
    if notification:
        try:
            conn = http.client.HTTPSConnection("api.pushover.net:443")
            params = {
                "token": notification["token"],
                "user": notification["user"],
                "message": notification["message"],
                "priority": notification["priority"]
            }
            if notification["priority"] == 2:
                params.update({"expire": 60, "retry": 60})
            conn.request("POST", "/1/messages.json", urllib.parse.urlencode(params), {"Content-type": "application/x-www-form-urlencoded"})
            response = conn.getresponse()
            if response.status == 200:
                print(f"Sent notification: {notification_name}")
            else:
                print(f"Failed to send notification '{notification_name}': {response.status} - {response.reason}")
            conn.close()
        except Exception as e:
            print(f"Error sending notification '{notification_name}': {e}")
    else:
        print(f"Notification '{notification_name}' not found in notifications: {page1.master.master.page2.notifications}")

def send_to_grok_ocr(image_base64, settings, variable_content):
    """Extract text from an image using Grok OCR API."""
    api_key = settings.get("grok_api_key")
    if not api_key:
        raise ValueError("Please enter a valid xAI API key. You can obtain one from https://console.x.ai.")

    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "grok-2-vision-1212",
        "messages": [
            {"role": "system", "content": ""  + variable_content},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                {"type": "text", "text": "" + variable_content}
            ]}
        ],
        "max_tokens": 500
    }

    # url = "https://api.x.ai/v1/chat/completions"
    # headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    # payload = {
    #     "model": "grok-2-vision-1212",
    #     "messages": [
    #         {"role": "system", "content": "Analyze this image and extract the text. Return only the text, no additional response."  + variable_content},
    #         {"role": "user", "content": [
    #             {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
    #             {"type": "text", "text": "Extract the text. Do not respond with anything else. "}
    #         ]}
    #     ],
    #     "max_tokens": 500
    # }

    print("this is payload" + str(payload))
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        text = result.get("choices", [{}])[0].get("message", {}).get("content", "Text not found")
        return text
    except requests.exceptions.RequestException as e:
        return f"API request failed: {str(e)}"
    except ValueError as e:
        return f"JSON parsing error: {str(e)}"

def search_for_pattern(pattern_img_str, search_coords, settings, page1=None, click_if_found=False, wait_time=0, threshold=0.7):
    """Search for a pattern in the specified screen area."""
    print(search_coords)
    start_time = time.time()
    while (page1 is None or page1.running) and time.time() - start_time < wait_time:
        try:
            pattern_img = load_image(pattern_img_str)
            if search_coords and search_coords != 'Full Screen':
                x1, y1, x2, y2, width, height = unpack_coords(search_coords).values()
                print(f"Capturing screenshot in area: {search_coords}")
                screen = pyautogui.screenshot(region=(x1, y1, width, height))
                search_offset_x, search_offset_y = x1, y1
            else:
                print("Capturing full screen screenshot...")
                screen = pyautogui.screenshot()
                search_offset_x, search_offset_y = 0, 0
            print(f"Screen image captured, size: {screen.size}")
            print(f"Searching for pattern with confidence={threshold}, grayscale=True...")
            os.makedirs("./logs", exist_ok=True)
            screen.save("./logs/pattern_a.png")
            pattern_img.save("./logs/patter.png")
            location = pyautogui.locate(pattern_img, screen, grayscale=True, confidence=threshold)
            if location:
                print(f"Pattern found at {location}")
                if click_if_found:
                    center_x = search_offset_x + location.left + location.width // 2
                    center_y = search_offset_y + location.top + location.height // 2
                    print(f"Preparing to click at center: ({center_x}, {center_y})")
                    time.sleep(0.5)
                    pyautogui.click(center_x, center_y)
                    print(f"Clicked at pattern center: ({center_x}, {center_y})")
                return True
            else:
                if page1 and not page1.running:
                    print("Macro has been stopped. Exiting pattern search early.")
                    return False
                print(f"Pattern not found, retrying in 1 second... (Elapsed: {time.time() - start_time:.1f}s of {wait_time}s)")
                time.sleep(1)

        except pyautogui.ImageNotFoundException:
            print(f"Pattern not found (ImageNotFoundException), retrying in 1 second... (Elapsed: {time.time() - start_time:.1f}s of {wait_time}s)")
            time.sleep(1)
        except ValueError as ve:
            print(f"ValueError during pattern search: {ve} - Possibly invalid base64 data or coordinates")
            return False
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"Unexpected error during pattern search: {type(e).__name__}: {e}\nStack trace:\n{error_trace}")
            return False

    print(f"Pattern not found after {wait_time}s of retries")
    return False

def load_image(pattern_img_str):
    print("Decoding base64 pattern image...")
    pattern_data = base64.b64decode(pattern_img_str)
    pattern_buffer = BytesIO(pattern_data)
    pattern_img = Image.open(pattern_buffer)
    print(f"Pattern image loaded successfully, size: {pattern_img.size}")
    return pattern_img

def unpack_coords(search_coords):
    x1, y1 = search_coords['start']
    x2, y2 = search_coords['end']
    width, height = x2 - x1, y2 - y1
    if width <= 0 or height <= 0:
        print(f"Invalid search area dimensions: width={width}, height={height}")
        return False
    return {"x1": x1, "y1":y1, "x2": x2, "y2": y2, "width": width, "height": height}
    # return {x1, y1, x2, y2, width, height}

def image_to_base64(screenshot):
    buffered = BytesIO()
    screenshot.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

# Precompiled regex patterns
TIMESTAMP_PATTERN = re.compile(r"(\d+\.\d+) - (.+)")
KEY_PRESS_PATTERN = re.compile(r"Key pressed: (.+)")
KEY_RELEASE_PATTERN = re.compile(r"Key released: (.+)")
MOUSE_MOVE_PATTERN = re.compile(r"Mouse moved to: \((\d+), (\d+)\)")
MOUSE_SCROLL_PATTERN = re.compile(r"Mouse scrolled (up|down)(?: at: \((\d+), (\d+)\))?")
MOUSE_LEFT_PRESS_PATTERN = re.compile(r"Mouse Button\.left pressed(?: at: \((\d+), (\d+)\))?")
MOUSE_LEFT_RELEASE_PATTERN = re.compile(r"Mouse Button\.left released(?: at: \((\d+), (\d+)\))?")
MOUSE_RIGHT_PRESS_PATTERN = re.compile(r"Mouse Button\.right pressed(?: at: \((\d+), (\d+)\))?")
MOUSE_RIGHT_RELEASE_PATTERN = re.compile(r"Mouse Button\.right released(?: at: \((\d+), (\d+)\))?")
OCR_PATTERN = re.compile(r"OCR Search - Area: ({.+?}), Wait: (\d+\.\d+)s, Variable: (\w+), Variable Content: (.+)")
SEARCH_PATTERN = re.compile(r"Search Pattern - Image: (.+?), Search Area: (.+?), Succeed Go To: (.+?), Fail Go To: (.+?), Click: (True|False), Wait: (\d+\.\d+)s, Threshold: (\d+\.\d+), Scene Change: (True|False)(?:, Succeed Notification: ([\w-]+))?(?:, Fail Notification: ([\w-]+))?")
IF_PATTERN = re.compile(r"If (\w+) ([><=!%]+|Contains) (.+?), Succeed Go To: (.+?), Fail Go To: (.+?), Wait: (\d+\.\d+)s(?:, Succeed Notification: ([\w-]+))?(?:, Fail Notification: ([\w-]+))?")
WAIT_PATTERN = re.compile(r"Wait: (\d+\.\d+)s")

def execute_macro_logic(action, page1, current_index, variables, previous_timestamp=None):
    """Process a single macro event and return the next index and timestamp, waiting for time difference if needed."""
    if not page1.running:
        print("Macro not running, skipping event.")
        return current_index, previous_timestamp

    # print(f"Processing: {action} at index {current_index}")

    kb_controller = pynput_keyboard.Controller()
    mouse_controller = pynput_mouse.Controller()

    # Check and parse timestamp
    timestamp_match = TIMESTAMP_PATTERN.match(action)
    current_timestamp = None
    if timestamp_match:
        timestamp, event_action = timestamp_match.groups()
        current_timestamp = float(timestamp)
        print(f"Parsed timestamp: {current_timestamp}, action: {event_action}")
        action = event_action

        # Wait for the time difference between previous and current event
        if previous_timestamp is not None:
            time_diff = current_timestamp - previous_timestamp
            if time_diff > 0:
                print(f"Waiting {time_diff:.3f} seconds before executing...")
                time.sleep(time_diff)

    # Handle key press events
    key_press_match = KEY_PRESS_PATTERN.match(action)
    if key_press_match:
        page1.dynamic_text.set(f"line: {current_index} - " + key_press_match.string)
        key = key_press_match.group(1)
        try:
            if key.startswith("'") and key.endswith("'"):  # Single character keys: 'a', 's', 'd'
                kb_controller.press(key[1])
                print(f"Pressed key: {key}")
            elif key.startswith("Key."):  # Special keys: Key.alt_l, Key.tab
                key_name = key.replace("Key.", "")
                kb_controller.press(getattr(pynput_keyboard.Key, key_name))
                print(f"Pressed key: {key}")
            else:  # Plain single character keys: a, s, d
                kb_controller.press(key)
                print(f"Pressed key: {key}")
        except AttributeError:
            print(f"Key not recognized: {key}")
        return current_index + 1, current_timestamp

    # Handle key release events
    key_release_match = KEY_RELEASE_PATTERN.match(action)
    if key_release_match:
        page1.dynamic_text.set(f"line: {current_index} - " + key_release_match.string)
        key = key_release_match.group(1)
        try:
            if key.startswith("'") and key.endswith("'"):  # Single character keys: 'a', 's', 'd'
                kb_controller.release(key[1])
                print(f"Released key: {key}")
            elif key.startswith("Key."):  # Special keys: Key.alt_l, Key.tab
                key_name = key.replace("Key.", "")
                kb_controller.release(getattr(pynput_keyboard.Key, key_name))
                print(f"Released key: {key}")
            else:  # Plain single character keys: a, s, d
                kb_controller.release(key)
                print(f"Released key: {key}")
        except AttributeError:
            print(f"Key not recognized: {key}")
        return current_index + 1, current_timestamp

    mouse_move_match = MOUSE_MOVE_PATTERN.match(action)
    if mouse_move_match:
        page1.dynamic_text.set(f"line: {current_index} - " + mouse_move_match.string)
        x, y = map(int, mouse_move_match.groups())
        mouse_controller.position = (x, y)
        print(f"Moved mouse to: ({x}, {y})")
        return current_index + 1, current_timestamp

    mouse_scroll_match = MOUSE_SCROLL_PATTERN.match(action)
    if mouse_scroll_match:
        page1.dynamic_text.set(f"line: {current_index} - " + mouse_scroll_match.string)
        direction, x, y = mouse_scroll_match.groups()
        if x and y:
            mouse_controller.position = (int(x), int(y))
        else:
            x, y = mouse_controller.position
        scroll_amount = 1 if direction == "up" else -1
        mouse_controller.scroll(0, scroll_amount)
        print(f"Scrolled {direction} at: ({x}, {y})")
        return current_index + 1, current_timestamp


    mouse_left_press_match = MOUSE_LEFT_PRESS_PATTERN.match(action)
    if mouse_left_press_match:
        page1.dynamic_text.set(f"line: {current_index} - " + mouse_left_press_match.string)
        x, y = mouse_left_press_match.groups()
        if x and y:
            pos = (int(x), int(y))
            mouse_controller.position = pos
        else:
            pos = mouse_controller.position
        mouse_controller.press(pynput_mouse.Button.left)
        print(f"Left click pressed at: {pos}")
        return current_index + 1, current_timestamp


    mouse_left_release_match = MOUSE_LEFT_RELEASE_PATTERN.match(action)
    if mouse_left_release_match:
        page1.dynamic_text.set(f"line: {current_index} - " + mouse_left_release_match.string)
        x, y = mouse_left_release_match.groups()
        if x and y:
            pos = (int(x), int(y))
            mouse_controller.position = pos
        else:
            pos = mouse_controller.position
        mouse_controller.release(pynput_mouse.Button.left)
        print(f"Left click released at: {pos}")
        return current_index + 1, current_timestamp


    mouse_right_press_match = MOUSE_RIGHT_PRESS_PATTERN.match(action)
    if mouse_right_press_match:
        page1.dynamic_text.set(f"line: {current_index} - " + mouse_right_press_match.string)
        x, y = mouse_right_press_match.groups()
        if x and y:
            pos = (int(x), int(y))
            mouse_controller.position = pos
        else:
            pos = mouse_controller.position
        mouse_controller.press(pynput_mouse.Button.right)
        print(f"Right click pressed at: {pos}")
        return current_index + 1, current_timestamp


    mouse_right_release_match = MOUSE_RIGHT_RELEASE_PATTERN.match(action)
    if mouse_right_release_match:
        page1.dynamic_text.set(f"line: {current_index} - " + mouse_right_release_match.string)
        x, y = mouse_right_release_match.groups()
        if x and y:
            pos = (int(x), int(y))
            mouse_controller.position = pos
        else:
            pos = mouse_controller.position
        mouse_controller.release(pynput_mouse.Button.right)
        print(f"Right click released at: {pos}")
        return current_index + 1, current_timestamp

    ocr_match = OCR_PATTERN.match(action)
    if ocr_match:
        page1.dynamic_text.set(f"line: {current_index} - " + ocr_match.string)
        coords_str, wait_time, variable_name, variable_content = ocr_match.groups()
        coords = eval(coords_str)
        wait_time = float(wait_time)
        x1, y1 = coords['start']
        x2, y2 = coords['end']

        screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
        buffered = BytesIO()
        os.makedirs("./logs", exist_ok=True)
        screenshot.save(buffered, format="PNG")
        screenshot.save("./logs/ocr.png")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        text = send_to_grok_ocr(img_str, page1.master.master.settings, variable_content)
        print(f"OCR Result: {text}")

        if variable_name:
            page1.variables[variable_name] = text
            print(f"OCR result '{text}' saved to variable '{variable_name}'")
            print(f"Current variables: {page1.variables}")
            page1.page2.update_variables_list()

        if "Text not found" in text or "API request failed" in text or "JSON parsing error" in text:
            print(f"OCR failed, waiting {wait_time} seconds before stopping...")
            time.sleep(wait_time)
            page1.running = False
        else:
            print("OCR found text, continuing macro...")
        return current_index + 1, previous_timestamp

    search_match = SEARCH_PATTERN.match(action)
    if search_match:
        page1.dynamic_text.set(f"line: {current_index} - " + search_match.string)
        img_str, search_coords_str, succeed_checkpoint, fail_checkpoint, click_if_found, wait_time, threshold_str, scene_change, succeed_notification_name, fail_notification_name = search_match.groups()
        print(f"Parsed Search event: Image={img_str[:25]}, Search Area={search_coords_str}, Succeed Go To={succeed_checkpoint}, Fail Go To={fail_checkpoint}, Click={click_if_found}, Wait={wait_time}, Threshold={threshold_str}")
        try:
            wait_time = float(wait_time)
            threshold = float(threshold_str) if threshold_str.replace('.', '').isdigit() else 0.7
            search_coords = eval(search_coords_str) if search_coords_str != 'Full Screen' else 'Full Screen'
            click_if_found = click_if_found == 'True'

            print("Calling search_for_pattern...")
            pattern_found = search_for_pattern(img_str, search_coords, page1.master.master.settings, page1=page1, click_if_found=click_if_found, wait_time=wait_time, threshold=threshold)
            print(f"search_for_pattern returned: {pattern_found}")
            target_checkpoint = succeed_checkpoint if pattern_found else fail_checkpoint
            print(f"Pattern {'found' if pattern_found else 'not found'}, going to '{target_checkpoint}'...")

            # Send notification based on pattern result
            if pattern_found and succeed_notification_name:
                print(f"Attempting to send succeed notification: {succeed_notification_name}")
                send_notification(succeed_notification_name, page1)
            elif not pattern_found and fail_notification_name:
                print(f"Attempting to send fail notification: {fail_notification_name}")
                send_notification(fail_notification_name, page1)

            if scene_change == 'True' and not pattern_found:
                x1, y1, x2, y2, width, height = unpack_coords(search_coords).values()
                screen = pyautogui.screenshot(region=(x1, y1, width, height))
                screen_str = image_to_base64(screen)
                os.makedirs("./logs", exist_ok=True)
                load_image(screen_str).save("./logs/newone.png")
                new_text = re.sub(r'Image: [^\s,]+', 'Image: ' + str(screen_str), page1.left_treeview.item(page1.left_treeview.get_children()[current_index])["text"])                # Update the event in self.events and treeview text
                page1.left_treeview.item(page1.left_treeview.get_children()[current_index], text=new_text)
                
            if target_checkpoint != "Next":
                next_index = page1.get_checkpoint_index(target_checkpoint)
                if next_index is not None:
                    print(f"Jumping to checkpoint index: {next_index}")
                    return next_index, current_timestamp
                print(f"Checkpoint '{target_checkpoint}' not found, continuing to next event...")
            return current_index + 1, current_timestamp

        except ValueError as e:
            print(f"Error parsing numeric values: {e}")
            return current_index + 1, current_timestamp

    if_match = IF_PATTERN.match(action)
    if if_match:
        page1.dynamic_text.set(f"line: {current_index} - " + if_match.string)
        variable_name, condition, value, succeed_checkpoint, fail_checkpoint, wait_time, succeed_notification_name, fail_notification_name = if_match.groups()
        print(f"Parsed If event: Variable={variable_name}, Condition={condition}, Value={value}, Succeed Go To={succeed_checkpoint}, Fail Go To={fail_checkpoint}, Wait={wait_time}")
        now = datetime.datetime.now()
        variables["time_hour"] = now.hour
        variables["time_minute"] = now.minute
        variables["time_second"] = now.second
        variables["time_weekday"] = now.weekday()
        variables["time_day"] = now.day
        variables["time_month"] = now.month
        variables["time_year"] = now.year
        wait_time = float(wait_time)
        variable_value = variables.get(variable_name)
        
        if variable_value is None:
            print(f"Variable '{variable_name}' not found in variables: {variables}, skipping If condition.")
            return current_index + 1, current_timestamp
        print(f"variable_value: {variable_value} - value: {value}")
        condition_met = False
        if condition == "==":
            try:
                # Destek: time_minute % 5 == 0 gibi ifadeleri çöz
                condition_met = eval(str(variable_value) + "==" + str(value))
            except:
                condition_met = str(variable_value) == str(value)
        elif condition == ">":
            condition_met = float(variable_value) > float(value) if variable_value.replace('.', '').isdigit() and value.replace('.', '').isdigit() else False
        elif condition == "<":
            condition_met = float(variable_value) < float(value) if variable_value.replace('.', '').isdigit() and value.replace('.', '').isdigit() else False
        elif condition == ">=":
            condition_met = float(variable_value) >= float(value) if variable_value.replace('.', '').isdigit() and value.replace('.', '').isdigit() else False
        elif condition == "<=":
            condition_met = float(variable_value) <= float(value) if variable_value.replace('.', '').isdigit() and value.replace('.', '').isdigit() else False
        elif condition == "!=":
            condition_met = str(variable_value) != str(value)
        elif condition == "Contains":
            condition_met = str(value) in str(variable_value)
        elif condition == "%":
            try:
                condition_met = int(variable_value) % int(value) == 0
            except:
                condition_met = False

        target_checkpoint = succeed_checkpoint if condition_met else fail_checkpoint
        print(f"Condition {'met' if condition_met else 'not met'}, going to '{target_checkpoint}'...")

        # Send notification based on condition result
        if condition_met and succeed_notification_name:
            print(f"Attempting to send succeed notification: {succeed_notification_name}")
            send_notification(succeed_notification_name, page1)
        elif not condition_met and fail_notification_name:
            print(f"Attempting to send fail notification: {fail_notification_name}")
            send_notification(fail_notification_name, page1)

        if target_checkpoint != "Next":
            next_index = page1.get_checkpoint_index(target_checkpoint)
            if next_index is not None:
                print(f"Jumping to checkpoint index: {next_index}")
                return next_index, current_timestamp
            print(f"Checkpoint '{target_checkpoint}' not found, continuing to next event...")
        return current_index + 1, current_timestamp

    wait_match = WAIT_PATTERN.match(action)
    if wait_match:
        wait_time = float(wait_match.group(1))
        print(f"Waiting for {wait_time} seconds...")
        for i in range(int(wait_time)):
            page1.dynamic_text.set(f"line: {current_index} - " + f"waiting: {wait_time-i}")
            time.sleep(1)
            if page1 and not page1.running:
                page1.running = False
                return current_index, previous_timestamp
    
        print(f"Wait completed after {wait_time} seconds.")
        return current_index + 1, current_timestamp

    checkpoint_match = action.startswith("Checkpoint: ")
    if checkpoint_match:
        page1.dynamic_text.set(f"line: {current_index} - " + action)
        checkpoint_name = action.split("Checkpoint: ")[1]
        print(f"Reached Checkpoint: {checkpoint_name}")
        return current_index + 1, current_timestamp

    print(f"Unrecognized event format: {action}")
    return current_index + 1, current_timestamp

def execute_macro_logic_wrapper(action, page1, current_index, variables, previous_timestamp=None):
    """Wrapper for execute_macro_logic with error handling."""
    try:
        next_index, new_timestamp = execute_macro_logic(action, page1, current_index, variables, previous_timestamp)
        return next_index, new_timestamp
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Unexpected error in execute_macro_logic: {type(e).__name__}: {e}\nStack trace:\n{error_trace}")
        page1.running = False
        return current_index, previous_timestamp