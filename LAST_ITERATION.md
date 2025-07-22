This iteration introduces a new powerful structure and attack, the Railgun, and improves the user experience during the setup phase.

### 1. New Structure & Action: The Railgun

-   **Files**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`
-   **Change**: A new passive formation, the **Railgun**, has been introduced.
    -   **Formation**: Two friendly lines that are parallel, of similar length, and reasonably close to each other form a Railgun.
    -   **Action**: This structure unlocks the new **`[FIGHT] Fire Railgun`** action. It fires a high-velocity projectile that destroys the first two enemy lines in its path, piercing through shields.
    -   **Strategy**: This provides teams with a powerful tool for breaking through heavily defended areas or clusters of enemy lines, rewarding strategic placement of parallel lines.
    -   **Visuals**: Active railguns are visualized by a translucent field between the two lines with energy particles flowing along them. The firing action has a distinct, fast-moving projectile effect.

### 2. UI/UX Improvements

-   **File**: `static/js/main.js`
-   **Change**: Improved feedback during the setup phase.
    -   **Functionality**: When the user hovers the mouse over the grid during setup, the status bar at the bottom now displays the current grid coordinates `(x, y)`.
    -   **Benefit**: This makes it easier for users to place points precisely without having to guess or count grid squares. The display disappears when the mouse leaves the canvas or when the game starts.

### 3. State & Rendering

-   **Files**: `game_app/game_logic.py`, `static/js/main.js`
-   **Change**: The backend and frontend have been updated to handle the new Railgun state.
    -   The game state now tracks railgun formations for each team.
    -   The live stats panel now displays the number of active railguns for each team.