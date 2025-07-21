import random
import math
import uuid  # For unique point IDs

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
            "game_log": [{'message': "Welcome! Default teams Alpha and Beta are ready. Place points to begin."}],
            "turn": 0,
            "max_turns": 100,
            "game_phase": "SETUP", # SETUP, RUNNING, FINISHED
            "victory_condition": None,
            "sole_survivor_tracker": {'teamId': None, 'turns': 0},
            "interpretation": {},
            "last_action_details": {}, # For frontend visualization
            "initial_state": None, # Store the setup config for restarts
            "action_in_turn": 0, # Which team's action in the current turn
            "active_teams_this_turn": [] # List of team IDs for the current turn
        }

    def get_state(self):
        """Returns the current game state, augmenting with transient data for frontend."""
        # On-demand calculation of interpretation when game is finished
        if self.state['game_phase'] == 'FINISHED' and not self.state['interpretation']:
            self.state['interpretation'] = self.calculate_interpretation()

        # Create a copy to avoid modifying original state
        state_copy = self.state.copy()
        
        # Augment lines with shield status for easier rendering
        augmented_lines = []
        for line in self.state['lines']:
            augmented_line = line.copy()
            augmented_line['is_shielded'] = line.get('id') in self.state['shields']
            augmented_lines.append(augmented_line)
        state_copy['lines'] = augmented_lines

        # Augment points with anchor status
        augmented_points = {}
        for pid, point in self.state['points'].items():
            augmented_point = point.copy()
            augmented_point['is_anchor'] = pid in self.state['anchors']
            augmented_points[pid] = augmented_point
        state_copy['points'] = augmented_points

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
        
        # Add a default 'Balanced' trait if none is provided from the frontend
        for team_id, team_data in teams.items():
            if 'trait' not in team_data:
                team_data['trait'] = 'Balanced'
            team_data['id'] = team_id # Ensure team object contains its own ID

        self.state['teams'] = teams
        # Convert points list to a dictionary with unique IDs
        for p in points:
            point_id = f"p_{uuid.uuid4().hex[:6]}"
            self.state['points'][point_id] = {**p, 'id': point_id}
        self.state['max_turns'] = max_turns
        self.state['grid_size'] = grid_size
        self.state['game_phase'] = "RUNNING" if len(points) > 0 else "SETUP"
        self.state['game_log'].append({'message': "Game initialized."})
        self.state['action_in_turn'] = 0
        self.state['active_teams_this_turn'] = []
        
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
        p1 = points[line['p1_id']]
        p2 = points[line['p2_id']]

        # Randomly choose which direction to extend from
        if random.random() > 0.5:
            p1, p2 = p2, p1 # Extend from p2, using p1 for direction

        border_point = self._get_extended_border_point(p1, p2)
        if not border_point:
            return {'success': False, 'reason': 'line cannot be extended'}

        # Create new point with a unique ID
        new_point_id = f"p_{uuid.uuid4().hex[:6]}"
        new_point = {**border_point, "teamId": teamId, "id": new_point_id}
        self.state['points'][new_point_id] = new_point
        return {'success': True, 'type': 'extend_line', 'new_point': new_point}

    def expand_action_fracture_line(self, teamId):
        """[EXPAND ACTION]: Splits a line into two, creating a new point."""
        team_lines = self.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to fracture'}

        # Try a few times to find a suitable line
        for _ in range(5):
            line_to_fracture = random.choice(team_lines)
            
            points = self.state['points']
            if line_to_fracture['p1_id'] not in points or line_to_fracture['p2_id'] not in points:
                continue # This line's points are gone, try another

            p1 = points[line_to_fracture['p1_id']]
            p2 = points[line_to_fracture['p2_id']]

            # Don't fracture very short lines
            if distance_sq(p1, p2) < 4.0: # min length of 2
                continue

            # Find a new point on the segment
            ratio = random.uniform(0.25, 0.75)
            new_x = p1['x'] + (p2['x'] - p1['x']) * ratio
            new_y = p1['y'] + (p2['y'] - p1['y']) * ratio

            # Create new point
            new_point_id = f"p_{uuid.uuid4().hex[:6]}"
            new_point = {"x": new_x, "y": new_y, "teamId": teamId, "id": new_point_id}
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
        
        return {'success': False, 'reason': 'line is too short to fracture'}


    def fight_action_attack_line(self, teamId):
        """[FIGHT ACTION]: Extend a line to hit an enemy line, destroying it."""
        team_lines = self.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to attack with'}

        # Create a copy to iterate over while modifying the original list
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        if not enemy_lines:
            return {'success': False, 'reason': 'no enemy lines to attack'}

        random.shuffle(team_lines)
        points = self.state['points']

        for line in team_lines:
            # Skip if line points are gone (can happen after sacrifice)
            if line['p1_id'] not in points or line['p2_id'] not in points:
                continue
            
            p1 = points[line['p1_id']]
            p2 = points[line['p2_id']]

            # Try extending from both ends of the segment
            for p_start, p_end in [(p1, p2), (p2, p1)]:
                border_point = self._get_extended_border_point(p_start, p_end)
                if not border_point:
                    continue

                # The attacking ray is the segment from the line's endpoint to the border
                attack_segment_p1 = p_end
                attack_segment_p2 = border_point

                for enemy_line in enemy_lines:
                    # Skip if enemy line points are gone
                    if enemy_line['p1_id'] not in points or enemy_line['p2_id'] not in points:
                        continue
                    
                    # Check if enemy line is shielded
                    if enemy_line.get('id') in self.state['shields']:
                        continue # Can't attack a shielded line

                    ep1 = points[enemy_line['p1_id']]
                    ep2 = points[enemy_line['p2_id']]

                    if segments_intersect(attack_segment_p1, attack_segment_p2, ep1, ep2):
                        # Target found! Remove the enemy line.
                        self.state['lines'].remove(enemy_line)
                        # Also remove any shield it might have had (e.g. if shield expired same turn)
                        self.state['shields'].pop(enemy_line.get('id'), None)
                        enemy_team_name = self.state['teams'][enemy_line['teamId']]['name']
                        return {
                            'success': True, 
                            'type': 'attack_line', 
                            'destroyed_team': enemy_team_name, 
                            'destroyed_line': enemy_line,
                            'attacker_line': line,
                            'attack_ray': {'p1': attack_segment_p1, 'p2': attack_segment_p2}
                        }

        return {'success': False, 'reason': 'no target was hit'}

    def sacrifice_action_nova_burst(self, teamId):
        """[SACRIFICE ACTION]: A point is destroyed, removing nearby enemy lines."""
        team_point_ids = self.get_team_point_ids(teamId)
        # A team cannot sacrifice its last point, as this is self-destructive.
        if len(team_point_ids) <= 1:
            return {'success': False, 'reason': 'not enough points to sacrifice safely'}

        sac_point_id = random.choice(team_point_ids)
        sac_point = self.state['points'][sac_point_id]
        
        # Define the blast radius (squared for efficiency)
        blast_radius_sq = (self.state['grid_size'] * 0.25)**2 

        lines_to_remove = []
        points_to_check = self.state['points']

        # 1. Remove all lines connected to the sacrificed point
        for line in self.state['lines']:
            if line['p1_id'] == sac_point_id or line['p2_id'] == sac_point_id:
                lines_to_remove.append(line)
        
        # 2. Remove nearby enemy lines
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId and l not in lines_to_remove]
        for line in enemy_lines:
            # Check if line points exist
            if not (line['p1_id'] in points_to_check and line['p2_id'] in points_to_check):
                continue
            
            p1 = points_to_check[line['p1_id']]
            p2 = points_to_check[line['p2_id']]

            # Check if either end of the enemy line is within the blast radius
            if distance_sq(sac_point, p1) < blast_radius_sq or distance_sq(sac_point, p2) < blast_radius_sq:
                 if line not in lines_to_remove:
                    lines_to_remove.append(line)

        if not lines_to_remove:
             # Even if no lines are destroyed, the point is still sacrificed
             pass

        # Perform removals
        for l in lines_to_remove:
            self.state['shields'].pop(l.get('id'), None) # Remove shield if line is destroyed
        self.state['lines'] = [l for l in self.state['lines'] if l not in lines_to_remove]
        del self.state['points'][sac_point_id]
        
        # Also remove any territories that used this point
        self.state['territories'] = [t for t in self.state['territories'] if sac_point_id not in t['point_ids']]

        return {'success': True, 'type': 'nova_burst', 'sacrificed_point': sac_point, 'lines_destroyed': len(lines_to_remove)}

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

            # Check if the new point is within the grid boundaries
            grid_size = self.state['grid_size']
            if not (0 <= new_x < grid_size and 0 <= new_y < grid_size):
                continue # Try another line if this one grows out of bounds

            # We found a valid growth, create the new point and line
            new_point_id = f"p_{uuid.uuid4().hex[:6]}"
            new_point = {"x": round(new_x), "y": round(new_y), "teamId": teamId, "id": new_point_id}
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

                # Check if it's too close to any existing point
                is_too_close = False
                for existing_p in self.state['points'].values():
                    if distance_sq(reflected_p, existing_p) < 1.0: # min dist of 1 unit
                        is_too_close = True
                        break
                if is_too_close:
                    continue

                # If valid, add it to the list to be created
                new_point_id = f"p_{uuid.uuid4().hex[:6]}"
                new_points_to_create.append({**reflected_p, "teamId": teamId, "id": new_point_id})

            # 4. If we successfully found points to create, do it and return
            if new_points_to_create:
                for p in new_points_to_create:
                    # Round to integers to conform to the new design requirement.
                    p['x'] = round(p['x'])
                    p['y'] = round(p['y'])
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
        
        # 1. Sacrifice the first point
        sacrificed_point = self.state['points'].pop(p_to_sac_id)

        # Also remove any lines or territories that used the sacrificed point
        self.state['lines'] = [l for l in self.state['lines'] if p_to_sac_id not in (l['p1_id'], l['p2_id'])]
        self.state['territories'] = [t for t in self.state['territories'] if p_to_sac_id not in t['point_ids']]
        self.state['shields'].pop(p_to_sac_id, None) # A point ID can't be a line ID, but good practice
        self.state['anchors'].pop(p_to_sac_id, None) # Can't sacrifice an anchor to make another

        # 2. Create the anchor
        anchor_duration = 5 # turns
        self.state['anchors'][p_to_anchor_id] = {'teamId': teamId, 'turns_left': anchor_duration}

        anchor_point = self.state['points'][p_to_anchor_id]

        return {
            'success': True, 
            'type': 'create_anchor', 
            'anchor_point': anchor_point,
            'sacrificed_point': sacrificed_point
        }

    def fight_action_convert_point(self, teamId):
        """[FIGHT ACTION]: Sacrifice a line to convert a nearby enemy point."""
        team_lines = self.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to sacrifice'}

        enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId]
        if not enemy_points:
            return {'success': False, 'reason': 'no enemy points to convert'}

        random.shuffle(team_lines)
        points_map = self.state['points']

        for line_to_sac in team_lines:
            # Ensure line points exist
            if line_to_sac['p1_id'] not in points_map or line_to_sac['p2_id'] not in points_map:
                continue
            
            p1 = points_map[line_to_sac['p1_id']]
            p2 = points_map[line_to_sac['p2_id']]
            midpoint = {'x': (p1['x'] + p2['x']) / 2, 'y': (p1['y'] + p2['y']) / 2}
            
            # Find the closest enemy point to the line's midpoint
            closest_enemy_point = min(enemy_points, key=lambda p: distance_sq(midpoint, p))
            
            dist_sq = distance_sq(midpoint, closest_enemy_point)
            
            # Define conversion range (squared for efficiency)
            conversion_range_sq = (self.state['grid_size'] * 0.3)**2
            
            if dist_sq < conversion_range_sq:
                # Success! Sacrifice the line and convert the point.
                
                # 1. Remove the sacrificed line
                self.state['lines'].remove(line_to_sac)
                self.state['shields'].pop(line_to_sac.get('id'), None) # Remove shield if it had one
                
                # 2. Convert the enemy point
                original_team_id = closest_enemy_point['teamId']
                original_team_name = self.state['teams'][original_team_id]['name']
                closest_enemy_point['teamId'] = teamId
                
                return {
                    'success': True,
                    'type': 'convert_point',
                    'converted_point': closest_enemy_point,
                    'sacrificed_line': line_to_sac,
                    'original_team_name': original_team_name
                }
        
        return {'success': False, 'reason': 'no enemy points in range'}

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
            'fight_attack': self.fight_action_attack_line,
            'fight_convert': self.fight_action_convert_point,
            'fortify_claim': self.fortify_action_claim_territory,
            'fortify_anchor': self.fortify_action_create_anchor,
            'fortify_mirror': self.fortify_action_mirror_structure,
            'sacrifice_nova': self.sacrifice_action_nova_burst,
            'defend_shield': self.shield_action_protect_line,
        }

        # --- Evaluate possible actions based on game state and exclusion list ---
        possible_actions = []
        action_preconditions = {
            'expand_add': len(team_point_ids) >= 2,
            'expand_extend': bool(team_lines),
            'expand_grow': bool(team_lines),
            'expand_fracture': bool(team_lines),
            'fight_attack': bool(team_lines) and any(l['teamId'] != teamId for l in self.state['lines']),
            'fight_convert': bool(team_lines) and any(p['teamId'] != teamId for p in self.state['points'].values()),
            'defend_shield': any(l.get('id') not in self.state['shields'] for l in team_lines),
            'fortify_claim': len(team_point_ids) >= 3,
            'fortify_anchor': len(team_point_ids) >= 3,
            'fortify_mirror': len(team_point_ids) >= 3,
            'sacrifice_nova': len(team_point_ids) > 1,
        }

        for name, is_possible in action_preconditions.items():
            if name not in exclude_actions and is_possible:
                possible_actions.append(name)
        
        if not possible_actions:
            return None, None

        # --- Apply trait-based weights to the *possible* actions ---
        base_weights = {
            'expand_add': 10, 'expand_extend': 8, 'expand_grow': 12, 'expand_fracture': 10, 'fight_attack': 10, 'fight_convert': 8,
            'fortify_claim': 8, 'fortify_anchor': 5, 'fortify_mirror': 6, 'sacrifice_nova': 3, 'defend_shield': 8,
        }
        trait_multipliers = {
            'Aggressive': {'fight_attack': 2.5, 'fight_convert': 2.0, 'sacrifice_nova': 1.5, 'defend_shield': 0.5},
            'Expansive':  {'expand_add': 2.0, 'expand_extend': 1.5, 'expand_grow': 2.5, 'expand_fracture': 2.0, 'fortify_claim': 0.5, 'fortify_mirror': 2.0},
            'Defensive':  {'defend_shield': 3.0, 'fortify_claim': 2.0, 'fortify_anchor': 1.5, 'fight_attack': 0.5, 'expand_grow': 0.5},
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
        """Performs start-of-turn maintenance and identifies active teams."""
        self.state['turn'] += 1
        self.state['action_in_turn'] = 0
        
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

        # --- Set up active teams for the turn ---
        active_teams = [teamId for teamId in self.state['teams'] if len(self.get_team_point_ids(teamId)) > 0]
        random.shuffle(active_teams) # Randomize action order each turn
        self.state['active_teams_this_turn'] = active_teams
        self.state['game_log'].append({'message': f"--- Turn {self.state['turn']} ---"})

    def _check_end_of_turn_victory_conditions(self):
        """Checks for victory conditions that are evaluated at the end of a full turn."""
        active_teams = self.state['active_teams_this_turn']
        
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
                self.state['game_log'].append({'message': self.state['victory_condition']})
                return
        else:
            self.state['sole_survivor_tracker'] = {'teamId': None, 'turns': 0}

        # 2. Max Turns Reached
        if self.state['turn'] >= self.state['max_turns']:
            self.state['game_phase'] = 'FINISHED'
            self.state['victory_condition'] = "Max turns reached."
            self.state['game_log'].append({'message': "Max turns reached. Game finished."})

    def run_next_action(self):
        """Runs a single successful action for the next team in the current turn."""
        if self.state['game_phase'] != 'RUNNING':
            return

        # Check if we need to start a new turn
        turn_is_over = self.state['action_in_turn'] >= len(self.state['active_teams_this_turn'])
        if turn_is_over:
            self._start_new_turn()
            
            # Check for immediate extinction after maintenance and team setup
            if not self.state['active_teams_this_turn']:
                self.state['game_phase'] = 'FINISHED'
                self.state['victory_condition'] = "Extinction"
                self.state['game_log'].append({'message': "All teams have been eliminated. Game over."})
                return

        # Get the current team to act
        teamId = self.state['active_teams_this_turn'][self.state['action_in_turn']]
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
            
        self.state['last_action_details'] = result if result.get('success') else {}
        
        # Log the final result. Invalid/failed actions are no longer logged individually.
        log_message = f"Team {team_name} "
        if result.get('success'):
            action_type = result.get('type')
            if action_type == 'add_line': log_message += "connected two points."
            elif action_type == 'extend_line': log_message += "extended a line to the border, creating a new point."
            elif action_type == 'grow_line': log_message += "grew a new branch, creating a new point."
            elif action_type == 'fracture_line': log_message += "fractured a line, creating a new point."
            elif action_type == 'attack_line': log_message += f"attacked and destroyed a line from Team {result['destroyed_team']}."
            elif action_type == 'convert_point': log_message += f"sacrificed a line to convert a point from Team {result['original_team_name']}."
            elif action_type == 'claim_territory': log_message += "fortified its position, claiming new territory."
            elif action_type == 'mirror_structure': log_message += f"mirrored its structure, creating {len(result['new_points'])} new points."
            elif action_type == 'create_anchor': log_message += "sacrificed a point to create a gravitational anchor."
            elif action_type == 'nova_burst': log_message += f"sacrificed a point in a nova burst, destroying {result['lines_destroyed']} lines."
            elif action_type == 'shield_line': log_message += "raised a defensive shield on one of its lines."
            else: log_message += "performed a successful action."
        else:
            log_message += "could not find a valid move and passed its turn."
            
        self.state['game_log'].append({'teamId': teamId, 'message': log_message})
        
        # Increment for next action
        self.state['action_in_turn'] += 1
        
        # If this was the last action of the turn, check for victory conditions
        if self.state['action_in_turn'] >= len(self.state['active_teams_this_turn']):
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

# --- Global Game Instance ---
# This is a singleton pattern. The Flask app will interact with this instance.
game = Game()

def init_game_state():
    """Resets the global game instance."""
    global game
    game.reset()