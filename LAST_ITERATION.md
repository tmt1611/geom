This iteration focuses on cleaning up the codebase by refactoring geometry-related logic.

### Code Refactoring: Centralizing Geometry Logic

1.  **Identified Misplaced Logic**: I found that several geometry-related helper functions (e.g., for checking valid spawn locations, extending lines to borders) were defined within the main `Game` class in `game_logic.py`. This made the class larger than necessary and mixed state management with pure calculation logic.

2.  **Consolidated into `geometry.py`**: To address this, I moved the logic for `_is_spawn_location_valid`, `_get_extended_border_point`, and `_is_ray_blocked` out of `game_logic.py` and consolidated them into the `geometry.py` module. They are now implemented as pure functions that receive the necessary parts of the game state (like grid size, points, fissures) as arguments, rather than accessing a `self.state` object directly.

3.  **Updated Call Sites**: I updated all the action handlers (`expand_actions.py`, `fight_actions.py`, etc.) and the `turn_processor.py` to import and use these pure functions from `geometry.py`. This involved changing calls from `self.game.some_geometry_method(...)` to `some_geometry_method(...)` and passing the required state variables.

This refactoring makes the code cleaner, more modular, and easier to maintain. The `Game` class is now more focused on state and turn management, while `geometry.py` serves as the single source of truth for all geometric calculations.