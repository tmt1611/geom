This iteration focuses on improving the user interface during the setup phase and introducing a new, visually dynamic action that enhances strategic possibilities.

### 1. New Action: Phase Shift

-   **Files**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`
-   **Change**: A new sacrifice-class action, **`[SACRIFICE] Phase Shift`**, has been introduced.
    -   **Functionality**: A team can sacrifice one of its lines to instantly teleport one of the line's endpoints to a new random location. All other lines connected to the moved point remain, creating long, stretched connections across the grid.
    -   **Strategy**: This high-risk, high-reward action allows for dramatic strategic repositioning, enabling teams to escape dangerous areas, flank opponents, or connect disparate groups of points.
    -   **Visuals**: The action is accompanied by new visual effects: a colorful implosion at the point's original location and a corresponding explosion at its new destination, making the event clear and visually exciting.

### 2. UI/UX Improvements

-   **File**: `static/js/main.js`
-   **Change**: The team editing interface in the setup panel has been redesigned to be less disruptive.
    -   **Before**: Clicking "Edit" would replace the entire team information line with input fields.
    -   **After**: Clicking "Edit" now displays the editing controls inline below the team's information, which remains visible. This makes for a smoother and more intuitive user experience when managing teams.

### 3. Visual Polish

-   **File**: `static/js/main.js`
-   **Change**: The visual effects for several sacrifice actions (`Create Anchor`, `Create Whirlpool`, `Bastion Pulse`) have been updated to use the appropriate team's color, making the cause of "implosion" effects clearer.
-   **Benefit**: This small change improves visual consistency and helps the user to better understand events on the battlefield at a glance.