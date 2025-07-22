This iteration focuses on making the game's logic more transparent to the user, enhancing strategic depth with a new rune, and improving the visual flair of actions.

### 1. New Feature: Action Preview Panel

-   **Files**: `game_app/game_logic.py`, `game_app/routes.py`, `static/js/main.js`, `templates/index.html`, `static/css/style.css`
-   **Change**: A new "Action Preview" panel has been added to the UI. At the start of each team's turn, this panel now displays:
    -   The name of the team whose turn it is.
    -   A list of all possible actions they can take.
    -   The percentage chance for each action to be selected, visualized with a bar graph.
-   **Benefit**: This makes the AI's decision-making process transparent and engaging. Users can now see why a team performs a certain action based on its available options and trait-influenced probabilities, adding a layer of analytical depth to the viewing experience.

### 2. New Rune and Action: The Shield Rune

-   **Files**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`
-   **Change**: A new defensive rune, the **Shield Rune**, has been introduced.
    -   **Formation**: It forms when three of a team's points, connected by lines to form a triangle, enclose another friendly point (the "core").
    -   **Ability**: The rune unlocks the **[RUNE] Area Shield** action. When used, it applies a temporary shield to all friendly lines located inside the rune's triangular boundary, offering a powerful way to protect a core part of a team's structure.
    -   **Frontend**: Shield Runes are now visualized as a pulsating, translucent triangle, and the Area Shield action triggers a distinct visual effect.
-   **Benefit**: The Shield Rune provides a strong defensive and area-denial option, encouraging players to build dense, layered formations and offering a new strategic counter to area-of-effect attacks.

### 3. Code Refactoring and Cleanup

-   **File**: `game_app/game_logic.py`
-   **Change**: The action selection logic in `_choose_action_for_team` has been significantly refactored. The large dictionaries for action weights and multipliers were moved to class-level constants (`ACTION_BASE_WEIGHTS`, `TRAIT_MULTIPLIERS`). A new helper method, `_get_action_weights`, now centralizes the logic for calculating weighted probabilities.
-   **Benefit**: This refactoring reduces code duplication, as the new `get_action_probabilities` method and the `_choose_action_for_team` method now share the same core logic. This makes the system more maintainable and easier to expand with new actions or traits in the future.

### 4. Enhanced Visual Effects

-   **File**: `static/js/main.js`
-   **Change**: The system for handling action visuals has been refactored from a large `if/else if` block into a more organized, dispatch-map pattern. Several key visual effects were enhanced to be more dynamic and "stunning":
    -   **Attack Line**: Now an animated, streaking "comet" that travels from the attacker to the target's line.
    -   **Pincer Attack**: Visualized as two converging animated rays.
    -   **Nova Burst**: Now features energetic particles bursting outwards from the explosion's center.
-   **Benefit**: These improvements make the game more visually exciting and provide clearer, more impactful feedback for game events, fulfilling one of the core design goals.