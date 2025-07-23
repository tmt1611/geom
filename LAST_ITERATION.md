This iteration focuses on code cleanup and the introduction of a new tactical action inspired by warfare principles.

### 1. Code Cleanup and Bug Fixes

*   **Fixed Duplication:** Removed a duplicated `scorch_territory` method in `game_app/actions/sacrifice_actions.py` which was a remnant of a previous merge.
*   **Resolved Inconsistency:** The action to shield a line was inconsistently named `defend_shield` and `fortify_shield`. All references in `game_app/game_data.py` have been standardized to `fortify_shield` to match the rest of the codebase and its action group.
*   **Added Missing Action Data:** The `sacrifice_scorch_territory` action was missing from the `ACTION_GROUPS` and `ACTION_DESCRIPTIONS` dictionaries in `game_data.py`, causing it to not be selected by the AI. This has been corrected.

### 2. New Warfare Action: Reposition Point

Inspired by Sun Tzu's principle of "subduing the enemy without fighting," a new subtle, strategic action has been added to the `Fortify` group:

*   **Action:** `Reposition Point`
*   **Effect:** Moves a single "free" point (one not part of a critical structure like a rune or bastion) to a new nearby location.
*   **Strategic Impact:** This action allows a team to make minor tactical adjustments to its board presence. It can be used to untangle a dense cluster of points, move a point into a more advantageous position for a future formation, or subtly shift the team's center of gravity. It's a preparatory move that emphasizes positioning over direct conflict.
*   **Fallback:** If a valid new position cannot be found, the action strengthens a random friendly line, ensuring the turn is never wasted.