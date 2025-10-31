import os
import curses

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PACKAGE_DIR)
LANGUAGES_DIR = os.path.join(PROJECT_ROOT, "languages")
QUOTES_DIR = os.path.join(PROJECT_ROOT, "quotes")

THEMES = {
    "default": {
        "text_correct": (curses.COLOR_GREEN, -1),
        "text_incorrect": (curses.COLOR_RED, -1),
        "text_untyped": (curses.COLOR_WHITE, -1),
        "caret": (curses.COLOR_BLACK, curses.COLOR_WHITE),
        "menu_highlight": (curses.COLOR_BLACK, curses.COLOR_GREEN),
        "menu_title": (curses.COLOR_GREEN, -1),
    },
    "serenity": {
        "text_correct": (22, -1),  # Soft Teal
        "text_incorrect": (125, -1),  # Muted Plum
        "text_untyped": (244, -1),  # Dim Gray
        "caret": (231, 22),  # Bright White on Soft Teal
        "menu_highlight": (231, 240),  # Bright White on Gray
        "menu_title": (31, -1),  # Bright Cyan
    },
    "cyberpunk": {
        "text_correct": (118, -1),  # Electric Lime
        "text_incorrect": (198, -1),  # Hot Pink
        "text_untyped": (51, -1),  # Cool Cyan
        "caret": (16, 226),  # Black on Yellow
        "menu_highlight": (16, 198),  # Black on Hot Pink
        "menu_title": (226, -1),  # Yellow
    },
    "catppuccin-mocha": { # https://catppuccin.com/palette/ for reference!
        "text_correct": (151, -1), # Green
        "text_incorrect": (211, -1), # red
        "text_untyped": (60, -1), # Overlay 0
        "caret": (16, 223), # Crust on Yellow
        "menu_highlight": (0, 147), # default on Violet 
        "menu_title": (111, -1), # Blue
    },
}
