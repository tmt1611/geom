This iteration focuses on a major code cleanup, UI/UX enhancements for the setup phase, and the introduction of a new chaotic, map-altering gameplay mechanic.

### 1. Major Code Refactoring: Log Generation

-   **File**: `game_app/game_logic.py`
-   **Change**: The large and unwieldy `if/elif` block in `run_next_action` for generating log messages has been completely replaced. A new private helper method, `_get_action_log_messages`, now uses a clean, maintainable dictionary to map action types to their corresponding log message strings.
-   **Benefit**: This resolves a significant piece of technical debt, making the `run_next_action` method much shorter and more readable. Adding or modifying log messages for new actions is now a trivial, single-line change in the dictionary, vastly improving maintainability.

### 2. New Gameplay Mechanic: Whirlpool

-   **Files**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`
-   **Concept**: A new sacrifice action, `[SACRIFICE] Create Whirlpool`, has been introduced.
-   **Mechanics**:
    -   **Cost**: A team sacrifices one of its non-critical points.
    -   **Effect**: A chaotic whirlpool is created at the point's location. For 4 turns, it slowly pulls all nearby points (both friendly and enemy) towards its center while swirling them around. This can be used to disrupt enemy formations, pull targets into range, or create general chaos on the battlefield.
-   **Backend (`game_logic.py`):**
    -   A new `whirlpools` list has been added to the game state.
    -   The `sacrifice_action_create_whirlpool` function was implemented.
    -   The main turn-update logic in `_start_new_turn` now processes active whirlpools, updating the coordinates of affected points each turn using polar coordinate math for the spiral motion.
-   **Frontend (`static/js/main.js`):**
    -   A new `drawWhirlpools` function renders a visual vortex effect for active whirlpools on the canvas, providing clear visual feedback for the area of effect.

### 3. UI/UX Improvements

-   **Files**: `static/js/main.js`, `templates/index.html`
-   **Change 1: Smarter Team Creation Defaults**:
    -   The team color input now defaults to a new, random, visually appealing (HSL-based) color each time a team is added, encouraging more colorful and diverse-looking games without manual user effort.
    -   The team trait selection now defaults to "Random". The backend will assign a random trait (`Aggressive`, `Expansive`, etc.) when a team is created with this option. This aligns with the game's design goal of being a "highly random" sandbox.
-   **Benefit**: These changes streamline the setup process for the user, making it quicker to get a varied and interesting game running.

### 4. Documentation

-   **File**: `rules.md` and `README.md`
-   **Change**: The rules have been updated to include a description of the new **[SACRIFICE] Create Whirlpool** action and to mention the "Random" trait option. The `README.md` was updated to provide a better overview of game actions and direct users to `rules.md` for details.