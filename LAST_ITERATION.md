This iteration focuses on improving code organization by separating static text data from game logic configuration. This aligns with the goal of making text-based operations easier to manage.

**Summary of Changes:**

1.  **Created `game_app/text_data.py`:**
    *   A new file, `text_data.py`, was created to house large, static dictionaries of text.
    *   The `DEFAULT_TEAMS`, `ACTION_DESCRIPTIONS`, and `ACTION_VERBOSE_DESCRIPTIONS` dictionaries were moved from `game_data.py` to this new file.

2.  **Refactored `game_app/game_data.py`:**
    *   This file now imports the text data from `text_data.py`.
    *   The moved dictionaries are re-exported from `game_data.py` to maintain a single point of import for most other modules, preventing the need for widespread changes across the codebase. This keeps the API consistent for files like `game_logic.py` and `routes.py`.

3.  **Updated Project Configuration:**
    *   `game_app/utils.py`: Added `game_app/text_data.py` to the `WATCHED_FILES` list to ensure the live-update detection system tracks changes to this new file.
    *   `static/js/api.js`: Added `text_data.py` to the `pyodideFileStructure` list, ensuring it is loaded into the virtual filesystem when the application runs in static/Pyodide mode.

This change cleans up `game_data.py`, making it easier to see the core game balance data (weights, groups, etc.) without being cluttered by large blocks of text.