This iteration focused on implementing the `Build Wonder` action, a key missing feature from the design documents (`design.md` and `rules.md`).

1.  **Implemented Wonder Creation**:
    *   The `build_chronos_spire` action method was added to `game_app/actions/sacrifice_actions.py`. This action allows a team to sacrifice a Star-Rune to create the Chronos Spire wonder.
    *   The corresponding `can_perform_build_chronos_spire` precondition check was also added to ensure the action is only available when a Star-Rune exists.

2.  **Implemented Wonder Bonuses**:
    *   The logic in `game_app/game_logic.py` was updated to grant the Wonder's owner a bonus action each turn, as specified in `rules.md`. The `_build_action_queue` method now checks for Wonders alongside Nexuses.
    *   The victory condition via the Wonder's countdown is already handled by the `turn_processor`, so the new Wonder object integrates seamlessly with existing logic.

3.  **Documentation Cleanup**:
    *   `rules.md` was updated to correctly categorize the `Build Wonder`, `Cultivate Heartwood`, and `Form Rift Spire` actions under the `[SACRIFICE]` group. This ensures consistency with the design principle that actions involving sacrifice are labeled as such.