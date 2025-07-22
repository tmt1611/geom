### Action System Redesign (Part 3): Whirlpool Fallback and Cleanup

This iteration completes the "never useless" action system redesign by implementing a fallback effect for the `sacrifice_whirlpool` action, as suggested. This ensures that even when a whirlpool is created in an empty area, the action still has a tangible, strategic effect on the game board.

-   **Files Modified**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`

-   **Core Change**:
    -   **`sacrifice_create_whirlpool`**: This action has been redesigned to be more dynamic and avoid wasted turns.
        -   **Primary Effect**: Sacrifices a friendly point to create a vortex that pulls all nearby points towards its center for several turns. This happens only if there are other points within its radius upon creation.
        -   **Fallback Effect**: If no points are nearby to be affected, the sacrifice is not wasted. Instead of a whirlpool, the action creates a small, temporary **Fissure** on the map. This terrain feature can block movement and other actions, providing a different kind of strategic value.

-   **Frontend & Documentation**:
    -   Added a new visual effect in `static/js/main.js` for the "fizzle" case of the whirlpool, reusing the existing fissure-drawing logic (`growing_wall`). This provides clear visual feedback for the fallback effect.
    -   Updated the action description in `rules.md` to accurately reflect the new dual-outcome nature of the whirlpool action.
    -   Added a new log message in `game_logic.py` to ensure the game log clearly communicates when the fallback effect occurs.