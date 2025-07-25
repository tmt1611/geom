This iteration focuses on adding a new, geometry-rich action to the Expand group, as suggested by the design principles in `design.md`.

1.  **New Action: `Mirror Point`**
    *   Designed and implemented a new `Expand` action called `expand_mirror_point`.
    *   **Mechanic:** This action reflects a friendly point through another friendly point to create a new point symmetrically, e.g., given points A and B, it creates a new point C such that B is the midpoint of AC. This provides a clean, predictable way to generate points based on existing geometry.
    *   **Fallback Logic:** To ensure the action is robust, it includes layered fallbacks. If no valid location for a mirrored point can be found, it first attempts to strengthen the line between the two points it was trying to use. If that also fails, it falls back to strengthening a random friendly line, ensuring the action is never wasted.

2.  **Implementation Details**
    *   Added the new action's metadata to `game_app/action_data.py`.
    *   Implemented the core logic and precondition check in `game_app/actions/expand_actions.py`.
    *   The new action correctly integrates with other game systems, such as checking for the Ley Line bonus upon point creation.

3.  **Documentation**
    *   Updated `rules.md` to include a description of the new "Mirror Point" action for players.