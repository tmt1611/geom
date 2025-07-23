This iteration focuses on two main areas: continuing the visual enhancement of the Action Guide by adding new illustrations, and cleaning up the Python codebase by refactoring more game logic out of the main `game_logic.py` file into specialized handlers.

### 1. New Illustrations for Action Guide

To make the Action Guide more comprehensive and visually intuitive, illustrations for two more actions have been created:

-   **`fight_chain_lightning`**: The new illustration depicts a friendly team's "I-Rune" (a straight line of three points) sacrificing its central point to launch a bolt of lightning that strikes and destroys a nearby enemy point. This clearly communicates the action's cost and effect.
-   **`rune_shield_pulse`**: This illustration shows a friendly "Shield-Rune" (a triangle with a point inside) emitting a circular shockwave that pushes enemy points away, demonstrating its defensive, area-denial capability.

These additions help users better understand the game's mechanics without needing to read lengthy descriptions.

### 2. Code Refactoring and Cleanup

The main `game_logic.py` file was becoming overly long, containing implementations for many different types of actions. To improve code organization and adhere to the single-responsibility principle, the following refactoring was performed:

-   **`FightActionsHandler` Integration**: The `game_logic.py` file was updated to properly use the existing `FightActionsHandler` class from `game_app/actions/fight_actions.py`.
-   **Method Migration**: The logic for four major "Fight" actions (`attack_line`, `convert_point`, `pincer_attack`, and `territory_strike`) was removed from `game_logic.py`. The `Game` class now calls the corresponding methods on the `fight_handler` instance, significantly shortening and simplifying the main game class.
-   **Code De-duplication**: A helper method, `_get_vulnerable_enemy_points`, was duplicated in both `game_logic.py` and `fight_actions.py`. The duplicate was removed from the handler, which now calls the single, authoritative version in the main `Game` class, reducing redundancy and centralizing the logic.

These changes make the codebase cleaner, more modular, and easier to maintain and expand upon in the future.