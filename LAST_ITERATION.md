This iteration focuses on improving the UI layout consistency and readability, particularly during the setup and game phases.

### 1. Consistent Grid Layout and Sizing
The main layout grid is now consistent across all game phases (Setup, Running, Finished). Previously, different grid column definitions were used, causing the game grid canvas to be too large and overflow the screen during the setup phase. By unifying the CSS grid definition and simply toggling the visibility of setup vs. game panels, the grid now maintains a correct and stable size from the start. Obsolete and conflicting CSS rules for the running phase have been cleaned up.

### 2. Compact Action Preview Panel
The "Action Preview" panel, which displays a team's possible moves, has been made more vertically compact. The font size for action names, spacing between items, and the height of probability bars have all been reduced. This ensures that even for teams with many available actions, the entire list is visible without needing to scroll, providing a better at-a-glance overview.

### Other Items Checked
- The request to move "Place Points" and "Game Settings" to a right-hand column during setup was confirmed to be already implemented from a previous iteration.
- The request to move the end-game statistics into the now-empty "Action Preview" column upon game completion was also confirmed as already implemented.

These changes contribute to a cleaner and more user-friendly interface.