This iteration introduces a new strategic element inspired by geomancy and Feng Shui: **Ley Lines**. This feature adds a new layer to the `Fortify` strategy, encouraging players to build specific formations (I-Runes) and then expand around them to gain bonuses.

### 1. New Concept: Ley Lines

A new action, `Create Ley Line`, has been added, bringing concepts of energy flow and strategic placement into the game.

*   **Concept:** Ley Lines are mystical lines of energy that run across the battlefield. In the game, they are formed by activating an existing `I-Rune` (a straight line of 3 or more connected points). This is inspired by the idea of building upon existing energy conduits.
*   **Mechanics:**
    1.  A team with an `I-Rune` can use the **`[FORTIFY] Create Ley Line`** action.
    2.  This converts the I-Rune into an active Ley Line for several turns.
    3.  **Bonus Effect:** While the Ley Line is active, any new friendly point created near it is automatically connected to the closest point on the Ley Line with a free bonus line. This promotes structured expansion and reinforces the team's control over the area.
    4.  **Fallback:** If all of a team's I-Runes are already converted into Ley Lines, the action instead **pulses** an existing Ley Line, strengthening all lines connected to it.
*   **Strategic Impact:** This encourages players to think about not just where they expand, but *how*. Building long, straight formations becomes a valuable long-term strategy, as these can be turned into conduits for rapid, reinforced expansion.

### 2. Code Implementation

To support this new feature, the following changes were made:

*   **`fortify_actions.py`:** A new `create_ley_line` method and its `can_perform_create_ley_line` precondition check have been added.
*   **`game_logic.py`:** The game state now tracks `ley_lines`. A new helper method, `_check_and_apply_ley_line_bonus`, was created to handle the bonus effect whenever a new point is created by any `Expand` action.
*   **`expand_actions.py`:** All actions that create new points (`spawn_point`, `extend_line`, `fracture_line`, etc.) have been updated to call the new bonus-checking helper and include any bonus lines in their action results.
*   **`turn_processor.py`:** Logic has been added to handle the turn-based decay of active Ley Lines.
*   **`game_data.py`:** All necessary descriptions, logs, and mappings for the new action have been added.
*   **`static/js/main.js`:** A new `drawLeyLines` function was created to give them a distinct, glowing visual effect on the canvas. The `processActionVisuals` function was updated to handle the new `ley_line_fade` and `ley_line_bonus` events.

This change is self-contained, enhances strategic depth, and fits the user's request to incorporate concepts from geomancy/Feng Shui while maintaining clean code.