This iteration focused on a mix of code cleanup, a critical bug fix for the static deployment mode, and expanding the visual content in the Action Guide.

### 1. Code Cleanup & Refactoring
- **`game_logic.py`**: An unused helper function (`_reflect_point`) and an unused import (`is_regular_pentagon`) were removed from the main game logic file to reduce code duplication and improve clarity.

### 2. Pyodide Bug Fix
- **`static/js/api.js`**: A significant bug in the Pyodide (static/WebAssembly) mode has been fixed. The previous implementation failed to load several essential Python files (`game_data.py`, `turn_processor.py`, and all action handlers in `game_app/actions/`). This prevented the game from running when deployed as a static site (e.g., on GitHub Pages). The file loading logic has been rewritten to correctly construct the entire `game_app` package in Pyodide's virtual filesystem, ensuring the static version now functions as intended.

### 3. New Illustrations for Action Guide
To further enhance the user experience and visual clarity of the game's mechanics, I have developed and implemented illustrations for three previously un-illustrated, high-impact Rune actions:

- **Rune: Focus Beam:** Depicts a Star-Rune firing a concentrated beam from its center to destroy a high-value enemy structure.
- **Rune: Cardinal Pulse:** Shows a Plus-Rune being consumed to unleash four beams in cardinal directions, illustrating one beam destroying an enemy line and another creating a new friendly point.
- **Rune: Parallel Discharge:** Illustrates a Parallelogram-Rune emitting an energy blast that destroys an enemy line crossing its interior.