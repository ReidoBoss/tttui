import random
from . import storage


def reset_game(config):
    """Initializes a new game state."""
    language = config.get("language", "english")
    mode = config["mode"]

    if mode == "quote":
        items = storage.load_items("quotes", language)
        target_text = random.choice(items) if items else "No quotes found."
    else:
        items = storage.load_items("words", language)
        random.shuffle(items)
        if mode == "time":
            target_text = " ".join(items * 3)
        else:
            target_text = " ".join(items[: config.get("value", 25)])

    lines, current_line, line_width = [], "", 80
    for word in target_text.split(" "):
        if len(current_line) + len(word) + 1 > line_width:
            lines.append(current_line)
            current_line = word
        else:
            current_line += (" " if current_line else "") + word
    lines.append(current_line)

    return {
        "config": config,
        "target_text": target_text,
        "lines": lines,
        "current_line_idx": 0,
        "current_text": "",
        "start_time": 0,
        "time_elapsed": 0,
        "started": False,
        "test_focus": "text",
        "command_options": ["reset", "menu"],
        "selected_command_idx": 0,
        "total_typed_chars": 0,
        "errors": 0,
    }


def calculate_results(state):
    """Calculates final results."""
    time_elapsed = state["time_elapsed"]
    errors, total_typed = state["errors"], state["total_typed_chars"]
    correct_chars = total_typed - errors
    accuracy = (correct_chars / total_typed) * 100 if total_typed > 0 else 0
    net_wpm = (correct_chars / 5) / (time_elapsed / 60) if time_elapsed > 0 else 0
    return {"wpm": net_wpm, "acc": accuracy, "errors": errors}
