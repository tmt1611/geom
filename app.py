from flask import Flask, render_template, jsonify, request
import json
import random
import os
import hashlib

app = Flask(__name__)

# --- File Hashing for Live Update Detection ---
WATCHED_FILES = [__file__, 'static/js/main.js', 'templates/index.html']
STARTUP_HASH = ''

def get_files_hash():
    """Calculates a hash of the watched files."""
    hasher = hashlib.md5()
    for filepath in WATCHED_FILES:
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                buf = f.read()
                hasher.update(buf)
    return hasher.hexdigest()

STARTUP_HASH = get_files_hash()

# --- Game State ---
game_state = {}

def init_game_state():
    """Initializes or resets the game state."""
    global game_state
    game_state = {
        "grid_size": 10,
        "teams": {}, # { "team-1": {"name": "A", "color": "#ff0000"}}
        "points": [], # { "x": 1, "y": 1, "teamId": "team-1" }
        "lines": [], # { "p1_idx": 0, "p2_idx": 1, "teamId": "team-1" }
        "triangles": [], # { "p1_idx": 0, "p2_idx": 1, "p3_idx": 2, "teamId": "team-1" }
        "game_log": [],
        "turn": 0,
        "max_turns": 100,
        "is_running": False,
        "is_finished": False,
    }

# --- Game Logic ---

def get_team_points(teamId):
    """Returns indices of points belonging to a team."""
    return [i for i, p in enumerate(game_state['points']) if p['teamId'] == teamId]

def get_team_lines(teamId):
    """Returns indices of lines belonging to a team."""
    return [i for i, l in enumerate(game_state['lines']) if l['teamId'] == teamId]

def expand_action_add_line(teamId):
    """[EXPAND ACTION]: Add a line segment connecting two random points of the same team."""
    team_points_indices = get_team_points(teamId)
    if len(team_points_indices) < 2:
        return f"Team {game_state['teams'][teamId]['name']} has less than 2 points, cannot add line."

    # Try a few times to find a non-existing line
    for _ in range(10):
        p1_idx, p2_idx = random.sample(team_points_indices, 2)
        is_duplicate = False
        for line in game_state['lines']:
            if line['teamId'] == teamId and set([line['p1_idx'], line['p2_idx']]) == set([p1_idx, p2_idx]):
                is_duplicate = True
                break
        if not is_duplicate:
            game_state['lines'].append({"p1_idx": p1_idx, "p2_idx": p2_idx, "teamId": teamId})
            return f"Team {game_state['teams'][teamId]['name']} connected two points with a new line."
    
    return f"Team {game_state['teams'][teamId]['name']} failed to add a new unique line."


def extend_line_to_border(p1, p2, grid_size):
    """Calculates the intersection point of a line segment with the grid border."""
    x1, y1 = p1['x'], p1['y']
    x2, y2 = p2['x'], p2['y']
    dx, dy = x2 - x1, y2 - y1

    if dx == 0 and dy == 0:
        return None

    t_values = []
    if dx != 0:
        t_values.append((0 - x1) / dx) # left border
        t_values.append((grid_size - 1 - x1) / dx) # right border
    if dy != 0:
        t_values.append((0 - y1) / dy) # top border
        t_values.append((grid_size - 1 - y1) / dy) # bottom border

    # We want to extend the line, so we are interested in t > 1
    valid_t = [t for t in t_values if t > 1]
    if not valid_t:
        return None

    t = min(valid_t)
    ix, iy = x1 + t * dx, y1 + t * dy

    ix = round(max(0, min(grid_size - 1, ix)))
    iy = round(max(0, min(grid_size - 1, iy)))

    return {"x": ix, "y": iy}


def expand_action_extend_line(teamId):
    """[EXPAND ACTION]: Extend a random line segment to the border and add a point."""
    team_line_indices = get_team_lines(teamId)
    if not team_line_indices:
        return f"Team {game_state['teams'][teamId]['name']} has no lines to extend."

    line_idx = random.choice(team_line_indices)
    line = game_state['lines'][line_idx]
    
    p1 = game_state['points'][line['p1_idx']]
    p2 = game_state['points'][line['p2_idx']]

    # Randomly choose which point of the line to extend from
    if random.random() > 0.5:
        p1, p2 = p2, p1 # Extend from p2 through p1

    new_point_coords = extend_line_to_border(p1, p2, game_state['grid_size'])

    if new_point_coords:
        game_state['points'].append({**new_point_coords, "teamId": teamId})
        return f"Team {game_state['teams'][teamId]['name']} extended a line to the border, creating a new point."
    else:
        return f"Team {game_state['teams'][teamId]['name']} failed to extend a line to the border."

# NOTE: Fight and Fortify actions are complex and will be skipped for this MVP improvement
# to keep the changes manageable, but the structure is here to add them.

def run_next_turn():
    """Runs one turn of the game."""
    if game_state['is_finished']:
        return

    game_state['turn'] += 1
    game_state['game_log'].append(f"--- Turn {game_state['turn']} ---")

    active_teams = [teamId for teamId in game_state['teams'] if len(get_team_points(teamId)) > 0]
    if not active_teams:
        game_state['is_finished'] = True
        game_state['game_log'].append("No active teams left. Game over.")
        return

    for teamId in active_teams:
        # Choose a random action to perform for the team
        possible_actions = [expand_action_add_line, expand_action_extend_line]
        
        # Give higher probability to adding lines if there are few
        if len(get_team_lines(teamId)) < len(get_team_points(teamId)):
             action_to_perform = expand_action_add_line
        else:
            action_to_perform = random.choice(possible_actions)

        log_message = action_to_perform(teamId)
        game_state['game_log'].append(log_message)

    if game_state['turn'] >= game_state['max_turns']:
        game_state['is_finished'] = True
        game_state['is_running'] = False
        game_state['game_log'].append("Max turns reached. Game finished.")


# --- API Endpoints ---

@app.route('/')
def index():
    init_game_state()
    return render_template('index.html')

@app.route('/api/check_updates', methods=['GET'])
def check_updates():
    """Endpoint for the client to check for file changes."""
    current_hash = get_files_hash()
    if current_hash != STARTUP_HASH:
        return jsonify({"updated": True, "message": "Source files have changed. Please restart the server and refresh the page."})
    return jsonify({"updated": False})

@app.route('/api/game/state', methods=['GET'])
def get_game_state():
    """Returns the complete current game state."""
    return jsonify(game_state)

@app.route('/api/game/reset', methods=['POST'])
def reset_game():
    """Resets the game with new initial settings from the client."""
    init_game_state()
    data = request.json
    game_state['teams'] = data.get('teams', {})
    game_state['points'] = data.get('points', [])
    game_state['max_turns'] = int(data.get('maxTurns', 100))
    game_state['is_running'] = len(game_state['points']) > 0
    game_state['game_log'].append("Game initialized.")
    return jsonify(game_state)

@app.route('/api/game/next_turn', methods=['POST'])
def next_turn():
    """Processes the next turn."""
    run_next_turn()
    return jsonify(game_state)


if __name__ == '__main__':
    # You can run this file directly using "python app.py"
    # The server will be available at http://127.0.0.1:8888
    app.run(debug=True, port=8888)