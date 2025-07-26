import random
import math
from itertools import combinations
from ..geometry import (
    distance_sq, segments_intersect, get_segment_intersection_point,
    get_extended_border_point, is_ray_blocked,
    polygon_area, points_centroid, clamp_and_round_point_coords,
    get_angle_bisector_vector, get_convex_hull, is_point_in_polygon
)

class FightActionsHandler:
    def __init__(self, game):
        self.game = game

    # --- Action Precondition Checks ---

    def can_perform_attack_line(self, teamId):
        return len(self.game.get_team_lines(teamId)) > 0, "Requires at least 1 line to attack from."

    def can_perform_pincer_attack(self, teamId):
        return len(self.game.get_team_point_ids(teamId)) >= 2, "Requires at least 2 points."

    def can_perform_territory_strike(self, teamId):
        return len(self._get_large_territories(teamId)) > 0, "No large territories available."

    def can_perform_territory_bisector_strike(self, teamId):
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        return len(team_territories) > 0, "No claimed territories available."

    def can_perform_sentry_zap(self, teamId):
        team_i_runes = self.state.get('runes', {}).get(teamId, {}).get('i_shape', [])
        can_perform = any(r.get('internal_points') for r in team_i_runes)
        return can_perform, "Requires an I-Rune with at least 3 points."

    def can_perform_refraction_beam(self, teamId):
        has_prism = bool(self.state.get('runes', {}).get(teamId, {}).get('prism', []))
        num_enemy_lines = len(self.state['lines']) - len(self.game.get_team_lines(teamId))
        can_perform = has_prism and num_enemy_lines > 0
        return can_perform, "Requires a Prism Rune and enemy lines."

    def can_perform_launch_payload(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('trebuchet', []))
        return can_perform, "Requires a Trebuchet Rune."

    def can_perform_purify_territory(self, teamId):
        # Action is possible if a purifier exists, due to the fallback push effect.
        can_perform = bool(self.state.get('purifiers', {}).get(teamId, []))
        return can_perform, "Requires a Purifier."

    def can_perform_isolate_point(self, teamId):
        # With push/barricade fallbacks, action is always possible if team has at least one point.
        can_perform = len(self.game.get_team_point_ids(teamId)) >= 1
        reason = "" if can_perform else "Requires at least one point to act."
        return can_perform, reason

    def can_perform_parallel_strike(self, teamId):
        team_lines = self.game.get_team_lines(teamId)
        team_point_ids = self.game.get_team_point_ids(teamId)
        
        if not team_lines or not team_point_ids:
            return False, "Requires at least one point and one line."

        # Since the action can create a point if it misses, we don't need to check for enemy points.
        # We just need to check if a valid geometric setup exists: a point and a line it is not part of.
        for p_id in team_point_ids:
            for line in team_lines:
                if p_id != line['p1_id'] and p_id != line['p2_id']:
                    return True, "" # Found a valid combination, so action is possible.
        
        return False, "No valid point/line combination found for a parallel strike."

    def can_perform_hull_breach(self, teamId):
        # With the push fallback, action is always possible if team has at least 3 points.
        return len(self.game.get_team_point_ids(teamId)) >= 3, "Requires at least 3 points to form a hull."

    # --- End Precondition Checks ---

    @property
    def state(self):
        """Provides direct access to the game's current state dictionary."""
        return self.game.state

    def _find_closest_attack_hit(self, attack_segment_p1, attack_segment_p2, enemy_lines, team_has_cross_rune, bastion_line_ids):
        points = self.state['points']
        closest_hit = None
        min_dist_sq = float('inf')

        for enemy_line in enemy_lines:
            is_shielded = enemy_line.get('id') in self.state['shields']
            if is_shielded and not team_has_cross_rune:
                continue
            
            if enemy_line.get('id') in bastion_line_ids:
                continue
            
            if enemy_line['p1_id'] not in points or enemy_line['p2_id'] not in points: continue
            ep1 = points[enemy_line['p1_id']]
            ep2 = points[enemy_line['p2_id']]

            intersection_point = get_segment_intersection_point(attack_segment_p1, attack_segment_p2, ep1, ep2)
            if intersection_point:
                dist_sq = distance_sq(attack_segment_p1, intersection_point)
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_hit = {
                        'target_line': enemy_line,
                        'intersection_point': intersection_point,
                        'bypassed_shield': is_shielded and team_has_cross_rune
                    }
        return closest_hit

    def _handle_attack_hit(self, closest_hit, attacker_line, attack_segment_p1):
        enemy_line = closest_hit['target_line']
        is_energized_attack = self.game._is_line_energized(attacker_line)

        line_strength = self.state.get('line_strengths', {}).get(enemy_line['id'])
        if line_strength and line_strength > 0:
            self.state['line_strengths'][enemy_line['id']] -= 1
            if self.state['line_strengths'][enemy_line['id']] <= 0:
                del self.state['line_strengths'][enemy_line['id']]
            return {
                'success': True, 'type': 'attack_line_strengthened',
                'damaged_line': enemy_line, 'attacker_line': attacker_line,
                'attack_ray': {'p1': attack_segment_p1, 'p2': closest_hit['intersection_point']},
                'intersection_point': closest_hit['intersection_point']
            }

        enemy_team_name = self.state['teams'][enemy_line['teamId']]['name']
        self.game._delete_line(enemy_line)

        destroyed_points_data = []
        if is_energized_attack:
            aggressor_team_id = attacker_line['teamId']
            p1_data = self.game._delete_point_and_connections(enemy_line['p1_id'], aggressor_team_id)
            if p1_data: destroyed_points_data.append(p1_data)
            p2_data = self.game._delete_point_and_connections(enemy_line['p2_id'], aggressor_team_id)
            if p2_data: destroyed_points_data.append(p2_data)

        return {
            'success': True, 
            'type': 'attack_line_energized' if is_energized_attack else 'attack_line',
            'destroyed_team': enemy_team_name, 
            'destroyed_line': enemy_line,
            'destroyed_points': destroyed_points_data,
            'attacker_line': attacker_line, 
            'attack_ray': {'p1': attack_segment_p1, 'p2': closest_hit['intersection_point']},
            'bypassed_shield': closest_hit['bypassed_shield']
        }

    def _handle_attack_miss(self, teamId, border_point, attacker_line, attack_segment_p1):
        new_point = self.game._helper_spawn_on_border(teamId, border_point)
        if new_point:
            return {
                'success': True, 'type': 'attack_miss_spawn', 'new_point': new_point,
                'attacker_line': attacker_line, 'attack_ray': {'p1': attack_segment_p1, 'p2': border_point}
            }
        return None

    def attack_line(self, teamId):
        """[FIGHT ACTION]: Extend a line to hit an enemy line. If it misses, it creates a new point on the border."""
        team_lines = self.game.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to attack from'}
        
        points = self.state['points']
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        team_has_cross_rune = len(self.state.get('runes', {}).get(teamId, {}).get('cross', [])) > 0
        bastion_line_ids = self.game._get_bastion_line_ids()
        
        random.shuffle(team_lines)
        for line in team_lines:
            if line['p1_id'] not in points or line['p2_id'] not in points: continue
            
            p1 = points[line['p1_id']]
            p2 = points[line['p2_id']]
            
            p_start, p_end = random.choice([(p1, p2), (p2, p1)])
            border_point = get_extended_border_point(
                p_start, p_end, self.state['grid_size'],
                self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])
            )
            if not border_point: continue

            attack_segment_p1 = p_end
            attack_segment_p2 = border_point

            if is_ray_blocked(attack_segment_p1, attack_segment_p2, self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])):
                continue

            closest_hit = self._find_closest_attack_hit(attack_segment_p1, attack_segment_p2, enemy_lines, team_has_cross_rune, bastion_line_ids)
            
            if closest_hit:
                return self._handle_attack_hit(closest_hit, line, attack_segment_p1)
            else:
                result = self._handle_attack_miss(teamId, border_point, line, attack_segment_p1)
                if result:
                    return result
        
        return {'success': False, 'reason': 'no valid attack or spawn opportunity found'}

    def _pincer_attack_fallback_barricade(self, teamId, p1_id, p2_id):
        points = self.state['points']
        p1 = points.get(p1_id)
        p2 = points.get(p2_id)

        if not p1 or not p2:
            return {'success': False, 'reason': 'points for fallback barricade do not exist'}
        
        new_barricade = self.game._create_temporary_barricade(teamId, p1, p2, 2)
        return {
            'success': True, 'type': 'pincer_fizzle_barricade',
            'barricade': new_barricade, 'pincer_points': [p1_id, p2_id]
        }

    def pincer_attack(self, teamId):
        """[FIGHT ACTION]: Two points flank and destroy an enemy point. If not possible, they form a defensive barricade."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 2:
            return {'success': False, 'reason': 'not enough points for pincer attack'}

        enemy_points = self.game._get_vulnerable_enemy_points(teamId)

        points_map = self.state['points']
        max_range_sq = (self.state['grid_size'] * 0.4)**2
        pincer_angle_threshold = -0.866  # cos(150 deg)
        
        pincer_candidates = list(combinations(team_point_ids, 2))
        random.shuffle(pincer_candidates)
        for p1_id, p2_id in pincer_candidates[:10]:
            p1 = points_map[p1_id]
            p2 = points_map[p2_id]
            
            possible_targets = []
            for ep in enemy_points:
                if distance_sq(p1, ep) > max_range_sq or distance_sq(p2, ep) > max_range_sq:
                    continue
                v1 = {'x': p1['x'] - ep['x'], 'y': p1['y'] - ep['y']}
                v2 = {'x': p2['x'] - ep['x'], 'y': p2['y'] - ep['y']}
                mag1_sq, mag2_sq = v1['x']**2 + v1['y']**2, v2['x']**2 + v2['y']**2
                if mag1_sq < 0.1 or mag2_sq < 0.1: continue
                dot_product = v1['x'] * v2['x'] + v1['y'] * v2['y']
                cos_theta = dot_product / (math.sqrt(mag1_sq) * math.sqrt(mag2_sq))
                if cos_theta < pincer_angle_threshold:
                    possible_targets.append(ep)

            if possible_targets:
                midpoint = points_centroid([p1, p2])
                target_point = min(possible_targets, key=lambda p: distance_sq(midpoint, p))
                destroyed_point_data = self.game._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
                if not destroyed_point_data: continue
                destroyed_team_name = self.state['teams'][destroyed_point_data['teamId']]['name']
                return {
                    'success': True, 'type': 'pincer_attack', 'destroyed_point': destroyed_point_data,
                    'attacker_p1_id': p1_id, 'attacker_p2_id': p2_id, 'destroyed_team_name': destroyed_team_name
                }
        
        # --- Fallback: Create Barricade ---
        # This block is reached if no targets were found in the loop or if there were no enemies to begin with.
        p1_id, p2_id = random.sample(team_point_ids, 2)
        return self._pincer_attack_fallback_barricade(teamId, p1_id, p2_id)

    def _get_large_territories(self, teamId):
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        if not team_territories: return []
        points_map = self.state['points']
        MIN_AREA = 10.0
        large_territories = []
        for territory in team_territories:
            p_ids = territory['point_ids']
            if all(pid in points_map for pid in p_ids):
                triangle_points = [points_map[pid] for pid in p_ids]
                if len(triangle_points) == 3 and polygon_area(triangle_points) >= MIN_AREA:
                    large_territories.append(territory)
        return large_territories

    def territory_strike(self, teamId):
        """[FIGHT ACTION]: Launches an attack from a large territory. If no targets, reinforces the territory."""
        large_territories = self._get_large_territories(teamId)
        if not large_territories:
            return {'success': False, 'reason': 'no large territories to strike from'}

        territory = random.choice(large_territories)
        points_map = self.state['points']
        if not all(pid in points_map for pid in territory['point_ids']):
            return {'success': False, 'reason': 'territory points no longer exist'}
        
        triangle_points = [points_map[pid] for pid in territory['point_ids']]
        centroid = points_centroid(triangle_points)

        enemy_points = self.game._get_vulnerable_enemy_points(teamId)
        if enemy_points:
            target_point = min(enemy_points, key=lambda p: distance_sq(centroid, p))
            destroyed_point_data = self.game._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
            if not destroyed_point_data:
                 return {'success': False, 'reason': 'failed to destroy target point'}
            destroyed_team_name = self.state['teams'][destroyed_point_data['teamId']]['name']
            return {
                'success': True, 'type': 'territory_strike', 'destroyed_point': destroyed_point_data,
                'territory_point_ids': territory['point_ids'], 'attack_ray': {'p1': centroid, 'p2': target_point},
                'destroyed_team_name': destroyed_team_name
            }
        else:
            strengthened_lines = self.game._reinforce_territory_boundaries(territory)
            return {
                'success': True, 'type': 'territory_fizzle_reinforce',
                'territory_point_ids': territory['point_ids'], 'strengthened_lines': strengthened_lines
            }

    def _sentry_zap_fallback_strengthen(self, teamId, rune):
        strengthened_lines = []
        all_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.game.get_team_lines(teamId)}
        for i in range(len(rune['point_ids']) - 1):
            p1_id, p2_id = rune['point_ids'][i], rune['point_ids'][i+1]
            line_key = tuple(sorted((p1_id, p2_id)))
            if line_key in all_lines_by_points:
                line_to_strengthen = all_lines_by_points[line_key]
                if self.game._strengthen_line(line_to_strengthen):
                    strengthened_lines.append(line_to_strengthen)
        return {
            'success': True,
            'type': 'sentry_zap_fizzle_strengthen',
            'strengthened_lines': strengthened_lines,
            'rune_points': rune['point_ids']
        }

    def _refraction_beam_fallback_strengthen(self, teamId, prism):
        all_prism_pids = prism['all_point_ids']
        strengthened_lines = []
        all_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.game.get_team_lines(teamId)}

        # A prism is two triangles sharing an edge. Total 4 points.
        # This will try to strengthen any of the 5 outer lines plus the shared inner line if they exist.
        for p1_id, p2_id in combinations(all_prism_pids, 2):
            line_key = tuple(sorted((p1_id, p2_id)))
            if line_key in all_lines_by_points:
                line_to_strengthen = all_lines_by_points[line_key]
                if self.game._strengthen_line(line_to_strengthen):
                    strengthened_lines.append(line_to_strengthen)
        
        return {
            'success': True,
            'type': 'refraction_fizzle_strengthen',
            'strengthened_lines': strengthened_lines,
            'prism_point_ids': all_prism_pids
        }

    def territory_bisector_strike(self, teamId):
        """[FIGHT ACTION]: A claimed territory fires three beams along its angle bisectors."""
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        if not team_territories:
            return {'success': False, 'reason': 'no territories to strike from'}

        territory = random.choice(team_territories)
        points_map = self.state['points']
        p_ids = territory['point_ids']
        if not all(pid in points_map for pid in p_ids):
            return {'success': False, 'reason': 'territory points no longer exist'}
        
        p1, p2, p3 = points_map[p_ids[0]], points_map[p_ids[1]], points_map[p_ids[2]]
        vertices = [(p1, p2, p3), (p2, p1, p3), (p3, p1, p2)]

        destroyed_lines = []
        created_points = []
        attack_rays = []
        
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        team_has_cross_rune = len(self.state.get('runes', {}).get(teamId, {}).get('cross', [])) > 0
        bastion_line_ids = self.game._get_bastion_line_ids()

        for p_vertex, p_leg1, p_leg2 in vertices:
            bisector_v = get_angle_bisector_vector(p_vertex, p_leg1, p_leg2)
            if not bisector_v:
                continue

            dummy_end_point = {'x': p_vertex['x'] + bisector_v['x'], 'y': p_vertex['y'] + bisector_v['y']}
            border_point = get_extended_border_point(
                p_vertex, dummy_end_point, self.state['grid_size'],
                self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])
            )
            if not border_point:
                continue
            
            attack_ray_p1 = p_vertex
            attack_ray_p2 = border_point

            closest_hit = self._find_closest_attack_hit(attack_ray_p1, attack_ray_p2, enemy_lines, team_has_cross_rune, bastion_line_ids)

            if closest_hit:
                # To prevent destroying the same line twice.
                if closest_hit['target_line'] in destroyed_lines:
                    continue

                self.game._delete_line(closest_hit['target_line'])
                destroyed_lines.append(closest_hit['target_line'])
                attack_rays.append({'p1': attack_ray_p1, 'p2': closest_hit['intersection_point']})
                # After destroying a line, it's no longer an enemy line for subsequent beams.
                enemy_lines.remove(closest_hit['target_line'])
            else:
                new_point = self.game._helper_spawn_on_border(teamId, border_point)
                if new_point:
                    created_points.append(new_point)
                    attack_rays.append({'p1': attack_ray_p1, 'p2': border_point})

        if not destroyed_lines and not created_points:
            # Fallback: Reinforce the territory's boundaries
            strengthened_lines = self.game._reinforce_territory_boundaries(territory)
            return {
                'success': True,
                'type': 'territory_bisector_strike_fizzle',
                'territory_point_ids': territory['point_ids'],
                'strengthened_lines': strengthened_lines,
                'reason': 'all beams were blocked, reinforcing instead'
            }

        return {
            'success': True,
            'type': 'territory_bisector_strike',
            'territory_point_ids': territory['point_ids'],
            'destroyed_lines': destroyed_lines,
            'created_points': created_points,
            'attack_rays': attack_rays
        }

    def launch_payload(self, teamId):
        """[FIGHT ACTION]: A Trebuchet launches a payload. Prioritizes high-value points, then any enemy, and finally creates a fissure if no targets exist."""
        team_trebuchets = self.state.get('runes', {}).get(teamId, {}).get('trebuchet', [])
        if not team_trebuchets:
            return {'success': False, 'reason': 'no active Trebuchet Runes'}

        trebuchet = random.choice(team_trebuchets)
        if not all(pid in self.state['points'] for pid in trebuchet.get('point_ids', [])):
             return {'success': False, 'reason': 'trebuchet points no longer exist'}

        # --- Target Prioritization ---
        target_point = None

        # 1. High-value targets
        all_enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId]
        stasis_point_ids = set(self.state.get('stasis_points', {}).keys())
        # We still need the components of immunity to define "high-value"
        fortified_ids = self.game._get_fortified_point_ids()
        bastion_cores = self.game._get_bastion_point_ids()['cores']
        monolith_point_ids = {pid for m in self.state.get('monoliths', {}).values() for pid in m['point_ids']}

        high_value_targets = [
            p for p in all_enemy_points if
            p['id'] not in stasis_point_ids and (
                p['id'] in fortified_ids or
                p['id'] in bastion_cores or
                p['id'] in monolith_point_ids
            )
        ]
        
        if high_value_targets:
            target_point = random.choice(high_value_targets)
        else:
            # 2. Any vulnerable enemy target
            # Use the new helper to get all immune points.
            immune_point_ids = self.game._get_all_immune_point_ids()
            vulnerable_targets = self.game._get_vulnerable_enemy_points(teamId, immune_point_ids=immune_point_ids)
            if vulnerable_targets:
                target_point = random.choice(vulnerable_targets)
        
        # --- Execute Action ---
        if target_point:
            # --- Primary or Secondary Effect: Destroy Point ---
            destroyed_point_data = self.game._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
            if not destroyed_point_data:
                return {'success': False, 'reason': 'failed to destroy target point'}
            
            # Determine if the target was high-value for logging/visuals
            is_high_value = (destroyed_point_data['id'] in fortified_ids or
                            destroyed_point_data['id'] in bastion_cores or
                            destroyed_point_data['id'] in monolith_point_ids)

            destroyed_team_name = self.state['teams'][destroyed_point_data['teamId']]['name']
            return {
                'success': True,
                'type': 'launch_payload' if is_high_value else 'launch_payload_fallback_hit',
                'trebuchet_points': trebuchet['point_ids'],
                'launch_point_id': trebuchet['apex_id'],
                'destroyed_point': destroyed_point_data,
                'destroyed_team_name': destroyed_team_name
            }
        else:
            # --- Fallback Effect: Create Fissure ---
            grid_size = self.state['grid_size']
            fissure_len = grid_size * 0.3
            
            # Create fissure at a random location
            center_x = random.uniform(fissure_len, grid_size - fissure_len)
            center_y = random.uniform(fissure_len, grid_size - fissure_len)
            center_coords = {'x': center_x, 'y': center_y}
            
            new_fissure = self.game._create_random_fissure(center_coords, fissure_len, 3)

            return {
                'success': True,
                'type': 'launch_payload_fizzle_fissure',
                'fissure': new_fissure,
                'trebuchet_points': trebuchet['point_ids'],
                'launch_point_id': trebuchet['apex_id'],
                'impact_site': center_coords
            }

    def sentry_zap(self, teamId):
        """[FIGHT ACTION]: An I-Rune fires a beam to destroy an enemy point. If it misses, it creates a new point on the border."""
        team_i_runes = self.state.get('runes', {}).get(teamId, {}).get('i_shape', [])
        # A Sentry Zap requires an internal point to shoot from.
        possible_zaps = [r for r in team_i_runes if r.get('internal_points')]
        if not possible_zaps:
            return {'success': False, 'reason': 'no I-Runes with an internal point to fire from'}

        rune = random.choice(possible_zaps)
        points = self.state['points']
        
        # Pick a random internal point as the 'eye'
        eye_id = random.choice(rune['internal_points'])
        eye_index = rune['point_ids'].index(eye_id)
        
        # Posts are its direct neighbors in the line
        post1_id = rune['point_ids'][eye_index - 1]
        post2_id = rune['point_ids'][eye_index + 1]

        p_eye = points.get(eye_id)
        p_post1 = points.get(post1_id)
        p_post2 = points.get(post2_id)

        if not all([p_eye, p_post1, p_post2]):
            return {'success': False, 'reason': 'I-Rune points no longer exist'}
        
        # Vector of the I-Rune's alignment. Use posts relative to eye to find it.
        # This is more robust than assuming p_post1 and p_post2 are opposite.
        vx = p_post1['x'] - p_eye['x']
        vy = p_post1['y'] - p_eye['y']
        
        # Perpendicular vector (for the zap), randomized direction
        zap_vx, zap_vy = random.choice([(-vy, vx), (vy, -vx)])
        
        zap_range_sq = (self.state['grid_size'] * 0.35)**2
        
        # Get list of vulnerable enemy points
        stasis_point_ids = set(self.state.get('stasis_points', {}).keys())
        vulnerable_enemy_points = [p for p in points.values() if p['teamId'] != teamId and p['id'] not in stasis_point_ids]
        
        possible_targets = []
        if vulnerable_enemy_points:
            for enemy_p in vulnerable_enemy_points:
                enemy_vx = enemy_p['x'] - p_eye['x']
                enemy_vy = enemy_p['y'] - p_eye['y']
                
                if (enemy_vx**2 + enemy_vy**2) > zap_range_sq:
                    continue

                cross_product = zap_vx * enemy_vy - zap_vy * enemy_vx
                dot_product = zap_vx * enemy_vx + zap_vy * enemy_vy
                mag_zap_dir_sq = zap_vx**2 + zap_vy**2
                if mag_zap_dir_sq == 0: continue
                
                distance_from_ray_sq = cross_product**2 / mag_zap_dir_sq
                
                if distance_from_ray_sq < 0.5**2 and dot_product > 0:
                    possible_targets.append(enemy_p)

        if possible_targets:
            # --- Primary Effect: Destroy Point ---
            target_point = min(possible_targets, key=lambda p: distance_sq(p_eye, p))
            destroyed_point_data = self.game._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
            if not destroyed_point_data:
                return {'success': False, 'reason': 'failed to destroy target point'}
            
            zap_ray_end = get_extended_border_point(
                p_eye, target_point, self.state['grid_size'],
                self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])
            ) or target_point
            destroyed_team_name = self.state['teams'][destroyed_point_data['teamId']]['name']
            
            return {
                'success': True, 'type': 'sentry_zap',
                'destroyed_point': destroyed_point_data,
                'rune_points': rune['point_ids'],
                'attack_ray': {'p1': p_eye, 'p2': zap_ray_end},
                'destroyed_team_name': destroyed_team_name
            }
        else:
            # --- Fallback Effect: Spawn Point on Border ---
            # Create a dummy point along the zap vector to find the border intersection
            dummy_end_point = {'x': p_eye['x'] + zap_vx, 'y': p_eye['y'] + zap_vy}
            border_point = get_extended_border_point(
                p_eye, dummy_end_point, self.state['grid_size'],
                self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])
            )
            
            if not border_point or is_ray_blocked(p_eye, border_point, self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])):
                 return self._sentry_zap_fallback_strengthen(teamId, rune)

            new_point = self.game._helper_spawn_on_border(teamId, border_point)
            if not new_point:
                return self._sentry_zap_fallback_strengthen(teamId, rune)
            
            return {
                'success': True, 'type': 'sentry_zap_miss_spawn',
                'new_point': new_point,
                'rune_points': rune['point_ids'],
                'attack_ray': {'p1': p_eye, 'p2': border_point}
            }

    def refraction_beam(self, teamId):
        """[FIGHT ACTION]: Uses a Prism to refract an attack beam. If it misses, it creates a new point on the border."""
        team_prisms = self.state.get('runes', {}).get(teamId, {}).get('prism', [])
        if not team_prisms:
            return {'success': False, 'reason': 'no active Prism Runes'}
        
        points = self.state['points']
        
        prism_point_ids = {pid for p in team_prisms for pid in p['all_point_ids']}
        source_lines = [l for l in self.game.get_team_lines(teamId) if l['p1_id'] not in prism_point_ids and l['p2_id'] not in prism_point_ids]
        if not source_lines:
            return {'success': False, 'reason': 'no valid source lines for refraction'}

        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        
        potential_outcomes = []

        # Try a few combinations of prisms and source lines
        for _ in range(10):
            prism = random.choice(team_prisms)
            source_line = random.choice(source_lines)

            if source_line['p1_id'] not in points or source_line['p2_id'] not in points: continue
            
            ls1, ls2 = random.choice([(points[source_line['p1_id']], points[source_line['p2_id']]), (points[source_line['p2_id']], points[source_line['p1_id']])])
            
            source_ray_end = get_extended_border_point(
                ls1, ls2, self.state['grid_size'],
                self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])
            )
            if not source_ray_end: continue
            source_ray = {'p1': ls2, 'p2': source_ray_end}

            if prism['shared_p1_id'] not in points or prism['shared_p2_id'] not in points: continue
            prism_edge_p1 = points[prism['shared_p1_id']]
            prism_edge_p2 = points[prism['shared_p2_id']]

            intersection_point = get_segment_intersection_point(source_ray['p1'], source_ray['p2'], prism_edge_p1, prism_edge_p2)
            if not intersection_point: continue

            edge_vx = prism_edge_p2['x'] - prism_edge_p1['x']
            edge_vy = prism_edge_p2['y'] - prism_edge_p1['y']
            
            perp_vectors = [(-edge_vy, edge_vx), (edge_vy, -edge_vx)]

            for pvx, pvy in perp_vectors:
                mag = math.sqrt(pvx**2 + pvy**2)
                if mag == 0: continue
                
                refracted_end_dummy = {'x': intersection_point['x'] + pvx/mag, 'y': intersection_point['y'] + pvy/mag}
                refracted_ray_end = get_extended_border_point(
                    intersection_point, refracted_end_dummy, self.state['grid_size'],
                    self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])
                )
                if not refracted_ray_end: continue
                
                refracted_ray = {'p1': intersection_point, 'p2': refracted_ray_end}

                # Check this ray for hits
                hit_found = False
                if enemy_lines:
                    bastion_line_ids = self.game._get_bastion_line_ids()
                    for enemy_line in enemy_lines:
                        if enemy_line.get('id') in bastion_line_ids: continue
                        if enemy_line['p1_id'] not in points or enemy_line['p2_id'] not in points: continue
                        ep1, ep2 = points[enemy_line['p1_id']], points[enemy_line['p2_id']]

                        if segments_intersect(refracted_ray['p1'], refracted_ray['p2'], ep1, ep2):
                            potential_outcomes.append({
                                'type': 'hit', 'enemy_line': enemy_line, 'source_ray': source_ray,
                                'refracted_ray': refracted_ray, 'prism': prism
                            })
                            hit_found = True
                            break # Found a hit for this refracted ray
                
                if not hit_found:
                    # If no hit, this is a potential miss outcome
                    potential_outcomes.append({
                        'type': 'miss', 'border_point': refracted_ray_end, 'source_ray': source_ray,
                        'refracted_ray': refracted_ray, 'prism': prism
                    })

        if not potential_outcomes:
            if team_prisms:
                # Fallback if no paths could be calculated at all.
                return self._refraction_beam_fallback_strengthen(teamId, random.choice(team_prisms))
            return {'success': False, 'reason': 'no valid refraction paths or prisms found'}

        # Prioritize hits over misses
        hits = [o for o in potential_outcomes if o['type'] == 'hit']
        if hits:
            # --- Primary Effect: Hit an enemy line ---
            chosen_hit = random.choice(hits)
            enemy_line = chosen_hit['enemy_line']
            self.game._delete_line(enemy_line)
            
            return {
                'success': True, 'type': 'refraction_beam',
                'destroyed_line': enemy_line, 'source_ray': chosen_hit['source_ray'],
                'refracted_ray': chosen_hit['refracted_ray'], 'prism_point_ids': chosen_hit['prism']['all_point_ids']
            }
        else:
            # --- Fallback Effect: Spawn a point on the border ---
            chosen_miss = random.choice(potential_outcomes) # All are misses
            border_point = chosen_miss['border_point']
            new_point = self.game._helper_spawn_on_border(teamId, border_point)
            if new_point:
                return {
                    'success': True, 'type': 'refraction_miss_spawn',
                    'new_point': new_point, 'source_ray': chosen_miss['source_ray'],
                    'refracted_ray': chosen_miss['refracted_ray'], 'prism_point_ids': chosen_miss['prism']['all_point_ids']
                }

            else:
                # If spawn fails, strengthen the prism as a final fallback.
                return self._refraction_beam_fallback_strengthen(teamId, chosen_miss['prism'])

    def purify_territory(self, teamId):
        """[FIGHT ACTION]: A Purifier cleanses an enemy territory. If none, it pushes enemy points."""
        team_purifiers = self.state.get('purifiers', {}).get(teamId, [])
        if not team_purifiers:
            return {'success': False, 'reason': 'no purifiers available'}
        
        points_map = self.state['points']
        enemy_territories = [t for t in self.state.get('territories', []) if t['teamId'] != teamId]

        if enemy_territories:
            # --- Primary Effect: Cleanse Territory ---
            best_target = None
            min_dist_sq = float('inf')
            for purifier in team_purifiers:
                if not all(pid in points_map for pid in purifier['point_ids']): continue
                purifier_points = [points_map[pid] for pid in purifier['point_ids']]
                purifier_center = points_centroid(purifier_points)
                if not purifier_center: continue
                
                for territory in enemy_territories:
                    if not all(pid in points_map for pid in territory['point_ids']): continue
                    territory_points = [points_map[pid] for pid in territory['point_ids']]
                    if len(territory_points) != 3: continue
                    territory_center = points_centroid(territory_points)

                    dist_sq = distance_sq(purifier_center, territory_center)
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        best_target = {'purifier_point_ids': purifier['point_ids'], 'territory_to_cleanse': territory}
            
            if best_target:
                territory_to_cleanse = best_target['territory_to_cleanse']
                cleansed_team_name = self.state['teams'][territory_to_cleanse['teamId']]['name']
                self.state['territories'].remove(territory_to_cleanse)
                return {
                    'success': True, 'type': 'purify_territory',
                    'cleansed_territory': territory_to_cleanse, 'purifier_point_ids': best_target['purifier_point_ids'],
                    'cleansed_team_name': cleansed_team_name
                }

        # --- Fallback Effect: Repulsive Pulse ---
        # This triggers if no enemy territories exist, or if they did but were invalid for some reason.
        purifier_to_pulse_from = random.choice(team_purifiers)
        if not all(pid in points_map for pid in purifier_to_pulse_from['point_ids']):
            return {'success': False, 'reason': 'purifier points for fallback no longer exist'}
        
        purifier_points = [points_map[pid] for pid in purifier_to_pulse_from['point_ids']]
        pulse_center = points_centroid(purifier_points)
        pulse_radius_sq = (self.state['grid_size'] * 0.25)**2
        
        points_to_push = [p for p in self.state['points'].values() if p['teamId'] != teamId]
        pushed_points = self.game._push_points_in_radius(pulse_center, pulse_radius_sq, 2.5, points_to_push)
        
        return {
            'success': True, 'type': 'purify_fizzle_push',
            'purifier_point_ids': purifier_to_pulse_from['point_ids'], 'pulse_center': pulse_center,
            'pushed_points_count': len(pushed_points)
        }

    def isolate_point(self, teamId):
        """[FIGHT ACTION]: Uses a point to project an isolation field onto a critical enemy point. Fallback to create a barricade."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if not team_point_ids:
            return {'success': False, 'reason': 'no points to project from'}

        # Find a target
        enemy_team_ids = [tid for tid in self.game.state['teams'] if tid != teamId]
        random.shuffle(enemy_team_ids)
        
        possible_targets = []
        for enemy_team_id in enemy_team_ids:
            # Don't isolate points that are already isolated or in stasis
            articulation_points = self.game._find_articulation_points(enemy_team_id)
            for pid in articulation_points:
                if pid in self.state['points'] and \
                   pid not in self.state.get('isolated_points', {}) and \
                   pid not in self.state.get('stasis_points', {}):
                     possible_targets.append(self.state['points'][pid])

        if possible_targets:
            # Use a random friendly point as the 'projector' of the effect
            projector_point_id = random.choice(team_point_ids)
            projector_point = self.state['points'][projector_point_id]
            
            target_point = min(possible_targets, key=lambda p: distance_sq(projector_point, p))
            target_point_id = target_point['id']

            # --- Primary Effect: Isolate Point ---
            if 'isolated_points' not in self.state:
                self.state['isolated_points'] = {}
            
            self.state['isolated_points'][target_point_id] = 4 # Isolated for 4 turns
            
            target_team_name = self.state['teams'][target_point['teamId']]['name']
            return {
                'success': True, 'type': 'isolate_point',
                'isolated_point': target_point,
                'projector_point': projector_point,
                'target_team_name': target_team_name
            }
        else:
            # --- Fallback Logic ---
            if len(team_point_ids) >= 2:
                # Fallback 1: Create barricade
                p1_id, p2_id = random.sample(team_point_ids, 2)
                p1 = self.state['points'][p1_id]
                p2 = self.state['points'][p2_id]
                new_barricade = self.game._create_temporary_barricade(teamId, p1, p2, 2)
                return {
                    'success': True, 'type': 'isolate_fizzle_barricade',
                    'barricade': new_barricade
                }
            else:
                # Fallback 2: Push a nearby enemy
                projector_point = self.state['points'][team_point_ids[0]]
                pulse_radius_sq = (self.state['grid_size'] * 0.2)**2
                points_to_push = [p for p in self.state['points'].values() if p['teamId'] != teamId]
                pushed_points = self.game._push_points_in_radius(projector_point, pulse_radius_sq, 1.5, points_to_push)

                return {
                    'success': True, 'type': 'isolate_fizzle_push',
                    'projector_point': projector_point,
                    'pushed_points_count': len(pushed_points)
                }

    def parallel_strike(self, teamId):
        """[FIGHT ACTION]: From a point, draw a line parallel to a friendly line. If it hits an enemy point, destroy it. If it hits the border, generate a point."""
        team_lines = self.game.get_team_lines(teamId)
        team_point_ids = self.game.get_team_point_ids(teamId)
        enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId]

        if not team_lines or not team_point_ids:
            return {'success': False, 'reason': 'missing required elements for parallel strike'}

        points = self.state['points']
        
        # Create a list of potential origins and reference lines to try
        potential_actions = []
        for p_origin_id in team_point_ids:
            for l_ref in team_lines:
                # To be a true parallel strike, the origin point shouldn't be part of the reference line
                if l_ref['p1_id'] != p_origin_id and l_ref['p2_id'] != p_origin_id:
                    potential_actions.append({'p_id': p_origin_id, 'l_ref': l_ref})
        
        if not potential_actions:
            return {'success': False, 'reason': 'no valid origin point / reference line pairs found'}

        random.shuffle(potential_actions)
        
        # Try a few combinations
        for action_combo in potential_actions[:15]:
            p_origin = points.get(action_combo['p_id'])
            l_ref = action_combo['l_ref']
            
            if not p_origin or not (l_ref['p1_id'] in points and l_ref['p2_id'] in points):
                continue

            p_ref1 = points[l_ref['p1_id']]
            p_ref2 = points[l_ref['p2_id']]
            
            ref_vx = p_ref2['x'] - p_ref1['x']
            ref_vy = p_ref2['y'] - p_ref1['y']
            
            if ref_vx == 0 and ref_vy == 0: continue

            # We check both parallel directions from the origin
            for strike_vx, strike_vy in [(ref_vx, ref_vy), (-ref_vx, -ref_vy)]:
                
                possible_targets = []
                for enemy_p in enemy_points:
                    enemy_vx = enemy_p['x'] - p_origin['x']
                    enemy_vy = enemy_p['y'] - p_origin['y']
                    
                    # Collinearity check using cross-product (with tolerance)
                    if abs(strike_vx * enemy_vy - strike_vy * enemy_vx) > 0.5: continue
                    # Direction check using dot-product
                    if (strike_vx * enemy_vx + strike_vy * enemy_vy) <= 0: continue
                    
                    possible_targets.append(enemy_p)
                
                if possible_targets:
                    target_point = min(possible_targets, key=lambda p: distance_sq(p_origin, p))
                    
                    if is_ray_blocked(p_origin, target_point, self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])):
                        continue

                    destroyed_point_data = self.game._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
                    if not destroyed_point_data: continue
                    
                    destroyed_team_name = self.state['teams'][destroyed_point_data['teamId']]['name']
                    return {
                        'success': True, 'type': 'parallel_strike_hit',
                        'destroyed_point': destroyed_point_data, 'destroyed_team_name': destroyed_team_name,
                        'attack_ray': {'p1': p_origin, 'p2': target_point}, 'ref_line': l_ref
                    }

                # If no targets were hit, try spawning on border
                dummy_end = {'x': p_origin['x'] + strike_vx, 'y': p_origin['y'] + strike_vy}
                border_point = get_extended_border_point(
                    p_origin, dummy_end, self.state['grid_size'],
                    self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])
                )
                if border_point:
                    new_point = self.game._helper_spawn_on_border(teamId, border_point)
                    if new_point:
                        return {
                            'success': True, 'type': 'parallel_strike_miss',
                            'new_point': new_point,
                            'attack_ray': {'p1': p_origin, 'p2': border_point}, 'ref_line': l_ref
                        }

        return {'success': False, 'reason': 'no valid parallel strike could be found'}

    def hull_breach(self, teamId):
        """[FIGHT ACTION]: Converts an enemy point inside the team's hull. If none, reinforces the hull."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 3:
            return {'success': False, 'reason': 'not enough points to form a hull'}

        all_points_map = self.state['points']
        team_points_list = [all_points_map[pid] for pid in team_point_ids if pid in all_points_map]
        
        hull_points = get_convex_hull(team_points_list)
        if len(hull_points) < 3:
            return {'success': False, 'reason': 'could not form a valid hull polygon'}

        vulnerable_enemies = self.game._get_vulnerable_enemy_points(teamId)
        
        targets_inside_hull = [
            p for p in vulnerable_enemies 
            if is_point_in_polygon(p, hull_points)
        ]

        if targets_inside_hull:
            # --- Primary Effect: Convert Point ---
            hull_centroid = points_centroid(hull_points)
            # Target the enemy point closest to the hull's center
            target_point = min(targets_inside_hull, key=lambda p: distance_sq(hull_centroid, p))

            original_team_id = target_point['teamId']
            original_team_name = self.state['teams'][original_team_id]['name']
            
            # Change team
            target_point['teamId'] = teamId
            
            # The point might have been part of enemy structures. Clean them up.
            self.game._cleanup_structures_for_point(target_point['id'])
            
            return {
                'success': True,
                'type': 'hull_breach_convert',
                'converted_point': target_point,
                'original_team_name': original_team_name,
                'hull_points': hull_points
            }
        else:
            # --- Fallback Effect: Reinforce or Create Hull Lines ---
            strengthened_lines = []
            created_lines = []
            team_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.game.get_team_lines(teamId)}
            
            for i in range(len(hull_points)):
                p1 = hull_points[i]
                p2 = hull_points[(i + 1) % len(hull_points)]
                line_key = tuple(sorted((p1['id'], p2['id'])))
                
                line_to_strengthen = team_lines_by_points.get(line_key)
                if line_to_strengthen:
                    if self.game._strengthen_line(line_to_strengthen):
                        strengthened_lines.append(line_to_strengthen)
                else:
                    # Line does not exist, create it
                    line_id = self.game._generate_id('l')
                    new_line = {"id": line_id, "p1_id": p1['id'], "p2_id": p2['id'], "teamId": teamId}
                    self.state['lines'].append(new_line)
                    created_lines.append(new_line)
            
            # If reinforcement/creation happened, it's a success
            if strengthened_lines or created_lines:
                return {
                    'success': True,
                    'type': 'hull_breach_fizzle_reinforce',
                    'strengthened_lines': strengthened_lines,
                    'created_lines': created_lines,
                    'hull_points': hull_points
                }
            
            # --- Final Fallback: Pulse ---
            # If hull is fully reinforced and connected, pulse to push nearby enemies.
            hull_centroid = points_centroid(hull_points)
            pulse_radius_sq = (self.game.state['grid_size'] * 0.2)**2
            points_to_push = [p for p in self.game.state['points'].values() if p['teamId'] != teamId]
            pushed_points = self.game._push_points_in_radius(hull_centroid, pulse_radius_sq, 1.5, points_to_push)
            
            return {
                'success': True,
                'type': 'hull_breach_fizzle_push',
                'hull_points': hull_points,
                'pushed_points_count': len(pushed_points)
            }