### Action System Redesign (Part 9) & New T-Rune

This iteration continues the goal of making every action meaningful by adding intelligent fallback behaviors. It also expands the game's strategic depth by introducing a new geometric formation: the **T-Rune**.

-   **Files Modified**: `game_app/game_logic.py`, `rules.md`, `LAST_ITERATION.md`

-   **New Content**:
    -   **New T-Rune**:
        -   **Formation**: A new rune formed by four points in a 'T' shape. It requires a central point connected to three other points, where two of the connections form a straight line (the stem) and the third is perpendicular to it (the head). All three connecting lines must exist.
        -   **New Action `[RUNE] T-Hammer Slam`**: The T-Rune unlocks this action. It sacrifices the 'head' point of the T to create a powerful shockwave emanating from the 'stem' line, pushing all nearby points away perpendicularly.
        -   **Fallback**: If the Hammer Slam has no points in its area of effect, it instead reinforces the two lines that form the rune's stem.

-   **"Never Useless" Action Enhancements**:
    -   **`fortify_action_claim_territory`**:
        -   **Primary Effect**: Claims a new triangle of points as territory.
        -   **New Fallback**: If no new triangles are available to be claimed, the action now strengthens the boundary lines of an *existing* friendly territory, making it more resilient.

    -   **`fight_action_purify_territory`**:
        -   **Primary Effect**: A Purifier structure cleanses a nearby enemy territory.
        -   **New Fallback**: If no enemy territories are available to cleanse, the Purifier now emits a pulse that pushes nearby enemy *points* away, disrupting enemy formations.

    -   **`rune_action_hourglass_stasis`**:
        -   **Primary Effect**: An Hourglass Rune freezes a nearby enemy point in time.
        -   **New Fallback**: If there are no valid enemy targets, the rune sacrifices one of its own points to turn another point from the rune formation into a temporary gravitational **anchor**, pulling in nearby enemies. This high-risk fallback adds another layer of strategic depth.

    -   **`rune_action_focus_beam`**:
        -   **Primary Effect**: A Star Rune fires a powerful beam to destroy a high-value enemy structure (Wonder, Bastion Core, etc.).
        -   **New Fallback**: If no high-value targets are available, the beam will instead target and destroy a regular, vulnerable enemy point, ensuring the action is still offensively useful.

-   **Code Quality**:
    -   The `ACTION_DESCRIPTIONS` dictionary and `_get_action_log_messages` helper were updated to include user-friendly names and log messages for all new primary and fallback action types.
    -   Precondition logic in `_get_all_actions_status` was updated for all modified actions to correctly reflect their new fallbacks, making them available more often.