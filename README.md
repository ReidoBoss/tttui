# T.T. TUI - A Terminal Typing Test

`T.T. TUI` is a fast, lightweight, and feature-rich typing test application that runs entirely in your terminal. Inspired by the clean aesthetic and core functionality of Monkeytype, `tttui` provides a focused, distraction-free environment to practice your typing skills, track your progress, and compete against your own personal bests.

![gigif](https://github.com/user-attachments/assets/58cb0964-1311-4c72-aa04-a76eee20173f)

---

## Features

-   **Multiple Test Modes:** Practice with different challenges.
    -   **Time:** Type as much as you can in a set amount of time (15, 30, 60, 120 seconds).
    -   **Words:** Complete a specific number of words (10, 25, 50, 100).
    -   **Quote:** Type out a quote from the collection.
-   **High-Fidelity WPM Graph:** Get a detailed, high-resolution line graph of your WPM over the course of the test, rendered beautifully with Unicode Braille.
-   **Personal Best Tracking:** `tttui` automatically saves your best score for every test combination (mode, duration, and language) and shows you how your current run compares.
-   **Detailed Performance Stats:** The results screen provides a clean, organized breakdown of your performance, including Net WPM, Raw WPM, accuracy, consistency, and character stats.
-   **Customization:**
    -   **Themes:** Choose from a selection of built-in themes or easily create your own.
    -   **Languages:** Add new languages and wordlists simply by creating text files.
-   **Persistent Configuration:** Your chosen theme, language, and all your personal bests are saved locally, so your experience is consistent every time you launch the app.
-   **Minimalist UI:** A keyboard-driven, distraction-free interface that keeps you focused on the text.

---

## Showcase

#### The Typing Interface

A clean and focused interface shows only what you need while typing. The text is displayed centrally, with minimal status information at the top.

https://github.com/user-attachments/assets/7af94392-fe44-4bfa-91f0-76f3f410ca1c

#### The Results Screen

After each test, you're presented with a detailed breakdown of your performance and a beautiful WPM graph. If you set a new record, you'll be celebrated!

![Results Screen Mock-up](https://github.com/user-attachments/assets/08469162-aa20-407d-b178-2742f428f0ac)

---

## Installation

`tttui` is designed to be simple to install and run.

#### Prerequisites

-   Python 3

#### 1. Clone the Repository

First, clone this repository to your local machine.

```sh
git clone https://github.com/reidoboss/tttui.git
cd tttui
```

#### 2. Make the Script Executable

Give the launch script execute permissions.

```sh
chmod +x bin/tttui.sh
```

#### 3. Run It!

You can now run the application directly.

```sh
./bin/tttui.sh
```

#### 4. (Recommended) Install System-Wide

For the best experience, move the executable to a directory in your system's `PATH`. This allows you to run `tttui` from any terminal, anywhere on your system.

```sh
sudo mv bin/tttui.sh /usr/local/bin/tttui
```

Now you can simply open a terminal and type `tttui` to launch the application.

---

## Usage

`tttui` is controlled entirely with the keyboard.

-   **Menu Navigation:** Use the `UP` and `DOWN` arrow keys or `K`/`J` (case-insensitive) to navigate menus and `ENTER` to select.
-   **Go Back:** Press `TAB` to return to the main menu from a sub-menu.
-   **In-Test Commands:** During a test, press `TAB` to switch focus from the text area to the command bar at the bottom. Use the arrow keys and `ENTER` to `reset` the test or return to the `menu`.
-   **Quit:** Press `q` from the main menu or the results screen to quit the application.

---

## Customization

You can easily add your own themes and languages.

#### Adding a Theme

1.  Open `tttui/config.py`.
2.  Add a new dictionary entry to the `THEMES` dictionary. Follow the existing structure. You can use standard color names (`"red"`, `"blue"`, etc.) or 256-color codes (integers `0-255`).

    ```python
    "my_cool_theme": {
        "text_correct": ("green", -1),      # (foreground, background)
        "text_incorrect": ("red", -1),
        "text_untyped": (244, -1),
        "caret": ("black", "white"),
        "menu_highlight": ("black", "cyan"),
        "menu_title": ("cyan", -1),
    },
    ```
    *A value of `-1` for the background means it will be transparent.*

3.  Launch `tttui` and select your new theme from the theme menu.

#### Adding a Language / Wordlist

1.  Find the `tttui` configuration directory on your system. The application will create it automatically on first run at `~/.config/tttui/`.
2.  Inside that directory, you will find a `languages` folder.
3.  Simply add a new `.txt` file to this folder (e.g., `german.txt`). The file should contain words separated by newlines.
4.  The new language will automatically appear in the `language` menu in the app.

---

## Project Structure

```
tttui/
├── bin/
│   └── tttui.sh          # The main executable launch script.
├── tttui/
│   ├── __init__.py       # Main application loop and state management.
│   ├── __main__.py       # Entry point for running as a module.
│   ├── config.py         # Stores default themes and directory paths.
│   ├── game.py           # Core game logic, state resets, and result calculations.
│   ├── menu.py           # Handles menu navigation and logic.
│   ├── storage.py        # Manages loading/saving of configs, PBs, and language files.
│   └── ui.py             # All rendering logic (menus, test screen, results, graph).
└── README.md
```

---

## License

This project is licensed under the MIT License.
