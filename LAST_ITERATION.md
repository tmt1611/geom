### New "Plus" Rune and Action

This iteration focuses on expanding the strategic options available to players by introducing a new rune based on the user's suggestions. This continues the overarching goal of increasing strategic diversity and ensuring actions have meaningful outcomes.

-   **Files Modified**: `game_app/game_logic.py`, `rules.md`, `LAST_ITERATION.md`

-   **New Content**:
    -   **New Plus-Rune (`+`)**:
        -   **Formation**: A new rune formed by five points in a `+` shape. It requires a central point connected to four other points. These four points must form two perpendicular lines that pass through the center. All four lines connecting the center to the outer points must exist.
        -   **New Action `[RUNE] Plus Burst`**: This rune unlocks a powerful area-of-effect attack. The action sacrifices one of the rune's four outer "arm" points. Energy then fires from the center along the rune's two main axes, destroying any enemy lines in its path.
        -   **"Never Useless" Fallback**: If the `Plus Burst` attack doesn't hit any enemy lines, it doesn't go to waste. Instead, the energy is reabsorbed into the rune, reinforcing the lines of the three remaining arms.

-   **Code & Rule Updates**:
    -   `game_logic.py` was updated with the logic to detect the Plus-Rune (`_check_plus_rune`) and execute its corresponding action (`rune_action_plus_burst`).
    -   Action weights, descriptions, preconditions, and log messages were all updated to fully integrate the new action into the game's decision-making and reporting systems.
    -   `rules.md` was updated to document the new Plus-Rune, its formation, and its unique action, making the new mechanic clear to players.