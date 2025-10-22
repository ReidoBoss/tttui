import os
from . import config


def ensure_dirs():
    """Ensure languages and quotes directories exist."""
    os.makedirs(config.LANGUAGES_DIR, exist_ok=True)
    os.makedirs(config.QUOTES_DIR, exist_ok=True)


def get_available_languages():
    """Dynamically find available language files."""
    if not os.path.exists(config.LANGUAGES_DIR):
        return ["english"]  # Default
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


def add_item(item_type, language, item):
    """Add a word or quote to the appropriate file."""
    dir_path = config.LANGUAGES_DIR if item_type == "words" else config.QUOTES_DIR
    file_path = os.path.join(dir_path, f"{language}.txt")
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"\n{item}")


def remove_item(item_type, language, item_to_remove):
    """Remove a word or quote from the appropriate file."""
    dir_path = config.LANGUAGES_DIR if item_type == "words" else config.QUOTES_DIR
    file_path = os.path.join(dir_path, f"{language}.txt")
    try:
        items = load_items(item_type, language)
        if item_to_remove in items:
            items.remove(item_to_remove)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(items))
            return True
    except Exception:
        return False
    return False
