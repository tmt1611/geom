This iteration focused on better aligning actions with the design document, specifically the rule: "Action that does not generate points or deal damage (like rotations, push, pull, etc) must not cost points."

1.  **Identified Costed Utility Actions**: Reviewed `action_data.py` and identified three actions that performed utility functions (push, pull, apply status) but were not marked as `'no_cost'`.
    *   `fight_purify_territory`: Removes a territory status or pushes points.
    *   `rune_area_shield`: Applies shields or pushes points.
    *   `rune_shield_pulse`: Pushes or pulls points.

2.  **Updated Actions to be No-Cost**:
    *   In `game_app/action_data.py`, added `'no_cost': True` to `fight_purify_territory`, `rune_area_shield`, and `rune_shield_pulse`.
    *   Updated the descriptions for these actions to inform the user that they are free.
    *   The game logic already handles `no_cost` actions by granting a bonus action, so this change integrates seamlessly.

3.  **Corrected Action Precondition**:
    *   The precondition check for `fight_purify_territory` in `game_app/actions/fight_actions.py` was too strict. It required an enemy territory to exist, ignoring its fallback effect. The check was corrected to only require an active Purifier structure, making the action always available when the structure is present.

4.  **Improved Frontend Display**:
    *   Added a CSS rule in `static/css/style.css` for the `.no-cost-tag` class to visually highlight free actions in the UI, improving clarity for the player.