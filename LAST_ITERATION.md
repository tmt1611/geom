This iteration focuses on improving the action design by replacing a less-defined action with a more geometrically sound one, in line with `design.md` principles.

1.  **Replaced Action: `Grow Vine` -> `Bisect Angle`**
    *   **Old Action (`Grow Vine`):** This action created a new point by growing a branch from an existing point at a random angle. This was functionally effective but lacked clear geometric intent.
    *   **New Action (`Bisect Angle`):** This new `Expand` action is more deterministic and strategic. It identifies a vertex (a point with at least two connected lines forming an angle), calculates the angle's bisector, and spawns a new point along that bisector.
    *   **Geometric Principle:** This change aligns better with the design goal of using "constructs: points, lines, shapes, hulls, rotations, mirrors" and avoids generic effects. It gives purpose to simple 'V' shapes on the grid.

2.  **Implementation Details**
    *   Replaced `expand_grow` with `expand_bisect_angle` in `game_app/action_data.py`, including new user-facing descriptions and log messages.
    *   Implemented `bisect_angle` and its precondition check `can_perform_bisect_angle` in `game_app/actions/expand_actions.py`. The new action correctly utilizes the existing `get_angle_bisector_vector` helper.
    *   The fallback logic was also improved: if bisecting fails, it attempts to strengthen one of the two lines forming the angle, making the fallback more context-aware. A final, generic fallback to strengthen any random line remains as a failsafe.

3.  **Documentation**
    *   Updated `rules.md` to remove the "Grow Line (Vine)" action and add the new "Bisect Angle" action with its description.