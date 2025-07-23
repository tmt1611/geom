This iteration focuses on cleaning up the codebase by removing redundant data structures from the main `Game` class.

**Summary of Changes:**

1.  **Refactor `game_logic.py`:** Large dictionaries (`ACTION_GROUPS`, `ACTION_MAP`, etc.) were being copied from `game_data.py` into the `Game` class as class attributes. This was redundant. I have removed these attributes from the `Game` class. All logic within `game_logic.py` now directly accesses these constants from the `game_data` module, adhering to the DRY (Don't Repeat Yourself) principle.

2.  **Update `routes.py`:** The API endpoint for retrieving all action descriptions (`/api/actions/all`) was previously accessing the data from the `game` instance. It has been updated to import `game_data` and use the constants directly, reflecting the change in `game_logic.py`.

3.  **Update `static/js/api.js`:** The Pyodide (in-browser Python) mode was also accessing these data structures through the `game` object proxy. I've updated the Pyodide initialization to also create a proxy for the `game_data` module. The JavaScript functions now correctly retrieve action information from this new `game_data` proxy when running in static mode.

This refactoring makes the code cleaner, reduces memory usage by avoiding data duplication, and centralizes the single source of truth for game data constants within the `game_data.py` module.