This iteration focuses on cleaning up a complex piece of game logic in the Python backend and improving the clarity of an illustration in the Action Guide frontend.

### Code Cleanup and Bug Fixes

1.  **Refactored Critical Point Identification**: The logic for finding a "non-critical" point to sacrifice was complex, duplicated logic from other parts of the codebase, and contained a bug.
    *   In `game_app/game_logic.py`, a new private helper method, `_get_critical_structure_point_ids(teamId)`, was created to consolidate the logic for identifying all points that are part of a specific team's important structures (Runes, Bastions, Monoliths, etc.).
    *   This new method fixes a bug in the original implementation where structures from *all* teams were being considered critical, not just the acting team's own structures.
    *   The `_find_non_critical_sacrificial_point` method was refactored to use this new helper, making its code significantly shorter, cleaner, and more correct.

### UI/UX Improvements: Action Guide

1.  **Improved Illustration Clarity**: The illustration for the `Launch Payload` action in the Action Guide has been improved to better communicate its purpose.
    *   In `static/js/main.js`, a new drawing helper was created to render a "fortified" point (a diamond shape).
    *   The `fight_launch_payload` illustration was updated to use this helper, now showing the trebuchet targeting a fortified point, which aligns with the action's description of prioritizing high-value targets.
    *   An explosion effect was also added to the target point to make the destructive outcome of the action more obvious at a glance.