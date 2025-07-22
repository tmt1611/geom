This iteration focuses on improving the action system, enhancing visual feedback, and synchronizing documentation with game mechanics.

### 1. "Never Useless" Action Enhancements
Several actions were redesigned to include fallback effects, ensuring they are always useful and making the simulation more dynamic and less prone to "wasted" turns.

-   **`Shield Line`**: If all friendly lines are already shielded, this action now **overcharges** a random existing shield, increasing its duration.
-   **`Grow Line`**: If it fails to find a valid spot to grow a new "vine", it now reinforces the line it was attempting to grow from.
-   **`Create Orbital`**: If a valid orbital structure cannot be formed, the action now reinforces all lines connected to the chosen center point, strengthening a core area.
-   **`Focus Beam` (Star-Rune)**: If no enemy targets are available, the beam now fires at the heart of the largest enemy cluster, creating a small, temporary **fissure** to disrupt their territory.

### 2. I-Rune Integration and Visualization
The `I-Rune` (a straight line of 3+ points) was not fully implemented. This has been corrected:
-   A robust method for detecting `I-Rune` formations (`_check_i_rune`) has been implemented.
-   The frontend now visually distinguishes the parts of an `I-Rune`, rendering the internal points as "eyes" and endpoints as "posts", which provides clearer visual cues for the `Sentry Zap` and `Chain Lightning` actions.

### 3. Documentation and Rule Clarity
-   The `rules.md` file was significantly updated to match the new action fallbacks.
-   The **Star-Rune** and its associated actions (`Starlight Cascade`, `Focus Beam`) were formally documented, clarifying their mechanics and role in the game, including their function as a prerequisite for the Chronos Spire wonder.

### 4. Code Health and Bug Fixes
-   Fixed a bug where the application would crash when trying to calculate action probabilities due to calls to non-existent methods (`_update_sentries_for_team`, `_update_conduits_for_team`).
-   Corrected a visual rendering bug where a point with multiple special properties (e.g., being a bastion core and also fortified) would not display its most important form. A priority system for rendering point styles was implemented.
-   Cleaned up visual effect triggers in the Javascript to use correct data keys from the backend.