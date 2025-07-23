This iteration focuses on cleaning up the codebase by refactoring duplicated logic into centralized helper methods, making the code more DRY (Don't Repeat Yourself).

**Key Changes:**

1.  **Centralized Territory Logic:**
    *   Identified that the logic for finding the boundary lines of a claimed territory was duplicated across three different action handler files (`expand_actions.py`, `fight_actions.py`, `fortify_actions.py`).
    *   Created two new helper methods in `game_logic.py`: `_get_territory_boundary_line_keys` (for a single territory) and `_get_all_territory_boundary_line_keys` (for all of a team's territories).
    *   Refactored the three action handler files to use these new, centralized helpers, removing the repeated code blocks.

2.  **Simplified `pincer_attack` Logic:**
    *   The `pincer_attack` method in `fight_actions.py` had two separate blocks of code that would trigger the same fallback effect (creating a barricade).
    *   Refactored the method to remove the initial check, allowing the logic to flow naturally to a single fallback block at the end if no valid attack target is found. This makes the code shorter and easier to follow.