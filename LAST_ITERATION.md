This iteration focuses on cleaning up the codebase by refactoring duplicated code. Specifically, several geometric helper functions were present in multiple files (`game_logic.py`, `formations.py`). These have been consolidated into the `geometry.py` module, making it the single source of truth for geometric calculations.

### Code Cleanup: Geometry Function Consolidation

1.  **Centralized `polygon_area` and `is_point_inside_triangle`**:
    - The `_polygon_area` and `_is_point_inside_triangle` methods were duplicated in `game_logic.py` and `formations.py`.
    - These have been moved to `geometry.py` as stateless, public functions: `polygon_area()` and `is_point_inside_triangle()`.
    - All modules (`game_logic.py`, `formations.py`, `rune_actions.py`) have been updated to import and use these centralized functions, removing the duplicated local implementations.

2.  **Centralized Ray/Border Collision Logic**:
    - The `_get_extended_border_point` and `_is_ray_blocked` methods were duplicated in `game_logic.py` and `geometry.py`.
    - The implementations in `game_logic.py` were removed.
    - The call site in `rune_actions.py` was updated to use the canonical function from `geometry.py`, ensuring consistent collision detection with fissures and barricades.

These changes significantly improve the codebase's maintainability and consistency by adhering to the Don't Repeat Yourself (DRY) principle, without altering any game logic.