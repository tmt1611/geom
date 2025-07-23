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

    def bastion_pulse(self, teamId):
        """[FIGHT ACTION]: A bastion sacrifices a prong to destroy crossing enemy lines. If it fizzles, it creates a shockwave."""
        possible_bastions = self.game._find_possible_bastion_pulses(teamId)
        if not possible_bastions:
            return {'success': False, 'reason': 'no active bastions with crossing enemy lines'}

        bastion_to_pulse = random.choice(possible_bastions)
        if not bastion_to_pulse['prong_ids']:
            return {'success': False, 'reason': 'bastion has no prongs to sacrifice'}

        prong_to_sac_id = random.choice(bastion_to_pulse['prong_ids'])
        sacrificed_prong_data = self.game._delete_point_and_connections(prong_to_sac_id, aggressor_team_id=teamId)
        if not sacrificed_prong_data:
            return {'success': False, 'reason': 'selected prong point does not exist'}
        
        current_bastion_state = self.state['bastions'].get(bastion_to_pulse['id'])
        points_map = self.state['points']
        
        # If bastion is still valid and has prongs, proceed with primary effect
        if current_bastion_state and len(current_bastion_state.get('prong_ids', [])) >= 2:
            prong_points = [points_map[pid] for pid in current_bastion_state['prong_ids'] if pid in points_map]
            
            # Sort points angularly to form a correct simple polygon
            centroid = self.game._points_centroid(prong_points)
            prong_points.sort(key=lambda p: math.atan2(p['y'] - centroid['y'], p['x'] - centroid['x']))
            
            enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
            lines_destroyed = []
            for enemy_line in enemy_lines:
                if enemy_line['p1_id'] not in points_map or enemy_line['p2_id'] not in points_map: continue
                ep1, ep2 = points_map[enemy_line['p1_id']], points_map[enemy_line['p2_id']]
                
                for i in range(len(prong_points)):
                    perimeter_p1, perimeter_p2 = prong_points[i], prong_points[(i + 1) % len(prong_points)]
                    if segments_intersect(ep1, ep2, perimeter_p1, perimeter_p2):
                        lines_destroyed.append(enemy_line); break
            
            for l in lines_destroyed:
                if l in self.state['lines']: self.state['lines'].remove(l); self.state['shields'].pop(l.get('id'), None)
            
            return {
                'success': True, 'type': 'bastion_pulse',
                'sacrificed_prong': sacrificed_prong_data, 'lines_destroyed': lines_destroyed, 'bastion_id': bastion_to_pulse['id']
            }

        # --- Fallback Effect: Shockwave ---
        else:
            pushed_points = []
            push_distance = 2.0
            grid_size = self.state['grid_size']
            blast_radius_sq = (self.state['grid_size'] * 0.2)**2

            for point in self.state['points'].values():
                if distance_sq(sacrificed_prong_data, point) < blast_radius_sq:
                    dx, dy = point['x'] - sacrificed_prong_data['x'], point['y'] - sacrificed_prong_data['y']
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist < 0.1: continue

                    push_vx, push_vy = dx / dist, dy / dist
                    new_x = point['x'] + push_vx * push_distance
                    new_y = point['y'] + push_vy * push_distance
                    
                    point['x'] = round(max(0, min(grid_size - 1, new_x)))
                    point['y'] = round(max(0, min(grid_size - 1, new_y)))
                    pushed_points.append(point.copy())
            
            return {
                'success': True, 'type': 'bastion_pulse_fizzle_shockwave',
                'sacrificed_prong': sacrificed_prong_data, 'pushed_points_count': len(pushed_points), 'bastion_id': bastion_to_pulse['id']
            }

    def launch_payload(self, teamId):
        """[FIGHT ACTION]: A Trebuchet launches a payload. Prioritizes high-value points, then any enemy, and finally creates a fissure if no targets exist."""
        team_trebuchets = self.state.get('trebuchets', {}).get(teamId, [])
        if not team_trebuchets:
            return {'success': False, 'reason': 'no active trebuchets'}

        trebuchet = random.choice(team_trebuchets)
        if not all(pid in self.state['points'] for pid in trebuchet.get('point_ids', [])):
             return {'success': False, 'reason': 'trebuchet points no longer exist'}

        # --- Target Prioritization ---
        target_point = None

        # 1. High-value targets
        all_enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId]
        stasis_point_ids = set(self.state.get('stasis_points', {}).keys())
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
            vulnerable_targets = self._get_vulnerable_enemy_points(teamId)
            if vulnerable_targets:
                target_point = random.choice(vulnerable_targets)
        
        # --- Execute Action ---
        if target_point:
            # --- Primary or Secondary Effect: Destroy Point ---
            destroyed_point_data = self.game._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
            if not destroyed_point_data:
                return {'success': False, 'reason': 'failed to destroy target point'}
            
            # Determine if the target was high-value for logging/visuals
            is_high_value = destroyed_point_data['id'] in fortified_ids or \
                            destroyed_point_data['id'] in bastion_cores or \
                            destroyed_point_data['id'] in monolith_point_ids

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
            fissure_id = f"f_{uuid.uuid4().hex[:6]}"
            fissure_len = self.state['grid_size'] * 0.3
            
            # Create fissure at a random location
            center_x = random.uniform(fissure_len, grid_size - fissure_len)
            center_y = random.uniform(fissure_len, grid_size - fissure_len)
            angle = random.uniform(0, math.pi)

            p1 = {'x': center_x - (fissure_len / 2) * math.cos(angle), 'y': center_y - (fissure_len / 2) * math.sin(angle)}
            p2 = {'x': center_x + (fissure_len / 2) * math.cos(angle), 'y': center_y + (fissure_len / 2) * math.sin(angle)}

            p1['x'] = round(max(0, min(grid_size - 1, p1['x'])))
            p1['y'] = round(max(0, min(grid_size - 1, p1['y'])))
            p2['x'] = round(max(0, min(grid_size - 1, p2['x'])))
            p2['y'] = round(max(0, min(grid_size - 1, p2['y'])))

            new_fissure = {'id': fissure_id, 'p1': p1, 'p2': p2, 'turns_left': 3}
            if 'fissures' not in self.state: self.state['fissures'] = []
            self.state['fissures'].append(new_fissure)

            return {
                'success': True,
                'type': 'launch_payload_fizzle_fissure',
                'fissure': new_fissure,
                'trebuchet_points': trebuchet['point_ids'],
                'launch_point_id': trebuchet['apex_id'],
                'impact_site': {'x': center_x, 'y': center_y}
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
            
            zap_ray_end = self.game._get_extended_border_point(p_eye, target_point) or target_point
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
            border_point = self.game._get_extended_border_point(p_eye, dummy_end_point)
            
            if not border_point or self.game._is_ray_blocked(p_eye, border_point):
                 return {'success': False, 'reason': 'zap path to border was blocked'}
            
            is_valid, _ = self.game._is_spawn_location_valid(border_point, teamId)
            if not is_valid:
                 return {'success': False, 'reason': 'no valid spawn location on border for zap miss'}

            new_point_id = f"p_{uuid.uuid4().hex[:6]}"
            new_point = {**border_point, "teamId": teamId, "id": new_point_id}
            self.state['points'][new_point_id] = new_point
            
            return {
                'success': True, 'type': 'sentry_zap_miss_spawn',
                'new_point': new_point,
                'rune_points': rune['point_ids'],
                'attack_ray': {'p1': p_eye, 'p2': border_point}
            }

    def chain_lightning(self, teamId):
        """[FIGHT ACTION]: An I-Rune sacrifices an internal point to strike an enemy. If it fizzles, it creates a mini-nova."""
        team_i_runes = self.state.get('runes', {}).get(teamId, {}).get('i_shape', [])
        # Requires an internal point to sacrifice
        valid_runes = [r for r in team_i_runes if r.get('internal_points')]
        if not valid_runes:
            return {'success': False, 'reason': 'no I-Runes with sacrificial points'}

        chosen_rune = random.choice(valid_runes)
        p_to_sac_id = random.choice(chosen_rune['internal_points'])
        sacrificed_point_data = self.game._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
        if not sacrificed_point_data:
             return {'success': False, 'reason': 'failed to sacrifice I-Rune point'}

        endpoint1_id, endpoint2_id = chosen_rune.get('endpoints', [None, None])
        
        target_point = None
        if endpoint1_id in self.state['points'] and endpoint2_id in self.state['points']:
            endpoint1 = self.state['points'][endpoint1_id]
            endpoint2 = self.state['points'][endpoint2_id]
            vulnerable_enemies = self._get_vulnerable_enemy_points(teamId)
            
            if vulnerable_enemies:
                closest_enemy = min(vulnerable_enemies, key=lambda p: min(distance_sq(endpoint1, p), distance_sq(endpoint2, p)))
                target_point = closest_enemy
        
        if target_point:
            # --- Primary Effect: Destroy Point ---
            destroyed_point_data = self.game._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
            if not destroyed_point_data:
                 return {'success': False, 'reason': 'failed to destroy target point'}
            
            destroyed_team_name = self.state['teams'][destroyed_point_data['teamId']]['name']
            return {
                'success': True, 'type': 'chain_lightning',
                'sacrificed_point': sacrificed_point_data,
                'destroyed_point': destroyed_point_data,
                'rune_points': chosen_rune['point_ids'],
                'destroyed_team_name': destroyed_team_name
            }
        else:
            # --- Fallback Effect: Mini-Nova ---
            blast_radius_sq = (self.state['grid_size'] * 0.15)**2
            lines_destroyed = []
            enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
            points_map = self.state['points']

            for line in enemy_lines:
                if line.get('id') in self.game._get_bastion_line_ids() or line.get('id') in self.state['shields']: continue
                if not (line['p1_id'] in points_map and line['p2_id'] in points_map): continue
                p1, p2 = points_map[line['p1_id']], points_map[line['p2_id']]

                if distance_sq(sacrificed_point_data, p1) < blast_radius_sq or distance_sq(sacrificed_point_data, p2) < blast_radius_sq:
                    lines_destroyed.append(line)
            
            for l in lines_destroyed:
                if l in self.state['lines']:
                    self.state['lines'].remove(l)
                    self.state['shields'].pop(l.get('id'), None)
            
            return {
                'success': True, 'type': 'chain_lightning_fizzle_nova',
                'sacrificed_point': sacrificed_point_data,
                'lines_destroyed_count': len(lines_destroyed),
                'rune_points': chosen_rune['point_ids']
            }

    def refraction_beam(self, teamId):
        """[FIGHT ACTION]: Uses a Prism to refract an attack beam. If it misses, it creates a new point on the border."""
        team_prisms = self.state.get('prisms', {}).get(teamId, [])
        if not team_prisms:
            return {'success': False, 'reason': 'no active prisms'}
        
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
            
            source_ray_end = self.game._get_extended_border_point(ls1, ls2)
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
                refracted_ray_end = self.game._get_extended_border_point(intersection_point, refracted_end_dummy)
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
            return {'success': False, 'reason': 'no valid refraction paths found'}

        # Prioritize hits over misses
        hits = [o for o in potential_outcomes if o['type'] == 'hit']
        if hits:
            # --- Primary Effect: Hit an enemy line ---
            chosen_hit = random.choice(hits)
            enemy_line = chosen_hit['enemy_line']
            self.state['lines'].remove(enemy_line)
            self.state['shields'].pop(enemy_line.get('id'), None)
            
            return {
                'success': True, 'type': 'refraction_beam',
                'destroyed_line': enemy_line, 'source_ray': chosen_hit['source_ray'],
                'refracted_ray': chosen_hit['refracted_ray'], 'prism_point_ids': chosen_hit['prism']['all_point_ids']
            }
        else:
            # --- Fallback Effect: Spawn a point on the border ---
            chosen_miss = random.choice(potential_outcomes) # All are misses
            border_point = chosen_miss['border_point']
            is_valid, _ = self.game._is_spawn_location_valid(border_point, teamId)
            if is_valid:
                new_point_id = f"p_{uuid.uuid4().hex[:6]}"
                new_point = {**border_point, "teamId": teamId, "id": new_point_id}
                self.state['points'][new_point_id] = new_point
                return {
                    'success': True, 'type': 'refraction_miss_spawn',
                    'new_point': new_point, 'source_ray': chosen_miss['source_ray'],
                    'refracted_ray': chosen_miss['refracted_ray'], 'prism_point_ids': chosen_miss['prism']['all_point_ids']
                }

        # If we got here, it means we only had miss options but none were valid spawn locations
        return {'success': False, 'reason': 'no valid spawn location for refracted beam miss'}

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
                purifier_center = self.game._points_centroid(purifier_points)
                if not purifier_center: continue
                
                for territory in enemy_territories:
                    if not all(pid in points_map for pid in territory['point_ids']): continue
                    territory_points = [points_map[pid] for pid in territory['point_ids']]
                    if len(territory_points) != 3: continue
                    territory_center = self.game._points_centroid(territory_points)

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
        pulse_center = self.game._points_centroid(purifier_points)
        pulse_radius_sq = (self.state['grid_size'] * 0.25)**2
        
        pushed_points = []
        push_distance = 2.5
        grid_size = self.state['grid_size']

        for point in [p for p in self.state['points'].values() if p['teamId'] != teamId]:
            if distance_sq(pulse_center, point) < pulse_radius_sq:
                dx = point['x'] - pulse_center['x']
                dy = point['y'] - pulse_center['y']
                dist = math.sqrt(dx**2 + dy**2)
                if dist < 0.1: continue

                new_x = point['x'] + (dx / dist) * push_distance
                new_y = point['y'] + (dy / dist) * push_distance
                point['x'] = round(max(0, min(grid_size - 1, new_x)))
                point['y'] = round(max(0, min(grid_size - 1, new_y)))
                pushed_points.append(point.copy())
        
        return {
            'success': True, 'type': 'purify_fizzle_push',
            'purifier_point_ids': purifier_to_pulse_from['point_ids'], 'pulse_center': pulse_center,
            'pushed_points_count': len(pushed_points)
        }