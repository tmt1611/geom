This iteration focused on improving the action system by implementing missing actions and fixing a rule violation, adhering to `design.md`.

1.  **Corrected Rule Violation:**
    -   The fallback for the `hourglass_stasis` action was sacrificing a rune point, which violates the rule "Rune, territory, and wonder points cannot be sacrificed."
    -   This has been corrected. The fallback now *converts* one of the rune's own points into a temporary anchor, degrading the rune without an illicit sacrifice. This makes the cost of failure the temporary loss of the rune structure itself.
    -   The action's precondition check (`can_perform_hourglass_stasis`) was also made more robust to account for this new fallback logic.

2.  **Implemented Missing Sacrifice Actions:**
    -   The `convert_point` and `bastion_pulse` actions, which were defined in `action_data.py` but not implemented, have now been added to `sacrifice_actions.py`.
    -   `convert_point`: Sacrifices a friendly line to convert a nearby vulnerable enemy point. If no target is in range, it creates a repulsive pulse.
    -   `bastion_pulse`: An active Bastion sacrifices one of its outer points to destroy all enemy lines crossing its perimeter. If the Bastion dissolves from the sacrifice, it creates a local shockwave instead.

3.  **Code Refactoring:**
    -   Moved `_find_possible_bastion_pulses` from `game_logic.py` to `sacrifice_actions.py` to keep the action logic self-contained within its handler.