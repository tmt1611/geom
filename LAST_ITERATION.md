Refactored several actions to better align with the `no_cost` action design rules from `design.md`.

1.  **Corrected Action Costs:**
    *   The `design.md` rule states that actions not generating points or dealing damage should be free. Based on this, several actions were updated.
    *   `fortify_shield`, `terraform_create_fissure`, `fortify_create_ley_line`, and `rune_hourglass_stasis` were all made `no_cost` as their primary effects are buffs, terraforming, or control effects, not direct damage or point generation.
    *   Descriptions in `action_data.py` and `rules.md` were updated to reflect these changes.

2.  **Fixed `rune_cardinal_pulse` Cost:**
    *   This action was incorrectly marked as `no_cost` in a previous refactor.
    *   Since it destroys enemy lines (deals damage) and can create points, it should have a cost. The `no_cost` flag was removed.

3.  **Updated Documentation:**
    *   The description for the Plus-Rune in `rules.md` was corrected to remove the "one-use sacrificial" text, as the `cardinal_pulse` action no longer consumes the rune.
    *   The description for `rune_hourglass_stasis` was also corrected to clarify its fallback mechanism does not involve a sacrifice.