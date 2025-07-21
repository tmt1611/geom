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

1.  **Make the run script executable (on Linux/macOS):**
    ```bash
    chmod +x run.sh
    ```

2.  **Start the server:**
    ```bash
    ./run.sh
    ```
    On Windows, you can run the commands from `run.sh` directly:
    ```batch
    set FLASK_APP=app.py
    set FLASK_ENV=development
    flask run --port=8888
    ```

3.  **Access the application:**
    Open your web browser and navigate to `http://127.0.0.1:8888`.

## How to Play

1.  **Setup Phase:**
    - Add one or more teams using the "Controls" panel.
    - Select a team.
    - Click on the grid to place points for the selected team.
2.  **Action Phase:**
    - Click "Start Game" to begin the simulation.
    - Click "Play Next Turn" to advance the game by one step.
    - Click "Auto-Play" to have the game run automatically until the maximum number of turns is reached.
    - The "Game Log" will show the actions taken in each turn.
3.  **Interpretation Phase:**
    - Once the game stops, observe the final geometric patterns on the grid.
    - The "Interpretation" panel provides statistics like the number of points and lines for each team.

## Development

The server runs in debug mode, which means it will automatically reload when you save changes to a Python file. For changes in frontend files (JavaScript, CSS), the application will detect the changes and prompt you to restart the server and refresh your browser to see the updates.