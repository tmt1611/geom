import random
import math
from itertools import combinations
from ..geometry import distance_sq, reflect_point, rotate_point, is_rectangle, is_regular_pentagon, points_centroid, clamp_and_round_point_coords, get_edges_by_distance

class FortifyActionsHandler:
    def __init__(self, game):
        self.game = game

    # --- Action Precondition Checks ---

    def can_perform_shield_line(self, teamId):
        return len(self.game.get_team_lines(teamId)) > 0, "Requires at least one line to shield or overcharge."

    def can_perform_claim_territory(self, teamId):
        # A rough check to avoid expensive triangle enumeration for the precondition.
        # The action itself will do the precise check.
        can_potentially_claim = len(self.game.get_team_point_ids(teamId)) >= 3 and len(self.game.get_team_lines(teamId)) >= 3
        can_reinforce = any(t['teamId'] == teamId for t in self.state.get('territories', []))
        can_perform = can_potentially_claim or can_reinforce
        reason = "" if can_perform else "Requires at least 3 points and 3 lines to claim, or an existing territory to reinforce."
        return can_perform, reason

    def can_perform_create_anchor(self, teamId):
        # Action is possible if there is at least one "free" point that is not already an anchor.
        team_point_ids = self.game.get_team_point_ids(teamId)
        if not team_point_ids:
            return False, "Requires at least one point."

        critical_pids = self.game._get_critical_structure_point_ids(teamId)
        articulation_pids = set(self.game._find_articulation_points(teamId))
        anchor_pids = set(self.state.get('anchors', {}).keys())

        has_candidate = any(
            pid not in critical_pids and pid not in articulation_pids and pid not in anchor_pids
            for pid in team_point_ids
        )
        return has_candidate, "No available non-critical points to turn into an anchor."

    def _find_a_valid_mirror(self, teamId, num_attempts=5):
        """
        Tries to find a valid mirror operation by randomly selecting axes and points.
        Returns a dictionary with operation details if successful, otherwise None.
        """
        team_point_ids = self.game.get_team_point_ids(teamId)
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

    def can_perform_mirror_structure(self, teamId):
        # Primary needs at least 3 points. Fallback needs at least one line, or at least 2 points to create a line.
        # This is a cheap check; the action itself performs the more expensive geometric validation.
        team_point_ids = self.game.get_team_point_ids(teamId)
        has_points_for_primary = len(team_point_ids) >= 3
        has_lines_for_fallback_strengthen = len(self.game.get_team_lines(teamId)) > 0
        has_points_for_fallback_add_line = len(team_point_ids) >= 2
        can_perform = has_points_for_primary or has_lines_for_fallback_strengthen or has_points_for_fallback_add_line
        reason = "" if can_perform else "Requires at least 2 points."
        return can_perform, reason

    def can_perform_form_bastion(self, teamId):
        can_form = len(self._find_possible_bastions(teamId)) > 0
        can_reinforce = bool(self.game._get_fortified_point_ids().intersection(self.game.get_team_point_ids(teamId)))
        can_perform = can_form or can_reinforce
        reason = "" if can_perform else "No valid bastion formation and no fortified points to reinforce."
        return can_perform, reason

    def _find_possible_monoliths_and_fallbacks(self, teamId):
        """Helper to find valid monoliths (tall rectangles) and regular rectangles for fallback reinforcement."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 4:
            return [], []

        points = self.state['points']
        existing_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.game.get_team_lines(teamId)}
        existing_monolith_points = {pid for m in self.state.get('monoliths', {}).values() for pid in m['point_ids']}

        possible_monoliths = []
        fallback_candidates = []
        
        for p_ids_tuple in combinations(team_point_ids, 4):
            if any(pid in existing_monolith_points for pid in p_ids_tuple):
                continue
            
            if not all(pid in points for pid in p_ids_tuple):
                continue
            
            p_list = [points[pid] for pid in p_ids_tuple]
            is_rect, aspect_ratio = is_rectangle(*p_list)

            if is_rect:
                edge_data = get_edges_by_distance(p_list)
                side_pairs = edge_data['sides']

                if all(tuple(sorted(pair)) in existing_lines_by_points for pair in side_pairs):
                    if aspect_ratio > 3.0:
                        center_x = sum(p['x'] for p in p_list) / 4
                        center_y = sum(p['y'] for p in p_list) / 4
                        possible_monoliths.append({
                            'point_ids': list(p_ids_tuple),
                            'center_coords': {'x': center_x, 'y': center_y}
                        })
                    else:
                        fallback_candidates.append({'point_ids': list(p_ids_tuple), 'side_pairs': side_pairs})
        return possible_monoliths, fallback_candidates

    def can_perform_form_monolith(self, teamId):
        possible_monoliths, fallback_candidates = self._find_possible_monoliths_and_fallbacks(teamId)
        can_perform = len(possible_monoliths) > 0 or len(fallback_candidates) > 0
        return can_perform, "No valid rectangle formation found."

    def _find_possible_purifiers(self, teamId):
        """Helper to find valid pentagonal formations for a Purifier."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 5:
            return []

        points = self.state['points']
        existing_lines = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in self.game.get_team_lines(teamId)}
        
        # Get points already used in other major structures
        existing_purifier_points = {pid for p_list in self.state.get('purifiers', {}).values() for p in p_list for pid in p['point_ids']}

        possible_purifiers = []
        for p_ids_tuple in combinations(team_point_ids, 5):
            if any(pid in existing_purifier_points for pid in p_ids_tuple):
                continue

            # Defensive check to ensure all points exist before creating the list.
            if not all(pid in points for pid in p_ids_tuple):
                continue

            p_list = [points[pid] for pid in p_ids_tuple]
            if is_regular_pentagon(*p_list):
                # To be a valid formation, the 5 outer "side" lines must exist.
                edge_data = get_edges_by_distance(p_list)
                side_pairs = edge_data['sides']

                if all(tuple(sorted(pair)) in existing_lines for pair in side_pairs):
                    possible_purifiers.append({'point_ids': list(p_ids_tuple)})
        return possible_purifiers

    def can_perform_form_purifier(self, teamId):
        can_perform = len(self._find_possible_purifiers(teamId)) > 0
        return can_perform, "No valid pentagon formation found."

    def can_perform_create_fissure(self, teamId):
        team_spires = self.state.get('rift_spires', {}).values()
        can_perform = any(s['teamId'] == teamId and s.get('charge', 0) >= s.get('charge_needed', 3) for s in team_spires)
        return can_perform, "Requires a charged Rift Spire."

    def can_perform_reposition_point(self, teamId):
        can_reposition = bool(self.game._find_repositionable_point(teamId))
        reason = "" if can_reposition else "No free points to reposition."
        return can_reposition, reason

    def can_perform_rotate_point(self, teamId):
        can_rotate = bool(self.game._find_repositionable_point(teamId))
        reason = "" if can_rotate else "No free points to rotate."
        return can_rotate, reason
    
    def can_perform_create_ley_line(self, teamId):
        # The action is possible as long as an I-Rune exists.
        # The action logic handles whether to create a new Ley Line or pulse an existing one.
        has_i_rune = bool(self.state.get('runes', {}).get(teamId, {}).get('i_shape', []))
        return has_i_rune, "Requires an I-Rune (a line of 3+ points)."

    def _find_rift_spire_candidates(self, teamId):
        """Helper to find points that are vertices of 3+ territories."""
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        if len(team_territories) < 3:
            return []

        vertex_counts = {}
        for territory in team_territories:
            for pid in territory.get('point_ids', []):
                vertex_counts[pid] = vertex_counts.get(pid, 0) + 1
        
        existing_spire_pids = {spire['point_id'] for spire in self.state.get('rift_spires', {}).values()}
        
        candidates = [pid for pid, count in vertex_counts.items() if count >= 3 and pid not in existing_spire_pids]
        return candidates

    def can_perform_form_rift_spire(self, teamId):
        can_perform = len(self._find_rift_spire_candidates(teamId)) > 0
        return can_perform, "Requires a point that is a vertex of at least 3 territories."


    # --- End Precondition Checks ---

    @property
    def state(self):
        """Provides direct access to the game's current state dictionary."""
        return self.game.state

    def shield_line(self, teamId):
        """[FORTIFY ACTION]: Applies a temporary shield to a line. If all lines are shielded, it overcharges one."""
        team_lines = self.game.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to shield'}

        # Find lines that are not already shielded
        unshielded_lines = [l for l in team_lines if l.get('id') not in self.state['shields']]

        if unshielded_lines:
            # --- Primary Effect: Shield a new line ---
            line_to_shield = random.choice(unshielded_lines)
            shield_duration = 3 # in turns
            self.state['shields'][line_to_shield['id']] = shield_duration
            return {'success': True, 'type': 'shield_line', 'shielded_line': line_to_shield}
        else:
            # --- Fallback Effect: Overcharge an existing shield ---
            line_to_overcharge = random.choice(team_lines)
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

    def _find_claimable_triangles(self, teamId):
        """Finds all triangles for a team that have not yet been claimed."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        team_lines = self.game.get_team_lines(teamId)
        
        all_triangles = self.game.formation_manager._find_all_triangles(team_point_ids, team_lines)
        if not all_triangles:
            return []
            
        claimed_triangles = {tuple(sorted(t['point_ids'])) for t in self.state['territories']}
        return list(all_triangles - claimed_triangles)

    def claim_territory(self, teamId):
        """[FORTIFY ACTION]: Find a triangle and claim it. If not possible, reinforces an existing territory."""
        newly_claimable_triangles = self._find_claimable_triangles(teamId)

        if newly_claimable_triangles:
            # --- Primary Effect: Claim Territory ---
            triangle_to_claim = random.choice(newly_claimable_triangles)
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
            
            territory_to_reinforce = random.choice(team_territories)
            strengthened_lines = self.game._reinforce_territory_boundaries(territory_to_reinforce)
            
            # The action is 'successful' even if no lines were strengthened (they might be maxed out)
            # The log message will reflect if lines were strengthened or not.
            return {
                'success': True, 'type': 'claim_fizzle_reinforce',
                'territory_point_ids': territory_to_reinforce['point_ids'], 'strengthened_lines': strengthened_lines
            }

    def _find_possible_bastions(self, teamId):
        """Finds all valid formations for creating a new bastion."""
        fortified_point_ids = self.game._get_fortified_point_ids()
        if not fortified_point_ids:
            return []

        team_point_ids = self.game.get_team_point_ids(teamId)
        adj = {pid: set() for pid in team_point_ids}
        for line in self.game.get_team_lines(teamId):
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])
        
        existing_bastion_points = self.game._get_bastion_point_ids()
        used_points = existing_bastion_points['cores'].union(existing_bastion_points['prongs'])

        possible_bastions = []
        for core_candidate_id in fortified_point_ids:
            if core_candidate_id not in team_point_ids or core_candidate_id in used_points:
                continue
            
            prong_candidates = [
                pid for pid in adj.get(core_candidate_id, set())
                if pid not in fortified_point_ids and pid not in used_points
            ]

            if len(prong_candidates) >= 3:
                possible_bastions.append({
                    'core_id': core_candidate_id,
                    'prong_ids': prong_candidates
                })
        return possible_bastions

    def form_bastion(self, teamId):
        """[FORTIFY ACTION]: Converts a fortified point and its connections into a defensive bastion. If not possible, reinforces a key point."""
        possible_bastions = self._find_possible_bastions(teamId)

        if not possible_bastions:
            # --- Fallback: Reinforce most connected fortified point ---
            fortified_point_ids = self.game._get_fortified_point_ids().intersection(self.game.get_team_point_ids(teamId))
            if not fortified_point_ids:
                return {'success': False, 'reason': 'no valid bastion formation and no fortified points to reinforce'}
            
            adj = {pid: 0 for pid in self.game.get_team_point_ids(teamId)}
            for line in self.game.get_team_lines(teamId):
                if line['p1_id'] in adj: adj[line['p1_id']] += 1
                if line['p2_id'] in adj: adj[line['p2_id']] += 1

            # Find the fortified point with the highest degree
            point_to_reinforce_id = max(fortified_point_ids, key=lambda pid: adj.get(pid, 0), default=None)

            if not point_to_reinforce_id:
                return {'success': False, 'reason': 'could not find a fortified point to reinforce'}
            
            lines_to_strengthen = [l for l in self.game.get_team_lines(teamId) if l['p1_id'] == point_to_reinforce_id or l['p2_id'] == point_to_reinforce_id]
            
            strengthened_lines = []
            for line in lines_to_strengthen:
                if self.game._strengthen_line(line):
                    strengthened_lines.append(line)
            
            return {
                'success': True, 'type': 'bastion_fizzle_reinforce',
                'reinforced_point_id': point_to_reinforce_id, 'strengthened_lines': strengthened_lines
            }
        
        # --- Primary Action: Form Bastion ---
        chosen_bastion = random.choice(possible_bastions)
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
            chosen_monolith_data = random.choice(possible_monoliths)
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
            # --- Fallback: Reinforce a regular rectangle ---
            candidate = random.choice(fallback_candidates)
            strengthened_lines = []
            existing_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.game.get_team_lines(teamId)}
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

    def create_fissure(self, teamId):
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

        fissure_id = self.game._generate_id('f')
        new_fissure = { 'id': fissure_id, 'p1': p1, 'p2': p2, 'turns_left': 8 }
        self.state['fissures'].append(new_fissure)
        
        spire['charge'] = 0 # Reset charge

        return {
            'success': True,
            'type': 'create_fissure',
            'fissure': new_fissure,
            'spire_id': spire['id']
        }

    def reposition_point(self, teamId):
        """[FORTIFY ACTION]: Moves a single non-critical point to a new nearby location. This action has no cost."""
        point_to_move_id = self.game._find_repositionable_point(teamId)
        
        if not point_to_move_id or point_to_move_id not in self.state['points']:
            # The point that made this action possible is gone. Fizzle.
            return {'success': True, 'type': 'reposition_fizzle', 'reason': 'target point for reposition disappeared'}

        p_origin = self.state['points'][point_to_move_id]
        original_coords = {'x': p_origin['x'], 'y': p_origin['y'], 'id': p_origin['id'], 'teamId': p_origin['teamId']}


        # Try a few times to find a valid empty spot nearby
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            # Move between 1 and 3 units away
            radius = random.uniform(1.0, 3.0)
            
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
        point_to_move_id = self.game._find_repositionable_point(teamId)
        
        if not point_to_move_id or point_to_move_id not in self.state['points']:
            # The point that made this action possible is gone. Fizzle.
            return {'success': True, 'type': 'rotate_fizzle', 'reason': 'target point for rotate disappeared'}

        p_origin = self.state['points'][point_to_move_id]
        original_coords = {'x': p_origin['x'], 'y': p_origin['y'], 'id': p_origin['id'], 'teamId': p_origin['teamId']}

        team_point_ids = self.game.get_team_point_ids(teamId)

        # Try a few times to find a valid rotation
        for _ in range(10):
            # Choose pivot: 50% grid center, 50% another friendly point
            if random.random() < 0.5 or len(team_point_ids) <= 1:
                grid_size = self.state['grid_size']
                pivot = {'x': (grid_size - 1) / 2, 'y': (grid_size - 1) / 2}
                is_grid_center = True
            else:
                other_point_ids = [pid for pid in team_point_ids if pid != point_to_move_id]
                pivot_id = random.choice(other_point_ids)
                pivot = self.state['points'][pivot_id]
                is_grid_center = False

            # Choose angle
            angle = random.choice([math.pi / 4, math.pi / 2, math.pi, -math.pi / 2, -math.pi/4]) # 45, 90, 180 deg
            
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
        team_point_ids = self.game.get_team_point_ids(teamId)
        if not team_point_ids:
             return {'success': False, 'reason': 'no points to mirror or strengthen'}
        
        # Strengthen lines connected to a couple of random points
        points_to_strengthen_ids = random.sample(team_point_ids, min(len(team_point_ids), 2))
        strengthened_lines = []
        all_team_lines = self.game.get_team_lines(teamId)
        
        for line in all_team_lines:
            if line['p1_id'] in points_to_strengthen_ids or line['p2_id'] in points_to_strengthen_ids:
                if self.game._strengthen_line(line):
                    strengthened_lines.append(line)
        
        if not strengthened_lines:
            # To be truly "never useless", we can try to add a new line as a final fallback.
            if len(team_point_ids) >= 2:
                p1_id, p2_id = random.sample(team_point_ids, 2)
                existing_lines_keys = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in all_team_lines}
                if tuple(sorted((p1_id, p2_id))) not in existing_lines_keys:
                    line_id = self.game._generate_id('l')
                    new_line = {"id": line_id, "p1_id": p1_id, "p2_id": p2_id, "teamId": teamId}
                    self.state['lines'].append(new_line)
                    # For logging purposes, it's better to return a unique type
                    return {'success': True, 'type': 'mirror_fizzle_add_line', 'new_line': new_line}
            
            return {'success': False, 'reason': 'mirroring failed and structure is already fully connected/strengthened'}

        return {
            'success': True, 'type': 'mirror_fizzle_strengthen',
            'strengthened_lines': strengthened_lines
        }

    def create_anchor(self, teamId):
        """[FORTIFY ACTION]: Turns a non-critical point into a gravity well. This action does not cost a point."""
        # Find a point that can be turned into an anchor.
        # It must not be part of a critical structure or an articulation point, and not already an anchor.
        team_point_ids = self.game.get_team_point_ids(teamId)
        if not team_point_ids:
            return {'success': False, 'reason': 'no points to create anchor from'}
        
        critical_pids = self.game._get_critical_structure_point_ids(teamId)
        articulation_pids = set(self.game._find_articulation_points(teamId))
        anchor_pids = set(self.state.get('anchors', {}).keys())
        
        candidate_pids = [
            pid for pid in team_point_ids 
            if pid not in critical_pids and pid not in articulation_pids and pid not in anchor_pids
        ]

        if not candidate_pids:
            return {'success': False, 'reason': 'no non-critical points available to become an anchor'}

        p_to_anchor_id = random.choice(candidate_pids)
        
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
        """[FORTIFY ACTION]: Forms a Purifier from a regular pentagon of points."""
        possible_purifiers = self._find_possible_purifiers(teamId)
        
        if not possible_purifiers:
            return {'success': False, 'reason': 'no valid pentagon formation found'}

        chosen_purifier_data = random.choice(possible_purifiers)
        
        self.state.setdefault('purifiers', {}).setdefault(teamId, []).append(chosen_purifier_data)
        
        return {'success': True, 'type': 'form_purifier', 'purifier': chosen_purifier_data}

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
            rune_to_activate = random.choice(available_runes)
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

            return {
                'success': True,
                'type': 'create_ley_line',
                'ley_line': new_ley_line
            }
        else:
            # --- Fallback Effect: Pulse an existing Ley Line ---
            team_ley_lines = [ll for ll in self.state.get('ley_lines', {}).values() if ll['teamId'] == teamId]
            if not team_ley_lines:
                return {'success': False, 'reason': 'no I-Runes to convert and no Ley Lines to pulse'}

            ley_line_to_pulse = random.choice(team_ley_lines)
            
            # Strengthen all lines connected to any point on the ley line
            strengthened_lines = []
            all_team_lines = self.game.get_team_lines(teamId)
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

    def form_rift_spire(self, teamId):
        """[FORTIFY ACTION]: Erects a Rift Spire at a territorial nexus without sacrifice."""
        candidate_pids = self._find_rift_spire_candidates(teamId)
        if not candidate_pids:
            return {'success': False, 'reason': 'no valid location for a Rift Spire found'}

        nexus_point_id = random.choice(candidate_pids)
        nexus_point = self.state['points'].get(nexus_point_id)
        if not nexus_point:
            return {'success': False, 'reason': 'nexus point for spire disappeared'}

        spire_id = self.game._generate_id('rs')
        new_spire = {
            'id': spire_id,
            'teamId': teamId,
            'point_id': nexus_point_id,
            'coords': {'x': nexus_point['x'], 'y': nexus_point['y']},
            'charge': 0,
            'charge_needed': 3
        }
        
        self.state.setdefault('rift_spires', {})[spire_id] = new_spire

        return {
            'success': True,
            'type': 'form_rift_spire',
            'spire': new_spire
        }