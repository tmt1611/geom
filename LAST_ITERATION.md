This iteration focused on improving code quality, robustness, and developer experience through several refactorings and bug fixes.

1.  **Refactored Rune Point Detection:** The logic for identifying which points are part of a "critical" rune structure (`_get_all_rune_point_ids` in `game_logic.py`) was rewritten. It no longer depends on manually maintained lists of dictionary keys. Instead, it dynamically inspects rune data to identify point IDs. This fixes a bug where some rune points (e.g., the legs of a V-Rune) were not correctly marked as critical and could be sacrificed, breaking the rune.

2.  **Code Cleanup:**
    *   Removed duplicated `_process_scorched_zones` method from `game_app/turn_processor.py`.
    *   Removed duplicated `drawScorchedZones` function from `static/js/main.js`.

3.  **Improved Developer Experience and Robustness:**
    *   The list of watched files in `game_app/utils.py` was significantly expanded to include all Python action handlers, data files, and frontend assets. This ensures the developer-mode "file changed" warning works correctly for all relevant files.
    *   Added `structure_data.py` to the list of files fetched for the in-browser Pyodide mode in `static/js/api.js`. This prevents potential `ModuleNotFoundError` errors when running the game as a static site.

### Changes
*   **`game_app/game_logic.py`:**
    *   Removed the `_RUNE_LIST_POINT_ID_KEYS` and `_RUNE_SINGLE_POINT_ID_KEYS` class variables.
    *   Replaced the implementation of `_get_all_rune_point_ids` with a more robust version that dynamically finds point IDs in rune data.
*   **`game_app/turn_processor.py`:**
    *   Deleted a duplicated `_process_scorched_zones` method.
*   **`game_app/utils.py`:**
    *   Expanded the `WATCHED_FILES` list to be comprehensive.
*   **`static/js/api.js`:**
    *   Added `structure_data.py` to the `pyodideFileStructure` dictionary.
*   **`static/js/main.js`:**
    *   Deleted a duplicated `drawScorchedZones` function.

These changes enhance code maintainability, fix subtle bugs in the game logic and static deployment mode, and improve the development workflow.