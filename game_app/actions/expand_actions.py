import random
import math
import uuid
from itertools import combinations
from ..geometry import distance_sq, get_extended_border_point

class ExpandActionsHandler:
    def __init__(self, game):
        self.game = game

    # --- Action Precondition Checks ---

    def can_perform_add_line(self, teamId):
        return len(self.game.get_team_point_ids(teamId)) >= 2, "Requires at least 2 points."

    def can_perform_extend_line(self, teamId):
        can_perform = len(self._find_possible_extensions(teamId)) > 0
        return can_perform, "No lines can be validly extended."

    def can_perform_grow_line(self, teamId):
        return len(self.game.get_team_lines(teamId)) > 0, "Requires at least 1 line to grow from."

    def can_perform_fracture_line(self, teamId):
        can_perform = len(self._find_fracturable_lines(teamId)) > 0
        return can_perform, "No non-territory lines long enough to fracture."

    def can_perform_spawn_point(self, teamId):
        return len(self.game.get_team_point_ids(teamId)) > 0, "Requires at least 1 point to spawn from."

    def can_perform_create_orbital(self, teamId):
        return len(self.game.get_team_point_ids(teamId)) >= 5, "Requires at least 5 points."

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
            border_point1 = get_extended_border_point(
                p1, p2, self.state['grid_size'],
                self.state.get('fissures', []), self.state.get('barricades', [])
            )
            if border_point1:
                is_valid, _ = self.game._is_spawn_location_valid(border_point1, teamId)
                if is_valid:
                    possible_extensions.append({'origin_point_id': p2['id'], 'border_point': border_point1})
            
            # Try extending from p2 through p1
            border_point2 = get_extended_border_point(
                p2, p1, self.state['grid_size'],
                self.state.get('fissures', []), self.state.get('barricades', [])
            )
            if border_point2:
                is_valid, _ = self.game._is_spawn_location_valid(border_point2, teamId)
                if is_valid:
                    possible_extensions.append({'origin_point_id': p1['id'], 'border_point': border_point2})
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
        
        result_payload = {'success': True, 'type': 'extend_line', 'new_point': new_point, 'is_empowered': is_empowered}
        
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
        territory_lines = set()
        for t in self.state.get('territories', []):
            if t['teamId'] == teamId:
                p_ids = t['point_ids']
                territory_lines.add(tuple(sorted((p_ids[0], p_ids[1]))))
                territory_lines.add(tuple(sorted((p_ids[1], p_ids[2]))))
                territory_lines.add(tuple(sorted((p_ids[2], p_ids[0]))))

        for line in team_lines:
            if tuple(sorted((line['p1_id'], line['p2_id']))) in territory_lines:
                continue
            if line['p1_id'] in points and line['p2_id'] in points:
                p1 = points[line['p1_id']]
                p2 = points[line['p2_id']]
                if distance_sq(p1, p2) >= 4.0: # min length of 2
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
        grid_size = self.state['grid_size']
        final_x = round(max(0, min(grid_size - 1, new_x)))
        final_y = round(max(0, min(grid_size - 1, new_y)))

        new_point_id = self.game._generate_id('p')
        new_point = {"x": final_x, "y": final_y, "teamId": teamId, "id": new_point_id}
        self.state['points'][new_point_id] = new_point

        # Remove old line and its potential shield
        self.state['lines'].remove(line_to_fracture)
        self.state['shields'].pop(line_to_fracture.get('id'), None)

        # Create two new lines
        line_id_1 = self.game._generate_id('l')
        new_line_1 = {"id": line_id_1, "p1_id": line_to_fracture['p1_id'], "p2_id": new_point_id, "teamId": teamId}
        line_id_2 = self.game._generate_id('l')
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

    def spawn_point(self, teamId):
        """[EXPAND ACTION]: Creates a new point near an existing one. If not possible, strengthens a line."""
        team_point_ids = self.game.get_team_point_ids(teamId)
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
            is_valid, reason = self.game._is_spawn_location_valid(new_p_coords, teamId)
            if not is_valid:
                continue

            # We found a valid spawn, create the new point
            new_point_id = self.game._generate_id('p')
            new_point = {"x": final_x, "y": final_y, "teamId": teamId, "id": new_point_id}
            self.state['points'][new_point_id] = new_point

            return {'success': True, 'type': 'spawn_point', 'new_point': new_point}

        # Fallback: Strengthen a random line
        return self.game._fallback_strengthen_random_line(teamId, 'spawn')

    def create_orbital(self, teamId):
        """[EXPAND ACTION]: Creates a new orbital structure. If not possible, strengthens lines around a potential center."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 5:
            return {'success': False, 'reason': 'not enough points to create an orbital'}

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
                
                grid_size = self.state['grid_size']
                final_x = round(max(0, min(grid_size - 1, new_x)))
                final_y = round(max(0, min(grid_size - 1, new_y)))

                new_p_coords = {'x': final_x, 'y': final_y}
                is_valid, _ = self.game._is_spawn_location_valid(new_p_coords, teamId, min_dist_sq=2.0)
                if not is_valid:
                    valid_orbital = False; break
                
                is_too_close_to_sibling = any(distance_sq(new_p_coords, p_sib) < 2.0 for p_sib in new_points_to_create)
                if is_too_close_to_sibling:
                    valid_orbital = False; break
                
                new_point_id = self.game._generate_id('p')
                new_points_to_create.append({"x": final_x, "y": final_y, "teamId": teamId, "id": new_point_id})
            
            if not valid_orbital:
                continue

            # --- Primary Effect: Create Orbital ---
            created_points = []
            created_lines = []
            for new_p_data in new_points_to_create:
                self.state['points'][new_p_data['id']] = new_p_data
                created_points.append(new_p_data)
                line_id = self.game._generate_id('l')
                new_line = {"id": line_id, "p1_id": p_center_id, "p2_id": new_p_data['id'], "teamId": teamId}
                self.state['lines'].append(new_line)
                created_lines.append(new_line)
            
            return {
                'success': True, 'type': 'create_orbital', 'center_point_id': p_center_id,
                'new_points': created_points, 'new_lines': created_lines
            }
        
        # --- Fallback: Strengthen lines around a chosen center ---
        p_center_id_fallback = random.choice(team_point_ids)
        lines_to_strengthen = [l for l in self.game.get_team_lines(teamId) if l['p1_id'] == p_center_id_fallback or l['p2_id'] == p_center_id_fallback]
        
        if not lines_to_strengthen:
             return {'success': False, 'reason': 'could not find a valid position for an orbital and no lines to strengthen'}
        
        strengthened_lines_info = []
        max_strength = 3
        for line in lines_to_strengthen:
            line_id = line.get('id')
            if line_id:
                current_strength = self.state['line_strengths'].get(line_id, 0)
                if current_strength < max_strength:
                    self.state['line_strengths'][line_id] = current_strength + 1
                    strengthened_lines_info.append(line)

        return {
            'success': True, 'type': 'orbital_fizzle_strengthen',
            'center_point_id': p_center_id_fallback, 'strengthened_lines': strengthened_lines_info
        }

    def grow_line(self, teamId):
        """[EXPAND ACTION]: Grows a new short line from an existing point. If not possible, strengthens a random friendly line."""
        team_lines = self.game.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to grow from'}

        shuffled_lines = random.sample(team_lines, len(team_lines))
        points_map = self.state['points']
        
        for line in shuffled_lines:
            if not (line['p1_id'] in points_map and line['p2_id'] in points_map):
                continue
            
            # Try to grow from this line
            for _ in range(2): # Try both endpoints
                p_origin_id, p_other_id = random.choice([(line['p1_id'], line['p2_id']), (line['p2_id'], line['p1_id'])])
                p_origin = points_map[p_origin_id]
                p_other = points_map[p_other_id]

                vx = p_origin['x'] - p_other['x']
                vy = p_origin['y'] - p_other['y']
                angle = random.uniform(-math.pi * 2/3, math.pi * 2/3)
                new_vx = vx * math.cos(angle) - vy * math.sin(angle)
                new_vy = vx * math.sin(angle) + vy * math.cos(angle)
                mag = math.sqrt(new_vx**2 + new_vy**2)
                if mag == 0: continue
                
                growth_length = self.state['grid_size'] * random.uniform(0.1, 0.2)
                new_x = p_origin['x'] + (new_vx / mag) * growth_length
                new_y = p_origin['y'] + (new_vy / mag) * growth_length

                grid_size = self.state['grid_size']
                if not (0 <= new_x < grid_size and 0 <= new_y < grid_size):
                    continue

                new_point_coords = {"x": round(new_x), "y": round(new_y)}
                is_valid, _ = self.game._is_spawn_location_valid(new_point_coords, teamId)
                if not is_valid:
                    continue

                # --- Primary Effect: Grow Line ---
                new_point_id = self.game._generate_id('p')
                new_point = {**new_point_coords, "teamId": teamId, "id": new_point_id}
                self.state['points'][new_point_id] = new_point
                line_id = self.game._generate_id('l')
                new_line = {"id": line_id, "p1_id": p_origin_id, "p2_id": new_point_id, "teamId": teamId}
                self.state['lines'].append(new_line)
                return {'success': True, 'type': 'grow_line', 'new_point': new_point, 'new_line': new_line}

        # --- Fallback: Strengthen a line ---
        return self.game._fallback_strengthen_random_line(teamId, 'grow')