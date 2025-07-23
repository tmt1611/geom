This iteration focused on a significant code refactoring to improve encapsulation and maintainability, specifically around how action preconditions are checked.

### 1. Decoupling Action Preconditions from `Game` Class
- The large, hard-to-maintain dictionary of lambda functions inside `game_logic.py`'s `_get_all_actions_status` method has been removed.
- **`game_app/actions/expand_actions.py`**: Added `can_perform_*` methods (e.g., `can_perform_add_line`) for each action in the handler. These methods encapsulate the logic for checking if an action is valid (e.g., having enough points, finding a valid target).
- **`game_app/actions/fight_actions.py`**: Added corresponding `can_perform_*` methods for all fight-related actions.
- **`game_app/actions/fortify_actions.py`**: Added corresponding `can_perform_*` methods for all fortify, defend, and terraform actions managed by this handler.

### 2. Centralized Precondition Dispatch in `game_logic.py`
- A new method, `_init_action_preconditions`, was added to the `Game` class constructor.
- This method creates a dispatch map (`self.action_preconditions`) that links action names (e.g., `'expand_add'`) to the new `can_perform_*` methods in their respective handlers.
- For actions whose logic has not yet been moved to a handler (like `Sacrifice` and `Rune` actions), private helper methods (e.g., `_can_perform_sacrifice_nova`) were created within the `Game` class to contain their precondition logic, and these were also added to the dispatch map.
- The `_get_all_actions_status` method was refactored into a simple loop that iterates through the `action_preconditions` map, calling the appropriate check for each action.

This refactoring makes the `Game` class less aware of the internal logic of each action, delegating that responsibility to the specialized handlers. This improves code organization, reduces coupling, and makes it easier to add or modify actions and their validation rules in the future.