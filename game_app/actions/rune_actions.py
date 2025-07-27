import random
import math
from itertools import combinations
from ..geometry import (
    distance_sq, segments_intersect, get_segment_intersection_point,
    get_extended_border_point, is_point_in_polygon,
    points_centroid, get_angle_bisector_vector, clamp_and_round_point_coords
)

class RuneActionsHandler:
    def __init__(self, game):
        self.game = game

    @property
    def state(self):
        """Provides direct access to the game's current state dictionary."""
        return self.game.state

    def _shoot_bisector_fallback_strengthen(self, teamId, rune):
        strengthened_lines = []
        all_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.game.query.get_team_lines(teamId)}
        
        # Strengthen the two legs of the V
        key1 = tuple(sorted((rune['vertex_id'], rune['leg1_id'])))
        key2 = tuple(sorted((rune['vertex_id'], rune['leg2_id'])))

        if key1 in all_lines_by_points and self.game._strengthen_line(all_lines_by_points[key1]):
            strengthened_lines.append(all_lines_by_points[key1])
        if key2 in all_lines_by_points and self.game._strengthen_line(all_lines_by_points[key2]):
            strengthened_lines.append(all_lines_by_points[key2])

        return {
            'success': True,
            'type': 'vbeam_fizzle_strengthen',
            'strengthened_lines': strengthened_lines,
            'rune_points': [rune['vertex_id'], rune['leg1_id'], rune['leg2_id']]
        }

    def shoot_bisector(self, teamId):
        """[RUNE ACTION]: Fires a powerful beam from a V-Rune. If it misses, it creates a fissure."""
        active_v_runes = self.state.get('runes', {}).get(teamId, {}).get('v_shape', [])
        if not active_v_runes:
            return {'success': False, 'reason': 'no active V-runes'}

        # Choose the V-Rune closest to an enemy
        enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId]
        points = self.state['points']
        
        def get_v_rune_proximity(v_rune):
            if not enemy_points or v_rune['vertex_id'] not in points: return float('inf')
            return min(distance_sq(points[v_rune['vertex_id']], ep) for ep in enemy_points)
            
        rune = min(active_v_runes, key=get_v_rune_proximity)
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
        if not border_point:
            return self._shoot_bisector_fallback_strengthen(teamId, rune)
        
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
            # Hit the closest line to the rune's vertex
            target_line = min(hits, key=lambda h: distance_sq(p_vertex, points_centroid([points[h['p1_id']], points[h['p2_id']]])))
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

        # Choose the shield rune with the most friendly lines inside it
        points = self.state['points']
        team_lines = self.game.query.get_team_lines(teamId)
        
        def count_shieldable_lines(shield_rune):
            tri_points = [points.get(pid) for pid in shield_rune['triangle_ids']]
            if not all(tri_points): return 0
            count = 0
            for line in team_lines:
                line_p1, line_p2 = points.get(line['p1_id']), points.get(line['p2_id'])
                if line_p1 and line_p2:
                    if is_point_in_polygon(line_p1, tri_points) and is_point_in_polygon(line_p2, tri_points):
                        count += 1
            return count

        rune = max(active_shield_runes, key=count_shieldable_lines)
        points = self.state['points']
        all_rune_pids = rune['triangle_ids'] + [rune['core_id']]
        if not all(pid in points for pid in all_rune_pids):
            return {'success': False, 'reason': 'rune points no longer exist'}
            
        tri_points = [points[pid] for pid in rune['triangle_ids']]
        p1, p2, p3 = tri_points[0], tri_points[1], tri_points[2]
        
        # --- Find Primary Targets ---
        lines_to_shield = []
        for line in self.game.query.get_team_lines(teamId):
            if line.get('id') in self.state['shields']: continue
            line_p1, line_p2 = points.get(line['p1_id']), points.get(line['p2_id'])
            if line_p1 and line_p2 and line_p1['id'] not in rune['triangle_ids'] and line_p2['id'] not in rune['triangle_ids']:
                if is_point_in_polygon(line_p1, [p1, p2, p3]) and is_point_in_polygon(line_p2, [p1, p2, p3]):
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

        # Choose the shield rune closest to the most enemies
        points = self.state['points']
        enemy_points = [p for p in points.values() if p['teamId'] != teamId]

        def count_enemies_in_range(shield_rune):
            if not enemy_points: return 0
            tri_points = [points[pid] for pid in shield_rune['triangle_ids'] if pid in points]
            if not tri_points: return 0
            rune_center = points_centroid(tri_points)
            if not rune_center: return 0
            pulse_radius_sq = (self.state['grid_size'] * 0.3)**2
            return sum(1 for p in enemy_points if distance_sq(rune_center, p) < pulse_radius_sq)

        rune = max(active_shield_runes, key=count_enemies_in_range)
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
                'success': True, 'type': 'shield_pulse_fizzle_pull', 'pulled_points': pulled_points,
                'rune_points': all_rune_pids, 'pulse_center': rune_center, 'pulse_radius_sq': pulse_radius_sq
            }

    def impale(self, teamId):
        """[RUNE ACTION]: Fires a powerful, shield-piercing beam from a Trident Rune. If it misses, it creates a temporary barricade."""
        active_trident_runes = self.state.get('runes', {}).get(teamId, {}).get('trident', [])
        if not active_trident_runes:
            return {'success': False, 'reason': 'no active Trident Runes'}
            
        # Choose the trident closest to an enemy line
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        points = self.state['points']

        def get_trident_proximity(trident_rune):
            if not enemy_lines or trident_rune['apex_id'] not in points: return float('inf')
            p_apex = points[trident_rune['apex_id']]
            return min(distance_sq(p_apex, points_centroid([points[l['p1_id']], points[l['p2_id']]])) for l in enemy_lines if l['p1_id'] in points and l['p2_id'] in points)
            
        rune = min(active_trident_runes, key=get_trident_proximity)
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
        
        for line in enemy_lines:
            # This is a powerful rune action that pierces shields and bastions.
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

        # Choose the parallel rune with the largest area
        points = self.state['points']
        rune_p_ids_tuple = max(active_parallel_runes, key=lambda p_ids: polygon_area([points[pid] for pid in p_ids if pid in points]))
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

        # Choose the hourglass rune closest to an enemy
        points_map = self.state['points']
        enemy_points = self.game.query.get_vulnerable_enemy_points(teamId)
        def get_hourglass_proximity(hg_rune):
            if not enemy_points or hg_rune['vertex_id'] not in points_map: return float('inf')
            p_vertex = points_map[hg_rune['vertex_id']]
            return min(distance_sq(p_vertex, ep) for ep in enemy_points)
        
        rune = min(active_hourglass_runes, key=get_hourglass_proximity)
        points_map = self.state['points']
        
        rune_pids = rune['all_points']
        if not all(pid in points_map for pid in rune_pids):
            return {'success': False, 'reason': 'rune points no longer exist'}
        
        p_vertex = points_map[rune['vertex_id']]
        stasis_range_sq = (self.state['grid_size'] * 0.3)**2
        
        enemy_points = self.game.query.get_vulnerable_enemy_points(teamId)
        possible_targets = [ep for ep in enemy_points if distance_sq(p_vertex, ep) < stasis_range_sq]

        if possible_targets:
            # --- Primary Effect: Apply Stasis ---
            # Target the closest vulnerable enemy
            p_vertex = points_map[rune['vertex_id']]
            target_point = min(possible_targets, key=lambda p: distance_sq(p_vertex, p))
            self.state['stasis_points'][target_point['id']] = 3 # 3 turns
            target_team_name = self.state['teams'][target_point['teamId']]['name']
            return {
                'success': True, 'type': 'rune_hourglass_stasis',
                'target_point': target_point, 'rune_points': rune_pids, 'rune_vertex_id': rune['vertex_id'],
                'target_team_name': target_team_name
            }
        else:
            # --- Fallback Effect: Create Anchor ---
            # Degrade the rune by turning one of its non-vertex points into an anchor. No sacrifice.
            non_vertex_pids = [pid for pid in rune_pids if pid != rune['vertex_id'] and pid not in self.state.get('anchors', {})]
            if not non_vertex_pids:
                return {'success': False, 'reason': 'no valid rune points to convert to anchor'}
            
            # Convert the non-vertex point furthest from the vertex into an anchor
            p_vertex = points_map[rune['vertex_id']]
            p_to_anchor_id = max(non_vertex_pids, key=lambda pid: distance_sq(p_vertex, points_map[pid]))
            anchor_point = points_map.get(p_to_anchor_id)
            if not anchor_point:
                return {'success': False, 'reason': 'chosen anchor point for fallback does not exist'}

            self.state['anchors'][p_to_anchor_id] = {'teamId': teamId, 'turns_left': 3}

            return {
                'success': True, 'type': 'hourglass_fizzle_anchor',
                'anchor_point': anchor_point, 'rune_points': rune_pids
            }
    
    def focus_beam(self, teamId):
        """[RUNE ACTION]: A Star Rune fires a beam at a high-value target. If none, a regular one. If no targets, creates a fissure."""
        active_star_runes = self.state.get('runes', {}).get(teamId, {}).get('star', [])
        if not active_star_runes:
            return {'success': False, 'reason': 'no active Star Runes'}

        # Choose the star rune with the largest area
        points_map = self.state['points']
        rune = max(active_star_runes, key=lambda r: polygon_area([points_map[pid] for pid in r['cycle_ids'] if pid in points_map]))
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
            vulnerable_targets = self.game.query.get_vulnerable_enemy_points(teamId)
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

    def starlight_cascade(self, teamId):
        """[RUNE ACTION]: A Star Rune unleashes a cascade of energy, damaging or destroying nearby lines."""
        team_star_runes = self.state.get('runes', {}).get(teamId, {}).get('star', [])
        if not team_star_runes: return {'success': False, 'reason': 'no active star runes'}
        
        # Choose the star rune with the largest area
        points = self.state['points']
        rune = max(team_star_runes, key=lambda r: polygon_area([points[pid] for pid in r['cycle_ids'] if pid in points]))
        points = self.state['points']
        center_point = points.get(rune['center_id'])
        if not center_point: return {'success': False, 'reason': 'rune center point no longer exists'}
        
        blast_radius_sq = (self.state['grid_size'] * 0.25)**2
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        
        lines_to_destroy = []
        lines_to_damage = []

        for line in enemy_lines:
            if line.get('id') in self.state['shields']: continue
            if not (line['p1_id'] in points and line['p2_id'] in points): continue
            
            p1 = points[line['p1_id']]
            p2 = points[line['p2_id']]
            midpoint = points_centroid([p1, p2])

            if distance_sq(center_point, midpoint) < blast_radius_sq:
                line_strength = self.state.get('line_strengths', {}).get(line['id'], 0)
                if line_strength > 0:
                    lines_to_damage.append(line)
                else:
                    lines_to_destroy.append(line)
        
        if not lines_to_destroy and not lines_to_damage:
            return {
                'success': True, 'type': 'rune_starlight_cascade_fizzle',
                'rune_points': rune['all_points'], 'blast_center': center_point
            }

        for line in lines_to_destroy:
            self.game._delete_line(line)
        
        for line in lines_to_damage:
            self.state['line_strengths'][line['id']] -= 1
            if self.state['line_strengths'][line['id']] <= 0:
                del self.state['line_strengths'][line['id']]
            
        return {
            'success': True, 'type': 'rune_starlight_cascade',
            'destroyed_lines': lines_to_destroy, 'damaged_lines': lines_to_damage,
            'rune_points': rune['all_points'], 'blast_center': center_point
        }

    def gravity_well(self, teamId):
        """[RUNE ACTION]: Uses a Star Rune to push enemies away, or pull allies in."""
        active_star_runes = self.state.get('runes', {}).get(teamId, {}).get('star', [])
        if not active_star_runes:
            return {'success': False, 'reason': 'no active Star Runes'}

        # Choose the star rune closest to any non-friendly point
        points = self.state['points']
        non_friendly_points = [p for p in points.values() if p['teamId'] != teamId]

        def get_star_proximity(star_rune):
            if not non_friendly_points or star_rune['center_id'] not in points: return float('inf')
            center_point = points[star_rune['center_id']]
            return min(distance_sq(center_point, nfp) for nfp in non_friendly_points)
        
        rune = min(active_star_runes, key=get_star_proximity)
        points = self.state['points']
        center_point = points.get(rune['center_id'])
        if not center_point:
            return {'success': False, 'reason': 'rune center point no longer exists'}

        pulse_radius_sq = (self.state['grid_size'] * 0.4)**2
        grid_size = self.state['grid_size']

        # --- Find Primary Targets (Non-friendly points) ---
        non_friendly_points_in_range = [
            p for p in points.values() 
            if p['teamId'] != teamId and distance_sq(center_point, p) < pulse_radius_sq
        ]

        if non_friendly_points_in_range:
            # --- Primary Effect: Push Enemies ---
            pushed_points_count = 0
            push_distance = 3.0
            for point in non_friendly_points_in_range:
                dx, dy = point['x'] - center_point['x'], point['y'] - center_point['y']
                dist = math.sqrt(dx**2 + dy**2)
                if dist < 0.1: continue
                
                new_x = point['x'] + (dx / dist) * push_distance
                new_y = point['y'] + (dy / dist) * push_distance
                point['x'] = round(max(0, min(grid_size - 1, new_x)))
                point['y'] = round(max(0, min(grid_size - 1, new_y)))
                pushed_points_count += 1

            return {
                'success': True, 'type': 'rune_gravity_well_push', 'pushed_points_count': pushed_points_count,
                'rune_points': rune['all_points'], 'pulse_center': center_point, 'pulse_radius_sq': pulse_radius_sq
            }
        else:
            # --- Fallback Effect: Pull Allies ---
            pulled_points_count = 0
            pull_distance = 1.5
            # Find friendly points inside the pulse radius (but not part of the rune itself)
            for point in [p for p in points.values() if p['teamId'] == teamId and p['id'] not in rune['all_points']]:
                if distance_sq(center_point, p) < pulse_radius_sq:
                    dx, dy = center_point['x'] - point['x'], center_point['y'] - point['y']
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist < 0.1: continue
                    
                    new_x = point['x'] + (dx / dist) * pull_distance
                    new_y = point['y'] + (dy / dist) * pull_distance
                    point['x'] = round(max(0, min(grid_size - 1, new_x)))
                    point['y'] = round(max(0, min(grid_size - 1, new_y)))
                    pulled_points_count += 1
            
            return {
                'success': True, 'type': 'gravity_well_fizzle_pull', 'pulled_points_count': pulled_points_count,
                'rune_points': rune['all_points'], 'pulse_center': center_point, 'pulse_radius_sq': pulse_radius_sq
            }

    def t_hammer_slam(self, teamId):
        """[RUNE ACTION]: A T-Rune creates a perpendicular shockwave from its stem."""
        team_t_runes = self.state.get('runes', {}).get(teamId, {}).get('t_shape', [])
        if not team_t_runes: return {'success': False, 'reason': 'no active T-runes'}
        
        # Choose the T-Rune closest to the most points (friend or foe)
        points = self.state['points']
        def count_points_in_range(t_rune):
            p_mid = points.get(t_rune['mid_id'])
            if not p_mid: return 0
            push_radius_sq = (self.state['grid_size'] * 0.2)**2
            return sum(1 for p in points.values() if p['id'] not in t_rune['all_points'] and distance_sq(p, p_mid) < push_radius_sq)
        
        rune = max(team_t_runes, key=count_points_in_range)
        points = self.state['points']
        if not all(pid in points for pid in rune['all_points']): return {'success': False, 'reason': 'rune points no longer exist'}
        
        p_mid = points[rune['mid_id']]
        p_stem1 = points[rune['stem1_id']]
        p_stem2 = points[rune['stem2_id']]

        # Push logic
        push_radius_sq = (self.state['grid_size'] * 0.2)**2
        # We can push any point, including friendly ones, that are not part of the rune itself.
        points_to_check = [p for p in points.values() if p['id'] not in rune['all_points']]
        pushed_points = []
        
        stem_vx, stem_vy = p_stem2['x'] - p_stem1['x'], p_stem2['y'] - p_stem1['y']
        mag_stem_sq = stem_vx**2 + stem_vy**2

        if mag_stem_sq > 0.1:
            for p in points_to_check:
                # Check if point is near the stem
                if distance_sq(p, p_mid) > push_radius_sq: continue

                # project p onto stem line
                dot = (p['x'] - p_stem1['x']) * stem_vx + (p['y'] - p_stem1['y']) * stem_vy
                t = dot / mag_stem_sq
                if 0 <= t <= 1: # check if projection is on segment
                    proj_x = p_stem1['x'] + t * stem_vx
                    proj_y = p_stem1['y'] + t * stem_vy
                    
                    # Push perpendicularly
                    push_vx, push_vy = p['x'] - proj_x, p['y'] - proj_y
                    mag_push = math.sqrt(push_vx**2 + push_vy**2)
                    if mag_push < 0.1: continue

                    new_x = p['x'] + (push_vx/mag_push) * 2.0
                    new_y = p['y'] + (push_vy/mag_push) * 2.0
                    
                    new_coords = clamp_and_round_point_coords({'x': new_x, 'y': new_y}, self.state['grid_size'])
                    p['x'], p['y'] = new_coords['x'], new_coords['y']
                    pushed_points.append(p)
                    
        if pushed_points:
            return {
                'success': True, 'type': 'rune_t_hammer_slam',
                'pushed_points_count': len(pushed_points),
                'rune_points': rune['all_points']
            }
        else:
            # Fallback: Reinforce the stem lines
            strengthened = []
            all_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.game.query.get_team_lines(teamId)}
            key1 = tuple(sorted((rune['mid_id'], rune['stem1_id'])))
            key2 = tuple(sorted((rune['mid_id'], rune['stem2_id'])))
            
            if key1 in all_lines_by_points and self.game._strengthen_line(all_lines_by_points[key1]):
                strengthened.append(all_lines_by_points[key1])
            if key2 in all_lines_by_points and self.game._strengthen_line(all_lines_by_points[key2]):
                strengthened.append(all_lines_by_points[key2])

            return {
                'success': True, 'type': 't_slam_fizzle_reinforce',
                'strengthened_lines': strengthened, 'rune_points': rune['all_points']
            }

    def cardinal_pulse(self, teamId):
        """[RUNE ACTION]: Fires four beams from a Plus-Rune's center."""
        team_plus_runes = self.state.get('runes', {}).get(teamId, {}).get('plus_shape', [])
        if not team_plus_runes: return {'success': False, 'reason': 'no active plus runes'}
        
        # Choose the Plus-Rune closest to an enemy
        points = self.state['points']
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        if not enemy_lines: # Fallback if no enemy lines
            rune = team_plus_runes[0]
        else:
            def get_plus_proximity(plus_rune):
                if plus_rune['center_id'] not in points: return float('inf')
                center_p = points[plus_rune['center_id']]
                return min(distance_sq(center_p, points_centroid([points[l['p1_id']], points[l['p2_id']]])) for l in enemy_lines if l['p1_id'] in points and l['p2_id'] in points)
            
            rune = min(team_plus_runes, key=get_plus_proximity)
        points = self.state['points']
        if not all(pid in points for pid in rune['all_points']): return {'success': False, 'reason': 'rune points no longer exist'}
            
        p_center = points[rune['center_id']]
        
        # --- Fire beams ---
        destroyed_lines = []
        created_points = []
        attack_rays = []
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        bastion_line_ids = self.game.query.get_bastion_line_ids()
        
        for arm_id in rune['arm_ids']:
            arm_point = points.get(arm_id)
            if not arm_point: continue

            border_point = get_extended_border_point(p_center, arm_point, self.state['grid_size'],
                self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', []))
            if not border_point: continue
            
            attack_ray_p1, attack_ray_p2 = p_center, border_point
            
            closest_hit = None
            min_dist_sq = float('inf')
            current_points_map = self.state['points'] # Use current points map
            for enemy_line in enemy_lines:
                if enemy_line.get('id') in bastion_line_ids: continue
                if enemy_line['p1_id'] not in current_points_map or enemy_line['p2_id'] not in current_points_map: continue
                
                ep1, ep2 = current_points_map[enemy_line['p1_id']], current_points_map[enemy_line['p2_id']]
                intersection_point = get_segment_intersection_point(attack_ray_p1, attack_ray_p2, ep1, ep2)
                if intersection_point:
                    dist_sq = distance_sq(attack_ray_p1, intersection_point)
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        closest_hit = {'target_line': enemy_line, 'intersection_point': intersection_point}
            
            if closest_hit and closest_hit['target_line'] not in destroyed_lines:
                self.game._delete_line(closest_hit['target_line'])
                destroyed_lines.append(closest_hit['target_line'])
                attack_rays.append({'p1': attack_ray_p1, 'p2': closest_hit['intersection_point']})
                enemy_lines.remove(closest_hit['target_line'])
            else:
                new_point = self.game._helper_spawn_on_border(teamId, border_point)
                if new_point:
                    created_points.append(new_point)
                    attack_rays.append({'p1': attack_ray_p1, 'p2': border_point})
                    
        return {
            'success': True, 'type': 'rune_cardinal_pulse',
            'lines_destroyed': destroyed_lines, 'points_created': created_points,
            'attack_rays': attack_rays, 'rune_points': rune['all_points']
        }

    def raise_barricade(self, teamId):
        """[RUNE ACTION]: Creates a temporary wall from a Barricade-Rune without consuming it."""
        team_barricade_runes = self.state.get('runes', {}).get(teamId, {}).get('barricade', [])
        if not team_barricade_runes:
            return {'success': False, 'reason': 'no active barricade runes'}

        # Choose the largest barricade rune by area
        points_map = self.state['points']
        rune_p_ids_tuple = max(team_barricade_runes, key=lambda p_ids: polygon_area([points_map[pid] for pid in p_ids]))
        points_map = self.state['points']

        if not all(pid in points_map for pid in rune_p_ids_tuple):
            return {'success': False, 'reason': 'rune points no longer exist'}
        
        p_list = [points_map[pid] for pid in rune_p_ids_tuple]
        
        # Determine the barricade path along one of the rune's diagonals.
        edge_data = get_edges_by_distance(p_list)
        diag_pairs = edge_data.get('diagonals', [])
        
        if not diag_pairs:
             return {
                 'success': True, 'type': 'raise_barricade_fizzle', 'rune_points': rune_p_ids_tuple
            }
            
        diag_to_use = random.choice(diag_pairs)
        p1 = points_map.get(diag_to_use[0])
        p2 = points_map.get(diag_to_use[1])

        if not p1 or not p2:
             return {
                 'success': True, 'type': 'raise_barricade_fizzle', 'rune_points': rune_p_ids_tuple
            }

        # --- Create the barricade ---
        new_barricade = self.game._create_temporary_barricade(teamId, p1, p2, 5) # 5-turn duration

        return {
            'success': True,
            'type': 'raise_barricade',
            'barricade': new_barricade,
            'rune_points': rune_p_ids_tuple,
        }