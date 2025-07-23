This iteration focuses on improving the user interface and experience of the **Action Guide** tab. The layout has been redesigned to be more compact and visually appealing, and a new illustration has been added to further clarify game mechanics.

### 1. Action Guide Layout Redesign

To address the suggestion of making the Action Guide more compact and less cluttered, the layout was changed from a single-column list to a responsive grid.

-   **CSS Grid Layout**: The action guide now uses a CSS grid that automatically arranges action cards into columns based on available screen space. This allows users to see many more actions at a glance.
-   **Vertical Card Layout**: The individual action cards have been redesigned. The illustration canvas is now positioned above the text description, creating a more traditional and space-efficient card format that fits well within the new grid system.
-   **Responsive Illustrations**: The illustration canvases are now responsive, scaling to fit the card width while maintaining a consistent 3:2 aspect ratio.

### 2. New Illustration & Code Cleanup

To enhance the visual guide, a new illustration has been created and the associated drawing code has been cleaned up.

-   **`fight_chain_lightning` Illustration**: A new illustration was added for the "Chain Lightning" action. It visually depicts an I-Rune sacrificing its central point to unleash a lightning strike on an enemy point.
-   **Code De-duplication**: A `drawJaggedLine` helper function was added to the central `illustrationHelpers` object to be reused across multiple illustrations (like lightning and fissures), reducing code duplication.

These changes result in a more user-friendly and informative Action Guide.