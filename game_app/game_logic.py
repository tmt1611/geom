import random
import math
import uuid  # For unique point IDs
from itertools import combinations

# --- Geometric Helper Functions ---

def distance_sq(p1, p2):
    """Calculates the squared distance between two points."""
    return (p1['x'] - p2['x'])**2 + (p1['y'] - p2['y'])**2

def on_segment(p, q, r):
    """Given three collinear points p, q, r, checks if point q lies on line segment 'pr'."""
    return (q['x'] <= max(p['x'], r['x']) and q['x'] >= min(p['x'], r['x']) and
            q['y'] <= max(p['y'], r['y']) and q['y'] >= min(p['y'], r['y']))

def orientation(p, q, r):
    """Finds orientation of ordered triplet (p, q, r).
    Returns:
    0 --> p, q and r are collinear
    1 --> Clockwise
    2 --> Counterclockwise
    """
    val = (q['y'] - p['y']) * (r['x'] - q['x']) - \
          (q['x'] - p['x']) * (r['y'] - q['y'])
    if val == 0: return 0  # Collinear
    return 1 if val > 0 else 2  # Clockwise or Counter-clockwise

def segments_intersect(p1, q1, p2, q2):
    """Checks if line segment 'p1q1' and 'p2q2' intersect."""
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # General case: segments cross each other
    if o1 != o2 and o3 != o4:
        return True

    # Special Cases for collinear points
    # p1, q1 and p2 are collinear and p2 lies on segment p1q1
    if o1 == 0 and on_segment(p1, p2, q1): return True
    # p1, q1 and q2 are collinear and q2 lies on segment p1q1
    if o2 == 0 and on_segment(p1, q2, q1): return True
    # p2, q2 and p1 are collinear and p1 lies on segment p2q2
    if o3 == 0 and on_segment(p2, p1, q2): return True
    # p2, q2 and q1 are collinear and q1 lies on segment p2q2
    if o4 == 0 and on_segment(p2, q1, q2): return True

    return False

def get_segment_intersection_point(p1, q1, p2, q2):
    """Finds the intersection point of two line segments 'p1q1' and 'p2q2'.
    Returns a dict {'x', 'y'} or None if they do not intersect on the segments.
    """
    x1, y1 = p1['x'], p1['y']
    x2, y2 = q1['x'], q1['y']
    x3, y3 = p2['x'], p2['y']
    x4, y4 = q2['x'], q2['y']

    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if den == 0:
        return None  # Lines are parallel or collinear

    t_num = (x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)
    u_num = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3))

    t = t_num / den
    u = u_num / den

    # If 0<=t<=1 and 0<=u<=1, the segments intersect
    if 0 <= t <= 1 and 0 <= u <= 1:
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return {'x': ix, 'y': iy}

    return None  # Intersection point is not on both segments

def _is_spawn_location_valid(self, new_point_coords, new_point_teamId, min_dist_sq=1.0):
    """Checks if a new point can be spawned at the given coordinates."""
    # Check proximity to existing points
    for existing_p in self.state['points'].values():
        if distance_sq(new_point_coords, existing_p) < min_dist_sq:
            return False, 'too close to an existing point'
    
    # Check proximity to fissures (a simple bounding box check for performance)
    for fissure in self.state.get('fissures', []):
        p1 = fissure['p1']
        p2 = fissure['p2']
        # Bounding box of the fissure segment
        box_x_min = min(p1['x'], p2['x']) - 1
        box_x_max = max(p1['x'], p2['x']) + 1
        box_y_min = min(p1['y'], p2['y']) - 1
        box_y_max = max(p1['y'], p2['y']) + 1
        
        if (new_point_coords['x'] >= box_x_min and new_point_coords['x'] <= box_x_max and
            new_point_coords['y'] >= box_y_min and new_point_coords['y'] <= box_y_max):
            # A more precise check can be done here if needed, but this is a good first pass
            return False, 'too close to a fissure'

    # Check against enemy Heartwood defensive aura
    if self.state.get('heartwoods'):
        for teamId, heartwood in self.state['heartwoods'].items():
            if teamId != new_point_teamId:
                aura_radius_sq = (self.state['grid_size'] * 0.2)**2
                if distance_sq(new_point_coords, heartwood['center_coords']) < aura_radius_sq:
                    return False, 'blocked by an enemy Heartwood aura'
    
    return True, 'valid'

def is_rectangle(p1, p2, p3, p4):
    """Checks if four points form a rectangle. Returns (is_rect, aspect_ratio).
    This is a helper function that doesn't rely on game state.
    """
    points = [p1, p2, p3, p4]
    
    # Check for non-collapsed points. Using tuple of coords for hashability.
    if len(set((p['x'], p['y']) for p in points)) < 4:
        return False, 0

    # There are 6 distances between 4 points.
    dists_sq = sorted([
        distance_sq(p1, p2), distance_sq(p1, p3), distance_sq(p1, p4),
        distance_sq(p2, p3), distance_sq(p2, p4), distance_sq(p3, p4)
    ])

    # For a rectangle, the sorted squared distances should be [s1, s1, s2, s2, d, d]
    # where s1 and s2 are sides and d is the diagonal.
    s1_sq, s2_sq = dists_sq[0], dists_sq[2]
    d_sq = dists_sq[4]

    # Check for non-zero side length
    if s1_sq < 0.01:
        return False, 0
    
    # Check for 2 pairs of equal sides (with a small tolerance for float issues)
    if not (abs(dists_sq[0] - dists_sq[1]) < 0.01 and abs(dists_sq[2] - dists_sq[3]) < 0.01):
        return False, 0
    
    # Check for 2 equal diagonals
    if not abs(dists_sq[4] - dists_sq[5]) < 0.01:
        return False, 0
    
    # Check Pythagorean theorem for a right angle: s1^2 + s2^2 = d^2
    if not abs((s1_sq + s2_sq) - d_sq) < 0.01:
        return False, 0

    # Calculate aspect ratio (long side / short side)
    side1 = math.sqrt(s1_sq)
    side2 = math.sqrt(s2_sq)
    
    # This check is redundant due to the s1_sq check above, but safe.
    if side1 < 0.1 or side2 < 0.1: return False, 0

    aspect_ratio = max(side1, side2) / min(side1, side2)
    
    return True, aspect_ratio

def get_isosceles_triangle_info(p1, p2, p3):
    """
    Checks if 3 points form an isosceles triangle.
    Returns a dict with {'apex': point, 'base': [p_b1, p_b2], 'height_sq': h^2} or None.
    The apex is the vertex where the two equal sides meet.
    """
    dists = {
        '12': distance_sq(p1, p2),
        '13': distance_sq(p1, p3),
        '23': distance_sq(p2, p3),
    }
    
    TOLERANCE = 0.01 # Using a small tolerance for float equality

    # Check for non-degenerate triangles
    if dists['12'] < TOLERANCE or dists['13'] < TOLERANCE or dists['23'] < TOLERANCE:
        return None

    # Check for two equal sides
    if abs(dists['12'] - dists['13']) < TOLERANCE:
        height_sq = dists['12'] - (dists['23'] / 4.0)
        return {'apex': p1, 'base': [p2, p3], 'height_sq': height_sq, 'leg_sq': dists['12']}
    elif abs(dists['12'] - dists['23']) < TOLERANCE:
        height_sq = dists['12'] - (dists['13'] / 4.0)
        return {'apex': p2, 'base': [p1, p3], 'height_sq': height_sq, 'leg_sq': dists['12']}
    elif abs(dists['13'] - dists['23']) < TOLERANCE:
        height_sq = dists['13'] - (dists['12'] / 4.0)
        return {'apex': p3, 'base': [p1, p2], 'height_sq': height_sq, 'leg_sq': dists['13']}
    
    return None

