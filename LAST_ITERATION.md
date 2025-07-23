This iteration focuses on improving the user interface and experience of the **Action Guide** tab, making it significantly more compact and easier to browse, while also adding a new illustration to expand its visual coverage of game mechanics.

### 1. Action Guide Layout Redesigned to a Grid

To address the suggestion of making the Action Guide more compact and less cluttered, the layout was changed from a single-column list to a responsive grid.

-   **CSS Grid Implementation**: The action guide now uses a CSS grid (`display: grid`) that automatically arranges action cards into columns based on available screen space (`grid-template-columns: repeat(auto-fill, minmax(350px, 1fr))`). This allows users to see many more actions at a glance without excessive scrolling.
-   **Vertical Card Layout**: To better fit the new grid structure, individual action cards have been redesigned to a vertical format (`flex-direction: column`). The illustration canvas is now positioned above the text description, creating a more traditional and space-efficient card format.
-   **Responsive Illustrations**: The illustration canvases are now fully responsive (`width: 100%`, `aspect-ratio: 3 / 2`), scaling to fit the card width while maintaining a consistent aspect ratio. This ensures the guide looks good on various screen sizes.

### 2. New Illustration for "Purify Territory"

To continue expanding the visual documentation of the game's actions, a new illustration has been created.

-   **`fight_purify_territory` Illustration**: A new drawing was added for the "Purify Territory" action. It visually depicts a friendly team's pentagonal "Purifier" structure emitting a wave of energy that neutralizes a nearby enemy's claimed territory (a triangle), clarifying this high-level strategic action.

These changes result in a more user-friendly, information-dense, and visually appealing Action Guide.