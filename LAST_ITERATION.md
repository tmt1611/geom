This iteration introduces a major refactoring of the game's action selection logic for better maintainability, adds a new high-level "Purifier" structure to expand strategic options, and polishes the control panel UI for a more intuitive user experience.

### 1. Code Refactoring: Action Selection System

-   **File**: `game_app/game_logic.py`
-   **Change**: The core action selection method, `_choose_action_for_team`, has been significantly refactored. The monolithic `action_preconditions` dictionary was replaced with a new helper method, `_get_possible_actions`. This new method contains a registry of lambda functions, each responsible for checking if a single action is currently possible for a given team.
-   **Benefit**: This change dramatically improves code readability and maintainability. The logic for determining if an action is possible is now cleanly separated from the logic of weighting and selecting an action. This makes it much easier to add, remove, or debug individual actions in the future without altering the core selection loop.

### 2. New Feature: The Purifier

-   **Files**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`
-   **Change**: A new strategic structure, the **Purifier**, has been added to the game.
    -   **Formation**: It is formed via the new `[FORTIFY] Form Purifier` action, which requires a team to create a geometrically-perfect regular pentagon with five of its points and all five connecting perimeter lines. A new helper function, `is_regular_pentagon`, was added to detect this complex shape.
    -   **Ability**: A team with a Purifier unlocks the `[FIGHT] Purify Territory` action. This powerful ability allows the Purifier to "cleanse" the nearest enemy-claimed territory, neutralizing it and making its corner points vulnerable again.
    -   **Frontend**: The Purifier points are rendered as a distinct star shape for easy identification. The live stats panel now tracks the number of active Purifiers for each team. Visual effects were added for its formation and for the territory cleansing action.
-   **Benefit**: The Purifier introduces a high-investment, high-reward counter-strategy to teams focusing on area control (`Fortify Territory`). This adds a new layer of strategic depth and encourages more diverse geometric constructions on the battlefield.

### 3. UI/UX Improvements

-   **File**: `templates/index.html`
-   **Change**: The "Restart Simulation" and "Reset Game" buttons have been moved from their disparate locations and grouped together into a new "Game Management" fieldset in the control panel.
-   **Benefit**: This provides a more logical and intuitive layout for the user. It clarifies the distinction between restarting the current simulation and resetting the entire game back to the setup phase, preventing potential confusion.

### 4. General Code Cleanup

-   **File**: `game_app/game_logic.py`
-   **Change**: The internal method `_triangle_centroid` was renamed to the more general `_points_centroid` and is now used for calculating the center of any set of points, including for the new Purifier and existing territory strikes. This removes redundant code and improves clarity.