import time
import threading
from pynput import keyboard as pynput_keyboard, mouse as pynput_mouse
from pynput.keyboard import Key

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
            print("Recording started, appending to existing events...")

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
            print("Recording stopped")

    def start_macro(self):
        """Start executing the recorded macro."""
        print(f"user input {self.page1.run_times.get()}")
        if not self.page1.running:
            self.page1.running = True
            self.page1.run_button.config(state="disabled")
            self.page1.stop_run_button.config(state="normal")
            threading.Thread(target=self.execute_macro, daemon=True).start()
            print("Macro started")
            print("Treeview content before macro starts:", [self.page1.left_treeview.item(child, "text") for child in self.page1.left_treeview.get_children()])

    def stop_macro(self):
        """Stop the executing macro."""
        self.page1.running = False
        self.page1.run_continuously.set(False)
        self.page1.run_button.config(state="normal")
        self.page1.stop_run_button.config(state="disabled")
        print("Macro stopped")

    def execute_macro(self):
        """Execute the recorded macro event s."""
        from misc import execute_macro_logic_wrapper as execute_macro_logic
        self.events = [self.page1.left_treeview.item(item)["text"] for item in self.page1.left_treeview.get_children()]
        print("self.events content:", self.events)
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
        print("Macro execution completed.")

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
        self.ctrl_pressed = False
        self.global_listener = pynput_keyboard.Listener(on_press=self.on_global_key_press, on_release=self.on_global_key_release)
        self.global_listener.start()

    def on_global_key_press(self, key):
        """Handle global key press events with shortcut detection."""
        try:
            key_char = getattr(key, 'char', None)
            key_vk = getattr(key, 'vk', None)
            key_name = str(key)
            print(f"Pressed key: char={key_char}, vk={key_vk}, name={key_name}, ctrl_pressed={self.ctrl_pressed}")

            if key in (Key.ctrl_l, Key.ctrl_r):
                self.ctrl_pressed = True
                print("Ctrl pressed")
                return

            if self.ctrl_pressed and key_vk:
                key_str = chr(key_vk).lower()
                if key_str == self.page1.start_recording_key and not self.page1.recording:
                    print(f"'Ctrl + {key_str}' pressed, starting recording...")
                    self.page1.start_recording()
                elif key_str == self.page1.stop_recording_key and self.page1.recording:
                    print(f"'Ctrl + {key_str}' pressed, stopping recording...")
                    self.page1.stop_recording()
                elif key_str == self.page1.start_macro_key and not self.page1.running:
                    print(f"'Ctrl + {key_str}' pressed, starting macro...")
                    self.page1.start_macro()
                elif key_str == self.page1.stop_macro_key and self.page1.running:
                    print(f"'Ctrl + {key_str}' pressed, stopping macro...")
                    self.page1.stop_macro()

        except Exception as e:
            print(f"Error: {e}")

    def on_global_key_release(self, key):
        """Handle global key release events."""
        if key in (Key.ctrl_l, Key.ctrl_r):
            self.ctrl_pressed = False
            print("Ctrl released")

# Aşağıdaki fonksiyonlar Windows’a özel, bu nedenle yorum satırı olarak bırakıldı
"""
def get_monitors():
    # Windows-specific monitor detection
    monitors = []
    i = 0
    while True:
        try:
            monitor_info = win32api.EnumDisplayDevices(None, i)
            monitor_settings = win32api.EnumDisplaySettings(monitor_info.DeviceName, win32con.ENUM_CURRENT_SETTINGS)
            monitors.append({
                "device_name": monitor_info.DeviceName,
                "width": monitor_settings.PelsWidth,
                "height": monitor_settings.PelsHeight,
                "x": monitor_settings.Position_x,
                "y": monitor_settings.Position_y
            })
            i += 1
        except:
            break
    return monitors

def update_monitor_info(selected_monitor, monitors, canvas):
    # Update monitor preview on canvas
    if selected_monitor is not None:
        monitor = monitors[selected_monitor]
        with mss.mss() as sct:
            monitor_region = {
                "top": monitor["y"],
                "left": monitor["x"],
                "width": monitor["width"],
                "height": monitor["height"]
            }
            screenshot = sct.grab(monitor_region)
            img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            img = img.resize((canvas_width, canvas_height), Image.LANCZOS)
            screenshot_tk = ImageTk.PhotoImage(img)
            canvas.create_image(0, 0, anchor=tk.NW, image=screenshot_tk)
            canvas.image = screenshot_tk

def on_monitor_select(event, monitor_listbox, monitors, monitor_canvas, monitor_info_label):
    # Handle monitor selection event
    selected_monitor = monitor_listbox.curselection()
    if selected_monitor:
        selected_monitor = int(selected_monitor[0])
        update_monitor_info(selected_monitor, monitors, monitor_canvas)
    else:
        monitor_info_label.config(text="Monitor Selected.")
"""