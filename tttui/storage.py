import os
import json
from . import config

CONFIG_DIR = os.path.expanduser("~/.config/tttui")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_CONFIG = {
    "user_preferences": {
        "language": "english",
        "theme": "default",
    },
    "personal_bests": {},
}


def _ensure_config_file():
    """Ensure the config directory and file exist."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)


def load_config():
    """Load the user's configuration from the JSON file."""
    _ensure_config_file()
    try:
        with open(CONFIG_FILE, "r") as f:
            loaded_config = json.load(f)
            config = DEFAULT_CONFIG.copy()
            config.update(loaded_config)
            return config
    except (json.JSONDecodeError, IOError):
        return DEFAULT_CONFIG


def save_config(config_data):
    """Save the user's configuration to the JSON file."""
    _ensure_config_file()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=2)


def get_pb(all_pbs, test_key):
    """Get the personal best for a specific test key."""
    return all_pbs.get(test_key)


def ensure_dirs():
    """Ensure languages and quotes directories exist."""
    os.makedirs(config.LANGUAGES_DIR, exist_ok=True)
    os.makedirs(config.QUOTES_DIR, exist_ok=True)


def get_available_languages():
    """Dynamically find available language files."""
    if not os.path.exists(config.LANGUAGES_DIR):
        return ["english"]
    return [
        f.replace(".txt", "")
        for f in os.listdir(config.LANGUAGES_DIR)
        if f.endswith(".txt")
    ] or ["english"]


def load_items(item_type, language):
    """Generic function to load words or quotes from a file."""
    dir_path = config.LANGUAGES_DIR if item_type == "words" else config.QUOTES_DIR
    file_path = os.path.join(dir_path, f"{language}.txt")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            items = [line.strip() for line in f if line.strip()]
        return items if items else [f"No {item_type} found for {language}"]
    except FileNotFoundError:
        return [f"No {item_type} file for {language}"]
