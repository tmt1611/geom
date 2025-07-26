Refactored internal game logic for improved clarity and maintainability.

1.  **Centralized Structure Iteration**: Introduced a new private helper method, `_iterate_structures`, in `game_logic.py`. This generator centralizes the complex logic for looping through different types of stored structures (e.g., lists, dictionaries, team-specific dictionaries) based on definitions in `structure_data.py`.

2.  **Centralized Point ID Extraction**: Added another helper, `_get_pids_from_struct`, to handle the extraction of point IDs from a generic structure object. This reduces code duplication.

3.  **Simplified Core Methods**: Refactored two key methods, `_get_critical_structure_point_ids` and `_get_all_point_flags`, to use these new helpers. This makes their own logic significantly shorter, more readable, and less prone to errors, as the complex iteration and data extraction logic is now handled by the new, single-purpose helpers.

This refactoring does not change any game rules or behavior but improves the internal consistency and organization of the codebase, making future modifications to the structure system easier.