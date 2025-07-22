This is a substantial update focusing on enhancing strategic depth, improving user interface clarity, and enriching the visual experience.

### 1. New Rune Power & Improved Action Logic

-   **Files**: `game_app/game_logic.py`, `rules.md`
-   **Change**: A new action has been added to an existing rune, and a key strategic action has been made smarter.
    -   **New Action**: The **Shield Rune** was previously only for the `Area Shield` action. It now also unlocks **`[RUNE] Shield Pulse`**, a defensive shockwave that forcefully pushes all nearby enemy points away from the rune's center, allowing for tactical repositioning and breaking up enemy formations.
    -   **Smarter Sacrifices**: The `[SACRIFICE] Phase Shift` action logic has been significantly improved. It now intelligently avoids sacrificing lines that would leave a point isolated (a "bridge" line), preserving the team's structural integrity. This makes the AI's use of this powerful repositioning tool less self-destructive and more strategic.

### 2. Enhanced Action Preview Panel

-   **File**: `static/js/main.js`
-   **Change**: The "Action Preview" panel, which details the upcoming team's turn, has been redesigned for clarity. Actions are now grouped into logical categories: **Fight, Expand, Fortify / Defend, Sacrifice,** and **Rune**.
-   **Benefit**: This organization makes the long list of potential actions much easier to parse. Players can now quickly assess a team's strategic posture—whether it's leaning towards offense, defense, or expansion—by seeing which categories have the most available actions and highest probabilities.

### 3. Diverse and Thematic Visual Effects

-   **Files**: `static/js/main.js`, `game_app/game_logic.py`
-   **Change**: Several key actions have received unique, thematic visual effects to make them more distinct and visually impressive, moving away from generic highlights.
    -   **`Form Bastion`**: Triggers a "shield-up" animation where growing, semi-transparent energy shields materialize along the bastion's perimeter lines.
    -   **`Form Monolith`**: A dramatic beam of light now descends from the top of the screen to the monolith's center, visually "erecting" the structure.
    -   **`Convert Point`**: Now shows a swirling stream of energy particles flowing from the sacrificed line's midpoint to the newly converted point, clearly illustrating the transfer of allegiance.
    -   **`Shield Pulse`**: The new rune action is visualized with a powerful radial shockwave expanding from the rune's center, visually matching its push effect.
-   **Benefit**: These new visuals make the game more exciting to watch and provide immediate, intuitive feedback for major game events. Each significant action now has a unique visual signature.

### 4. Codebase & Rule Documentation

-   **Files**: `game_logic.py`, `rules.md`
-   **Change**: The codebase was updated to integrate the new `Shield Pulse` action, including its weight, trait multipliers, and preconditions. The `rules.md` file has been updated to document the new action, ensuring the game's mechanics remain transparent and understandable.