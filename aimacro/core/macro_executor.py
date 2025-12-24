"""Macro execution logic - processes macro events and executes actions."""
import time
import re
import datetime
import os
import ast
import base64
import traceback
from io import BytesIO

from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse
import pyautogui

# Import patterns
from .event_patterns import (
    TIMESTAMP_PATTERN,
    KEY_PRESS_PATTERN,
    KEY_RELEASE_PATTERN,
    MOUSE_MOVE_PATTERN,
    MOUSE_SCROLL_PATTERN,
    MOUSE_LEFT_PRESS_PATTERN,
    MOUSE_LEFT_RELEASE_PATTERN,
    MOUSE_RIGHT_PRESS_PATTERN,
    MOUSE_RIGHT_RELEASE_PATTERN,
    OCR_PATTERN,
    SEARCH_PATTERN,
    IF_PATTERN,
    WAIT_PATTERN,
    GOTO_PATTERN,
)

# Import services
from ..services.ai_services import send_to_chatgpt, send_to_azure, send_to_local_ocr
from ..services.notification_service import send_notification

# Import utilities
from ..utils.pattern_utils import search_for_pattern, unpack_coords, load_image, image_to_base64
from ..utils.image_utils import upscale_min_size
from ..utils.logger import verbose, info, error


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
        verbose(f"Parsed timestamp: {current_timestamp}, action: {event_action}")
        action = event_action

        # Wait for the time difference between previous and current event
        if previous_timestamp is not None:
            time_diff = current_timestamp - previous_timestamp
            if time_diff > 0:
                verbose(f"Waiting {time_diff:.3f} seconds before executing...")
                time.sleep(time_diff)

    # Handle key press events
    key_press_match = KEY_PRESS_PATTERN.match(action)
    if key_press_match:
        page1.dynamic_text.set(f"line: {current_index} - " + key_press_match.string)
        key = key_press_match.group(1)
        try:
            if key.startswith("'") and key.endswith("'"):  # Single character keys: 'a', 's', 'd'
                kb_controller.press(key[1])
                verbose(f"Pressed key: {key}")
            elif key.startswith("Key."):  # Special keys: Key.alt_l, Key.tab
                key_name = key.replace("Key.", "")
                kb_controller.press(getattr(pynput_keyboard.Key, key_name))
                verbose(f"Pressed key: {key}")
            else:  # Plain single character keys: a, s, d
                kb_controller.press(key)
                verbose(f"Pressed key: {key}")
        except AttributeError:
            error(f"Key not recognized: {key}")
        return current_index + 1, current_timestamp

    # Handle key release events
    key_release_match = KEY_RELEASE_PATTERN.match(action)
    if key_release_match:
        page1.dynamic_text.set(f"line: {current_index} - " + key_release_match.string)
        key = key_release_match.group(1)
        try:
            if key.startswith("'") and key.endswith("'"):  # Single character keys: 'a', 's', 'd'
                kb_controller.release(key[1])
                verbose(f"Released key: {key}")
            elif key.startswith("Key."):  # Special keys: Key.alt_l, Key.tab
                key_name = key.replace("Key.", "")
                kb_controller.release(getattr(pynput_keyboard.Key, key_name))
                verbose(f"Released key: {key}")
            else:  # Plain single character keys: a, s, d
                kb_controller.release(key)
                verbose(f"Released key: {key}")
        except AttributeError:
            error(f"Key not recognized: {key}")
        return current_index + 1, current_timestamp

    mouse_move_match = MOUSE_MOVE_PATTERN.match(action)
    if mouse_move_match:
        page1.dynamic_text.set(f"line: {current_index} - " + mouse_move_match.string)
        x, y = map(int, mouse_move_match.groups())
        mouse_controller.position = (x, y)
        verbose(f"Moved mouse to: ({x}, {y})")
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
        verbose(f"Scrolled {direction} at: ({x}, {y})")
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
        verbose(f"Left click pressed at: {pos}")
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
        verbose(f"Left click released at: {pos}")
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
        verbose(f"Right click pressed at: {pos}")
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
        verbose(f"Right click released at: {pos}")
        return current_index + 1, current_timestamp

    verbose(f"Action after timestamp parsing: {action}")
    action = action.strip()  # Remove leading/trailing whitespace

    # Use .search instead of .match for more tolerance
    ocr_match = OCR_PATTERN.search(action)
    if ocr_match:
        page1.dynamic_text.set(f"line: {current_index} - " + ocr_match.string)
        provider, feature, coords_str, variable_name, variable_content = ocr_match.groups()

        # Safe parse
        try:
            coords = ast.literal_eval(coords_str)
        except Exception as e:
            error(f"Area parse error: {e} -> coords_str={coords_str!r}")
            return current_index + 1, previous_timestamp

        variable_content = (variable_content or "").strip()

        x1, y1 = coords['start']
        x2, y2 = coords['end']

        screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
        buffered = BytesIO()
        os.makedirs("./logs", exist_ok=True)
        screenshot.save(buffered, format="PNG")
        screenshot.save("./logs/ocr.png")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        img_str = upscale_min_size(img_str, min_size=(50, 50))

        # Route to appropriate provider based on selection
        if provider.lower() == "azure":
            text = send_to_azure(img_str, page1.master.master.settings, feature=feature)
        elif provider.lower() == "chatgpt":
            # Use the variable_content as prompt for ChatGPT
            prompt = variable_content if variable_content else "What's in this image?"
            text = send_to_chatgpt(img_str, page1.master.master.settings, prompt=prompt)
        elif provider.lower() in ("local ocr", "local_ocr", "local"):
            # Local OCR doesn't use feature or prompt, just extracts text
            text = send_to_local_ocr(img_str, page1.master.master.settings)
        else:
            text = f"Unknown provider: {provider}"
        
        verbose(f"AI Result: {text}")

        if variable_name:
            # If you want to use Variable Content directly:
            # page1.variables[variable_name] = variable_content or text
            # Otherwise, write the OCR result:
            page1.variables[variable_name] = text
            verbose(f"OCR result '{text}' saved to variable '{variable_name}'")
            verbose(f"Current variables: {page1.variables}")
            page1.page2.update_variables_list()

        if any(bad in str(text) for bad in ("API request failed", "JSON parsing error")):
            error(f"OCR failed, stopping macro...")
            page1.running = False
        else:
            verbose("OCR found text, continuing macro...")

        return current_index + 1, previous_timestamp

    search_match = SEARCH_PATTERN.match(action)
    if search_match:
        page1.dynamic_text.set(f"line: {current_index} - " + search_match.string)
        img_str, search_coords_str, succeed_checkpoint, fail_checkpoint, click_if_found, wait_time, threshold_str, scene_change, succeed_notification_name, fail_notification_name = search_match.groups()
        verbose(f"Parsed Search event: Image={img_str[:25]}, Search Area={search_coords_str}, Succeed Go To={succeed_checkpoint}, Fail Go To={fail_checkpoint}, Click={click_if_found}, Wait={wait_time}, Threshold={threshold_str}")
        try:
            wait_time = float(wait_time)
            threshold = float(threshold_str) if threshold_str.replace('.', '').isdigit() else 0.7
            search_coords = eval(search_coords_str) if search_coords_str != 'Full Screen' else 'Full Screen'
            click_if_found = click_if_found == 'True'

            verbose("Calling search_for_pattern...")
            pattern_found = search_for_pattern(img_str, search_coords, page1.master.master.settings, page1=page1, click_if_found=click_if_found, wait_time=wait_time, threshold=threshold)
            verbose(f"search_for_pattern returned: {pattern_found}")
            target_checkpoint = succeed_checkpoint if pattern_found else fail_checkpoint
            verbose(f"Pattern {'found' if pattern_found else 'not found'}, going to '{target_checkpoint}'...")

            # Send notification based on pattern result
            if pattern_found and succeed_notification_name:
                verbose(f"Attempting to send succeed notification: {succeed_notification_name}")
                send_notification(succeed_notification_name, page1)
            elif not pattern_found and fail_notification_name:
                verbose(f"Attempting to send fail notification: {fail_notification_name}")
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
                    verbose(f"Jumping to checkpoint index: {next_index}")
                    return next_index, current_timestamp
                error(f"Checkpoint '{target_checkpoint}' not found, stopping macro...")
                page1.running = False
                return current_index, current_timestamp
            return current_index + 1, current_timestamp

        except ValueError as e:
            error(f"Error parsing numeric values: {e}")
            return current_index + 1, current_timestamp

    if_match = IF_PATTERN.match(action)
    if if_match:
        page1.dynamic_text.set(f"line: {current_index} - " + if_match.string)
        variable_name, condition, value, succeed_checkpoint, fail_checkpoint, succeed_notification_name, fail_notification_name = if_match.groups()
        verbose(f"Parsed If event: Variable={variable_name}, Condition={condition}, Value={value}, Succeed Go To={succeed_checkpoint}, Fail Go To={fail_checkpoint}")
        now = datetime.datetime.now()
        # Update time variables in page1.variables to ensure consistency
        page1.variables["time_hour"] = now.hour
        page1.variables["time_minute"] = now.minute
        page1.variables["time_second"] = now.second
        page1.variables["time_weekday"] = now.weekday()
        page1.variables["time_day"] = now.day
        page1.variables["time_month"] = now.month
        page1.variables["time_year"] = now.year
        # Always get variable from page1.variables directly to ensure we have the latest value
        variable_value = page1.variables.get(variable_name)
        
        if variable_value is None:
            verbose(f"Variable '{variable_name}' not found in variables: {page1.variables}, skipping If condition.")
            return current_index + 1, current_timestamp
        verbose(f"variable_value: {variable_value} - value: {value}")
        condition_met = False
        if condition == "==":
            try:
                # Support: evaluate expressions like time_minute % 5 == 0
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
            # Remove spaces and make case-insensitive for comparison
            value_normalized = str(value).replace(" ", "").lower()
            variable_normalized = str(variable_value).replace(" ", "").lower()
            condition_met = value_normalized in variable_normalized
        elif condition == "%":
            try:
                condition_met = int(variable_value) % int(value) == 0
            except:
                condition_met = False

        target_checkpoint = succeed_checkpoint if condition_met else fail_checkpoint
        verbose(f"Condition {'met' if condition_met else 'not met'}, going to '{target_checkpoint}'...")

        # Send notification based on condition result
        if condition_met and succeed_notification_name:
            verbose(f"Attempting to send succeed notification: {succeed_notification_name}")
            send_notification(succeed_notification_name, page1)
        elif not condition_met and fail_notification_name:
            verbose(f"Attempting to send fail notification: {fail_notification_name}")
            send_notification(fail_notification_name, page1)

        if target_checkpoint != "Next":
            next_index = page1.get_checkpoint_index(target_checkpoint)
            if next_index is not None:
                verbose(f"Jumping to checkpoint index: {next_index}")
                return next_index, current_timestamp
            error(f"Checkpoint '{target_checkpoint}' not found, stopping macro...")
            page1.running = False
            return current_index, current_timestamp
        return current_index + 1, current_timestamp

    wait_match = WAIT_PATTERN.match(action)
    if wait_match:
        wait_time = float(wait_match.group(1))
        verbose(f"Waiting for {wait_time} seconds...")
        for i in range(int(wait_time)):
            page1.dynamic_text.set(f"line: {current_index} - " + f"waiting: {wait_time-i}")
            time.sleep(1)
            if page1 and not page1.running:
                page1.running = False
                return current_index, previous_timestamp
    
        verbose(f"Wait completed after {wait_time} seconds.")
        return current_index + 1, current_timestamp

    goto_match = GOTO_PATTERN.match(action)
    if goto_match:
        page1.dynamic_text.set(f"line: {current_index} - " + action)
        goto_type, target, element_text = goto_match.groups()
        
        if goto_type == "Checkpoint":
            checkpoint_name = target.strip()
            next_index = page1.get_checkpoint_index(checkpoint_name)
            if next_index is not None:
                verbose(f"Jumping to checkpoint '{checkpoint_name}' at index: {next_index}")
                return next_index, current_timestamp
            else:
                error(f"Checkpoint '{checkpoint_name}' not found, stopping macro...")
                page1.running = False
                return current_index, current_timestamp
        else:  # Line
            try:
                line_num = int(target.strip())
                children = page1.left_treeview.get_children()
                if 0 <= line_num < len(children):
                    # Optional: Verify element hasn't changed
                    if element_text:
                        current_element = page1.left_treeview.item(children[line_num])["text"]
                        if current_element != element_text:
                            verbose(f"WARNING: Element at line {line_num} has changed from saved value")
                    verbose(f"Jumping to line {line_num}")
                    return line_num, current_timestamp
                else:
                    error(f"Line number {line_num} is out of range, continuing to next event...")
                    return current_index + 1, current_timestamp
            except ValueError:
                error(f"Invalid line number '{target}', continuing to next event...")
                return current_index + 1, current_timestamp

    checkpoint_match = action.startswith("Checkpoint: ")
    if checkpoint_match:
        page1.dynamic_text.set(f"line: {current_index} - " + action)
        checkpoint_name = action.split("Checkpoint: ")[1]
        verbose(f"Reached Checkpoint: {checkpoint_name}")
        return current_index + 1, current_timestamp

    verbose(f"Unrecognized event format: {action}")
    return current_index + 1, current_timestamp


def execute_macro_logic_wrapper(action, page1, current_index, variables, previous_timestamp=None):
    """Wrapper for execute_macro_logic with error handling."""
    try:
        next_index, new_timestamp = execute_macro_logic(action, page1, current_index, variables, previous_timestamp)
        return next_index, new_timestamp
    except Exception as e:
        error_trace = traceback.format_exc()
        error(f"Unexpected error in execute_macro_logic: {type(e).__name__}: {e}\nStack trace:\n{error_trace}")
        page1.running = False
        return current_index, previous_timestamp

