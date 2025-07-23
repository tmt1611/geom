This iteration focuses on two key areas of code cleaning: reducing duplication and optimizing a frequently used function.

1.  **Code Duplication:** The `game_logic.py` file had identical blocks of code in both `run_next_action` and `get_action_probabilities` responsible for updating game structures like runes and prisms. I've consolidated this logic into a single new helper method, `_update_structures_for_team`, making the code cleaner and easier to maintain.

2.  **Performance Optimization:** The `launch_payload` action in `fight_actions.py` was performing redundant calculations. It would fetch lists of fortified and bastion points to find high-value targets, and if none were found, it would call `_get_vulnerable_enemy_points`, which would *re-fetch* the same lists internally. To fix this, I've modified `_get_vulnerable_enemy_points` to optionally accept a pre-calculated set of immune point IDs. The `launch_payload` action now calculates this set once and reuses it for both target-finding steps, eliminating the redundant work.

These changes improve code quality and slightly enhance performance without altering any game mechanics.