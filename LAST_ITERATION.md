This iteration focuses on small but meaningful performance optimizations within the action handlers. I identified several places where expensive calculations (specifically, finding all bastion line IDs) were being performed inside loops.

1.  **Optimized `attack_line`:** In `fight_actions.py`, the `_get_bastion_line_ids()` call was inside the `_find_closest_attack_hit` helper, which itself was called inside a loop in `attack_line`. I hoisted this call out of the loops into the main `attack_line` method and passed the result down as an argument. This reduces redundant computations significantly.

2.  **Optimized `chain_lightning`:** In the fallback "Mini-Nova" effect for `chain_lightning` in `fight_actions.py`, the `_get_bastion_line_ids()` call was inside a loop iterating over enemy lines. I moved this call to before the loop.

3.  **Optimized `cardinal_pulse`:** In `rune_actions.py`, the `_get_bastion_line_ids()` call was inside a loop that fires the four beams of the pulse. Since the set of bastion lines doesn't change during this action, I hoisted the call to before the loop.

These changes reduce the computational load of several fight actions, especially in late-game scenarios with many lines and structures on the board, without altering the game logic.

### Changes
*   **`game_app/actions/fight_actions.py`:**
    *   Modified `_find_closest_attack_hit` to accept `bastion_line_ids` as an argument instead of calculating it internally.
    *   Updated `attack_line` to calculate `bastion_line_ids` once and pass it to `_find_closest_attack_hit`.
    *   In `chain_lightning`, moved the `_get_bastion_line_ids()` call outside the `for line in enemy_lines` loop.
*   **`game_app/actions/rune_actions.py`:**
    *   In `cardinal_pulse`, moved the `_get_bastion_line_ids()` call outside the `for arm_pid in rune['arm_ids']` loop.