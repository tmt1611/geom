# Geometric Divination Game

This is a web-based auto-battle sandbox and divination tool based on geometric interactions.

## Description

As per the design, this is a minimal viable product (MVP) of a game where users can define teams, place points on a grid, and watch them interact based on a set of geometric rules. The game proceeds in turns, with each team performing a random action. The final state of the grid can be interpreted for fun or for "divination".

## Prerequisites

- Python 3.x
- pip (Python package installer)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  **Start the server:**
    ```bash
    python run.py
    ```
    This will start the Flask development server.

2.  **Access the application:**
    Open your web browser and navigate to `http://127.0.0.1:8888`.

## How to Play

1.  **Setup Phase (Left Panel):**
    - **Add Teams:** Enter a team name, pick a color, and click "Add Team".
    - **Select a Team:** Click on a team in the list. The selected team will be highlighted.
    - **Place Points:** Click on the grid to place starting points for the selected team.
2.  **Action Phase (Left Panel):**
    - **Start Game:** Set the maximum number of turns and click "Start Game" to begin the simulation.
    - **Control Flow:** Use "Play Next Turn" for step-by-step advancement or "Auto-Play" to run the simulation automatically.
    - **Game Log:** Follow the events of the game in the log on the right. Actions are color-coded by team.
3.  **Interpretation Phase (Right Panel):**
    - Once the game stops (either by reaching max turns or another condition), observe the final geometric patterns.
    - The "Final Analysis" table will appear, providing detailed statistics for each team (e.g., area controlled, triangles formed) to aid in your "divination" or analysis.
    - **Reset Game:** Click "Reset Game" to start over from the beginning.

## Game Actions

The simulation runs on a complex set of rules. On its turn, a team will perform one of many possible actions, influenced by its Trait. Actions are broadly categorized into:
- **Expand:** Creating new points and lines (e.g., `Add Line`, `Extend Line`, `Create Orbital`).
- **Fight:** Directly attacking and disrupting enemy assets (e.g., `Attack Line`, `Pincer Attack`, `Sentry Zap`).
- **Fortify/Defend:** Building defensive structures and claiming territory (e.g., `Fortify Territory`, `Form Bastion`, `Shield Line`).
- **Sacrifice:** Destroying a team's own asset for a powerful, often area-of-effect, ability (e.g., `Nova Burst`, `Create Whirlpool`).
- **Rune:** Special powerful actions unlocked by specific geometric formations (e.g., `Shoot Bisector`).

For a full, detailed list of actions and structures, please see `rules.md`.

## Deployment

This application supports two deployment modes:

1.  **Server Mode:** The standard way to run a Flask application, with a Python backend. This is the default when running locally.
2.  **Static Mode (GitHub Pages):** The application can be deployed as a static site. In this mode, the Python game logic is executed directly in the browser using [Pyodide](https://pyodide.org/) (WebAssembly).

### Deploying to GitHub Pages

No build step is required. The application is configured to run directly from the repository.

1.  Push all the files (`run.py`, `game_app/`, `static/`, etc.) to your GitHub repository.
2.  In your repository's settings, go to the "Pages" section.
3.  Choose to deploy from a branch, select your main branch, and set the folder to `/ (root)`.
4.  Save the settings. GitHub will build and deploy your site. It may take a few minutes.

When accessed via the `github.io` URL, the application will automatically detect it's in static mode and load the Pyodide engine to run the game.

## Development

The server runs in debug mode by default (see `run.py`). This means it will automatically reload when you save changes to a Python file. For changes in frontend files (JavaScript, CSS), the application will detect the changes and prompt you to restart the server and refresh your browser to see the updates.

When running locally, the application uses the Flask backend. To test the Pyodide version locally, you can serve the project root directory with any simple static file server (e.g., `python -m http.server`). Note that you would need to adjust the logic in `static/js/main.js` that detects GitHub Pages if you want to test Pyodide locally without using the `github.io` domain.