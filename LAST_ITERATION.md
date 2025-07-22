This iteration introduces a new strategic element—the Hourglass Rune—and significantly enhancing the game's visual feedback to make actions more distinct and satisfying. Key structures and actions now have unique, thematic animations, improving the overall aesthetic and clarity of the auto-battle.

### 1. New Rune and Mechanic: The Hourglass Rune & Stasis

-   **Files**: `game_app/game_logic.py`, `rules.md`, `static/js/main.js`
-   **Change**: A new strategic rune, the **Hourglass Rune**, has been introduced.
    -   **Formation**: It forms from five points creating two triangles that share a single common vertex.
    -   **New Mechanic**: The rune unlocks the **[RUNE] Time Stasis** action. This ability targets a nearby vulnerable enemy point and "freezes" it for several turns.
    -   **Stasis Effect**: Points in stasis cannot be targeted by most actions (e.g., `Pincer Attack`, `Convert Point`, `Sentry Zap`), effectively removing them from play temporarily.
    -   **Frontend**: Hourglass runes are highlighted with a distinct double-triangle shape. Points in stasis are rendered with a pulsating "cage" effect, clearly indicating their status. The action itself is visualized by a beam of energy traveling from the rune's vertex to the target.
-   **Benefit**: The Stasis mechanic adds a new layer of control and counter-play. It allows teams to neutralize high-value enemy assets without destroying them, creating opportunities for strategic maneuvers and disrupting enemy formations.

### 2. Systematically Redesigned Visual Effects

-   **Files**: `static/js/main.js`, `game_app/game_logic.py`
-   **Change**: Several core actions now have unique and more thematic visual effects, replacing generic animations.
    -   **Bastion Formation**: Instead of a simple pulse, forming a bastion now triggers a "shield-up" animation where growing energy shields appear along the bastion's lines.
    -   **Monolith Formation**: A monolith's creation is now heralded by a beam of light descending from the sky, visually "erecting" the structure.
    -   **Convert Point**: This action now shows a swirling spiral of energy transferring from the sacrificed line's midpoint to the converted point, providing a clear visual narrative for the action.
-   **Benefit**: These distinct, high-impact visuals make the game more engaging to watch. Each major event is now instantly recognizable, making the flow of the battle easier to follow and more aesthetically pleasing.

### 3. Codebase Refinements for New Mechanics

-   **File**: `game_app/game_logic.py`
-   **Change**:
    -   The game state now properly tracks the new `stasis_points` status, including a turn-based countdown managed in the `_start_new_turn` phase.
    -   Point-targeting actions (`fight_pincer_attack`, `fight_convert_point`, etc.) have been updated to recognize and respect the stasis effect, preventing them from targeting frozen points.
    -   The `_check_hourglass_rune` function was added to the rune detection system, and the new action was integrated into the action selection logic (`_get_all_actions_status`, weights, etc.).
-   **Benefit**: The codebase has been cleanly extended to support the new Stasis mechanic, ensuring it integrates smoothly with existing game rules and logic. This maintains the robustness and extensibility of the game engine.