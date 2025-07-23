This iteration focuses on a combination of code cleanup and further UI improvements for the Action Guide, building on the previous work.

### Code Refactoring

1.  **Cleaner Rune Logic (`game_logic.py`)**: The internal helper method `_get_all_rune_point_ids`, which is crucial for identifying which points are part of important structures, was complex due to the varied data structures of different runes.
    *   I refactored this by defining two centralized sets of keys (`_RUNE_LIST_POINT_ID_KEYS` and `_RUNE_SINGLE_POINT_ID_KEYS`) that categorize all possible ways point IDs are stored in rune data.
    *   The `_get_all_rune_point_ids` method was rewritten to use these sets, making it significantly shorter, cleaner, and more maintainable. Now, adding new rune structures in the future will be less error-prone.

### UI/UX Improvements: Action Guide

1.  **Consistent Illustrations**: In the last iteration, I missed a few action illustrations that were still using a text emoji ('💥') for impacts. I've now fixed this to ensure all illustrations are visually consistent.
    *   In `static/js/main.js`, I replaced the remaining emoji-based explosions in the illustrators for `fight_bastion_pulse`, `sacrifice_whirlpool`, `rune_starlight_cascade`, `rune_focus_beam`, `rune_cardinal_pulse`, and `rune_parallel_discharge` with calls to the standardized `drawExplosion` helper function. This completes the visual cleanup of the action guide.