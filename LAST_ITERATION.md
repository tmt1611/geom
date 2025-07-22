### Action System Redesign (Part 6): Completing "Never Useless" Actions & Cleanup

This iteration finalizes the core goal of making every action meaningful by adding fallbacks to the remaining actions that could previously fizzle or fail after being chosen. This ensures that a team's turn is never truly wasted and adds more layers of dynamic behavior to the simulation. Several significant code cleanup tasks were also performed.

-   **Files Modified**: `game_app/game_logic.py`, `rules.md`, `LAST_ITERATION.md`

-   **Core Changes**:
    -   **Code Cleanup**: Refactored `game_app/game_logic.py` to remove several duplicated or erroneous function definitions (`fight_action_territory_strike`, `fight_action_launch_payload`, `fight_action_chain_lightning`), simplifying the codebase and improving clarity. A helper function `_get_eligible_phase_shift_lines` was also created to reduce code duplication.

    -   **`fight_action_bastion_pulse`**:
        -   **Primary Effect**: A bastion sacrifices a prong to destroy crossing enemy lines.
        -   **New Fallback**: If the pulse fizzles (e.g., because the bastion dissolves after the sacrifice), the sacrificed prong's energy is now released as a **local shockwave**, pushing all nearby points away.

    -   **`sacrifice_action_phase_shift`**:
        -   **Primary Effect**: Sacrifices a line to teleport one of its points to a new location.
        -   **New Fallback**: The action now pays its cost (sacrificing the line) upfront. If a valid new location cannot be found, the sacrificed line's energy now implodes into the *other* endpoint, turning it into a temporary **gravitational anchor** that pulls in nearby enemies.

    -   **`fight_action_chain_lightning`**:
        -   **Primary Effect**: A Conduit sacrifices an internal point to fire a lightning bolt at a nearby enemy point.
        -   **New Fallback**: If the attack fails to find a target (e.g., no enemies in range or the conduit's endpoints are gone), the sacrificed point now explodes in a **mini-nova**, destroying any nearby enemy lines.

-   **Documentation**:
    -   Updated the action descriptions in `rules.md` to reflect the new tiered outcomes for these actions.
    -   Added corresponding log messages in `game_logic.py` for each new fallback behavior.