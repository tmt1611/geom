This iteration integrates the rune detection system into the main data-driven structure management registry, removing special-case code and making the system more unified and extensible.

**Summary of Changes:**

1.  **Centralize Rune Definitions (`structure_data.py`):**
    *   All eleven rune types (`cross`, `v_shape`, `shield`, etc.) have been added as definitions to the `STRUCTURE_DEFINITIONS` registry.
    *   A new `storage_type` called `team_dict_of_structures` was introduced to handle the unique storage pattern of runes (`state['runes'][teamId][rune_type]`).
    *   Each rune definition now specifies its `structure_subtype_key` (e.g., 'cross'), `formation_checker` method, and required `formation_inputs`.
    *   The `point_id_keys` have been defined for each rune, including a special `('list_of_lists', None)` type to handle formatters that return a simple list of point IDs.

2.  **Generalize Structure Update Logic (`game_logic.py`):**
    *   The `_update_structures_for_team` method was enhanced to handle the new `team_dict_of_structures` storage type, allowing it to manage runes just like any other structure.
    *   The special-cased `_update_runes_for_team` method has been completely removed.

3.  **Unify Critical Point Detection (`game_logic.py`):**
    *   The `_get_critical_structure_point_ids` method was updated to parse point IDs from rune definitions by understanding the new storage type and `point_id_keys`.
    *   The now-redundant `_get_all_rune_point_ids` helper method has been deleted.

This refactoring centralizes all structure and rune definitions into a single registry, making the system significantly cleaner, more consistent, and easier to extend. Adding or modifying runes now follows the exact same data-driven pattern as any other complex structure in the game.