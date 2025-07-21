# Iteration Analysis and Changelog

## 1. Analysis Summary
This iteration addresses several key areas based on user feedback and a detailed code review, focusing on bug fixes, data integrity, and a significant refinement of the core gameplay logic. The primary goals were to fix a critical workflow bug with the game reset functionality, enforce integer-only coordinates for all points to improve stability, and overhaul the action system to make team behaviors appear more intelligent and successful.

## 2. Implemented Features and Improvements

### Core Gameplay & Backend (`game_logic.py`)
-   **Intelligent Action System:** The process for how a team selects and executes an action has been completely overhauled to eliminate the logging of failed attempts (e.g., "attack missed," "no target in range").
    -   The `run_next_action` method now iteratively tries different actions for a team until one succeeds.
    -   If no action can be successfully performed after several attempts, the team gracefully "passes" its turn. This results in a cleaner game log that only shows successful outcomes, making the AI teams feel more deliberate and effective.
    -   The `_choose_action_for_team` method was enhanced to support this new system by allowing actions that have already failed in a turn to be excluded from the selection pool.
-   **Integer Coordinate System:** All actions that generate new points now round the resulting coordinates to the nearest integer. This change, applied to actions like line fracturing, mirroring, and the gravity effect of anchors, ensures data consistency, prevents floating-point errors, and makes the geometric simulation more robust.
-   **Safer Sacrifice Actions:** To prevent teams from easily crippling or eliminating themselves, the preconditions for sacrifice-based actions were made stricter.
    -   `sacrifice_action_nova_burst` now requires a team to have more than one point, preventing a team from sacrificing its last entity.
    -   `fortify_action_create_anchor` now requires a team to have at least three points, ensuring the team remains viable after the action.

### Bug Fixes
-   **CRITICAL WORKFLOW FIX (Reset Game):** The "Reset Game (New Setup)" button, which was non-functional, has been fixed. Previously, it only reloaded the page, failing to reset the game's state on the server.
    -   A new `/api/game/reset` endpoint was created to properly call the `game.reset()` method on the backend, which returns the game to the initial `SETUP` phase.
    -   The frontend button now calls this new endpoint before reloading the page, correctly returning the user to the setup screen.

### API (`routes.py`)
-   Added the new `/api/game/reset` endpoint to handle a full game state reset, initiated by the user from the UI.