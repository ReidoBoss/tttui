import curses


def init_colors(theme):
    """Initialize color pairs based on the selected theme."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, theme["text_correct"][0], theme["text_correct"][1])
    curses.init_pair(2, theme["text_incorrect"][0], theme["text_incorrect"][1])
    curses.init_pair(3, theme["text_untyped"][0], theme["text_untyped"][1])
    curses.init_pair(4, theme["caret"][0], theme["caret"][1])
    curses.init_pair(5, theme["menu_highlight"][0], theme["menu_highlight"][1])
    curses.init_pair(6, theme["menu_title"][0], theme["menu_title"][1])
    curses.init_pair(7, 240, -1)


def display_menu(stdscr, title, options, selected_idx, status_bar=""):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    stdscr.addstr(3, (w - len(title)) // 2, title, curses.A_BOLD | curses.color_pair(6))
    for i, option in enumerate(options):
        y = 6 + i
        x = (w - len(option)) // 2
        style = curses.color_pair(5) if i == selected_idx else curses.A_NORMAL
        stdscr.addstr(y, x, f"  {option[:w-6]}  ", style)
    help_text = "UP/DOWN: navigate | ENTER: select | TAB: back | Q: quit"
    stdscr.addstr(h - 3, (w - len(help_text)) // 2, help_text)
    if status_bar:
        stdscr.addstr(h - 2, (w - len(status_bar)) // 2, status_bar, curses.A_REVERSE)
    stdscr.refresh()


def get_user_input(stdscr, prompt):
    h, w = stdscr.getmaxyx()
    curses.echo()
    curses.curs_set(1)
    win_h, win_w = 3, 42
    win_y, win_x = (h - win_h) // 2, (w - win_w) // 2
    input_win = curses.newwin(win_h, win_w, win_y, win_x)
    input_win.border()
    input_win.addstr(0, 2, f" {prompt} ")
    input_win.refresh()
    edit_win = curses.newwin(1, win_w - 2, win_y + 1, win_x + 1)
    input_str = edit_win.getstr(0, 0).decode("utf-8")
    curses.noecho()
    curses.curs_set(0)
    return input_str


def display_test_ui(stdscr, state):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    cfg = state["config"]
    header_parts = [
        f"Lang: {cfg.get('language', 'english')}",
        f"Theme: {cfg.get('theme', 'default')}",
    ]
    if cfg["mode"] == "time":
        header_parts.insert(
            0, f"Time: {max(0, cfg['value'] - state['time_elapsed']):.1f}s"
        )
    elif cfg["mode"] == "words":
        header_parts.insert(
            0, f"Words: {state['current_text'].count(' ')}/{cfg['value']}"
        )
    header = " | ".join(header_parts)
    stdscr.addstr(1, (w - len(header)) // 2, header)
    lines, current_line_idx = state["lines"], state["current_line_idx"]
    display_start, display_end = max(0, current_line_idx - 1), min(
        len(lines), current_line_idx + 2
    )
    for i, line in enumerate(lines[display_start:display_end]):
        line_y, start_x = (h // 2) + (i - 1), (w - len(line)) // 2
        line_idx_abs = display_start + i
        for j, char in enumerate(line):
            abs_char_pos = sum(len(l) + 1 for l in lines[:line_idx_abs]) + j
            color = curses.color_pair(7 if line_idx_abs < current_line_idx else 3)
            if abs_char_pos < len(state["current_text"]):
                color = curses.color_pair(
                    1
                    if state["current_text"][abs_char_pos]
                    == state["target_text"][abs_char_pos]
                    else 2
                )
            if abs_char_pos == len(state["current_text"]):
                color = (
                    curses.color_pair(4)
                    if state["test_focus"] == "text"
                    else curses.A_NORMAL
                )
            stdscr.addstr(line_y, start_x + j, char, color)
    stdscr.refresh()


def display_results(stdscr, state):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    results = state["results"]
    title = "Test Complete!"
    stdscr.addstr(3, (w - len(title)) // 2, title, curses.A_BOLD | curses.color_pair(6))
    stdscr.addstr(
        5,
        (w - 20) // 2,
        f"WPM:      {results['wpm']:.2f}",
        curses.color_pair(1) | curses.A_BOLD,
    )
    stdscr.addstr(6, (w - 20) // 2, f"Accuracy: {results['acc']:.2f}%")
    stdscr.addstr(7, (w - 20) // 2, f"Errors:   {results['errors']}")
    msg = "Press 'Enter' to retry, 'Tab' for menu, 'q' to quit."
    stdscr.addstr(h - 3, (w - len(msg)) // 2, msg)
    stdscr.refresh()
