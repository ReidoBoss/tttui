import curses
import time
from . import config, storage, ui, game, menu


def main(stdscr):
    """The main application function, wrapped by curses."""
    storage.ensure_dirs()
    curses.curs_set(0)

    app_config = {"language": "english", "theme": "default", "themes": config.THEMES}
    ui.init_colors(app_config["themes"]["default"])

    app_state = "MENU"
    test_state = None
    menu_handler = menu.Menu(stdscr, app_config)

    while True:
        if app_state == "MENU":
            menu_result = menu_handler.navigate()
            action = menu_result.get("action")

            if action == "quit":
                break
            elif action == "start_test":
                game_cfg = {
                    "language": app_config["language"],
                    "theme": app_config["theme"],
                    "mode": menu_result.get("mode"),
                }
                # In a full app, you'd navigate to another menu to get the value for time/words
                if game_cfg["mode"] in ["time", "words"]:
                    game_cfg["value"] = 15
                test_state = game.reset_game(game_cfg)
                app_state = "TEST"
                stdscr.nodelay(True)

        elif app_state == "TEST":
            if test_state["started"]:
                test_state["time_elapsed"] = time.time() - test_state["start_time"]

            is_over = False
            cfg = test_state["config"]
            if test_state["started"]:
                if cfg["mode"] == "time" and test_state["time_elapsed"] >= cfg["value"]:
                    is_over = True
                elif len(test_state["current_text"]) == len(test_state["target_text"]):
                    is_over = True

            if is_over:
                test_state["results"] = game.calculate_results(test_state)
                app_state = "RESULT"
                stdscr.nodelay(False)
                continue

            ui.display_test_ui(stdscr, test_state)
            key_code = stdscr.getch()
            if key_code == -1:
                continue

            if not test_state["started"]:
                test_state["started"], test_state["start_time"] = True, time.time()

            # Input handling logic (simplified)
            if 32 <= key_code <= 126:
                char, pos = chr(key_code), len(test_state["current_text"])
                if pos < len(test_state["target_text"]):
                    test_state["total_typed_chars"] += 1
                    if char != test_state["target_text"][pos]:
                        test_state["errors"] += 1
                    test_state["current_text"] += char

        elif app_state == "RESULT":
            ui.display_results(stdscr, test_state)
            key = stdscr.getch()
            if key == ord("q"):
                break
            elif key == ord("\t"):
                app_state = "MENU"
            elif key == curses.KEY_ENTER or key == 10:
                test_state = game.reset_game(test_state["config"])
                app_state = "TEST"
                stdscr.nodelay(True)
