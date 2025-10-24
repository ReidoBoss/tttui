# Contributing

Thank you for your interest in contributing to this project!

## Prerequisites

- Python / Python 3

## Commits

- Make sure to use [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/)
- Make sure to include issue number in your commits
  - bugfix(#3): fix something
  - feature(#2): add <feature>

## Enhancing Existing Functions

- You are welcome to improve existing functions.
- Avoid introducing breaking changes.

## Adding New Functions

- Open an issue to discuss your idea before starting work.
- Do not add third-party dependencies to the core package to keep it lightweight.

## Creating Add-ons

- New add-ons and extensions are welcome!

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
## Code Style
Any code style will do.

## Thank You

We appreciate your contributions. You are awesome!

