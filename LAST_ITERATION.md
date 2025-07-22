This iteration focuses on a significant refactoring and cleanup of `game_logic.py` to improve its structure, readability, and efficiency, and to fix a critical bug.

### 1. Code Cleanup & Refactoring in `game_logic.py`

The main `Game` class has been substantially improved through the following changes:

- **Fixed Bug:** A critical bug was fixed where the `FormationManager` was being used without ever being initialized in the `Game` class. An instance is now correctly created in the `__init__` method, restoring the functionality of all rune and structure detection.
- **Removed Dead Code:** Over 400 lines of redundant and unused `_check_*_rune` methods were deleted from the `Game` class. This logic was correctly delegated to the `FormationManager` in a previous iteration, but the old methods had been left behind. Their removal greatly simplifies the file.
- **Refactored Action Dispatching:** The large `action_map` dictionary, which was previously created on every call to the `_choose_action_for_team` method, has been moved to a class-level constant `ACTION_MAP`. The method now uses this constant and `getattr` for a cleaner and more efficient implementation.
- **Refactored Log Generation:** The even larger `log_generators` dictionary inside the `_get_action_log_messages` method was refactored:
    - It was moved to a class-level constant `ACTION_LOG_GENERATORS`, decluttering the method body.
    - Lambdas inside the dictionary that required access to the `Game` instance (`self`) were made stateless. This was achieved by modifying the action methods themselves to include necessary data (like team names) in their result dictionaries.
    - This change simplifies the `_get_action_log_messages` method to a simple dictionary lookup and makes the log generation system more modular.
- **Improved Action Results:** To support the log generation refactoring, several action methods were updated to return more context in their results (e.g., the name of an affected enemy team).

These changes make `game_logic.py` shorter, cleaner, more efficient, and easier to maintain, while also fixing a significant bug related to formation detection.