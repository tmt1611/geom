This is a comprehensive update addressing several points from your request, focusing on expanding the rune system, ensuring actions are "never useless" by adding fallbacks, and refactoring core mechanics for clarity and consistency.

### 1. New Rune and Action: The Plus-Rune (`+`)

A new high-tier, single-use rune has been added.

-   **Formation**: The **Plus-Rune** is formed by a central point connected to four other points, creating two straight, perpendicular lines (a `+` shape). All five points and four lines must belong to the same team.
-   **New Action**: Unlocks the `[RUNE] Cardinal Pulse` action.
-   **Mechanic**: This is a powerful sacrificial action. The five points of the rune are consumed to fire four energy beams from the center along the rune's arms.
-   **"Never Useless" Design**: Each beam destroys the first enemy line it hits (bypassing shields). Any beam that misses its target travels to the edge of the grid and creates a new friendly point, ensuring the action always has a significant impact.

### 2. Refactoring into the I-Rune (Line Rune)

To improve clarity and merge redundant concepts as requested, the `Sentry` and `Conduit` structures have been refactored into a single, unified **I-Rune**.

-   **Formation**: The **I-Rune** is formed by three or more collinear points connected sequentially by lines.
-   **Unified Bonuses**: This single rune now grants all the bonuses previously split between Sentries and Conduits:
    -   Unlocks the **[FIGHT] Sentry Zap** action (fires from an internal point).
    -   Unlocks the **[FIGHT] Chain Lightning** action (sacrifices an internal point).
    -   Passively empowers the **[EXPAND] Extend Line** action when used from an endpoint.
-   **Code Cleanup**: This change simplified the game state by removing the separate `sentries` and `conduits` objects, and streamlined the logic for checking formations and powering actions.

### 3. "Never Useless" Action Fallbacks

Following the design philosophy of making every action count, fallbacks have been added to core expansion actions that could previously fail and do nothing.

-   **[EXPAND] Extend Line**: If no valid extension to the border is possible, the action now **reinforces an existing friendly line** instead of failing.
-   **[EXPAND] Fracture Line**: If no lines are long enough to be fractured, the action now **reinforces an existing friendly line** as a fallback.

### 4. Equalized Action Probabilities

As requested, the base chance for all actions has been equalized.

-   The internal `ACTION_BASE_WEIGHTS` have all been set to `1`.
-   This makes the `Balanced` team trait truly have an equal probability for any valid action.
-   The strategic diversity now comes entirely from the **Team Traits**, which apply multipliers to specific action categories, making their behavior more pronounced and readable.

### 5. Documentation and UI Updates

-   The `rules.md` file has been extensively updated to reflect the new Plus-Rune, the unified I-Rune, and the new action fallbacks.
-   The frontend point rendering logic was updated to correctly display the new I-Rune points.

These changes significantly increase strategic depth, make gameplay more dynamic and predictable (in a good way), and clean up the underlying game logic.