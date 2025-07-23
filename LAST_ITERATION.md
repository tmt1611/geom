This iteration introduces a new strategic action based on warfare concepts and performs a clean code refactoring for better consistency.

### 1. New Warfare Action: Scorch Territory

Drawing from the concept of "scorched earth" tactics, a new `Sacrifice` action has been added:

*   **Action:** `Scorch Territory`
*   **Effect:** A team can sacrifice one of its claimed territories. The points and lines of the territory are destroyed, and the triangular area becomes a "scorched zone" for several turns.
*   **Strategic Impact:** Scorched zones are impassable. No points can be created inside them, and line-based actions (like attacks or extensions) cannot cross their boundaries. This provides a powerful area-denial tool, allowing teams to create defensive barriers or choke points at the cost of their own assets.
*   **Implementation:**
    *   A new `scorch_territory` method was added to `sacrifice_actions.py`.
    *   The game state now tracks `scorched_zones`, which decay over time via the `turn_processor.py`.
    *   Core geometry functions (`is_spawn_location_valid`, `is_ray_blocked`) in `geometry.py` were updated to account for these new zones.
    *   The frontend in `main.js` now renders scorched zones with a distinct dark, fiery visual effect.

### 2. Code Refactoring & Cleanup

To improve code consistency and readability, a minor refactoring was performed on the line-shielding action:

*   The action key `defend_shield` was renamed to `fortify_shield` to align with the standard `group_action` naming convention.
*   The corresponding method in `fortify_actions.py` was renamed from `protect_line` to `shield_line`.
*   All references in `game_data.py` and `game_logic.py` were updated accordingly.

This change, while small, makes the action's identity clearer and the codebase easier to navigate.