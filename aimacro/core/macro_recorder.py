"""Macro recording and execution functionality."""
import time
import threading
from pynput import keyboard as pynput_keyboard, mouse as pynput_mouse
from pynput.keyboard import Key
from ..utils.logger import verbose, info, error


class MacroRecorder:
    def __init__(self, page1):
        super().__init__()
        self.page1 = page1
        self.events = []
        self.keyboard_listener = None
        self.mouse_listener = None
        self.start_time = None
        self.last_mouse_move_time = 0

    def start_recording(self):
        """Start recording mouse and keyboard events."""
        if not self.page1.recording:
            self.page1.recording = True
            self.start_time = time.time()
            self.last_mouse_move_time = self.start_time
            self.keyboard_listener = pynput_keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
            self.keyboard_listener.start()
            self.mouse_listener = pynput_mouse.Listener(
                on_move=self.on_mouse_move,
                on_click=self.on_mouse_click,
                on_scroll=self.on_mouse_scroll
            )
            self.mouse_listener.start()
            self.page1.start_button.config(state="disabled")
            self.page1.stop_button.config(state="normal")
            info("Recording started, appending to existing events...")

    def stop_recording(self):
        """Stop recording mouse and keyboard events."""
        if self.page1.recording:
            self.page1.recording = False
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            if self.mouse_listener:
                self.mouse_listener.stop()
            self.page1.start_button.config(state="normal")
            self.page1.stop_button.config(state="disabled")
            info("Recording stopped")

    def start_macro(self):
        """Start executing the recorded macro."""
        if not self.page1.running:
            self.page1.running = True
            self.page1.run_button.config(state="disabled")
            self.page1.stop_run_button.config(state="normal")
            threading.Thread(target=self.execute_macro, daemon=True).start()
            info("Macro started")
            # print("Treeview content before macro starts:", [self.page1.left_treeview.item(child, "text") for child in self.page1.left_treeview.get_children()])

    def stop_macro(self):
        """Stop the executing macro."""
        self.page1.running = False
        self.page1.run_continuously.set(False)
        self.page1.run_button.config(state="normal")
        self.page1.stop_run_button.config(state="disabled")
        info("Macro stopped")

    def execute_macro(self):
        """Execute the recorded macro event s."""
        from .macro_executor import execute_macro_logic_wrapper as execute_macro_logic
        self.events = [self.page1.left_treeview.item(item)["text"] for item in self.page1.left_treeview.get_children()]
        # print("self.events content:", self.events)
        current_index = 0
        run_count = 1
        previous_timestamp = None
        while self.page1.running and current_index < len(self.events):
            action = self.events[current_index]
            current_index, previous_timestamp = execute_macro_logic(action, self.page1, current_index, self.page1.variables, previous_timestamp)
            if int(self.page1.run_times.get() if self.page1.run_times.get() else 1) > run_count and current_index >= len(self.events):
                run_count += 1
                current_index = 0
                previous_timestamp = None  # Reset timestamp for continuous run
        self.page1.running = False
        self.page1.run_button.config(state="normal")
        self.page1.stop_run_button.config(state="disabled")
        info("Macro execution completed.")

    def on_key_press(self, key):
        """Handle key press events during recording."""
        if self.page1.recording:
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            try:
                event = f"{elapsed_time:.3f} - Key pressed: {key.char}"
            except AttributeError:
                event = f"{elapsed_time:.3f} - Key pressed: {key}"
            self.events.append(event)
            self.page1.add_event_to_treeview(event)

    def on_key_release(self, key):
        """Handle key release events during recording."""
        if self.page1.recording:
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            event = f"{elapsed_time:.3f} - Key released: {key}"
            self.events.append(event)
            self.page1.add_event_to_treeview(event)

    def on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events during recording."""
        if self.page1.recording:
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            direction = "up" if dy > 0 else "down"
            event = f"{elapsed_time:.3f} - Mouse scrolled {direction} at: ({x}, {y})"
            self.events.append(event)
            self.page1.add_event_to_treeview(event)

    def on_mouse_move(self, x, y):
        """Handle mouse move events during recording with a throttle."""
        if self.page1.recording:
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            if current_time - self.last_mouse_move_time >= 0.05:  # Throttle to 50ms
                event = f"{elapsed_time:.3f} - Mouse moved to: ({x}, {y})"
                self.events.append(event)
                self.page1.add_event_to_treeview(event)
                self.last_mouse_move_time = current_time

    def on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events during recording."""
        if self.page1.recording:
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            action = "pressed" if pressed else "released"
            button_str = str(button).replace("Button.", "")
            event = f"{elapsed_time:.3f} - Mouse Button.{button_str} {action} at: ({x}, {y})"
            self.events.append(event)
            self.page1.add_event_to_treeview(event)


class ShortcutHandler:
    def __init__(self, page1):
        self.page1 = page1
        self.pressed_keys = set()
        self.global_listener = pynput_keyboard.Listener(
            on_press=self.on_global_key_press,
            on_release=self.on_global_key_release
        )
        self.global_listener.start()

    def on_global_key_press(self, key):
        try:
            if key in self.pressed_keys:
                return  # Skip repeated holding
            self.pressed_keys.add(key)

            key_char = getattr(key, 'char', None)

            if not key_char:
                return

            # Normalize input key
            pressed = key_char.lower().strip()

            # Fetch normalized shortcut keys from page1
            shortcuts = {
                self.page1.start_recording_key.lower().strip(): self.page1.start_recording,
                self.page1.stop_recording_key.lower().strip(): self.page1.stop_recording,
                self.page1.start_macro_key.lower().strip(): self.page1.start_macro,
                self.page1.stop_macro_key.lower().strip(): self.page1.stop_macro,
            }

            # Check and trigger action
            if pressed in shortcuts:
                action = shortcuts[pressed]
                if callable(action):
                    # Check state guards
                    if action == self.page1.start_recording and not self.page1.recording:
                        action()
                    elif action == self.page1.stop_recording and self.page1.recording:
                        action()
                    elif action == self.page1.start_macro and not self.page1.running:
                        action()
                    elif action == self.page1.stop_macro and self.page1.running:
                        action()

        except Exception as e:
            error(f"Error in shortcut handler: {e}")

    def on_global_key_release(self, key):
        self.pressed_keys.discard(key)

