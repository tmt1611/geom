This iteration focused on cleaning up the action handler code by refactoring repeated logic into centralized helper methods. Specifically, the creation of temporary structures like `barricades` and `fissures` was duplicated across multiple action files.

By moving this logic into new helper methods within the main `Game` class, I have reduced code duplication, improved maintainability, and ensured these operations behave consistently wherever they are used.

**Key Changes:**

1.  **New Helper Methods in `game_logic.py`:**
    *   Added `_create_temporary_barricade` to handle the creation and state management of barricades.
    *   Added `_create_random_fissure` to centralize the logic for creating randomly oriented fissures around a center point.

2.  **Refactored Action Handlers:**
    *   Updated `fight_actions.py`, `fortify_actions.py`, and `rune_actions.py` to call the new `_create_temporary_barricade` helper instead of implementing the logic inline.
    *   Updated `fight_actions.py`, `sacrifice_actions.py`, and `rune_actions.py` to use the new `_create_random_fissure` helper, which also fixed a minor bug related to coordinate clamping.

3.  **Improved Code Consistency:**
    *   Standardized point creation in `expand_actions.py`'s `grow_line` action to use the `clamp_and_round_point_coords` helper, making it more robust and consistent with other actions.
    *   Made a minor improvement in `rune_actions.py` to use `setdefault` for list appends, making the code more defensive.

These changes make the action handlers cleaner, more concise, and easier to understand, while improving the overall robustness of the game logic.