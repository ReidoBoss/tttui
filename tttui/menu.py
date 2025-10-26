import curses
from . import storage, ui


class Menu:
    def __init__(self, stdscr, app_config):
        self.stdscr = stdscr
        self.app_config = app_config
        self.current_menu = "main"
        self.selected_idx = 0

    def get_menu_options(self):
        """Generate menu options, indicating the current selection."""
        languages = storage.get_available_languages()
        themes = list(self.app_config["themes"].keys())

        current_lang = self.app_config["language"]
        current_theme = self.app_config["theme"]

        lang_options = [
            f"{lang} [{'*' if lang == current_lang else ' '}]" for lang in languages
        ]
        theme_options = [
            f"{theme} [{'*' if theme == current_theme else ' '}]" for theme in themes
        ]

        return {
            "main": [
                "time",
                "words",
                "quote",
                f"language [{current_lang}]",
                f"theme [{current_theme}]",
            ],
            "time": ["15", "30", "60", "120", "back"],
            "words": ["10", "25", "50", "100", "back"],
            "language": lang_options + ["back"],
            "theme": theme_options + ["back"],
        }

    def navigate(self):
        menu_options = self.get_menu_options()
        title = (
            "tttui" if self.current_menu == "main" else f"tttui / {self.current_menu}"
        )
        ui.display_menu(
            self.stdscr, title, menu_options[self.current_menu], self.selected_idx
        )

        key = self.stdscr.getch()
        if key == curses.KEY_UP or chr(key).lower() == "k":
            self.selected_idx = max(0, self.selected_idx - 1)
        elif key == curses.KEY_DOWN or chr(key).lower() == "j":
            self.selected_idx = min(
                len(menu_options[self.current_menu]) - 1, self.selected_idx + 1
            )
        elif key == ord("\t") and self.current_menu != "main":
            self.current_menu = "main"
            self.selected_idx = 0
        elif key == ord("q"):
            return {"action": "quit"}
        elif key in (curses.KEY_ENTER, 10):
            selection_text = menu_options[self.current_menu][self.selected_idx]
            return self.handle_selection(selection_text)
        return {"action": "navigate"}

    def handle_selection(self, selection_text):
        selection = selection_text.split(" ")[0]

        if selection == "back":
            self.current_menu = "main"
            self.selected_idx = 0
            return {"action": "navigate"}

        if self.current_menu == "main":
            if selection in ["time", "words", "language", "theme"]:
                self.current_menu = selection
                self.selected_idx = 0
            elif selection == "quote":
                return {"action": "start_test", "mode": "quote"}

        elif self.current_menu in ["time", "words"]:
            return {
                "action": "start_test",
                "mode": self.current_menu,
                "value": int(selection),
            }

        elif self.current_menu == "language":
            self.app_config["language"] = selection
            return {"action": "setting_changed"}

        elif self.current_menu == "theme":
            self.app_config["theme"] = selection
            ui.init_colors(self.app_config["themes"][selection])
            return {"action": "setting_changed"}

        return {"action": "navigate"}
