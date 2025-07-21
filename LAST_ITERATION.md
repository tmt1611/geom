# Iteration Analysis and Changelog

This iteration focuses on expanding the strategic depth of the game by introducing a new geometric structure: the **Prism**. This structure encourages a different style of play, rewarding teams for building adjacent, connected territories. The Prism unlocks a new, visually impressive attack action, the `Refraction Beam`, which allows for "bank shots" that can bypass conventional defenses and attack enemies from unexpected angles. This not only adds a new tactical layer but also enhances the visual spectacle of the auto-battle.

## 1. Key Changes

### 1.1. New Structure: The Prism
- **Files**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`
- **Concept:** A new passive structure formed when two of a team's claimed territories (triangles) share a common edge.
- **Bonus:** Unlocks the **[FIGHT] Refraction Beam** action.
- **Backend (`game_logic.py`):**
    - Implemented `_update_prisms_for_team` to efficiently detect Prism formations by checking for shared edges between territories.
    - Added a new `fight_action_refraction_beam` function. This action fires a "source" beam, calculates its intersection with the Prism's shared edge, and then fires a new "refracted" beam along a perpendicular axis to destroy an enemy line.
    - A new helper function, `get_segment_intersection_point`, was added to calculate the precise intersection point between two line segments.
    - Integrated the new action into the AI's decision-making process (`_choose_action_for_team`), giving it a high weight to encourage its use.
- **Frontend (`static/js/main.js`):**
    - Implemented `drawPrisms` to provide a clear visual indicator for active Prisms by rendering a glow effect on their shared edge.
    - Added a custom visual effect for the `refraction_beam` action, showing the initial yellow source beam followed by the powerful red refracted beam, making the action's mechanics clear and visually satisfying.
    - Updated the "Live Stats" panel to show the count of active Prisms for each team, alongside Runes.
- **Documentation (`rules.md`):**
    - Updated the rules to explain the Prism formation, its requirements, and the new Refraction Beam action it unlocks.

### 1.2. Helper Function and Code Refinements
- **File**: `game_app/game_logic.py`
- **Change:** Added the global helper function `get_segment_intersection_point` to support the new refraction action. This is more versatile than the existing `segments_intersect` boolean check. The turn logic now calls `_update_prisms_for_team` before a team takes its turn, ensuring all structures are up-to-date.