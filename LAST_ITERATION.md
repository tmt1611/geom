This iteration focused on improving action robustness to better respect the `design.md` rule: "Action pool should NEVER be empty".

1.  **Identified Brittle Action**: The `expand_spawn` action was identified as a potential point of failure. If a team had only one point and no lines, `can_perform_spawn_point` would return true, but the action itself could fail if the local area was crowded, causing the team to pass its turn unnecessarily.

2.  **Refactored `spawn_point` Action**:
    *   In `game_app/actions/expand_actions.py`, the `spawn_point` method was refactored to include a hierarchy of fallbacks.
    *   **Primary Effect:** Tries to spawn a point near an existing friendly point.
    *   **Fallback 1:** If the primary effect fails, it attempts to strengthen a friendly line (the original fallback).
    *   **Fallback 2:** If strengthening a line is not possible (e.g., no lines exist), it now attempts to project a ray from a random friendly point to the border and create a new point there. This provides a robust last-resort option.
    *   This change makes the action significantly more likely to succeed, preventing a team from passing its turn when it has at least one point.

3.  **Simplified Precondition Check**:
    *   The `can_perform_spawn_point` method was simplified. Since the action is now guaranteed to have a possible outcome if at least one point exists, the check no longer needs to consider the existence of lines.

4.  **Updated Action Metadata**:
    *   The description for `expand_spawn` in `game_app/action_data.py` was updated to reflect its new multi-level fallback logic.
    *   A new log generator for `'spawn_fizzle_border_spawn'` was added to provide clear feedback to the user when the new fallback is triggered.