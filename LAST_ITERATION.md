This iteration focuses on improving action robustness by ensuring a key sacrificial action is "never useless", fulfilling a core design goal.

### 1. "Never Useless" Whirlpool Action

The `[SACRIFICE] Create Whirlpool` action has been redesigned to provide a useful fallback effect, ensuring it always has an impact on the game state.

-   **Previous Behavior**: The action would sacrifice a point to create a whirlpool, but the effect was wasted if no other points were nearby to be pulled in.
-   **New Behavior**: The action now checks for nearby targets *before* execution.
    -   If points are within range, it creates the whirlpool as normal.
    -   If no points are in range, the action "fizzles" and instead creates a small, temporary **fissure** on the map at the sacrificed point's location.
-   **Impact**: This change makes the `Create Whirlpool` action a more reliable and strategic choice. It's now either a targeted crowd-control ability or a small area-denial tool, guaranteeing value for the sacrificed point.

### 2. Documentation and UI Updates

-   The `rules.md` file has been updated to reflect the new fallback mechanic for the Whirlpool action.
-   A visual effect has been added to the frontend to show the fissure being created when the whirlpool fizzles, providing clear visual feedback to the user.

### 3. Code Refactoring

-   The logic for selecting a non-critical point for sacrifice, which was slightly different across several actions, has been standardized and improved for actions like `sacrifice_nova_burst` and `sacrifice_action_create_whirlpool`.