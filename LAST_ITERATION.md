This iteration focused on improving the robustness of the action system, ensuring that actions are available even in extreme edge cases, as per `design.md`.

1.  **Ensured Action Availability for Single Points:**
    - Identified that for a team with only one or two points, the available action pool could become very small or empty, violating a core design principle.
    - The `reposition_point` and `rotate_point` actions were previously unavailable for teams with <= 2 points because they incorrectly used a helper method designed for sacrificial actions.

2.  **Refactored Point Selection Logic:**
    - Created a new helper method, `_find_repositionable_point`, in `game_logic.py`. This method specifically finds "free" points that are not part of critical structures and are not articulation points, making it suitable for non-destructive move actions.
    - Unlike the old method, this new logic correctly identifies that a single point, or points in a simple line, can be safely moved.

3.  **Updated Fortify Actions:**
    - Modified `reposition_point` and `rotate_point` (and their `can_perform_*` checks) in `fortify_actions.py` to use the new `_find_repositionable_point` method.
    - This change makes these "no-cost" movement actions available in more scenarios, particularly for teams with very few points, thus guaranteeing a richer and more resilient action pool.