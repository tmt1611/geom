This iteration focuses on improving the user interface of the "Action Guide" tab, making it more visually appealing, compact, and informative by adding new illustrations.

### 1. Action Guide Layout Redesign
The layout of the Action Guide has been significantly refactored for better readability and space efficiency.

- **File**: `static/css/style.css`
- **Changes**:
    - The grid now supports more compact cards (`minmax(300px, 1fr)`), allowing more actions to be visible on screen at once.
    - Action cards now use a vertical layout (`flex-direction: column`), placing the illustration on top of the description. This creates a cleaner, more modern card design.
    - The canvas for illustrations is now larger (`100%` width, `150px` height) to accommodate more detailed visuals.
    - Paddings, gaps, and text styles within the cards were adjusted to reduce clutter and improve the presentation of information.

- **File**: `static/js/main.js`
- **Changes**:
    - The JavaScript function that dynamically creates the action cards has been updated to generate the new HTML structure (placing the `<canvas>` outside the `.action-card-text` div).
    - The canvas resolution was increased to `300x150` to match the new aspect ratio and provide a sharper drawing surface for the illustrations.

### 2. New Action Illustrations
To make the guide more useful, several previously un-illustrated actions now have custom visuals.

- **File**: `static/js/main.js`
- **Changes**:
    - Added new drawing functions to the `illustrationDrawers` object for the following actions:
        - `rune_starlight_cascade`: Shows a Star Rune sacrificing a point to create a damaging area-of-effect blast.
        - `rune_focus_beam`: Depicts a Star Rune firing a concentrated beam at a high-value enemy structure.
        - `rune_cardinal_pulse`: Illustrates the consumption of a Plus Rune to fire four destructive beams in cardinal directions.
    - All illustration functions were updated to draw on the new, larger `300x150` canvas.

These changes result in a more professional and user-friendly Action Guide that better communicates the function of each game mechanic.