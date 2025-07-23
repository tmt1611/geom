This iteration focused on significantly improving the layout and content of the "Action Guide" tab.

### 1. Compact Grid Layout
The Action Guide has been refactored from a single-column list into a responsive, multi-column grid. This makes the layout much more compact, allowing users to see many more actions at a glance without excessive scrolling. Key changes include:
- The `action-guide-grid` now uses `grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))` for a flexible card layout.
- Individual action cards (`.action-card`) now stack their content vertically (illustration on top, text below) to fit the new grid format.
- The illustration canvas within each card is now responsive, scaling to fit the card's width while maintaining a 3:2 aspect ratio.
- A subtle hover effect was added to the cards to improve interactivity.

### 2. New Illustrations
To continue filling out the visual guide, new illustrations have been developed for two previously un-illustrated actions:
- **Fortify: Form Rift Spire:** The artwork shows three friendly territories converging on a single point, which is then sacrificed to create the powerful Rift Spire structure.
- **Rune: Starlight Cascade:** This illustration depicts a Star-Rune formation sacrificing one of its outer points to unleash a damaging area-of-effect blast on nearby enemy lines.