This iteration focuses on aligning two actions with the design principle that actions not generating points or dealing damage should not have a resource cost.

1.  **Refactor `fortify_create_anchor`**:
    *   This action previously sacrificed one point to turn another into a gravitational anchor. This violated the "no cost for control effects" rule.
    *   The action has been modified in `game_app/actions/fortify_actions.py` to no longer sacrifice a point. It now selects one of a team's non-critical, non-articulation points and converts it into an anchor directly.
    *   The precondition check `can_perform_create_anchor` was updated to reflect the new requirements (i.e., needing at least one eligible point instead of multiple points for sacrifice).
    *   The action's description and log message in `game_app/action_data.py` have been updated to remove references to sacrifice.

2.  **Refactor `fight_isolate_point`**:
    *   This action previously sacrificed a line to apply the 'isolated' status to an enemy point.
    *   The action has been modified in `game_app/actions/fight_actions.py` to remove the line sacrifice. It now uses a friendly point to "project" the effect. The fallback to create a barricade also no longer has a cost.
    *   The `can_perform_isolate_point` check was updated to reflect that it no longer requires lines, but instead points.
    *   The action's description in `game_app/action_data.py` was updated to remove the mention of a sacrifice cost.