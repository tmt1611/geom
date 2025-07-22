### New "Rift Trap" Sacrificial Action

This iteration introduces a new sacrificial action with a safe fallback, directly addressing user feedback to create more dynamic and strategic options. This enhances the game by adding a layer of tactical area denial and delayed rewards.

-   **Files Modified**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`, `LAST_ITERATION.md`

-   **New Content**:
    -   **New Action: `[SACRIFICE] Create Rift Trap`**:
        -   **Mechanic**: A team can sacrifice one of its non-critical points to lay a `Rift Trap` on the grid.
        -   **Trigger**: The trap is armed for 3 turns. If an enemy point moves into its radius, the trap detonates, destroying the enemy point and the trap itself.
        -   **"Never Useless" Fallback**: If the trap remains untriggered for its full duration, it safely collapses and transforms back into a new point for the team that created it. This provides a guaranteed (though delayed) return on investment, making the action never truly wasted.

-   **Code & Rule Updates**:
    -   `game_logic.py`:
        -   Added state management for `rift_traps`.
        -   Implemented the `sacrifice_action_rift_trap` function.
        -   Added turn-based logic in `_start_new_turn` to handle trap triggering and expiration.
        -   Integrated the new action into the game's decision-making (weights, preconditions) and logging systems.
    -   `static/js/main.js`:
        -   Added a `drawRiftTraps` function to render the armed traps on the grid with a subtle, flickering visual effect.
        -   Implemented new visual effects for the trap being set, triggering on an enemy, and expiring safely into a new point.
    -   `rules.md`: Updated the rules to clearly explain the new `Create Rift Trap` action, its trigger condition, and its expiration-based fallback.