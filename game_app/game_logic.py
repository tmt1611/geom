import random
import math

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

# --- Game Class ---
class Game:
    """Encapsulates the entire game state and logic."""
    def __init__(self):
        self.reset()

    def reset(self):
        """Initializes or resets the game state."""
        self.state = {
            "grid_size": 10,
            "teams": {},
            "points": [],
            "lines": [],
            "game_log": [],
            "turn": 0,
            "max_turns": 100,
            "is_running": False,
            "is_finished": False,
            "interpretation": {}
        }

    def get_state(self):
        """Returns the current game state."""
        # On-demand calculation of interpretation when game is finished
        if self.state['is_finished'] and not self.state['interpretation']:
            self.state['interpretation'] = self.calculate_interpretation()
        return self.state

    def start_game(self, teams, points, max_turns, grid_size):
        """Starts a new game with the given parameters."""
        self.reset()
        self.state['teams'] = teams
        self.state['points'] = points
        self.state['max_turns'] = max_turns
        self.state['grid_size'] = grid_size
        self.state['is_running'] = len(points) > 0
        self.state['game_log'].append({'message': "Game initialized."})

    def get_team_points_indices(self, teamId):
        """Returns indices of points belonging to a team."""
        return [i for i, p in enumerate(self.state['points']) if p['teamId'] == teamId]

    def get_team_lines(self, teamId):
        """Returns lines belonging to a team."""
        return [l for l in self.state['lines'] if l['teamId'] == teamId]

    # --- Game Actions ---

    def expand_action_add_line(self, teamId):
        """[EXPAND ACTION]: Add a line between two random points."""
        team_points_indices = self.get_team_points_indices(teamId)
        if len(team_points_indices) < 2:
            return {'success': False, 'reason': 'not enough points'}

        # Create a set of existing lines for quick lookup
        existing_lines = set()
        for line in self.state['lines']:
            if line['teamId'] == teamId:
                existing_lines.add(tuple(sorted((line['p1_idx'], line['p2_idx']))))

        # Try to find a non-existing line
        possible_pairs = []
        for i in range(len(team_points_indices)):
            for j in range(i + 1, len(team_points_indices)):
                p1_idx = team_points_indices[i]
                p2_idx = team_points_indices[j]
                if tuple(sorted((p1_idx, p2_idx))) not in existing_lines:
                    possible_pairs.append((p1_idx, p2_idx))
        
        if not possible_pairs:
            return {'success': False, 'reason': 'no new lines possible'}

        p1_idx, p2_idx = random.choice(possible_pairs)
        self.state['lines'].append({"p1_idx": p1_idx, "p2_idx": p2_idx, "teamId": teamId})
        return {'success': True, 'type': 'add_line'}

        self.state['lines'].append({"p1_idx": p1_idx, "p2_idx": p2_idx, "teamId": teamId})
        return {'success': True, 'type': 'add_line'}

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
        if not team_lines:
            return {'success': False, 'reason': 'no lines to extend'}

        line = random.choice(team_lines)
        points = self.state['points']
        p1 = points[line['p1_idx']]
        p2 = points[line['p2_idx']]

        # Randomly choose which direction to extend from
        if random.random() > 0.5:
            p1, p2 = p2, p1 # Extend from p2, using p1 for direction

        border_point = self._get_extended_border_point(p1, p2)
        if not border_point:
            return {'success': False, 'reason': 'line cannot be extended'}

        self.state['points'].append({**border_point, "teamId": teamId})
        return {'success': True, 'type': 'extend_line', 'new_point': border_point}

    def fight_action_attack_line(self, teamId):
        """[FIGHT ACTION]: Extend a line to hit an enemy line, destroying it."""
        team_lines = self.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to attack with'}

        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        if not enemy_lines:
            return {'success': False, 'reason': 'no enemy lines to attack'}

        random.shuffle(team_lines)
        points = self.state['points']

        for line in team_lines:
            p1 = points[line['p1_idx']]
            p2 = points[line['p2_idx']]

            # Try extending from both ends of the segment
            for p_start, p_end in [(p1, p2), (p2, p1)]:
                border_point = self._get_extended_border_point(p_start, p_end)
                if not border_point:
                    continue

                # The attacking ray is the segment from the line's endpoint to the border
                attack_segment_p1 = p_end
                attack_segment_p2 = border_point

                for enemy_line in enemy_lines:
                    ep1 = points[enemy_line['p1_idx']]
                    ep2 = points[enemy_line['p2_idx']]

                    if segments_intersect(attack_segment_p1, attack_segment_p2, ep1, ep2):
                        # Target found! Remove the enemy line.
                        self.state['lines'].remove(enemy_line)
                        enemy_team_name = self.state['teams'][enemy_line['teamId']]['name']
                        return {'success': True, 'type': 'attack_line', 'destroyed_team': enemy_team_name}

        return {'success': False, 'reason': 'no target was hit'}

    # --- Turn Logic ---

    def run_next_turn(self):
        """Runs one turn of the game."""
        if self.state['is_finished']:
            return

        self.state['turn'] += 1
        self.state['game_log'].append({'message': f"--- Turn {self.state['turn']} ---"})

        active_teams = [teamId for teamId in self.state['teams'] if len(self.get_team_points_indices(teamId)) > 0]
        if not active_teams:
            self.state['is_finished'] = True
            self.state['game_log'].append({'message': "No active teams left. Game over."})
            return

        for teamId in active_teams:
            team_name = self.state['teams'][teamId]['name']
            
            # Choose a random action to perform
            possible_actions = [
                self.expand_action_add_line,
                self.expand_action_extend_line,
                self.fight_action_attack_line
            ]
            action_to_perform = random.choice(possible_actions)
            result = action_to_perform(teamId)

            # Log the result
            log_message = f"Team {team_name} "
            if result.get('success'):
                action_type = result.get('type')
                if action_type == 'add_line':
                    log_message += "connected two points."
                elif action_type == 'extend_line':
                    log_message += "extended a line to the border, creating a new point."
                elif action_type == 'attack_line':
                    log_message += f"attacked and destroyed a line from Team {result['destroyed_team']}."
                else:
                    log_message += "performed a successful action."
            else:
                reason = result.get('reason', 'an unknown reason')
                if reason == 'not enough points':
                    log_message += "could not act (not enough points)."
                elif reason == 'no new lines possible':
                    log_message += "failed to add a new line (all points connected)."
                elif reason == 'no lines to extend':
                     log_message += "had no lines to extend."
                elif reason == 'no lines to attack with':
                     log_message += "had no lines to attack with."
                elif reason == 'no enemy lines to attack':
                    log_message += "found no enemy lines to attack."
                elif reason == 'no target was hit':
                    log_message += "attempted an attack but missed."
                else:
                    log_message += f"failed an action: {reason}."

            self.state['game_log'].append({'teamId': teamId, 'message': log_message})


        if self.state['turn'] >= self.state['max_turns']:
            self.state['is_finished'] = True
            self.state['is_running'] = False
            self.state['game_log'].append({'message': "Max turns reached. Game finished."})
    
    # --- Interpretation ---

    def calculate_interpretation(self):
        """Calculates geometric properties for each team."""
        interpretation = {}
        for teamId, team_data in self.state['teams'].items():
            team_points_indices = self.get_team_points_indices(teamId)
            team_points = [self.state['points'][i] for i in team_points_indices]
            team_lines = self.get_team_lines(teamId)

            if len(team_points) < 1:
                 interpretation[teamId] = { 'point_count': 0, 'line_count': 0, 'line_length': 0, 'triangles': 0, 'hull_area': 0, 'hull_perimeter': 0}
                 continue

            # 1. Total Line Length
            total_length = 0
            for line in team_lines:
                p1 = self.state['points'][line['p1_idx']]
                p2 = self.state['points'][line['p2_idx']]
                total_length += math.sqrt(distance_sq(p1, p2))

            # 2. Triangle Count
            adj = {i: set() for i in team_points_indices}
            for line in team_lines:
                adj[line['p1_idx']].add(line['p2_idx'])
                adj[line['p2_idx']].add(line['p1_idx'])
            
            triangles = 0
            for i in team_points_indices:
                for j in adj[i]:
                    if j > i:
                        for k in adj[j]:
                            if k > j and k in adj[i]:
                                triangles += 1
            
            # 3. Convex Hull and its properties (using Graham Scan)
            hull_points = self._get_convex_hull(team_points)
            hull_area = 0
            hull_perimeter = 0
            if len(hull_points) >= 3:
                hull_area = self._polygon_area(hull_points)
                hull_perimeter = self._polygon_perimeter(hull_points)


            interpretation[teamId] = {
                'point_count': len(team_points),
                'line_count': len(team_lines),
                'line_length': round(total_length, 2),
                'triangles': triangles,
                'hull_area': round(hull_area, 2),
                'hull_perimeter': round(hull_perimeter, 2)
            }
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

# --- Global Game Instance ---
# This is a singleton pattern. The Flask app will interact with this instance.
game = Game()

def init_game_state():
    """Resets the global game instance."""
    global game
    game.reset()