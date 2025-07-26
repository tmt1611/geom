Refactored several sacrifice-based actions to conform to the design rule that "Rune, territory, and wonder points cannot be sacrificed."

1.  **Redesigned Rune Actions:**
    *   `sacrifice_t_hammer_slam`, `sacrifice_cardinal_pulse`, and `sacrifice_raise_barricade` were violating the no-sacrifice rule for rune points.
    *   These actions have been moved from the `Sacrifice` group to the `Rune` group.
    *   Their implementations were refactored to no longer sacrifice or consume their respective runes' points. They are now `no_cost` actions that can be used repeatedly as long as the rune exists.
    *   Updated `action_data.py` and `rules.md` to reflect these changes in grouping, cost, and description.

2.  **Fixed and Redesigned Rift Spire Formation:**
    *   The action `sacrifice_form_rift_spire` was defined but not implemented, and its design violated the rule against sacrificing territory points.
    *   Renamed it to `fortify_form_rift_spire`, moved it to the `Fortify` group, and implemented it as a `no_cost` action in `fortify_actions.py`.
    *   The action now erects a Rift Spire at a valid territorial nexus without sacrificing the point, making the cost purely geometric.
    *   Added a corresponding definition for Rift Spires in `structure_data.py` to correctly flag its point as critical.
    *   Updated `rules.md` to reflect this non-sacrificial design.