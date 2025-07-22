This iteration introduces a significant new strategic and visual element: **Nexus Detonations**. This feature enhances the "auto-battle sandbox" aspect of the game by creating opportunities for spectacular chain reactions, making the battlefield more dynamic and visually engaging.

### 1. New Mechanic: Nexus Detonation

-   **Files**: `game_app/game_logic.py`, `static/js/main.js`
-   **Change**: Nexuses, the economic powerhouses of a team, are now volatile. When a point that is part of a Nexus is destroyed, the Nexus detonates in a violent energy discharge.
-   **Effect**: The detonation creates a shockwave centered on the former Nexus. This shockwave destroys any nearby enemy points and lines, potentially triggering further cascades if another structure is hit. This turns Nexuses into high-risk, high-reward structures and key strategic targets.
-   **Visuals**: A new visual effect has been added for the detonation—an expanding shockwave of the Nexus owner's color—clearly signaling the cause of the secondary destruction on the battlefield.

### 2. Code Refactoring & Quality Improvement

-   **File**: `game_app/game_logic.py`
-   **Change**: The core point destruction function, `_delete_point_and_connections`, was refactored to handle the new cascade logic cleanly. It now accepts an `aggressor_team_id` to correctly attribute the destruction and its side effects.
-   **Benefit**: This change centralizes the logic for secondary effects. Instead of adding checks to every single attack action, the cascade logic is handled in one place, making the code more robust and easier to maintain. All actions that destroy points were updated to use this improved function.

### 3. State Management and Event Handling

-   **File**: `game_app/game_logic.py`
-   **Change**: A new `action_events` list was added to the game state. This list is used to communicate secondary visual effects (like the Nexus Detonation) from the backend to the frontend for a single action.
-   **Benefit**: This provides a structured way to handle complex visual sequences that result from a single game action, ensuring the UI can accurately represent everything that happened in the correct order. The state is cleared after each action, keeping it clean and preventing bleed-over between turns.

These changes directly address the user's request to make the final picture "more interesting or visually stunning" by introducing dramatic, geometry-based chain reactions that can drastically alter the state of the game in a single, explosive moment.