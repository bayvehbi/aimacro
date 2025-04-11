import tkinter as tk
from tkinter import ttk, Toplevel, Label, Entry, OptionMenu, StringVar, Button
import http.client
import urllib.parse
import json
import os

class Page2(tk.Frame):
    def __init__(self, master, page1):
        super().__init__(master)
        self.page1 = page1  # Reference to Page1 for accessing variables and checkpoints
        self.notifications = {}  # Dictionary to store notifications

    def setup_ui(self):
        """Set up the UI elements for Page2."""
        # Top frame for variables and notifications lists
        top_frame = tk.Frame(self)
        top_frame.pack(side=tk.TOP, padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Variables list section
        variables_frame = tk.LabelFrame(top_frame, text="Variables")
        variables_frame.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

        self.variables_listbox = tk.Listbox(variables_frame, height=10)
        self.variables_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar_var = ttk.Scrollbar(variables_frame, orient="vertical", command=self.variables_listbox.yview)
        scrollbar_var.pack(side=tk.RIGHT, fill=tk.Y)
        self.variables_listbox.config(yscrollcommand=scrollbar_var.set)
        self.update_variables_list()

        # Notifications list section
        notifications_frame = tk.LabelFrame(top_frame, text="Notifications")
        notifications_frame.pack(side=tk.RIGHT, padx=5, fill=tk.BOTH, expand=True)

        self.notifications_listbox = tk.Listbox(notifications_frame, height=10)
        self.notifications_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar_notif = ttk.Scrollbar(notifications_frame, orient="vertical", command=self.notifications_listbox.yview)
        scrollbar_notif.pack(side=tk.RIGHT, fill=tk.Y)
        self.notifications_listbox.config(yscrollcommand=scrollbar_notif.set)

        # Bottom frame for buttons
        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, padx=10, pady=5, fill=tk.X)

        add_button = ttk.Button(button_frame, text="Add Notification", command=self.open_add_notification_window)
        add_button.pack(side=tk.LEFT, padx=5)

        test_button = ttk.Button(button_frame, text="Test Selected Notification", command=self.test_notification)
        test_button.pack(side=tk.LEFT, padx=5)

        self.update_notifications_list()

    def update_variables_list(self):
        """Update the variables listbox with current values."""
        self.variables_listbox.delete(0, tk.END)
        for name, value in self.page1.variables.items():
            self.variables_listbox.insert(tk.END, f"{name}: {value}")

    def update_notifications_list(self):
        """Update the notifications listbox with current notifications."""
        self.notifications_listbox.delete(0, tk.END)
        for name, details in self.notifications.items():
            self.notifications_listbox.insert(tk.END, f"{name}: Priority {details['priority']}")

    def open_add_notification_window(self):
        """Open the window to add a new notification."""
        window = Toplevel(self)
        window.title("Add Notification")
        window.geometry("400x400")
        window.attributes("-topmost", True)

        Label(window, text="Notification Name:").pack(pady=5)
        name_entry = Entry(window)
        name_entry.pack(pady=5)

        Label(window, text="Pushover Token:").pack(pady=5)
        token_entry = Entry(window)
        # No longer fetching from settings, keeping it blank
        token_entry.pack(pady=5)

        Label(window, text="Pushover User:").pack(pady=5)
        user_entry = Entry(window)
        # No longer fetching from settings, keeping it blank
        user_entry.pack(pady=5)

        Label(window, text="Priority:").pack(pady=5)
        priority_var = StringVar(value="Normal (0)")
        priority_dropdown = OptionMenu(window, priority_var, "Normal (0)", "Emergency (2)")
        priority_dropdown.pack(pady=5)

        Label(window, text="Message:").pack(pady=5)
        message_entry = Entry(window)
        message_entry.pack(pady=5)

        def save_notification():
            """Save the new notification to the dictionary."""
            name = name_entry.get().strip()
            token = token_entry.get().strip()
            user = user_entry.get().strip()
            priority = 0 if priority_var.get() == "Normal (0)" else 2
            message = message_entry.get().strip()

            if not name or not token or not user or not message:
                print("All fields (Name, Token, User, Message) must be filled.")
                return

            self.notifications[name] = {
                "token": token,
                "user": user,
                "priority": priority,
                "message": message
            }
            self.update_notifications_list()
            print(f"Notification '{name}' added: {self.notifications[name]}")
            window.destroy()

        Button(window, text="Save", command=save_notification).pack(pady=10)

    def test_notification(self):
        """Test and send the selected notification."""
        selected = self.notifications_listbox.curselection()
        if not selected:
            print("No notification selected to test.")
            return
        
        name = self.notifications_listbox.get(selected[0]).split(":")[0].strip()
        if name not in self.notifications:
            print(f"Notification '{name}' not found.")
            return

        notification = self.notifications[name]
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        params = {
            "token": notification["token"],
            "user": notification["user"],
            "message": notification["message"],
            "sound": "vibrate",
            "priority": notification["priority"]
        }
        if notification["priority"] == 2:
            params.update({"expire": 60, "retry": 60})

        try:
            conn.request("POST", "/1/messages.json",
                         urllib.parse.urlencode(params),
                         {"Content-type": "application/x-www-form-urlencoded"})
            response = conn.getresponse()
            if response.status == 200:
                print(f"Test notification '{name}' sent successfully.")
            else:
                print(f"Failed to send test notification '{name}': {response.status} - {response.reason}")
        except Exception as e:
            print(f"Error sending test notification '{name}': {e}")
        finally:
            conn.close()