import curses
from . import storage, ui


class Menu:
    def __init__(self, stdscr, app_config):
        self.stdscr = stdscr
        self.app_config = app_config
        self.current_menu = "main"
        self.selected_idx = 0
        self.management_target = {}

    def get_menu_options(self):
        languages = storage.get_available_languages()
        themes = list(self.app_config["themes"].keys())
        return {
            "main": ["time", "words", "quote", "language", "theme", "manage"],
            "time": ["15", "30", "60", "back"],
            "words": ["10", "25", "50", "back"],
            "language": languages + ["back"],
            "theme": themes + ["back"],
            "manage": ["manage languages", "manage quotes", "back"],
            "manage_languages": ["add language"] + languages + ["back"],
            "manage_quotes": languages + ["back"],
            "language_actions": ["add word", "remove word", "back"],
            "quote_actions": ["add quote", "remove quote", "back"],
        }

    def navigate(self):
        menu_options = self.get_menu_options()
        status_bar = f"Language: {self.app_config['language']} | Theme: {self.app_config['theme']}"
        ui.display_menu(
            self.stdscr,
            f"tttui / {self.current_menu}",
            menu_options[self.current_menu],
            self.selected_idx,
            status_bar,
        )

        key = self.stdscr.getch()
        if key == curses.KEY_UP:
            self.selected_idx = max(0, self.selected_idx - 1)
        elif key == curses.KEY_DOWN:
            self.selected_idx = min(
                len(menu_options[self.current_menu]) - 1, self.selected_idx + 1
            )
        elif key == ord("\t"):
            if self.current_menu != "main":
                self.current_menu = "main"
                self.selected_idx = 0
        elif key == ord("q"):
            return {"action": "quit"}
        elif key == curses.KEY_ENTER or key == 10:
            selection = menu_options[self.current_menu][self.selected_idx]
            return self.handle_selection(selection)
        return {"action": "navigate"}

    def handle_selection(self, selection):
        if selection == "back":
            self.current_menu = "main"
            self.selected_idx = 0
            return {"action": "navigate"}

        if self.current_menu == "main":
            if selection in ["time", "words", "quote"]:
                return {"action": "start_test", "mode": selection}
            else:
                self.current_menu = selection
                self.selected_idx = 0

        elif self.current_menu == "language":
            self.app_config["language"] = selection
            self.current_menu = "main"
            self.selected_idx = 0

        elif self.current_menu == "theme":
            self.app_config["theme"] = selection
            ui.init_colors(self.app_config["themes"][selection])
            self.current_menu = "main"
            self.selected_idx = 0

        return {"action": "navigate"}
