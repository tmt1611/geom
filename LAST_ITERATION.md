This iteration introduces significant refactoring to `game_logic.py` to improve its structure, readability, and maintainability. A bug related to Monolith line strengthening has also been fixed.

### 1. Refactored `game_logic.py` for Clarity and Maintainability

Several of the largest and most complex methods in the `Game` class have been broken down into smaller, more focused helper methods.

- **`get_state()` Refactoring:** The `get_state()` method, which prepares the game state for the frontend, was over 100 lines long. Its core responsibilities—augmenting points, augmenting lines, and calculating live stats—have been extracted into separate helper methods (`_augment_points_for_frontend`, `_augment_lines_for_frontend`, `_calculate_live_stats`). This makes the `get_state` method a clean, high-level summary of its function and makes the augmentation logic easier to manage.

- **`_start_new_turn()` Refactoring:** This was the largest method in the class, responsible for all start-of-turn maintenance. It has been refactored into a clear orchestrator method that calls a series of new, single-purpose helpers:
  - `_process_shields_and_stasis()`
  - `_process_rift_traps()`
  - `_process_anchors()`
  - `_process_heartwoods()`
  - `_process_whirlpools()`
  - `_process_monoliths()`
  - `_process_wonders()`
  - `_process_spires_fissures_barricades()`
  - `_build_action_queue()`

This change dramatically improves the readability of the turn-start logic, isolating the complex rules for each game object into its own manageable function.

### 2. Bug Fix: Monolith Line Strengthening

During the refactoring of `_start_new_turn`, a bug was discovered and fixed in the Monolith processing logic. The code was attempting to read from and write to a non-existent `self.state['empowered_lines']` dictionary instead of the correct `self.state['line_strengths']`. The refactored `_process_monoliths` method now correctly calls the `_strengthen_line` helper, ensuring Monoliths function as intended.

### 3. Code Consolidation

- The `expand_action_grow_line` method contained a custom implementation of the "strengthen line" fallback effect. This has been replaced with a call to the existing `_fallback_strengthen_random_line` helper method, reducing code duplication and ensuring consistent behavior for fizzled actions.

These changes result in a cleaner, more organized, and more correct `game_logic.py` file, making future development and debugging significantly easier.