"""
Notification service integrations.
Currently supports Pushover API.
"""
import http.client
import urllib.parse


def send_notification(notification_name, page1):
    """
    Send a notification via Pushover API.
    
    Args:
        notification_name: Name of the notification configuration
        page1: Page1 instance to access notification settings
        
    Returns:
        None (prints status messages)
    """
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

