This iteration focuses on a significant code cleanup by refactoring a commonly used helper function.

The geometric helper function `is_spawn_location_valid` is called from almost every action file to verify if a new point can be created at a given coordinate. Each call required passing multiple slices of the game state (e.g., `grid_size`, `points`, `fissures`, `heartwoods`). This created repetitive, verbose code.

To address this, I have:
1.  Created a new wrapper method, `Game.is_spawn_location_valid()`, in `game_logic.py`.
2.  This new method automatically retrieves the necessary state slices and calls the underlying geometry function. This centralizes the logic and simplifies the call sites.
3.  Updated all 15+ call sites across the action handlers (`expand`, `fight`, `fortify`, etc.) and the `turn_processor` to use this new, cleaner wrapper method.
4.  The wrapper was designed to handle a few special cases where a modified list of points is needed for the check, ensuring the refactoring could be applied universally without losing functionality.

This change significantly improves code readability and maintainability by reducing boilerplate and abstracting the details of state management for this common task.