# Iteration Analysis and Changelog

## 1. Analysis Summary
This iteration introduces a major new strategic element, the **Nexus**, and overhauls the core turn-taking mechanic to support bonus actions. The Nexus is a powerful defensive and economic structure formed by creating a square with points and lines. It rewards players for intricate geometric construction by granting them a bonus action for each Nexus they control per turn.

This change significantly deepens the strategic possibilities, creating a new "builder" playstyle that competes with aggressive and expansive strategies. The underlying game logic was refactored to handle a dynamic action queue, making the system more robust and extensible for future features like wonders or other special structures that might grant actions.

## 2. Key Changes

### 2.1. New Structure: The Nexus
- **Files**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`
- **Concept:** A new passive structure formed by 4 points creating a square, with the 4 outer lines and at least one diagonal connected.
- **Bonus:** For each Nexus a team controls at the start of a turn, it gains one bonus action for that turn.
- **Backend (`game_logic.py`):**
    - Implemented a robust `is_square` helper function to detect square formations.
    - Added `nexuses` to the game state and created the `_update_nexuses_for_team` method to detect valid Nexus structures.
    - **Reworked Turn Logic:** The turn execution system was refactored. Instead of a simple list of teams, the game now uses an `actions_queue_this_turn` containing action objects (`{teamId, is_bonus}`). This queue is built at the start of each turn based on which teams have Nexuses.
    - Added new log messages to announce when teams gain bonus actions from their Nexuses.
- **Frontend (`static/js/main.js`):**
    - Implemented `drawNexuses` to render a translucent fill inside the Nexus square and a pulsating, glowing orb at its center, providing a clear and visually appealing representation.
    - Updated `drawPoints` to give points that are part of a Nexus a distinct visual style (concentric circles).
    - The turn counter in the UI now accurately reflects the total number of actions in the queue (e.g., "Turn: 5 (Action 3 / 7)").
- **Documentation (`rules.md`):**
    - Updated the rules to explain the Nexus formation, its requirements, and the bonus action reward.

### 2.2. Code Refactoring and Cleanup
- **File**: `game_logic.py`
    - The `run_next_action` and `_start_new_turn` methods were completely rewritten to use the new action queue system, making the flow of a turn more explicit and easier to follow.
    - State management was updated to replace the old `active_teams_this_turn` with the new, more descriptive `actions_queue_this_turn`.