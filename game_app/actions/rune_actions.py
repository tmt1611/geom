import random
import math
import uuid
from itertools import combinations
from ..geometry import (
    distance_sq, segments_intersect, get_segment_intersection_point
)

class RuneActionsHandler:
    def __init__(self, game):
        self.game = game

    # --- Action Precondition Checks ---
    
    def can_perform_shoot_bisector(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('v_shape', []))
        return can_perform, "Requires an active V-Rune."
    
    def can_perform_area_shield(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('shield', []))
        return can_perform, "Requires an active Shield Rune."

    def can_perform_shield_pulse(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('shield', []))
        return can_perform, "Requires an active Shield Rune."

    def can_perform_impale(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('trident', []))
        return can_perform, "Requires an active Trident Rune."

    def can_perform_hourglass_stasis(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('hourglass', []))
        return can_perform, "Requires an active Hourglass Rune."

    def can_perform_starlight_cascade(self, teamId):
        can_perform = len(self._find_possible_starlight_cascades(teamId)) > 0
        return can_perform, "No Star Rune has a valid target in range."

    def can_perform_focus_beam(self, teamId):
        has_star_rune = bool(self.state.get('runes', {}).get(teamId, {}).get('star', []))
        num_enemy_points = len(self.state['points']) - len(self.game.get_team_point_ids(teamId))
        can_perform = has_star_rune and num_enemy_points > 0
        return can_perform, "Requires a Star Rune and an enemy point."

    def can_perform_t_hammer_slam(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('t_shape', []))
        return can_perform, "Requires an active T-Rune."

    def can_perform_cardinal_pulse(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('plus_shape', []))
        return can_perform, "Requires an active Plus-Rune."

    def can_perform_parallel_discharge(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('parallel', []))
        return can_perform, "Requires an active Parallelogram Rune."

    # --- End Precondition Checks ---

    @property
    def state(self):
        """Provides direct access to the game's current state dictionary."""
        return self.game.state

    def shoot_bisector(self, teamId):
        """[RUNE ACTION]: Fires a powerful beam from a V-Rune. If it misses, it creates a fissure."""
        active_v_runes = self.state.get('runes', {}).get(teamId, {}).get('v_shape', [])
        if not active_v_runes:
            return {'success': False, 'reason': 'no active V-runes'}

        rune = random.choice(active_v_runes)
        points = self.state['points']
        
        p_vertex = points.get(rune['vertex_id'])
        p_leg1 = points.get(rune['leg1_id'])
        p_leg2 = points.get(rune['leg2_id'])

        if not all([p_vertex, p_leg1, p_leg2]):
            return {'success': False, 'reason': 'rune points no longer exist'}
        
        # Calculate bisector vector
        v1 = {'x': p_leg1['x'] - p_vertex['x'], 'y': p_leg1['y'] - p_vertex['y']}
        v2 = {'x': p_leg2['x'] - p_vertex['x'], 'y': p_leg2['y'] - p_vertex['y']}
        mag1, mag2 = math.sqrt(v1['x']**2 + v1['y']**2), math.sqrt(v2['x']**2 + v2['y']**2)
        if mag1 == 0 or mag2 == 0: return {'success': False, 'reason': 'invalid V-rune geometry'}

        bisector_v = {'x': v1['x']/mag1 + v2['x']/mag2, 'y': v1['y']/mag1 + v2['y']/mag2}
        mag_b = math.sqrt(bisector_v['x']**2 + bisector_v['y']**2)
        if mag_b == 0: return {'success': False, 'reason': 'V-rune legs are opposing'}

        p_end = {'x': p_vertex['x'] + bisector_v['x']/mag_b, 'y': p_vertex['y'] + bisector_v['y']/mag_b}
        border_point = self.game._get_extended_border_point(p_vertex, p_end)
        if not border_point: return {'success': False, 'reason': 'bisector attack path blocked'}
        
        attack_ray_p1, attack_ray_p2 = p_vertex, border_point

        # Find first enemy line intersected by this ray
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        hits = []
        for line in enemy_lines:
            if line['p1_id'] not in points or line['p2_id'] not in points: continue
            # This attack CAN destroy bastion lines, but not shielded lines.
            if line.get('id') in self.state['shields']: continue
            
            ep1, ep2 = points[line['p1_id']], points[line['p2_id']]
            if get_segment_intersection_point(attack_ray_p1, attack_ray_p2, ep1, ep2):
                hits.append(line)
        
        rune_points_payload = [rune['vertex_id'], rune['leg1_id'], rune['leg2_id']]

        if hits:
            # --- Primary Effect: Destroy Line ---
            target_line = random.choice(hits)
            self.state['lines'].remove(target_line)
            self.state['shields'].pop(target_line.get('id'), None)
            return {
                'success': True, 'type': 'rune_shoot_bisector', 'destroyed_line': target_line,
                'attack_ray': {'p1': attack_ray_p1, 'p2': attack_ray_p2}, 'rune_points': rune_points_payload
            }
        else:
            # --- Fallback Effect: Create Fissure ---
            fissure_id = f"f_{uuid.uuid4().hex[:6]}"
            # The fissure is the segment from the vertex to the border
            new_fissure = {'id': fissure_id, 'p1': p_vertex, 'p2': border_point, 'turns_left': 2}
            self.state['fissures'].append(new_fissure)
            return {
                'success': True, 'type': 'vbeam_miss_fissure', 'fissure': new_fissure,
                'attack_ray': {'p1': attack_ray_p1, 'p2': attack_ray_p2}, 'rune_points': rune_points_payload
            }
    
    def area_shield(self, teamId):
        """[RUNE ACTION]: Uses a Shield Rune to protect internal lines, or de-clutter friendly points."""
        active_shield_runes = self.state.get('runes', {}).get(teamId, {}).get('shield', [])
        if not active_shield_runes:
            return {'success': False, 'reason': 'no active Shield Runes'}

        rune = random.choice(active_shield_runes)
        points = self.state['points']
        all_rune_pids = rune['triangle_ids'] + [rune['core_id']]
        if not all(pid in points for pid in all_rune_pids):
            return {'success': False, 'reason': 'rune points no longer exist'}
            
        tri_points = [points[pid] for pid in rune['triangle_ids']]
        p1, p2, p3 = tri_points[0], tri_points[1], tri_points[2]
        
        # --- Find Primary Targets ---
        lines_to_shield = []
        for line in self.game.get_team_lines(teamId):
            if line.get('id') in self.state['shields']: continue
            line_p1, line_p2 = points.get(line['p1_id']), points.get(line['p2_id'])
            if line_p1 and line_p2 and line_p1['id'] not in rune['triangle_ids'] and line_p2['id'] not in rune['triangle_ids']:
                if self.game._is_point_inside_triangle(line_p1, p1, p2, p3) and self.game._is_point_inside_triangle(line_p2, p1, p2, p3):
                    lines_to_shield.append(line)
        
        if lines_to_shield:
            # --- Primary Effect: Shield Lines ---
            for line in lines_to_shield:
                self.state['shields'][line['id']] = 3 # Shield for 3 turns
            return {
                'success': True, 'type': 'rune_area_shield', 'shielded_lines_count': len(lines_to_shield),
                'rune_points': all_rune_pids, 'rune_triangle_ids': rune['triangle_ids']
            }
        else:
            # --- Fallback Effect: Push Friendly Points ---
            pushed_points = []
            rune_center = self.game._points_centroid(tri_points)
            push_radius_sq = (self.state['grid_size'] * 0.2)**2
            push_distance = 1.5
            grid_size = self.state['grid_size']
            
            # Find friendly points inside the push radius (but not part of the rune itself)
            for point in [p for p in points.values() if p['teamId'] == teamId and p['id'] not in all_rune_pids]:
                if distance_sq(rune_center, point) < push_radius_sq:
                    dx, dy = point['x'] - rune_center['x'], point['y'] - rune_center['y']
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist < 0.1: continue

                    point['x'] = round(max(0, min(grid_size - 1, point['x'] + (dx/dist) * push_distance)))
                    point['y'] = round(max(0, min(grid_size - 1, point['y'] + (dy/dist) * push_distance)))
                    pushed_points.append(point.copy())
            
            return {
                'success': True, 'type': 'area_shield_fizzle_push', 'pushed_points_count': len(pushed_points),
                'rune_points': all_rune_pids, 'pulse_center': rune_center, 'pulse_radius_sq': push_radius_sq
            }

    def shield_pulse(self, teamId):
        """[RUNE ACTION]: Uses a Shield Rune to push enemies away, or pull allies in."""
        active_shield_runes = self.state.get('runes', {}).get(teamId, {}).get('shield', [])
        if not active_shield_runes:
            return {'success': False, 'reason': 'no active Shield Runes'}

        rune = random.choice(active_shield_runes)
        points = self.state['points']
        all_rune_pids = rune['triangle_ids'] + [rune['core_id']]
        if not all(pid in points for pid in all_rune_pids):
            return {'success': False, 'reason': 'rune points no longer exist'}
            
        tri_points = [points[pid] for pid in rune['triangle_ids']]
        rune_center = self.game._points_centroid(tri_points)
        if not rune_center: return {'success': False, 'reason': 'could not calculate rune center'}

        pulse_radius_sq = (self.state['grid_size'] * 0.3)**2
        grid_size = self.state['grid_size']

        # --- Find Primary Targets (Enemies) ---
        enemy_points_in_range = [p for p in points.values() if p['teamId'] != teamId and distance_sq(rune_center, p) < pulse_radius_sq]

        if enemy_points_in_range:
            # --- Primary Effect: Push Enemies ---
            pushed_points = []
            push_distance = 3.0
            for point in enemy_points_in_range:
                dx, dy = point['x'] - rune_center['x'], point['y'] - rune_center['y']
                dist = math.sqrt(dx**2 + dy**2)
                if dist < 0.1: continue
                
                new_x = point['x'] + (dx / dist) * push_distance
                new_y = point['y'] + (dy / dist) * push_distance
                point['x'] = round(max(0, min(grid_size - 1, new_x)))
                point['y'] = round(max(0, min(grid_size - 1, new_y)))
                pushed_points.append(point.copy())

            return {
                'success': True, 'type': 'rune_shield_pulse', 'pushed_points_count': len(pushed_points),
                'rune_points': all_rune_pids, 'pulse_center': rune_center, 'pulse_radius_sq': pulse_radius_sq
            }
        else:
            # --- Fallback Effect: Pull Allies ---
            pulled_points = []
            pull_distance = 1.5
            # Find friendly points inside the pulse radius (but not part of the rune itself)
            for point in [p for p in points.values() if p['teamId'] == teamId and p['id'] not in all_rune_pids]:
                if distance_sq(rune_center, point) < pulse_radius_sq:
                    dx, dy = rune_center['x'] - point['x'], rune_center['y'] - point['y']
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist < 0.1: continue
                    
                    new_x = point['x'] + (dx / dist) * pull_distance
                    new_y = point['y'] + (dy / dist) * pull_distance
                    point['x'] = round(max(0, min(grid_size - 1, new_x)))
                    point['y'] = round(max(0, min(grid_size - 1, new_y)))
                    pulled_points.append(point.copy())
            
            return {
                'success': True, 'type': 'shield_pulse_fizzle_pull', 'pulled_points_count': len(pulled_points),
                'rune_points': all_rune_pids, 'pulse_center': rune_center, 'pulse_radius_sq': pulse_radius_sq
            }

    def impale(self, teamId):
        """[RUNE ACTION]: Fires a powerful, shield-piercing beam from a Trident Rune. If it misses, it creates a temporary barricade."""
        active_trident_runes = self.state.get('runes', {}).get(teamId, {}).get('trident', [])
        if not active_trident_runes:
            return {'success': False, 'reason': 'no active Trident Runes'}
            
        rune = random.choice(active_trident_runes)
        points = self.state['points']
        
        p_handle = points.get(rune['handle_id'])
        p_apex = points.get(rune['apex_id'])
        
        if not p_handle or not p_apex:
            return {'success': False, 'reason': 'rune points no longer exist'}
            
        # The attack fires from the apex, directed by the handle
        border_point = self.game._get_extended_border_point(p_handle, p_apex)
        if not border_point:
            return {'success': False, 'reason': 'impale attack does not hit border'}
            
        attack_ray_p1 = p_apex
        attack_ray_p2 = border_point
        
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        lines_to_destroy = []
        intersection_points = []
        bastion_line_ids = self.game._get_bastion_line_ids()
        
        for line in enemy_lines:
            if line.get('id') in bastion_line_ids:
                continue # Cannot impale bastion lines
            if line['p1_id'] not in points or line['p2_id'] not in points:
                continue
            
            ep1 = points[line['p1_id']]
            ep2 = points[line['p2_id']]
            
            intersection_pt = get_segment_intersection_point(attack_ray_p1, attack_ray_p2, ep1, ep2)
            if intersection_pt:
                lines_to_destroy.append(line)
                intersection_points.append(intersection_pt)

        rune_points_payload = [rune['handle_id'], rune['apex_id']] + rune['prong_ids']

        if lines_to_destroy:
            # --- Primary Effect: Destroy Lines ---
            for line in lines_to_destroy:
                if line in self.state['lines']:
                    self.state['lines'].remove(line)
                    self.state['shields'].pop(line.get('id'), None) # Pierces shields
                    self.state['line_strengths'].pop(line.get('id'), None) # Pierces monolith empowerment
                    
            return {
                'success': True,
                'type': 'rune_impale',
                'destroyed_lines': lines_to_destroy,
                'intersection_points': intersection_points,
                'attack_ray': {'p1': attack_ray_p1, 'p2': attack_ray_p2},
                'rune_points': rune_points_payload
            }
        else:
            # --- Fallback Effect: Create Barricade ---
            barricade_id = f"bar_{uuid.uuid4().hex[:6]}"
            new_barricade = {
                'id': barricade_id,
                'teamId': teamId,
                'p1': {'x': attack_ray_p1['x'], 'y': attack_ray_p1['y']},
                'p2': {'x': attack_ray_p2['x'], 'y': attack_ray_p2['y']},
                'turns_left': 2 # A short-lived barricade
            }
            if 'barricades' not in self.state: self.state['barricades'] = []
            self.state['barricades'].append(new_barricade)

            return {
                'success': True,
                'type': 'impale_fizzle_barricade',
                'barricade': new_barricade,
                'attack_ray': {'p1': attack_ray_p1, 'p2': attack_ray_p2},
                'rune_points': rune_points_payload
            }

    def parallel_discharge(self, teamId):
        """[RUNE ACTION]: Uses a Parallel Rune to destroy crossing enemy lines. If none, creates a central structure."""
        active_parallel_runes = self.state.get('runes', {}).get(teamId, {}).get('parallel', [])
        if not active_parallel_runes:
            return {'success': False, 'reason': 'no active Parallel Runes'}

        rune_p_ids_tuple = random.choice(active_parallel_runes)
        points = self.state['points']
        
        if not all(pid in points for pid in rune_p_ids_tuple):
            return {'success': False, 'reason': 'rune points no longer exist'}
        
        # Find diagonals
        all_pairs = list(combinations(rune_p_ids_tuple, 2))
        all_pair_dists = {pair: distance_sq(points[pair[0]], points[pair[1]]) for pair in all_pairs}
        sorted_pairs = sorted(all_pair_dists.keys(), key=lambda pair: all_pair_dists[pair])
        diag1_p_ids = sorted_pairs[-1]
        diag2_p_ids = sorted_pairs[-2]
        d1_p1, d1_p2 = points[diag1_p_ids[0]], points[diag1_p_ids[1]]
        d2_p1, d2_p2 = points[diag2_p_ids[0]], points[diag2_p_ids[1]]

        # --- Primary Effect: Find and destroy crossing lines ---
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        lines_to_destroy = []
        for line in enemy_lines:
            if not (line['p1_id'] in points and line['p2_id'] in points): continue
            
            ep1, ep2 = points[line['p1_id']], points[line['p2_id']]
            
            # A line crosses if it intersects either diagonal
            if segments_intersect(ep1, ep2, d1_p1, d1_p2) or segments_intersect(ep1, ep2, d2_p1, d2_p2):
                lines_to_destroy.append(line)
        
        if lines_to_destroy:
            for l in lines_to_destroy:
                if l in self.state['lines']:
                    self.state['lines'].remove(l)
                    self.state['shields'].pop(l.get('id'), None)
            
            return {
                'success': True, 'type': 'parallel_discharge',
                'lines_destroyed': lines_to_destroy, 'rune_points': list(rune_p_ids_tuple)
            }
        
        # --- Fallback Effect: Create central structure ---
        else:
            mid1 = self.game._points_centroid([d1_p1, d1_p2])
            mid2 = self.game._points_centroid([d2_p1, d2_p2])
            
            grid_size = self.state['grid_size']
            p1_coords = {
                'x': round(max(0, min(grid_size - 1, mid1['x']))),
                'y': round(max(0, min(grid_size - 1, mid1['y'])))
            }
            p2_coords = {
                'x': round(max(0, min(grid_size - 1, mid2['x']))),
                'y': round(max(0, min(grid_size - 1, mid2['y'])))
            }
            
            is_valid1, _ = self.game._is_spawn_location_valid(p1_coords, teamId)
            is_valid2, _ = self.game._is_spawn_location_valid(p2_coords, teamId)
            
            if not is_valid1 or not is_valid2:
                 return {'success': False, 'reason': 'center of parallelogram is blocked'}

            p1_id = f"p_{uuid.uuid4().hex[:6]}"
            new_p1 = {**p1_coords, 'id': p1_id, 'teamId': teamId}
            self.state['points'][p1_id] = new_p1
            
            p2_id = f"p_{uuid.uuid4().hex[:6]}"
            new_p2 = {**p2_coords, 'id': p2_id, 'teamId': teamId}
            self.state['points'][p2_id] = new_p2
            
            line_id = f"l_{uuid.uuid4().hex[:6]}"
            new_line = {'id': line_id, 'p1_id': p1_id, 'p2_id': p2_id, 'teamId': teamId}
            self.state['lines'].append(new_line)
            
            return {
                'success': True, 'type': 'parallel_discharge_fizzle_spawn',
                'new_points': [new_p1, new_p2], 'new_line': new_line, 'rune_points': list(rune_p_ids_tuple)
            }

    def hourglass_stasis(self, teamId):
        """[RUNE ACTION]: Uses an Hourglass Rune to freeze an enemy point. If no target, creates an anchor."""
        active_hourglass_runes = self.state.get('runes', {}).get(teamId, {}).get('hourglass', [])
        if not active_hourglass_runes:
            return {'success': False, 'reason': 'no active Hourglass Runes'}

        rune = random.choice(active_hourglass_runes)
        points_map = self.state['points']
        
        rune_pids = rune['all_points']
        if not all(pid in points_map for pid in rune_pids):
            return {'success': False, 'reason': 'rune points no longer exist'}
        
        p_vertex = points_map[rune['vertex_id']]
        stasis_range_sq = (self.state['grid_size'] * 0.3)**2
        
        enemy_points = self.game._get_vulnerable_enemy_points(teamId)
        possible_targets = [ep for ep in enemy_points if distance_sq(p_vertex, ep) < stasis_range_sq]

        if possible_targets:
            # --- Primary Effect: Apply Stasis ---
            target_point = random.choice(possible_targets)
            self.state['stasis_points'][target_point['id']] = 3 # 3 turns
            target_team_name = self.state['teams'][target_point['teamId']]['name']
            return {
                'success': True, 'type': 'rune_hourglass_stasis',
                'target_point': target_point, 'rune_points': rune_pids, 'rune_vertex_id': rune['vertex_id'],
                'target_team_name': target_team_name
            }
        else:
            # --- Fallback Effect: Create Anchor ---
            if len(rune_pids) < 2:
                return {'success': False, 'reason': 'not enough rune points for fallback anchor'}
            
            # Sacrifice one point from the rune to make another an anchor.
            p_to_sac_id, p_to_anchor_id = random.sample(rune_pids, 2)
            
            sacrificed_point_data = self.game._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
            if not sacrificed_point_data:
                return {'success': False, 'reason': 'failed to sacrifice rune point for fallback'}
            
            # Check if anchor point still exists after cascade
            if p_to_anchor_id not in self.state['points']:
                # The anchor point was destroyed by the sacrifice of its neighbor. The action is just the sacrifice.
                return {'success': True, 'type': 'hourglass_fizzle_anchor', 'anchor_point': None, 'sacrificed_point': sacrificed_point_data, 'rune_points': rune_pids}
            
            self.state['anchors'][p_to_anchor_id] = {'teamId': teamId, 'turns_left': 3}
            anchor_point = self.state['points'][p_to_anchor_id]

            return {
                'success': True, 'type': 'hourglass_fizzle_anchor',
                'anchor_point': anchor_point, 'sacrificed_point': sacrificed_point_data, 'rune_points': rune_pids
            }
    
    def _find_possible_starlight_cascades(self, teamId):
        active_star_runes = self.state.get('runes', {}).get(teamId, {}).get('star', [])
        if not active_star_runes: return []

        damage_radius_sq = (self.state['grid_size'] * 0.3)**2
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        bastion_line_ids = self.game._get_bastion_line_ids()
        points_map = self.state['points']

        potential_cascades = []
        # A bit complex: we want to return a list of valid {rune, sac_point_id} dicts
        for rune in active_star_runes:
            if not rune.get('cycle_ids'): continue
            
            for p_to_sac_id in rune['cycle_ids']:
                if p_to_sac_id not in points_map: continue
                sac_point_coords = points_map[p_to_sac_id]
                
                has_target = False
                for line in enemy_lines:
                    # Starlight cascade damages, it doesn't destroy shields/bastions, so skip them
                    if line.get('id') in bastion_line_ids or line.get('id') in self.state['shields']: continue
                    if line['p1_id'] not in points_map or line['p2_id'] not in points_map: continue
                    p1 = points_map[line['p1_id']]
                    p2 = points_map[line['p2_id']]
                    midpoint = {'x': (p1['x'] + p2['x']) / 2, 'y': (p1['y'] + p2['y']) / 2}

                    if distance_sq(sac_point_coords, midpoint) < damage_radius_sq:
                        potential_cascades.append({'rune': rune, 'sac_point_id': p_to_sac_id})
                        has_target = True
                        break # Found a target for this point, move to next sac candidate
                if has_target:
                    # Since we only need one valid sacrificial point per rune to make the rune "activatable"
                    # we could break here. But for the action to be effective, we want to pick from *any*
                    # valid sacrificial point. So we continue checking all sac points.
                    pass
        return potential_cascades

    def starlight_cascade(self, teamId):
        """[RUNE ACTION]: A Star Rune sacrifices a point to damage nearby enemy lines."""
        possible_cascades = self._find_possible_starlight_cascades(teamId)
        if not possible_cascades:
            return {'success': False, 'reason': 'no valid targets for starlight cascade'}

        chosen_cascade = random.choice(possible_cascades)
        rune = chosen_cascade['rune']
        p_to_sac_id = chosen_cascade['sac_point_id']
        sacrificed_point_data = self.game._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
        
        if not sacrificed_point_data:
            return {'success': False, 'reason': 'failed to sacrifice rune point'}
            
        # Define damage area
        damage_radius_sq = (self.state['grid_size'] * 0.3)**2
        
        # Find enemy lines within the area
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        bastion_line_ids = self.game._get_bastion_line_ids()
        damaged_lines = []
        points_map = self.state['points']

        for line in enemy_lines:
            if line.get('id') in bastion_line_ids or line.get('id') in self.state['shields']:
                continue
            if line['p1_id'] not in points_map or line['p2_id'] not in points_map:
                continue
            
            p1 = points_map[line['p1_id']]
            p2 = points_map[line['p2_id']]
            midpoint = {'x': (p1['x'] + p2['x']) / 2, 'y': (p1['y'] + p2['y']) / 2}

            if distance_sq(sacrificed_point_data, midpoint) < damage_radius_sq:
                # Damage the line by reducing its strength
                line_strength = self.state.get('line_strengths', {}).get(line['id'])
                if line_strength and line_strength > 0:
                    self.state['line_strengths'][line['id']] -= 1
                    damaged_lines.append(line)
                    if self.state['line_strengths'][line['id']] <= 0:
                        del self.state['line_strengths'][line['id']]
                else:
                    # Line had no strength, so it's destroyed
                    if line in self.state['lines']:
                        self.state['lines'].remove(line)
                        damaged_lines.append(line)

        return {
            'success': True,
            'type': 'rune_starlight_cascade',
            'damaged_lines': damaged_lines,
            'sacrificed_point': sacrificed_point_data,
            'rune_points': rune['all_points']
        }

    def focus_beam(self, teamId):
        """[RUNE ACTION]: A Star Rune fires a beam at a high-value target. If none, a regular one. If no targets, creates a fissure."""
        active_star_runes = self.state.get('runes', {}).get(teamId, {}).get('star', [])
        if not active_star_runes:
            return {'success': False, 'reason': 'no active Star Runes'}

        rune = random.choice(active_star_runes)
        points_map = self.state['points']
        center_point = points_map.get(rune['center_id'])
        if not center_point or not all(pid in points_map for pid in rune['cycle_ids']):
            return {'success': False, 'reason': 'rune points no longer exist'}
            
        # --- Target Prioritization ---
        target_point, target_wonder, target_type = None, None, None

        # 1. High-value structures
        wonder_coords_list = [w for w in self.state.get('wonders', {}).values() if w['teamId'] != teamId]
        if wonder_coords_list:
            target_wonder = min(wonder_coords_list, key=lambda w: distance_sq(center_point, w['coords']))
            target_type = 'wonder'
        else:
            high_value_points = [
                p for p in self.game._get_vulnerable_enemy_points(teamId) if 
                p['id'] in self.game._get_bastion_point_ids()['cores'] or 
                p['id'] in {pid for m in self.state.get('monoliths', {}).values() for pid in m['point_ids']}
            ]
            if high_value_points:
                target_point = min(high_value_points, key=lambda p: distance_sq(center_point, p))
                target_type = 'high_value_point'
        
        # 2. Fallback to any vulnerable enemy
        if not target_type:
            vulnerable_targets = self.game._get_vulnerable_enemy_points(teamId)
            if vulnerable_targets:
                target_point = min(vulnerable_targets, key=lambda p: distance_sq(center_point, p))
                target_type = 'fallback_point'

        # --- Execute Action ---
        if target_type:
            destroyed_point_data, destroyed_wonder_data = None, None
            if target_type == 'wonder':
                destroyed_wonder_data = self.state['wonders'].pop(target_wonder['id'])
                team_name = self.state['teams'][destroyed_wonder_data['teamId']]['name']
                self.state['game_log'].append({'teamId': teamId, 'message': f"The Focus Beam obliterated the Chronos Spire of Team {team_name}!", 'short_message': '[WONDER DESTROYED!]'})
            else:
                destroyed_point_data = self.game._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
                if not destroyed_point_data:
                    return {'success': False, 'reason': 'failed to destroy target point'}
            
            result_payload = {
                'success': True,
                'type': 'rune_focus_beam' if target_type != 'fallback_point' else 'focus_beam_fallback_hit',
                'destroyed_point': destroyed_point_data,
                'destroyed_wonder': destroyed_wonder_data,
                'rune_points': rune['all_points'],
                'beam_origin': center_point,
                'beam_target': (target_point or target_wonder.get('coords'))
            }
            if destroyed_point_data:
                result_payload['destroyed_team_name'] = self.state['teams'][destroyed_point_data['teamId']]['name']
            
            return result_payload
        
        # 3. Fallback to creating a fissure if no targets were found at all
        else:
            # Aim at the centroid of the enemy team with the most points
            enemy_team_points = {}
            for pid, p in points_map.items():
                if p['teamId'] != teamId:
                    if p['teamId'] not in enemy_team_points: enemy_team_points[p['teamId']] = []
                    enemy_team_points[p['teamId']].append(p)
            
            if not enemy_team_points:
                return {'success': False, 'reason': 'no enemies to target for focus beam fizzle'}

            largest_enemy_team_id = max(enemy_team_points, key=lambda tid: len(enemy_team_points[tid]))
            enemy_centroid = self.game._points_centroid(enemy_team_points[largest_enemy_team_id])

            fissure_id = f"f_{uuid.uuid4().hex[:6]}"
            fissure_len = self.state['grid_size'] * 0.2
            angle = random.uniform(0, math.pi)
            p1 = {'x': enemy_centroid['x'] - (fissure_len / 2) * math.cos(angle), 'y': enemy_centroid['y'] - (fissure_len / 2) * math.sin(angle)}
            p2 = {'x': enemy_centroid['x'] + (fissure_len / 2) * math.cos(angle), 'y': enemy_centroid['y'] + (fissure_len / 2) * math.sin(angle)}

            grid_size = self.state['grid_size']
            p1['x'] = round(max(0, min(grid_size - 1, p1['x'])))
            p1['y'] = round(max(0, min(grid_size - 1, p1['y'])))
            p2['x'] = round(max(0, min(grid_size - 1, p2['x'])))
            p2['y'] = round(max(0, min(grid_size - 1, p2['y'])))

            new_fissure = {'id': fissure_id, 'p1': p1, 'p2': p2, 'turns_left': 2}
            self.state['fissures'].append(new_fissure)
            
            return {
                'success': True,
                'type': 'focus_beam_fizzle_fissure',
                'fissure': new_fissure,
                'rune_points': rune['all_points'],
                'beam_origin': center_point,
                'beam_target': enemy_centroid
            }

    def cardinal_pulse(self, teamId):
        """[RUNE ACTION]: A Plus-Rune is consumed to fire four beams from its center. Beams destroy the first enemy line hit, or create a point on the border if they miss."""
        active_plus_runes = self.state.get('runes', {}).get(teamId, {}).get('plus_shape', [])
        if not active_plus_runes:
            return {'success': False, 'reason': 'no active Plus-Runes'}
        
        rune = random.choice(active_plus_runes)
        points_map = self.state['points']
        center_point = points_map.get(rune['center_id'])

        if not center_point or not all(pid in points_map for pid in rune['arm_ids']):
             return {'success': False, 'reason': 'rune points no longer exist'}
        
        # --- Consume the rune ---
        sacrificed_points_data = []
        for pid in rune['all_points']:
            sac_data = self.game._delete_point_and_connections(pid, aggressor_team_id=teamId)
            if sac_data:
                sacrificed_points_data.append(sac_data)

        if not sacrificed_points_data:
            return {'success': False, 'reason': 'failed to sacrifice points for cardinal pulse'}
            
        # --- Fire 4 beams ---
        lines_destroyed = []
        points_created = []
        attack_rays = []
        
        for arm_pid in rune['arm_ids']:
            # The arm point itself was sacrificed, so we use its last known coordinates from the sacrifice data.
            arm_point_data = next((p for p in sacrificed_points_data if p['id'] == arm_pid), None)
            if not arm_point_data: continue

            border_point = self.game._get_extended_border_point(center_point, arm_point_data)
            if not border_point: continue

            attack_ray = {'p1': center_point, 'p2': border_point}
            attack_rays.append(attack_ray)
            
            # This is complex because points/lines are being removed as we iterate.
            # We need to check against the current state of the board for each beam.
            enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
            hits = []
            for enemy_line in enemy_lines:
                 # Cardinal Pulse is powerful, it bypasses shields but not bastions.
                if enemy_line.get('id') in self.game._get_bastion_line_ids(): continue
                if enemy_line['p1_id'] not in self.state['points'] or enemy_line['p2_id'] not in self.state['points']: continue
                
                ep1 = self.state['points'][enemy_line['p1_id']]
                ep2 = self.state['points'][enemy_line['p2_id']]

                intersection_point = get_segment_intersection_point(attack_ray['p1'], attack_ray['p2'], ep1, ep2)
                if intersection_point:
                    dist_sq = distance_sq(attack_ray['p1'], intersection_point)
                    hits.append({'line': enemy_line, 'dist_sq': dist_sq})
            
            if hits:
                # Destroy the closest line hit by this beam
                closest_hit = min(hits, key=lambda h: h['dist_sq'])
                line_to_destroy = closest_hit['line']
                
                if line_to_destroy in self.state['lines']: # Check it hasn't been destroyed by another beam
                    self.state['lines'].remove(line_to_destroy)
                    self.state['shields'].pop(line_to_destroy.get('id'), None)
                    self.state['line_strengths'].pop(line_to_destroy.get('id'), None)
                    lines_destroyed.append(line_to_destroy)
            else:
                # Miss: create point on border
                is_valid, _ = self.game._is_spawn_location_valid(border_point, teamId)
                if is_valid:
                    new_point_id = f"p_{uuid.uuid4().hex[:6]}"
                    new_point = {**border_point, "teamId": teamId, "id": new_point_id}
                    self.state['points'][new_point_id] = new_point
                    points_created.append(new_point)

        if not lines_destroyed and not points_created:
            return {'success': False, 'reason': 'cardinal pulse had no effect'}

        return {
            'success': True,
            'type': 'rune_cardinal_pulse',
            'sacrificed_points': sacrificed_points_data,
            'lines_destroyed': lines_destroyed,
            'points_created': points_created,
            'attack_rays': attack_rays
        }

    def t_hammer_slam(self, teamId):
        """[RUNE ACTION]: A T-Rune sacrifices its head to push points away from its stem."""
        active_t_runes = self.state.get('runes', {}).get(teamId, {}).get('t_shape', [])
        if not active_t_runes:
            return {'success': False, 'reason': 'no active T-Runes'}
            
        rune = random.choice(active_t_runes)
        points = self.state['points']
        
        if not all(pid in points for pid in rune['all_points']):
            return {'success': False, 'reason': 'rune points no longer exist'}
            
        # Sacrifice the head point
        sacrificed_point_data = self.game._delete_point_and_connections(rune['head_id'], aggressor_team_id=teamId)
        if not sacrificed_point_data:
            return {'success': False, 'reason': 'failed to sacrifice rune head point'}
        
        # Check if stem points still exist after potential cascade
        p_stem1 = points.get(rune['stem1_id'])
        p_stem2 = points.get(rune['stem2_id'])
        if not p_stem1 or not p_stem2:
             return {'success': False, 'reason': 'rune stem points were destroyed during sacrifice'}
             
        # Find points to push
        pushed_points = []
        push_dist = 2.0
        push_width = 2.0 # How far from the line to check
        grid_size = self.state['grid_size']

        # Vector for the stem and its perpendicular
        v_stem_x, v_stem_y = p_stem2['x'] - p_stem1['x'], p_stem2['y'] - p_stem1['y']
        mag_stem = math.sqrt(v_stem_x**2 + v_stem_y**2)
        v_perp_x, v_perp_y = -v_stem_y / mag_stem, v_stem_x / mag_stem

        for p_target in list(points.values()):
            if p_target['id'] in rune['all_points']: continue

            # Check distance from line segment
            # Project p_target onto the stem line
            v_s1_t_x, v_s1_t_y = p_target['x'] - p_stem1['x'], p_target['y'] - p_stem1['y']
            dot = v_s1_t_x * v_stem_x + v_s1_t_y * v_stem_y
            t = max(0, min(1, dot / (mag_stem**2)))
            
            p_closest = {'x': p_stem1['x'] + t * v_stem_x, 'y': p_stem1['y'] + t * v_stem_y}
            
            if distance_sq(p_target, p_closest) < push_width**2:
                # Push the point
                p_target['x'] = round(max(0, min(grid_size - 1, p_target['x'] + v_perp_x * push_dist)))
                p_target['y'] = round(max(0, min(grid_size - 1, p_target['y'] + v_perp_y * push_dist)))
                pushed_points.append(p_target.copy())

        if pushed_points:
            return {
                'success': True, 'type': 'rune_t_hammer_slam',
                'pushed_points_count': len(pushed_points), 'sacrificed_point': sacrificed_point_data,
                'rune_points': rune['all_points']
            }
        else:
            # Fallback: Strengthen the stem lines
            strengthened_lines = []
            max_strength = 3
            stem_lines_keys = [tuple(sorted((rune['mid_id'], rune['stem1_id']))), tuple(sorted((rune['mid_id'], rune['stem2_id'])))]
            for line in self.game.get_team_lines(teamId):
                if tuple(sorted((line['p1_id'], line['p2_id']))) in stem_lines_keys:
                    line_id = line.get('id')
                    if line_id and self.state['line_strengths'].get(line_id, 0) < max_strength:
                        self.state['line_strengths'][line_id] = self.state['line_strengths'].get(line_id, 0) + 1
                        strengthened_lines.append(line)
            
            return {
                'success': True, 'type': 't_slam_fizzle_reinforce',
                'strengthened_lines': strengthened_lines, 'sacrificed_point': sacrificed_point_data,
                'rune_points': rune['all_points']
            }