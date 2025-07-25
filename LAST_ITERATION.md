This iteration focuses on implementing a new, geometry-rich action for Territories as specified in `design.md`.

1.  **New Geometry Helper:**
    *   Created a new reusable helper function `get_angle_bisector_vector` in `game_app/geometry.py`. This function calculates the normalized vector of an angle's bisector given three points forming the angle.
    *   Refactored the existing `rune_shoot_bisector` action (for V-Runes) in `game_app/actions/rune_actions.py` to use this new, more robust helper function.

2.  **New Territory Action: `Territory Tri-Beam`**
    *   Added a new action, `fight_territory_bisector_strike`, as described in `design.md`. This action allows a claimed territory (a triangle) to fire three beams along its angle bisectors.
    *   The action was added to `game_app/action_data.py` with a display name, description, and log generators.
    *   The core logic was implemented in `game_app/actions/fight_actions.py`, including a `can_perform_territory_bisector_strike` precondition check.
    *   The action's logic reuses the `_find_closest_attack_hit` helper, allowing it to correctly interact with shields (and Cross-Runes) and find the nearest target.
    *   If a beam misses, it creates a new point on the border, providing a fallback consistent with other ranged attacks.

3.  **Documentation:**
    *   The new "Territory Tri-Beam" action has been added to `rules.md` to keep the documentation in sync with the game's mechanics.