import random
import math
from itertools import combinations
from ..geometry import (
    distance_sq, segments_intersect, get_segment_intersection_point,
    get_extended_border_point, is_point_inside_triangle,
    points_centroid, get_angle_bisector_vector
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

    def can_perform_focus_beam(self, teamId):
        has_star_rune = bool(self.state.get('runes', {}).get(teamId, {}).get('star', []))
        num_enemy_points = len(self.state['points']) - len(self.game.get_team_point_ids(teamId))
        can_perform = has_star_rune and num_enemy_points > 0
        return can_perform, "Requires a Star Rune and an enemy point."

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
        
        bisector_v = get_angle_bisector_vector(p_vertex, p_leg1, p_leg2)
        if not bisector_v:
            return {'success': False, 'reason': 'invalid V-rune geometry'}
        
        p_end = {'x': p_vertex['x'] + bisector_v['x'], 'y': p_vertex['y'] + bisector_v['y']}
        border_point = get_extended_border_point(
            p_vertex, p_end, self.state['grid_size'],
            self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])
        )
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
            self.game._delete_line(target_line)
            return {
                'success': True, 'type': 'rune_shoot_bisector', 'destroyed_line': target_line,
                'attack_ray': {'p1': attack_ray_p1, 'p2': attack_ray_p2}, 'rune_points': rune_points_payload
            }
        else:
            # --- Fallback Effect: Create Fissure ---
            fissure_id = self.game._generate_id('f')
            # The fissure is the segment from the vertex to the border
            new_fissure = {'id': fissure_id, 'p1': p_vertex, 'p2': border_point, 'turns_left': 2}
            self.state.setdefault('fissures', []).append(new_fissure)
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
                if is_point_inside_triangle(line_p1, p1, p2, p3) and is_point_inside_triangle(line_p2, p1, p2, p3):
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
            rune_center = points_centroid(tri_points)
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
        rune_center = points_centroid(tri_points)
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
        border_point = get_extended_border_point(
            p_handle, p_apex, self.state['grid_size'],
            self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])
        )
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
                self.game._delete_line(line)
                    
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
            new_barricade = self.game._create_temporary_barricade(
                teamId, attack_ray_p1, attack_ray_p2, 2
            )

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
        from ..geometry import get_edges_by_distance, points_centroid
        p_list = [points[pid] for pid in rune_p_ids_tuple]
        edge_data = get_edges_by_distance(p_list)
        diag1_p_ids, diag2_p_ids = edge_data['diagonals']
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
                self.game._delete_line(l)
            
            return {
                'success': True, 'type': 'parallel_discharge',
                'lines_destroyed': lines_to_destroy, 'rune_points': list(rune_p_ids_tuple)
            }
        
        # --- Fallback Effect: Create central structure ---
        else:
            mid1 = points_centroid([d1_p1, d1_p2])
            mid2 = points_centroid([d2_p1, d2_p2])
            
            from ..geometry import clamp_and_round_point_coords
            grid_size = self.state['grid_size']
            p1_coords = clamp_and_round_point_coords(mid1, grid_size)
            p2_coords = clamp_and_round_point_coords(mid2, grid_size)
            
            is_valid1, _ = self.game.is_spawn_location_valid(p1_coords, teamId)
            is_valid2, _ = self.game.is_spawn_location_valid(p2_coords, teamId)
            
            if not is_valid1 or not is_valid2:
                 return {'success': False, 'reason': 'center of parallelogram is blocked'}

            p1_id = self.game._generate_id('p')
            new_p1 = {**p1_coords, 'id': p1_id, 'teamId': teamId}
            self.state['points'][p1_id] = new_p1
            
            p2_id = self.game._generate_id('p')
            new_p2 = {**p2_coords, 'id': p2_id, 'teamId': teamId}
            self.state['points'][p2_id] = new_p2
            
            line_id = self.game._generate_id('l')
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
            all_enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId and p['id'] not in self.state.get('stasis_points', {})]
            bastion_cores = self.game._get_bastion_point_ids()['cores']
            monolith_point_ids = {pid for m in self.state.get('monoliths', {}).values() for pid in m['point_ids']}

            high_value_points = [
                p for p in all_enemy_points if
                p['id'] in bastion_cores or p['id'] in monolith_point_ids
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
            enemy_centroid = points_centroid(enemy_team_points[largest_enemy_team_id])

            fissure_len = self.state['grid_size'] * 0.2
            new_fissure = self.game._create_random_fissure(enemy_centroid, fissure_len, 2)
            
            return {
                'success': True,
                'type': 'focus_beam_fizzle_fissure',
                'fissure': new_fissure,
                'rune_points': rune['all_points'],
                'beam_origin': center_point,
                'beam_target': enemy_centroid
            }