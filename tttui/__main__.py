import curses
from . import main

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except curses.error as e:
        print("Error initializing the terminal.")
        print("Please ensure your terminal supports colors and is large enough.")
        print(f"Curses error: {e}")
    except KeyboardInterrupt:
        print("\nExiting tttui. Goodbye!")
