This iteration combines code cleanup with the introduction of a new strategic action based on topological and warfare concepts.

### 1. Code Cleanup and Consistency

Multiple files were updated to fix bugs and ensure consistency for existing actions:

*   **Duplication Bug:** In `fortify_actions.py`, a duplicated `reposition_point` method and its corresponding `can_perform` check were removed.
*   **Missing Action Data:** The `fortify_attune_nexus` action was fully integrated into the game's data structures (`game_data.py`, `game_logic.py`), making it available for teams to use.
*   **Documentation Update:** The official `rules.md` was updated to include the descriptions for `Attune Nexus` and `Reposition Point`, and to correct the category for `Shield Line` to `[FORTIFY]` for consistency.

### 2. New Warfare/Topology Action: Isolate Point

A new action has been added to the `Fight` category, introducing concepts of topological weak points and strategic isolation from warfare.

*   **Action:** `Isolate Point`
*   **Concept:** This action is inspired by the military tactic of cutting off enemy supply lines by targeting critical infrastructure. In the game's context, this translates to identifying and neutralizing an enemy's "articulation point".
*   **Topological Basis:** An articulation point (or cut vertex) is a point in a graph which, if removed, would split the graph into separate, disconnected components. These points are the glue holding a team's structure together.
*   **Mechanics:**
    1.  The action identifies an enemy articulation point.
    2.  It sacrifices a friendly line to "isolate" the target.
    3.  The isolated point cannot be used by its owner and becomes vulnerable. Each turn, it has a chance to collapse and be destroyed.
*   **Strategic Impact:** This provides a way to dismantle an opponent's network without direct destruction, creating strategic decay. It encourages players (and the AI) to build resilient, interconnected structures rather than long, fragile chains.
*   **Fallback:** If no enemy articulation point can be found, the action creates a temporary defensive `barricade` instead, representing a shift to a defensive posture.