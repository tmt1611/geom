This iteration focuses on deepening the strategic variety of the game by implementing new runes, adding "never useless" fallbacks to several actions, and ensuring the codebase is clean and consistent.

### 1. New Rune: The Plus-Rune (+)
A new high-level rune has been implemented, as requested.
-   **Formation (`+`):** Requires five points in a plus-shape, with a central point connected to four arms that form two perpendicular lines.
-   **Detection:** Added the `_check_plus_rune` method to robustly detect this formation.
-   **Action:** The existing `rune_cardinal_pulse` action is now correctly tied to this rune. When activated, the rune is consumed in a powerful attack, firing four destructive beams from its center. This provides a strong incentive for players to build complex geometric structures.

### 2. New Rune: The Parallel-Rune
To introduce more geometric concepts, a new rune based on parallelograms has been added.
-   **Formation:** Requires four points forming a parallelogram, with all four outer edge lines connected.
-   **Action (`Parallel Discharge`):** The rune can be activated to discharge energy across its area, destroying any enemy lines that cross between its parallel sides.
-   **Fallback:** If the discharge hits no targets, it creates two new points and a connecting line in the center of the formation, reinforcing the team's structure.

### 3. "Never Useless" Action Enhancements
Several actions that could previously fail and result in a wasted turn now have strategic fallbacks.
-   **`Form Bastion`:** If no valid formation is found, the action now reinforces the lines connected to the most promising "core" candidate point, strengthening a key defensive position.
-   **`Starlight Cascade` (Star-Rune):** If there are no enemy lines in range to damage, the sacrificed point now explodes in a chaotic shockwave, pushing *all* nearby points (friend and foe) away, creating disruption instead of targeted damage.

### 4. Code Health and Bug Fixes
-   **Cleaned `game_logic.py`:** Removed several duplicated methods and a redundant `__init__` constructor that were present in the `Game` class, improving code clarity and correctness.
-   **Updated Documentation:** The `rules.md` file has been updated to include the new runes and the new action fallbacks, ensuring the documentation accurately reflects the game's mechanics.
-   **Expanded Game State:** The core game state dictionary was updated to track the new `parallel` rune type.