This iteration focuses on improving the user interface and experience for the "Action Guide" tab, specifically by cleaning up the visual presentation of action illustrations and making the layout more compact.

### UI/UX Improvements: Action Guide

1.  **Cleaner & Consistent Illustrations**: Many action illustrations used a text emoji ('💥') to represent impacts or explosions, which looked inconsistent.
    *   I replaced all instances of the explosion emoji across all relevant action illustrators in `static/js/main.js` with calls to the existing `drawExplosion` helper function. This results in a cleaner, more visually cohesive, and professional-looking guide.
    *   To better communicate the relative power of different actions, I adjusted the size of the explosion graphic. For example, the `rune_focus_beam` action now shows a larger explosion than a standard `fight_attack`, providing a subtle visual cue about its higher impact.

2.  **More Compact Layout**: To reduce scrolling and make the guide easier to browse, I adjusted the card sizes to fit more content on the screen.
    *   In `static/css/style.css`, I reduced the minimum width for each action card in the grid from 300px to 280px.
    *   I also reduced the height of the illustration canvas on each card from 180px to 160px.
    *   In `static/js/main.js`, I updated the canvas dimensions passed to the illustration drawing functions to match these new, smaller sizes. This allows the responsive grid to display more cards per row on wider screens.