This iteration focuses on expanding the strategic depth of the game by introducing a new defensive structure, the Monolith, and improving underlying code quality.

### 1. New Structure: The Monolith

-   **Files**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`
-   **Change**: A new defensive structure, the **Monolith**, has been added.
    -   **Formation**: Teams can now perform the `[FORTIFY] Form Monolith` action, which converts four of their points into a Monolith if they form a tall, thin rectangle with connected perimeter lines.
    -   **Effect**: Every few turns, the Monolith emits a "Resonance Wave". This wave **empowers** all friendly lines within its radius, allowing them to absorb one or more attacks before being destroyed. This introduces a new layer of defense and encourages strategic positioning.
    -   **Visuals**: Monoliths, their points, empowered lines, and the resonance wave all have unique visual representations on the canvas, enhancing the visual feedback and spectacle of the game.

### 2. Code Quality: Refactoring Geometry Helpers

-   **File**: `game_app/game_logic.py`
-   **Change**: The `is_square()` helper function has been replaced with a more versatile `is_rectangle()` function. This new function not only checks if four points form a rectangle but also returns their aspect ratio.
-   **Benefit**: This refactoring simplifies the codebase. The `is_rectangle()` function is now used for multiple checks:
    -   Detecting squares for **Nexus** formations (aspect ratio ≈ 1).
    -   Detecting tall rectangles for the new **Monolith** formation (aspect ratio > 3).
    -   This makes the geometric detection logic more robust, reusable, and easier to extend in the future.

### 3. Gameplay Tuning: Attack Logic

-   **File**: `game_app/game_logic.py`
-   **Change**: The `fight_action_attack_line` logic was updated to account for the new "Empowered" line status from Monoliths.
-   **Benefit**: Instead of being destroyed, an empowered line now absorbs the hit, reducing its empowerment level. This creates more interesting tactical interactions where players must decide whether to focus fire on empowered lines or attack weaker targets. The action result and game log now reflect this new outcome ("damaged" vs. "destroyed").