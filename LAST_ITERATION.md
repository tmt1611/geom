This iteration focused on implementing a new action suggested by `design.md` and performing a related code cleanup for robustness.

1.  **Implemented `fight_hull_breach` Action:** Added a new `Fight` action as inspired by the `design.md` suggestion to "convert a point that is contained in the hull of the team".
    -   This action calculates the team's convex hull.
    -   **Primary Effect:** If vulnerable enemy points are inside the hull, it converts the one closest to the hull's center to its own team.
    -   **Fallback Effect:** If no enemies are inside, it reinforces the hull's boundary by strengthening existing lines or creating missing ones.
    -   This adds a new strategic layer related to controlling board space and enveloping enemies.

2.  **Refactored Point-in-Polygon Logic:**
    -   Replaced the `is_point_inside_triangle` function, which was based on area calculations, with a more robust and generic `is_point_in_polygon` function that uses the Ray Casting algorithm.
    -   Updated all call sites (`check_shield_rune` and `is_spawn_location_valid`) to use the new, more reliable function. This improves the accuracy of geometric checks throughout the application.

3.  **Updated Game Data:**
    -   Added the new action to `action_data.py` with its display name, description, and log generators.
    -   The precondition check was added to `fight_actions.py` to ensure the action is only available when a team can form a hull (>= 3 points).