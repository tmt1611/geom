This iteration introduces a major new feature: an "Action Guide" tab that provides visual and textual explanations for all game actions. It also includes backend data structuring to support this feature.

### 1. New Feature: Action Guide Tab
A new "Action Guide" tab has been added to the application, allowing users to browse and understand all available actions without leaving the game.

- **UI Implementation (`index.html`, `style.css`):**
    - The main layout has been refactored to include a tabbed navigation system ("Game" and "Action Guide").
    - The Action Guide tab contains a responsive grid of "action cards". Each card is designed to clearly present information.

- **Backend Support (`game_logic.py`, `routes.py`):**
    - A new `ACTION_VERBOSE_DESCRIPTIONS` dictionary has been added to `game_logic.py`, containing detailed explanations for every game action, derived from `rules.md`.
    - A new API endpoint, `/api/actions/all`, was created to serve all action names, groups, and their verbose descriptions to the frontend.

- **Frontend Logic (`api.js`, `main.js`):**
    - The JavaScript API wrapper (`api.js`) has been updated to fetch data from the new endpoint, with a corresponding implementation for Pyodide/static mode.
    - The "Action Guide" tab is dynamically populated with action cards upon page load.
    - Each action card features a unique, dynamically-drawn canvas illustration that visually represents the action (e.g., drawing lines, explosions, shields). This provides an at-a-glance understanding of the action's purpose.

This new feature significantly enhances the user experience by making the game's complex mechanics more accessible and understandable directly within the application.