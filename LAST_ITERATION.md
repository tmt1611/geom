This iteration introduces a significant new strategic layer: **Wonders**. These are unique, powerful, late-game structures that provide an alternative path to victory, rewarding teams that invest in creating complex geometric formations. The first Wonder, the **Chronos Spire**, has been implemented.

### New Feature: The Chronos Spire (Wonder)

-   **Files**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`
-   **Change**: A new `fortify_action_build_chronos_spire` action has been added. Teams can now build this Wonder by creating a complex "star" formation (a 5 or 6-point cycle with a connected center point) and then sacrificing all points in the formation.
-   **Effect**: The Chronos Spire is an indestructible structure that provides its owner with two major benefits:
    1.  A **bonus action** every turn, which stacks with any existing Nexuses.
    2.  An **alternative victory condition**: If the Spire survives for 10 turns, its owner automatically wins the game.
-   **Strategic Impact**: This introduces a "Wonder Victory" path, creating a tense race against time once a Spire is built. It encourages players and AI to pursue intricate geometric patterns as a viable alternative to military dominance.
-   **Visuals**: The Chronos Spire has a unique, impressive visual representation on the grid, including a pulsing energy core, rotating rings, and a clear turn countdown to its victory condition, making it a central feature of the battlefield.

### Code & System Improvements

-   **File**: `game_logic.py`
-   **Change**: A new helper function, `_find_star_formations`, was implemented to efficiently detect the complex geometry required for the Wonder.
-   **Benefit**: This adds a challenging but highly rewarding objective, directly addressing the design goal of making geometric shapes more valuable than just raw point count.
-   **File**: `game_logic.py`
-   **Change**: The game's turn lifecycle functions (`_start_new_turn`) were updated to seamlessly integrate the Spire's bonus actions and victory checks into the existing game flow.
-   **File**: `static/js/main.js`
-   **Change**: Added a new `drawWonders` function and visual effects for the creation and presence of the Chronos Spire, enhancing the visual feedback and "wow" factor of this new feature. The live stats panel was also updated to show active Wonders.