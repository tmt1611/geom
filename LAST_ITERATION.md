This iteration refactors the structure detection logic in `game_logic.py` to be more data-driven and less repetitive, following the DRY (Don't Repeat Yourself) principle.

**Summary of Changes:**

1.  **Centralize Formation Checking Logic (`structure_data.py`):**
    *   The `STRUCTURE_DEFINITIONS` registry in `structure_data.py` has been extended with new keys: `formation_checker` and `formation_inputs`.
    *   These keys store the name of the corresponding check method in `FormationManager` and the data it requires (e.g., points, lines, territories), respectively. This turns the registry into a single source of truth for how structures are defined and detected.

2.  **Generalize Structure Updates (`game_logic.py`):**
    *   The `_update_structures_for_team` method has been rewritten. It now iterates through the `STRUCTURE_DEFINITIONS` registry, dynamically calling the appropriate checker method from `FormationManager` with the correct arguments for each structure type.
    *   This eliminates the need for several repetitive, single-purpose update methods (`_update_nexuses_for_team`, `_update_prisms_for_team`, `_update_trebuchets_for_team`), which have been deleted. The code is now cleaner and easier to extend with new structures.

3.  **Corrected Logic for Bonus Actions:**
    *   The call to update structures is now correctly placed within `_build_action_queue`. This ensures that bonus actions (e.g., from a Nexus) are granted based on the state at the beginning of the turn.
    *   A clarifying comment was added to `run_next_action` to explain why `_update_structures_for_team` is still called there (to re-sync state after other teams' actions within the same turn).

This refactoring makes the system for detecting new game structures more robust, maintainable, and extensible. Adding a new structure that is formed from points and lines now only requires an entry in the `STRUCTURE_DEFINITIONS` registry and a corresponding checker method in `FormationManager`, with no changes needed in `game_logic.py`.