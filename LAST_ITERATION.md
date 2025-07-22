This iteration focuses on a significant code cleanup and continues the expansion of the Action Guide with new illustrations and corresponding animations.

### 1. Code Refactoring and Organization

To improve maintainability and readability, the monolithic `game_logic.py` file has been broken down into more specialized modules.

- **`game_app/geometry.py` (New File):**
  - All generic, stateless geometric helper functions (like `distance_sq`, `is_rectangle`, `segments_intersect`, etc.) have been moved from `game_logic.py` into this new, dedicated file.
  - This separation of concerns makes the core geometric utilities reusable and easier to test independently.

- **`game_app/formations.py` (New File):**
  - A new `FormationManager` class has been created in this file.
  - Its responsibility is to detect all complex geometric structures on the board, such as Runes (V-Rune, Shield-Rune, etc.), Prisms, Nexuses, and Trebuchets.
  - Over 20 methods related to structure detection were moved from the main `Game` class into this manager, significantly reducing the size and complexity of `game_logic.py`.
  - The `Game` class now holds an instance of `FormationManager` and delegates all formation-checking tasks to it.

- **`game_logic.py` (Refactored):**
  - The file is now much shorter and more focused on the core game loop and action execution.
  - It now imports from the new `geometry` and `formations` modules, leading to cleaner code.

- **Supporting Files (`utils.py`, `api.js`):**
  - Both files were updated to recognize the new Python modules (`geometry.py`, `formations.py`). This ensures that the live-update checker and the Pyodide (in-browser) version of the game continue to function correctly.

### 2. New Action Illustrations and Animations

The "Action Guide" continues to be a priority. Five new illustrations and their corresponding animations have been added to provide better visual feedback to the user.

- **`static/js/main.js`**:
  - The `illustrationDrawers` object, which powers the Action Guide, now includes drawings for:
    - `fortify_cultivate_heartwood`: Shows the sacrifice of a star-like formation to create a central Heartwood.
    - `fortify_form_purifier`: Illustrates the formation of a perfect pentagon structure.
    - `fight_launch_payload`: Depicts a kite-shaped Trebuchet firing an arcing projectile.
    - `rune_hourglass_stasis`: Visualizes an hourglass rune freezing an enemy point in a cage of light.
    - `sacrifice_rift_trap`: Shows a point imploding to leave behind a latent, shimmering trap.
  - The `actionVisualsMap` object has been updated with new animation handlers for these actions, reusing and extending the existing animation system for effects like projectile arcs, implosions, and flashes.

This refactoring makes the project's structure more scalable for future development, while the new visuals continue to enrich the user's understanding of the game's complex mechanics.