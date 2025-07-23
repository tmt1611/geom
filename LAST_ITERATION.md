This iteration focuses on cleaning up the codebase in both the Python backend and JavaScript frontend.

**Key Changes:**

1.  **Bug Fix in Game Logic:** Fixed a critical bug in `game_logic.py` where the action probability calculation was referencing a non-existent dictionary (`game_data.ACTION_DESCRIPTIONS`), which would have caused a server error. The code now correctly retrieves the `display_name` from the single source of truth, `action_data.py`.

2.  **Data Refactoring:** The `DEFAULT_TEAMS` data structure in `game_data.py` was refactored from a dictionary with redundant keys to a cleaner list of objects. The game's `reset()` method was updated to handle this improved structure. This reduces data redundancy and improves clarity.

3.  **Frontend Code Organization:** The `main.js` file, which was becoming excessively large, has been split. All the illustration-drawing logic (`illustrationHelpers` and `illustrationDrawers`), which is static and self-contained, has been moved to a new `static/js/illustrations.js` file. This significantly slims down `main.js`, making it easier to navigate and maintain, and improves the overall organization of the frontend code.