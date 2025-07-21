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

The simulation runs on a simple set of rules. On its turn, a team will randomly perform one of the following actions:
- **Add Line:** Connect two of its own points with a new line.
- **Extend Line:** Extend an existing line to the border of the grid, creating a new point.
- **Attack Line:** Extend an existing line. If it hits an enemy team's line, the enemy line is destroyed.
- **Fortify Territory:** If three points and their connecting lines form a triangle, the team can claim that triangle as its territory, shading the area in its color.

## Development

The server runs in debug mode by default (see `run.py`). This means it will automatically reload when you save changes to a Python file. For changes in frontend files (JavaScript, CSS), the application will detect the changes and prompt you to restart the server and refresh your browser to see the updates.