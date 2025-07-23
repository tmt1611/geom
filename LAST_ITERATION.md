This iteration focused on refactoring and centralizing all action-related metadata. Previously, information about game actions (their group, description, implementation mapping, and log messages) was spread across `game_data.py` and `text_data.py`. This made adding or modifying actions cumbersome and error-prone.

To improve this, I've introduced a single source of truth for all action definitions.

**Key Changes:**

1.  **New `action_data.py` file:** A new file, `game_app/action_data.py`, has been created. It contains a single dictionary named `ACTIONS` that serves as a registry for every action in the game. Each entry contains all relevant metadata: its group, display name, detailed description, handler mapping, and associated log message generators.

2.  **Simplified `game_data.py`:** This file now dynamically builds the older data structures (like `ACTION_MAP`, `ACTION_GROUPS`, etc.) by importing and processing the `ACTIONS` dictionary from the new file. This maintains backward compatibility with the existing game logic, requiring no changes to `game_logic.py` or `routes.py`, while still benefiting from the centralized data source.

3.  **Removed `text_data.py`:** With all action descriptions and default team data consolidated into `action_data.py` and `game_data.py` respectively, `text_data.py` became redundant and has been deleted.

This refactoring significantly improves the codebase's organization and maintainability. It's now much cleaner and more straightforward to manage the game's action system, adhering to the DRY (Don't Repeat Yourself) principle.