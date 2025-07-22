### Action System Redesign (Part 7): Never Useless Shield and Mirror Actions

This iteration continues the overarching goal of making every action meaningful by adding intelligent fallback behaviors to several more actions. This ensures a team's turn is never truly wasted and adds more layers of dynamic behavior to the simulation. The focus this time was on `Fortify` and `Rune` actions that could previously fail if their primary targets were unavailable.

-   **Files Modified**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`, `LAST_ITERATION.md`

-   **Core Changes**:
    -   **`fortify_action_mirror_structure`**:
        -   **Primary Effect**: Reflects points across a chosen axis to create new symmetrical points.
        -   **New Fallback**: If a valid reflection cannot be found, the action now strengthens the lines connected to the points that were considered for mirroring, reinforcing the existing structure instead.
        -   **New Secondary Fallback**: If strengthening also fails, it makes a final attempt to add a new line to ensure the action is productive.

    -   **`rune_action_area_shield`**:
        -   **Primary Effect**: Protects all friendly lines inside the rune's triangular boundary with shields.
        -   **New Fallback**: If no friendly lines are found inside the rune to protect, it now emits a gentle shockwave that pushes friendly points outwards, helping to de-clutter a dense formation.

    -   **`rune_action_shield_pulse`**:
        -   **Primary Effect**: Emits a powerful shockwave that pushes all nearby *enemy* points away.
        -   **New Fallback**: If no enemies are in range to be pushed, the pulse now reverses, gently pulling nearby *friendly* points closer to the rune's center to consolidate the team's position.

-   **Visual Effects & UI**:
    -   Added new frontend visual effects in `static/js/main.js` for the new fallback actions, including a "point pull" effect for the shield pulse's new ability.
    -   Updated the data payload for these actions to include the necessary information for the new visuals.

-   **Documentation**:
    -   Updated `rules.md` to reflect the new dual-purpose nature of the modified actions.
    -   Added corresponding log messages in `game_logic.py` for each new fallback behavior.