This iteration focused on improving the user interface for team management and introducing a new strategic, map-altering gameplay mechanic.

### UI/UX Improvement: Smoother Team Editing

-   **Files**: `static/js/main.js`, `static/css/style.css`
-   **Change**: The team management UI during the setup phase has been completely overhauled. Previously, clicking "edit" would replace the team display with a somewhat disruptive block of input fields.
-   **New Behavior**: The new implementation provides a much smoother inline editing experience. When a user clicks the edit icon:
    -   The team name and trait become editable fields directly within the list item.
    -   The color picker is seamlessly integrated.
    -   Save and Cancel icons replace the standard action buttons.
-   **Benefit**: This makes the process of creating and modifying teams more intuitive and visually appealing, reducing layout shifts and improving the overall user workflow during setup.

### New Feature: Rift Spires & Fissures

A new "Terraforming" strategic layer has been added to the game, allowing teams to directly manipulate the battlefield.

-   **Files**: `game_logic.py`, `static/js/main.js`, `rules.md`
-   **New Structure: Rift Spire**
    -   **Formation:** A team can sacrifice a highly valuable point—one that serves as a vertex for at least three of its claimed territories—to create a **Rift Spire**.
    -   **Function:** The Spire is a permanent structure that passively charges over several turns.
-   **New Action: Create Fissure**
    -   **Mechanic:** Once fully charged, a Rift Spire can execute the `Create Fissure` action. This creates a long, jagged crack across the battlefield that lasts for a set number of turns.
    -   **Strategic Impact:** Fissures are impassable barriers. They block line-of-sight for attacks, prevent line extensions, and no new points can be created near them. This introduces a powerful map control element, allowing a team to create defensive walls, block off enemy expansion, or isolate parts of the grid.
-   **Visuals**:
    -   Rift Spires are rendered with a unique, spiky, pulsing visual that includes a charge indicator.
    -   Fissures are drawn as thick, jagged, decaying cracks on the grid, providing clear and immediate visual feedback about the altered terrain.
-   **System Integration**: The core game logic (`_is_spawn_location_valid`, `fight_action_attack_line`, etc.) has been updated to respect the blocking nature of these new fissures.