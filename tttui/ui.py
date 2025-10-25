import curses
import math


def simple_moving_average(data, window_size):
    if not data or window_size <= 1:
        return data
    smoothed = []
    for i in range(len(data)):
        start, end = max(0, i - window_size // 2), min(
            len(data), i + window_size // 2 + 1
        )
        smoothed.append(sum(data[start:end]) / len(data[start:end]))
    return smoothed


def init_colors(theme):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, theme["text_correct"][0], theme["text_correct"][1])
    curses.init_pair(2, theme["text_incorrect"][0], theme["text_incorrect"][1])
    curses.init_pair(3, theme["text_untyped"][0], theme["text_untyped"][1])
    curses.init_pair(4, theme["caret"][0], theme["caret"][1])
    curses.init_pair(5, theme["menu_highlight"][0], theme["menu_highlight"][1])
    curses.init_pair(6, theme["menu_title"][0], theme["menu_title"][1])
    curses.init_pair(7, 240, -1)
    curses.init_pair(8, 238, -1)


def display_menu(
    stdscr,
    title,
    options,
    selected_idx,
    status_bar="",
    pb_summary="",
    settings_summary="",
    descriptions=None,
):
    h, w = stdscr.getmaxyx()

    ascii_title = [
        "██████████████████████████████████",
        "             T.T. TUI             ",
        "██████████Typing Test TUI█████████",
    ]

    top_padding = 2
    option_padding = 2
    group_divider = "─" * 38

    menu_width = (
        max(max(len(line) for line in ascii_title), *(len(opt) + 20 for opt in options))
        + 8
    )
    menu_height = (
        top_padding + len(ascii_title) + 1 + option_padding + len(options) * 2 + 6
    )
    x = (w - menu_width) // 2
    y = (h - menu_height) // 2

    stdscr.erase()

    stdscr.addstr(y, x, "┌" + "─" * (menu_width - 2) + "┐", curses.A_BOLD)
    for i in range(1, menu_height - 1):
        stdscr.addstr(y + i, x, "│" + " " * (menu_width - 2) + "│")
    stdscr.addstr(
        y + menu_height - 1, x, "└" + "─" * (menu_width - 2) + "┘", curses.A_BOLD
    )

    for idx, line in enumerate(ascii_title):
        stdscr.addstr(
            y + top_padding + idx,
            x + (menu_width - len(line)) // 2,
            line,
            curses.A_BOLD | curses.color_pair(6),
        )

    stdscr.addstr(
        y + top_padding + len(ascii_title),
        x + (menu_width - len(group_divider)) // 2,
        group_divider,
        curses.A_DIM,
    )

    opt_base_y = y + top_padding + len(ascii_title) + 2 + option_padding
    for i, option in enumerate(options):
        opt_y = opt_base_y + i * 2
        prefix = "▸ " if i == selected_idx else "  "
        style = (
            curses.A_BOLD | curses.color_pair(5)
            if i == selected_idx
            else curses.A_NORMAL
        )

        if i == 3 and len(options) > 4:
            stdscr.addstr(
                opt_y - 1,
                x + (menu_width - len(group_divider)) // 2,
                group_divider,
                curses.A_DIM,
            )
        stdscr.addstr(opt_y, x + 6, prefix + option, style)
        if descriptions and i < len(descriptions) and descriptions[i]:
            stdscr.addstr(opt_y + 1, x + 10, descriptions[i], curses.A_DIM)

    divider_y = opt_base_y + len(options) * 2 + 1
    stdscr.addstr(
        divider_y,
        x + (menu_width - len(group_divider)) // 2,
        group_divider,
        curses.A_DIM,
    )
    if pb_summary:
        stdscr.addstr(divider_y + 1, x + 4, pb_summary, curses.A_BOLD | curses.A_DIM)
    if settings_summary:
        stdscr.addstr(divider_y + 2, x + 4, settings_summary, curses.A_DIM)

    hint = "↑/↓ move   Enter select   Tab back   Q quit"
    stdscr.addstr(h - 2, (w - len(hint)) // 2, hint, curses.A_DIM)

    stdscr.refresh()


def display_test_ui(stdscr, state):
    """Displays the test UI without the live stats."""
    h, w = stdscr.getmaxyx()
    stdscr.erase()
    cfg = state["config"]

    mode_str = f"{cfg['mode']}" + (f" {cfg['value']}" if "value" in cfg else "")
    header_parts = [mode_str, f"lang: {cfg.get('language', 'english')}"]

    if cfg["mode"] == "time":
        time_remaining_str = (
            f"time: {max(0, cfg.get('value', 0) - state['time_elapsed']):.1f}s"
        )
        header_parts.insert(0, time_remaining_str)

    header = " | ".join(header_parts)
    stdscr.addstr(1, (w - len(header)) // 2, header, curses.A_DIM)

    lines, current_line_idx = state["lines"], state["current_line_idx"]
    display_start, display_end = max(0, current_line_idx - 1), min(
        len(lines), current_line_idx + 2
    )

    for i, line in enumerate(lines[display_start:display_end]):
        line_idx_abs = display_start + i
        line_y = (h // 2) + (i - 1)
        line_len = state["line_char_counts"][line_idx_abs]
        start_x = (w - line_len) // 2
        line_offset = 0

        for j, char in enumerate(line):
            abs_char_pos = sum(len(l) + 1 for l in lines[:line_idx_abs]) + j
            color = curses.color_pair(7 if line_idx_abs < current_line_idx else 3)
            char_to_display = char

            if abs_char_pos < len(state["current_text"]):
                if abs_char_pos in state["extra_chars"]:
                    char_to_display = state["extra_chars"][abs_char_pos]
                    color = curses.color_pair(2)
                    stdscr.addstr(
                        line_y, start_x + j + line_offset, char_to_display, color
                    )
                    line_offset += 1
                    char_to_display = " "

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
            stdscr.addstr(line_y, start_x + j + line_offset, char_to_display, color)

    command_bar_y = h - 3
    command_options = state["command_options"]
    total_bar_width = sum(len(opt) for opt in command_options) + (
        len(command_options) * 4
    )
    command_bar_x = (w - total_bar_width) // 2
    for i, option in enumerate(command_options):
        style = curses.A_NORMAL
        if state["test_focus"] == "command" and i == state["selected_command_idx"]:
            style = curses.color_pair(5)
        stdscr.addstr(command_bar_y, command_bar_x, f"  {option}  ", style)
        command_bar_x += len(option) + 4
    stdscr.refresh()


def _draw_wpm_graph(stdscr, y, x, width, height, history, duration):
    if not history:
        return
    smoothing_window = max(1, len(history) // 6)
    smoothed_history = simple_moving_average(history, smoothing_window)
    y_axis_width = 4
    x_axis_height = 1
    graph_area_width = (width - y_axis_width) * 2
    graph_area_height = (height - x_axis_height) * 4
    canvas = [
        [False for _ in range(graph_area_width)] for _ in range(graph_area_height)
    ]
    max_wpm = max(smoothed_history) if smoothed_history else 0
    y_max = math.ceil(max_wpm / 10.0) * 10 if max_wpm > 0 else 50
    grid_line_char = "·"
    grid_line_style = curses.color_pair(8) | curses.A_DIM
    num_grid_lines = 6
    for i in range(num_grid_lines + 1):
        line_y = y + int(i * ((height - x_axis_height - 1) / num_grid_lines))
        wpm_label = int(y_max * (1 - i / num_grid_lines))
        stdscr.addstr(line_y, x, f"{wpm_label:<{y_axis_width-1}}")
        for c in range(width - y_axis_width):
            if c % 2 == 0:
                stdscr.addstr(
                    line_y, x + y_axis_width + c, grid_line_char, grid_line_style
                )
    for i in range(graph_area_width - 1):
        idx1 = int(i * (len(smoothed_history) / graph_area_width))
        idx2 = int((i + 1) * (len(smoothed_history) / graph_area_width))
        if idx2 >= len(smoothed_history):
            idx2 = len(smoothed_history) - 1
        y1 = (
            int((smoothed_history[idx1] / y_max) * (graph_area_height - 1))
            if y_max > 0
            else 0
        )
        y2 = (
            int((smoothed_history[idx2] / y_max) * (graph_area_height - 1))
            if y_max > 0
            else 0
        )
        dx, dy = 1, y2 - y1
        steps = max(abs(dx), abs(dy))
        steps = 1 if steps == 0 else steps
        for step in range(steps + 1):
            px, py = i + int(step * dx / steps), y1 + int(step * dy / steps)
            if 0 <= py < graph_area_height:
                canvas[py][px] = True
    for r in range(height - x_axis_height):
        for c in range(width - y_axis_width):
            dots = [canvas[r * 4 + j][c * 2 + k] for j in range(4) for k in range(2)]
            braille_code = 0x2800
            dot_map = [0x01, 0x02, 0x04, 0x40, 0x08, 0x10, 0x20, 0x80]
            for i, dot in enumerate(dots):
                if dot:
                    braille_code += dot_map[i]
            if braille_code != 0x2800:
                stdscr.addstr(
                    y + (height - x_axis_height - 1 - r),
                    x + y_axis_width + c,
                    chr(braille_code),
                    curses.color_pair(1),
                )
    int_duration = int(duration)
    end_time_str = f"{int_duration}s"
    stdscr.addstr(
        y + height - x_axis_height,
        x + width - len(end_time_str),
        end_time_str,
        curses.A_DIM,
    )
    stdscr.addstr(y + height - x_axis_height, x + y_axis_width, "0s", curses.A_DIM)


def display_results(stdscr, state):
    h, w = stdscr.getmaxyx()
    stdscr.erase()
    results, cfg = state["results"], state["config"]
    wpm_str = f"{results['net_wpm']:.2f} WPM"
    acc_str = f"{results['acc']:.2f}% acc"
    stdscr.addstr(
        1, (w - len(wpm_str)) // 2, wpm_str, curses.color_pair(1) | curses.A_BOLD
    )
    stdscr.addstr(2, (w - len(acc_str)) // 2, acc_str)
    y_offset = 4
    if results["is_new_pb"]:
        pb_title = "New Personal Best!"
        stdscr.addstr(
            y_offset,
            (w - len(pb_title)) // 2,
            pb_title,
            curses.color_pair(1) | curses.A_BOLD,
        )
        y_offset += 2
    box_width = 50
    box_height = 6
    box_x = (w - box_width) // 2
    box_y = y_offset
    col1_x = box_x + 3
    col2_x = box_x + 26
    stdscr.addstr(box_y, box_x, "┌" + "─" * (box_width - 2) + "┐")
    for i in range(1, box_height - 1):
        stdscr.addstr(box_y + i, box_x, "│")
        stdscr.addstr(box_y + i, box_x + box_width - 1, "│")
    stdscr.addstr(box_y + box_height - 1, box_x, "└" + "─" * (box_width - 2) + "┘")
    stats_y = box_y + 1
    test_mode_str = f"{cfg['mode']}" + (f" {cfg['value']}" if cfg.get("value") else "")
    stdscr.addstr(stats_y, col1_x, f"{'wpm':<12}{results['net_wpm']:.2f}")
    stdscr.addstr(stats_y, col2_x, f"{'raw':<12}{results['raw_wpm']:.2f}")
    stdscr.addstr(stats_y + 1, col1_x, f"{'acc':<12}{results['acc']:.2f}%")
    stdscr.addstr(
        stats_y + 1, col2_x, f"{'consistency':<12}{results['consistency']:.2f}%"
    )
    stdscr.addstr(stats_y + 2, col1_x, f"{'time':<12}{results['time']:.2f}s")
    stdscr.addstr(stats_y + 2, col2_x, f"{'chars':<12}{results['char_stats']}")
    stdscr.addstr(stats_y + 3, col1_x, f"{'test':<12}{test_mode_str}")
    stdscr.addstr(stats_y + 3, col2_x, f"{'language':<12}{cfg['language']}")
    graph_h = 14
    graph_w = 70
    graph_y = box_y + box_height + 1
    graph_x = (w - graph_w) // 2
    _draw_wpm_graph(
        stdscr,
        graph_y,
        graph_x,
        graph_w,
        graph_h,
        results["wpm_history"],
        results["time"],
    )
    msg = "Press 'Enter' to retry, 'Tab' for menu, 'q' to quit."
    stdscr.addstr(h - 2, (w - len(msg)) // 2, msg)
    stdscr.refresh()
