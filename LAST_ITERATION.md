# Iteration Analysis and Changelog

## 1. Analysis Summary
The previous iteration successfully introduced the "Mirror Structure" action and fixed a minor code duplication bug. The application is stable and the core gameplay loop is solid. The next steps focus on a significant improvement of the user experience by providing more granular control over the simulation, fixing a visual bug during setup, and adding more gameplay variety.

## 2. Implemented Features and Improvements

### Core Gameplay & Backend (`game_logic.py`)
-   **Per-Action Simulation:** The game loop has been fundamentally refactored. Instead of processing a whole turn at once, the game now advances one action at a time. The backend logic was changed from `run_next_turn` to `run_next_action`, allowing the frontend to step through each team's move individually. This makes the simulation much easier to follow.
-   **New Action - Fracture Line:** A new `[EXPAND]` action has been added to create more intricate structures.
    -   A team can "fracture" one of its existing lines, creating a new point along the line's segment and replacing the original line with two new ones.
    -   This action is favored by the `Expansive` trait and helps organically increase point and line density.
-   **Restart Simulation Feature:** A `restart_game` method was added to the backend. It uses a saved copy of the initial game setup (teams, points, settings) to restart the simulation from Turn 0 without requiring the user to go back to the setup screen.

### Frontend & UI (`main.js`, `index.html`)
-   **CRITICAL BUGFIX (Point Visibility):** Fixed a bug where points placed during the `SETUP` phase were not visible. The rendering logic was centralized into the main animation loop, which now correctly draws the locally-stored points before the game has officially started, providing immediate visual feedback. The buggy `redrawSetupPoints` function was removed.
-   **"Next Action" Control:** The "Next Turn" button has been changed to "Next Action" to match the new backend logic. The game turn counter in the UI now also displays which action within the turn is being shown (e.g., "Turn: 5 (2/3)").
-   **"Restart Simulation" Button:** A new button has been added to the UI, visible during the `RUNNING` and `FINISHED` phases. This button calls the new restart endpoint, allowing users to easily re-run a simulation with the same starting parameters.
-   **UI Control Panel Refactor:** The left-hand control panel has been reorganized. "Setup" controls are now cleanly separated from "Simulation" controls, which only appear after the game has started. This provides a cleaner and more intuitive workflow.

### API (`routes.py`)
-   The `/api/game/next_turn` endpoint has been replaced with `/api/game/next_action`.
-   A new `/api/game/restart` endpoint has been added to support the restart feature.

### Documentation (`rules.md`)
-   The game rules have been updated to include a description of the new "Fracture Line" action.