# --- Game Class ---
class Game:
    """Encapsulates the entire game state and logic."""
    def __init__(self):
        self.reset()

    def reset(self):
        """Initializes or resets the game state with default teams."""
        # Using fixed IDs for default teams ensures they can be referenced consistently.
        default_teams = {
            'team_alpha_default': {'id': 'team_alpha_default', 'name': 'Team Alpha', 'color': '#ff4b4b', 'trait': 'Aggressive'},
            'team_beta_default': {'id': 'team_beta_default', 'name': 'Team Beta', 'color': '#4b4bff', 'trait': 'Defensive'}
        }
        self.state = {
            "grid_size": 10,
            "teams": default_teams,
            "points": {},
            "lines": [],  # Each line will now get a unique ID
            "shields": {}, # {line_id: turns_left}
            "anchors": {}, # {point_id: {teamId: teamId, turns_left: N}}
            "territories": [], # Added for claimed triangles
            "bastions": {}, # {bastion_id: {teamId, core_id, prong_ids}}
            "runes": {}, # {teamId: {'cross': [], 'v_shape': []}}
            "sentries": {}, # {teamId: [sentry1, sentry2, ...]}
            "nexuses": {}, # {teamId: [nexus1, nexus2, ...]}
            "conduits": {}, # {teamId: [conduit1, conduit2, ...]}
            "prisms": {}, # {teamId: [prism1, prism2, ...]}
            "heartwoods": {}, # {teamId: {id, center_coords, growth_counter}}
            "whirlpools": [], # {id, teamId, coords, turns_left, strength, radius_sq}
            "monoliths": {}, # {monolith_id: {teamId, point_ids, ...}}
            "trebuchets": {}, # {teamId: [trebuchet1, ...]}
            "rift_spires": {}, # {spire_id: {teamId, coords, charge}}
            "fissures": [], # {id, p1, p2, turns_left}
            "wonders": {}, # {wonder_id: {teamId, type, turns_to_victory, ...}}
            "empowered_lines": {}, # {line_id: strength}
            "game_log": [{'message': "Welcome! Default teams Alpha and Beta are ready. Place points to begin.", 'short_message': '[READY]'}],
            "turn": 0,
            "max_turns": 100,
            "game_phase": "SETUP", # SETUP, RUNNING, FINISHED
            "victory_condition": None,
            "sole_survivor_tracker": {'teamId': None, 'turns': 0},
            "interpretation": {},
            "last_action_details": {}, # For frontend visualization
            "initial_state": None, # Store the setup config for restarts
            "new_turn_events": [], # For visualizing things that happen at turn start
            "action_in_turn": 0, # Which action index in the current turn's queue
            "actions_queue_this_turn": [], # List of action dicts {teamId, is_bonus} for the current turn
            "action_events": [] # For visualizing secondary effects of an action
        }

    def get_state(self):
        """Returns the current game state, augmenting with transient data for frontend."""
        # On-demand calculation of interpretation when game is finished
        if self.state['game_phase'] == 'FINISHED' and not self.state['interpretation']:
            self.state['interpretation'] = self.calculate_interpretation()

        # Create a copy to avoid modifying original state
        state_copy = self.state.copy()
        
        # Augment lines with shield/bastion status for easier rendering
        bastion_line_ids = self._get_bastion_line_ids()
        augmented_lines = []
        for line in self.state['lines']:
            augmented_line = line.copy()
            augmented_line['is_shielded'] = line.get('id') in self.state['shields']
            augmented_line['is_bastion_line'] = line.get('id') in bastion_line_ids
            augmented_line['empower_strength'] = self.state.get('empowered_lines', {}).get(line.get('id'), 0)
            augmented_lines.append(augmented_line)
        state_copy['lines'] = augmented_lines

        # Augment points with anchor and fortified status
        fortified_point_ids = self._get_fortified_point_ids()
        bastion_point_ids = self._get_bastion_point_ids()
        
        # Get all Sentry point IDs for quick lookup
        sentry_eye_ids = set()
        sentry_post_ids = set()
        for team_sentries in self.state.get('sentries', {}).values():
            for sentry in team_sentries:
                sentry_eye_ids.add(sentry['eye_id'])
                sentry_post_ids.add(sentry['post1_id'])
                sentry_post_ids.add(sentry['post2_id'])

        # Get all Conduit point IDs for quick lookup
        conduit_point_ids = set()
        for team_conduits in self.state.get('conduits', {}).values():
            for conduit in team_conduits:
                for pid in conduit.get('point_ids', []):
                    conduit_point_ids.add(pid)
        
        # Get all Nexus point IDs for quick lookup
        nexus_point_ids = set()
        for team_nexuses in self.state.get('nexuses', {}).values():
            for nexus in team_nexuses:
                for pid in nexus.get('point_ids', []):
                    nexus_point_ids.add(pid)
        
        # Get all Monolith point IDs for quick lookup
        monolith_point_ids = set()
        for monolith in self.state.get('monoliths', {}).values():
            for pid in monolith.get('point_ids', []):
                monolith_point_ids.add(pid)

        # Get all Trebuchet point IDs for quick lookup
        trebuchet_point_ids = set()
        for team_trebuchets in self.state.get('trebuchets', {}).values():
            for trebuchet in team_trebuchets:
                for pid in trebuchet.get('point_ids', []):
                    trebuchet_point_ids.add(pid)

        augmented_points = {}
        for pid, point in self.state['points'].items():
            augmented_point = point.copy()
            augmented_point['is_anchor'] = pid in self.state['anchors']
            augmented_point['is_fortified'] = pid in fortified_point_ids
            augmented_point['is_bastion_core'] = pid in bastion_point_ids['cores']
            augmented_point['is_bastion_prong'] = pid in bastion_point_ids['prongs']
            augmented_point['is_sentry_eye'] = pid in sentry_eye_ids
            augmented_point['is_sentry_post'] = pid in sentry_post_ids
            augmented_point['is_conduit_point'] = pid in conduit_point_ids
            augmented_point['is_nexus_point'] = pid in nexus_point_ids
            augmented_point['is_monolith_point'] = pid in monolith_point_ids
            augmented_point['is_trebuchet_point'] = pid in trebuchet_point_ids
            augmented_points[pid] = augmented_point
        state_copy['points'] = augmented_points

        # Add structures for frontend rendering
        state_copy['nexuses'] = self.state.get('nexuses', {})
        state_copy['prisms'] = self.state.get('prisms', {})
        state_copy['heartwoods'] = self.state.get('heartwoods', {})
        state_copy['whirlpools'] = self.state.get('whirlpools', [])
        state_copy['monoliths'] = self.state.get('monoliths', {})
        state_copy['trebuchets'] = self.state.get('trebuchets', {})
        state_copy['rift_spires'] = self.state.get('rift_spires', {})
        state_copy['fissures'] = self.state.get('fissures', [])
        state_copy['wonders'] = self.state.get('wonders', {})

        # Add live stats for real-time display, regardless of phase, for consistency
        live_stats = {}
        all_points = self.state['points'] # Use original points for calculations
        for teamId, team_data in self.state['teams'].items():
            team_point_ids = self.get_team_point_ids(teamId)
            team_lines = self.get_team_lines(teamId)
            team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]

            # Calculate controlled area
            controlled_area = 0
            for territory in team_territories:
                triangle_point_ids = territory['point_ids']
                if all(pid in all_points for pid in triangle_point_ids):
                    triangle_points = [all_points[pid] for pid in triangle_point_ids]
                    if len(triangle_points) == 3:
                        controlled_area += self._polygon_area(triangle_points)

            live_stats[teamId] = {
                'point_count': len(team_point_ids),
                'line_count': len(team_lines),
                'controlled_area': round(controlled_area, 2)
            }
        state_copy['live_stats'] = live_stats

        return state_copy

    def start_game(self, teams, points, max_turns, grid_size):
        """Starts a new game with the given parameters."""
        self.reset()
        
        # Process team traits, handling 'Random' selection
        available_traits = ['Aggressive', 'Expansive', 'Defensive', 'Balanced']
        for team_id, team_data in teams.items():
            if team_data.get('trait') == 'Random' or 'trait' not in team_data:
                team_data['trait'] = random.choice(available_traits)
            team_data['id'] = team_id # Ensure team object contains its own ID

        self.state['teams'] = teams
        # Convert points list to a dictionary with unique IDs
        for p in points:
            point_id = f"p_{uuid.uuid4().hex[:6]}"
            self.state['points'][point_id] = {**p, 'id': point_id}
        self.state['max_turns'] = max_turns
        self.state['grid_size'] = grid_size
        self.state['game_phase'] = "RUNNING" if len(points) > 0 else "SETUP"
        self.state['game_log'].append({'message': "Game initialized.", 'short_message': '[INIT]'})
        self.state['action_in_turn'] = 0
        self.state['actions_queue_this_turn'] = []
        
        # Store the initial state for restarting
        self.state['initial_state'] = {
            'teams': self.state['teams'],
            'points': points, # Use original point list before IDs are added
            'max_turns': max_turns,
            'grid_size': grid_size
        }

    def get_team_point_ids(self, teamId):
        """Returns IDs of points belonging to a team."""
        return [pid for pid, p in self.state['points'].items() if p['teamId'] == teamId]

    def get_team_lines(self, teamId):
        """Returns lines belonging to a team."""
        return [l for l in self.state['lines'] if l['teamId'] == teamId]

    def _get_fortified_point_ids(self):
        """Returns a set of all point IDs that are part of any claimed territory."""
        fortified_ids = set()
        for territory in self.state.get('territories', []):
            for point_id in territory['point_ids']:
                fortified_ids.add(point_id)
        return fortified_ids

    def _get_bastion_point_ids(self):
        """Returns a dict of bastion core and prong point IDs."""
        core_ids = set()
        prong_ids = set()
        for bastion in self.state.get('bastions', {}).values():
            core_ids.add(bastion['core_id'])
            for pid in bastion['prong_ids']:
                prong_ids.add(pid)
        return {'cores': core_ids, 'prongs': prong_ids}

    def _get_bastion_line_ids(self):
        """Returns a set of line IDs that are part of any bastion."""
        bastion_lines = set()
        all_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l['id'] for l in self.state['lines']}

        for bastion in self.state.get('bastions', {}).values():
            core_id = bastion['core_id']
            for prong_id in bastion['prong_ids']:
                line_key = tuple(sorted((core_id, prong_id)))
                if line_key in all_lines_by_points:
                    bastion_lines.add(all_lines_by_points[line_key])
        return bastion_lines

    def _trigger_nexus_detonation(self, nexus, aggressor_team_id):
        """Handles the logic for a Nexus exploding when one of its points is destroyed."""
        center = nexus['center']
        radius_sq = (self.state['grid_size'] * 0.2)**2
        nexus_owner_teamId = nexus['teamId']
        nexus_owner_name = self.state['teams'][nexus_owner_teamId]['name']
        aggressor_name = self.state['teams'][aggressor_team_id]['name'] if aggressor_team_id and aggressor_team_id in self.state['teams'] else "an unknown force"

        log_msg = f"The destruction of a Nexus from Team {nexus_owner_name} by Team {aggressor_name} caused a violent energy discharge!"
        self.state['game_log'].append({'message': log_msg, 'short_message': '[NEXUS BOOM!]', 'teamId': nexus_owner_teamId})
        self.state['action_events'].append({
            'type': 'nexus_detonation',
            'center': center,
            'radius_sq': radius_sq,
            'color': self.state['teams'][nexus_owner_teamId]['color']
        })

        points_to_destroy_ids = []
        lines_to_destroy = []
        # Target enemies of the nexus owner
        for pid, p in list(self.state['points'].items()):
            if p['teamId'] != nexus_owner_teamId and distance_sq(center, p) < radius_sq:
                points_to_destroy_ids.append(pid)

        for line in list(self.state['lines']):
            if line['teamId'] != nexus_owner_teamId:
                p1 = self.state['points'].get(line['p1_id'])
                p2 = self.state['points'].get(line['p2_id'])
                if p1 and p2 and (distance_sq(center, p1) < radius_sq or distance_sq(center, p2) < radius_sq):
                    lines_to_destroy.append(line)
        
        destroyed_points_count = 0
        for pid in points_to_destroy_ids:
            if pid in self.state['points']:
                self._delete_point_and_connections(pid, aggressor_team_id)
                destroyed_points_count += 1
        
        destroyed_lines_count = 0
        for line in lines_to_destroy:
            if line in self.state['lines']:
                self.state['lines'].remove(line)
                self.state['shields'].pop(line.get('id'), None)
                destroyed_lines_count += 1

        if destroyed_points_count > 0 or destroyed_lines_count > 0:
            log_msg = f"The blast destroyed {destroyed_points_count} points and {destroyed_lines_count} lines."
            self.state['game_log'].append({'message': log_msg, 'short_message': '[CASCADE]', 'teamId': nexus_owner_teamId})

    def _delete_point_and_connections(self, point_id, aggressor_team_id=None):
        """A robust helper to delete a point and handle all cascading effects."""
        if point_id not in self.state['points']:
            return None # Point already gone

        # 1. Pre-deletion checks for cascades
        # Check for Nexus destruction. A point can only belong to one nexus.
        nexus_to_detonate = None
        all_nexuses = [n for team_nexuses in self.state.get('nexuses', {}).values() for n in team_nexuses]
        for nexus in all_nexuses:
            if point_id in nexus.get('point_ids', []):
                nexus_to_detonate = nexus
                break
        
        # 2. Delete the point object itself, returning its data
        deleted_point_data = self.state['points'].pop(point_id)

        # 3. Trigger cascade effects AFTER the point is deleted
        if nexus_to_detonate and aggressor_team_id:
            self._trigger_nexus_detonation(nexus_to_detonate, aggressor_team_id)

        # 4. Remove connected lines (and their shields)
        lines_before = self.state['lines'][:]
        self.state['lines'] = []
        for l in lines_before:
            if point_id in (l['p1_id'], l['p2_id']):
                self.state['shields'].pop(l.get('id'), None)
            else:
                self.state['lines'].append(l)

        # 5. Remove territories that used this point
        self.state['territories'] = [t for t in self.state['territories'] if point_id not in t['point_ids']]

        # 6. Handle anchors
        self.state['anchors'].pop(point_id, None)

        # 7. Handle bastions
        bastions_to_dissolve = []
        for bastion_id, bastion in list(self.state['bastions'].items()):
            if bastion['core_id'] == point_id:
                # Core is gone, bastion dissolves completely
                bastions_to_dissolve.append(bastion_id)
            elif point_id in bastion['prong_ids']:
                # A prong is gone, update the bastion
                bastion['prong_ids'].remove(point_id)
                # If bastion has too few prongs, it dissolves
                if len(bastion['prong_ids']) < 2:
                    bastions_to_dissolve.append(bastion_id)
        
        for bastion_id in bastions_to_dissolve:
            if bastion_id in self.state['bastions']:
                del self.state['bastions'][bastion_id]

        # 6. Handle Trebuchets
        if self.state.get('trebuchets'):
            for teamId, trebuchets in list(self.state.get('trebuchets', {}).items()):
                self.state['trebuchets'][teamId] = [
                    t for t in trebuchets if point_id not in t['point_ids']
                ]
        
        return deleted_point_data

    def _triangle_centroid(self, points):
        """Calculates the centroid of a triangle. Assumes points is a list of 3 point dicts."""
        if not points or len(points) != 3:
            return None
        x_sum = sum(p['x'] for p in points)
        y_sum = sum(p['y'] for p in points)
        return {'x': x_sum / 3.0, 'y': y_sum / 3.0}

    # --- Game Actions ---

    def expand_action_add_line(self, teamId):
        """[EXPAND ACTION]: Add a line between two random points."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 2:
            return {'success': False, 'reason': 'not enough points'}

        # Create a set of existing lines for quick lookup
        existing_lines = set()
        for line in self.state['lines']:
            if line['teamId'] == teamId:
                existing_lines.add(tuple(sorted((line['p1_id'], line['p2_id']))))

        # Try to find a non-existing line
        possible_pairs = []
        for i in range(len(team_point_ids)):
            for j in range(i + 1, len(team_point_ids)):
                p1_id = team_point_ids[i]
                p2_id = team_point_ids[j]
                if tuple(sorted((p1_id, p2_id))) not in existing_lines:
                    possible_pairs.append((p1_id, p2_id))
        
        if not possible_pairs:
            return {'success': False, 'reason': 'no new lines possible'}

        p1_id, p2_id = random.choice(possible_pairs)
        line_id = f"l_{uuid.uuid4().hex[:6]}"
        new_line = {"id": line_id, "p1_id": p1_id, "p2_id": p2_id, "teamId": teamId}
        self.state['lines'].append(new_line)
        return {'success': True, 'type': 'add_line', 'line': new_line}

    def _get_extended_border_point(self, p1, p2):
        """
        Extends a line segment p1-p2 from p1 outwards through p2 to the border.
        Returns the border point dictionary or None.
        """
        grid_size = self.state['grid_size']
        x1, y1 = p1['x'], p1['y']
        x2, y2 = p2['x'], p2['y']
        dx, dy = x2 - x1, y2 - y1

        if dx == 0 and dy == 0: return None

        # Check if extension is blocked by a fissure
        # Create a very long ray for intersection test
        ray_end_point = {'x': p2['x'] + dx * grid_size * 2, 'y': p2['y'] + dy * grid_size * 2}
        for fissure in self.state.get('fissures', []):
            if segments_intersect(p2, ray_end_point, fissure['p1'], fissure['p2']):
                return None # Extension is blocked by a fissure

        # We are calculating p_new = p1 + t * (p2 - p1) for t > 1
        t_values = []
        if dx != 0:
            t_values.append((0 - x1) / dx)
            t_values.append((grid_size - 1 - x1) / dx)
        if dy != 0:
            t_values.append((0 - y1) / dy)
            t_values.append((grid_size - 1 - y1) / dy)

        # Use a small epsilon to avoid floating point issues with the point itself
        valid_t = [t for t in t_values if t > 1.0001]
        if not valid_t: return None

        t = min(valid_t)
        ix, iy = x1 + t * dx, y1 + t * dy
        ix = round(max(0, min(grid_size - 1, ix)))
        iy = round(max(0, min(grid_size - 1, iy)))
        return {"x": ix, "y": iy}

    def expand_action_extend_line(self, teamId):
        """[EXPAND ACTION]: Extend a line to the border to create a new point."""
        team_lines = self.get_team_lines(teamId)
        points = self.state['points']
        
        possible_extensions = []
        for line in team_lines:
            if line['p1_id'] not in points or line['p2_id'] not in points:
                continue
            p1 = points[line['p1_id']]
            p2 = points[line['p2_id']]
            
            # Direction 1: extend from p1 through p2
            border_point1 = self._get_extended_border_point(p1, p2)
            if border_point1:
                possible_extensions.append({'origin_point_id': p2['id'], 'border_point': border_point1})
            
            # Direction 2: extend from p2 through p1
            border_point2 = self._get_extended_border_point(p2, p1)
            if border_point2:
                possible_extensions.append({'origin_point_id': p1['id'], 'border_point': border_point2})

        if not possible_extensions:
            return {'success': False, 'reason': 'no lines can be extended to the border'}

        # Let's try a few extensions to find a valid one
        random.shuffle(possible_extensions)
        chosen_extension = None
        for extension in possible_extensions:
            is_valid, reason = self._is_spawn_location_valid(extension['border_point'], teamId)
            if is_valid:
                chosen_extension = extension
                break
        
        if not chosen_extension:
            return {'success': False, 'reason': 'no valid border position found for extension'}

        border_point = chosen_extension['border_point']
        origin_point_id = chosen_extension['origin_point_id']
        
        # Check if this extension is empowered by a Conduit
        is_empowered = False
        team_conduits = self.state.get('conduits', {}).get(teamId, [])
        for conduit in team_conduits:
            if origin_point_id in (conduit['endpoint1_id'], conduit['endpoint2_id']):
                is_empowered = True
                break

        # Create new point with a unique ID
        new_point_id = f"p_{uuid.uuid4().hex[:6]}"
        new_point = {**border_point, "teamId": teamId, "id": new_point_id}
        self.state['points'][new_point_id] = new_point
        
        result_payload = {'success': True, 'type': 'extend_line', 'new_point': new_point, 'is_empowered': is_empowered}
        
        if is_empowered:
            # Empowered extension also creates a line to the new point
            line_id = f"l_{uuid.uuid4().hex[:6]}"
            new_line = {"id": line_id, "p1_id": origin_point_id, "p2_id": new_point_id, "teamId": teamId}
            self.state['lines'].append(new_line)
            result_payload['new_line'] = new_line
        
        return result_payload

    def expand_action_fracture_line(self, teamId):
        """[EXPAND ACTION]: Splits a line into two, creating a new point."""
        team_lines = self.get_team_lines(teamId)
        points = self.state['points']

        # Get territory boundary lines to exclude them from fracturing
        territory_lines = set()
        for t in self.state.get('territories', []):
            if t['teamId'] == teamId:
                p_ids = t['point_ids']
                # A territory is a triangle, so it has 3 sides (lines)
                territory_lines.add(tuple(sorted((p_ids[0], p_ids[1]))))
                territory_lines.add(tuple(sorted((p_ids[1], p_ids[2]))))
                territory_lines.add(tuple(sorted((p_ids[2], p_ids[0]))))

        fracturable_lines = []
        for line in team_lines:
            # Check if line is a territory boundary
            if tuple(sorted((line['p1_id'], line['p2_id']))) in territory_lines:
                continue

            if line['p1_id'] not in points or line['p2_id'] not in points:
                continue
            p1 = points[line['p1_id']]
            p2 = points[line['p2_id']]
            if distance_sq(p1, p2) >= 4.0: # min length of 2
                fracturable_lines.append(line)

        if not fracturable_lines:
            return {'success': False, 'reason': 'no non-territory lines long enough to fracture'}

        line_to_fracture = random.choice(fracturable_lines)
        p1 = points[line_to_fracture['p1_id']]
        p2 = points[line_to_fracture['p2_id']]

        # Find a new point on the segment
        ratio = random.uniform(0.25, 0.75)
        new_x = p1['x'] + (p2['x'] - p1['x']) * ratio
        new_y = p1['y'] + (p2['y'] - p1['y']) * ratio

        # Create new point, ensuring integer coordinates
        new_point_id = f"p_{uuid.uuid4().hex[:6]}"
        new_point = {"x": round(new_x), "y": round(new_y), "teamId": teamId, "id": new_point_id}
        self.state['points'][new_point_id] = new_point

        # Remove old line and its potential shield
        self.state['lines'].remove(line_to_fracture)
        self.state['shields'].pop(line_to_fracture.get('id'), None)

        # Create two new lines
        line_id_1 = f"l_{uuid.uuid4().hex[:6]}"
        new_line_1 = {"id": line_id_1, "p1_id": line_to_fracture['p1_id'], "p2_id": new_point_id, "teamId": teamId}
        line_id_2 = f"l_{uuid.uuid4().hex[:6]}"
        new_line_2 = {"id": line_id_2, "p1_id": new_point_id, "p2_id": line_to_fracture['p2_id'], "teamId": teamId}
        self.state['lines'].extend([new_line_1, new_line_2])

        return {
            'success': True,
            'type': 'fracture_line',
            'new_point': new_point,
            'new_line1': new_line_1,
            'new_line2': new_line_2,
            'old_line': line_to_fracture
        }


    def fight_action_attack_line(self, teamId):
        """[FIGHT ACTION]: Extend a line to hit an enemy line, destroying it."""
        possible_attacks = []
        team_lines = self.get_team_lines(teamId)
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        points = self.state['points']

        if not team_lines or not enemy_lines:
            return {'success': False, 'reason': 'not enough lines to perform an attack'}

        team_has_cross_rune = len(self.state.get('runes', {}).get(teamId, {}).get('cross', [])) > 0

        for line in team_lines:
            if line['p1_id'] not in points or line['p2_id'] not in points: continue
            p1 = points[line['p1_id']]
            p2 = points[line['p2_id']]

            for p_start, p_end in [(p1, p2), (p2, p1)]:
                border_point = self._get_extended_border_point(p_start, p_end)
                if not border_point: continue

                attack_segment_p1 = p_end
                attack_segment_p2 = border_point

                for enemy_line in enemy_lines:
                    is_shielded = enemy_line.get('id') in self.state['shields']
                    
                    # Bastion lines are immune to normal attacks
                    bastion_line_ids = self._get_bastion_line_ids()
                    if enemy_line.get('id') in bastion_line_ids:
                        continue

                    if is_shielded and not team_has_cross_rune:
                        continue # Shield protects if attacker has no Cross Rune
                    
                    empower_strength = self.state.get('empowered_lines', {}).get(enemy_line.get('id'))

                    if enemy_line['p1_id'] not in points or enemy_line['p2_id'] not in points: continue
                    
                    ep1 = points[enemy_line['p1_id']]
                    ep2 = points[enemy_line['p2_id']]

                    # Check if attack ray is blocked by a fissure
                    is_blocked_by_fissure = False
                    for fissure in self.state.get('fissures', []):
                        if get_segment_intersection_point(attack_segment_p1, attack_segment_p2, fissure['p1'], fissure['p2']):
                             is_blocked_by_fissure = True
                             break
                    if is_blocked_by_fissure:
                        continue

                    if segments_intersect(attack_segment_p1, attack_segment_p2, ep1, ep2):
                        possible_attacks.append({
                            'attacker_line': line,
                            'target_line': enemy_line,
                            'attack_ray': {'p1': attack_segment_p1, 'p2': attack_segment_p2},
                            'bypassed_shield': is_shielded and team_has_cross_rune,
                            'was_empowered': bool(empower_strength)
                        })

        if not possible_attacks:
            return {'success': False, 'reason': 'no target in range'}

        # Choose one of the possible attacks and execute it.
        chosen_attack = random.choice(possible_attacks)
        enemy_line = chosen_attack['target_line']
        enemy_team_name = self.state['teams'][enemy_line['teamId']]['name']
        
        # Check if the line is empowered by a Monolith
        empower_strength = self.state.get('empowered_lines', {}).get(enemy_line['id'])
        if empower_strength:
            self.state['empowered_lines'][enemy_line['id']] -= 1
            if self.state['empowered_lines'][enemy_line['id']] <= 0:
                del self.state['empowered_lines'][enemy_line['id']]
            
            # The line was hit but not destroyed
            return {
                'success': True,
                'type': 'attack_line_empowered',
                'damaged_line': enemy_line,
                'attacker_line': chosen_attack['attacker_line'],
                'attack_ray': chosen_attack['attack_ray']
            }

        # Line is not empowered, destroy it
        self.state['lines'].remove(enemy_line)
        self.state['shields'].pop(enemy_line.get('id'), None)
        self.state['empowered_lines'].pop(enemy_line.get('id'), None) # Clean up just in case
        
        return {
            'success': True, 
            'type': 'attack_line', 
            'destroyed_team': enemy_team_name, 
            'destroyed_line': enemy_line,
            'attacker_line': chosen_attack['attacker_line'],
            'attack_ray': chosen_attack['attack_ray'],
            'bypassed_shield': chosen_attack['bypassed_shield']
        }

    def sacrifice_action_nova_burst(self, teamId):
        """[SACRIFICE ACTION]: A point is destroyed, removing nearby enemy lines."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) <= 2:
            return {'success': False, 'reason': 'not enough points to sacrifice safely'}

        sac_point_id = random.choice(team_point_ids)
        # We must copy the point's data before it's deleted by the helper function.
        sac_point_coords = self.state['points'][sac_point_id].copy()
        
        # Define the blast radius (squared for efficiency)
        blast_radius_sq = (self.state['grid_size'] * 0.25)**2 

        # Temporarily store lines connected to the sacrificed point to count them later
        connected_lines_before = [l for l in self.state['lines'] if sac_point_id in (l['p1_id'], l['p2_id'])]
        
        # 1. Sacrifice the point and its direct connections/structures
        self._delete_point_and_connections(sac_point_id, aggressor_team_id=teamId)
        
        # 2. Find and remove nearby enemy lines that still exist
        lines_to_remove_by_proximity = []
        points_to_check = self.state['points']
        bastion_line_ids = self._get_bastion_line_ids()
        # Only check enemy lines that are still in the game state
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]

        for line in enemy_lines:
            if line.get('id') in bastion_line_ids: continue
            if not (line['p1_id'] in points_to_check and line['p2_id'] in points_to_check): continue
            
            p1 = points_to_check[line['p1_id']]
            p2 = points_to_check[line['p2_id']]

            if distance_sq(sac_point_coords, p1) < blast_radius_sq or distance_sq(sac_point_coords, p2) < blast_radius_sq:
                lines_to_remove_by_proximity.append(line)

        # Perform removals
        for l in lines_to_remove_by_proximity:
            self.state['shields'].pop(l.get('id'), None)
        
        self.state['lines'] = [l for l in self.state['lines'] if l not in lines_to_remove_by_proximity]
        
        total_destroyed = len(connected_lines_before) + len(lines_to_remove_by_proximity)

        return {'success': True, 'type': 'nova_burst', 'sacrificed_point': sac_point_coords, 'lines_destroyed': total_destroyed}

    def sacrifice_action_create_whirlpool(self, teamId):
        """[SACRIFICE ACTION]: A point is destroyed, creating a swirling vortex."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) <= 1: # Cannot sacrifice the last point
            return {'success': False, 'reason': 'not enough points to sacrifice'}

        # To avoid destroying critical structures, prefer non-special points
        bastion_points = self._get_bastion_point_ids()
        non_critical_points = [
            pid for pid in team_point_ids
            if pid not in self._get_fortified_point_ids() and
               pid not in bastion_points['cores'] and
               pid not in bastion_points['prongs']
        ]

        if not non_critical_points:
             # If all points are critical, maybe allow sacrificing a simple fortified one as a last resort
            fortified = self._get_fortified_point_ids().intersection(team_point_ids)
            # Exclude bastion points even from this fallback
            eligible_fortified = [pid for pid in fortified if pid not in bastion_points['cores'] and pid not in bastion_points['prongs']]
            if not eligible_fortified:
                return {'success': False, 'reason': 'no non-critical points available to sacrifice'}
            p_to_sac_id = random.choice(list(eligible_fortified))
        else:
            p_to_sac_id = random.choice(non_critical_points)
        
        # Get coords before deletion
        sac_point_coords = self.state['points'][p_to_sac_id].copy()
        
        # Sacrifice the point
        sacrificed_point_data = self._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
        if not sacrificed_point_data:
             return {'success': False, 'reason': 'failed to sacrifice point'}

        # Create the whirlpool
        whirlpool_id = f"wp_{uuid.uuid4().hex[:6]}"
        new_whirlpool = {
            'id': whirlpool_id,
            'teamId': teamId,
            'coords': sac_point_coords,
            'turns_left': 4,
            'strength': 0.05, # pull-in strength per turn
            'swirl': 0.5, # radians per turn
            'radius_sq': (self.state['grid_size'] * 0.3)**2
        }
        
        if 'whirlpools' not in self.state: self.state['whirlpools'] = []
        self.state['whirlpools'].append(new_whirlpool)

        return {
            'success': True, 
            'type': 'create_whirlpool',
            'whirlpool': new_whirlpool,
            'sacrificed_point': sacrificed_point_data
        }

    def sacrifice_action_phase_shift(self, teamId):
        """[SACRIFICE ACTION]: Sacrifice a line to teleport one of its points."""
        team_lines = self.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to sacrifice'}

        # Prioritize sacrificing lines whose points are not part of critical structures
        fortified_point_ids = self._get_fortified_point_ids()
        bastion_point_ids = self._get_bastion_point_ids()
        monolith_point_ids = {pid for m in self.state.get('monoliths', {}).values() for pid in m.get('point_ids', [])}
        nexus_point_ids = {pid for nexus_list in self.state.get('nexuses', {}).values() for nexus in nexus_list for pid in nexus.get('point_ids', [])}
        
        critical_point_ids = fortified_point_ids.union(
            bastion_point_ids['cores'],
            bastion_point_ids['prongs'],
            monolith_point_ids,
            nexus_point_ids
        )

        eligible_lines = [
            line for line in team_lines 
            if line['p1_id'] not in critical_point_ids and line['p2_id'] not in critical_point_ids
        ]

        # As a fallback, allow any line if no "safe" lines are available, but only if the team has more than 2 points to avoid self-destruction
        if not eligible_lines:
            if len(self.get_team_point_ids(teamId)) > 2:
                eligible_lines = team_lines
            else:
                return {'success': False, 'reason': 'no non-critical lines to sacrifice for phase shift'}

        line_to_sac = random.choice(eligible_lines)
        
        # Choose one of the two endpoints to move
        p_to_move_id, _ = random.choice([
            (line_to_sac['p1_id'], line_to_sac['p2_id']),
            (line_to_sac['p2_id'], line_to_sac['p1_id'])
        ])

        point_to_move = self.state['points'][p_to_move_id]
        original_coords = {'x': point_to_move['x'], 'y': point_to_move['y']}

        # Find a new valid location
        new_coords = None
        grid_size = self.state['grid_size']
        for _ in range(25): # Try several times to find a random spot
            candidate_coords = {
                'x': random.randint(0, grid_size - 1),
                'y': random.randint(0, grid_size - 1)
            }
            is_valid, _ = self._is_spawn_location_valid(candidate_coords, teamId, min_dist_sq=1.0)
            if is_valid:
                new_coords = candidate_coords
                break
        
        if not new_coords:
            return {'success': False, 'reason': 'could not find a valid location to phase shift to'}

        # Apply the move
        point_to_move['x'] = new_coords['x']
        point_to_move['y'] = new_coords['y']

        # Sacrifice the line
        self.state['lines'].remove(line_to_sac)
        self.state['shields'].pop(line_to_sac.get('id'), None)

        return {
            'success': True,
            'type': 'phase_shift',
            'moved_point_id': p_to_move_id,
            'original_coords': original_coords,
            'new_coords': new_coords,
            'sacrificed_line': line_to_sac
        }

    def expand_action_spawn_point(self, teamId):
        """[EXPAND ACTION]: Creates a new point near an existing one. A last resort action."""
        team_point_ids = self.get_team_point_ids(teamId)
        if not team_point_ids:
            return {'success': False, 'reason': 'no points to spawn from'}

        # Try a few times to find a valid empty spot
        for _ in range(10):
            p_origin_id = random.choice(team_point_ids)
            p_origin = self.state['points'][p_origin_id]

            # Spawn in a small radius
            angle = random.uniform(0, 2 * math.pi)
            radius = self.state['grid_size'] * random.uniform(0.05, 0.15)
            
            new_x = p_origin['x'] + math.cos(angle) * radius
            new_y = p_origin['y'] + math.sin(angle) * radius
            
            # Clamp to grid and round to integer
            grid_size = self.state['grid_size']
            final_x = round(max(0, min(grid_size - 1, new_x)))
            final_y = round(max(0, min(grid_size - 1, new_y)))

            new_p_coords = {'x': final_x, 'y': final_y}
            is_valid, reason = self._is_spawn_location_valid(new_p_coords, teamId)
            if not is_valid:
                continue

            # We found a valid spawn, create the new point
            new_point_id = f"p_{uuid.uuid4().hex[:6]}"
            new_point = {"x": final_x, "y": final_y, "teamId": teamId, "id": new_point_id}
            self.state['points'][new_point_id] = new_point

            return {'success': True, 'type': 'spawn_point', 'new_point': new_point}

        return {'success': False, 'reason': 'could not find a valid position to spawn'}

    def expand_action_create_orbital(self, teamId):
        """[EXPAND ACTION]: Creates a new orbital structure of points around an existing point."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 5:
            return {'success': False, 'reason': 'not enough points to create an orbital'}

        # Try a few times to find a valid spot
        for _ in range(5):
            p_center_id = random.choice(team_point_ids)
            p_center = self.state['points'][p_center_id]
            
            num_satellites = random.randint(3, 5)
            radius = self.state['grid_size'] * random.uniform(0.15, 0.25)
            angle_offset = random.uniform(0, 2 * math.pi)
            
            new_points_to_create = []
            valid_orbital = True

            for i in range(num_satellites):
                angle = angle_offset + (2 * math.pi * i / num_satellites)
                new_x = p_center['x'] + math.cos(angle) * radius
                new_y = p_center['y'] + math.sin(angle) * radius
                
                # Clamp to grid and round to integer
                grid_size = self.state['grid_size']
                final_x = round(max(0, min(grid_size - 1, new_x)))
                final_y = round(max(0, min(grid_size - 1, new_y)))

                new_p_coords = {'x': final_x, 'y': final_y}
                # Use a larger clearance for orbitals to look good
                is_valid, reason = self._is_spawn_location_valid(new_p_coords, teamId, min_dist_sq=2.0)
                if not is_valid:
                    valid_orbital = False
                    break
                
                # Check proximity to other points in this same orbital creation
                is_too_close_to_sibling = False
                for p_sibling in new_points_to_create:
                    if distance_sq(new_p_coords, p_sibling) < 2.0:
                         is_too_close_to_sibling = True
                         break
                if is_too_close_to_sibling:
                    valid_orbital = False
                    break
                
                new_point_id = f"p_{uuid.uuid4().hex[:6]}"
                new_points_to_create.append({"x": final_x, "y": final_y, "teamId": teamId, "id": new_point_id})
            
            if not valid_orbital:
                continue # Try with another center point

            # If we're here, the orbital is valid. Create points and lines.
            created_points = []
            created_lines = []
            for new_p_data in new_points_to_create:
                self.state['points'][new_p_data['id']] = new_p_data
                created_points.append(new_p_data)

                # Add a line from the center to the new satellite point
                line_id = f"l_{uuid.uuid4().hex[:6]}"
                new_line = {"id": line_id, "p1_id": p_center_id, "p2_id": new_p_data['id'], "teamId": teamId}
                self.state['lines'].append(new_line)
                created_lines.append(new_line)
            
            return {
                'success': True,
                'type': 'create_orbital',
                'center_point_id': p_center_id,
                'new_points': created_points,
                'new_lines': created_lines
            }

        return {'success': False, 'reason': 'could not find a valid position for an orbital'}

    def shield_action_protect_line(self, teamId):
        """[DEFEND ACTION]: Applies a temporary shield to a line, protecting it from attacks."""
        team_lines = self.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to shield'}

        # Find lines that are not already shielded
        unshielded_lines = [l for l in team_lines if l.get('id') not in self.state['shields']]

        if not unshielded_lines:
            return {'success': False, 'reason': 'all lines are already shielded'}
        
        line_to_shield = random.choice(unshielded_lines)
        shield_duration = 3 # in turns
        self.state['shields'][line_to_shield['id']] = shield_duration
        
        return {'success': True, 'type': 'shield_line', 'shielded_line': line_to_shield}

    def expand_action_grow_line(self, teamId):
        """[EXPAND ACTION]: Grows a new short line from an existing point, like a vine."""
        team_lines = self.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to grow from'}

        random.shuffle(team_lines)
        points_map = self.state['points']
        
        for line in team_lines:
            if not (line['p1_id'] in points_map and line['p2_id'] in points_map):
                continue
            
            # Choose a random endpoint to grow from
            p_origin_id, p_other_id = random.choice([(line['p1_id'], line['p2_id']), (line['p2_id'], line['p1_id'])])
            p_origin = points_map[p_origin_id]
            p_other = points_map[p_other_id]

            # Vector from other to origin, defining the line's direction at the origin
            vx = p_origin['x'] - p_other['x']
            vy = p_origin['y'] - p_other['y']

            # Rotate this vector by a random angle. Avoids growing straight back.
            angle = random.uniform(-math.pi * 2/3, math.pi * 2/3) # -120 to +120 degrees
            
            new_vx = vx * math.cos(angle) - vy * math.sin(angle)
            new_vy = vx * math.sin(angle) + vy * math.cos(angle)

            # Normalize the new vector
            mag = math.sqrt(new_vx**2 + new_vy**2)
            if mag == 0: continue # Should not happen if line has length

            # Define the length of the new "vine"
            growth_length = self.state['grid_size'] * random.uniform(0.1, 0.2)
            
            # Calculate new point position
            new_x = p_origin['x'] + (new_vx / mag) * growth_length
            new_y = p_origin['y'] + (new_vy / mag) * growth_length

            # Check if the new point is within the grid boundaries and valid
            grid_size = self.state['grid_size']
            if not (0 <= new_x < grid_size and 0 <= new_y < grid_size):
                continue

            new_point_coords = {"x": round(new_x), "y": round(new_y)}
            is_valid, reason = self._is_spawn_location_valid(new_point_coords, teamId)
            if not is_valid:
                continue

            # We found a valid growth, create the new point and line
            new_point_id = f"p_{uuid.uuid4().hex[:6]}"
            new_point = {**new_point_coords, "teamId": teamId, "id": new_point_id}
            self.state['points'][new_point_id] = new_point

            line_id = f"l_{uuid.uuid4().hex[:6]}"
            new_line = {"id": line_id, "p1_id": p_origin_id, "p2_id": new_point_id, "teamId": teamId}
            self.state['lines'].append(new_line)

            return {'success': True, 'type': 'grow_line', 'new_point': new_point, 'new_line': new_line}

        return {'success': False, 'reason': 'could not find a valid position to grow'}

    def fortify_action_claim_territory(self, teamId):
        """[FORTIFY ACTION]: Find a triangle and claim it as territory."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 3:
            return {'success': False, 'reason': 'not enough points for a triangle'}

        # Build adjacency list for the team's graph using point IDs
        adj = {pid: set() for pid in team_point_ids}
        for line in self.get_team_lines(teamId):
            # Check if points for the line still exist
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])

        # Find all triangles
        all_triangles = set()
        # Sort point ids to have a consistent order for checking i,j,k
        sorted_point_ids = sorted(list(team_point_ids)) 
        for i in sorted_point_ids:
            for j in adj.get(i, set()):
                if j > i:
                    for k in adj.get(j, set()):
                        if k > j and k in adj.get(i, set()):
                            # Found a triangle (i, j, k)
                            all_triangles.add(tuple(sorted((i, j, k))))

        if not all_triangles:
            return {'success': False, 'reason': 'no triangles formed'}

        # Find a triangle that hasn't been claimed yet
        claimed_triangles = set(tuple(sorted(t['point_ids'])) for t in self.state['territories'])
        
        newly_claimable_triangles = list(all_triangles - claimed_triangles)

        if not newly_claimable_triangles:
            return {'success': False, 'reason': 'all triangles already claimed'}
        
        # Claim a random new triangle
        triangle_to_claim = random.choice(newly_claimable_triangles)
        new_territory = {
            'teamId': teamId,
            'point_ids': list(triangle_to_claim)
        }
        self.state['territories'].append(new_territory)
        
        return {'success': True, 'type': 'claim_territory', 'territory': new_territory}

    def fortify_action_form_bastion(self, teamId):
        """[FORTIFY ACTION]: Converts a fortified point and its connections into a defensive bastion."""
        # A bastion must be formed around a point that is already a vertex of a claimed territory.
        fortified_point_ids = self._get_fortified_point_ids()
        if not fortified_point_ids:
            return {'success': False, 'reason': 'no fortified points to build a bastion on'}

        team_point_ids = self.get_team_point_ids(teamId)
        adj = {pid: set() for pid in team_point_ids}
        for line in self.get_team_lines(teamId):
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])
        
        # Get all points that are already part of a bastion to avoid re-using them
        existing_bastion_points = self._get_bastion_point_ids()
        used_points = existing_bastion_points['cores'].union(existing_bastion_points['prongs'])

        possible_bastions = []
        for core_candidate_id in fortified_point_ids:
            # The core must belong to the current team and not be part of an existing bastion
            if core_candidate_id not in team_point_ids or core_candidate_id in used_points:
                continue

            # Find connected points ("prongs") that are NOT fortified and NOT part of another bastion
            prong_candidates = [
                pid for pid in adj.get(core_candidate_id, set())
                if pid not in fortified_point_ids and pid not in used_points
            ]

            # A bastion needs at least 3 prongs
            if len(prong_candidates) >= 3:
                possible_bastions.append({
                    'core_id': core_candidate_id,
                    'prong_ids': prong_candidates
                })

        if not possible_bastions:
            return {'success': False, 'reason': 'no valid bastion formation found'}
        
        chosen_bastion = random.choice(possible_bastions)
        bastion_id = f"b_{uuid.uuid4().hex[:6]}"
        new_bastion = {
            'id': bastion_id,
            'teamId': teamId,
            **chosen_bastion
        }
        self.state['bastions'][bastion_id] = new_bastion

        return {'success': True, 'type': 'form_bastion', 'bastion': new_bastion}

    def fortify_action_form_monolith(self, teamId):
        """[FORTIFY ACTION]: Forms a Monolith from a tall, thin rectangle of points."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 4:
            return {'success': False, 'reason': 'not enough points'}

        points = self.state['points']
        existing_lines = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in self.get_team_lines(teamId)}
        existing_monolith_points = {pid for m in self.state.get('monoliths', {}).values() for pid in m['point_ids']}

        possible_monoliths = []
        for p_ids_tuple in combinations(team_point_ids, 4):
            # Check if any of these points are already part of a monolith
            if any(pid in existing_monolith_points for pid in p_ids_tuple):
                continue
            
            p_list = [points[pid] for pid in p_ids_tuple]
            is_rect, aspect_ratio = is_rectangle(*p_list)

            # Monolith requires a thin rectangle, aspect ratio > 3.0
            if is_rect and aspect_ratio > 3.0:
                # Check for the 4 outer perimeter lines
                all_pairs = list(combinations(p_ids_tuple, 2))
                all_pair_dists = {pair: distance_sq(points[pair[0]], points[pair[1]]) for pair in all_pairs}
                sorted_pairs = sorted(all_pair_dists.keys(), key=lambda pair: all_pair_dists[pair])
                side_pairs = sorted_pairs[0:4]

                if all(tuple(sorted(pair)) in existing_lines for pair in side_pairs):
                    center_x = sum(p['x'] for p in p_list) / 4
                    center_y = sum(p['y'] for p in p_list) / 4
                    possible_monoliths.append({
                        'point_ids': list(p_ids_tuple),
                        'center_coords': {'x': center_x, 'y': center_y}
                    })
        
        if not possible_monoliths:
            return {'success': False, 'reason': 'no valid monolith formation found'}

        chosen_monolith_data = random.choice(possible_monoliths)
        monolith_id = f"m_{uuid.uuid4().hex[:6]}"
        new_monolith = {
            'id': monolith_id,
            'teamId': teamId,
            'point_ids': chosen_monolith_data['point_ids'],
            'center_coords': chosen_monolith_data['center_coords'],
            'charge_counter': 0,
            'charge_interval': 4, # Emits wave every 4 turns
            'wave_radius_sq': (self.state['grid_size'] * 0.3)**2
        }
        
        if 'monoliths' not in self.state: self.state['monoliths'] = {}
        self.state['monoliths'][monolith_id] = new_monolith
        
        return {'success': True, 'type': 'form_monolith', 'monolith': new_monolith}

    def fortify_action_cultivate_heartwood(self, teamId):
        """[FORTIFY ACTION]: Cultivates a Heartwood from a point with many connections."""
        team_point_ids = self.get_team_point_ids(teamId)
        # A heartwood for a team is unique.
        if teamId in self.state.get('heartwoods', {}):
            return {'success': False, 'reason': 'team already has a heartwood'}
        
        HEARTWOOD_MIN_BRANCHES = 5
        
        adj = {pid: set() for pid in team_point_ids}
        for line in self.get_team_lines(teamId):
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])
        
        possible_formations = []
        for center_pid, connections in adj.items():
            if len(connections) >= HEARTWOOD_MIN_BRANCHES:
                # All connected points must also belong to the team (already ensured by get_team_lines)
                possible_formations.append({
                    'center_id': center_pid,
                    'branch_ids': list(connections)
                })

        if not possible_formations:
            return {'success': False, 'reason': f'no point with at least {HEARTWOOD_MIN_BRANCHES} connections found'}
        
        chosen_formation = random.choice(possible_formations)
        center_id = chosen_formation['center_id']
        branch_ids = chosen_formation['branch_ids']
        
        # Get coordinates of center point before deleting it
        center_coords = self.state['points'][center_id].copy()
        
        # --- Sacrifice all points in the formation ---
        all_points_to_sac_ids = [center_id] + branch_ids
        sacrificed_points_data = []
        for pid in all_points_to_sac_ids:
            # Note: _delete_point_and_connections also removes connected lines,
            # so we don't need to worry about them separately.
            sac_data = self._delete_point_and_connections(pid, aggressor_team_id=teamId)
            if sac_data:
                sacrificed_points_data.append(sac_data)

        if not sacrificed_points_data:
            return {'success': False, 'reason': 'failed to sacrifice points for heartwood'}

        # --- Create the Heartwood ---
        heartwood_id = f"hw_{uuid.uuid4().hex[:6]}"
        new_heartwood = {
            'id': heartwood_id,
            'teamId': teamId,
            'center_coords': {'x': center_coords['x'], 'y': center_coords['y']},
            'growth_counter': 0,
            'growth_interval': 3, # spawns a point every 3 turns
        }
        
        if 'heartwoods' not in self.state: self.state['heartwoods'] = {}
        self.state['heartwoods'][teamId] = new_heartwood
        
        return {
            'success': True,
            'type': 'cultivate_heartwood',
            'heartwood': new_heartwood,
            'sacrificed_points': sacrificed_points_data
        }

    def _find_star_formations(self, teamId, min_cycle=5, max_cycle=6):
        """
        Finds "star" formations for a team.
        A star is a central point connected to all points in a cycle of N points.
        Returns a list of dicts, each describing a star formation.
        e.g., [{'center_id': p_id, 'cycle_ids': [p1_id, p2_id, ...]}]
        """
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < min_cycle + 1:
            return []

        adj = {pid: set() for pid in team_point_ids}
        for line in self.get_team_lines(teamId):
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])

        found_stars = []
        
        # Avoid reusing points for multiple stars in one turn
        used_points = set()

        for center_candidate_id in team_point_ids:
            if center_candidate_id in used_points:
                continue
                
            neighbors = list(adj.get(center_candidate_id, set()))
            if len(neighbors) < min_cycle:
                continue

            # Check all combinations of neighbors to form a cycle
            for cycle_len in range(min_cycle, max_cycle + 1):
                if len(neighbors) < cycle_len:
                    continue
                
                for cycle_candidate_ids in combinations(neighbors, cycle_len):
                    # Check if these points form a cycle among themselves.
                    # Build a sub-adjacency list for only the candidates.
                    sub_adj = {pid: [] for pid in cycle_candidate_ids}
                    for i, p_id in enumerate(cycle_candidate_ids):
                        # Check connections within the cycle candidate points
                        for j in range(i + 1, len(cycle_candidate_ids)):
                            other_p_id = cycle_candidate_ids[j]
                            if other_p_id in adj.get(p_id, set()):
                                sub_adj[p_id].append(other_p_id)
                                sub_adj[other_p_id].append(p_id)
                    
                    # Each node in a simple cycle must have exactly 2 neighbors in the cycle.
                    if not all(len(sub_adj[pid]) == 2 for pid in cycle_candidate_ids):
                        continue

                    # We found a valid degree-2 subgraph. Now, confirm it is a single connected cycle
                    # by walking it, not two disjoint cycles (e.g., 2 triangles for N=6).
                    start_node = cycle_candidate_ids[0]
                    ordered_cycle = [start_node]
                    prev_node = start_node
                    curr_node = sub_adj[start_node][0] 
                    is_valid_cycle = True
                    
                    while curr_node != start_node and len(ordered_cycle) < cycle_len:
                        ordered_cycle.append(curr_node)
                        next_node_options = [n for n in sub_adj[curr_node] if n != prev_node]
                        if not next_node_options:
                            is_valid_cycle = False; break
                        prev_node = curr_node
                        curr_node = next_node_options[0]

                    if not is_valid_cycle or len(ordered_cycle) != cycle_len:
                        continue

                    # Check if any points are already used in another star found this turn
                    all_star_points = set(ordered_cycle) | {center_candidate_id}
                    if not used_points.intersection(all_star_points):
                        found_stars.append({
                            'center_id': center_candidate_id,
                            'cycle_ids': ordered_cycle,
                            'all_points': list(all_star_points)
                        })
                        used_points.update(all_star_points)
                        # Break from inner loops to not find smaller stars with the same center
                        break
                if center_candidate_id in used_points:
                    break
        
        return found_stars

    def fortify_action_form_rift_spire(self, teamId):
        """[FORTIFY ACTION]: Forms a Rift Spire from a point that is a vertex of 3 territories."""
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        if len(team_territories) < 3:
            return {'success': False, 'reason': 'not enough claimed territories'}

        # Count how many territories each point belongs to
        point_territory_count = {}
        for territory in team_territories:
            for pid in territory['point_ids']:
                if pid not in self.state['points']: continue
                point_territory_count[pid] = point_territory_count.get(pid, 0) + 1
        
        # Find points that are part of 3 or more territories
        existing_spire_coords = { (s['coords']['x'], s['coords']['y']) for s in self.state.get('rift_spires', {}).values() }

        possible_spires = []
        for pid, count in point_territory_count.items():
            if count >= 3:
                point_coords = self.state['points'][pid]
                if (point_coords['x'], point_coords['y']) not in existing_spire_coords:
                    possible_spires.append(pid)
        
        if not possible_spires:
            return {'success': False, 'reason': 'no point is a vertex of 3+ territories'}

        p_to_sac_id = random.choice(possible_spires)
        sacrificed_point_data = self._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
        
        if not sacrificed_point_data:
            return {'success': False, 'reason': 'failed to sacrifice point for spire'}

        spire_id = f"rs_{uuid.uuid4().hex[:6]}"
        new_spire = {
            'id': spire_id,
            'teamId': teamId,
            'coords': { 'x': sacrificed_point_data['x'], 'y': sacrificed_point_data['y'] },
            'charge': 0,
            'charge_needed': 3 # Takes 3 turns to charge up
        }
        if 'rift_spires' not in self.state: self.state['rift_spires'] = {}
        self.state['rift_spires'][spire_id] = new_spire

        return {
            'success': True,
            'type': 'form_rift_spire',
            'spire': new_spire,
            'sacrificed_point': sacrificed_point_data
        }

    def terraform_action_create_fissure(self, teamId):
        """[TERRAFORM ACTION]: A Rift Spire creates a fissure on the map."""
        team_spires = [s for s in self.state.get('rift_spires', {}).values() if s['teamId'] == teamId and s.get('charge', 0) >= s.get('charge_needed', 3)]
        if not team_spires:
            return {'success': False, 'reason': 'no charged rift spires available'}

        spire = random.choice(team_spires)
        grid_size = self.state['grid_size']
        
        # Create a long fissure, e.g., from one border to another
        borders = [
            {'x': 0, 'y': random.randint(0, grid_size - 1)},
            {'x': grid_size - 1, 'y': random.randint(0, grid_size - 1)},
            {'x': random.randint(0, grid_size - 1), 'y': 0},
            {'x': random.randint(0, grid_size - 1), 'y': grid_size - 1}
        ]
        p1 = random.choice(borders)
        
        opposite_borders = []
        if p1['x'] == 0: opposite_borders.append({'x': grid_size - 1, 'y': random.randint(0, grid_size - 1)})
        if p1['x'] == grid_size - 1: opposite_borders.append({'x': 0, 'y': random.randint(0, grid_size - 1)})
        if p1['y'] == 0: opposite_borders.append({'x': random.randint(0, grid_size - 1), 'y': grid_size - 1})
        if p1['y'] == grid_size - 1: opposite_borders.append({'x': random.randint(0, grid_size - 1), 'y': 0})
        
        p2 = random.choice(opposite_borders) if opposite_borders else random.choice(borders)

        fissure_id = f"f_{uuid.uuid4().hex[:6]}"
        new_fissure = { 'id': fissure_id, 'p1': p1, 'p2': p2, 'turns_left': 8 }
        self.state['fissures'].append(new_fissure)
        
        spire['charge'] = 0 # Reset charge

        return {
            'success': True,
            'type': 'create_fissure',
            'fissure': new_fissure,
            'spire_id': spire['id']
        }

    def fortify_action_build_chronos_spire(self, teamId):
        """[WONDER ACTION]: Build the Chronos Spire."""
        # Check if this team already has a wonder. Limit one per team for now.
        if any(w['teamId'] == teamId for w in self.state.get('wonders', {}).values()):
            return {'success': False, 'reason': 'team already has a wonder'}

        star_formations = self._find_star_formations(teamId)
        if not star_formations:
            return {'success': False, 'reason': 'no star formation found'}

        # Choose a formation to build on
        formation = random.choice(star_formations)
        
        center_point = self.state['points'][formation['center_id']]
        spire_coords = {'x': center_point['x'], 'y': center_point['y']}
        
        # Sacrifice all points in the formation
        points_to_sacrifice = formation['all_points']
        sacrificed_points_data = []
        for pid in points_to_sacrifice:
            sac_data = self._delete_point_and_connections(pid, aggressor_team_id=teamId)
            if sac_data:
                sacrificed_points_data.append(sac_data)
        
        if len(sacrificed_points_data) != len(points_to_sacrifice):
            return {'success': False, 'reason': 'failed to sacrifice all formation points'}
            
        # Create the Wonder
        wonder_id = f"w_{uuid.uuid4().hex[:6]}"
        new_wonder = {
            'id': wonder_id,
            'teamId': teamId,
            'type': 'ChronosSpire',
            'coords': spire_coords,
            'turns_to_victory': 10,
            'creation_turn': self.state['turn']
        }
        
        if 'wonders' not in self.state: self.state['wonders'] = {}
        self.state['wonders'][wonder_id] = new_wonder
        
        return {
            'success': True,
            'type': 'build_chronos_spire',
            'wonder': new_wonder,
            'sacrificed_points_count': len(sacrificed_points_data)
        }

    def _reflect_point(self, point, p1_axis, p2_axis):
        """Reflects a point across the line defined by p1_axis and p2_axis."""
        px, py = point['x'], point['y']
        x1, y1 = p1_axis['x'], p1_axis['y']
        x2, y2 = p2_axis['x'], p2_axis['y']

        # Line equation ax + by + c = 0
        a = y2 - y1
        b = x1 - x2
        
        if a == 0 and b == 0: # The axis points are the same, no line.
            return None

        c = -a * x1 - b * y1
        
        den = a**2 + b**2
        if den == 0: return None
        
        val = -2 * (a * px + b * py + c) / den
        
        rx = px + val * a
        ry = py + val * b
        
        return {'x': rx, 'y': ry}

    def fortify_action_mirror_structure(self, teamId):
        """[FORTIFY ACTION]: Creates a symmetrical pattern by reflecting points."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 3:
            return {'success': False, 'reason': 'not enough points to mirror'}

        # Try a few times to find a good axis and points to mirror
        for _ in range(5):
            # 1. Select two distinct points for the axis of symmetry
            axis_p_ids = random.sample(team_point_ids, 2)
            p_axis1 = self.state['points'][axis_p_ids[0]]
            p_axis2 = self.state['points'][axis_p_ids[1]]

            # Ensure axis points are not too close for stable calculation
            if distance_sq(p_axis1, p_axis2) < (self.state['grid_size'] * 0.1)**2:
                continue

            # 2. Select points to mirror (that are not on the axis)
            other_point_ids = [pid for pid in team_point_ids if pid not in axis_p_ids]
            if not other_point_ids:
                continue

            # Mirror up to 2 points for visual clarity
            num_to_mirror = min(len(other_point_ids), 2)
            points_to_mirror_ids = random.sample(other_point_ids, num_to_mirror)
            
            new_points_to_create = []
            grid_size = self.state['grid_size']

            # 3. Reflect points and check validity
            for pid in points_to_mirror_ids:
                point_to_mirror = self.state['points'][pid]
                reflected_p = self._reflect_point(point_to_mirror, p_axis1, p_axis2)
                
                if not reflected_p: continue

                # Check if the new point is within the grid boundaries
                if not (0 <= reflected_p['x'] < grid_size and 0 <= reflected_p['y'] < grid_size):
                    continue

                # Round to integer coords before checking validity.
                reflected_p_int = {'x': round(reflected_p['x']), 'y': round(reflected_p['y'])}

                is_valid, reason = self._is_spawn_location_valid(reflected_p_int, teamId)
                if not is_valid:
                    continue

                # If valid, add it to the list to be created
                new_point_id = f"p_{uuid.uuid4().hex[:6]}"
                new_points_to_create.append({**reflected_p_int, "teamId": teamId, "id": new_point_id})

            # 4. If we successfully found points to create, do it and return
            if new_points_to_create:
                for p in new_points_to_create:
                    # Coordinates are already rounded integers
                    self.state['points'][p['id']] = p
                
                return {
                    'success': True,
                    'type': 'mirror_structure',
                    'new_points': new_points_to_create,
                    'axis_p1_id': axis_p_ids[0],
                    'axis_p2_id': axis_p_ids[1],
                }

        return {'success': False, 'reason': 'could not find a valid reflection'}

    def fortify_action_create_anchor(self, teamId):
        """[FORTIFY ACTION]: Sacrifice a point to turn another into a gravity well."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 3: # Requires at least 3 points to not cripple the team.
            return {'success': False, 'reason': 'not enough points to create anchor'}

        # Find a point to sacrifice and a point to turn into an anchor
        # Ensure they are not the same point
        p_to_sac_id, p_to_anchor_id = random.sample(team_point_ids, 2)
        
        # 1. Sacrifice the first point using the robust helper
        sacrificed_point_data = self._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
        if not sacrificed_point_data:
             return {'success': False, 'reason': 'failed to sacrifice point'}

        # 2. Create the anchor
        anchor_duration = 5 # turns
        self.state['anchors'][p_to_anchor_id] = {'teamId': teamId, 'turns_left': anchor_duration}

        anchor_point = self.state['points'][p_to_anchor_id]

        return {
            'success': True, 
            'type': 'create_anchor', 
            'anchor_point': anchor_point,
            'sacrificed_point': sacrificed_point_data
        }

    def fight_action_convert_point(self, teamId):
        """[FIGHT ACTION]: Sacrifice a line to convert a nearby enemy point."""
        team_lines = self.get_team_lines(teamId)
        fortified_point_ids = self._get_fortified_point_ids()
        bastion_point_ids = self._get_bastion_point_ids()
        immune_point_ids = fortified_point_ids.union(bastion_point_ids['cores']).union(bastion_point_ids['prongs'])
        enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId and p['id'] not in immune_point_ids]
        points_map = self.state['points']

        if not team_lines or not enemy_points:
            return {'success': False, 'reason': 'no lines to sacrifice or no enemy points'}

        possible_conversions = []
        conversion_range_sq = (self.state['grid_size'] * 0.3)**2

        for line_to_sac in team_lines:
            if line_to_sac['p1_id'] not in points_map or line_to_sac['p2_id'] not in points_map:
                continue
            
            p1 = points_map[line_to_sac['p1_id']]
            p2 = points_map[line_to_sac['p2_id']]
            midpoint = {'x': (p1['x'] + p2['x']) / 2, 'y': (p1['y'] + p2['y']) / 2}

            for enemy_point in enemy_points:
                dist_sq = distance_sq(midpoint, enemy_point)
                if dist_sq < conversion_range_sq:
                    possible_conversions.append({'line': line_to_sac, 'point': enemy_point})

        if not possible_conversions:
            return {'success': False, 'reason': 'no vulnerable enemy points in range'}

        # Choose a random valid conversion and execute it
        chosen_conversion = random.choice(possible_conversions)
        line_to_sac = chosen_conversion['line']
        point_to_convert = chosen_conversion['point']

        # 1. Remove the sacrificed line
        self.state['lines'].remove(line_to_sac)
        self.state['shields'].pop(line_to_sac.get('id'), None)

        # 2. Convert the enemy point
        original_team_id = point_to_convert['teamId']
        original_team_name = self.state['teams'][original_team_id]['name']
        point_to_convert['teamId'] = teamId

        return {
            'success': True,
            'type': 'convert_point',
            'converted_point': point_to_convert,
            'sacrificed_line': line_to_sac,
            'original_team_name': original_team_name
        }

    def fight_action_bastion_pulse(self, teamId):
        """[FIGHT ACTION]: A bastion sacrifices a prong to destroy crossing enemy lines."""
        team_bastions = [b for b in self.state['bastions'].values() if b['teamId'] == teamId]
        if not team_bastions:
            return {'success': False, 'reason': 'no active bastions'}

        # Choose a bastion that has at least one prong to sacrifice
        bastion_to_pulse = random.choice(team_bastions)
        if len(bastion_to_pulse['prong_ids']) == 0:
             return {'success': False, 'reason': 'bastion has no prongs to sacrifice'}

        # 1. Sacrifice a prong point using the robust helper.
        # This also updates the bastion state (removes prong, may dissolve bastion).
        prong_to_sac_id = random.choice(bastion_to_pulse['prong_ids'])
        sacrificed_prong_data = self._delete_point_and_connections(prong_to_sac_id, aggressor_team_id=teamId)

        if not sacrificed_prong_data: # Should not happen, but defensive
            return {'success': False, 'reason': 'selected prong point does not exist'}
        
        # After deletion, bastion might no longer exist in the state, so we get a fresh reference
        current_bastion_state = self.state['bastions'].get(bastion_to_pulse['id'])

        # If bastion was dissolved, we can't pulse. But the sacrifice is already done.
        # This is a fair outcome of the action. The pulse fizzles.
        if not current_bastion_state:
             return {'success': True, 'type': 'bastion_pulse', 'sacrificed_prong': sacrificed_prong_data, 'lines_destroyed': [], 'bastion_id': bastion_to_pulse['id']}

        # 2. Define the bastion's perimeter polygon for checking intersections
        points_map = self.state['points']
        prong_points = [points_map[pid] for pid in current_bastion_state['prong_ids'] if pid in points_map]
        
        if len(prong_points) < 2: # Need at least a line to check against
             return {'success': True, 'type': 'bastion_pulse', 'sacrificed_prong': sacrificed_prong_data, 'lines_destroyed': [], 'bastion_id': bastion_to_pulse['id']}

        # Sort points angularly to form a correct simple polygon
        centroid = {
            'x': sum(p['x'] for p in prong_points) / len(prong_points),
            'y': sum(p['y'] for p in prong_points) / len(prong_points),
        }
        prong_points.sort(key=lambda p: math.atan2(p['y'] - centroid['y'], p['x'] - centroid['x']))

        # 3. Find and destroy intersecting enemy lines
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        lines_destroyed = []
        for enemy_line in enemy_lines:
            if enemy_line['p1_id'] not in points_map or enemy_line['p2_id'] not in points_map:
                continue
            
            ep1 = points_map[enemy_line['p1_id']]
            ep2 = points_map[enemy_line['p2_id']]

            # Check for intersection with any segment of the bastion's perimeter
            for i in range(len(prong_points)):
                perimeter_p1 = prong_points[i]
                perimeter_p2 = prong_points[(i + 1) % len(prong_points)]
                if segments_intersect(ep1, ep2, perimeter_p1, perimeter_p2):
                    lines_destroyed.append(enemy_line)
                    break # Don't need to check other segments for this line

        # 4. Remove the destroyed lines
        for l in lines_destroyed:
            if l in self.state['lines']:
                self.state['lines'].remove(l)
                self.state['shields'].pop(l.get('id'), None)
        
        return {
            'success': True,
            'type': 'bastion_pulse',
            'sacrificed_prong': sacrificed_prong_data,
            'lines_destroyed': lines_destroyed,
            'bastion_id': bastion_to_pulse['id']
        }

    def fight_action_sentry_zap(self, teamId):
        """[FIGHT ACTION]: A sentry fires a short beam to destroy an enemy point."""
        team_sentries = self.state.get('sentries', {}).get(teamId, [])
        if not team_sentries:
            return {'success': False, 'reason': 'no active sentries'}

        sentry = random.choice(team_sentries)
        points = self.state['points']
        
        p_eye = points[sentry['eye_id']]
        p_post1 = points[sentry['post1_id']]
        
        # Vector of the sentry's alignment
        vx = p_post1['x'] - p_eye['x']
        vy = p_post1['y'] - p_eye['y']
        
        # Perpendicular vector (for the zap)
        zap_vx, zap_vy = -vy, vx
        
        zap_range_sq = (self.state['grid_size'] * 0.35)**2
        
        # Check both directions of the perpendicular
        possible_targets = []
        for direction in [1, -1]:
            zap_dir_x = zap_vx * direction
            zap_dir_y = zap_vy * direction
            
            # Find all enemy points
            enemy_points = [p for p in points.values() if p['teamId'] != teamId]
            
            for enemy_p in enemy_points:
                # Vector from eye to enemy
                enemy_vx = enemy_p['x'] - p_eye['x']
                enemy_vy = enemy_p['y'] - p_eye['y']
                
                # Check if enemy is within range
                if (enemy_vx**2 + enemy_vy**2) > zap_range_sq:
                    continue

                # Check for near-collinearity with the zap vector using cross product
                cross_product = zap_dir_x * enemy_vy - zap_dir_y * enemy_vx
                
                # Also check dot product to ensure it's in the correct direction
                dot_product = zap_dir_x * enemy_vx + zap_dir_y * enemy_vy

                # Allow for a small tolerance: point can be within 0.5 units of the ray
                # Distance from point to line is |cross_product| / |zap_dir|
                mag_zap_dir_sq = zap_dir_x**2 + zap_dir_y**2
                if mag_zap_dir_sq == 0: continue
                
                distance_from_ray_sq = cross_product**2 / mag_zap_dir_sq
                
                if distance_from_ray_sq < 0.5**2 and dot_product > 0:
                    possible_targets.append(enemy_p)

        if not possible_targets:
            return {'success': False, 'reason': 'no enemy point in zap path'}
            
        # Find the closest target among the possibilities
        target_point = min(possible_targets, key=lambda p: distance_sq(p_eye, p))

        # Destroy the point and all its connections
        destroyed_point_data = self._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
        if not destroyed_point_data:
            return {'success': False, 'reason': 'failed to destroy target point'}

        # Create data for the visual effect
        zap_ray_p1 = p_eye
        # For visualization, find where the ray to the target would hit a border
        zap_ray_end = self._get_extended_border_point(p_eye, target_point)
        if not zap_ray_end: # Should not happen if target is found
            zap_ray_end = target_point
        
        return {
            'success': True,
            'type': 'sentry_zap',
            'destroyed_point': destroyed_point_data,
            'sentry_points': [sentry['eye_id'], sentry['post1_id'], sentry['post2_id']],
            'attack_ray': {'p1': zap_ray_p1, 'p2': zap_ray_end}
        }

    def fight_action_chain_lightning(self, teamId):
        """[FIGHT ACTION]: A Conduit sacrifices an internal point to strike a nearby enemy point."""
        team_conduits = self.state.get('conduits', {}).get(teamId, [])
        # Find conduits that have at least one internal point to sacrifice
        valid_conduits = [c for c in team_conduits if c.get('internal_point_ids')]
        if not valid_conduits:
            return {'success': False, 'reason': 'no conduits with sacrificial points'}

        # 1. Choose a conduit and a point to sacrifice
        chosen_conduit = random.choice(valid_conduits)
        p_to_sac_id = random.choice(chosen_conduit['internal_point_ids'])

        # 2. Sacrifice the point. Its data is returned.
        sacrificed_point_data = self._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
        if not sacrificed_point_data:
             return {'success': False, 'reason': 'failed to sacrifice conduit point'}

        # 3. Find the closest enemy point to one of the conduit's endpoints
        endpoint1_id = chosen_conduit['endpoint1_id']
        endpoint2_id = chosen_conduit['endpoint2_id']
        
        # Check if endpoints still exist after the sacrifice cascade
        if endpoint1_id not in self.state['points'] or endpoint2_id not in self.state['points']:
            # The action succeeded (point was sacrificed) but fizzled.
            return {
                'success': True, 'type': 'chain_lightning',
                'sacrificed_point': sacrificed_point_data, 'destroyed_point': None,
                'conduit_point_ids': chosen_conduit['point_ids']
            }

        endpoint1 = self.state['points'][endpoint1_id]
        endpoint2 = self.state['points'][endpoint2_id]
        enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId]

        if not enemy_points:
            return {
                'success': True, 'type': 'chain_lightning',
                'sacrificed_point': sacrificed_point_data, 'destroyed_point': None,
                'conduit_point_ids': chosen_conduit['point_ids']
            }

        # Find the single closest enemy to either endpoint
        closest_enemy = min(
            enemy_points,
            key=lambda p: min(distance_sq(endpoint1, p), distance_sq(endpoint2, p))
        )
        
        # 4. Destroy the target
        destroyed_point_data = self._delete_point_and_connections(closest_enemy['id'], aggressor_team_id=teamId)
        if not destroyed_point_data:
            return {'success': False, 'reason': 'failed to destroy target point'}
            
        return {
            'success': True,
            'type': 'chain_lightning',
            'sacrificed_point': sacrificed_point_data,
            'destroyed_point': destroyed_point_data,
            'conduit_point_ids': chosen_conduit['point_ids']
        }

    def fight_action_pincer_attack(self, teamId):
        """[FIGHT ACTION]: Two points flank and destroy an enemy point."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 2:
            return {'success': False, 'reason': 'not enough points for pincer'}

        # Get a list of immune point IDs to exclude from targeting
        fortified_point_ids = self._get_fortified_point_ids()
        bastion_point_ids = self._get_bastion_point_ids()
        immune_point_ids = fortified_point_ids.union(bastion_point_ids['cores']).union(bastion_point_ids['prongs'])
        
        enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId and p['id'] not in immune_point_ids]
        if not enemy_points:
            return {'success': False, 'reason': 'no vulnerable enemy points'}

        points_map = self.state['points']
        possible_pincers = []
        max_range_sq = (self.state['grid_size'] * 0.4)**2 # Max range of attack
        pincer_angle_threshold = -0.866 # cos(150 deg), angle must be > 150 deg

        for p1_id, p2_id in combinations(team_point_ids, 2):
            p1 = points_map[p1_id]
            p2 = points_map[p2_id]

            for ep in enemy_points:
                # Basic range check to reduce calculations
                if distance_sq(p1, ep) > max_range_sq or distance_sq(p2, ep) > max_range_sq:
                    continue

                # Vector from enemy point to p1 and p2
                v1 = {'x': p1['x'] - ep['x'], 'y': p1['y'] - ep['y']}
                v2 = {'x': p2['x'] - ep['x'], 'y': p2['y'] - ep['y']}

                mag1_sq = v1['x']**2 + v1['y']**2
                mag2_sq = v2['x']**2 + v2['y']**2

                if mag1_sq < 0.1 or mag2_sq < 0.1: # Avoid division by zero / same point
                    continue
                
                # Dot product
                dot_product = v1['x'] * v2['x'] + v1['y'] * v2['y']
                
                # Cosine of the angle p1-ep-p2
                cos_theta = dot_product / (math.sqrt(mag1_sq) * math.sqrt(mag2_sq))

                if cos_theta < pincer_angle_threshold:
                    possible_pincers.append({
                        'pincer_p1_id': p1_id,
                        'pincer_p2_id': p2_id,
                        'target_point': ep
                    })
        
        if not possible_pincers:
            return {'success': False, 'reason': 'no pincer formation found'}

        chosen_pincer = random.choice(possible_pincers)
        target_point = chosen_pincer['target_point']

        destroyed_point_data = self._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
        if not destroyed_point_data:
            return {'success': False, 'reason': 'failed to destroy target point'}
        
        return {
            'success': True,
            'type': 'pincer_attack',
            'destroyed_point': destroyed_point_data,
            'attacker_p1_id': chosen_pincer['pincer_p1_id'],
            'attacker_p2_id': chosen_pincer['pincer_p2_id'],
        }

    def fight_action_territory_strike(self, teamId):
        """[FIGHT ACTION]: Launches an attack from a large territory."""
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        if not team_territories:
            return {'success': False, 'reason': 'no territories'}

        points_map = self.state['points']
        
        # Find large territories
        MIN_AREA = 10.0 # Define a minimum area for a territory to be able to strike
        large_territories = []
        for territory in team_territories:
            p_ids = territory['point_ids']
            if not all(pid in points_map for pid in p_ids):
                continue
            
            triangle_points = [points_map[pid] for pid in p_ids]
            if len(triangle_points) == 3:
                area = self._polygon_area(triangle_points)
                if area >= MIN_AREA:
                    large_territories.append(territory)
        
        if not large_territories:
            return {'success': False, 'reason': f'no territories with area >= {MIN_AREA}'}

        # Find enemy points to target
        immune_point_ids = self._get_fortified_point_ids().union(self._get_bastion_point_ids()['cores']).union(self._get_bastion_point_ids()['prongs'])
        enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId and p['id'] not in immune_point_ids]
        if not enemy_points:
            return {'success': False, 'reason': 'no vulnerable enemy points'}

        # Find the best strike (closest enemy to a territory centroid)
        best_strike = None
        min_dist_sq = float('inf')

        for territory in large_territories:
            p_ids = territory['point_ids']
            triangle_points = [points_map[pid] for pid in p_ids]
            centroid = self._triangle_centroid(triangle_points)
            
            for ep in enemy_points:
                dist_sq = distance_sq(centroid, ep)
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    best_strike = {'territory': territory, 'target': ep, 'centroid': centroid}
        
        if not best_strike:
            return {'success': False, 'reason': 'no target found'}

        target_point = best_strike['target']
        centroid = best_strike['centroid']

        destroyed_point_data = self._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
        if not destroyed_point_data:
            return {'success': False, 'reason': 'failed to destroy target point'}
        
        return {
            'success': True,
            'type': 'territory_strike',
            'destroyed_point': destroyed_point_data,
            'territory_point_ids': best_strike['territory']['point_ids'],
            'attack_ray': {'p1': centroid, 'p2': target_point}
        }

    def fight_action_refraction_beam(self, teamId):
        """[FIGHT ACTION]: Uses a Prism to refract an attack beam."""
        team_prisms = self.state.get('prisms', {}).get(teamId, [])
        if not team_prisms:
            return {'success': False, 'reason': 'no active prisms'}
        
        points = self.state['points']
        
        # All lines for this team that could be a "source beam"
        # Exclude lines that are part of any prism for simplicity.
        prism_point_ids = set()
        for p in team_prisms:
            prism_point_ids.update(p['all_point_ids'])
        
        source_lines = [l for l in self.get_team_lines(teamId) if l['p1_id'] not in prism_point_ids and l['p2_id'] not in prism_point_ids]
        if not source_lines:
            return {'success': False, 'reason': 'no valid source lines for refraction'}

        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        if not enemy_lines:
            return {'success': False, 'reason': 'no enemy lines to target'}
        
        # Try a few combinations of prisms and source lines
        for _ in range(10):
            prism = random.choice(team_prisms)
            source_line = random.choice(source_lines)

            # 1. Create the initial attack ray from the source line
            if source_line['p1_id'] not in points or source_line['p2_id'] not in points: continue
            
            # Choose a random direction for the source ray
            ls1, ls2 = random.choice([(points[source_line['p1_id']], points[source_line['p2_id']]), (points[source_line['p2_id']], points[source_line['p1_id']])])
            
            source_ray_end = self._get_extended_border_point(ls1, ls2)
            if not source_ray_end: continue
            source_ray = {'p1': ls2, 'p2': source_ray_end}

            # 2. Find intersection with the prism's shared edge
            if prism['shared_p1_id'] not in points or prism['shared_p2_id'] not in points: continue
            prism_edge_p1 = points[prism['shared_p1_id']]
            prism_edge_p2 = points[prism['shared_p2_id']]

            intersection_point = get_segment_intersection_point(source_ray['p1'], source_ray['p2'], prism_edge_p1, prism_edge_p2)
            if not intersection_point:
                continue # This combo doesn't work, try another

            # 3. Create refracted rays and check for hits
            # Vector for the shared edge
            edge_vx = prism_edge_p2['x'] - prism_edge_p1['x']
            edge_vy = prism_edge_p2['y'] - prism_edge_p1['y']
            
            # Perpendicular vectors (the two possible directions for the beam)
            perp_vectors = [(-edge_vy, edge_vx), (edge_vy, -edge_vx)]

            for pvx, pvy in perp_vectors:
                mag = math.sqrt(pvx**2 + pvy**2)
                if mag == 0: continue
                
                # Create a point far along the refracted ray to define it
                refracted_end_dummy = {'x': intersection_point['x'] + pvx/mag, 'y': intersection_point['y'] + pvy/mag}
                refracted_ray_end = self._get_extended_border_point(intersection_point, refracted_end_dummy)
                if not refracted_ray_end: continue
                
                refracted_ray = {'p1': intersection_point, 'p2': refracted_ray_end}

                # Check this ray against all enemy lines
                for enemy_line in enemy_lines:
                    if enemy_line['p1_id'] not in points or enemy_line['p2_id'] not in points: continue
                    ep1 = points[enemy_line['p1_id']]
                    ep2 = points[enemy_line['p2_id']]

                    # This special attack ignores shields but not bastions
                    bastion_line_ids = self._get_bastion_line_ids()
                    if enemy_line.get('id') in bastion_line_ids:
                        continue

                    if segments_intersect(refracted_ray['p1'], refracted_ray['p2'], ep1, ep2):
                        # We have a successful hit!
                        self.state['lines'].remove(enemy_line)
                        self.state['shields'].pop(enemy_line.get('id'), None)
                        
                        return {
                            'success': True,
                            'type': 'refraction_beam',
                            'destroyed_line': enemy_line,
                            'source_ray': source_ray,
                            'refracted_ray': refracted_ray,
                            'prism_point_ids': prism['all_point_ids']
                        }
        
        # If loop finishes without a successful hit
        return {'success': False, 'reason': 'no refraction path found to a target'}

    def fight_action_launch_payload(self, teamId):
        """[FIGHT ACTION]: A Trebuchet launches a payload to destroy a high-value enemy point."""
        team_trebuchets = self.state.get('trebuchets', {}).get(teamId, [])
        if not team_trebuchets:
            return {'success': False, 'reason': 'no active trebuchets'}

        # Find all possible high-value enemy targets
        all_enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId]
        
        # Get IDs of special points for easier lookup
        fortified_ids = self._get_fortified_point_ids()
        bastion_cores = self._get_bastion_point_ids()['cores']
        monolith_point_ids = {pid for m in self.state.get('monoliths', {}).values() for pid in m['point_ids']}
        
        possible_targets = [
            p for p in all_enemy_points if
            p['id'] in fortified_ids or
            p['id'] in bastion_cores or
            p['id'] in monolith_point_ids
        ]
        
        if not possible_targets:
            return {'success': False, 'reason': 'no high-value enemy targets available'}
        
        trebuchet = random.choice(team_trebuchets)
        target_point = random.choice(possible_targets)
        
        # Destroy the target point and all its connections
        destroyed_point_data = self._delete_point_and_connections(target_point['id'])
        if not destroyed_point_data:
            return {'success': False, 'reason': 'failed to destroy target point'}
            
        return {
            'success': True,
            'type': 'launch_payload',
            'trebuchet_points': trebuchet['point_ids'],
            'launch_point_id': trebuchet['apex_id'],
            'destroyed_point': destroyed_point_data
        }

    def _update_nexuses_for_team(self, teamId):
        """Checks for Nexus formations (a square of points with outer lines and one diagonal)."""
        if 'nexuses' not in self.state: self.state['nexuses'] = {}
        self.state['nexuses'][teamId] = [] # Recalculate each time

        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 4:
            return

        points = self.state['points']
        existing_lines = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in self.get_team_lines(teamId)}

        for p_ids_tuple in combinations(team_point_ids, 4):
            # Ensure all points still exist before lookup
            if not all(pid in points for pid in p_ids_tuple): continue
            
            p_list = [points[pid] for pid in p_ids_tuple]
            
            is_rect, aspect_ratio = is_rectangle(*p_list)
            # A Nexus requires a square, which is a rectangle with aspect ratio ~1.0
            if is_rect and abs(aspect_ratio - 1.0) < 0.05:
                # We found a square. Now check for lines.
                # The 4 shortest distances are sides, 2 longest are diagonals.
                
                all_pairs = list(combinations(p_ids_tuple, 2))
                all_pair_dists = {pair: distance_sq(points[pair[0]], points[pair[1]]) for pair in all_pairs}
                
                # Sort pairs by distance
                sorted_pairs = sorted(all_pair_dists.keys(), key=lambda pair: all_pair_dists[pair])
                
                side_pairs = sorted_pairs[0:4]
                diag_pairs = sorted_pairs[4:6]

                # Check if all 4 side lines exist
                num_side_lines = sum(1 for p1_id, p2_id in side_pairs if tuple(sorted((p1_id, p2_id))) in existing_lines)
                if num_side_lines < 4:
                    continue

                # Check if at least one diagonal line exists
                has_diagonal = any(tuple(sorted((p1_id, p2_id))) in existing_lines for p1_id, p2_id in diag_pairs)
                
                if has_diagonal:
                    # This is a valid Nexus.
                    center_x = sum(p['x'] for p in p_list) / 4
                    center_y = sum(p['y'] for p in p_list) / 4
                    
                    self.state['nexuses'][teamId].append({
                        'point_ids': list(p_ids_tuple),
                        'center': {'x': center_x, 'y': center_y}
                    })

    def rune_action_shoot_bisector(self, teamId):
        """[RUNE ACTION]: Fires a powerful beam from a V-Rune."""
        active_v_runes = self.state.get('runes', {}).get(teamId, {}).get('v_shape', [])
        if not active_v_runes:
            return {'success': False, 'reason': 'no active V-runes'}

        rune = random.choice(active_v_runes)
        points = self.state['points']
        
        p_vertex = points[rune['vertex_id']]
        p_leg1 = points[rune['leg1_id']]
        p_leg2 = points[rune['leg2_id']]
        
        # Calculate bisector vector
        v1 = {'x': p_leg1['x'] - p_vertex['x'], 'y': p_leg1['y'] - p_vertex['y']}
        v2 = {'x': p_leg2['x'] - p_vertex['x'], 'y': p_leg2['y'] - p_vertex['y']}

        # Normalize vectors
        mag1 = math.sqrt(v1['x']**2 + v1['y']**2)
        mag2 = math.sqrt(v2['x']**2 + v2['y']**2)
        
        if mag1 == 0 or mag2 == 0:
            return {'success': False, 'reason': 'invalid V-rune geometry'}

        v1_norm = {'x': v1['x']/mag1, 'y': v1['y']/mag1}
        v2_norm = {'x': v2['x']/mag2, 'y': v2['y']/mag2}
        
        # Bisector direction is the sum of normalized vectors
        bisector_v = {'x': v1_norm['x'] + v2_norm['x'], 'y': v1_norm['y'] + v2_norm['y']}

        # Normalize bisector vector
        mag_b = math.sqrt(bisector_v['x']**2 + bisector_v['y']**2)
        if mag_b == 0:
            return {'success': False, 'reason': 'V-rune legs are opposing'}

        # Create a "dummy" point far along the bisector vector to define the attack ray
        p_end = {'x': p_vertex['x'] + bisector_v['x']/mag_b, 'y': p_vertex['y'] + bisector_v['y']/mag_b}
        
        border_point = self._get_extended_border_point(p_vertex, p_end)
        if not border_point:
            return {'success': False, 'reason': 'bisector attack does not hit border'}
        
        attack_ray_p1 = p_vertex
        attack_ray_p2 = border_point

        # Find first enemy line intersected by this ray
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        intersected_lines = []
        for line in enemy_lines:
            if line['p1_id'] not in points or line['p2_id'] not in points: continue
            ep1 = points[line['p1_id']]
            ep2 = points[line['p2_id']]
            if segments_intersect(attack_ray_p1, attack_ray_p2, ep1, ep2):
                intersected_lines.append(line)

        if not intersected_lines:
            return {'success': False, 'reason': 'no target in bisector path'}

        target_line = random.choice(intersected_lines)
        
        # This special attack does not bypass shields by default.
        # However, it CAN destroy bastion lines, making it a valuable counter.
        if target_line.get('id') in self.state['shields']:
            return {'success': False, 'reason': 'target is shielded'}

        self.state['lines'].remove(target_line)
        self.state['shields'].pop(target_line.get('id'), None)

        return {
            'success': True,
            'type': 'rune_shoot_bisector',
            'destroyed_line': target_line,
            'attack_ray': {'p1': attack_ray_p1, 'p2': attack_ray_p2},
            'rune_points': [rune['vertex_id'], rune['leg1_id'], rune['leg2_id']]
        }

    def _choose_action_for_team(self, teamId, exclude_actions=None):
        """Intelligently chooses an action for a team, excluding any that have already failed this turn."""
        if exclude_actions is None:
            exclude_actions = []

        team_trait = self.state['teams'][teamId].get('trait', 'Balanced')
        team_point_ids = self.get_team_point_ids(teamId)
        team_lines = self.get_team_lines(teamId)
        
        action_map = {
            'expand_add': self.expand_action_add_line,
            'expand_extend': self.expand_action_extend_line,
            'expand_grow': self.expand_action_grow_line,
            'expand_fracture': self.expand_action_fracture_line,
            'expand_spawn': self.expand_action_spawn_point,
            'expand_orbital': self.expand_action_create_orbital,
            'fight_attack': self.fight_action_attack_line,
            'fight_convert': self.fight_action_convert_point,
            'fight_pincer_attack': self.fight_action_pincer_attack,
            'fight_territory_strike': self.fight_action_territory_strike,
            'fight_bastion_pulse': self.fight_action_bastion_pulse,
            'fight_chain_lightning': self.fight_action_chain_lightning,
            'fight_refraction_beam': self.fight_action_refraction_beam,
            'fight_launch_payload': self.fight_action_launch_payload,
            'fortify_claim': self.fortify_action_claim_territory,
            'fortify_anchor': self.fortify_action_create_anchor,
            'fortify_mirror': self.fortify_action_mirror_structure,
            'fortify_form_bastion': self.fortify_action_form_bastion,
            'fortify_form_monolith': self.fortify_action_form_monolith,
            'fortify_cultivate_heartwood': self.fortify_action_cultivate_heartwood,
            'fortify_form_rift_spire': self.fortify_action_form_rift_spire,
            'terraform_create_fissure': self.terraform_action_create_fissure,
            'fortify_build_wonder': self.fortify_action_build_chronos_spire,
            'sacrifice_nova': self.sacrifice_action_nova_burst,
            'sacrifice_whirlpool': self.sacrifice_action_create_whirlpool,
            'sacrifice_phase_shift': self.sacrifice_action_phase_shift,
            'defend_shield': self.shield_action_protect_line,
            'rune_shoot_bisector': self.rune_action_shoot_bisector,
            'fight_sentry_zap': self.fight_action_sentry_zap,
        }

        # --- Evaluate possible actions based on game state and exclusion list ---
        possible_actions = []
        action_preconditions = {
            'fight_sentry_zap': bool(self.state.get('sentries', {}).get(teamId, [])),
            'fight_chain_lightning': any(c.get('internal_point_ids') for c in self.state.get('conduits', {}).get(teamId, [])),
            'fight_refraction_beam': bool(self.state.get('prisms', {}).get(teamId, [])),
            'fight_launch_payload': bool(self.state.get('trebuchets', {}).get(teamId, [])),
            'expand_add': len(team_point_ids) >= 2,
            'expand_extend': bool(team_lines),
            'expand_grow': bool(team_lines),
            'expand_fracture': any(distance_sq(self.state['points'][l['p1_id']], self.state['points'][l['p2_id']]) >= 4.0 for l in team_lines if l['p1_id'] in self.state['points'] and l['p2_id'] in self.state['points']),
            'expand_spawn': len(team_point_ids) > 0,
            'expand_orbital': len(team_point_ids) >= 5,
            'fight_attack': bool(team_lines) and any(l['teamId'] != teamId for l in self.state['lines']),
            'fight_convert': bool(team_lines) and any(p['teamId'] != teamId for p in self.state['points'].values()),
            'fight_pincer_attack': len(team_point_ids) >= 2 and any(p['teamId'] != teamId for p in self.state['points'].values()),
            'fight_territory_strike': len([t for t in self.state.get('territories', []) if t['teamId'] == teamId]) > 0,
            'fight_bastion_pulse': any(b['teamId'] == teamId for b in self.state.get('bastions', {}).values()),
            'defend_shield': any(l.get('id') not in self.state['shields'] for l in team_lines),
            'fortify_claim': len(team_point_ids) >= 3,
            'fortify_anchor': len(team_point_ids) >= 3,
            'fortify_mirror': len(team_point_ids) >= 3,
            'fortify_form_bastion': bool(self._get_fortified_point_ids().intersection(team_point_ids)), # Team has at least one of its own fortified points
            'fortify_form_monolith': len(team_point_ids) >= 4,
            'fortify_cultivate_heartwood': len(team_point_ids) >= 6 and teamId not in self.state.get('heartwoods', {}),
            'fortify_form_rift_spire': len([t for t in self.state.get('territories', []) if t['teamId'] == teamId]) >= 3,
            'terraform_create_fissure': any(s['teamId'] == teamId and s.get('charge', 0) >= s.get('charge_needed', 3) for s in self.state.get('rift_spires', {}).values()),
            'fortify_build_wonder': len(team_point_ids) >= 6 and not any(w['teamId'] == teamId for w in self.state.get('wonders', {}).values()),
            'sacrifice_nova': len(team_point_ids) > 2,
            'sacrifice_whirlpool': len(team_point_ids) > 1,
            'sacrifice_phase_shift': bool(team_lines),
            'rune_shoot_bisector': bool(self.state.get('runes', {}).get(teamId, {}).get('v_shape', [])),
        }

        for name, is_possible in action_preconditions.items():
            if name not in exclude_actions and is_possible:
                possible_actions.append(name)
        
        if not possible_actions:
            return None, None

        # --- Apply trait-based weights to the *possible* actions ---
        base_weights = {
            'expand_add': 10, 'expand_extend': 8, 'expand_grow': 12, 'expand_fracture': 10, 'expand_spawn': 1, # Low weight, last resort
            'expand_orbital': 7,
            'fight_attack': 10, 'fight_convert': 8, 'fight_pincer_attack': 12, 'fight_territory_strike': 15, 'fight_bastion_pulse': 15, 'fight_sentry_zap': 20, 'fight_chain_lightning': 18, 'fight_refraction_beam': 22, 'fight_launch_payload': 25,
            'fortify_claim': 8, 'fortify_anchor': 5, 'fortify_mirror': 6, 'fortify_form_bastion': 7, 'fortify_form_monolith': 14, 'fortify_cultivate_heartwood': 20, 'fortify_form_rift_spire': 18, 'terraform_create_fissure': 25, 'fortify_build_wonder': 100,
            'sacrifice_nova': 3, 'sacrifice_whirlpool': 6, 'defend_shield': 8,
            'rune_shoot_bisector': 25, # High value special action
        }
        trait_multipliers = {
            'Aggressive': {'fight_attack': 2.5, 'fight_convert': 2.0, 'fight_pincer_attack': 2.5, 'fight_territory_strike': 2.0, 'sacrifice_nova': 1.5, 'defend_shield': 0.5, 'rune_shoot_bisector': 1.5, 'fight_bastion_pulse': 2.0, 'fight_sentry_zap': 2.5, 'fight_chain_lightning': 2.2, 'fight_refraction_beam': 2.5, 'fight_launch_payload': 3.0},
            'Expansive':  {'expand_add': 2.0, 'expand_extend': 1.5, 'expand_grow': 2.5, 'expand_fracture': 2.0, 'fortify_claim': 0.5, 'fortify_mirror': 2.0, 'expand_orbital': 2.5, 'fortify_cultivate_heartwood': 1.5},
            'Defensive':  {'defend_shield': 3.0, 'fortify_claim': 2.0, 'fortify_anchor': 1.5, 'fight_attack': 0.5, 'expand_grow': 0.5, 'fortify_form_bastion': 3.0, 'fortify_form_monolith': 2.5, 'fortify_cultivate_heartwood': 2.5},
            'Balanced':   {}
        }
        multipliers = trait_multipliers.get(team_trait, {})
        
        action_weights = []
        for action_name in possible_actions:
            weight = base_weights.get(action_name, 1)
            multiplier = multipliers.get(action_name, 1.0)
            action_weights.append(weight * multiplier)
            
        # Use random.choices to pick an action based on the calculated weights
        chosen_action_name = random.choices(possible_actions, weights=action_weights, k=1)[0]
        return chosen_action_name, action_map[chosen_action_name]


    def restart_game(self):
        """Restarts the game from its initial configuration."""
        if not self.state.get('initial_state'):
            return {"error": "No initial state saved to restart from."}
        
        initial_config = self.state['initial_state']
        
        # We need to create fresh copies of mutable objects
        teams = {tid: t.copy() for tid, t in initial_config['teams'].items()}
        points = [p.copy() for p in initial_config['points']]

        self.start_game(
            teams=teams,
            points=points,
            max_turns=initial_config['max_turns'],
            grid_size=initial_config['grid_size']
        )
        return self.get_state()

    def _start_new_turn(self):
        """Performs start-of-turn maintenance and sets up the action queue for the new turn."""
        self.state['turn'] += 1
        self.state['action_in_turn'] = 0
        self.state['last_action_details'] = {} # Clear last action from previous turn
        self.state['new_turn_events'] = [] # Clear events from previous turn
        
        # --- Start of Turn Maintenance ---
        # 1. Manage shields
        expired_shields = [lid for lid, turns in self.state['shields'].items() if turns - 1 <= 0]
        self.state['shields'] = {lid: turns - 1 for lid, turns in self.state['shields'].items() if turns - 1 > 0}

        # 2. Process anchors
        expired_anchors = []
        pull_strength = 0.2
        grid_size = self.state['grid_size']
        for anchor_pid, anchor_data in list(self.state['anchors'].items()):
            if anchor_pid not in self.state['points']:
                expired_anchors.append(anchor_pid)
                continue
            
            anchor_point = self.state['points'][anchor_pid]
            anchor_radius_sq = (grid_size * 0.4)**2
            for point in self.state['points'].values():
                if point['teamId'] != anchor_data['teamId'] and distance_sq(anchor_point, point) < anchor_radius_sq:
                    dx, dy = anchor_point['x'] - point['x'], anchor_point['y'] - point['y']
                    # Apply pull and round to keep coordinates as integers
                    new_x = point['x'] + dx * pull_strength
                    new_y = point['y'] + dy * pull_strength
                    point['x'] = round(max(0, min(grid_size - 1, new_x)))
                    point['y'] = round(max(0, min(grid_size - 1, new_y)))

            anchor_data['turns_left'] -= 1
            if anchor_data['turns_left'] <= 0:
                expired_anchors.append(anchor_pid)
        for anchor_pid in expired_anchors:
            if anchor_pid in self.state['anchors']: del self.state['anchors'][anchor_pid]
            
        # 3. Process Heartwoods
        if self.state.get('heartwoods'):
            for teamId, heartwood in self.state['heartwoods'].items():
                heartwood['growth_counter'] += 1
                if heartwood['growth_counter'] >= heartwood['growth_interval']:
                    heartwood['growth_counter'] = 0
                    
                    # Spawn a new point.
                    for _ in range(10): # Try a few times to find a spot
                        angle = random.uniform(0, 2 * math.pi)
                        radius = self.state['grid_size'] * random.uniform(0.05, 0.15)
                        
                        new_x = heartwood['center_coords']['x'] + math.cos(angle) * radius
                        new_y = heartwood['center_coords']['y'] + math.sin(angle) * radius
                        
                        grid_size = self.state['grid_size']
                        final_x = round(max(0, min(grid_size - 1, new_x)))
                        final_y = round(max(0, min(grid_size - 1, new_y)))
                        
                        new_p_coords = {'x': final_x, 'y': final_y}
                        is_valid, reason = self._is_spawn_location_valid(new_p_coords, teamId)
                        if not is_valid: continue

                        # Found a valid spot
                        new_point_id = f"p_{uuid.uuid4().hex[:6]}"
                        new_point = {"x": final_x, "y": final_y, "teamId": teamId, "id": new_point_id}
                        self.state['points'][new_point_id] = new_point
                        
                        team_name = self.state['teams'][teamId]['name']
                        log_msg = {
                            'teamId': teamId,
                            'message': f"The Heartwood of Team {team_name} birthed a new point.",
                            'short_message': '[HW:GROWTH]'
                        }
                        self.state['game_log'].append(log_msg)
                        self.state['new_turn_events'].append({
                            'type': 'heartwood_growth',
                            'new_point': new_point,
                            'heartwood_id': heartwood['id']
                        })
                        break # Stop trying to find a spot
        
        # 4. Process Whirlpools
        if self.state.get('whirlpools'):
            active_whirlpools = []
            grid_size = self.state['grid_size']
            for whirlpool in self.state['whirlpools']:
                whirlpool['turns_left'] -= 1
                if whirlpool['turns_left'] > 0:
                    active_whirlpools.append(whirlpool)

                    wp_coords = whirlpool['coords']
                    wp_radius_sq = whirlpool['radius_sq']
                    wp_strength = whirlpool['strength']
                    wp_swirl = whirlpool['swirl']

                    # Affect all points, regardless of team
                    for point in self.state['points'].values():
                        if distance_sq(wp_coords, point) < wp_radius_sq:
                            # Vector from point to whirlpool center
                            dx = wp_coords['x'] - point['x']
                            dy = wp_coords['y'] - point['y']

                            # Convert to polar
                            dist = math.sqrt(dx**2 + dy**2)
                            angle = math.atan2(dy, dx)
                            
                            if dist < 0.1: continue # Don't move points already at the center

                            # Modify polar coordinates
                            new_dist = dist * (1 - wp_strength) # Pull in
                            new_angle = angle + wp_swirl # Swirl

                            # Convert back to cartesian offset from whirlpool center
                            new_dx = math.cos(new_angle) * new_dist
                            new_dy = math.sin(new_angle) * new_dy

                            # Calculate new absolute position and clamp/round
                            new_x = wp_coords['x'] - new_dx
                            new_y = wp_coords['y'] - new_dy
                            point['x'] = round(max(0, min(grid_size - 1, new_x)))
                            point['y'] = round(max(0, min(grid_size - 1, new_y)))

            self.state['whirlpools'] = active_whirlpools

        # 5. Process Monoliths
        if self.state.get('monoliths'):
            for monolith_id, monolith in list(self.state['monoliths'].items()):
                monolith['charge_counter'] += 1
                if monolith['charge_counter'] >= monolith['charge_interval']:
                    monolith['charge_counter'] = 0
                    
                    team_name = self.state['teams'][monolith['teamId']]['name']
                    log_msg = {
                        'teamId': monolith['teamId'],
                        'message': f"A Monolith from Team {team_name} emits a reinforcing wave.",
                        'short_message': '[MONOLITH:WAVE]'
                    }
                    self.state['game_log'].append(log_msg)
                    self.state['new_turn_events'].append({
                        'type': 'monolith_wave',
                        'monolith_id': monolith_id,
                        'center_coords': monolith['center_coords'],
                        'radius_sq': monolith['wave_radius_sq']
                    })

                    # Find and empower nearby friendly lines
                    center = monolith['center_coords']
                    radius_sq = monolith['wave_radius_sq']
                    max_strength = 3
                    
                    for line in self.get_team_lines(monolith['teamId']):
                        # Check if line midpoint is in range
                        if line['p1_id'] not in self.state['points'] or line['p2_id'] not in self.state['points']: continue
                        p1 = self.state['points'][line['p1_id']]
                        p2 = self.state['points'][line['p2_id']]
                        midpoint = {'x': (p1['x'] + p2['x']) / 2, 'y': (p1['y'] + p2['y']) / 2}
                        
                        if distance_sq(center, midpoint) < radius_sq:
                            current_strength = self.state['empowered_lines'].get(line.get('id'), 0)
                            if current_strength < max_strength:
                                self.state['empowered_lines'][line['id']] = current_strength + 1
        
        # 6. Process Wonders
        if self.state.get('wonders'):
            for wonder_id, wonder in list(self.state['wonders'].items()):
                if wonder['type'] == 'ChronosSpire':
                    wonder['turns_to_victory'] -= 1
                    team_name = self.state['teams'][wonder['teamId']]['name']
                    
                    log_msg = {
                        'teamId': wonder['teamId'],
                        'message': f"The Chronos Spire of Team {team_name} pulses. Victory in {wonder['turns_to_victory']} turns.",
                        'short_message': f'[SPIRE: T-{wonder["turns_to_victory"]}]'
                    }
                    self.state['game_log'].append(log_msg)
                    
                    # Check for wonder victory here at start of turn
                    if wonder['turns_to_victory'] <= 0:
                        self.state['game_phase'] = 'FINISHED'
                        self.state['victory_condition'] = f"Team '{team_name}' achieved victory with the Chronos Spire."
                        self.state['game_log'].append({'message': self.state['victory_condition'], 'short_message': '[WONDER VICTORY]'})
                        # We should stop processing the rest of the turn start.
                        self.state['actions_queue_this_turn'] = [] # empty queue
                        return # exit early
        
        # 7. Process Rift Spires (charging) and Fissures (decay)
        if self.state.get('rift_spires'):
            for spire in self.state['rift_spires'].values():
                if spire.get('charge', 0) < spire.get('charge_needed', 3):
                    spire['charge'] = spire.get('charge', 0) + 1
        
        if self.state.get('fissures'):
            active_fissures = []
            for f in self.state['fissures']:
                f['turns_left'] -= 1
                if f['turns_left'] > 0:
                    active_fissures.append(f)
            self.state['fissures'] = active_fissures

        # --- Set up action queue for the turn ---
        self.state['game_log'].append({'message': f"--- Turn {self.state['turn']} ---", 'short_message': f"~ T{self.state['turn']} ~"})
        active_teams = [teamId for teamId in self.state['teams'] if len(self.get_team_point_ids(teamId)) > 0]
        
        actions_queue = []
        # Update structures to determine bonus actions, then build the queue
        for teamId in active_teams:
            # This update is specifically to determine bonus actions for this turn
            self._update_nexuses_for_team(teamId)
            num_nexuses = len(self.state.get('nexuses', {}).get(teamId, []))
            
            # Add base action
            actions_queue.append({'teamId': teamId, 'is_bonus': False})

            # Add bonus actions from Nexuses
            if num_nexuses > 0:
                team_name = self.state['teams'][teamId]['name']
                plural = "s" if num_nexuses > 1 else ""
                self.state['game_log'].append({
                    'message': f"Team {team_name} gains {num_nexuses} bonus action{plural} from its Nexus{plural}.",
                    'short_message': f'[NEXUS:+{num_nexuses}ACT]'
                })
                for _ in range(num_nexuses):
                    actions_queue.append({'teamId': teamId, 'is_bonus': True})

            # Add bonus action from Wonders
            num_wonders = sum(1 for w in self.state.get('wonders', {}).values() if w['teamId'] == teamId)
            if num_wonders > 0:
                team_name = self.state['teams'][teamId]['name']
                plural = "s" if num_wonders > 1 else ""
                self.state['game_log'].append({
                    'message': f"Team {team_name} gains {num_wonders} bonus action{plural} from its Wonder{plural}.",
                    'short_message': f'[WONDER:+{num_wonders}ACT]'
                })
                for _ in range(num_wonders):
                    actions_queue.append({'teamId': teamId, 'is_bonus': True})

        random.shuffle(actions_queue) # Randomize action order each turn
        self.state['actions_queue_this_turn'] = actions_queue
        
    def _check_end_of_turn_victory_conditions(self):
        """Checks for victory conditions that are evaluated at the end of a full turn."""
        # Get unique team IDs that had actions this turn
        active_teams = list(set(info['teamId'] for info in self.state['actions_queue_this_turn'] if info))
        
        # 1. Dominance Victory
        DOMINANCE_TURNS_REQUIRED = 3
        if len(active_teams) == 1:
            sole_survivor_id = active_teams[0]
            tracker = self.state['sole_survivor_tracker']
            if tracker['teamId'] == sole_survivor_id:
                tracker['turns'] += 1
            else:
                tracker['teamId'] = sole_survivor_id
                tracker['turns'] = 1
            
            if tracker['turns'] >= DOMINANCE_TURNS_REQUIRED:
                self.state['game_phase'] = 'FINISHED'
                team_name = self.state['teams'][sole_survivor_id]['name']
                self.state['victory_condition'] = f"Team '{team_name}' achieved dominance."
                self.state['game_log'].append({'message': self.state['victory_condition'], 'short_message': '[VICTORY]'})
                return
        else:
            self.state['sole_survivor_tracker'] = {'teamId': None, 'turns': 0}

        # 2. Max Turns Reached
        if self.state['turn'] >= self.state['max_turns']:
            self.state['game_phase'] = 'FINISHED'
            self.state['victory_condition'] = "Max turns reached."
            self.state['game_log'].append({'message': "Max turns reached. Game finished.", 'short_message': '[END]'})

    def _get_action_log_messages(self, result):
        """Generates the long and short log messages for a given action result."""
        action_type = result.get('type')

        # Lambdas are used to defer f-string evaluation until the function is called.
        log_generators = {
            'add_line': lambda r: ("connected two points.", "[+LINE]"),
            'extend_line': lambda r: (
                f"extended a line to the border, creating a new point{' with an empowered Conduit extension!' if r.get('is_empowered') else '.'}",
                "[RAY!]" if r.get('is_empowered') else "[EXTEND]"
            ),
            'grow_line': lambda r: ("grew a new branch, creating a new point.", "[GROW]"),
            'fracture_line': lambda r: ("fractured a line, creating a new point.", "[FRACTURE]"),
            'spawn_point': lambda r: ("spawned a new point from an existing one.", "[SPAWN]"),
            'create_orbital': lambda r: (f"created an orbital structure with {len(r['new_points'])} new points.", "[ORBITAL]"),
            'attack_line': lambda r: (
                f"attacked and destroyed a line from Team {r['destroyed_team']}{', bypassing its shield with a Cross Rune!' if r.get('bypassed_shield') else '.'}",
                "[PIERCE!]" if r.get('bypassed_shield') else "[ATTACK]"
            ),
            'attack_line_empowered': lambda r: ("attacked an empowered line, weakening its defenses.", "[DAMAGE]"),
            'convert_point': lambda r: (f"sacrificed a line to convert a point from Team {r['original_team_name']}.", "[CONVERT]"),
            'claim_territory': lambda r: ("fortified its position, claiming new territory.", "[CLAIM]"),
            'form_bastion': lambda r: ("consolidated its power, forming a new bastion.", "[BASTION]"),
            'form_monolith': lambda r: ("erected a resonant Monolith, a bastion of endurance.", "[MONOLITH]"),
            'cultivate_heartwood': lambda r: (f"sacrificed {len(r['sacrificed_points'])} points to cultivate a mighty Heartwood.", "[HEARTWOOD!]"),
            'build_chronos_spire': lambda r: (f"sacrificed {r['sacrificed_points_count']} points to construct the Chronos Spire, a path to victory!", "[WONDER!]"),
            'bastion_pulse': lambda r: (f"unleashed a defensive pulse from its bastion, destroying {len(r['lines_destroyed'])} lines.", "[PULSE!]"),
            'mirror_structure': lambda r: (f"mirrored its structure, creating {len(r['new_points'])} new points.", "[MIRROR]"),
            'create_anchor': lambda r: ("sacrificed a point to create a gravitational anchor.", "[ANCHOR]"),
            'nova_burst': lambda r: (f"sacrificed a point in a nova burst, destroying {r['lines_destroyed']} lines.", "[NOVA]"),
            'shield_line': lambda r: ("raised a defensive shield on one of its lines.", "[SHIELD]"),
            'rune_shoot_bisector': lambda r: ("unleashed a powerful beam from a V-Rune, destroying an enemy line.", "[V-BEAM!]"),
            'sentry_zap': lambda r: (f"fired a precision shot from a Sentry, obliterating a point from Team {self.state['teams'][r['destroyed_point']['teamId']]['name']}.", "[ZAP!]"),
            'refraction_beam': lambda r: ("fired a refracted beam from a Prism, destroying an enemy line.", "[REFRACT!]"),
            'chain_lightning': lambda r: (
                f"unleashed Chain Lightning from a Conduit, destroying a point from Team {self.state['teams'][r['destroyed_point']['teamId']]['name']}." if r.get('destroyed_point') 
                else "attempted to use Chain Lightning, but the attack fizzled.",
                "[LIGHTNING!]" if r.get('destroyed_point') else "[FIZZLE]"
            ),
            'pincer_attack': lambda r: (f"executed a pincer attack, destroying a point from Team {self.state['teams'][r['destroyed_point']['teamId']]['name']}.", "[PINCER!]"),
            'territory_strike': lambda r: (f"launched a strike from its territory, destroying a point from Team {self.state['teams'][r['destroyed_point']['teamId']]['name']}.", "[TERRITORY!]"),
            'launch_payload': lambda r: (f"launched a payload from a Trebuchet, obliterating a fortified point from Team {self.state['teams'][r['destroyed_point']['teamId']]['name']}.", "[TREBUCHET!]"),
            'create_whirlpool': lambda r: ("sacrificed a point to create a chaotic whirlpool.", "[WHIRLPOOL!]"),
            'phase_shift': lambda r: ("sacrificed a line to phase shift a point to a new location.", "[PHASE!]")
        }

        if action_type in log_generators:
            long_msg, short_msg = log_generators[action_type](result)
            return long_msg, short_msg
        
        # Fallback for any action that might not have a custom message
        return "performed a successful action.", "[ACTION]"

    def run_next_action(self):
        """Runs a single successful action for the next team in the current turn."""
        if self.state['game_phase'] != 'RUNNING':
            return

        self.state['action_events'] = [] # Clear events from the previous action

        # Check if we need to start a new turn
        if not self.state.get('actions_queue_this_turn') or self.state['action_in_turn'] >= len(self.state['actions_queue_this_turn']):
            self._start_new_turn()
            
            # Check for immediate extinction after new turn setup (no teams left to act)
            if not self.state['actions_queue_this_turn']:
                self.state['game_phase'] = 'FINISHED'
                self.state['victory_condition'] = "Extinction"
                self.state['game_log'].append({'message': "All teams have been eliminated. Game over.", 'short_message': '[EXTINCTION]'})
                return

        # Get the current team to act from the queue
        action_info = self.state['actions_queue_this_turn'][self.state['action_in_turn']]
        teamId = action_info['teamId']
        is_bonus_action = action_info['is_bonus']
        
        # Update all special structures for the current team right before it acts.
        # This ensures the team acts based on its most current state.
        self._update_runes_for_team(teamId)
        self._update_sentries_for_team(teamId)
        self._update_conduits_for_team(teamId)
        self._update_prisms_for_team(teamId)
        self._update_trebuchets_for_team(teamId)
        # We also re-update nexuses here mainly so the frontend display is accurate
        # if a nexus is created or destroyed mid-turn. Bonus actions for this turn
        # are already locked in from _start_new_turn.
        self._update_nexuses_for_team(teamId)

        team_name = self.state['teams'][teamId]['name']
        
        # --- Perform a successful action for this team, trying until one succeeds ---
        result = None
        failed_actions = []
        MAX_ACTION_ATTEMPTS = 15 # Avoid infinite loops if no action can ever succeed
        
        for _ in range(MAX_ACTION_ATTEMPTS):
            action_name, action_func = self._choose_action_for_team(teamId, exclude_actions=failed_actions)
            
            if not action_func:
                result = {'success': False, 'reason': 'no possible actions'}
                break # No more actions available to try
            
            attempt_result = action_func(teamId)
            
            if attempt_result.get('success'):
                result = attempt_result
                break # Success, action is done
            else:
                # Action failed, add its name to the exclusion list for the next attempt
                failed_actions.append(action_name)
        else:
            # This 'else' belongs to the 'for' loop, running if it finishes without a 'break'
            result = {'success': False, 'reason': 'all attempted actions failed'}
            
        if result.get('success'):
            if self.state['action_events']:
                result['action_events'] = self.state['action_events'][:]
            self.state['last_action_details'] = result
        else:
            self.state['last_action_details'] = {}
        
        # --- Log the final result using the new helper method ---
        log_message = f"Team {team_name} "
        short_log_message = "[ACTION]"

        if is_bonus_action:
            log_message = f"[BONUS] Team {team_name} "

        if result.get('success'):
            long_msg_part, short_log_message = self._get_action_log_messages(result)
            log_message += long_msg_part
        else:
            log_message += "could not find a valid move and passed its turn."
            short_log_message = "[PASS]"
            
        self.state['game_log'].append({'teamId': teamId, 'message': log_message, 'short_message': short_log_message})
        
        # Increment for next action
        self.state['action_in_turn'] += 1
        
        # If this was the last action of the turn, check for victory conditions
        if self.state['action_in_turn'] >= len(self.state['actions_queue_this_turn']):
            self._check_end_of_turn_victory_conditions()
    
    # --- Interpretation ---

    def _generate_divination_text(self, stats):
        """Generates a short, horoscope-like text based on team stats."""
        if stats['point_count'] == 0:
            return "Faded from existence, a whisper in the cosmos."

        # Ratios
        line_density = stats['line_count'] / stats['point_count'] if stats['point_count'] > 0 else 0
        area_efficiency = stats['controlled_area'] / stats['hull_area'] if stats['hull_area'] > 0 else 0

        # Dominance checks
        if stats.get('aggression_score', 0) > 2: # Made-up stat for now
             return "A path of conflict and dominance, shaping destiny through force."
        if area_efficiency > 0.6 and stats['triangles'] > 2:
            return "A builder of empires, turning chaotic space into ordered, controlled territory."
        if stats['hull_area'] > 50 and area_efficiency < 0.2:
            return "An expansive and ambitious spirit, reaching for the outer edges of possibility."
        if line_density > 1.4: # Very interconnected
            return "An intricate and thoughtful strategist, weaving a complex web of influence."
        if stats['line_length'] > 100:
            return "A far-reaching presence, connecting distant ideas and holding vast influence."
        
        return "A balanced force, showing steady and stable development."


    def calculate_interpretation(self):
        """Calculates geometric properties for each team."""
        interpretation = {}
        all_points = self.state['points']
        for teamId, team_data in self.state['teams'].items():
            team_point_ids = self.get_team_point_ids(teamId)
            team_points_dict = {pid: all_points[pid] for pid in team_point_ids if pid in all_points}
            team_points_list = list(team_points_dict.values())
            
            team_lines = self.get_team_lines(teamId)
            team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]

            if len(team_points_list) < 1:
                 interpretation[teamId] = { 'point_count': 0, 'line_count': 0, 'line_length': 0, 'triangles': 0, 'controlled_area': 0, 'hull_area': 0, 'hull_perimeter': 0, 'hull_points': [], 'divination_text': 'Faded from existence.'}
                 continue

            # 1. Total Line Length
            total_length = 0
            for line in team_lines:
                if line['p1_id'] in all_points and line['p2_id'] in all_points:
                    p1 = all_points[line['p1_id']]
                    p2 = all_points[line['p2_id']]
                    total_length += math.sqrt(distance_sq(p1, p2))

            # 2. Triangle Count
            adj = {pid: set() for pid in team_point_ids}
            for line in team_lines:
                if line['p1_id'] in adj and line['p2_id'] in adj:
                    adj[line['p1_id']].add(line['p2_id'])
                    adj[line['p2_id']].add(line['p1_id'])
            
            triangles = 0
            sorted_point_ids = sorted(list(team_point_ids))
            for i in sorted_point_ids:
                for j in adj.get(i, set()):
                    if j > i:
                        for k in adj.get(j, set()):
                            if k > j and k in adj.get(i, set()):
                                triangles += 1
            
            # 3. Convex Hull and its properties (using Graham Scan)
            hull_points = self._get_convex_hull(team_points_list)
            hull_area = 0
            hull_perimeter = 0
            if len(hull_points) >= 3:
                hull_area = self._polygon_area(hull_points)
                hull_perimeter = self._polygon_perimeter(hull_points)

            # 4. Total Controlled Area from territories
            controlled_area = 0
            for territory in team_territories:
                triangle_point_ids = territory['point_ids']
                if all(pid in all_points for pid in triangle_point_ids):
                    triangle_points = [all_points[pid] for pid in triangle_point_ids]
                    if len(triangle_points) == 3:
                        controlled_area += self._polygon_area(triangle_points)


            stats = {
                'point_count': len(team_points_list),
                'line_count': len(team_lines),
                'line_length': round(total_length, 2),
                'triangles': triangles,
                'controlled_area': round(controlled_area, 2),
                'hull_area': round(hull_area, 2),
                'hull_perimeter': round(hull_perimeter, 2),
                'hull_points': hull_points
            }
            stats['divination_text'] = self._generate_divination_text(stats)
            interpretation[teamId] = stats
            
        return interpretation

    def _get_convex_hull(self, points):
        """Computes the convex hull of a set of points using Graham Scan."""
        if len(points) < 3:
            return points
        
        # Find pivot (lowest y, then lowest x)
        pivot = min(points, key=lambda p: (p['y'], p['x']))
        
        # Sort points by polar angle with pivot
        sorted_points = sorted(
            [p for p in points if p != pivot], 
            key=lambda p: (math.atan2(p['y'] - pivot['y'], p['x'] - pivot['x']), distance_sq(p, pivot))
        )
        
        hull = [pivot]
        for p in sorted_points:
            while len(hull) >= 2 and orientation(hull[-2], hull[-1], p) != 2: # 2 = counter-clockwise
                hull.pop()
            hull.append(p)
            
        return hull

    def _polygon_area(self, points):
        """Calculates area of a polygon using Shoelace formula."""
        area = 0.0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i]['x'] * points[j]['y']
            area -= points[j]['x'] * points[i]['y']
        return abs(area) / 2.0

    def _polygon_perimeter(self, points):
        """Calculates the perimeter of a polygon."""
        perimeter = 0.0
        n = len(points)
        for i in range(n):
            p1 = points[i]
            p2 = points[(i + 1) % n]
            perimeter += math.sqrt(distance_sq(p1, p2))
        return perimeter

    # --- Rune System ---
    
    def _update_runes_for_team(self, teamId):
        """Checks and updates all rune states for a given team."""
        if teamId not in self.state['runes']:
            self.state['runes'][teamId] = {}
        
        self.state['runes'][teamId]['cross'] = self._check_cross_rune(teamId)
        self.state['runes'][teamId]['v_shape'] = self._check_v_rune(teamId)

    def _update_sentries_for_team(self, teamId):
        """Checks for Sentry formations (3 collinear points with lines)."""
        if 'sentries' not in self.state: self.state['sentries'] = {}
        self.state['sentries'][teamId] = [] # Recalculate each time
        
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 3:
            return

        points = self.state['points']
        existing_lines = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in self.get_team_lines(teamId)}
        
        for p_ids in combinations(team_point_ids, 3):
            # Ensure all points still exist before lookup
            if not all(pid in points for pid in p_ids): continue
            p1, p2, p3 = points[p_ids[0]], points[p_ids[1]], points[p_ids[2]]

            # Check for collinearity
            if orientation(p1, p2, p3) == 0:
                # Identify the middle point ('eye')
                eye, post1, post2 = None, None, None
                if on_segment(p1, p2, p3): eye, post1, post2 = p2, p1, p3
                elif on_segment(p2, p1, p3): eye, post1, post2 = p1, p2, p3
                elif on_segment(p1, p3, p2): eye, post1, post2 = p3, p1, p2
                
                if eye:
                    # Check if lines from eye to posts exist
                    line1_exists = tuple(sorted((eye['id'], post1['id']))) in existing_lines
                    line2_exists = tuple(sorted((eye['id'], post2['id']))) in existing_lines
                    if line1_exists and line2_exists:
                        self.state['sentries'][teamId].append({
                            'eye_id': eye['id'],
                            'post1_id': post1['id'],
                            'post2_id': post2['id'],
                        })

    def _check_v_rune(self, teamId):
        """Finds all 'V' shapes for a team.
        A V-shape is two connected lines of similar length.
        Returns a list of dictionaries, each identifying a V-rune.
        e.g., [{'vertex_id': B, 'leg1_id': A, 'leg2_id': C}]
        """
        team_point_ids = self.get_team_point_ids(teamId)
        points = self.state['points']
        lines = self.get_team_lines(teamId)
        
        adj_lines = {pid: [] for pid in team_point_ids}
        for line in lines:
            if line['p1_id'] in adj_lines and line['p2_id'] in adj_lines:
                adj_lines[line['p1_id']].append(line)
                adj_lines[line['p2_id']].append(line)

        v_runes = []
        for vertex_id, connected_lines in adj_lines.items():
            if len(connected_lines) < 2: continue

            for i in range(len(connected_lines)):
                for j in range(i + 1, len(connected_lines)):
                    line1, line2 = connected_lines[i], connected_lines[j]
                    
                    p_vertex = points[vertex_id]
                    p_leg1 = points[line1['p1_id'] if line1['p2_id'] == vertex_id else line1['p2_id']]
                    p_leg2 = points[line2['p1_id'] if line2['p2_id'] == vertex_id else line2['p2_id']]

                    len1_sq = distance_sq(p_vertex, p_leg1)
                    len2_sq = distance_sq(p_vertex, p_leg2)

                    # Check for similar length (e.g., within 20% of each other)
                    if len1_sq > 0 and len2_sq > 0 and 0.8 < (len1_sq / len2_sq) < 1.2:
                        v_runes.append({
                            'vertex_id': vertex_id,
                            'leg1_id': p_leg1['id'],
                            'leg2_id': p_leg2['id'],
                        })
        return v_runes

    def _check_cross_rune(self, teamId):
        """Finds all 'Cross' runes.
        A Cross rune is a rectangle of 4 points with both diagonals drawn.
        Returns a list of lists, each containing the 4 point IDs of a cross rune.
        """
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 4:
            return []
        
        points = self.state['points']
        existing_lines = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in self.get_team_lines(teamId)}

        cross_runes = []
        for p_ids in combinations(team_point_ids, 4):
            p = [points[pid] for pid in p_ids]
            
            pairings = [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]
            
            for d1_idx, d2_idx in pairings:
                p_d1_1, p_d1_2 = p[d1_idx[0]], p[d1_idx[1]]
                p_d2_1, p_d2_2 = p[d2_idx[0]], p[d2_idx[1]]

                # Midpoints must be the same (for a parallelogram)
                mid1_x = (p_d1_1['x'] + p_d1_2['x']) / 2
                mid1_y = (p_d1_1['y'] + p_d1_2['y']) / 2
                mid2_x = (p_d2_1['x'] + p_d2_2['x']) / 2
                mid2_y = (p_d2_1['y'] + p_d2_2['y']) / 2
                if abs(mid1_x - mid2_x) > 0.01 or abs(mid1_y - mid2_y) > 0.01:
                    continue

                # Diagonal lengths must be same (for a rectangle)
                if abs(distance_sq(p_d1_1, p_d1_2) - distance_sq(p_d2_1, p_d2_2)) > 0.01:
                    continue

                # Both diagonals must exist as lines
                diag1_exists = tuple(sorted((p_d1_1['id'], p_d1_2['id']))) in existing_lines
                diag2_exists = tuple(sorted((p_d2_1['id'], p_d2_2['id']))) in existing_lines

                if diag1_exists and diag2_exists:
                    cross_runes.append(list(p_ids))
                    break  # Found the correct diagonal pairing
        
        return cross_runes

    def _update_conduits_for_team(self, teamId):
        """Checks for Conduit formations (3+ collinear points)."""
        if 'conduits' not in self.state: self.state['conduits'] = {}
        
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 3:
            self.state['conduits'][teamId] = []
            return

        points = self.state['points']
        team_points = [points[pid] for pid in team_point_ids]
        
        # O(n^2) approach to find all sets of collinear points
        found_conduits_sets = set()
        for i in range(len(team_points)):
            p1 = team_points[i]
            slopes = {}
            for j in range(i + 1, len(team_points)):
                p2 = team_points[j]
                dx = p2['x'] - p1['x']
                dy = p2['y'] - p1['y']
                
                slope = math.atan2(dy, dx) # Use angle for consistent slope key
                
                if slope not in slopes:
                    slopes[slope] = []
                slopes[slope].append(p2['id'])

            for slope in slopes:
                if len(slopes[slope]) >= 2: # p1 + at least 2 other points form a line of 3+
                    collinear_ids = tuple(sorted([p1['id']] + slopes[slope]))
                    found_conduits_sets.add(collinear_ids)

        # Convert sets of point IDs into formatted conduit objects
        final_conduits = []
        for id_tuple in found_conduits_sets:
            conduit_points = [points[pid] for pid in id_tuple]
            
            # Sort points along the line to find endpoints
            if len(set(p['x'] for p in conduit_points)) > 1: # Not a vertical line
                conduit_points.sort(key=lambda p: p['x'])
            else: # Vertical line
                conduit_points.sort(key=lambda p: p['y'])
            
            sorted_ids = [p['id'] for p in conduit_points]
            
            final_conduits.append({
                'point_ids': sorted_ids,
                'endpoint1_id': sorted_ids[0],
                'endpoint2_id': sorted_ids[-1],
                'internal_point_ids': sorted_ids[1:-1]
            })

        self.state['conduits'][teamId] = final_conduits

    def _update_prisms_for_team(self, teamId):
        """Checks for Prism formations (two territories sharing an edge)."""
        if 'prisms' not in self.state: self.state['prisms'] = {}
        self.state['prisms'][teamId] = []

        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        if len(team_territories) < 2:
            return

        # Map edges to the territories they belong to
        edge_to_territories = {}
        for i, territory in enumerate(team_territories):
            p_ids = territory['point_ids']
            # Create the 3 edges for the triangle
            edges = [
                tuple(sorted((p_ids[0], p_ids[1]))),
                tuple(sorted((p_ids[1], p_ids[2]))),
                tuple(sorted((p_ids[2], p_ids[0])))
            ]
            for edge in edges:
                if edge not in edge_to_territories:
                    edge_to_territories[edge] = []
                edge_to_territories[edge].append(i) # Store territory index

        # Find edges that are shared by exactly two territories
        for edge, ter_indices in edge_to_territories.items():
            if len(ter_indices) == 2:
                ter1 = team_territories[ter_indices[0]]
                ter2 = team_territories[ter_indices[1]]
                
                all_points = set(ter1['point_ids']).union(set(ter2['point_ids']))
                
                # A prism is formed by 4 points
                if len(all_points) == 4:
                    self.state['prisms'][teamId].append({
                        'shared_p1_id': edge[0],
                        'shared_p2_id': edge[1],
                        'all_point_ids': list(all_points)
                    })

    def _update_trebuchets_for_team(self, teamId):
        """Checks for Trebuchet formations (a specific kite shape)."""
        if 'trebuchets' not in self.state: self.state['trebuchets'] = {}
        self.state['trebuchets'][teamId] = []

        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 4:
            return

        points = self.state['points']
        adj = {pid: set() for pid in team_point_ids}
        for line in self.get_team_lines(teamId):
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])
        
        used_points = set()
        possible_trebuchets = []

        # Iterate through every point as a potential 'apex' of the structure
        for apex_id in team_point_ids:
            if apex_id in used_points: continue
            
            neighbors = list(adj.get(apex_id, set()))
            if len(neighbors) < 2: continue

            # Iterate through pairs of neighbors to form a triangle with the apex
            for i in range(len(neighbors)):
                for j in range(i + 1, len(neighbors)):
                    base1_id, base2_id = neighbors[i], neighbors[j]
                    
                    if base1_id in used_points or base2_id in used_points: continue

                    p_apex, p_base1, p_base2 = points[apex_id], points[base1_id], points[base2_id]
                    
                    leg1_sq, leg2_sq = distance_sq(p_apex, p_base1), distance_sq(p_apex, p_base2)

                    # Check for isosceles triangle with apex at apex_id
                    if abs(leg1_sq - leg2_sq) > 0.01 or leg1_sq < 1.0:
                        continue

                    # Check for "tight" triangle (base shorter than legs)
                    base_len_sq = distance_sq(p_base1, p_base2)
                    if base_len_sq > leg1_sq:
                        continue
                    
                    # The base of the triangle must be a connected line
                    if base2_id not in adj.get(base1_id, set()):
                        continue

                    # Find a counterweight: a common neighbor of the two base points, which is not the apex
                    common_neighbors = adj.get(base1_id, set()).intersection(adj.get(base2_id, set()))
                    
                    for cw_id in common_neighbors:
                        if cw_id == apex_id or cw_id in used_points: continue
                        
                        p_cw = points[cw_id]
                        base_midpoint = {'x': (p_base1['x'] + p_base2['x']) / 2, 'y': (p_base1['y'] + p_base2['y']) / 2}
                        
                        v_apex = {'x': p_apex['x'] - base_midpoint['x'], 'y': p_apex['y'] - base_midpoint['y']}
                        v_cw = {'x': p_cw['x'] - base_midpoint['x'], 'y': p_cw['y'] - base_midpoint['y']}
                        
                        cross_product = v_apex['x'] * v_cw['y'] - v_apex['y'] * v_cw['x']
                        if abs(cross_product) > 1.0:
                            continue

                        if (v_apex['x'] * v_cw['x'] + v_apex['y'] * v_cw['y']) >= 0:
                            continue
                        
                        all_p_ids = {apex_id, base1_id, base2_id, cw_id}
                        if not used_points.intersection(all_p_ids):
                            possible_trebuchets.append({
                                'point_ids': list(all_p_ids),
                                'apex_id': apex_id,
                                'base_ids': [base1_id, base2_id],
                                'counterweight_id': cw_id,
                            })
                            used_points.update(all_p_ids)

        self.state['trebuchets'][teamId] = possible_trebuchets


# --- Global Game Instance ---
# This is a singleton pattern. The Flask app will interact with this instance.
game = Game()

def init_game_state():
    """Resets the global game instance."""
    global game
    game.reset()