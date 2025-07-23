This iteration focuses on two main areas: code quality and user interface enhancement.

### Code Refactoring: Centralized Geometry Logic

1.  **Eliminated Duplication**: The geometry utility functions `_get_extended_border_point` and `_is_ray_blocked` were duplicated in `game_logic.py`. These methods were removed from `game_logic.py` to establish `geometry.py` as the single source of truth for geometric calculations.

2.  **Improved Encapsulation**: The functions in `geometry.py` are pure functions that receive all necessary data (like `grid_size`, `fissures`, `barricades`) as arguments. The old methods in `game_logic.py` accessed the game state directly (`self.state`). This refactoring improves encapsulation and makes the geometry functions more modular and easier to test.

3.  **Updated Action Handlers**: All action handler modules (`expand_actions.py`, `fight_actions.py`, `rune_actions.py`) were updated to import and use the centralized functions from `geometry.py`, passing the required state information as parameters. This makes the data flow more explicit and the code easier to follow.

### UI Improvement: Action Guide Enhancements

1.  **Action Counts**: The filter buttons in the "Action Guide" tab now display a count of how many actions belong to each category (e.g., "Fight (10)", "Expand (6)"). This gives users a quick overview of the action distribution in the game.

2.  **Sorted Categories**: The filter buttons are now sorted alphabetically for a more organized and predictable user experience.

These changes result in a cleaner, more maintainable codebase and a slightly more informative user interface.