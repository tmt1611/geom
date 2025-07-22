### Action System Redesign: "Never Useless" Actions

In this iteration, I've performed a significant redesign of the game's action system to align with the principle that an action, once chosen, should always have a meaningful effect on the game state. This avoids "wasted" turns and makes the simulation more dynamic and interesting.

-   **Files Modified**: `game_app/game_logic.py`, `static/js/main.js`

-   **Core Change**: I refactored several actions to have both a primary (ideal) effect and a secondary (fallback) effect. The action's internal logic now determines which effect to trigger based on the current board state.

-   **Specific Action Changes**:
    1.  **`fight_attack`**: This action has been fundamentally changed.
        -   **Primary Effect**: If the attack ray hits an enemy line, it destroys it (as before). The attack now targets the *closest* enemy line in its path.
        -   **Fallback Effect**: If the attack ray hits no enemy lines, it doesn't fizzle. Instead, it creates a new friendly point at the border where the ray terminates, similar to the `expand_extend` action. This makes aggressive strategies still contribute to board presence even without a direct target.
    2.  **`sacrifice_nova`**: This sacrifice action is now more versatile.
        -   **Primary Effect**: If the sacrificed point is near enemy lines, it unleashes a destructive nova that destroys them.
        -   **Fallback Effect**: If there are no enemy lines in range, the nova instead creates a powerful **shockwave**, pushing all nearby points (friendly and enemy) away from the blast's epicenter. This makes it a useful tool for both destruction and battlefield control.
    3.  **`sacrifice_whirlpool`**: This action now guarantees a result.
        -   **Primary Effect**: If there are other points within its potential radius, it creates a standard swirling whirlpool that pulls points in.
        -   **Fallback Effect**: If the sacrificed point is isolated and would create an empty whirlpool, the action instead "fizzles" and creates a small, temporary **fissure** on the map. This turns a potentially useless action into a temporary terrain-blocking move.

-   **System-level Improvements**:
    -   **Simplified Preconditions**: The logic in `_get_all_actions_status` has been simplified. Instead of complex checks to pre-validate every possible target, it now uses simpler checks (e.g., "does the team have lines?"). The complex branching logic now resides within the action functions themselves.
    -   **Code Cleanup**: As part of the refactor, the now-redundant `_find_possible_line_attacks` helper function was removed, and the action functions were cleaned up to be more self-contained.
    -   **Frontend Visuals**: New visual effects were added in `static/js/main.js` to represent the new fallback action outcomes (`attack_miss_spawn`, `nova_shockwave`, `whirlpool_fizzle_fissure`), ensuring the user can see what happened.