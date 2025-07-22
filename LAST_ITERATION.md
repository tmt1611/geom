### Action System Redesign (Part 4): "Never Useless" Fight Actions

This iteration continues the work on the action system, focusing on making several key `FIGHT` actions more robust by giving them useful fallback effects. This reduces the number of "wasted" turns and adds another layer of strategic depth, as a failed attack can now pivot into a defensive or expansive outcome.

-   **Files Modified**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`

-   **Core Changes**:
    -   **`fight_action_pincer_attack`**:
        -   **Primary Effect**: Two friendly points flank and destroy an enemy point.
        -   **Fallback Effect**: If no valid pincer target can be found, the two chosen points now create a small, temporary **Barricade** between them, pivoting a failed attack into a defensive maneuver.

    -   **`fight_action_territory_strike`**:
        -   **Primary Effect**: A large territory fires a projectile to destroy the nearest enemy point.
        -   **Fallback Effect**: If there are no vulnerable enemy points on the board, the territory now reinforces its own three boundary lines, increasing their strength and durability.

    -   **`fight_action_sentry_zap`**:
        -   **Primary Effect**: A Sentry structure fires a precision shot to destroy an enemy point.
        -   **Fallback Effect**: If the zap has no valid target in its line of fire, the beam now travels to the edge of the grid and creates a new friendly point, similar to the `fight_attack` miss effect.

-   **Frontend & Documentation**:
    -   Added new visual effects in `static/js/main.js` to clearly communicate when these fallback effects occur.
    -   Updated the action descriptions in `rules.md` to reflect the new dual-outcome nature of these three actions.
    -   Added corresponding log messages in `game_logic.py` for each new fallback.

-   **Refactoring**:
    -   The internal logic for finding pincer attacks was moved directly into the action function, removing the need for a separate, expensive helper function (`_find_possible_pincers`) and simplifying the precondition checks.