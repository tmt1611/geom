### 1. Major UI/Layout Overhaul for Gameplay Phase
- **Files**: `templates/index.html`, `static/css/style.css`, `static/js/main.js`
- **Change**: The user interface during the game simulation phase (`game-running`) has been completely redesigned for better usability and information hierarchy.
  - The previous layout with a right-side info panel and a separate bottom control bar has been replaced with a clean, two-column layout: the game grid on the left and a single, comprehensive "dashboard" panel on the right.
  - All game controls (`Next Action`, `Auto-Play`, `Restart`, `End Game`) have been moved from the bottom bar into a dedicated `Game Controls` fieldset at the top of the right-hand dashboard. This fixes a bug where these buttons were not visible during gameplay.
  - The right-hand panel is now vertically organized, containing Game Controls, turn/action counters, live team stats, the action preview, and the game log. This aligns with the request to have these elements organized "in their own column". The entire panel is now scrollable to accommodate all information on any screen size.
- **Benefit**: This change resolves the critical bug of invisible controls and provides a much cleaner, more intuitive layout for observing and interacting with the game as it unfolds.

### 2. Code Refactoring and Simplification
- **Files**: `game_app/game_logic.py`
- **Change**: To improve code quality and reduce redundancy, a new helper method `_get_vulnerable_enemy_points` was created. This method centralizes the logic for identifying which enemy points can be targeted by standard actions (i.e., not immune due to being fortified, part of a bastion, or in stasis).
- **Benefit**: This helper function simplified the code in four different action-finder methods (`_find_possible_conversions`, `_find_possible_pincers`, `_find_possible_territory_strikes`, `rune_action_hourglass_stasis`), making the game logic easier to read, maintain, and preventing potential inconsistencies in targeting rules.