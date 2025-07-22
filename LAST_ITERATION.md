This iteration focuses on a major strategic overhaul of the AI's action selection system to be more transparent, strategic, and aligned with team traits.

### 1. New Action Selection System (Group-Based Probabilities)
- **Previous System:** The old system assigned a weight to every individual action, which was then modified by a team's trait. This made it difficult to balance and understand a team's overall strategy.
- **New System:** Actions are now categorized into five distinct strategic groups: `Expand`, `Fight`, `Fortify`, `Sacrifice`, and `Rune`.
- **Trait-Driven Strategy:** Team traits (`Aggressive`, `Defensive`, etc.) now apply powerful multipliers to these *groups* instead of individual actions. For example, an 'Aggressive' team will have a much higher probability of choosing the 'Fight' group.
- **Fairness within Groups:** Once a strategic group is chosen, the system picks one of the *valid* actions from that group with equal probability. This ensures that all available tactical options within a chosen strategy are considered fairly.
- **Benefit:** This change makes team behavior more predictable and strategically coherent. An 'Expansive' team will clearly prioritize expansion, and its specific choice of *how* to expand is situational. This also makes balancing easier, as tweaks can be made at the group level.

### 2. UI Overhaul for Action Preview
- The "Action Preview" panel on the frontend has been completely redesigned to reflect the new system.
- It now clearly displays each action group, the total probability of the AI choosing that group, and then lists the available actions within it, each with its final calculated probability.
- This makes the AI's decision-making process transparent to the player, enhancing the strategic and analytical aspects of the game.

### 3. Code Refactoring and Cleanup
- **`game_logic.py`:** The core `_choose_action_for_team` and `get_action_probabilities` functions were rewritten to implement the new group-based logic. Old, complex data structures for per-action weights (`ACTION_BASE_WEIGHTS`, `TRAIT_MULTIPLIERS`) were removed and replaced with simpler, more powerful group-based structures.
- **`static/js/main.js`:** The `updateActionPreview` function was refactored to parse and display the new grouped data structure from the API. The redundant `getActionCategory` helper function was removed.