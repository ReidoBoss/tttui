# tttui

`tttui` is a minimal terminal typing test written in Rust. It keeps the interface compact: choose your settings from the home menu, move to `start`, and type.

<img width="1092" height="614" alt="tttui-rust-rewrite-demo" src="https://github.com/user-attachments/assets/02bf6d52-bdf5-4c65-a80a-7dc5ad69ed8f" />

## Features

- Time, words, punctuation, numbers, and quote modes
- Compact selector-first home screen
- Configurable key sequences
- User-editable TOML themes with color and presentation overrides
- Bundled and user-provided languages / quotes
- Personal best tracking
- Bounded recent session history
- Result stats and WPM graph
- Layout that remains usable at `80x24`

## Runing and Installation

Since this is published to crates.io, install globally with:

```sh
cargo install tttui
tttui
```

Run from a source checkout:

```sh
cargo run --bin tttui
```

## Controls

Default bindings:

- `Tab` / `Shift+Tab` / `Up` / `Down` / `j` / `k`: move focus on the home screen
- `1` / `2` / `3` / `4` / `5`: jump to mode, length, language, theme, or start
- `Enter`: open a picker, confirm a picker choice, start from the `start` row, or retry
- `Up` / `Down`: move inside an open picker
- `Esc`: close an open picker
- `q`: quit
- `Tab Enter`: restart during a test
- `Tab m`: return to the menu during a test

All bindings are configurable in the app config file.

## Configuration

On Unix-like systems, the app follows the XDG config path: `$XDG_CONFIG_HOME/tttui/` when `XDG_CONFIG_HOME` is set, otherwise `~/.config/tttui/`. On Windows, it uses `%APPDATA%\tttui\` by default. The app creates its config directory on first launch:

```text
~/.config/tttui/
├── config.toml
├── languages/
├── quotes/
└── themes/
```

Example `config.toml`:

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
focus_next = ["tab", "down", "j"]
focus_previous = ["shift+tab", "up", "k"]
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

Keybindings support multi-key sequences such as `"tab enter"` and modified keys such as `"ctrl+r"`.

Supported modes are `time`, `words`, `punctuation`, `numbers`, and `quote`. The word-count selector is reused by `words`, `punctuation`, and `numbers`.

Press `g` from the home screen to open recent history. Completed runs are kept newest-first in `config.toml`, bounded by `history_limit`.

## Themes

Place custom themes in `~/.config/tttui/themes/<name>.toml`. Built-in themes are `default`, `nord`, and `catppuccin-mocha`.

Example theme:

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

Supported colors:

- Named terminal colors such as `"green"` or `"lightcyan"`
- 256-color indexes such as `"151"`
- Hex RGB values such as `"#a6e3a1"`
- `"default"` for the terminal default background

Theme presentation currently supports optional graph borders and selectable border styles without recompiling.

For the full configuration reference, see [`docs/configuration.md`](docs/configuration.md).

## Custom content

Add word lists and quote files here:

```text
~/.config/tttui/languages/<language>.txt
~/.config/tttui/quotes/<language>.txt
```

Each file uses one word or quote per line. User files override bundled files with the same name.

## Workspace

```text
crates/
├── tttui_core/
│   └── shared kernel types and errors
└── tttui_app/
    ├── config/
    ├── features/preferences/
    └── features/typing_test/
```

The code follows feature boundaries where they carry real responsibility, without adding empty layers only to satisfy a directory pattern.

## Contributing

Contributions are welcome. Open an issue to discuss a change, or send a pull request. Bug reports, new themes, and language/quote packs are all useful.

## Contributors

Thanks to everyone who has contributed to `tttui`:

<a href="https://github.com/ReidoBoss/tttui/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ReidoBoss/tttui" alt="tttui contributors" />
</a>
