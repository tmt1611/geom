This iteration focused on implementing a previously designed but unimplemented action from the `Sacrifice` group, improving the consistency of the action system.

1.  **Implemented `sacrifice_raise_barricade` Action:** Added the full implementation for the `raise_barricade` sacrifice action, which was defined in `action_data.py` but missing from the `SacrificeActionsHandler`.
    -   **Precondition:** The action is only available if a team has an active **Barricade-Rune** (a rectangle of 4 points and 4 lines).
    -   **Effect:** The action consumes the entire Barricade-Rune, sacrificing its 4 points and 4 lines. It then creates a long-lasting (5-turn) impassable barricade along one of the diagonals of the sacrificed rune.
    -   **Fizzle Condition:** If the rune's geometry is somehow invalid (e.g., not a proper rectangle), the points are still sacrificed, but no barricade is formed. This introduces a risk/reward element appropriate for a sacrifice action.
    -   Added a new log message for the fizzle case.