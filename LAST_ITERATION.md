This iteration focuses on two key areas: refactoring the backend code for cleanliness and improving the UI of the "Action Guide" for better usability and compactness.

### 1. Code Cleanup: Removing Dead Code
A previous refactoring had moved all "Rune" action logic from the main `game_logic.py` file into a dedicated `RuneActionsHandler`. However, the original methods were left behind in `game_logic.py`, creating a significant amount of dead, unreachable code. This has now been removed, making the `Game` class smaller and easier to navigate, and ensuring that all action logic resides solely within its designated handler.

### 2. UI Improvement: Redesigning the Action Guide
The Action Guide tab has been redesigned to be more compact and visually scannable, addressing the user's request to avoid clutter and improve presentation.

- **New Layout**: The action cards now use a horizontal, two-column layout. The illustration appears on the left, and the title, category, and description are on the right.
- **Improved Compactness**: This new layout makes each card shorter, allowing more actions to be visible on the screen simultaneously, which reduces the need for vertical scrolling.
- **Canvas Resizing**: The illustration canvases have been resized to fit the new card dimensions (150x120px), and the drawing functions have been updated accordingly.

These changes result in a cleaner codebase and a more user-friendly interface for browsing the game's complex actions.