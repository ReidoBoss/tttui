import random
import statistics
from . import storage


def reset_game(config):
    """Initializes a new game state with performance tracking."""
    language = config.get("language", "english")
    mode = config["mode"]

    if mode == "quote":
        items = storage.load_items("quotes", language)
        target_text = random.choice(items) if items else "No quotes found."
    else:
        items = storage.load_items("words", language)
        random.shuffle(items)
        if mode == "time":
            target_text = " ".join(items * 10)
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
        "extra_chars": {},
        "line_char_counts": [len(line) for line in lines],
        "wpm_history": [],
        "last_wpm_record_time": 0,
    }


def calculate_results(state, personal_best):
    """Calculates final results and determines if it's a new PB."""
    time_elapsed = state["time_elapsed"]
    errors = state["errors"]
    total_typed = state["total_typed_chars"]
    correct_chars = total_typed - errors

    net_wpm = (correct_chars / 5) / (time_elapsed / 60) if time_elapsed > 0 else 0
    raw_wpm = (total_typed / 5) / (time_elapsed / 60) if time_elapsed > 0 else 0
    accuracy = (correct_chars / total_typed) * 100 if total_typed > 0 else 0
    wpm_values = [wpm for time, wpm in state["wpm_history"]]
    consistency = (
        (100 - statistics.stdev(wpm_values) / net_wpm * 100)
        if len(wpm_values) > 1 and net_wpm > 0
        else 100
    )

    is_new_pb = not personal_best or net_wpm > personal_best["net_wpm"]

    char_stats = f"{correct_chars}/{errors}/{len(state['target_text']) - len(state['current_text'])}"

    return {
        "net_wpm": net_wpm,
        "raw_wpm": raw_wpm,
        "acc": accuracy,
        "time": time_elapsed,
        "consistency": max(0, consistency),
        "wpm_history": wpm_values,
        "char_stats": char_stats,
        "is_new_pb": is_new_pb,
    }
