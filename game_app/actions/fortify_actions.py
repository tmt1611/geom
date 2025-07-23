import random
import math
import uuid
from itertools import combinations
from ..geometry import distance_sq, reflect_point, is_rectangle, is_regular_pentagon, points_centroid, clamp_and_round_point_coords, get_edges_by_distance

class FortifyActionsHandler:
    def __init__(self, game):
        self.game = game

    # --- Action Precondition Checks ---

    def can_perform_shield_line(self, teamId):
        return len(self.game.get_team_lines(teamId)) > 0, "Requires at least one line to shield or overcharge."

    def can_perform_claim_territory(self, teamId):
        can_perform = len(self._find_claimable_triangles(teamId)) > 0
        return can_perform, "No new triangles available to claim."

    def can_perform_create_anchor(self, teamId):
        return len(self.game.get_team_point_ids(teamId)) >= 3, "Requires at least 3 points to sacrifice one."

    def can_perform_mirror_structure(self, teamId):
        return len(self.game.get_team_point_ids(teamId)) >= 3, "Requires at least 3 points to mirror."

    def can_perform_form_bastion(self, teamId):
        can_perform = len(self._find_possible_bastions(teamId)) > 0
        return can_perform, "No valid bastion formation found."

    def can_perform_form_monolith(self, teamId):
        return len(self.game.get_team_point_ids(teamId)) >= 4, "Requires at least 4 points."

    def can_perform_form_purifier(self, teamId):
        return len(self.game.get_team_point_ids(teamId)) >= 5, "Requires at least 5 points."

    def can_perform_cultivate_heartwood(self, teamId):
        can_perform = len(self.game.get_team_point_ids(teamId)) >= 6 and teamId not in self.state.get('heartwoods', {})
        return can_perform, "Requires >= 6 points and no existing Heartwood."

    def can_perform_form_rift_spire(self, teamId):
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        return len(team_territories) >= 3, "Requires at least 3 territories."

    def can_perform_create_fissure(self, teamId):
        team_spires = self.state.get('rift_spires', {}).values()
        can_perform = any(s['teamId'] == teamId and s.get('charge', 0) >= s.get('charge_needed', 3) for s in team_spires)
        return can_perform, "Requires a charged Rift Spire."

    def can_perform_raise_barricade(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('barricade', []))
        return can_perform, "Requires an active Barricade Rune."

    def can_perform_reposition_point(self, teamId):
        can_perform = bool(self.game._find_non_critical_sacrificial_point(teamId))
        return can_perform, "No free points available to reposition."
    
    def can_perform_build_chronos_spire(self, teamId):
        has_wonder = any(w['teamId'] == teamId for w in self.state.get('wonders', {}).values())
        if has_wonder:
            return False, "Team already has a wonder."
        
        has_star_rune = len(self.game.formation_manager.check_star_rune(
            self.game.get_team_point_ids(teamId),
            self.game.get_team_lines(teamId),
            self.state['points']
        )) > 0
        return has_star_rune, "Requires a Star Rune and no existing Wonder."

    def can_perform_attune_nexus(self, teamId):
        can_perform = len(self._find_attunable_nexuses(teamId)) > 0
        return can_perform, "Requires a Nexus with a diagonal to sacrifice."

    def can_perform_create_ley_line(self, teamId):
        # An I-Rune is a line of 3 or more points.
        team_i_runes = self.state.get('runes', {}).get(teamId, {}).get('i_shape', [])
        if not team_i_runes:
            return False, "Requires an I-Rune (a line of 3+ points)."
        
        # Check if there's at least one I-Rune that isn't already an active Ley Line.
        for i_rune in team_i_runes:
            is_active = False
            for ll in self.state.get('ley_lines', {}).values():
                if set(ll['point_ids']) == set(i_rune['point_ids']):
                    is_active = True
                    break
            if not is_active:
                return True, ""
                
        return False, "All available I-Runes are already active Ley Lines."

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
            p_ids = territory_to_reinforce['point_ids']
            boundary_lines_keys = [tuple(sorted((p_ids[0], p_ids[1]))), tuple(sorted((p_ids[1], p_ids[2]))), tuple(sorted((p_ids[2], p_ids[0])))]
            
            strengthened_lines = []
            all_team_lines = self.game.get_team_lines(teamId)
            
            for line in all_team_lines:
                if tuple(sorted((line['p1_id'], line['p2_id']))) in boundary_lines_keys:
                    if self.game._strengthen_line(line):
                        strengthened_lines.append(line)
            
            # The action is 'successful' even if no lines were strengthened (they might be maxed out)
            # The log message will reflect if lines were strengthened or not.
            return {
                'success': True, 'type': 'claim_fizzle_reinforce',
                'territory_point_ids': p_ids, 'strengthened_lines': strengthened_lines
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
            max_strength = 3
            for line in lines_to_strengthen:
                line_id = line.get('id')
                if line_id:
                    current_strength = self.state['line_strengths'].get(line_id, 0)
                    if current_strength < max_strength:
                        self.state['line_strengths'][line_id] = current_strength + 1
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
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 4:
            return {'success': False, 'reason': 'not enough points'}

        points = self.state['points']
        existing_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.game.get_team_lines(teamId)}
        existing_monolith_points = {pid for m in self.state.get('monoliths', {}).values() for pid in m['point_ids']}

        possible_monoliths = []
        fallback_candidates = []
        
        for p_ids_tuple in combinations(team_point_ids, 4):
            if any(pid in existing_monolith_points for pid in p_ids_tuple):
                continue
            
            p_list = [points[pid] for pid in p_ids_tuple]
            is_rect, aspect_ratio = is_rectangle(*p_list)

            if is_rect:
                # Check for the 4 outer perimeter lines
                edge_data = get_edges_by_distance(p_list)
                side_pairs = edge_data['sides']

                if all(tuple(sorted(pair)) in existing_lines_by_points for pair in side_pairs):
                    # Monolith requires a thin rectangle, aspect ratio > 3.0
                    if aspect_ratio > 3.0:
                        center_x = sum(p['x'] for p in p_list) / 4
                        center_y = sum(p['y'] for p in p_list) / 4
                        possible_monoliths.append({
                            'point_ids': list(p_ids_tuple),
                            'center_coords': {'x': center_x, 'y': center_y}
                        })
                    else:
                        fallback_candidates.append({'point_ids': list(p_ids_tuple), 'side_pairs': side_pairs})
        
        if not possible_monoliths:
            # --- Fallback: Reinforce a regular rectangle ---
            if not fallback_candidates:
                return {'success': False, 'reason': 'no valid monolith or rectangle formation found'}
            
            candidate = random.choice(fallback_candidates)
            strengthened_lines = []
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

    def cultivate_heartwood(self, teamId):
        """[FORTIFY ACTION]: Cultivates a Heartwood from a point with many connections."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        # A heartwood for a team is unique.
        if teamId in self.state.get('heartwoods', {}):
            return {'success': False, 'reason': 'team already has a heartwood'}
        
        HEARTWOOD_MIN_BRANCHES = 5
        
        adj = {pid: set() for pid in team_point_ids}
        for line in self.game.get_team_lines(teamId):
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
            sac_data = self.game._delete_point_and_connections(pid, aggressor_team_id=teamId)
            if sac_data:
                sacrificed_points_data.append(sac_data)

        if not sacrificed_points_data:
            return {'success': False, 'reason': 'failed to sacrifice points for heartwood'}

        # --- Create the Heartwood ---
        heartwood_id = self.game._generate_id('hw')
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

    def form_rift_spire(self, teamId):
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
        sacrificed_point_data = self.game._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
        
        if not sacrificed_point_data:
            return {'success': False, 'reason': 'failed to sacrifice point for spire'}

        spire_id = self.game._generate_id('rs')
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

    def raise_barricade(self, teamId):
        """[TERRAFORM ACTION]: Consumes a Barricade Rune to create a barricade."""
        active_barricade_runes = self.state.get('runes', {}).get(teamId, {}).get('barricade', [])
        if not active_barricade_runes:
            return {'success': False, 'reason': 'no active Barricade Runes'}

        rune_p_ids_tuple = random.choice(active_barricade_runes)
        points = self.state['points']
        
        if not all(pid in points for pid in rune_p_ids_tuple):
            return {'success': False, 'reason': 'rune points no longer exist'}
        
        p_list = [points[pid] for pid in rune_p_ids_tuple]
        
        # Sacrifice the rune points
        sacrificed_points_data = []
        for pid in rune_p_ids_tuple:
            sac_data = self.game._delete_point_and_connections(pid, aggressor_team_id=teamId)
            if sac_data:
                sacrificed_points_data.append(sac_data)

        # Determine barricade from midpoints of an opposite pair of sides of the rectangle
        # Use the original coordinates from p_list for this.
        edge_data = get_edges_by_distance(p_list)
        side_pair_ids = edge_data['sides']

        # Pick one side
        side1_ids = set(side_pair_ids[0])
        # Find its opposite
        side2_ids = None
        for i in range(1, 4):
            candidate_side_ids = set(side_pair_ids[i])
            if not side1_ids.intersection(candidate_side_ids):
                side2_ids = candidate_side_ids
                break
        
        if not side2_ids:
            # Fallback for weird geometry, this should be rare for a valid rect.
            side1_ids = set(side_pair_ids[2])
            side2_ids = set()
            for i in [0,1,3]:
                candidate_side_ids = set(side_pair_ids[i])
                if not side1_ids.intersection(candidate_side_ids):
                    side2_ids = candidate_side_ids
                    break
        
        id_to_point = {p['id']: p for p in p_list}
        side1_pts = [id_to_point[pid] for pid in list(side1_ids)]
        side2_pts = [id_to_point[pid] for pid in list(side2_ids)]
        
        mid1 = points_centroid(side1_pts)
        mid2 = points_centroid(side2_pts)

        barricade_id = self.game._generate_id('bar')
        new_barricade = {
            'id': barricade_id,
            'teamId': teamId,
            'p1': mid1,
            'p2': mid2,
            'turns_left': 5
        }

        if 'barricades' not in self.state: self.state['barricades'] = []
        self.state['barricades'].append(new_barricade)

        return {
            'success': True,
            'type': 'raise_barricade',
            'barricade': new_barricade,
            'rune_points': list(rune_p_ids_tuple),
            'sacrificed_points_count': len(sacrificed_points_data)
        }

    def reposition_point(self, teamId):
        """[FORTIFY ACTION]: Moves a single non-critical point to a new nearby location. If not possible, strengthens a line."""
        # We can reuse the logic for finding a "non-critical" point, as it effectively finds a "free" point.
        point_to_move_id = self.game._find_non_critical_sacrificial_point(teamId)
        
        if not point_to_move_id or point_to_move_id not in self.state['points']:
            return self.game._fallback_strengthen_random_line(teamId, 'reposition')

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

        # Fallback: Strengthen a random line
        return self.game._fallback_strengthen_random_line(teamId, 'reposition')

    def build_chronos_spire(self, teamId):
        """[WONDER ACTION]: Build the Chronos Spire."""
        # Check if this team already has a wonder. Limit one per team for now.
        if any(w['teamId'] == teamId for w in self.state.get('wonders', {}).values()):
            return {'success': False, 'reason': 'team already has a wonder'}

        star_formations = self.game.formation_manager.check_star_rune(self.game.get_team_point_ids(teamId), self.game.get_team_lines(teamId), self.state['points'])
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
            sac_data = self.game._delete_point_and_connections(pid, aggressor_team_id=teamId)
            if sac_data:
                sacrificed_points_data.append(sac_data)
        
        if len(sacrificed_points_data) != len(points_to_sacrifice):
            return {'success': False, 'reason': 'failed to sacrifice all formation points'}
            
        # Create the Wonder
        wonder_id = self.game._generate_id('w')
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

    def _find_attunable_nexuses(self, teamId):
        """Finds nexuses that can be attuned."""
        self.game._update_nexuses_for_team(teamId)
        team_nexuses = self.state.get('nexuses', {}).get(teamId, [])
        if not team_nexuses:
            return []
        
        attuned_nexus_pids = {pid for an in self.state.get('attuned_nexuses', {}).values() for pid in an['point_ids']}
        
        attunable = []
        for nexus in team_nexuses:
            if any(pid in attuned_nexus_pids for pid in nexus['point_ids']):
                continue
            
            # A Nexus is defined by having a diagonal, so we just need to find one that isn't already part of an attuned structure.
            attunable.append(nexus)
            
        return attunable

    def attune_nexus(self, teamId):
        """[FORTIFY ACTION]: Empowers a Nexus by sacrificing a diagonal, energizing nearby friendly lines for powerful attacks."""
        attunable_nexuses = self._find_attunable_nexuses(teamId)
        if not attunable_nexuses:
            return {'success': False, 'reason': 'no valid nexus to attune'}
            
        nexus_to_attune = random.choice(attunable_nexuses)
        p_ids = nexus_to_attune['point_ids']
        points = self.state['points']

        # Find and sacrifice a diagonal line
        p_list = [points[pid] for pid in p_ids]
        edge_data = get_edges_by_distance(p_list)
        diag_pairs = edge_data['diagonals']

        existing_lines = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.game.get_team_lines(teamId)}
        
        line_to_sac = None
        for p1_id, p2_id in diag_pairs:
            line_key = tuple(sorted((p1_id, p2_id)))
            if line_key in existing_lines:
                line_to_sac = existing_lines[line_key]
                break
        
        if not line_to_sac:
            return {'success': False, 'reason': 'nexus found but its diagonal line is missing'}

        # --- Primary Effect: Attune the Nexus ---
        self.state['lines'].remove(line_to_sac)
        self.state['shields'].pop(line_to_sac.get('id'), None)

        nexus_id = self.game._generate_id('an')
        new_attuned_nexus = {
            'id': nexus_id,
            'teamId': teamId,
            'point_ids': p_ids,
            'center': nexus_to_attune['center'],
            'turns_left': 5,
            'radius_sq': (self.state['grid_size'] * 0.3)**2
        }
        if 'attuned_nexuses' not in self.state: self.state['attuned_nexuses'] = {}
        self.state['attuned_nexuses'][nexus_id] = new_attuned_nexus
        
        return {
            'success': True,
            'type': 'attune_nexus',
            'nexus': new_attuned_nexus,
            'sacrificed_line': line_to_sac
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

    def mirror_structure(self, teamId):
        """[FORTIFY ACTION]: Reflects points to create symmetry. If not possible, reinforces the structure."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 3:
            return {'success': False, 'reason': 'not enough points to mirror'}
        
        points_to_strengthen_ids = set()

        # Try a few times to find a good axis and points to mirror
        for _ in range(5):
            # 1. Select two distinct points for the axis of symmetry
            axis_p_ids = random.sample(team_point_ids, 2)
            p_axis1 = self.state['points'][axis_p_ids[0]]
            p_axis2 = self.state['points'][axis_p_ids[1]]

            # Ensure axis points are not too close
            if distance_sq(p_axis1, p_axis2) < 4.0:
                continue

            # 2. Select points to mirror
            other_point_ids = [pid for pid in team_point_ids if pid not in axis_p_ids]
            if not other_point_ids:
                continue
            
            num_to_mirror = min(len(other_point_ids), 2)
            points_to_mirror_ids = random.sample(other_point_ids, num_to_mirror)
            points_to_strengthen_ids.update(points_to_mirror_ids)
            
            new_points_to_create = []
            grid_size = self.state['grid_size']
            all_reflections_valid = True

            # 3. Reflect points and check validity
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
                # --- Primary Effect: Create Mirrored Points ---
                for p in new_points_to_create:
                    self.state['points'][p['id']] = p
                
                return {
                    'success': True, 'type': 'mirror_structure',
                    'new_points': new_points_to_create, 'axis_p1_id': axis_p_ids[0], 'axis_p2_id': axis_p_ids[1],
                }
        
        # --- Fallback Effect: Strengthen Lines ---
        if not points_to_strengthen_ids:
            # Fallback failed because we couldn't even pick points to mirror.
            return {'success': False, 'reason': 'could not select points to mirror'}

        strengthened_lines = []
        max_strength = 3
        all_team_lines = self.game.get_team_lines(teamId)
        
        for line in all_team_lines:
            if line['p1_id'] in points_to_strengthen_ids or line['p2_id'] in points_to_strengthen_ids:
                line_id = line.get('id')
                if line_id:
                    current_strength = self.state['line_strengths'].get(line_id, 0)
                    if current_strength < max_strength:
                        self.state['line_strengths'][line_id] = current_strength + 1
                        strengthened_lines.append(line)
        
        if not strengthened_lines:
            # This can happen if the chosen points have no lines or their lines are max strength.
            # To be truly "never useless", we can add a line between the last chosen axis points.
            last_axis_pids = random.sample(team_point_ids, 2)
            existing_lines_keys = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in all_team_lines}
            if tuple(sorted(last_axis_pids)) not in existing_lines_keys:
                line_id = self.game._generate_id('l')
                new_line = {"id": line_id, "p1_id": last_axis_pids[0], "p2_id": last_axis_pids[1], "teamId": teamId}
                self.state['lines'].append(new_line)
                return {'success': True, 'type': 'add_line', 'line': new_line} # Reuse add_line type
            else:
                return {'success': False, 'reason': 'mirroring failed and structure is already fully connected/strengthened'}

        return {
            'success': True, 'type': 'mirror_fizzle_strengthen',
            'strengthened_lines': strengthened_lines
        }

    def create_anchor(self, teamId):
        """[FORTIFY ACTION]: Sacrifice a point to turn another into a gravity well."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 3: # Requires at least 3 points to not cripple the team.
            return {'success': False, 'reason': 'not enough points to create anchor'}

        # Find a point to sacrifice and a point to turn into an anchor
        # Ensure they are not the same point
        p_to_sac_id, p_to_anchor_id = random.sample(team_point_ids, 2)
        
        # 1. Sacrifice the first point using the robust helper
        sacrificed_point_data = self.game._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
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

    def form_purifier(self, teamId):
        """[FORTIFY ACTION]: Forms a Purifier from a regular pentagon of points."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 5:
            return {'success': False, 'reason': 'not enough points'}

        points = self.state['points']
        existing_lines = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in self.game.get_team_lines(teamId)}
        
        # Get points already used in other major structures
        existing_purifier_points = {pid for p_list in self.state.get('purifiers', {}).values() for p in p_list for pid in p['point_ids']}

        possible_purifiers = []
        for p_ids_tuple in combinations(team_point_ids, 5):
            if any(pid in existing_purifier_points for pid in p_ids_tuple):
                continue

            p_list = [points[pid] for pid in p_ids_tuple]
            if is_regular_pentagon(*p_list):
                # To be a valid formation, the 5 outer "side" lines must exist.
                edge_data = get_edges_by_distance(p_list)
                side_pairs = edge_data['sides']

                if all(tuple(sorted(pair)) in existing_lines for pair in side_pairs):
                    possible_purifiers.append({'point_ids': list(p_ids_tuple)})
        
        if not possible_purifiers:
            return {'success': False, 'reason': 'no valid pentagon formation found'}

        chosen_purifier_data = random.choice(possible_purifiers)
        
        if teamId not in self.state.get('purifiers', {}):
            self.state['purifiers'][teamId] = []
            
        self.state['purifiers'][teamId].append(chosen_purifier_data)
        
        return {'success': True, 'type': 'form_purifier', 'purifier': chosen_purifier_data}