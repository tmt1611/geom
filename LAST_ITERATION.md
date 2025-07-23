This iteration focuses on cleaning up the codebase by removing data duplication and refactoring a verbose function to be more maintainable and data-driven.

**Summary of Changes:**

1.  **Completed Data Separation (`game_data.py`, `text_data.py`):**
    *   The previous iteration had moved text dictionaries to `text_data.py` but left duplicated definitions in `game_data.py`.
    *   I have now removed the duplicated `ACTION_DESCRIPTIONS` and `ACTION_VERBOSE_DESCRIPTIONS` dictionaries from `game_data.py`.
    *   `game_data.py` now correctly imports these, along with `DEFAULT_TEAMS`, directly from `text_data.py`, making `text_data.py` the single source of truth for static game text. This eliminates redundancy and improves code organization.

2.  **Refactored Point Augmentation Logic (`game_logic.py`):**
    *   The `_augment_points_for_frontend` method, which adds boolean flags to point objects for rendering, was a long, hardcoded block of checks.
    *   I have refactored this function to be data-driven. A new dictionary, `POINT_AUGMENTATIONS`, now defines the relationship between a flag name (e.g., `'is_anchor'`) and the data source to check against.
    *   The function now pre-fetches all necessary data sets and then iterates through this configuration dictionary, making the code cleaner, more declarative, and significantly easier to extend with new point statuses in the future.