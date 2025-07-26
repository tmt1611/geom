This iteration implements a key mechanic from `design.md` regarding sacrifice actions: **point regeneration**.

1.  **Implemented Point Regeneration:**
    *   When a non-critical point on a line is sacrificed for an action (`Nova Burst`, `Create Whirlpool`, `Rift Trap`, etc.), it now enters a "regenerating" state instead of being permanently destroyed.
    *   The point is removed from play for 3 turns. The lines it was connected to become temporarily inactive.
    *   After 3 turns, the point attempts to respawn at its original location. If the location is blocked, the regeneration fails.
    *   This adds strategic depth to sacrifices, making them less punishing and encouraging their use.

2.  **Code Changes:**
    *   Added a `regenerating_points` dictionary to the game state.
    *   Created a `_process_regenerating_points` method in `TurnProcessor` to handle the countdown and respawning logic at the start of each turn.
    *   Modified `_delete_point_and_connections` in `game_logic.py` to handle the regeneration logic conditionally, preserving line connections for when the point returns.
    *   Updated all relevant sacrifice actions in `sacrifice_actions.py` and `rune_actions.py` to trigger this new mechanic.

3.  **Updated Rules:**
    *   Added a "Sacrifice Mechanics" section to `rules.md` to clearly explain the new point regeneration feature to players.