This iteration focuses on a significant code cleanup by refactoring how frontend visualization flags for points are generated. The goal is to make this process more modular, maintainable, and data-driven by leveraging the existing `structure_data.py` registry, adhering to the DRY (Don't Repeat Yourself) principle.

### Key Changes:

1.  **Data-Driven Point Augmentation:** The `_get_structure_point_ids_by_type` method in `game_logic.py`, which gathers point IDs for special rendering flags, was previously hardcoded. It has been completely rewritten to be dynamically driven by the `STRUCTURE_DEFINITIONS` registry. This eliminates the need to manually update this function whenever a new visual structure is added to the game.

2.  **Enhanced Structure Registry:** To support the refactoring, the `STRUCTURE_DEFINITIONS` in `structure_data.py` has been enhanced with new metadata keys (`frontend_flag_key` and `frontend_flag_keys`). These keys explicitly link a structure's definition to the specific flags used by the frontend, making the connection clear and easy to manage.

3.  **Improved I-Rune Definition:** The definition for `rune_i_shape` was updated to include all its distinct point lists (`point_ids`, `internal_points`, `endpoints`). This allows the new data-driven system to correctly identify all specialized points within the I-Rune (such as the "sentry eye" and "posts") for unique visual rendering.

These changes centralize the logic for identifying structure points, reduce code redundancy, and make it simpler to add new structures with unique visual properties in the future.