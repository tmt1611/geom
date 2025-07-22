This iteration focuses on adding a new strategic action, improving the developer/debug experience, and polishing the UI for clarity.

### New Gameplay Feature: Barricades

-   **Files**: `game_logic.py`, `static/js/main.js`, `rules.md`
-   **Change**: Introduced a new `[TERRAFORM] Raise Barricade` action.
    -   **Logic**: A team can use its turn to create a temporary, impassable wall between two of its existing points. This wall, or "barricade," does not require sacrificing a point.
    -   **Strategic Impact**: Barricades act as neutral obstacles for a few turns. They block line-based attacks and extensions (`Attack Line`, `Extend Line`) and prevent new points from being created nearby. This adds a new layer of battlefield control and defensive strategy.
    -   **Implementation**: Added `barricades` to the game state, created the action logic in `game_logic.py`, and implemented checks for obstruction in relevant functions. The frontend now renders these barricades with a distinct, jagged visual style that fades over time. The `rules.md` has been updated with the new action.

### UI/UX and Developer Experience Improvements

-   **Files**: `templates/index.html`, `static/css/style.css`
-   **Change 1 (UI Polish)**: The "Reset Game" button text was changed to "Reset Game (Back to Setup)" to more clearly communicate its function and distinguish it from "Restart Simulation".
-   **Change 2 (Dev Tools Cleanup)**: The "Debug Tools" section has been renamed to "Developer Tools" and is now collapsed by default within a `<details>` tag, cleaning up the main interface for regular users.
-   **Change 3 (Safer UI)**: The "Shutdown Server" button inside the developer tools has been styled as a red "danger" button to visually warn of its destructive action. The "Copy Game State" button text was also made more explicit. All buttons in this section were styled for a consistent look.