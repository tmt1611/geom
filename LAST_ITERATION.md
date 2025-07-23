This iteration focused on a significant code cleanup by refactoring how action metadata is accessed throughout the application. The goal was to make `action_data.py` the true single source of truth for all action properties, reducing redundancy and improving maintainability.

**Key Changes:**

1.  **Simplified `game_data.py`:**
    *   Removed the large block of code that dynamically built several global dictionaries (`ACTION_MAP`, `ACTION_GROUPS`, etc.) at module load time.
    *   Replaced these with simple helper functions (`get_action_groups`, `get_log_generators`) that derive the necessary data structures directly from `action_data.ACTIONS` when needed. This ensures data is always fresh and avoids maintaining parallel, redundant data structures.

2.  **Refactored `game_logic.py`:**
    *   Modified all functions that previously used the dictionaries from `game_data` to access the information directly from `action_data.ACTIONS`.
    *   This affects key logic areas, including action precondition checking (`_init_action_preconditions`), probability calculations (`get_action_probabilities`), action selection (`_choose_action_for_team`), and log message generation (`_get_action_log_messages`).
    *   The logic is now more direct (e.g., using `action_data.ACTIONS[name]['group']` instead of `game_data.ACTION_NAME_TO_GROUP[name]`) and less prone to errors if new actions are added.

This refactoring makes the code cleaner, more robust, and easier to follow, as the flow of data from the central `action_data.py` file to its points of use is now explicit and direct.