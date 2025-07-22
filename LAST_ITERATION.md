This iteration introduces a new strategic layer to the game with the **Trebuchet**, a powerful siege engine designed to break fortified enemy positions.

### 1. New Structure: The Trebuchet

-   **Files**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`
-   **Change**: A new fortify-class structure, the **Trebuchet**, has been added to the game.
    -   **Formation**: Teams can form a Trebuchet if they create a specific kite-shaped structure with four points and the necessary connecting lines. The detection logic has been optimized to efficiently find these complex geometric shapes.
    -   **Action**: A successfully formed Trebuchet unlocks the `[FIGHT] Launch Payload` action. This powerful, long-range attack fires an arcing projectile that can destroy high-value enemy points, such as fortified points, bastion cores, and monolith anchor points, bypassing normal defenses.
    -   **Visuals**: Trebuchets have a distinct appearance on the grid, with a visible "arm" connecting the apex to the counterweight. The `Launch Payload` action is visualized with a projectile arcing across the battlefield and a large explosion on impact, adding to the visual spectacle.

### 2. Code and Engine Improvements

-   **File**: `game_app/game_logic.py`
-   **Change**: A geometric helper for detecting isosceles triangles has been added. The system for discovering complex, multi-point structures like the Trebuchet has been implemented efficiently to avoid performance degradation.
-   **Benefit**: This makes the game engine more robust and performant, allowing for the addition of more complex structures in the future.

### 3. Frontend Enhancements

-   **File**: `static/js/main.js`
-   **Change**: The live stats panel now correctly identifies and counts the number of active Trebuchets for each team. New drawing functions were added to render the Trebuchet structures and the arcing projectile animation.
-   **Benefit**: This provides players with clear, immediate feedback on the state of the game and enhances the visual storytelling of the battle.