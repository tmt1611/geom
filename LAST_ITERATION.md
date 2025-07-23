This iteration focuses on improving the accuracy and clarity of the game's action logic by refactoring several action handlers. The primary goal is to make the "precondition checks" more precise, which benefits both the AI's action selection and the user-facing "Action Preview" panel.

**Key Changes:**

1.  **Refactored `form_monolith` and `form_purifier`:**
    *   In `game_app/actions/fortify_actions.py`, the complex logic for finding valid geometric formations (rectangles for Monoliths, pentagons for Purifiers) was extracted from the main action methods into dedicated private helper methods (`_find_possible_monoliths_and_fallbacks`, `_find_possible_purifiers`). This improves code organization by separating the "finding" logic from the "acting" logic.
    *   The action precondition checks (`can_perform_...`) for these actions now use these helpers. Previously, they only checked for a minimum number of points, which was inaccurate. Now, an action is only considered "possible" if a valid geometric formation actually exists on the board, leading to smarter AI choices and more accurate UI feedback.
    *   The main action methods (`form_monolith`, `form_purifier`) were simplified to use the new helpers, making them cleaner and more focused.
    *   A minor bug in `form_purifier`'s state update logic was fixed by using `setdefault` for safer dictionary manipulation.

This refactoring makes the code cleaner and the game simulation more robust by ensuring that actions are only attempted when they have a genuine chance of succeeding.