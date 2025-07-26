This iteration focused on implementing the "no cost" action rule from `design.md`.

1.  **Identified No-Cost Actions**: Based on the rule "Action that does not generate points or deal damage (like rotations, push, pull, etc) must not cost points.", I identified the following actions as candidates:
    *   `fight_isolate_point`
    *   `fortify_anchor`
    *   `fortify_reposition_point`
    *   `fortify_rotate_point`

2.  **Updated Action Metadata**:
    *   Added a `'no_cost': True` flag to the definitions of these four actions in `game_app/action_data.py`. This provides a central, declarative way to mark such actions.

3.  **Implemented "No Cost" Logic**:
    *   Modified `game_logic.py` in the `run_next_action` method.
    *   After a successful action, the logic now checks if the action had the `no_cost` flag.
    *   If it did (and wasn't already a bonus action), it grants the team an immediate bonus action by inserting it into the current turn's action queue.
    *   This ensures that using a positional or utility action doesn't consume the team's main action for the turn, directly implementing the rule from `design.md`.

4.  **Updated API Data**:
    *   Adjusted `get_action_probabilities` in `game_logic.py` to include the `no_cost` flag in the data sent to the frontend, enabling future UI enhancements to visualize these special actions.