This iteration refactored two complex actions, `nova_burst` and `mirror_structure`, to improve the accuracy of their precondition checks and clean up the action logic itself. This follows the principle of separating the logic for *finding* a valid action from the logic for *executing* it.

**Key Changes:**

1.  **Refactored `sacrifice_actions.nova_burst`:**
    *   The precondition check (`can_perform_nova_burst`) was updated to be more precise. It now verifies if there is either an "ideal" sacrificial point (one that will destroy enemy lines) or a "non-critical" point available for the action's fallback effect.
    *   This removes the looser check of just counting team points and makes the AI's decision-making and the UI's Action Preview more accurate.
    *   The `nova_burst` method was simplified to use this more robust check, reducing redundant logic.

2.  **Refactored `fortify_actions.mirror_structure`:**
    *   A new private helper, `_find_a_valid_mirror`, was created to encapsulate the complex, randomized logic for finding a valid reflection operation.
    *   The `can_perform_mirror_structure` precondition now uses this helper, making it significantly more accurate than the previous simple point count check.
    *   The `mirror_structure` action method was refactored to call the new helper. This cleans up the main method by separating the "finding" logic from the "execution" and "fallback" logic, improving readability and maintainability.

These changes make the codebase cleaner and the simulation more robust by ensuring actions are only considered possible when they genuinely have a valid target or operation to perform.