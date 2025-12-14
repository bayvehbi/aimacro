"""
Configuration management for the application.
Handles loading and saving of application settings.
"""
import os
import json
try:
    from ..utils.logger import verbose, info
except ImportError:
    # Logger not available yet, use print as fallback
    def verbose(msg): pass
    def info(msg): print(msg)


def load_api_settings():
    """
    Load API settings from storage/settings.json.
    
    Returns:
        dict: Settings dictionary with all configuration values.
              Returns default settings if file doesn't exist or on error.
    """
    settings_file = os.path.join("storage", "settings.json")
    default_settings = {
        "start_macro_record_shortcut": "r",
        "stop_macro_record_shortcut": "s",
        "start_macro_run_shortcut": "p",
        "stop_macro_run_shortcut": "q",
        "chatgpt_api_key": "",
        "grok_api_key": "",
        "azure_api_key": "",  # Default Azure API key
        "azure_endpoint": "",  # Default Azure endpoint
        "azure_subscription_key": "",  # Default Azure subscription key
        "verbose_mode": False,  # Enable verbose logging/debug output
    }

    os.makedirs("storage", exist_ok=True)

    try:
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                settings = json.load(f)
            # Ensure all keys exist (for backward compatibility)
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=4)
            verbose(f"Settings loaded from {settings_file}")
            return settings
        else:
            with open(settings_file, "w") as f:
                json.dump(default_settings, f, indent=4)
            info(f"Default settings created at {settings_file}")
            return default_settings
    except Exception as e:
        info(f"Error loading settings: {e}, using default settings")
        return default_settings

