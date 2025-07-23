import random
import math
import uuid
from ..geometry import (
    distance_sq, segments_intersect, get_segment_intersection_point
)

class FightActionsHandler:
    def __init__(self, game):
        self.game = game

    # --- Action Precondition Checks ---

    def can_perform_attack_line(self, teamId):
        return len(self.game.get_team_lines(teamId)) > 0, "Requires at least 1 line to attack from."

    def can_perform_convert_point(self, teamId):
        return len(self.game.get_team_lines(teamId)) > 0, "Requires at least 1 line to sacrifice."

    def can_perform_pincer_attack(self, teamId):
        return len(self.game.get_team_point_ids(teamId)) >= 2, "Requires at least 2 points."

    def can_perform_territory_strike(self, teamId):
        return len(self._get_large_territories(teamId)) > 0, "No large territories available."

    def can_perform_bastion_pulse(self, teamId):
        can_perform = len(self.game._find_possible_bastion_pulses(teamId)) > 0
        return can_perform, "No bastion has crossing enemy lines to pulse."

    def can_perform_sentry_zap(self, teamId):
        team_i_runes = self.state.get('runes', {}).get(teamId, {}).get('i_shape', [])
        can_perform = any(r.get('internal_points') for r in team_i_runes)
        return can_perform, "Requires an I-Rune with at least 3 points."

    def can_perform_chain_lightning(self, teamId):
        team_i_runes = self.state.get('runes', {}).get(teamId, {}).get('i_shape', [])
        can_perform = any(r.get('internal_points') for r in team_i_runes)
        return can_perform, "Requires an I-Rune with internal points."

    def can_perform_refraction_beam(self, teamId):
        has_prism = bool(self.state.get('prisms', {}).get(teamId, []))
        num_enemy_lines = len(self.state['lines']) - len(self.game.get_team_lines(teamId))
        can_perform = has_prism and num_enemy_lines > 0
        return can_perform, "Requires a Prism and enemy lines."

    def can_perform_launch_payload(self, teamId):
        can_perform = bool(self.state.get('trebuchets', {}).get(teamId, []))
        return can_perform, "Requires a Trebuchet."

    def can_perform_purify_territory(self, teamId):
        has_purifier = bool(self.state.get('purifiers', {}).get(teamId, []))
        has_enemy_territory = any(t['teamId'] != teamId for t in self.state.get('territories', []))
        can_perform = has_purifier and has_enemy_territory
        return can_perform, "Requires a Purifier and an enemy territory."

    # --- End Precondition Checks ---

    @property
    def state(self):
        """Provides direct access to the game's current state dictionary."""
        return self.game.state

    def _get_vulnerable_enemy_points(self, teamId):
        """Returns a list of enemy points that are not immune to standard attacks."""
        return self.game._get_vulnerable_enemy_points(teamId)

    def attack_line(self, teamId):
        """[FIGHT ACTION]: Extend a line to hit an enemy line. If it misses, it creates a new point on the border."""
        team_lines = self.game.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to attack from'}
        
        points = self.state['points']
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        team_has_cross_rune = len(self.state.get('runes', {}).get(teamId, {}).get('cross', [])) > 0
        
        random.shuffle(team_lines)
        for line in team_lines:
            if line['p1_id'] not in points or line['p2_id'] not in points: continue
            
            p1 = points[line['p1_id']]
            p2 = points[line['p2_id']]
            
            p_start, p_end = random.choice([(p1, p2), (p2, p1)])
            border_point = self.game._get_extended_border_point(p_start, p_end)
            if not border_point: continue

            attack_segment_p1 = p_end
            attack_segment_p2 = border_point

            if self.game._is_ray_blocked(attack_segment_p1, attack_segment_p2):
                continue

            closest_hit = None
            min_dist_sq = float('inf')

            for enemy_line in enemy_lines:
                is_shielded = enemy_line.get('id') in self.state['shields']
                if is_shielded and not team_has_cross_rune:
                    continue
                
                bastion_line_ids = self.game._get_bastion_line_ids()
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
            
            if closest_hit:
                enemy_line = closest_hit['target_line']
                line_strength = self.state.get('line_strengths', {}).get(enemy_line['id'])
                if line_strength and line_strength > 0:
                    self.state['line_strengths'][enemy_line['id']] -= 1
                    if self.state['line_strengths'][enemy_line['id']] <= 0:
                        del self.state['line_strengths'][enemy_line['id']]
                    return {
                        'success': True, 'type': 'attack_line_strengthened',
                        'damaged_line': enemy_line, 'attacker_line': line,
                        'attack_ray': {'p1': attack_segment_p1, 'p2': closest_hit['intersection_point']},
                        'intersection_point': closest_hit['intersection_point']
                    }

                enemy_team_name = self.state['teams'][enemy_line['teamId']]['name']
                self.state['lines'].remove(enemy_line)
                self.state['shields'].pop(enemy_line.get('id'), None)
                self.state['line_strengths'].pop(enemy_line.get('id'), None)
                return {
                    'success': True, 'type': 'attack_line', 'destroyed_team': enemy_team_name, 'destroyed_line': enemy_line,
                    'attacker_line': line, 'attack_ray': {'p1': attack_segment_p1, 'p2': closest_hit['intersection_point']},
                    'bypassed_shield': closest_hit['bypassed_shield']
                }
            else:
                is_valid, _ = self.game._is_spawn_location_valid(border_point, teamId)
                if is_valid:
                    new_point_id = f"p_{uuid.uuid4().hex[:6]}"
                    new_point = {**border_point, "teamId": teamId, "id": new_point_id}
                    self.state['points'][new_point_id] = new_point
                    return {
                        'success': True, 'type': 'attack_miss_spawn', 'new_point': new_point,
                        'attacker_line': line, 'attack_ray': {'p1': attack_segment_p1, 'p2': border_point}
                    }
        
        return {'success': False, 'reason': 'no valid attack or spawn opportunity found'}

    def convert_point(self, teamId):
        """[FIGHT ACTION]: Sacrifice a line to convert a nearby enemy point. If no target, creates a repulsive pulse."""
        team_lines = self.game.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to sacrifice'}

        line_to_sac = random.choice(team_lines)
        points_map = self.state['points']
        
        if line_to_sac['p1_id'] not in points_map or line_to_sac['p2_id'] not in points_map:
             return {'success': False, 'reason': 'sacrificial line points do not exist'}

        p1 = points_map[line_to_sac['p1_id']]
        p2 = points_map[line_to_sac['p2_id']]
        midpoint = {'x': (p1['x'] + p2['x']) / 2, 'y': (p1['y'] + p2['y']) / 2}
        
        enemy_points = self._get_vulnerable_enemy_points(teamId)
        conversion_range_sq = (self.state['grid_size'] * 0.3)**2
        
        targets_in_range = [ep for ep in enemy_points if distance_sq(midpoint, ep) < conversion_range_sq]
        
        self.state['lines'].remove(line_to_sac)
        self.state['shields'].pop(line_to_sac.get('id'), None)

        if targets_in_range:
            point_to_convert = min(targets_in_range, key=lambda p: distance_sq(midpoint, p))
            original_team_id = point_to_convert['teamId']
            original_team_name = self.state['teams'][original_team_id]['name']
            point_to_convert['teamId'] = teamId
            return {
                'success': True, 'type': 'convert_point', 'converted_point': point_to_convert,
                'sacrificed_line': line_to_sac, 'original_team_name': original_team_name
            }
        else:
            pushed_points = []
            push_distance = 2.0
            grid_size = self.state['grid_size']
            for point in [p for p in self.state['points'].values() if p['teamId'] != teamId]:
                if distance_sq(midpoint, point) < conversion_range_sq:
                    dx, dy = point['x'] - midpoint['x'], point['y'] - midpoint['y']
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist < 0.1: continue
                    new_x = point['x'] + (dx / dist) * push_distance
                    new_y = point['y'] + (dy / dist) * push_distance
                    point['x'] = round(max(0, min(grid_size - 1, new_x)))
                    point['y'] = round(max(0, min(grid_size - 1, new_y)))
                    pushed_points.append(point.copy())
            return {
                'success': True, 'type': 'convert_fizzle_push', 'sacrificed_line': line_to_sac,
                'pulse_center': midpoint, 'radius_sq': conversion_range_sq, 'pushed_points_count': len(pushed_points)
            }

    def _pincer_attack_fallback_barricade(self, teamId, p1_id, p2_id):
        points = self.state['points']
        p1 = points.get(p1_id)
        p2 = points.get(p2_id)

        if not p1 or not p2:
            return {'success': False, 'reason': 'points for fallback barricade do not exist'}
        
        barricade_id = f"bar_{uuid.uuid4().hex[:6]}"
        new_barricade = {
            'id': barricade_id, 'teamId': teamId,
            'p1': {'x': p1['x'], 'y': p1['y']}, 'p2': {'x': p2['x'], 'y': p2['y']},
            'turns_left': 2
        }
        self.state['barricades'].append(new_barricade)
        return {
            'success': True, 'type': 'pincer_fizzle_barricade',
            'barricade': new_barricade, 'pincer_points': [p1_id, p2_id]
        }

    def pincer_attack(self, teamId):
        """[FIGHT ACTION]: Two points flank and destroy an enemy point. If not possible, they form a defensive barricade."""
        team_point_ids = self.game.get_team_point_ids(teamId)
        if len(team_point_ids) < 2:
            return {'success': False, 'reason': 'not enough points for pincer attack'}

        enemy_points = self._get_vulnerable_enemy_points(teamId)
        if not enemy_points:
             p1_id, p2_id = random.sample(team_point_ids, 2)
             return self._pincer_attack_fallback_barricade(teamId, p1_id, p2_id)

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
                midpoint = self.game._points_centroid([p1, p2])
                target_point = min(possible_targets, key=lambda p: distance_sq(midpoint, p))
                destroyed_point_data = self.game._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
                if not destroyed_point_data: continue
                destroyed_team_name = self.state['teams'][destroyed_point_data['teamId']]['name']
                return {
                    'success': True, 'type': 'pincer_attack', 'destroyed_point': destroyed_point_data,
                    'attacker_p1_id': p1_id, 'attacker_p2_id': p2_id, 'destroyed_team_name': destroyed_team_name
                }
        
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
                if len(triangle_points) == 3 and self.game._polygon_area(triangle_points) >= MIN_AREA:
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
        centroid = self.game._points_centroid(triangle_points)

        enemy_points = self._get_vulnerable_enemy_points(teamId)
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
            p_ids = territory['point_ids']
            boundary_lines_keys = [tuple(sorted((p_ids[0], p_ids[1]))), tuple(sorted((p_ids[1], p_ids[2]))), tuple(sorted((p_ids[2], p_ids[0])))]
            strengthened_lines = []
            for line in self.game.get_team_lines(teamId):
                if tuple(sorted((line['p1_id'], line['p2_id']))) in boundary_lines_keys:
                    if self.game._strengthen_line(line):
                        strengthened_lines.append(line)
            return {
                'success': True, 'type': 'territory_fizzle_reinforce',
                'territory_point_ids': territory['point_ids'], 'strengthened_lines': strengthened_lines
            }