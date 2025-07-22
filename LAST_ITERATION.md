### Action System Redesign (Part 8): More "Never Useless" Actions

This iteration continues the overarching goal of making every action meaningful by adding intelligent fallback behaviors to more actions. This ensures a team's turn is never truly wasted and adds more layers of dynamic behavior to the simulation. The focus this time was on `Fortify` and `Rune` actions that previously failed if their primary targets or conditions were not met.

-   **Files Modified**: `game_app/game_logic.py`, `LAST_ITERATION.md`

-   **Core Changes**:
    -   **`fortify_action_claim_territory`**:
        -   **Primary Effect**: Claims a new triangle of points as territory.
        -   **New Fallback**: If no new triangles are available to be claimed, the action now strengthens the boundary lines of an *existing* friendly territory, making it more resilient.

    -   **`fight_action_purify_territory`**:
        -   **Primary Effect**: A Purifier structure cleanses a nearby enemy territory, removing its fortified status.
        -   **New Fallback**: If no enemy territories are available to cleanse, the Purifier now emits a pulse that pushes nearby enemy points away from it, disrupting enemy formations.

    -   **`rune_action_hourglass_stasis`**:
        -   **Primary Effect**: An Hourglass Rune freezes a nearby enemy point in time, making it unable to act.
        -   **New Fallback**: If there are no valid enemy targets in range, the rune's power is turned inward, transforming a nearby friendly point (not part of the rune itself) into a temporary gravitational anchor that pulls enemies towards it.

    -   **`rune_action_focus_beam`**:
        -   **Primary Effect**: A Star Rune fires a powerful beam to destroy a high-value enemy structure (Wonder, Bastion Core, Monolith point).
        -   **New Fallback**: If no high-value targets are available, the beam will instead target and destroy a regular, vulnerable enemy point.

-   **Code Quality**:
    -   The `ACTION_DESCRIPTIONS` dictionary was completely reorganized and updated to include user-friendly names for all primary and fallback action types, improving clarity in the frontend action preview panel.

-   **Precondition Logic**:
    -   The precondition checks for the modified actions in `_get_all_actions_status` were updated to account for their new fallbacks, ensuring they are correctly identified as "valid" actions more often.