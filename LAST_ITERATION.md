This iteration focused on redesigning sacrifice actions, implementing a new action directly from `design.md`.

1.  **Interpreted `design.md` Sacrifice Rules**:
    - Analyzed the "Sacrifice Variants" section in `design.md`, specifically the rule for sacrificing a point that is part of a line.
    - The rule states: "Line also sacrificed: fires a perpendicular and an extended line."

2.  **Designed and Implemented `Line Retaliation` Action**:
    - Created a new sacrifice action, `sacrifice_line_retaliation`, that fulfills the design specification.
    - **Action Logic**: The action sacrifices a non-critical point on a line. This causes the line to be destroyed, and from its former midpoint, two projectiles are fired: one along the line's original vector and another perpendicularly. Each projectile destroys the first enemy line it hits or creates a new point on the border if it misses.
    - This adds a new strategic option to the `Sacrifice` group, providing a powerful area-denial and potential creation tool at the cost of a point and a line.

3.  **Added Action Metadata**:
    - Updated `action_data.py` with the new action's display name, description, and log generation messages for clear feedback to the user in the game log.
    - Implemented the `can_perform_line_retaliation` precondition check in `sacrifice_actions.py` to ensure the action is only available when a valid, non-critical line can be targeted.