This iteration introduces a significant code cleanup by refactoring line deletion logic into a centralized helper method. This adheres to the DRY (Don't Repeat Yourself) principle and makes the codebase cleaner and easier to maintain.

**Key Changes:**

1.  **Centralized Line Deletion Logic:**
    *   Identified that the logic for deleting a line and its associated properties (shields, strength) was duplicated across more than 10 different methods in the 5 action handler files.
    *   Created a new helper method, `_delete_line(line_to_delete)`, in `game_logic.py`. This method robustly removes a line from the main list and also cleans up its corresponding entries in the `shields` and `line_strengths` dictionaries.
    *   Refactored `_cleanup_structures_for_point` to use this new helper, simplifying its own logic for removing lines connected to a deleted point.
    *   Replaced all manual line deletion code blocks in `expand_actions.py`, `fight_actions.py`, `rune_actions.py`, and `sacrifice_actions.py` with a single call to the new `_delete_line` helper. This greatly reduces code duplication and ensures that line deletion is handled consistently everywhere.