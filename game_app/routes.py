from flask import Blueprint, render_template, jsonify, request
from . import game_logic
from . import utils

# Using a Blueprint to organize routes.
# The first argument is the name of the blueprint.
# The second argument, __name__, helps Flask locate the blueprint's resources.
main_routes = Blueprint('main', __name__)

@main_routes.route('/')
def index():
    # The game is reset when a new game is started via the API,
    # so we don't need to reset it here anymore.
    # This allows refreshing the page without losing state, which can be useful.
    # A hard reset button is provided on the frontend.
    return render_template('index.html')

@main_routes.route('/api/check_updates', methods=['GET'])
def check_updates():
    """Endpoint for the client to check for file changes."""
    current_hash = utils.get_files_hash()
    if current_hash != utils.STARTUP_HASH:
        return jsonify({"updated": True, "message": "Source files have changed. Please restart the server and refresh the page."})
    return jsonify({"updated": False})

@main_routes.route('/api/game/state', methods=['GET'])
def get_game_state():
    """Returns the complete current game state."""
    return jsonify(game_logic.game.get_state())

@main_routes.route('/api/game/start', methods=['POST'])
def start_game():
    """Resets and initializes the game with settings from the client."""
    data = request.json
    teams = data.get('teams', {})
    points = data.get('points', [])
    # Add some basic validation
    try:
        max_turns = int(data.get('maxTurns', 100))
        grid_size = int(data.get('gridSize', 10))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid maxTurns or gridSize"}), 400

    game_logic.game.start_game(teams, points, max_turns, grid_size)
    return jsonify(game_logic.game.get_state())

@main_routes.route('/api/game/restart', methods=['POST'])
def restart_game():
    """Restarts the simulation with the same initial settings."""
    result = game_logic.game.restart_game()
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)

@main_routes.route('/api/game/reset', methods=['POST'])
def reset_game():
    """Resets the game to its initial empty state (SETUP phase)."""
    game_logic.game.reset()
    return jsonify(game_logic.game.get_state())

@main_routes.route('/api/game/next_action', methods=['POST'])
def next_action():
    """Processes the next single action in a turn."""
    game_logic.game.run_next_action()
    return jsonify(game_logic.game.get_state())