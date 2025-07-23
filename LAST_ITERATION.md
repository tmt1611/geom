This iteration focuses on a significant code refactoring to improve the project's structure, maintainability, and overall code quality, aligning with the "clean code" objective.

### 1. Creation of a Dedicated `RuneActionsHandler`
Previously, all logic for "Rune" actions was implemented directly within the main `game_logic.py` file, breaking the established pattern of using dedicated handlers for each action category.

- **File Created**: `game_app/actions/rune_actions.py`
- **Changes**:
    - A new `RuneActionsHandler` class was created to encapsulate all logic related to Rune actions.
    - All `rune_action_*` methods and their corresponding `_can_perform_rune_*` precondition checks were moved from `game_logic.py` into this new handler.
    - This change centralizes Rune logic and makes the `Game` class in `game_logic.py` cleaner.

### 2. Refactoring of the Action Dispatch Mechanism
The `Game` class contained numerous boilerplate wrapper methods (e.g., `expand_action_add_line`) whose only purpose was to call the corresponding method in a handler. This created unnecessary code and made the `Game` class excessively long.

- **File**: `game_data.py`
- **Changes**:
    - The `ACTION_MAP` data structure was completely redesigned. Instead of mapping an action name to a string method name on the `Game` class, it now maps to a tuple containing the **handler's attribute name** (e.g., `'expand_handler'`) and the **method name within that handler** (e.g., `'add_line'`).
    - Example: `'expand_add': 'expand_action_add_line'` became `'expand_add': ('expand_handler', 'add_line')`.

- **File**: `game_logic.py`
- **Changes**:
    - The `_choose_action_for_team` method was updated to use the new `ACTION_MAP` structure. It now dynamically gets the correct handler instance and method from the `Game` object, creating a direct link between the action name and the code that executes it.
    - **All wrapper methods** (like `expand_action_add_line`, `fight_action_attack_line`, etc.) have been **deleted**. This resulted in the removal of over 30 methods and approximately 250 lines of code from `game_logic.py`.
    - The `Game` class's `__init__` and `_init_action_preconditions` methods were updated to correctly instantiate and reference the new `RuneActionsHandler`.

This refactoring significantly slims down the `game_logic.py` file, improves the separation of concerns by placing all action logic within dedicated handlers, and makes the system for adding or modifying actions much cleaner and less error-prone.