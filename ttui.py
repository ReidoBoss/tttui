import curses
import time
import random
import math
import os


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LANGUAGES_DIR = os.path.join(SCRIPT_DIR, "languages")
QUOTES_DIR = os.path.join(SCRIPT_DIR, "quotes")


def ensure_dirs():
    """Ensure languages and quotes directories exist."""
    os.makedirs(LANGUAGES_DIR, exist_ok=True)
    os.makedirs(QUOTES_DIR, exist_ok=True)


def load_items(item_type, language):
    """Generic function to load words or quotes from a file."""
    dir_path = LANGUAGES_DIR if item_type == "words" else QUOTES_DIR
    file_path = os.path.join(dir_path, f"{language}.txt")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            items = [line.strip() for line in f if line.strip()]
        return items if items else [f"No {item_type} found for {language}"]
    except FileNotFoundError:
        return [f"No {item_type} file for {language}"]


def add_item(item_type, language, item):
    """Add a word or quote to the appropriate file."""
    dir_path = LANGUAGES_DIR if item_type == "words" else QUOTES_DIR
    file_path = os.path.join(dir_path, f"{language}.txt")
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"\n{item}")


def remove_item(item_type, language, item_to_remove):
    """Remove a word or quote from the appropriate file."""
    dir_path = LANGUAGES_DIR if item_type == "words" else QUOTES_DIR
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


