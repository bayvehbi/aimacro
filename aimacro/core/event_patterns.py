"""Regex patterns for parsing macro events."""
import re

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
OCR_PATTERN = re.compile(
    r"Image AI - Provider:\s*(.+?),\s*"
    r"Feature:\s*(.+?),\s*"
    r"Area:\s*(\{.*?\}),\s*"
    r"Variable:\s*(\w+),\s*"
    r"Variable Content:\s*(.*)",
    re.DOTALL
)
SEARCH_PATTERN = re.compile(r"Search Pattern - Image: (.+?), Search Area: (.+?), Succeed Go To: (.+?), Fail Go To: (.+?), Click: (True|False), Wait: (\d+\.\d+)s, Threshold: (\d+\.\d+), Scene Change: (True|False)(?:, Succeed Notification: ([\w-]+))?(?:, Fail Notification: ([\w-]+))?")
IF_PATTERN = re.compile(r"If - Variable:\s*(\w+),\s*Condition:\s*([><=!%]+|Contains),\s*Value:\s*(.+?),\s*Succeed Go To:\s*(.+?),\s*Fail Go To:\s*(.+?),\s*Wait:\s*(\d+\.\d+)s(?:,\s*Succeed Notification:\s*([\w-]+))?(?:,\s*Fail Notification:\s*([\w-]+))?")
WAIT_PATTERN = re.compile(r"Wait: (\d+\.\d+)s")
GOTO_PATTERN = re.compile(r"Go To - (Checkpoint|Line): (.+?)(?:, Element: (.+))?$")

