Improved the `isolate_point` action to increase action pool robustness.

1.  **Ensured Action Availability**: Modified the `isolate_point` action to ensure it's always possible if a team has at least one point. This helps fulfill the "action pool never empty" design requirement, especially for teams with very few assets left.

2.  **Added New Fallback**: Implemented a new fallback behavior for `isolate_point` in `fight_actions.py`. When a team has only one point and cannot find a primary target, instead of failing, it now emits a weak repulsive pulse to push nearby enemies. The existing fallback (creating a barricade) is kept for when the team has two or more points.

3.  **Updated Action Metadata**: Updated `action_data.py` to include a new log generator for the `isolate_fizzle_push` result type and revised the action's description to reflect its new, more robust fallback logic.