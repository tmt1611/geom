This iteration focused on refactoring repeated code into a shared helper function, which improves maintainability and consistency. The specific target was the logic for creating a new point on the grid border when a line-based "attack" action misses its target.

**Key Changes:**

1.  **New Helper `_helper_spawn_on_border` in `game_logic.py`:**
    *   A new private method was created to centralize the logic for spawning a point on the border.
    *   This helper takes a team ID and border coordinates, validates the spawn location, creates the new point, and adds it to the game state.
    *   **Enhancement:** The helper now also calls `_check_and_apply_ley_line_bonus`, adding a new potential synergy where missed attacks can still benefit from active Ley Lines. This was previously inconsistent.

2.  **Refactored "Miss" Logic in Action Handlers:**
    *   The miss-handling logic in several actions was simplified to call the new `_helper_spawn_on_border` method.
    *   This change was applied to the following actions:
        *   `fight_actions.attack_line` (via its `_handle_attack_miss` helper)
        *   `fight_actions.sentry_zap`
        *   `fight_actions.refraction_beam`
        *   `rune_actions.cardinal_pulse`

3.  **Minor Code Cleanup:**
    *   Removed a small piece of duplicated code (a comment and variable initialization) in `fight_actions.launch_payload`.

These changes make the code cleaner, reduce duplication, and ensure that all "spawn-on-miss" events behave consistently and can trigger the Ley Line bonus.