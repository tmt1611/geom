This iteration focuses on improving code quality by centralizing a piece of repeated logic. The concept of which points are "immune" to standard attacks (e.g., fortified points, bastion components) was being determined in multiple places.

**Key Changes:**

1.  **New Helper `_get_all_immune_point_ids` in `game_logic.py`:**
    *   A new private method was created to act as a single source of truth for defining which points are immune. It combines fortified points, bastion points, and points in stasis into a single set.

2.  **Refactored `_get_vulnerable_enemy_points` in `game_logic.py`:**
    *   This method now calls the new `_get_all_immune_point_ids` helper, simplifying its implementation and ensuring it always uses the canonical definition of immunity.

3.  **Simplified `fight_actions.launch_payload`:**
    *   The `launch_payload` action previously had to manually construct the set of immune points to find a fallback target. This logic was removed and replaced with a call to the new centralized helper, making the action's code cleaner and more maintainable.

These changes reduce code duplication and make it easier to modify or extend the rules for point immunity in the future, as the logic is now contained in one place.