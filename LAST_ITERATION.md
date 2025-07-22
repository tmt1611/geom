This iteration focused on fixing a critical bug and continuing the architectural improvements to the codebase.

### Bug Fix: Premature "Extinction" Game Over

-   **Problem:** A bug was reported where the game would end with an "Extinction" message even though teams still had points on the board and the turn limit had not been reached.
-   **Investigation:** The logic for triggering an "Extinction" event was tied to the creation of an empty action queue at the start of a turn. The check for "Dominance" victory (a single team remaining) was also found to be flawed, as it was based on the turn's action queue rather than the actual state of points on the board at the end of the turn.
-   **Solution:**
    1.  The `_check_end_of_turn_victory_conditions` method in `game_logic.py` was significantly improved. It now checks for victory conditions based on which teams currently have points, which is a more accurate reflection of the game state.
    2.  An explicit "Extinction" check was added to this method, ensuring the game ends immediately at the end of a turn if no teams have any points left. This is more robust than waiting for the next turn to fail to start.
    3.  The main game loop in `run_next_action` was refactored for better clarity, removing a redundant check and relying on the more robust end-of-turn checks to handle game state transitions correctly.

### Refactoring: `FightActionsHandler`

-   **Problem:** The `game_logic.py` file, while improved, still contained a large number of action implementations, making it hard to manage.
-   **Solution:** Following the pattern established in the previous iteration:
    1.  A new file, `game_app/actions/fight_actions.py`, was created.
    2.  A new `FightActionsHandler` class was implemented within this file.
    3.  All ten action methods related to the 'Fight' category (e.g., `fight_action_attack_line`, `fight_action_convert_point`) and their associated private helper methods were moved from the `Game` class into the new handler.
    4.  The `Game` class now instantiates `FightActionsHandler` and delegates all fight action calls to it.

This change extracts a significant amount of complex logic out of the main `Game` class, making the code cleaner, more modular, and easier to maintain and debug. The combination of this refactoring and the bug fix greatly improves the stability and quality of the codebase.