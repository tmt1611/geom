import os
import base64
import json
from flask import Blueprint, render_template, jsonify, request, current_app, send_from_directory, Response, stream_with_context
from . import game_logic
from . import game_data
from . import utils

# Using a Blueprint to organize routes.
# The first argument is the name of the blueprint.
# The second argument, __name__, helps Flask locate the blueprint's resources.
main_routes = Blueprint('main', __name__)

@main_routes.route('/')
def index():
    """Serves the main index.html file from the project root."""
    # current_app.root_path is the 'game_app' directory. We go one level up.
    project_root = os.path.abspath(os.path.join(current_app.root_path, '..'))
    return send_from_directory(project_root, 'index.html')

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
    """Runs a full simulation, streaming updates to the client."""
    data = request.json
    teams = data.get('teams', {})
    points = data.get('points', [])
    try:
        max_turns = int(data.get('maxTurns', 100))
        grid_size = int(data.get('gridSize', 10))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid maxTurns or gridSize"}), 400

    def generate():
        for update in game_logic.game.run_full_simulation_streamed(teams, points, max_turns, grid_size):
            # For streaming, we send augmented states so the client doesn't need to request them.
            if update['type'] == 'state':
                update['data'] = game_logic.game.augment_state_for_frontend(update['data'])
            
            # Send each update as a newline-delimited JSON object
            yield json.dumps(update) + '\n'

    # The 'application/x-json-stream' mimetype is a convention for this kind of streaming.
    return Response(stream_with_context(generate()), mimetype='application/x-json-stream')

@main_routes.route('/api/game/restart', methods=['POST'])
def restart_game():
    """Restarts the simulation with the same initial settings, streaming updates."""
    
    def generate():
        for update in game_logic.game.restart_game_and_run_simulation_streamed():
            if update.get('type') == 'error':
                yield json.dumps(update) + '\n'
                return

            # For streaming, we send augmented states so the client doesn't need to request them.
            if update['type'] == 'state':
                update['data'] = game_logic.game.augment_state_for_frontend(update['data'])
            
            # Send each update as a newline-delimited JSON object
            yield json.dumps(update) + '\n'

    return Response(stream_with_context(generate()), mimetype='application/x-json-stream')

@main_routes.route('/api/game/reset', methods=['POST'])
def reset_game():
    """Resets the game to its initial empty state (SETUP phase)."""
    game_logic.game.reset()
    return jsonify(game_logic.game.get_state())

@main_routes.route('/api/actions/all', methods=['GET'])
def get_all_actions():
    """Returns a structured list of all possible actions with their descriptions."""
    return jsonify(game_data.get_all_actions_data())

@main_routes.route('/api/dev/save_illustration', methods=['POST'])
def save_illustration():
    """(Dev only) Saves a base64 encoded PNG image for the action guide."""
    if not current_app.debug:
        return jsonify({"success": False, "error": "This function is only available in debug mode."}), 403

    data = request.json
    action_name = data.get('action_name')
    image_data_url = data.get('image_data')

    if not action_name or not image_data_url:
        return jsonify({"success": False, "error": "Missing action_name or image_data"}), 400

    try:
        # The data URL is in the format 'data:image/png;base64,iVBORw0KGgo...'
        header, encoded = image_data_url.split(",", 1)
        if not header.startswith('data:image/png;base64'):
            return jsonify({"success": False, "error": "Invalid image data format"}), 400
        
        image_data = base64.b64decode(encoded)

        # Create directory if it doesn't exist
        illustrations_dir = os.path.join(current_app.static_folder, 'illustrations')
        os.makedirs(illustrations_dir, exist_ok=True)
        
        file_path = os.path.join(illustrations_dir, f"{action_name}.png")
        
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        return jsonify({"success": True, "path": file_path})

    except Exception as e:
        current_app.logger.error(f"Failed to save illustration for {action_name}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@main_routes.route('/api/dev/restart', methods=['POST'])
def restart_server():
    """(Dev only) Restarts the Flask development server by touching a watched file."""
    if not current_app.debug:
        return jsonify({"error": "This function is only available in debug mode."}), 403

    # The Werkzeug reloader watches for file changes. We can trigger it by "touching" a file.
    # We'll touch run.py, which is the main entry point.
    try:
        # This will trigger the reloader in debug mode
        os.utime('run.py', None)
        return jsonify({"message": "Server is restarting..."})
    except Exception as e:
        current_app.logger.error(f"Could not trigger restart: {e}")
        return jsonify({"error": f"Could not trigger restart: {e}"}), 500

@main_routes.route('/game_app/<path:filename>')
def serve_game_app_files(filename):
    """
    Serve files from the game_app directory.
    This is needed for Pyodide to fetch the Python source in development mode.
    """
    if not current_app.debug:
        return jsonify({"error": "This function is only available in development mode."}), 403
        
    # current_app.root_path is the absolute path to the 'game_app' directory.
    py_dir = os.path.abspath(current_app.root_path)
    return send_from_directory(py_dir, filename)