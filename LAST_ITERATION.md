This iteration focused on a major redesign of the "Action Guide" tab to improve its layout, readability, and visual presentation, correctly implementing the vertical card design that was planned previously.

### Action Guide Redesign

1.  **Vertical Action Cards**: The layout for each action card has been changed from a horizontal format (illustration on the left, text on the right) to a vertical one. The illustration is now displayed prominently at the top with a wider aspect ratio, and the text content (name, group, description) is neatly organized below.
2.  **Responsive and Compact Grid**: The CSS grid for the action guide has been adjusted to use a smaller minimum card width (`300px` from `350px`), allowing for a more compact and responsive layout that fits more cards on screen without feeling cluttered.
3.  **Improved Readability**: By removing the fixed height on the action cards, descriptions of any length can now be displayed fully without requiring an internal scrollbar, which significantly improves readability and user experience.
4.  **Code Adjustments**: The relevant CSS and JavaScript were modified to support this new vertical layout, including changing flex-direction, removing fixed heights, and adjusting canvas dimensions for the illustrations.