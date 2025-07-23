This iteration focused on improving code quality and fixing logic bugs. Specifically, it addresses a major code duplication issue in the frontend JavaScript and refactors several backend action precondition checks to be more accurate and robust.

### 1. JavaScript Code Cleanup

A large block of code containing the `illustrationHelpers` and `illustrationDrawers` objects was duplicated in both `static/js/main.js` and `static/js/illustrations.js`. The duplicated code has been removed from `main.js`, as it is correctly sourced from `illustrations.js`. This cleanup reduces the size of `main.js` by over 450 lines, eliminates potential bugs from mismatched definitions, and improves maintainability.

### 2. Robust Action Precondition Checks

Several `can_perform_*` methods in the action handler files only checked if the primary effect of an action was possible, ignoring that many actions have a fallback effect (e.g., strengthening a line) that would still constitute a valid move. This could lead to the action selection logic incorrectly discarding perfectly valid moves.

The following precondition checks have been updated to account for both primary and fallback effects, making the AI's action selection more accurate and the game simulation more robust:

-   **`expand_actions.py`**:
    -   `can_perform_add_line`: Now considers both adding a new line and strengthening an existing one.
    -   `can_perform_extend_line`: Now correctly allows the action if any line exists (to be extended or strengthened).
    -   `can_perform_fracture_line`: Now correctly allows the action if any line exists (to be fractured or strengthened).
    -   `can_perform_spawn_point`: Now checks if a point can be spawned *or* if a line can be strengthened.
    -   `can_perform_create_orbital`: Now correctly checks for the primary condition (>=5 points) or the fallback condition (>=1 point and >=1 line).
-   **`fortify_actions.py`**:
    -   `can_perform_claim_territory`: Now allows the action if new territory can be claimed *or* if existing territory can be reinforced.
    -   `can_perform_form_bastion`: Now allows the action if a bastion can be formed *or* if a fortified point can be reinforced.
    -   `can_perform_reposition_point`: Now allows the action if a point can be moved *or* if a line can be strengthened.

These changes reduce the likelihood of the game engine needing to retry action selections and ensure that a team can always utilize its full range of possible moves.