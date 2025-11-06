# tttui: A Terminal Typing Test

**A fast, lightweight, and feature-rich typing test that runs directly in your terminal.**

Inspired by the minimalist design of Monkeytype, `tttui` provides a clean, distraction-free environment to practice your typing, track your progress, and race against your personal bests.

![tttui Showcase GIF](https://github.com/user-attachments/assets/58cb0964-1311-4c72-aa04-a76eee20173f)

---

## Features

- **Multiple Test Modes:**
  - **Time:** Type for 15, 30, 60, or 120 seconds.
  - **Words:** Complete 10, 25, 50, or 100 words.
  - **Quote:** Type out a famous quote.
- **High-Fidelity WPM Graph:** A detailed, high-resolution WPM graph rendered beautifully with Unicode Braille.
- **Personal Best Tracking:** Automatically saves and compares your best score for every test configuration.
- **Detailed Performance Stats:** Get a clean breakdown of your Net WPM, Raw WPM, accuracy, consistency, and character stats.
- **Customization:**
  - **Themes:** Choose from built-in themes or easily create your own.
  - **Languages:** Add new wordlists simply by creating new text files.
- **Persistent Configuration:** Your theme, language, and personal bests are saved locally for a consistent experience.
- **Minimalist, Keyboard-Driven UI:** Stay focused on typing with a clean, efficient interface.

---

## Showcase

<details>
<summary>Click to see more screenshots</summary>

#### Typing Interface

https://github.com/user-attachments/assets/7af94392-fe44-4bfa-91f0-76f3f410ca1c

#### Results Screen

_After each test, you get a detailed breakdown of your performance and a beautiful WPM graph. New records are celebrated!_
![Results Screen](https://github.com/user-attachments/assets/08469162-aa20-407d-b178-2742f428f0ac)

</details>

---

## Installation

`tttui` is designed for a simple and fast setup.

### Recommended Method: PyPI (pip)

The easiest way to install `tttui` is with `pip`.

```sh
pip install tttui
```

Then, run the application:

```sh
tttui
```

_(If the command isn't found, you may need to add Python's `bin` directory to your system's `PATH` or run `python -m tttui` instead.)_

```sh
python -m tttui
```

<br>

<details>
<summary><b>Alternative: Manual Installation from GitHub</b></summary>

#### 1. Clone the Repository

```sh
git clone https://github.com/reidoboss/tttui.git
cd tttui
```

#### 2. Make the Script Executable

```sh
chmod +x bin/tttui.sh
```

#### 3. Run the Application

```sh
./bin/tttui.sh
```

#### 4. (Optional) Install System-Wide

To run `tttui` from any directory, move the script to a location in your `PATH`.

```sh
sudo mv bin/tttui.sh /usr/local/bin/tttui
```

Now you can launch the app by just typing `tttui` in your terminal.

</details>

---

## Usage

Control `tttui` entirely with your keyboard:

- **Navigation:** Use `UP`/`DOWN` arrows or `K`/`J` to move through menus.
- **Select:** Press `ENTER` to confirm a selection.
- **Go Back:** Press `TAB` to return to the main menu from any sub-menu.
- **In-Test Options:** During a test, press `TAB` to access the command bar to **reset** the test or return to the **menu**.
- **Quit:** Press `q` from the main menu or results screen to exit.

---

## Customization

You can easily add your own themes and languages.

### Adding a Theme

1.  Open the `tttui/config.py` file.
2.  Add a new theme dictionary to the `THEMES` object. You can use color names (e.g., `"red"`) or 256-color codes (e.g., `196`). Use `-1` for a transparent background.

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

3.  Launch `tttui` and select your new theme from the **theme** menu.

### Adding a Language or Wordlist

1.  Locate the `tttui` installation directory. Inside, you will find `languages` and `quotes` folders.
2.  Add a new `.txt` file (e.g., `german.txt`) to the desired folder.
3.  The file should contain one word per line.
4.  The new language will automatically appear in the **language** menu in the app.

---

## Project Structure

```
tttui/
├── bin/
│   └── tttui.sh          # Main executable launch script
├── tttui/
│   ├── languages/        # Wordlists for different languages
│   ├── quotes/           # Quote files for quote mode
│   ├── __init__.py       # Main application loop and state management
│   ├── __main__.py       # Entry point for `python -m tttui`
│   ├── config.py         # Default themes and directory paths
│   ├── game.py           # Core typing test logic and result calculations
│   ├── menu.py           # Menu navigation and rendering
│   ├── storage.py        # Handles loading/saving configs and PBs
│   └── ui.py             # All rendering logic (menus, test screen, results)
└── README.md
```

---

## 📄 License

This project is licensed under the **MIT License**.
