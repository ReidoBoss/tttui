# Configuration

On Unix-like systems, `tttui` follows the XDG config path:

- `$XDG_CONFIG_HOME/tttui/` when `XDG_CONFIG_HOME` is set
- `~/.config/tttui/` otherwise

On Windows, it uses `%APPDATA%\tttui\` by default. Setting `XDG_CONFIG_HOME` still overrides the base config directory on any platform.

The Unix-like default layout is:

```text
~/.config/tttui/
├── config.toml
├── languages/
├── quotes/
└── themes/
```

The app creates these directories on first launch.

## Main Config

`config.toml` controls defaults, selectable options, keybindings, and locally stored results.

```toml
[defaults]
mode = "time"
duration = 30
word_count = 25
language = "english"
theme = "default"

[options]
durations = [15, 30, 60, 120]
word_counts = [10, 25, 50, 100]
history_limit = 20

[keybindings]
quit = ["q"]
start = ["enter"]
focus_next = ["tab", "down"]
focus_previous = ["shift+tab", "up"]
cycle_next = ["right", "l"]
cycle_previous = ["left", "h"]
picker_next = ["down", "j"]
picker_previous = ["up", "k"]
focus_mode = ["1"]
focus_length = ["2"]
focus_language = ["3"]
focus_theme = ["4"]
focus_start = ["5"]
restart = ["tab enter"]
menu = ["tab m"]
history = ["g"]
cancel = ["esc"]
backspace = ["backspace"]
delete_word = ["ctrl+backspace", "ctrl+h", "ctrl+w", "alt+backspace"]
```

`ctrl+backspace` is only delivered as such by terminals that support the kitty keyboard protocol (enabled automatically when available). Other terminals report it as `ctrl+h`, which the default bindings also cover.

Supported modes:

- `time`
- `words`
- `punctuation`
- `numbers`
- `quote`

The `word_counts` list is shared by `words`, `punctuation`, and `numbers`.

`personal_bests` and `session_history` are written by the app. You can edit them manually, but they are primarily app-owned state rather than normal preferences.

## Keybindings

Each action accepts one or more bindings:

```toml
quit = ["q", "ctrl+c"]
restart = ["tab enter", "ctrl+r"]
```

Supported binding forms include:

- Single keys such as `q`, `enter`, `tab`, `esc`, `up`, or `down`
- Modified keys such as `ctrl+r`, `alt+x`, or `shift+tab`
- Multi-key sequences separated by spaces such as `tab enter`

## Themes

Place custom themes in:

```text
~/.config/tttui/themes/<theme-name>.toml
```

Example:

```toml
[colors]
text = "#cdd6f4"
muted = "#6c7086"
correct = "#a6e3a1"
incorrect = "#f38ba8"
untyped = "#7f849c"
caret = "#f9e2af"
accent = "#89b4fa"
background = "default"
selection = "#45475a"

[presentation]
show_borders = false
border_style = "plain"
```

Supported color forms:

- Named terminal colors such as `green` or `lightcyan`
- 256-color indexes such as `151`
- Hex RGB values such as `#a6e3a1`
- `default` for the terminal default background

Built-in themes:

- `default`
- `nord`
- `catppuccin-mocha`

## Custom Content

Add or override word lists:

```text
~/.config/tttui/languages/<language>.txt
```

Add or override quotes:

```text
~/.config/tttui/quotes/<language>.txt
```

Use one word or quote per line. A user file with the same name as a bundled file overrides the bundled version.
