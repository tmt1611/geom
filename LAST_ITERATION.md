This iteration continues the development of the "Action Guide" tab by adding more illustrations, making the game's mechanics more visually understandable. A minor code cleanup was also performed.

### 1. New Illustrations in Action Guide
The "Action Guide" tab, introduced in the previous iteration, has been enhanced with illustrations for several more key actions across different categories.

- **Frontend Logic (`static/js/main.js`):**
    - The `illustrationDrawers` object has been expanded with new drawing functions for the following actions:
        - `expand_grow`
        - `fight_pincer_attack`
        - `fortify_anchor`
        - `sacrifice_phase_shift`
        - `rune_area_shield`
    - Each new illustration provides a clear, at-a-glance visual representation of the action's effect, such as showing points being pulled towards an anchor or a line being teleported.
    - The existing illustration functions were also sorted alphabetically to improve code maintainability.

### 2. Code Cleanup
- **`static/js/main.js`**: A duplicated function definition for `'mirror_fizzle_strengthen'` within the `actionVisualsMap` object was identified and removed, preventing potential inconsistencies and cleaning up the codebase.

These changes further improve the user experience by making the game's ruleset more accessible, while also maintaining code quality.