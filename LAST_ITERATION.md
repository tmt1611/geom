### Action System Redesign (Part 5): Expanding "Never Useless" Actions

This iteration continues the enhancement of the action system by adding fallback effects to several more actions, ensuring they are almost always useful and reducing wasted turns. This adds more dynamic and unexpected outcomes to the simulation.

-   **Files Modified**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`

-   **Core Changes**:
    -   **`rune_action_impale`**:
        -   **Primary Effect**: A Trident Rune fires a beam that pierces and destroys all enemy lines in its path.
        -   **Fallback Effect**: If the beam hits no targets, it now creates a temporary **Barricade** along its path, turning a missed attack into a useful area denial tool.

    -   **`fight_action_launch_payload`**:
        -   **Primary Effect**: A Trebuchet fires a payload to destroy a high-value enemy point (fortified, bastion core, etc.).
        -   **Fallback 1**: If no high-value targets are available, it now targets any standard vulnerable enemy point.
        -   **Fallback 2**: If there are no enemy points at all, the payload now impacts a random spot on the battlefield, creating a small, temporary **Fissure**.

    -   **`fight_action_refraction_beam`**:
        -   **Primary Effect**: A Prism structure is used to refract a beam and destroy an enemy line.
        -   **Fallback Effect**: If the refracted beam does not hit any enemy lines, it now travels to the edge of the grid and creates a new friendly point, similar to other missed beam attacks.

-   **Frontend & Documentation**:
    -   Added new visual effects in `static/js/main.js` to communicate the new fallback behaviors (e.g., an arcing payload that creates a fissure).
    -   Updated the action descriptions in `rules.md` to reflect the new tiered outcomes for these actions.
    -   Added corresponding log messages in `game_logic.py` for each new fallback.