import random
import math
from itertools import combinations
from ..geometry import distance_sq, reflect_point, rotate_point, is_rectangle, is_regular_pentagon, points_centroid, clamp_and_round_point_coords, get_edges_by_distance, polygon_area

class FortifyActionsHandler:
    def __init__(self, game):
        self.game = game

    def _find_a_valid_mirror(self, teamId, num_attempts=5):
        """
        Tries to find a valid mirror operation by randomly selecting axes and points.
        Returns a dictionary with operation details if successful, otherwise None.
        """
        team_point_ids = self.game.query.get_team_point_ids(teamId)
        if len(team_point_ids) < 3:
            return None

        for _ in range(num_attempts):
            # 1. Select axis
            axis_p_ids = random.sample(team_point_ids, 2)
            p_axis1 = self.state['points'][axis_p_ids[0]]
            p_axis2 = self.state['points'][axis_p_ids[1]]
            if distance_sq(p_axis1, p_axis2) < 4.0: continue

            # 2. Select points to mirror
            other_point_ids = [pid for pid in team_point_ids if pid not in axis_p_ids]
            if not other_point_ids: continue
            
            num_to_mirror = min(len(other_point_ids), random.randint(1, 2))
            points_to_mirror_ids = random.sample(other_point_ids, num_to_mirror)
            
            new_points_to_create = []
            grid_size = self.state['grid_size']
            all_reflections_valid = True

            # 3. Reflect and validate
            for pid in points_to_mirror_ids:
                point_to_mirror = self.state['points'][pid]
                reflected_p = reflect_point(point_to_mirror, p_axis1, p_axis2)
                
                if not reflected_p or not (0 <= reflected_p['x'] < grid_size and 0 <= reflected_p['y'] < grid_size):
                    all_reflections_valid = False; break
                
                reflected_p_int = clamp_and_round_point_coords(reflected_p, grid_size)
                is_valid, _ = self.game.is_spawn_location_valid(reflected_p_int, teamId)
                if not is_valid:
                    all_reflections_valid = False; break
                
                new_point_id = self.game._generate_id('p')
                new_points_to_create.append({**reflected_p_int, "teamId": teamId, "id": new_point_id})
            
            if all_reflections_valid and new_points_to_create:
                return {
                    'axis_p_ids': axis_p_ids,
                    'points_to_mirror_ids': points_to_mirror_ids,
                    'new_points_to_create': new_points_to_create
                }
        
        return None

    def _find_possible_monoliths_and_fallbacks(self, teamId):
        """Helper to find valid monoliths (tall rectangles) and regular rectangles for fallback reinforcement."""
        team_point_ids = self.game.query.get_team_point_ids(teamId)
        if len(team_point_ids) < 4:
            return [], []

        existing_monolith_points = {pid for m in self.state.get('monoliths', {}).values() for pid in m['point_ids']}

        possible_monoliths = []
        fallback_candidates = []
        
        all_rectangles = self.game.formation_manager.find_all_rectangles(
            team_point_ids, self.game.query.get_team_lines(teamId), self.state['points']
        )
        
        for rect_data in all_rectangles:
            p_ids_tuple = tuple(rect_data['point_ids'])
            if any(pid in existing_monolith_points for pid in p_ids_tuple):
                continue

            if rect_data['aspect_ratio'] > 3.0:
                center_x = sum(p['x'] for p in rect_data['points']) / 4
                center_y = sum(p['y'] for p in rect_data['points']) / 4
                possible_monoliths.append({
                    'point_ids': list(p_ids_tuple),
                    'center_coords': {'x': center_x, 'y': center_y},
                    'aspect_ratio': rect_data['aspect_ratio']
                })
            else:
                edge_data = get_edges_by_distance(rect_data['points'])
                side_pairs = edge_data['sides']
                fallback_candidates.append({'point_ids': list(p_ids_tuple), 'side_pairs': side_pairs})
        
        return possible_monoliths, fallback_candidates

    def _find_possible_purifiers(self, teamId):
        """
        Optimized helper to find valid pentagonal formations for a Purifier.
        Instead of a brute-force O(N^5) check, this builds up from corners (p1-p2-p3)
        and uses geometric constraints to find the remaining two points, significantly
        reducing the search space.
        """
        team_point_ids = self.game.query.get_team_point_ids(teamId)
        if len(team_point_ids) < 5:
            return []

        points = self.state['points']
        team_lines = self.game.query.get_team_lines(teamId)
        existing_lines_set = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in team_lines}
        adj = self.game.formation_manager.get_adjacency_list(team_point_ids, team_lines)
        
        existing_purifier_points = {pid for p_list in self.state.get('purifiers', {}).values() for p in p_list for pid in p['point_ids']}
        
        possible_purifiers = []
        checked_pentagons = set()

        # Geometric constants with tolerance
        cos_108 = math.cos(math.radians(108))
        phi_sq = ((1 + math.sqrt(5)) / 2)**2
        side_tolerance_sq = 0.5
        diag_tolerance_sq = side_tolerance_sq * phi_sq * 1.2 # Allow slightly more tolerance for diagonals
        angle_tolerance = 0.05 # Cosine tolerance

        # 1. Iterate over every point as a potential central vertex of a corner (p2)
        for p2_id in team_point_ids:
            if p2_id in existing_purifier_points: continue
            
            p2 = points[p2_id]
            neighbors = list(adj.get(p2_id, []))
            if len(neighbors) < 2: continue
            
            # 2. Iterate over pairs of neighbors to form a corner (p1-p2-p3)
            for p1_id, p3_id in combinations(neighbors, 2):
                if p1_id in existing_purifier_points or p3_id in existing_purifier_points: continue
                
                p1, p3 = points[p1_id], points[p3_id]
                
                s1_sq = distance_sq(p1, p2)
                s2_sq = distance_sq(p2, p3)
                if abs(s1_sq - s2_sq) > side_tolerance_sq: continue
                if s1_sq < 1.0: continue # Ignore tiny formations

                # Check angle p1-p2-p3 is ~108 degrees
                v1 = {'x': p1['x'] - p2['x'], 'y': p1['y'] - p2['y']}
                v2 = {'x': p3['x'] - p2['x'], 'y': p3['y'] - p2['y']}
                dot = v1['x'] * v2['x'] + v1['y'] * v2['y']
                mag_prod = math.sqrt(s1_sq * s2_sq)
                if mag_prod < 0.1: continue
                cos_theta = dot / mag_prod
                if abs(cos_theta - cos_108) > angle_tolerance: continue

                # 3. We have a valid corner. Find candidate points for p4 and p5.
                side_len_sq = s1_sq
                diag_len_sq = side_len_sq * phi_sq
                
                # Find candidates for p5 (connected to p1)
                for p5_id in adj.get(p1_id, []):
                    if p5_id == p2_id or p5_id in existing_purifier_points: continue
                    p5 = points[p5_id]
                    if abs(distance_sq(p1, p5) - side_len_sq) > side_tolerance_sq: continue
                    if abs(distance_sq(p2, p5) - diag_len_sq) > diag_tolerance_sq: continue
                    
                    # Find candidates for p4 (connected to p3 and p5)
                    p4_candidates = adj.get(p3_id, set()).intersection(adj.get(p5_id, set()))
                    for p4_id in p4_candidates:
                        if p4_id in {p1_id, p2_id, p3_id, p5_id} or p4_id in existing_purifier_points: continue
                        p4 = points[p4_id]

                        # 4. We have a full 5-point candidate. Verify all distances.
                        p_ids = [p1_id, p2_id, p3_id, p4_id, p5_id]
                        p_list_for_check = [p1, p2, p3, p4, p5]

                        if is_regular_pentagon(*p_list_for_check):
                             # 5. Verify all 5 side lines exist.
                            edge_data = get_edges_by_distance(p_list_for_check)
                            side_pairs = edge_data['sides']
                            if len(side_pairs) == 5 and all(tuple(sorted(pair)) in existing_lines_set for pair in side_pairs):
                                p_ids_tuple = tuple(sorted(p_ids))
                                if p_ids_tuple not in checked_pentagons:
                                    possible_purifiers.append({'point_ids': list(p_ids_tuple)})
                                    checked_pentagons.add(p_ids_tuple)
        return possible_purifiers

    @property
    def state(self):
        """Provides direct access to the game's current state dictionary."""
        return self.game.state

    def shield_line(self, teamId):
        """[FORTIFY ACTION]: Applies a temporary shield to a line. If all lines are shielded, it overcharges one."""
        team_lines = self.game.query.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to shield'}

        # Find lines that are not already shielded
        unshielded_lines = [l for l in team_lines if l.get('id') not in self.state['shields']]

        # This helper function needs to be defined before the if/else block to be in scope for both.
        enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId]
        points_map = self.state['points']
        def get_line_proximity(line):
            if not enemy_points or line['p1_id'] not in points_map or line['p2_id'] not in points_map:
                return float('inf')
            p1, p2 = points_map[line['p1_id']], points_map[line['p2_id']]
            dist1 = min((distance_sq(p1, ep) for ep in enemy_points), default=float('inf'))
            dist2 = min((distance_sq(p2, ep) for ep in enemy_points), default=float('inf'))
            return min(dist1, dist2)

        if unshielded_lines:
            # --- Primary Effect: Shield a new line ---
            # Shield the line closest to any enemy point
            line_to_shield = min(unshielded_lines, key=get_line_proximity)
            shield_duration = 3 # in turns
            self.state['shields'][line_to_shield['id']] = shield_duration
            return {'success': True, 'type': 'shield_line', 'shielded_line': line_to_shield}
        else:
            # --- Fallback Effect: Overcharge an existing shield ---
            # Overcharge the shield closest to an enemy
            line_to_overcharge = min(team_lines, key=get_line_proximity)
            line_id = line_to_overcharge.get('id')
            if line_id and line_id in self.state['shields']:
                max_shield_duration = 6
                current_duration = self.state['shields'][line_id]
                if current_duration < max_shield_duration:
                    self.state['shields'][line_id] += 2 # Add 2 turns
                
                return {
                    'success': True, 
                    'type': 'shield_overcharge', 
                    'overcharged_line': line_to_overcharge,
                    'new_duration': self.state['shields'][line_id]
                }
            
            # This should be very rare (e.g., lines have no IDs)
            return {'success': False, 'reason': 'no valid shield to overcharge'}

    def claim_territory(self, teamId):
        """[FORTIFY ACTION]: Find a triangle and claim it. If not possible, reinforces an existing territory."""
        newly_claimable_triangles = self.game.query.find_claimable_triangles(teamId)

        if newly_claimable_triangles:
            # --- Primary Effect: Claim Territory ---
            # Claim the triangle with the largest area first
            points_map = self.state['points']
            triangle_to_claim = max(newly_claimable_triangles, key=lambda tri: polygon_area([points_map[pid] for pid in tri]))
            new_territory = {
                'teamId': teamId,
                'point_ids': list(triangle_to_claim)
            }
            self.state['territories'].append(new_territory)
            return {'success': True, 'type': 'claim_territory', 'territory': new_territory}
        else:
            # --- Fallback Effect: Reinforce an existing territory ---
            team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
            if not team_territories:
                return {'success': False, 'reason': 'no new triangles to claim and no existing territories to reinforce'}
            
            # Reinforce the largest existing territory
            points_map = self.state['points']
            territory_to_reinforce = max(team_territories, key=lambda t: polygon_area([points_map[pid] for pid in t['point_ids'] if pid in points_map]))
            strengthened_lines = self.game._reinforce_territory_boundaries(territory_to_reinforce)
            
            # The action is 'successful' even if no lines were strengthened (they might be maxed out)
            # The log message will reflect if lines were strengthened or not.
            return {
                'success': True, 'type': 'claim_fizzle_reinforce',
                'territory_point_ids': territory_to_reinforce['point_ids'], 'strengthened_lines': strengthened_lines
            }



    def form_bastion(self, teamId):
        """[FORTIFY ACTION]: Converts a fortified point and its connections into a defensive bastion. If not possible, reinforces a key point."""
        possible_bastions = self.game.query.find_possible_bastions(teamId)

        if not possible_bastions:
            # --- Fallback: Reinforce most connected fortified point ---
            fortified_point_ids = self.game.query.get_fortified_point_ids().intersection(self.game.query.get_team_point_ids(teamId))
            if not fortified_point_ids:
                return {'success': False, 'reason': 'no valid bastion formation and no fortified points to reinforce'}
            
            degrees = self.game.query.get_team_degrees(teamId)
            # Find the fortified point with the highest degree
            point_to_reinforce_id = max(fortified_point_ids, key=lambda pid: degrees.get(pid, 0), default=None)

            if not point_to_reinforce_id:
                return {'success': False, 'reason': 'could not find a fortified point to reinforce'}
            
            lines_to_strengthen = [l for l in self.game.query.get_team_lines(teamId) if l['p1_id'] == point_to_reinforce_id or l['p2_id'] == point_to_reinforce_id]
            
            strengthened_lines = []
            for line in lines_to_strengthen:
                if self.game._strengthen_line(line):
                    strengthened_lines.append(line)
            
            return {
                'success': True, 'type': 'bastion_fizzle_reinforce',
                'reinforced_point_id': point_to_reinforce_id, 'strengthened_lines': strengthened_lines
            }
        
        # --- Primary Action: Form Bastion ---
        # Choose the bastion candidate with the most prongs
        chosen_bastion = max(possible_bastions, key=lambda b: len(b['prong_ids']))
        bastion_id = self.game._generate_id('b')
        new_bastion = {
            'id': bastion_id,
            'teamId': teamId,
            **chosen_bastion
        }
        self.state['bastions'][bastion_id] = new_bastion

        # Collect line IDs for the visual effect
        all_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l['id'] for l in self.state['lines']}
        bastion_line_ids = []
        core_id = new_bastion['core_id']
        for prong_id in new_bastion['prong_ids']:
            line_key = tuple(sorted((core_id, prong_id)))
            if line_key in all_lines_by_points:
                bastion_line_ids.append(all_lines_by_points[line_key])

        return {'success': True, 'type': 'form_bastion', 'bastion': new_bastion, 'point_ids': [core_id] + new_bastion['prong_ids'], 'line_ids': bastion_line_ids}

    def form_monolith(self, teamId):
        """[FORTIFY ACTION]: Forms a Monolith from a tall, thin rectangle. If not possible, reinforces a regular rectangle."""
        possible_monoliths, fallback_candidates = self._find_possible_monoliths_and_fallbacks(teamId)
        
        if possible_monoliths:
            # --- Primary Action: Form Monolith ---
            # Choose the monolith candidate with the highest aspect ratio (tallest and thinnest)
            chosen_monolith_data = max(possible_monoliths, key=lambda m: m.get('aspect_ratio', 0))
            monolith_id = self.game._generate_id('m')
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
        elif fallback_candidates:
            # --- Fallback: Reinforce the largest-area regular rectangle ---
            points_map = self.state['points']
            candidate = max(fallback_candidates, key=lambda c: polygon_area([points_map[pid] for pid in c['point_ids']]))
            strengthened_lines = []
            existing_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.game.query.get_team_lines(teamId)}
            for pair in candidate['side_pairs']:
                line = existing_lines_by_points.get(tuple(sorted(pair)))
                if line and self.game._strengthen_line(line):
                    strengthened_lines.append(line)
            
            return {
                'success': True,
                'type': 'monolith_fizzle_reinforce',
                'reinforced_point_ids': candidate['point_ids'],
                'strengthened_lines': strengthened_lines
            }
        else:
            return {'success': False, 'reason': 'no valid monolith or rectangle formation found'}



    def reposition_point(self, teamId):
        """[FORTIFY ACTION]: Moves a single non-critical point to a new nearby location. This action has no cost."""
        point_to_move_id = self.game.query.find_repositionable_point(teamId)
        
        if not point_to_move_id or point_to_move_id not in self.state['points']:
            # The point that made this action possible is gone. Fizzle.
            return {'success': True, 'type': 'reposition_fizzle', 'reason': 'target point for reposition disappeared'}

        p_origin = self.state['points'][point_to_move_id]
        original_coords = {'x': p_origin['x'], 'y': p_origin['y'], 'id': p_origin['id'], 'teamId': p_origin['teamId']}


        # Try a few times to find a valid empty spot nearby
        # Try to move towards the team's centroid to consolidate
        team_centroid = self.game.query.get_team_centroid(teamId)

        for i in range(15):
            # Try a spiral search pattern around the origin point
            angle = (i / 15.0) * 2 * math.pi * 3 # 3 spirals
            radius = 1.0 + (i / 15.0) * 2.0 # Move between 1 and 3 units away
            
            new_x = p_origin['x'] + math.cos(angle) * radius
            new_y = p_origin['y'] + math.sin(angle) * radius
            
            grid_size = self.state['grid_size']
            new_p_coords = clamp_and_round_point_coords({'x': new_x, 'y': new_y}, grid_size)
            
            # Temporarily remove the point being moved to validate its new spot
            temp_points = self.state['points'].copy()
            del temp_points[point_to_move_id]

            is_valid, _ = self.game.is_spawn_location_valid(new_p_coords, teamId, points_override=temp_points)
            if not is_valid:
                continue

            # We found a valid move
            p_origin['x'] = new_p_coords['x']
            p_origin['y'] = new_p_coords['y']

            return {
                'success': True, 
                'type': 'reposition_point', 
                'moved_point': p_origin,
                'original_coords': original_coords
            }

        # If the loop finishes without finding a valid move, it's a "fizzle".
        return {'success': True, 'type': 'reposition_fizzle', 'reason': 'no valid new position found'}

    def rotate_point(self, teamId):
        """[FORTIFY ACTION]: Rotates a free point around a pivot. This action has no cost."""
        point_to_move_id = self.game.query.find_repositionable_point(teamId)
        
        if not point_to_move_id or point_to_move_id not in self.state['points']:
            # The point that made this action possible is gone. Fizzle.
            return {'success': True, 'type': 'rotate_fizzle', 'reason': 'target point for rotate disappeared'}

        p_origin = self.state['points'][point_to_move_id]
        original_coords = {'x': p_origin['x'], 'y': p_origin['y'], 'id': p_origin['id'], 'teamId': p_origin['teamId']}

        team_point_ids = self.game.query.get_team_point_ids(teamId)

        # Try a few times to find a valid rotation
        for _ in range(10):
            # Choose pivot: if point is far from grid center, rotate around it. Otherwise, rotate around another point.
            grid_size = self.state['grid_size']
            grid_center = {'x': (grid_size - 1) / 2, 'y': (grid_size - 1) / 2}
            if distance_sq(p_origin, grid_center) > (grid_size * 0.3)**2 or len(team_point_ids) <= 1:
                grid_size = self.state['grid_size']
                pivot = {'x': (grid_size - 1) / 2, 'y': (grid_size - 1) / 2}
                is_grid_center = True
            else:
                # Rotate around the nearest other friendly point
                other_point_ids = [pid for pid in team_point_ids if pid != point_to_move_id]
                pivot_id = min(other_point_ids, key=lambda pid: distance_sq(p_origin, self.state['points'][pid]))
                pivot = self.state['points'][pivot_id]
                is_grid_center = False

            # Try angles in a deterministic order
            for angle in [math.pi / 2, -math.pi / 2, math.pi / 4, -math.pi/4, math.pi]:
            
                new_p_coords_float = rotate_point(p_origin, pivot, angle)
                new_p_coords = clamp_and_round_point_coords(new_p_coords_float, self.state['grid_size'])

                # Temporarily remove the point to validate its new spot
                temp_points = self.state['points'].copy()
                del temp_points[point_to_move_id]
                is_valid, _ = self.game.is_spawn_location_valid(new_p_coords, teamId, points_override=temp_points)
                if not is_valid:
                    continue

                # We found a valid move
                p_origin['x'] = new_p_coords['x']
                p_origin['y'] = new_p_coords['y']

                return {
                    'success': True, 
                    'type': 'rotate_point', 
                    'moved_point': p_origin,
                    'original_coords': original_coords,
                    'pivot_point': pivot,
                    'is_grid_center': is_grid_center,
                }

        # If the loop finishes without finding a valid move, it's a "fizzle".
        return {'success': True, 'type': 'rotate_fizzle', 'reason': 'no valid rotation found'}

    def mirror_structure(self, teamId):
        """[FORTIFY ACTION]: Reflects points to create symmetry. If not possible, reinforces the structure."""
        valid_mirror_op = self._find_a_valid_mirror(teamId)
        
        if valid_mirror_op:
            # --- Primary Effect: Create Mirrored Points ---
            for p in valid_mirror_op['new_points_to_create']:
                self.state['points'][p['id']] = p
            
            return {
                'success': True, 'type': 'mirror_structure',
                'new_points': valid_mirror_op['new_points_to_create'],
                'axis_p1_id': valid_mirror_op['axis_p_ids'][0],
                'axis_p2_id': valid_mirror_op['axis_p_ids'][1],
            }
        
        # --- Fallback Effect: Strengthen Lines ---
        team_point_ids = self.game.query.get_team_point_ids(teamId)
        if not team_point_ids:
             return {'success': False, 'reason': 'no points to mirror or strengthen'}
        
        # Strengthen lines connected to a couple of random points
        # Strengthen lines connected to the two closest points
        if len(team_point_ids) < 2:
            return {'success': False, 'reason': 'not enough points for fallback'}
        points_map = self.state['points']
        p1_id, p2_id = min(combinations(team_point_ids, 2), key=lambda p: distance_sq(points_map[p[0]], points_map[p[1]]))
        points_to_strengthen_ids = [p1_id, p2_id]
        strengthened_lines = []
        all_team_lines = self.game.query.get_team_lines(teamId)
        
        for line in all_team_lines:
            if line['p1_id'] in points_to_strengthen_ids or line['p2_id'] in points_to_strengthen_ids:
                if self.game._strengthen_line(line):
                    strengthened_lines.append(line)
        
        if not strengthened_lines:
            # To be truly "never useless", we can try to add a new line as a final fallback.
            # Add a line between the two closest points that don't already have one
            if len(team_point_ids) >= 2:
                points_map = self.state['points']
                possible_pairs = list(combinations(team_point_ids, 2))
                possible_pairs.sort(key=lambda p: distance_sq(points_map[p[0]], points_map[p[1]]))
                
                existing_lines_keys = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in all_team_lines}
                
                chosen_pair = None
                for p1_id, p2_id in possible_pairs:
                    if tuple(sorted((p1_id, p2_id))) not in existing_lines_keys:
                        chosen_pair = (p1_id, p2_id)
                        break
                
                if not chosen_pair:
                    return {'success': False, 'reason': 'structure is fully connected'}
                
                p1_id, p2_id = chosen_pair
                existing_lines_keys = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in all_team_lines}
                if tuple(sorted((p1_id, p2_id))) not in existing_lines_keys:
                    line_id = self.game._generate_id('l')
                    new_line = {"id": line_id, "p1_id": p1_id, "p2_id": p2_id, "teamId": teamId}
                    self.state['lines'].append(new_line)
                    # For logging purposes, it's better to return a unique type
                    return {'success': True, 'type': 'mirror_structure_fizzle_add_line', 'new_line': new_line}
            
            return {'success': False, 'reason': 'mirroring failed and structure is already fully connected/strengthened'}

        return {
            'success': True, 'type': 'mirror_structure_fizzle_strengthen',
            'strengthened_lines': strengthened_lines
        }

    def create_anchor(self, teamId):
        """[FORTIFY ACTION]: Turns a non-critical point into a gravity well. This action does not cost a point."""
        # Find a point that can be turned into an anchor.
        # It must not be part of a critical structure and not already an anchor.
        # The articulation point check is removed as this is a non-destructive action.
        team_point_ids = self.game.query.get_team_point_ids(teamId)
        if not team_point_ids:
            return {'success': False, 'reason': 'no points to create anchor from'}
        
        critical_pids = self.game.query.get_critical_structure_point_ids(teamId)
        anchor_pids = set(self.state.get('anchors', {}).keys())
        
        candidate_pids = [
            pid for pid in team_point_ids 
            if pid not in critical_pids and pid not in anchor_pids
        ]

        if not candidate_pids:
            return {'success': False, 'reason': 'no non-critical points available to become an anchor'}

        # Choose the candidate closest to the most enemies
        enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId]
        if not enemy_points:
            p_to_anchor_id = candidate_pids[0] # Fallback if no enemies
        else:
            points_map = self.state['points']
            p_to_anchor_id = min(candidate_pids, key=lambda pid: min(distance_sq(points_map[pid], ep) for ep in enemy_points))
        
        if p_to_anchor_id not in self.state['points']:
            return {'success': False, 'reason': 'chosen anchor point does not exist'}

        # Create the anchor
        anchor_duration = 5 # turns
        self.state['anchors'][p_to_anchor_id] = {'teamId': teamId, 'turns_left': anchor_duration}

        anchor_point = self.state['points'][p_to_anchor_id]

        return {
            'success': True, 
            'type': 'create_anchor', 
            'anchor_point': anchor_point
        }

    def form_purifier(self, teamId):
        """[FORTIFY ACTION]: Forms a Purifier from a regular pentagon of points. If not possible, reinforces a potential formation."""
        possible_purifiers = self._find_possible_purifiers(teamId)
        
        if possible_purifiers:
            # --- Primary Effect: Form Purifier ---
            # Choose the purifier formation with the largest area
            points_map = self.state['points']
            chosen_purifier_data = max(possible_purifiers, key=lambda p_data: polygon_area([points_map[pid] for pid in p_data['point_ids']]))
            self.state.setdefault('purifiers', {}).setdefault(teamId, []).append(chosen_purifier_data)
            return {'success': True, 'type': 'form_purifier', 'purifier': chosen_purifier_data}
        else:
            # --- Fallback Effect: Reinforce a potential structure ---
            team_point_ids = self.game.query.get_team_point_ids(teamId)
            if len(team_point_ids) < 5:
                return {'success': False, 'reason': 'not enough points for purifier or its fallback'}

            # Choose the 5 points that are closest to each other (form a cluster)
            points_map = self.state['points']
            team_points = [points_map[pid] for pid in team_point_ids]
            
            # Find a seed point (closest to centroid) and its 4 nearest neighbors
            team_centroid = self.game.query.get_team_centroid(teamId)
            seed_point = min(team_points, key=lambda p: distance_sq(p, team_centroid))
            
            other_points = [p for p in team_points if p['id'] != seed_point['id']]
            other_points.sort(key=lambda p: distance_sq(p, seed_point))
            
            points_to_reinforce_ids = [seed_point['id']] + [p['id'] for p in other_points[:4]]
            strengthened_lines = []
            all_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.game.query.get_team_lines(teamId)}

            for p1_id, p2_id in combinations(points_to_reinforce_ids, 2):
                line_key = tuple(sorted((p1_id, p2_id)))
                if line_key in all_lines_by_points:
                    line_to_strengthen = all_lines_by_points[line_key]
                    if self.game._strengthen_line(line_to_strengthen):
                        strengthened_lines.append(line_to_strengthen)
            
            if not strengthened_lines:
                return {'success': False, 'reason': 'no valid pentagon formation found and no lines to reinforce'}
            
            return {
                'success': True,
                'type': 'purifier_fizzle_reinforce',
                'strengthened_lines': strengthened_lines,
                'reinforced_point_ids': points_to_reinforce_ids
            }

    def create_ley_line(self, teamId):
        """[FORTIFY ACTION]: Activates an I-Rune into a Ley Line, granting bonuses to nearby point creation. If all are active, it pulses one."""
        team_i_runes = self.state.get('runes', {}).get(teamId, {}).get('i_shape', [])
        if not team_i_runes:
            return {'success': False, 'reason': 'no I-Runes to convert'}
        
        available_runes = []
        for i_rune in team_i_runes:
            # Check if this exact set of points is already a ley line.
            is_active = False
            for ll in self.state.get('ley_lines', {}).values():
                if set(ll['point_ids']) == set(i_rune['point_ids']):
                    is_active = True
                    break
            if not is_active:
                available_runes.append(i_rune)

        if available_runes:
            # --- Primary Effect: Create a new Ley Line ---
            # Activate the longest I-Rune
            rune_to_activate = max(available_runes, key=lambda r: len(r['point_ids']))
            ley_line_id = self.game._generate_id('ll')
            
            new_ley_line = {
                'id': ley_line_id,
                'teamId': teamId,
                'point_ids': rune_to_activate['point_ids'],
                'turns_left': 8,
                'bonus_radius_sq': (self.state['grid_size'] * 0.15)**2
            }

            if 'ley_lines' not in self.state:
                self.state['ley_lines'] = {}
            self.state['ley_lines'][ley_line_id] = new_ley_line

            # Find the line IDs connecting the points of the rune for the visual effect
            all_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l['id'] for l in self.game.query.get_team_lines(teamId)}
            ley_line_line_ids = []
            rune_pids = rune_to_activate['point_ids']
            for i in range(len(rune_pids) - 1):
                p1_id, p2_id = rune_pids[i], rune_pids[i+1]
                line_key = tuple(sorted((p1_id, p2_id)))
                if line_key in all_lines_by_points:
                    ley_line_line_ids.append(all_lines_by_points[line_key])

            return {
                'success': True,
                'type': 'create_ley_line',
                'ley_line': new_ley_line,
                'ley_line_line_ids': ley_line_line_ids
            }
        else:
            # --- Fallback Effect: Pulse an existing Ley Line ---
            team_ley_lines = [ll for ll in self.state.get('ley_lines', {}).values() if ll['teamId'] == teamId]
            if not team_ley_lines:
                return {'success': False, 'reason': 'no I-Runes to convert and no Ley Lines to pulse'}

            # Pulse the longest existing Ley Line
            ley_line_to_pulse = max(team_ley_lines, key=lambda ll: len(ll['point_ids']))
            
            # Strengthen all lines connected to any point on the ley line
            strengthened_lines = []
            all_team_lines = self.game.query.get_team_lines(teamId)
            ley_line_pids = set(ley_line_to_pulse['point_ids'])

            for line in all_team_lines:
                # Don't strengthen the ley line's own segments
                if line['p1_id'] in ley_line_pids and line['p2_id'] in ley_line_pids:
                    continue
                
                if line['p1_id'] in ley_line_pids or line['p2_id'] in ley_line_pids:
                    if self.game._strengthen_line(line):
                        strengthened_lines.append(line)
            
            return {
                'success': True,
                'type': 'ley_line_pulse',
                'pulsed_ley_line_id': ley_line_to_pulse['id'],
                'strengthened_lines': strengthened_lines
            }

