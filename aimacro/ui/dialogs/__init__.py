"""
Dialog windows for user input.
"""

def bind_enter_key(window, callback, focus_widget=None):
    """Bind Enter key to callback and optionally set focus on a widget."""
    window.bind("<Return>", lambda e: callback())
    if focus_widget:
        focus_widget.focus_set()
