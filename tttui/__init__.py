import curses
import time
from . import config, storage, ui, game, menu

GRAPH_SAMPLE_RATE = 0.25


def main(stdscr):
    curses.curs_set(0)
    storage.ensure_dirs()
    persistent_config = storage.load_config()
    app_config = {
        "language": persistent_config["user_preferences"].get("language", "english"),
        "theme": persistent_config["user_preferences"].get("theme", "default"),
        "themes": config.THEMES,
    }
    ui.init_colors(app_config["themes"][app_config["theme"]])

    app_state = "MENU"
    test_state = None
    menu_handler = menu.Menu(stdscr, app_config)

    while True:
        if app_state == "MENU":
            menu_result = menu_handler.navigate()
            action = menu_result.get("action")

            if action == "quit":
                break
            elif action == "setting_changed":
                persistent_config["user_preferences"]["language"] = app_config[
                    "language"
                ]
                persistent_config["user_preferences"]["theme"] = app_config["theme"]
                storage.save_config(persistent_config)
                menu_handler.current_menu = "main"
                menu_handler.selected_idx = 0
            elif action == "start_test":
                game_cfg = {
                    "language": app_config["language"],
                    "theme": app_config["theme"],
                    "mode": menu_result.get("mode"),
                    "value": menu_result.get("value"),
                }
                test_state = game.reset_game(game_cfg)
                app_state = "TEST"
                stdscr.nodelay(True)

        elif app_state == "TEST":
            current_time = time.time()
            if test_state["started"]:
                test_state["time_elapsed"] = current_time - test_state["start_time"]
            if (
                test_state["started"]
                and current_time - test_state["last_wpm_record_time"]
                >= GRAPH_SAMPLE_RATE
            ):
                if test_state["time_elapsed"] > 0:
                    cumulative_wpm = (test_state["total_typed_chars"] / 5) / (
                        test_state["time_elapsed"] / 60
                    )
                    test_state["wpm_history"].append(
                        (test_state["time_elapsed"], cumulative_wpm)
                    )
                test_state["last_wpm_record_time"] = current_time

            is_over = False
            cfg = test_state["config"]
            if test_state["started"]:
                if (
                    cfg.get("value")
                    and cfg["mode"] == "time"
                    and test_state["time_elapsed"] >= cfg["value"]
                ):
                    is_over = True
                elif len(test_state["current_text"]) == len(test_state["target_text"]):
                    is_over = True

            if is_over:
                test_key = f"{cfg['mode']}_{cfg.get('value', 'na')}_{cfg['language']}"
                pb_data = storage.get_pb(persistent_config["personal_bests"], test_key)
                test_state["personal_best"] = pb_data

                results = game.calculate_results(test_state, pb_data)
                test_state["results"] = results

                if results["is_new_pb"]:
                    persistent_config["personal_bests"][test_key] = {
                        "net_wpm": results["net_wpm"],
                        "acc": results["acc"],
                        "raw_wpm": results["raw_wpm"],
                    }
                    storage.save_config(persistent_config)

                app_state = "RESULT"
                stdscr.nodelay(False)
                continue

            ui.display_test_ui(stdscr, test_state)
            key_code = stdscr.getch()
            if key_code == -1:
                continue

            if not test_state["started"]:
                test_state["started"], test_state["start_time"] = True, time.time()
                test_state["last_wpm_record_time"] = test_state["start_time"]

            if test_state["test_focus"] == "text":
                if key_code == ord("\t"):
                    test_state["test_focus"] = "command"
                elif key_code in (curses.KEY_BACKSPACE, 127, ord("\b")):
                    if test_state["current_text"]:
                        last_char_pos = len(test_state["current_text"]) - 1
                        test_state["current_text"] = test_state["current_text"][:-1]
                        if last_char_pos in test_state["extra_chars"]:
                            del test_state["extra_chars"][last_char_pos]
                            test_state["line_char_counts"][
                                test_state["current_line_idx"]
                            ] -= 1

                elif 32 <= key_code <= 255:
                    char, pos = chr(key_code), len(test_state["current_text"])
                    if pos < len(test_state["target_text"]):
                        test_state["total_typed_chars"] += 1
                        is_space_expected = test_state["target_text"][pos] == " "
                        is_space_typed = char == " "

                        if is_space_expected and not is_space_typed:
                            test_state["errors"] += 1
                            test_state["extra_chars"][pos] = char
                            test_state["line_char_counts"][
                                test_state["current_line_idx"]
                            ] += 1
                            test_state["current_text"] += " "
                        else:
                            if char != test_state["target_text"][pos]:
                                test_state["errors"] += 1
                            test_state["current_text"] += char

            elif test_state["test_focus"] == "command":
                if key_code == ord("\t"):
                    next_idx = test_state["selected_command_idx"] + 1
                    if next_idx >= len(test_state["command_options"]):
                        test_state["test_focus"] = "text"
                        test_state["selected_command_idx"] = 0
                    else:
                        test_state["selected_command_idx"] = next_idx

                elif key_code == curses.KEY_BTAB:
                    prev_idx = test_state["selected_command_idx"] - 1
                    if prev_idx < 0:
                        test_state["test_focus"] = "text"
                    else:
                        test_state["selected_command_idx"] = prev_idx

                elif key_code == 27:
                    test_state["test_focus"] = "text"

                elif key_code in (curses.KEY_ENTER, 10, 13):
                    command = test_state["command_options"][
                        test_state["selected_command_idx"]
                    ]
                    if command == "reset":
                        test_state = game.reset_game(test_state["config"])
                    elif command == "menu":
                        app_state = "MENU"
                        stdscr.nodelay(False)

        elif app_state == "RESULT":
            ui.display_results(stdscr, test_state)
            key = stdscr.getch()
            if key == ord("q"):
                break
            elif key == ord("\t"):
                app_state = "MENU"
            elif key in (curses.KEY_ENTER, 10, 13):
                test_state = game.reset_game(test_state["config"])
                app_state = "TEST"
                stdscr.nodelay(True)
