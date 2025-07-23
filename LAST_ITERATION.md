This iteration focuses on improving the UI/UX of the "Action Guide" tab to make it more compact, readable, and efficient.

### UI Improvement: Action Guide Redesign

1.  **Compact List Layout**: The Action Guide has been redesigned from a space-intensive grid of cards into a more compact and scannable vertical list. Each action is now a single row, with its illustration on the left and the corresponding description on the right. This layout is more efficient, especially on wider screens, allowing users to see more actions at once without scrolling.

2.  **Optimized Illustrations**: To complement the new list layout, the canvas size for action illustrations has been reduced from `240x150` to `200x120`. This change makes each row shorter, contributing to the overall compactness, while still providing a clear visual representation of the action.

3.  **Refined Styling**: The CSS for the action cards has been updated to support the new `flex-direction: row` layout. This includes changing border separators from bottom to right, adjusting text padding and font sizes for better readability, and simplifying the hover effect to be more suitable for a list view.

These changes result in a cleaner, more organized Action Guide that is easier for users to navigate and understand.