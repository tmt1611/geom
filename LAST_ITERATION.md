This iteration focuses on improving the "Action Guide" tab by making the layout more compact and refining the illustrations. The action cards are now arranged in a vertical layout (illustration on top of text) which allows for more cards to be visible on screen at once. Additionally, the illustrations themselves have been upscaled and their drawing parameters adjusted to look sharper and better proportioned in the new layout.

### Action Guide Layout Improvements

1.  **Vertical Card Layout**: The CSS for `.action-card` was changed from `flex-direction: row` to `flex-direction: column`. This stacks the illustration canvas on top of the descriptive text, creating a taller, narrower card.

2.  **Compact Grid**: The CSS for `.action-guide-grid` was updated to use a smaller minimum width for cards (`minmax(280px, 1fr)` instead of `340px`), allowing more cards to fit horizontally in the available space.

3.  **Enhanced Illustrations**:
    *   The resolution of the illustration canvas elements was increased from `120x100` to `240x150` in `main.js`. This provides a larger drawing surface, resulting in less pixelated and clearer images when scaled by CSS.
    *   All hardcoded pixel values (e.g., line widths, font sizes, radii) within the JavaScript illustration drawing functions were manually scaled up to match the new, higher-resolution canvas, ensuring all visual elements remain proportional and aesthetically pleasing.

These changes collectively result in a cleaner, more organized, and visually appealing Action Guide that better utilizes screen real estate.