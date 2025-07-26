This iteration focused on improving the action design for the Star-Rune to better align with the principles in `design.md`. The goal was to ensure the Star-Rune offers more non-sacrificial actions than sacrificial ones.

1.  **Re-classified `Starlight Cascade` Action**:
    *   The `sacrifice_starlight_cascade` action was identified as a violation of two rules: it sacrificed a rune point, and it made the Star-Rune's action ratio unbalanced (1 non-sac vs 2 sac).
    *   The action was removed from the `Sacrifice` group and `sacrifice_actions.py`.
    *   It was re-implemented as a non-sacrificial `rune_starlight_cascade` action in `rune_actions.py`. The new version unleashes an energy cascade from the rune's center without destroying any friendly points, damaging or destroying nearby enemy lines. This aligns it with other non-sacrificial rune abilities.
    *   The `action_data.py` entry was updated to reflect this change in group, handler, description, and log messages.

2.  **Added New `Gravity Well` Action**:
    *   To further improve the Star-Rune's versatility and ensure it has a clear majority of non-sacrificial actions, a new action, `rune_gravity_well`, was designed and implemented.
    *   This is a `no_cost` control action that pushes non-friendly points away from the rune's center, with a fallback to pull friendly points closer, making it always useful.
    *   The action was added to `action_data.py`, and its logic was implemented in `rune_actions.py`.

With these changes, the Star-Rune now enables three non-sacrificial actions (`Focus Beam`, `Starlight Cascade`, `Gravity Well`) and one sacrificial action (`Build Wonder`), bringing its design in line with the rule: "Structures must offer more non-sacrifice actions than sacrifice actions."