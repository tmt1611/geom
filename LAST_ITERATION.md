### Action System Redesign (Part 2): Expanding "Never Useless" Philosophy

This iteration continues the significant redesign of the action system, further embedding the principle that an action should always have a meaningful effect. I've expanded the "Primary/Fallback" effect model to more actions, increasing the simulation's dynamism and strategic depth while cleaning up the codebase.

-   **Files Modified**: `game_app/game_logic.py`, `static/js/main.js`

-   **Core Change**: I refactored several more actions to have both a primary (ideal) effect and a secondary (fallback) effect. This makes the game more resilient to "dead" turns and creates more interesting, emergent behaviors.

-   **Specific Action Changes**:
    1.  **`expand_add_line`**:
        -   **Primary Effect**: Connects two friendly points with a new line.
        -   **Fallback Effect**: If all points are already fully connected, instead of failing, the action now **Reinforces** a random existing line, increasing its strength and making it more durable against attacks.
    2.  **`fight_convert_point`**:
        -   **Primary Effect**: Sacrifices a line to convert a nearby enemy point.
        -   **Fallback Effect**: If no enemy point is in range to be converted, the line's sacrifice is not wasted. It now creates a **Repulsive Pulse** at its midpoint, pushing all nearby enemy points away and disrupting their formation.
    3.  **`fortify_mirror_structure`**:
        -   **Primary Effect**: Creates new points by reflecting existing ones across a chosen axis.
        -   **Fallback Effect**: If no valid locations can be found for the new mirrored points, the action now **Reinforces** the structure by strengthening all lines connected to the points that were *intended* for mirroring.
    4.  **`rune_shoot_bisector`** (V-Rune):
        -   **Primary Effect**: Fires a powerful beam from the rune's vertex, destroying the first enemy line it hits.
        -   **Fallback Effect**: If the beam misses all targets, it now "scars" the battlefield by creating a temporary, impassable **Fissure** along its path.
    5.  **Shield Rune Duality**: The two actions available from a Shield Rune now have complementary fallback effects, making the rune more versatile.
        -   `rune_area_shield`: If there are no friendly lines inside the rune to shield, it will now emit a gentle pulse to **push friendly points away** from the center, helping to de-clutter a dense formation.
        -   `rune_shield_pulse`: If there are no enemy points in range to push away, it will now **pull friendly points in** toward the center, helping to consolidate a scattered formation.

-   **System-level Improvements**:
    -   **Bug Fix**: Fixed a critical bug where Monolith structures were not correctly applying strength to friendly lines due to a typo (`empowered_lines` vs. `line_strengths`).
    -   **Code Cleanup**: Removed the now-obsolete `_find_possible_conversions` helper function, as its logic has been integrated directly into the refactored `fight_action_convert_point` function.
    -   **Frontend Visuals**: Added new visual effects in `static/js/main.js` for all new fallback actions (`line_flash`, `point_pull`, etc.) and fixed a bug preventing strengthened lines from appearing thicker.