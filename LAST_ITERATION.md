*   **Improved Action Robustness:** Refactored several actions to ensure they always have a successful outcome, aligning with the design principle that the action pool should never be empty. This prevents situations where a team might pass its turn because its only available action could fail.
*   **Added Fallbacks:**
    *   `territory_bisector_strike`: Now reinforces its own territory boundaries if all three of its beams are blocked or miss, instead of failing.
    *   `sentry_zap`: Now reinforces the Sentry (I-Rune) lines if its attack path is blocked or if spawning a point on the border fails.
    *   `refraction_beam`: Now reinforces the Prism rune's lines if no valid refraction path can be found or if its miss-spawn fails.
    *   `rune_shoot_bisector`: Now reinforces the V-Rune's lines if its attack path is blocked.
*   **Updated Action Logs:** Added new log messages in `action_data.py` to reflect these new fallback behaviors, providing clearer feedback to the user (e.g., `[TRI-BEAM->REINFORCE]`).