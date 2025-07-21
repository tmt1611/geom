from flask import Blueprint, render_template, jsonify, request
from . import game_logic
from . import utils

# Using a Blueprint to organize routes.
# The first argument is the name of the blueprint.
# The second argument, __name__, helps Flask locate the blueprint's resources.
main_routes = Blueprint('main', __name__)

@main_routes.route('/')
def index():
    # Reset game state when user hits the main page.
    game_logic.init_game_state()
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
    return jsonify(game_logic.game_state)

@main_routes.route('/api/game/reset', methods=['POST'])
def reset_game():
    """Resets the game with new initial settings from the client."""
    game_logic.init_game_state()
    data = request.json
    gs = game_logic.game_state # Use a shorter alias for readability
    gs['teams'] = data.get('teams', {})
    gs['points'] = data.get('points', [])
    gs['max_turns'] = int(data.get('maxTurns', 100))
    gs['is_running'] = len(gs['points']) > 0
    gs['game_log'].append("Game initialized.")
    return jsonify(gs)

@main_routes.route('/api/game/next_turn', methods=['POST'])
def next_turn():
    """Processes the next turn."""
    game_logic.run_next_turn()
    return jsonify(game_logic.game_state)