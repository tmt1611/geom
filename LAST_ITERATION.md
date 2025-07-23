This iteration introduces two significant code cleanup efforts to improve code quality and maintainability, adhering to the DRY (Don't Repeat Yourself) principle.

**Key Changes:**

1.  **Refactored Sacrificial Point Selection:**
    *   The `_find_non_critical_sacrificial_point` method in `game_logic.py` was refactored for clarity and performance.
    *   It previously contained a complex, inefficient implementation for detecting articulation points (critical connection points).
    *   It now reuses the existing, more efficient `_find_articulation_points` helper method. This change makes the code shorter, faster, and its logic easier to follow.

2.  **Centralized Line Strengthening Logic:**
    *   Identified that the logic for strengthening a line (increasing its strength stat up to a maximum) was duplicated across multiple action handler files (`expand_actions.py`, `fortify_actions.py`, `rune_actions.py`).
    *   Replaced all instances of this manual logic with a call to the centralized `_strengthen_line` helper in `game_logic.py`. This reduces code duplication and ensures that line strengthening is handled consistently everywhere.