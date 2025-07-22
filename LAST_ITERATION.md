This iteration focuses on enhancing the "Action Guide" tab, a key feature for user understanding of the game's mechanics. I've introduced powerful filtering and search capabilities, and added several new illustrations for complex actions, making the guide a more useful and interactive tool.

### 1. Action Guide Filtering and Search
To help users navigate the growing list of actions, the "Action Guide" tab now includes filter controls.

- **UI Implementation (`index.html` & `static/css/style.css`):**
    - A search bar and a set of group toggle buttons (`Expand`, `Fight`, `Fortify`, etc.) have been added to the top of the Action Guide.
    - The buttons allow users to show actions from a specific category or view all actions at once.
    - The search bar allows users to filter actions by name or by keywords in their descriptions.
    - CSS styles were added to make these controls responsive and visually consistent with the application's theme.

- **Frontend Logic (`static/js/main.js`):**
    - The `initActionGuide` function was refactored to support the new controls.
    - It now dynamically generates the group filter buttons based on the action groups defined in the game logic.
    - Event listeners are attached to the search input and the group buttons. A `filterActions` function handles the logic of showing or hiding action cards based on the currently active filters, providing an immediate and responsive user experience.

### 2. New Action Illustrations
The visual dictionary of actions continues to expand with five new illustrations for key strategic actions.

- **`static/js/main.js`**:
    - The `illustrationDrawers` object now includes drawing functions for:
        - `fight_sentry_zap`: Depicts a collinear I-Rune firing a perpendicular beam at an enemy point.
        - `fight_territory_strike`: Shows a bolt of energy emerging from the center of a claimed territory to strike a foe.
        - `fortify_form_monolith`: Illustrates the formation of the tall, thin rectangular Monolith structure.
        - `fortify_mirror`: Clearly shows a point being reflected across an axis line to create a new, symmetrical point.
        - `rune_t_hammer_slam`: Visualizes a T-Rune formation and the perpendicular shockwave pushing enemy points away.

### 3. Code Cleanup
- **`static/js/main.js`**: As part of the update, the entire `illustrationDrawers` object was sorted alphabetically by action name. This improves code organization and makes it easier for developers to find and add new illustrations in the future.

These improvements make the Action Guide a significantly more powerful tool for both new and experienced players, directly addressing the goal of making the game's complex geometric rules more accessible and understandable.