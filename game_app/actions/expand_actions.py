import random
import math
from itertools import combinations
from ..geometry import distance_sq, get_extended_border_point, clamp_and_round_point_coords, get_angle_bisector_vector
from .. import game_data

class ExpandActionsHandler:
    def __init__(self, game):
        self.game = game

    # --- Action Precondition Checks ---

    def can_perform_add_line(self, teamId):
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 2:
            return False, "Requires at least 2 points."

        # Check if primary effect is possible
        max_lines = len(team_point_ids) * (len(team_point_ids) - 1) / 2
        num_existing_lines = len({tuple(sorted((l['p1_id'], l['p2_id']))) for l in self.state['lines'] if l['teamId'] == teamId})
        if max_lines > num_existing_lines:
            return True, ""

        # If primary is not possible, check if fallback is possible
        if self.game.get_team_lines(teamId):
            return True, ""
        
        return False, "No new lines can be added and no existing lines to strengthen."

    def can_perform_extend_line(self, teamId):
        # Primary needs a valid extension. Fallback needs any line to strengthen.
        # So, the action is possible if there are any lines at all.
        if len(self.game.get_team_lines(teamId)) > 0:
            return True, ""
        return False, "No lines to extend or strengthen."

    def can_perform_bisect_angle(self, teamId):
        # Action needs a point with at least 2 lines connected to it.
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 3: # Need at least a V shape
            return False, "Requires at least 3 points to form an angle."
        
        # Check if primary is possible
        adj = {pid: 0 for pid in team_point_ids}
        for line in self.game.get_team_lines(teamId):
            if line['p1_id'] in adj: adj[line['p1_id']] += 1
            if line['p2_id'] in adj: adj[line['p2_id']] += 1
        
        if any(degree >= 2 for degree in adj.values()):
            return True, ""

        # Check if fallback is possible (any line to strengthen)
        if self.game.get_team_lines(teamId):
            return True, ""

        return False, "No angles to bisect and no lines to strengthen."

    def can_perform_fracture_line(self, teamId):
        # Primary needs a fracturable line. Fallback needs any line.
        # So, the action is possible if there are any lines at all.
        if len(self.game.get_team_lines(teamId)) > 0:
            return True, ""
        return False, "No lines to fracture or strengthen."

    def can_perform_spawn_point(self, teamId):
        # With the new border-spawn fallback, this action is always possible if a point exists.
        can_perform = len(self.game.get_team_point_ids(teamId)) > 0
        reason = "" if can_perform else "Requires at least one point to spawn from."
        return can_perform, reason

    def can_perform_create_orbital(self, teamId):
        # Primary needs >= 5 points. Fallback needs >=1 point and >0 lines.
        num_points = len(self.game.get_team_point_ids(teamId))
        if num_points >= 5:
            return True, ""
        
        if num_points >= 1 and len(self.game.get_team_lines(teamId)) > 0:
            return True, ""

        return False, "Requires at least 5 points, or at least 1 point and 1 line for fallback."

    def can_perform_mirror_point(self, teamId):
        # Primary needs >= 2 points. Fallback needs any line.
        has_points = len(self.game.get_team_point_ids(teamId)) >= 2
        has_lines = len(self.game.get_team_lines(teamId)) > 0
        can_perform = has_points or has_lines
        reason = "" if can_perform else "Requires at least 2 points to mirror or a line to strengthen."
        return can_perform, reason

    # --- End Precondition Checks ---

    @property
    def state(self):
        """Provides direct access to the game's current state dictionary."""
        return self.game.state

    def add_line(self, teamId):
        """[EXPAND ACTION]: Add a line between two random points. If not possible, strengthens an existing line."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 2:
            return {'success': False, 'reason': 'not enough points'}

        # Using set operations is cleaner and often faster
        existing_line_keys = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in self.state['lines'] if l['teamId'] == teamId}
        
        possible_pairs = [
            (p1, p2) for p1, p2 in combinations(team_point_ids, 2) 
            if tuple(sorted((p1, p2))) not in existing_line_keys
        ]

        if possible_pairs:
            p1_id, p2_id = random.choice(possible_pairs)
            line_id = self.game._generate_id('l')
            new_line = {"id": line_id, "p1_id": p1_id, "p2_id": p2_id, "teamId": teamId}
            self.state['lines'].append(new_line)
            return {'success': True, 'type': 'add_line', 'line': new_line}
        else:
            # Fallback effect: Strengthen an existing line
            return self.game._fallback_strengthen_random_line(teamId, 'add_line')

    def _check_and_add_extension(self, p_start, p_end, origin_point_id, teamId, extensions_list):
        """Helper to check if a line extension is valid and add it to a list."""
        border_point = get_extended_border_point(
            p_start, p_end, self.state['grid_size'],
            self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])
        )
        if border_point:
            is_valid, _ = self.game.is_spawn_location_valid(border_point, teamId)
            if is_valid:
                extensions_list.append({'origin_point_id': origin_point_id, 'border_point': border_point})

    def _find_possible_extensions(self, teamId):
        """Finds all possible line extensions to the border."""
        team_lines = self.game.get_team_lines(teamId)
        points = self.state['points']
        possible_extensions = []
        for line in team_lines:
            if line['p1_id'] not in points or line['p2_id'] not in points:
                continue
            p1 = points[line['p1_id']]
            p2 = points[line['p2_id']]
            
            # Try extending from p1 through p2
            self._check_and_add_extension(p1, p2, p2['id'], teamId, possible_extensions)
            
            # Try extending from p2 through p1
            self._check_and_add_extension(p2, p1, p1['id'], teamId, possible_extensions)
            
        return possible_extensions

    def extend_line(self, teamId):
        """[EXPAND ACTION]: Extend a line to the border to create a new point. If not possible, strengthens a line."""
        possible_extensions = self._find_possible_extensions(teamId)

        if not possible_extensions:
            # Fallback: Strengthen an existing line
            return self.game._fallback_strengthen_random_line(teamId, 'extend')

        chosen_extension = random.choice(possible_extensions)
        border_point = chosen_extension['border_point']
        origin_point_id = chosen_extension['origin_point_id']
        
        # Check if this extension is empowered by an I-Rune
        is_empowered = False
        team_i_runes = self.state.get('runes', {}).get(teamId, {}).get('i_shape', [])
        for i_rune in team_i_runes:
            if origin_point_id in i_rune.get('endpoints', []):
                is_empowered = True
                break

        # Create new point with a unique ID
        new_point_id = self.game._generate_id('p')
        new_point = {**border_point, "teamId": teamId, "id": new_point_id}
        self.state['points'][new_point_id] = new_point
        
        # Check for Ley Line bonus
        bonus_line = self.game._check_and_apply_ley_line_bonus(new_point)

        result_payload = {'success': True, 'type': 'extend_line', 'new_point': new_point, 'is_empowered': is_empowered}
        if bonus_line:
            result_payload['bonus_line'] = bonus_line
        
        if is_empowered:
            # Empowered extension also creates a line to the new point
            line_id = self.game._generate_id('l')
            new_line = {"id": line_id, "p1_id": origin_point_id, "p2_id": new_point_id, "teamId": teamId}
            self.state['lines'].append(new_line)
            result_payload['new_line'] = new_line
        
        return result_payload

    def _find_fracturable_lines(self, teamId):
        """Finds all lines that are eligible for fracturing."""
        team_lines = self.game.get_team_lines(teamId)
        points = self.state['points']
        fracturable_lines = []
        
        # Get territory boundary lines to exclude them from fracturing
        territory_line_keys = self.game._get_all_territory_boundary_line_keys(teamId)

        for line in team_lines:
            if tuple(sorted((line['p1_id'], line['p2_id']))) in territory_line_keys:
                continue
            if line['p1_id'] in points and line['p2_id'] in points:
                p1 = points[line['p1_id']]
                p2 = points[line['p2_id']]
                if distance_sq(p1, p2) >= game_data.GAME_PARAMETERS['FRACTURE_LINE_MIN_LENGTH_SQ']:
                    fracturable_lines.append(line)
        return fracturable_lines

    def fracture_line(self, teamId):
        """[EXPAND ACTION]: Splits a line into two, creating a new point. If not possible, strengthens a line."""
        fracturable_lines = self._find_fracturable_lines(teamId)
        if not fracturable_lines:
            # Fallback: Strengthen an existing line
            return self.game._fallback_strengthen_random_line(teamId, 'fracture')

        line_to_fracture = random.choice(fracturable_lines)
        points = self.state['points']
        p1 = points[line_to_fracture['p1_id']]
        p2 = points[line_to_fracture['p2_id']]

        # Find a new point on the segment
        ratio = random.uniform(0.25, 0.75)
        new_x = p1['x'] + (p2['x'] - p1['x']) * ratio
        new_y = p1['y'] + (p2['y'] - p1['y']) * ratio

        # Create new point, ensuring integer coordinates and clamping to grid boundaries
        new_point_coords = clamp_and_round_point_coords({'x': new_x, 'y': new_y}, self.state['grid_size'])

        new_point_id = self.game._generate_id('p')
        new_point = {**new_point_coords, "teamId": teamId, "id": new_point_id}
        self.state['points'][new_point_id] = new_point

        # Check for Ley Line bonus
        bonus_line = self.game._check_and_apply_ley_line_bonus(new_point)

        # Remove old line and its potential shield/strength
        self.game._delete_line(line_to_fracture)

        # Create two new lines
        line_id_1 = self.game._generate_id('l')
        new_line_1 = {"id": line_id_1, "p1_id": line_to_fracture['p1_id'], "p2_id": new_point_id, "teamId": teamId}
        line_id_2 = self.game._generate_id('l')
        new_line_2 = {"id": line_id_2, "p1_id": new_point_id, "p2_id": line_to_fracture['p2_id'], "teamId": teamId}
        self.state['lines'].extend([new_line_1, new_line_2])

        result_payload = {
            'success': True,
            'type': 'fracture_line',
            'new_point': new_point,
            'new_line1': new_line_1,
            'new_line2': new_line_2,
            'old_line': line_to_fracture
        }
        if bonus_line:
            result_payload['bonus_line'] = bonus_line
        
        return result_payload

    def spawn_point(self, teamId):
        """[EXPAND ACTION]: Creates a new point near an existing one. If not possible, strengthens a line or spawns on border."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if not team_point_ids:
            return {'success': False, 'reason': 'no points to spawn from'}

        # --- Primary Effect: Try to spawn nearby ---
        for _ in range(10):
            p_origin_id = random.choice(team_point_ids)
            p_origin = self.state['points'][p_origin_id]

            angle = random.uniform(0, 2 * math.pi)
            radius = self.state['grid_size'] * random.uniform(0.05, 0.15)
            
            new_x = p_origin['x'] + math.cos(angle) * radius
            new_y = p_origin['y'] + math.sin(angle) * radius
            
            new_p_coords = clamp_and_round_point_coords({'x': new_x, 'y': new_y}, self.state['grid_size'])
            is_valid, _ = self.game.is_spawn_location_valid(new_p_coords, teamId)
            if not is_valid:
                continue

            new_point_id = self.game._generate_id('p')
            new_point = {**new_p_coords, "teamId": teamId, "id": new_point_id}
            self.state['points'][new_point_id] = new_point
            bonus_line = self.game._check_and_apply_ley_line_bonus(new_point)
            result_payload = {'success': True, 'type': 'spawn_point', 'new_point': new_point}
            if bonus_line: result_payload['bonus_line'] = bonus_line
            return result_payload

        # --- Fallback 1: Strengthen a random line ---
        strengthen_result = self.game._fallback_strengthen_random_line(teamId, 'spawn')
        if strengthen_result.get('success'):
            return strengthen_result
        
        # --- Fallback 2: Spawn on border from a random point ---
        # This case is reached if spawn failed and there are no lines to strengthen.
        p_origin_id = random.choice(team_point_ids)
        p_origin = self.state['points'][p_origin_id]

        for _ in range(10): # try 10 random directions
            angle = random.uniform(0, 2 * math.pi)
            p_dummy_end = {
                'x': p_origin['x'] + math.cos(angle) * self.state['grid_size'] * 2,
                'y': p_origin['y'] + math.sin(angle) * self.state['grid_size'] * 2
            }
            border_point = get_extended_border_point(
                p_origin, p_dummy_end, self.state['grid_size'],
                self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])
            )
            if border_point:
                new_point = self.game._helper_spawn_on_border(teamId, border_point)
                if new_point:
                    return {'success': True, 'type': 'spawn_fizzle_border_spawn', 'new_point': new_point}

        return {'success': False, 'reason': 'all spawn strategies, including fallbacks, failed'}

    def mirror_point(self, teamId):
        """[EXPAND ACTION]: Reflects a friendly point through another to create a new symmetrical point."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 2:
            return self.game._fallback_strengthen_random_line(teamId, 'mirror_point')

        points = self.state['points']
        possible_pairs = list(combinations(team_point_ids, 2))
        random.shuffle(possible_pairs)

        for p1_id, p2_id in possible_pairs:
            # Try reflecting p1 through p2, and p2 through p1
            for p_source_id, p_pivot_id in [(p1_id, p2_id), (p2_id, p1_id)]:
                p_source = points[p_source_id]
                p_pivot = points[p_pivot_id]

                # Calculate reflected point: P_new = P_pivot + (P_pivot - P_source)
                new_x = p_pivot['x'] + (p_pivot['x'] - p_source['x'])
                new_y = p_pivot['y'] + (p_pivot['y'] - p_source['y'])

                new_point_coords = clamp_and_round_point_coords({'x': new_x, 'y': new_y}, self.state['grid_size'])
                is_valid, _ = self.game.is_spawn_location_valid(new_point_coords, teamId)

                if is_valid:
                    # --- Primary Effect: Create Mirrored Point ---
                    new_point_id = self.game._generate_id('p')
                    new_point = {**new_point_coords, "teamId": teamId, "id": new_point_id}
                    self.state['points'][new_point_id] = new_point

                    # Check for Ley Line bonus
                    bonus_line = self.game._check_and_apply_ley_line_bonus(new_point)

                    result_payload = {
                        'success': True, 'type': 'mirror_point', 'new_point': new_point,
                        'source_point_id': p_source_id, 'pivot_point_id': p_pivot_id
                    }
                    if bonus_line:
                        result_payload['bonus_line'] = bonus_line
                    
                    return result_payload
        
        # --- Fallback: Strengthen the line between a pair ---
        all_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.game.get_team_lines(teamId)}
        for p1_id, p2_id in possible_pairs:
            line_key = tuple(sorted((p1_id, p2_id)))
            if line_key in all_lines_by_points:
                line_to_strengthen = all_lines_by_points[line_key]
                if self.game._strengthen_line(line_to_strengthen):
                    return {
                        'success': True, 'type': 'mirror_point_fizzle_strengthen',
                        'strengthened_line': line_to_strengthen
                    }
        
        # Final fallback if no lines existed between pairs
        return self.game._fallback_strengthen_random_line(teamId, 'mirror_point')

    def _create_orbital_fallback_strengthen(self, teamId):
        """Helper for the orbital fallback logic: strengthen lines around a central point."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if not team_point_ids:
             return {'success': False, 'reason': 'no points to use for fallback'}

        p_center_id_fallback = random.choice(team_point_ids)
        lines_to_strengthen = [l for l in self.game.get_team_lines(teamId) if l['p1_id'] == p_center_id_fallback or l['p2_id'] == p_center_id_fallback]
        
        if not lines_to_strengthen:
             return {'success': False, 'reason': 'no lines to strengthen for orbital fallback'}
        
        strengthened_lines_info = []
        for line in lines_to_strengthen:
            if self.game._strengthen_line(line):
                strengthened_lines_info.append(line)
        
        if not strengthened_lines_info:
            return {'success': False, 'reason': 'all connected lines are already at maximum strength'}

        return {
            'success': True, 'type': 'orbital_fizzle_strengthen',
            'center_point_id': p_center_id_fallback, 'strengthened_lines': strengthened_lines_info
        }

    def create_orbital(self, teamId):
        """[EXPAND ACTION]: Creates a new orbital structure. If not possible, strengthens lines around a potential center."""
        team_point_ids = self.game.get_team_point_ids(teamId)

        # Primary effect requires at least 5 points.
        if len(team_point_ids) >= 5:
            shuffled_point_ids = random.sample(team_point_ids, len(team_point_ids))

            # Try a few times to find a valid spot
            for p_center_id in shuffled_point_ids[:5]:
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
                    
                    new_p_coords = clamp_and_round_point_coords({'x': new_x, 'y': new_y}, self.state['grid_size'])
                    is_valid, _ = self.game.is_spawn_location_valid(new_p_coords, teamId, min_dist_sq=2.0)
                    if not is_valid:
                        valid_orbital = False; break
                    
                    is_too_close_to_sibling = any(distance_sq(new_p_coords, p_sib) < 2.0 for p_sib in new_points_to_create)
                    if is_too_close_to_sibling:
                        valid_orbital = False; break
                    
                    new_point_id = self.game._generate_id('p')
                    new_points_to_create.append({**new_p_coords, "teamId": teamId, "id": new_point_id})
                
                if not valid_orbital:
                    continue

                # --- Primary Effect: Create Orbital ---
                created_points = []
                created_lines = []
                bonus_lines = []
                for new_p_data in new_points_to_create:
                    self.state['points'][new_p_data['id']] = new_p_data
                    created_points.append(new_p_data)
                    
                    # Check for Ley Line bonus on each created point
                    bonus_line = self.game._check_and_apply_ley_line_bonus(new_p_data)
                    if bonus_line:
                        bonus_lines.append(bonus_line)

                    line_id = self.game._generate_id('l')
                    new_line = {"id": line_id, "p1_id": p_center_id, "p2_id": new_p_data['id'], "teamId": teamId}
                    self.state['lines'].append(new_line)
                    created_lines.append(new_line)
                
                result_payload = {
                    'success': True, 'type': 'create_orbital', 'center_point_id': p_center_id,
                    'new_points': created_points, 'new_lines': created_lines
                }
                if bonus_lines:
                    result_payload['bonus_lines'] = bonus_lines
                
                return result_payload
        
        # This is reached if len < 5 OR if the primary effect failed to find a spot.
        return self._create_orbital_fallback_strengthen(teamId)

    def bisect_angle(self, teamId):
        """[EXPAND ACTION]: Creates a new point by bisecting an angle. If not possible, strengthens a line."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        team_lines = self.game.get_team_lines(teamId)
        
        # Build adjacency list to find vertices
        adj = {pid: [] for pid in team_point_ids}
        for line in team_lines:
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].append(line['p2_id'])
                adj[line['p2_id']].append(line['p1_id'])
        
        possible_vertices = [pid for pid, neighbors in adj.items() if len(neighbors) >= 2]
        random.shuffle(possible_vertices)
        
        points_map = self.state['points']

        for vertex_id in possible_vertices:
            p_vertex = points_map.get(vertex_id)
            if not p_vertex: continue

            # Try a few combinations of legs from this vertex
            neighbor_pairs = list(combinations(adj[vertex_id], 2))
            random.shuffle(neighbor_pairs)

            for leg1_id, leg2_id in neighbor_pairs[:3]:
                p_leg1 = points_map.get(leg1_id)
                p_leg2 = points_map.get(leg2_id)
                if not p_leg1 or not p_leg2: continue

                bisector_v = get_angle_bisector_vector(p_vertex, p_leg1, p_leg2)
                if not bisector_v: continue

                # Spawn point a short distance along the bisector
                growth_length = self.state['grid_size'] * random.uniform(0.1, 0.2)
                new_x = p_vertex['x'] + bisector_v['x'] * growth_length
                new_y = p_vertex['y'] + bisector_v['y'] * growth_length

                new_point_coords = clamp_and_round_point_coords({'x': new_x, 'y': new_y}, self.state['grid_size'])
                is_valid, _ = self.game.is_spawn_location_valid(new_point_coords, teamId)
                if not is_valid: continue

                # --- Primary Effect: Create Bisected Point ---
                new_point_id = self.game._generate_id('p')
                new_point = {**new_point_coords, "teamId": teamId, "id": new_point_id}
                self.state['points'][new_point_id] = new_point

                bonus_line = self.game._check_and_apply_ley_line_bonus(new_point)

                # Create a line connecting the new point to the vertex
                line_id = self.game._generate_id('l')
                new_line = {"id": line_id, "p1_id": vertex_id, "p2_id": new_point_id, "teamId": teamId}
                self.state['lines'].append(new_line)
                
                result_payload = {'success': True, 'type': 'bisect_angle', 'new_point': new_point, 'new_line': new_line}
                if bonus_line:
                    result_payload['bonus_line'] = bonus_line
                
                return result_payload

        # --- Fallback: Strengthen one of the lines of a random angle ---
        if possible_vertices:
            vertex_id = random.choice(possible_vertices)
            leg_ids = adj.get(vertex_id, [])
            if not leg_ids:
                return self.game._fallback_strengthen_random_line(teamId, 'bisect')
            
            lines_of_angle = []
            all_team_lines = self.game.get_team_lines(teamId)
            for l in all_team_lines:
                if (l['p1_id'] == vertex_id and l['p2_id'] in leg_ids) or \
                   (l['p2_id'] == vertex_id and l['p1_id'] in leg_ids):
                    lines_of_angle.append(l)

            if lines_of_angle:
                line_to_strengthen = random.choice(lines_of_angle)
                if self.game._strengthen_line(line_to_strengthen):
                     return {'success': True, 'type': 'bisect_fizzle_strengthen', 'strengthened_line': line_to_strengthen}
        
        # Final fallback if even strengthening a specific line fails (e.g., they are all maxed out)
        return self.game._fallback_strengthen_random_line(teamId, 'bisect')