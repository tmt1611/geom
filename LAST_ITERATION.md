# Iteration Analysis and Changelog

This iteration introduces a new high-tier strategic objective: the **Heartwood**. This unique, team-specific structure offers a powerful "growth" and "turtling" strategy, rewarding teams for creating dense, star-like formations. It provides a long-term advantage through passive point generation and area denial, creating a valuable asset to be built and defended.

## 1. Key Changes

### 1.1. New Structure: The Heartwood
- **Files**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`
- **Concept**: A unique "wonder" that can only be built once per team.
- **Formation:** Requires a central point connected to at least 5 other "branch" points.
- **Cost:** The `[FORTIFY] Cultivate Heartwood` action sacrifices all points in the formation (center and branches).
- **Backend (`game_logic.py`):**
    - Added a new `heartwoods` dictionary to the game state.
    - Implemented the `fortify_action_cultivate_heartwood` action, including precondition checks and the sacrificial creation process.
    - Added logic to the `_start_new_turn` function to process Heartwood effects:
        - **Passive Growth:** Every 3 turns, a Heartwood spawns a new point for its team in a nearby valid location. A `new_turn_events` list was added to the state to communicate this event to the frontend for visualization.
        - **Defensive Aura:** Created a new helper function, `_is_spawn_location_valid`, which checks for proximity to other points and for the presence of an enemy Heartwood's defensive aura.
    - Refactored all point creation actions (`expand_action_spawn_point`, `expand_action_extend_line`, etc.) to use the `_is_spawn_location_valid` helper, centralizing the logic and enforcing the Heartwood's aura.
- **Frontend (`static/js/main.js`):**
    - Implemented a `drawHeartwoods` function to render the structure with a unique, pulsating visual that includes its defensive aura.
    - Added two new visual effects:
        - A "creation" effect where sacrificed points visually converge on the center.
        - A "growth" effect where a ray of light connects the Heartwood to its newly spawned point.
    - The frontend now processes `new_turn_events` from the game state to trigger these turn-based visuals.
- **Documentation (`rules.md`):**
    - Updated the rules to include the new Heartwood structure, its formation requirements, and its passive abilities.

### 1.2. Code Quality & Refactoring
- **File**: `game_app/game_logic.py`
- **Change:** Centralized the logic for validating new point positions into the `_is_spawn_location_valid` helper function. This reduces code duplication and makes it easier to add new global placement rules in the future. The new helper now accounts for minimum distance between points and the new Heartwood aura.

### 1.3. UI/UX Improvement
- **File**: `templates/index.html`, `static/js/main.js`
- **Change:** Added a "Copy Log" button to the Game Log panel. This allows users to easily copy the entire game history to their clipboard for analysis or sharing, using the `navigator.clipboard` API.