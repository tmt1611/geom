This iteration focused on enhancing the game's strategic depth and user experience based on the provided analysis and suggestions.

### 1. UI Enhancement: Action Preview
-   The "Action Preview" panel in the game-running view now correctly expands to fill the entire height of its dedicated column. This was achieved by overriding a `max-height` CSS property that was unintentionally constraining it, providing a cleaner and more readable layout for action probabilities.

### 2. New Rune: The Parallel-Rune
-   **New Formation:** A "Parallel-Rune" has been introduced. It is formed by four points creating a non-rectangular parallelogram with all four sides connected. This adds a new geometric shape for players to build and utilize.
-   **New Action (`Parallel Discharge`):** This rune unlocks a powerful area-denial action. When activated, it destroys all enemy lines that cross through the interior of the parallelogram.
-   **"Never Useless" Fallback:** If the `Parallel Discharge` hits no enemy lines, it doesn't fail. Instead, it reinforces the team's structure by creating two new points and a connecting line at the center of the parallelogram.

### 3. Improved Action Reliability
-   **`Form Bastion` Fallback:** The `Form Bastion` action is now more reliable. If a team attempts this action but has no valid formation, instead of failing the turn, it now identifies the team's most-connected fortified point and reinforces all of its connected lines, strengthening a key defensive position.

### 4. Code Cleanup
-   Removed the unused and redundant `init_game_state()` function from `game_logic.py`, simplifying the codebase.
-   Added a new geometric helper function, `is_parallelogram`, to support the new rune detection logic.

### 5. Documentation
-   The `rules.md` file has been updated to include the new Parallel-Rune and its associated action, as well as the new fallback behavior for the `Form Bastion` action, ensuring the documentation remains synchronized with the game's mechanics.