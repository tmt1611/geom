# Iteration Analysis and Changelog

## 1. Analysis Summary
This iteration focused on improving the backend game logic based on user feedback, specifically addressing suggestions #7 and #8. The primary goals were to make the action system more robust, ensure all point coordinates are integers, and guarantee that teams always have a valid move available.

## 2. Implemented Features and Improvements

### Backend (`game_logic.py`)

1.  **Robust Action System (Suggestion #8):**
    -   Several actions that could previously "miss" or fail after being selected (e.g., `attack_line`, `extend_line`, `convert_point`, `fracture_line`) have been refactored.
    -   These actions now first find all possible *successful* outcomes, then randomly choose one to execute. This prevents turns where a team attempts an action that is impossible to complete (like an attack that can't hit anything), making the simulation flow more logically and efficiently.
    -   The `run_next_action` loop is now primarily for handling actions with inherent randomness or for cases where simple preconditions pass but no complex valid outcome is found.

2.  **Guaranteed Valid Actions (Suggestion #8):**
    -   A new action, **`expand_action_spawn_point`**, has been added. This allows a team to create a new point near an existing one.
    -   This action is available even if a team has only one point left, ensuring that no team is ever completely "stuck" without a valid move.
    -   It is given a low weight in the action selection process, making it a last-resort or recovery-style move.

3.  **Integer Coordinates (Suggestion #7):**
    -   The `expand_action_fracture_line` was updated to ensure the new point it creates always has integer coordinates by rounding the calculated position. This brings it in line with other actions and maintains grid consistency.

4.  **Action Balancing and Preconditions:**
    -   The `sacrifice_action_nova_burst` now requires a team to have more than two points, making it a more strategic and less self-destructive choice.
    -   Precondition checks for actions like `expand_fracture_line` and `sacrifice_nova` have been made more precise in the `_choose_action_for_team` method to better reflect their possibilities.

### Rules (`rules.md`)
-   The new "Spawn Point" action has been documented in `rules.md` to reflect its addition to the game.