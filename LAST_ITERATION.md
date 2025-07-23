This iteration focuses on improving the user interface of the Action Guide and cleaning up the Python backend code by fixing a bug and performing a minor refactoring.

### UI/UX Improvements: Action Guide

1.  **More Compact and Informative Layout**: The layout of the Action Guide has been completely redesigned to be more compact and scannable.
    *   In `static/css/style.css`, the action cards were changed from a tall, vertical layout (illustration on top) to a wider, horizontal layout (illustration on the left, text on the right).
    *   Cards now have a fixed height (`140px`), making the grid of actions look much neater and more organized.
    *   The illustration canvas is now a square (`140x140px`), providing a consistent aspect ratio for all visuals.
    *   Long action descriptions will now scroll within the text area of the card, preventing them from breaking the layout.
    *   In `static/js/main.js`, the canvas drawing dimensions were updated to match the new layout, ensuring illustrations are rendered correctly without distortion.

### Code Cleanup and Bug Fixes

1.  **Bug Fix in `focus_beam` Action**: A critical bug was identified and fixed in the `focus_beam` action's targeting logic (`game_app/actions/rune_actions.py`).
    *   The code was attempting to find high-value targets (like Bastion cores) from a list of points that *already excluded* those same targets. This meant the primary effect of the action could never trigger.
    *   The logic was corrected to check for high-value targets from a list of all enemy points first, ensuring the action works as intended by the game rules.

2.  **Code Refactoring (`fight_actions.py`)**: A small refactoring was performed to remove redundant code.
    *   A private helper method, `_get_vulnerable_enemy_points`, existed solely to call the main implementation in `game_logic.py`. This proxy method has been removed.
    *   All calls within `FightActionsHandler` that used this proxy now directly call the canonical method on the game instance (`self.game._get_vulnerable_enemy_points`), making the code slightly cleaner and more direct.