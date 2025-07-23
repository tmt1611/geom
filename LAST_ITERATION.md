This iteration focuses on improving the layout and presentation of the "Action Guide" tab. The goal was to create a more compact and readable format for the action cards, addressing the suggestion to improve the layout and avoid clutter.

### Action Guide Layout Redesign

1.  **Horizontal Card Layout**: The action cards have been redesigned from a vertical layout (illustration on top) to a horizontal one (illustration on the side).
    *   The illustration canvas is now a fixed-size 150x150 square on the left, providing a consistent visual anchor for each card.
    *   The action's title, group tag, and detailed description are placed to the right of the illustration.
    *   This change makes each card shorter vertically, which allows more actions to be visible within the viewport simultaneously, making the guide feel more compact and easier to scan.

2.  **Adjusted Grid for Wider Cards**: To accommodate the new horizontal card format, the underlying CSS grid has been adjusted. The minimum width for each column is now larger, ensuring the new card layout has adequate space and remains responsive on various screen sizes.

3.  **Improved Typographic Alignment**: A small but impactful change was made to the alignment within each card's header. The vertical alignment has been set to `baseline`, which aligns the text of the action's title and its group tag along their bottom edge, resulting in a cleaner and more professional appearance.

These changes were implemented across `static/css/style.css` for the layout and `static/js/main.js` to update the canvas dimensions. Since all illustration functions use relative coordinates, they automatically adapted to the new square canvas without needing individual modifications.