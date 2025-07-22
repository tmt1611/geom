This iteration continues the major refactoring of the `game_logic.py` file to improve code organization and maintainability, focusing on separating action logic from the main game class.

### Refactoring Action Logic into Handlers

- **Problem:** `game_logic.py` was still extremely large, with the bulk of its size coming from the implementations of dozens of game actions directly within the `Game` class. This made the class unwieldy and violated the Single Responsibility Principle.

- **Solution:** I have initiated a structural refactoring to move action implementations into separate, dedicated "handler" classes.
    1. A new directory, `game_app/actions/`, has been created to house these handlers.
    2. A new file, `game_app/actions/expand_actions.py`, was created.
    3. All action methods related to the 'Expand' category (e.g., `expand_action_add_line`, `expand_action_extend_line`) and their private helper methods (`_find_possible_extensions`, `_find_fracturable_lines`) have been moved from the `Game` class into a new `ExpandActionsHandler` class within this file.
    4. The `Game` class now instantiates `ExpandActionsHandler` and the original `expand_action_*` methods have been converted into simple one-line wrappers that delegate the call to the handler instance.
    5. Helper methods that are used by multiple action categories (like `_get_extended_border_point`) were correctly identified and left within the main `Game` class to be shared.

This change successfully extracts over 200 lines of logic from `game_logic.py` into a more focused module. It establishes a clear pattern for refactoring the remaining action categories in future iterations, significantly improving the project's architecture and making the core game logic file cleaner and easier to manage.