def display_menu(
    stdscr,
    title,
    options,
    selected_idx,
    help_text="UP/DOWN: navigate | ENTER: select | TAB: back",
):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    stdscr.addstr(3, (w - len(title)) // 2, title, curses.A_BOLD | curses.color_pair(2))
    for i, option in enumerate(options):
        y = 6 + i
        x = (w - len(option)) // 2
        if i == selected_idx:
            stdscr.addstr(y, x, f"> {option[:w-6]} <", curses.A_REVERSE)
        else:
            stdscr.addstr(y, x, f"  {option[:w-6]}  ")
    stdscr.addstr(h - 2, (w - len(help_text)) // 2, help_text)
    stdscr.refresh()


def get_user_input(stdscr, prompt):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    stdscr.addstr(h // 2 - 1, (w - len(prompt)) // 2, prompt)
    stdscr.addstr(h // 2 + 1, w // 2 - 20, "_" * 40)
    stdscr.refresh()
    curses.echo()
    curses.curs_set(1)
    input_win = curses.newwin(1, 40, h // 2, w // 2 - 19)
    input_str = input_win.getstr(0, 0).decode("utf-8")
    curses.noecho()
    curses.curs_set(0)
    return input_str


def display_test_ui(stdscr, state):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    mode_cfg = state["config"]
    header_parts = []
    if mode_cfg["mode"] == "time":
        header_parts.append(
            f"Time: {max(0, mode_cfg['value'] - state['time_elapsed']):.1f}s"
        )
    elif mode_cfg["mode"] == "words":
        header_parts.append(
            f"Words: {state['current_text'].count(' ')}/{mode_cfg['value']}"
        )
    header_parts.append(f"Lang: {mode_cfg.get('language', 'english')}")
    header = " | ".join(header_parts)
    stdscr.addstr(1, (w - len(header)) // 2, header)
    lines = state["lines"]
    start_y = (h - len(lines)) // 2
    char_typed_count = len(state["current_text"])
    for i, line in enumerate(lines):
        start_x = (w - len(line)) // 2
        for j, char in enumerate(line):
            abs_char_pos = sum(len(l) + 1 for l in lines[:i]) + j
            color = curses.color_pair(5)
            if abs_char_pos < char_typed_count:
                color = (
                    curses.color_pair(2)
                    if state["current_text"][abs_char_pos]
                    == state["target_text"][abs_char_pos]
                    else curses.color_pair(3)
                )
            elif abs_char_pos == char_typed_count:
                color = (
                    curses.color_pair(4)
                    if state["test_focus"] == "text"
                    else curses.color_pair(6)
                )
            stdscr.addstr(start_y + i, start_x + j, char, color)
    command_bar_y = h - 3
    command_options = state["command_options"]
    total_bar_width = sum(len(opt) for opt in command_options) + (
        len(command_options) * 4
    )
    command_bar_x = (w - total_bar_width) // 2
    for i, option in enumerate(command_options):
        style = curses.A_NORMAL
        if state["test_focus"] == "command" and i == state["selected_command_idx"]:
            style = curses.A_REVERSE
        stdscr.addstr(command_bar_y, command_bar_x, f"  {option}  ", style)
        command_bar_x += len(option) + 4
    stdscr.refresh()


def display_results(stdscr, state):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    time_elapsed = state["time_elapsed"]
    errors = state["errors"]
    total_typed = state["total_typed_chars"]
    correct_chars = total_typed - errors
    accuracy = (correct_chars / total_typed) * 100 if total_typed > 0 else 0
    net_wpm = (correct_chars / 5) / (time_elapsed / 60) if time_elapsed > 0 else 0
    title = "Test Complete!"
    stdscr.addstr(3, (w - len(title)) // 2, title, curses.A_BOLD)
    stdscr.addstr(
        5,
        (w - len(f"WPM: {net_wpm:.2f}")) // 2,
        f"WPM: {net_wpm:.2f}",
        curses.color_pair(2) | curses.A_BOLD,
    )
    stdscr.addstr(
        6, (w - len(f"Accuracy: {accuracy:.2f}%")) // 2, f"Accuracy: {accuracy:.2f}%"
    )
    stdscr.addstr(
        8,
        (w - len(f"Characters (corr/err): {correct_chars}/{errors}")) // 2,
        f"Characters (corr/err): {correct_chars}/{errors}",
    )
    msg = "Press 'Enter' to retry, 'Tab' for menu, 'q' to quit."
    stdscr.addstr(h - 3, (w - len(msg)) // 2, msg)
    stdscr.refresh()


def reset_game(config):
    h, w = 80, 200
    words_for_test = load_items("words", config.get("language", "english"))
    random.shuffle(words_for_test)
    if config["mode"] == "time":
        target_text = " ".join(words_for_test * 2)
    elif config["mode"] == "words":
        target_text = " ".join(words_for_test[: config["value"]])
    elif config["mode"] == "quote":
        quotes = load_items("quotes", config.get("language", "english"))
        target_text = random.choice(quotes)
    lines = []
    line_width = min(w - 4, 80)
    words = target_text.split(" ")
    current_line = ""
    for word in words:
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


def main(stdscr):
    ensure_dirs()
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)

    app_state = "MENU"
    current_menu = "main"
    selected_idx = 0
    game_config = {"language": "english"}
    management_target = {}

    while True:
        language_files = [
            f.replace(".txt", "")
            for f in os.listdir(LANGUAGES_DIR)
            if f.endswith(".txt")
        ] or ["english"]
        menu_options = {
            "main": ["time", "words", "quote", "language", "manage"],
            "time": ["15", "30", "60", "back"],
            "words": ["10", "25", "50", "back"],
            "language": language_files + ["back"],
            "manage": ["manage languages", "manage quotes", "back"],
            "manage_languages": ["add language"] + language_files + ["back"],
            "manage_quotes": language_files + ["back"],
            "language_actions": ["add word", "remove word", "back"],
            "quote_actions": ["add quote", "remove quote", "back"],
        }

        if app_state == "MENU":
            stdscr.nodelay(False)
            display_menu(
                stdscr,
                f"monkeytype / {current_menu}",
                menu_options[current_menu],
                selected_idx,
            )
            key = stdscr.getch()
            if key == curses.KEY_UP:
                selected_idx = max(0, selected_idx - 1)
            elif key == curses.KEY_DOWN:
                selected_idx = min(
                    len(menu_options[current_menu]) - 1, selected_idx + 1
                )
            elif key == ord("\t"):
                if current_menu not in ["main"]:
                    current_menu = "main"
                    selected_idx = 0
            elif key == ord("q"):
                break
            elif key == curses.KEY_ENTER or key == 10:
                selection = menu_options[current_menu][selected_idx]
                if selection == "back":
                    if current_menu in ["manage_languages", "manage_quotes"]:
                        current_menu = "manage"
                    elif current_menu in ["language_actions", "quote_actions"]:
                        current_menu = f"manage_{management_target['type']}"
                    else:
                        current_menu = "main"
                    selected_idx = 0
                elif current_menu == "main":
                    if selection in ["time", "words", "language", "manage"]:
                        current_menu = selection
                        selected_idx = 0
                    else:
                        game_config.update({"mode": "quote", "value": None})
                        app_state = "TEST"
                elif current_menu == "manage":
                    current_menu = selection.replace(" ", "_")
                    selected_idx = 0
                elif current_menu == "manage_languages":
                    if selection == "add language":
                        new_lang = get_user_input(stdscr, "Enter new language name:")
                        if new_lang:
                            open(
                                os.path.join(LANGUAGES_DIR, f"{new_lang}.txt"), "w"
                            ).close()
                            open(
                                os.path.join(QUOTES_DIR, f"{new_lang}.txt"), "w"
                            ).close()
                    else:
                        management_target = {"type": "languages", "lang": selection}
                        current_menu = "language_actions"
                        selected_idx = 0
                elif current_menu == "manage_quotes":
                    management_target = {"type": "quotes", "lang": selection}
                    current_menu = "quote_actions"
                    selected_idx = 0
                elif current_menu == "language_actions":
                    action = selection.replace(" ", "_")
                    if action == "add_word":
                        new_word = get_user_input(
                            stdscr, f"Enter word to add to {management_target['lang']}:"
                        )
                        if new_word:
                            add_item("words", management_target["lang"], new_word)
                    elif action == "remove_word":
                        word_to_remove = get_user_input(
                            stdscr,
                            f"Enter word to remove from {management_target['lang']}:",
                        )
                        if word_to_remove:
                            remove_item(
                                "words", management_target["lang"], word_to_remove
                            )
                elif current_menu == "quote_actions":
                    action = selection.replace(" ", "_")
                    if action == "add_quote":
                        new_quote = get_user_input(
                            stdscr,
                            f"Enter quote to add to {management_target['lang']}:",
                        )
                        if new_quote:
                            add_item("quotes", management_target["lang"], new_quote)
                    elif action == "remove_quote":
                        quotes = load_items("quotes", management_target["lang"])
                        current_menu = "remove_quote_select"
                        selected_idx = 0
                        menu_options["remove_quote_select"] = quotes + ["back"]
                elif current_menu == "remove_quote_select":
                    remove_item("quotes", management_target["lang"], selection)
                    current_menu = "quote_actions"
                    selected_idx = 0
                elif current_menu == "language":
                    game_config["language"] = selection
                    current_menu = "main"
                    selected_idx = 0
                else:
                    game_config.update({"mode": current_menu, "value": int(selection)})
                    app_state = "TEST"
            if app_state == "TEST":
                state = reset_game(game_config)
                stdscr.nodelay(True)
        elif app_state == "TEST":
            if state["started"]:
                state["time_elapsed"] = time.time() - state["start_time"]
            test_over = False
            if state["started"]:
                cfg = state["config"]
                if cfg["mode"] == "time" and state["time_elapsed"] >= cfg["value"]:
                    test_over = True
                elif cfg["mode"] in ["words", "quote"] and len(
                    state["current_text"]
                ) == len(state["target_text"]):
                    test_over = True
            if test_over:
                app_state = "RESULT"
                stdscr.nodelay(False)
                continue
            display_test_ui(stdscr, state)
            key_code = stdscr.getch()
            if key_code == -1:
                continue
            if not state["started"] and key_code != -1:
                state["start_time"] = time.time()
                state["started"] = True
            if state["test_focus"] == "text":
                if key_code == ord("\t"):
                    state["test_focus"] = "command"
                elif key_code in (curses.KEY_BACKSPACE, 127):
                    if (
                        len(state["current_text"])
                        > state["current_text"].rfind(" ") + 1
                    ):
                        state["current_text"] = state["current_text"][:-1]
                elif 32 <= key_code <= 255:
                    char = chr(key_code)
                    if len(state["current_text"]) < len(state["target_text"]):
                        state["total_typed_chars"] += 1
                        current_pos = len(state["current_text"])
                        if char != state["target_text"][current_pos]:
                            state["errors"] += 1
                        state["current_text"] += char
            elif state["test_focus"] == "command":
                if key_code == ord("\t"):
                    state["selected_command_idx"] = (
                        state["selected_command_idx"] + 1
                    ) % len(state["command_options"])
                elif key_code == curses.KEY_BTAB:
                    state["selected_command_idx"] = (
                        state["selected_command_idx"]
                        - 1
                        + len(state["command_options"])
                    ) % len(state["command_options"])
                elif key_code == 27:
                    state["test_focus"] = "text"
                elif key_code == curses.KEY_ENTER or key_code == 10:
                    command = state["command_options"][state["selected_command_idx"]]
                    if command == "reset":
                        state = reset_game(game_config)
                    elif command == "menu":
                        stdscr.nodelay(False)
                        app_state = "MENU"
                        current_menu = "main"
                        selected_idx = 0
                        continue
        elif app_state == "RESULT":
            display_results(stdscr, state)
            key = stdscr.getch()
            if key == ord("q"):
                break
            elif key == ord("\t"):
                app_state = "MENU"
                current_menu = "main"
                selected_idx = 0
            elif key == curses.KEY_ENTER or key == 10:
                app_state = "TEST"
                state = reset_game(game_config)
                stdscr.nodelay(True)


if __name__ == "__main__":
    curses.wrapper(main)
