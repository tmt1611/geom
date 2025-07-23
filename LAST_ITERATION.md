This iteration focused on a code cleanup and simplification refactoring across all action handler modules. The goal was to reduce code duplication and improve robustness when handling point coordinates.

### 1. Centralized Coordinate Clamping and Rounding

A common pattern was identified across many action functions where new floating-point coordinates were calculated and then manually clamped to the grid boundaries and rounded to integers. This code was repetitive and slightly different in places, leading to potential inconsistencies.

*   **Action:** A new helper function, `clamp_and_round_point_coords`, was created in `game_app/geometry.py`. This function takes a coordinate dictionary and a grid size, and reliably performs the clamping and rounding operations.

*   **Benefit:** This centralizes the logic, ensuring that all new points are created using the exact same robust method.

### 2. Refactoring Action Handlers

All five action handler files (`expand_actions.py`, `fight_actions.py`, `fortify_actions.py`, `rune_actions.py`, and `sacrifice_actions.py`) were updated to import and use the new `clamp_and_round_point_coords` helper function.

*   **Examples:**
    *   In `expand_actions.py`, functions like `fracture_line`, `spawn_point`, and `create_orbital` were simplified.
    *   In `fight_actions.py` and others, functions that "push" points away from an effect now use the helper for safer coordinate updates.
    *   In `fortify_actions.py`, the `mirror_structure` action was made more robust. The original code had a check to see if a reflected point was in-bounds, but then rounded it, which could have pushed it out-of-bounds. The new logic uses the helper to safely round and clamp after the check.

This refactoring reduces the line count, simplifies the logic within each action, and makes the codebase cleaner and easier to maintain.