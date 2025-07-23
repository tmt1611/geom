This iteration focused on cleaning up the codebase by improving the separation of concerns between game logic and pure geometric calculations. Several stateless helper functions related to geometry were moved from the main `game_logic.py` file to the more appropriate `geometry.py` module.

### Code Refactoring: Separation of Concerns

1.  **Moved Geometric Helpers:** The following stateless methods were migrated from the `Game` class in `game_logic.py` to become standalone functions in `game_app/geometry.py`:
    *   `_points_centroid` -> `points_centroid`
    *   `_get_convex_hull` -> `get_convex_hull`
    *   `_polygon_perimeter` -> `polygon_perimeter`

2.  **Corrected a Latent Bug:** The `fight_actions.py` module was calling `self.game._polygon_area`, but this method did not exist on the `Game` object. This was corrected by importing the `polygon_area` function from `geometry.py` and calling it directly.

3.  **Updated Imports and Calls:** All modules that used these helper functions (`game_logic.py`, `fight_actions.py`, `fortify_actions.py`, `rune_actions.py`) have been updated to import them from `geometry.py` and call them directly, rather than through the `game` instance.

These changes make the `Game` class smaller and more focused on its core responsibility of managing game state. The `geometry.py` module now serves as a more complete library of pure geometric utility functions, improving code organization and reusability.