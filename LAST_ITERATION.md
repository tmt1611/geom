This iteration focused on refactoring the codebase to be more data-driven and consistent, following the principles of clean code and reducing repetition. The key changes involved:
1.  **Dynamically Generating Action Preconditions:** The large, manually maintained dictionary of action precondition checks in `game_logic.py` was replaced with a dynamic system that generates it from the existing `ACTION_MAP`. This reduces code duplication and simplifies the process of adding new actions.
2.  **Centralizing Structure Definitions:** Simple point statuses like `stasis_points` and `isolated_points` were moved from hardcoded logic into the central `structure_data.py` registry. This allows their properties (e.g., whether they make a point "critical") and cleanup logic to be managed in one place.
3.  **Consistent ID Generation:** Instances of manual `uuid` generation for new points were replaced with the centralized `game._generate_id()` helper method, ensuring all new game objects follow a consistent ID format.

### Changes
*   **Refactored `game_logic.py`:**
    *   The `_init_action_preconditions` method now dynamically builds the precondition mapping from `ACTION_MAP`, eliminating over 50 lines of boilerplate code.
    *   The `_cleanup_structures_for_point` method was simplified by removing hardcoded logic for `stasis_points` and `isolated_points`, which are now handled by the generic structure cleanup loop.
*   **Updated `structure_data.py`:**
    *   Added definitions for `stasis_points` and `isolated_points` to the `STRUCTURE_DEFINITIONS` registry, making them part of the data-driven system.
*   **Standardized ID Generation:**
    *   Corrected manual `uuid` calls in `fight_actions.py` and `turn_processor.py` to use the standard `self.game._generate_id()` method.

These changes make the codebase more robust, maintainable, and easier to extend with new game mechanics in the future.