This iteration introduces a new high-tier rune, enhances the user's insight into the game's mechanics, and adds more distinct and visually stunning effects for key actions, improving both strategic depth and visual appeal.

### 1. New Rune: The Trident Rune

-   **Files**: `game_app/game_logic.py`, `rules.md`, `static/js/main.js`
-   **Change**: A new offensive rune, the **Trident Rune**, has been added.
    -   **Formation**: It forms from a "pitchfork" shape: an isosceles triangle with a fourth "handle" point extending from the apex.
    -   **Ability**: Unlocks the **[RUNE] Impale** action, a devastating attack that fires a beam to destroy *all* enemy lines in its path, piercing through shields and other defenses.
    -   **Frontend**: Trident Runes are now drawn with a distinct glowing effect. The Impale action has a unique, powerful beam animation with multiple impact explosions.
-   **Benefit**: The Trident Rune adds a new high-level strategic objective for players. Its powerful action provides a tool to break through heavily fortified areas, creating more dynamic late-game scenarios.

### 2. Enhanced Action Transparency

-   **Files**: `game_app/game_logic.py`, `game_app/routes.py`, `static/js/main.js`, `static/css/style.css`, `templates/index.html`
-   **Change**: The "Action Preview" panel has been significantly upgraded. A new "Show Invalid" toggle allows users to see not just the team's possible actions, but also all the actions they *cannot* perform.
    -   Invalid actions are greyed out and have a tooltip explaining the reason for their invalidity (e.g., "Requires more than 2 points," "No active Sentry").
-   **Benefit**: This provides players with much deeper insight into the game's rules and each team's current strategic limitations, making the AI's decisions more understandable and the game state easier to analyze.

### 3. New and Redesigned Visual Effects

-   **Files**: `static/js/main.js`
-   **Change**: Key action visuals have been added or redesigned to be more unique and impactful.
    -   **Phase Shift**: Now creates two linked, shimmering portals, visually representing the teleportation from origin to destination.
    -   **Structure Formation**: Actions like `Form Bastion` now trigger a "power-up" animation where the structure's points and lines pulse with energy, giving clearer feedback on its creation.
    -   **Impale**: The new rune action is visualized with a thick, piercing energy beam and multiple small explosions at each point of impact.
-   **Benefit**: These visual enhancements make the game more exciting to watch and provide clearer, more intuitive feedback for complex game events.

### 4. Codebase Refactoring for Robustness

-   **File**: `game_app/game_logic.py`
-   **Change**: The logic for determining action validity has been centralized into a new `_get_all_actions_status` helper method. This method now serves as the single source of truth for checking action preconditions.
-   **Benefit**: This refactoring eliminates redundant checks that were scattered across the codebase. It simplifies the `_get_possible_actions` method and cleanly powers the new enhanced action preview feature. The result is more robust, maintainable, and easier-to-extend game logic.