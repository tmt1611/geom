import random
import math
from ..geometry import (
    distance_sq, clamp_and_round_point_coords, points_centroid, segments_intersect,
    get_edges_by_distance, get_extended_border_point, get_segment_intersection_point
)

class SacrificeActionsHandler:
    def __init__(self, game):
        self.game = game

    @property
    def state(self):
        """Provides direct access to the game's current state dictionary."""
        return self.game.state

    def nova_burst(self, teamId):
        """[SACRIFICE ACTION]: A point is destroyed. If near enemy lines, it destroys them. Otherwise, it pushes all nearby points away."""
        sac_point_id = None
        
        # Prioritize sacrificing a point that will have a definite effect
        ideal_sac_points = self.game.query.find_possible_nova_bursts(teamId)
        if ideal_sac_points:
            # Choose the ideal point that is closest to the team's centroid, to defend the core
            team_centroid = self.game.query.get_team_centroid(teamId)
            points = self.state['points']
            sac_point_id = min(ideal_sac_points, key=lambda pid: distance_sq(points[pid], team_centroid))
        else:
            # If no ideal point, find any non-critical point for the fallback shockwave effect.
            sac_point_id = self.game.query.find_non_critical_sacrificial_point(teamId)

        if not sac_point_id or sac_point_id not in self.state['points']:
            return {'success': False, 'reason': 'no suitable point found to sacrifice'}

        sac_point_coords = self.state['points'][sac_point_id].copy()
        blast_radius_sq = (self.state['grid_size'] * 0.25)**2

        # --- Perform Sacrifice ---
        self.game._delete_point_and_connections(sac_point_id, aggressor_team_id=teamId, allow_regeneration=True)
        
        # --- Check for Primary Effect (Line Destruction) ---
        lines_to_remove_by_proximity = []
        points_to_check = self.state['points']
        bastion_line_ids = self.game.query.get_bastion_line_ids()
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]

        for line in enemy_lines:
            if line.get('id') in bastion_line_ids: continue
            if not (line['p1_id'] in points_to_check and line['p2_id'] in points_to_check): continue
            
            p1 = points_to_check[line['p1_id']]
            p2 = points_to_check[line['p2_id']]

            if distance_sq(sac_point_coords, p1) < blast_radius_sq or distance_sq(sac_point_coords, p2) < blast_radius_sq:
                lines_to_remove_by_proximity.append(line)

        if lines_to_remove_by_proximity:
            # Primary effect happened
            for l in lines_to_remove_by_proximity:
                self.game._delete_line(l)
            
            return {
                'success': True,
                'type': 'nova_burst',
                'sacrificed_point': sac_point_coords,
                'lines_destroyed': len(lines_to_remove_by_proximity)
            }
        else:
            # Fallback Effect: Push points
            points_to_push = list(self.state['points'].values())
            pushed_points = self.game._push_points_in_radius(sac_point_coords, blast_radius_sq, 2.0, points_to_push)
            
            return {
                'success': True,
                'type': 'nova_shockwave',
                'sacrificed_point': sac_point_coords,
                'pushed_points_count': len(pushed_points)
            }

    def create_whirlpool(self, teamId):
        """[SACRIFICE ACTION]: A point is destroyed. If points are nearby, it creates a vortex. Otherwise, it creates a small fissure."""
        p_to_sac_id = self.game.query.find_non_critical_sacrificial_point(teamId)
        if not p_to_sac_id:
            # This should not happen if precondition is correct, but is a good safeguard.
            return {'success': False, 'reason': 'no non-critical points available to sacrifice'}
        sac_point_coords = self.state['points'][p_to_sac_id].copy()
        
        # Check for nearby points BEFORE sacrificing to decide the outcome
        whirlpool_radius_sq = (self.state['grid_size'] * 0.3)**2
        has_targets = any(
            p['id'] != p_to_sac_id and distance_sq(sac_point_coords, p) < whirlpool_radius_sq
            for p in self.state['points'].values()
        )

        # --- Perform Sacrifice ---
        sacrificed_point_data = self.game._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId, allow_regeneration=True)
        if not sacrificed_point_data:
            return {'success': False, 'reason': 'failed to sacrifice point'}

        # --- Determine Outcome ---
        if has_targets:
            # Primary Effect: Create Whirlpool
            whirlpool_id = self.game._generate_id('wp')
            new_whirlpool = {
                'id': whirlpool_id, 'teamId': teamId, 'coords': sac_point_coords,
                'turns_left': 4, 'strength': 0.05, 'swirl': 0.5,
                'radius_sq': whirlpool_radius_sq
            }
            if 'whirlpools' not in self.state: self.state['whirlpools'] = []
            self.state['whirlpools'].append(new_whirlpool)
            return {
                'success': True, 'type': 'create_whirlpool',
                'whirlpool': new_whirlpool, 'sacrificed_point': sacrificed_point_data
            }
        else:
            # Fallback Effect: Create a small fissure
            fissure_len = self.state['grid_size'] * 0.2
            new_fissure = self.game._create_random_fissure(sacrificed_point_data, fissure_len, 3)
            return {
                'success': True, 'type': 'whirlpool_fizzle_fissure',
                'fissure': new_fissure, 'sacrificed_point': sacrificed_point_data
            }

    def phase_shift(self, teamId):
        """[SACRIFICE ACTION]: Sacrifice a line to teleport one of its points. If teleport fails, the other point becomes a temporary anchor."""
        eligible_lines = self.game.query.get_eligible_phase_shift_lines(teamId)
        if not eligible_lines:
            return {'success': False, 'reason': 'no non-critical/safe lines to sacrifice'}

        # Sacrifice the line closest to a vulnerable enemy point
        vulnerable_enemies = self.game.query.get_vulnerable_enemy_points(teamId)
        points = self.state['points']
        
        def get_line_proximity_to_vulnerable(line):
            if not vulnerable_enemies or line['p1_id'] not in points or line['p2_id'] not in points:
                return float('inf')
            p1, p2 = points[line['p1_id']], points[line['p2_id']]
            midpoint = points_centroid([p1, p2])
            return min(distance_sq(midpoint, ep) for ep in vulnerable_enemies)

        line_to_sac = min(eligible_lines, key=get_line_proximity_to_vulnerable)
        p_to_move_id, p_to_anchor_id = random.choice([
            (line_to_sac['p1_id'], line_to_sac['p2_id']),
            (line_to_sac['p2_id'], line_to_sac['p1_id'])
        ])

        # Ensure points still exist before proceeding
        if p_to_move_id not in self.state['points'] or p_to_anchor_id not in self.state['points']:
            return {'success': False, 'reason': 'phase shift points no longer exist'}

        point_to_move = self.state['points'][p_to_move_id]
        original_coords = {'x': point_to_move['x'], 'y': point_to_move['y']}

        # Sacrifice the line first, as the action's cost is paid upfront
        self.game._delete_line(line_to_sac)

        # --- Try to find a new valid location ---
        new_coords = None
        grid_size = self.state['grid_size']
        for _ in range(25): # Try several times
            candidate_coords = {'x': random.randint(0, grid_size - 1), 'y': random.randint(0, grid_size - 1)}
            is_valid, _ = self.game.is_spawn_location_valid(candidate_coords, teamId, min_dist_sq=1.0)
            if is_valid:
                new_coords = candidate_coords
                break
        
        if new_coords:
            # --- Primary Effect: Phase Shift ---
            point_to_move['x'] = new_coords['x']
            point_to_move['y'] = new_coords['y']
            return {
                'success': True, 'type': 'phase_shift',
                'moved_point_id': p_to_move_id, 'original_coords': original_coords, 'new_coords': new_coords, 'sacrificed_line': line_to_sac
            }
        else:
            # --- Fallback Effect: Create Anchor ---
            anchor_duration = 3 # A shorter anchor for a fizzled action
            self.state['anchors'][p_to_anchor_id] = {'teamId': teamId, 'turns_left': anchor_duration}
            anchor_point = self.state['points'][p_to_anchor_id]
            return {
                'success': True, 'type': 'phase_shift_fizzle_anchor',
                'anchor_point': anchor_point, 'sacrificed_line': line_to_sac
            }

    def rift_trap(self, teamId):
        """[SACRIFICE ACTION]: Sacrifices a point to create a temporary trap. If an enemy enters, it's destroyed. If not, the trap becomes a new point."""
        # Find a non-critical point to sacrifice
        p_to_sac_id = self.game.query.find_non_critical_sacrificial_point(teamId)
        if not p_to_sac_id:
            return {'success': False, 'reason': 'no non-critical points available to sacrifice'}
        sac_point_coords = self.state['points'][p_to_sac_id].copy()
        
        # Perform Sacrifice
        sacrificed_point_data = self.game._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId, allow_regeneration=True)
        if not sacrificed_point_data:
            return {'success': False, 'reason': 'failed to sacrifice point for trap'}

        # Create the trap
        trap_id = self.game._generate_id('rt')
        new_trap = {
            'id': trap_id,
            'teamId': teamId,
            'coords': sac_point_coords,
            'turns_left': 4, # Expires at the start of turn 4, so exists for 3 full turns
            'radius_sq': (self.state['grid_size'] * 0.1)**2,
        }
        if 'rift_traps' not in self.state: self.state['rift_traps'] = []
        self.state['rift_traps'].append(new_trap)
        
        return {
            'success': True,
            'type': 'create_rift_trap',
            'trap': new_trap,
            'sacrificed_point': sacrificed_point_data
        }

    def scorch_territory(self, teamId):
        """[SACRIFICE ACTION]: Sacrifices a claimed territory to render the area impassable for several turns."""
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        if not team_territories:
            return {'success': False, 'reason': 'no territories to sacrifice'}
        
        # Sacrifice the smallest territory, as it's the least valuable
        points_map = self.state['points']
        territory_to_scorch = min(team_territories, key=lambda t: polygon_area([points_map[pid] for pid in t['point_ids'] if pid in points_map]))
        
        # Get point coordinates before deleting them
        points_map = self.state['points']
        if not all(pid in points_map for pid in territory_to_scorch['point_ids']):
            return {'success': False, 'reason': 'territory points no longer exist'}
        
        scorched_points_coords = [points_map[pid].copy() for pid in territory_to_scorch['point_ids']]

        # --- Sacrifice the territory ---
        # Remove territory object
        self.state['territories'].remove(territory_to_scorch)
        
        # Delete points and their connected lines
        sacrificed_points_data = []
        for pid in territory_to_scorch['point_ids']:
            sac_data = self.game._delete_point_and_connections(pid, aggressor_team_id=teamId)
            if sac_data:
                sacrificed_points_data.append(sac_data)

        if not sacrificed_points_data:
            return {'success': False, 'reason': 'failed to sacrifice territory points'}
            
        # --- Create Scorched Zone ---
        new_scorched_zone = {
            'teamId': teamId,
            'points': scorched_points_coords, # Store copies of point data
            'turns_left': 5
        }
        if 'scorched_zones' not in self.state: self.state['scorched_zones'] = []
        self.state['scorched_zones'].append(new_scorched_zone)
        
        return {
            'success': True,
            'type': 'scorch_territory',
            'scorched_zone': new_scorched_zone,
            'sacrificed_points_count': len(sacrificed_points_data)
        }



    def convert_point(self, teamId):
        """[SACRIFICE ACTION]: Sacrifices a line to convert a nearby enemy point. If not possible, creates a repulsive pulse."""
        # We should sacrifice a non-critical line if possible
        eligible_lines = self.game.query.get_eligible_phase_shift_lines(teamId)
        if not eligible_lines:
            # Fallback to any line if no "safe" lines are found
            eligible_lines = self.game.query.get_team_lines(teamId)
        
        if not eligible_lines:
            return {'success': False, 'reason': 'no lines to sacrifice'}

        # Sacrifice the line closest to a vulnerable enemy
        points = self.state['points']
        vulnerable_enemies = self.game.query.get_vulnerable_enemy_points(teamId)
        
        if vulnerable_enemies:
            def get_line_proximity(line):
                if line['p1_id'] not in points or line['p2_id'] not in points: return float('inf')
                midpoint = points_centroid([points[line['p1_id']], points[line['p2_id']]])
                return min(distance_sq(midpoint, ep) for ep in vulnerable_enemies)
            
            line_to_sac = min(eligible_lines, key=get_line_proximity)
        else:
            # Fallback: sacrifice the shortest line
            valid_eligible_lines = [l for l in eligible_lines if l['p1_id'] in points and l['p2_id'] in points]
            if not valid_eligible_lines:
                return {'success': False, 'reason': 'no valid lines with existing points'}
            line_to_sac = min(valid_eligible_lines, key=lambda l: distance_sq(points[l['p1_id']], points[l['p2_id']]))
        points = self.state['points']
        
        if line_to_sac['p1_id'] not in points or line_to_sac['p2_id'] not in points:
             return {'success': False, 'reason': 'line points for sacrifice no longer exist'}

        p1 = points[line_to_sac['p1_id']]
        p2 = points[line_to_sac['p2_id']]
        midpoint = points_centroid([p1, p2])
        
        # --- Sacrifice the line before determining outcome ---
        self.game._delete_line(line_to_sac)

        # --- Find Primary Target ---
        vulnerable_enemies = self.game.query.get_vulnerable_enemy_points(teamId)
        max_range_sq = (self.state['grid_size'] * 0.3)**2
        
        closest_target = None
        min_dist_sq = max_range_sq

        if vulnerable_enemies:
            for enemy_p in vulnerable_enemies:
                dist_sq = distance_sq(midpoint, enemy_p)
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_target = enemy_p

        if closest_target:
            # --- Primary Effect: Convert Point ---
            original_team_id = closest_target['teamId']
            original_team_name = self.state['teams'][original_team_id]['name']
            
            # Change team
            closest_target['teamId'] = teamId
            
            # The point might have been part of enemy structures. We need to clean those up.
            self.game._cleanup_structures_for_point(closest_target['id'])
            
            return {
                'success': True,
                'type': 'convert_point',
                'converted_point': closest_target,
                'original_team_name': original_team_name,
                'sacrificed_line': line_to_sac
            }
        else:
            # --- Fallback Effect: Repulsive Pulse ---
            pulse_radius_sq = (self.state['grid_size'] * 0.2)**2
            # We need to get enemy points again, as vulnerable_enemies might be empty
            enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId]
            
            pushed_points = self.game._push_points_in_radius(midpoint, pulse_radius_sq, 2.0, enemy_points)
            
            return {
                'success': True,
                'type': 'convert_fizzle_push',
                'sacrificed_line': line_to_sac,
                'pulse_center': midpoint,
                'pushed_points_count': len(pushed_points)
            }

    def line_retaliation(self, teamId):
        """[SACRIFICE ACTION]: Sacrifices a point on a line to fire two projectiles from the line's former position."""
        eligible_lines = self.game.query.get_eligible_phase_shift_lines(teamId)
        if not eligible_lines:
            return {'success': False, 'reason': 'no eligible line to sacrifice a point from'}

        # Choose the line that is furthest from the team's center, to attack from the periphery
        points = self.state['points']
        # Filter for lines with existing points before calculating distances.
        valid_eligible_lines = [l for l in eligible_lines if l['p1_id'] in points and l['p2_id'] in points]
        if not valid_eligible_lines:
            return {'success': False, 'reason': 'no valid lines with existing points'}
        
        team_centroid = self.game.query.get_team_centroid(teamId)
        line_to_unravel = max(valid_eligible_lines, key=lambda l: distance_sq(points_centroid([points[l['p1_id']], points[l['p2_id']]]), team_centroid))
        points = self.state['points']
        
        p1_id, p2_id = line_to_unravel['p1_id'], line_to_unravel['p2_id']
        if p1_id not in points or p2_id not in points:
            return {'success': False, 'reason': 'line points for sacrifice no longer exist'}
        
        # Sacrifice one point, keep the other
        p_to_sac_id, p_to_keep_id = random.choice([(p1_id, p2_id), (p2_id, p1_id)])

        p1_orig = points[p1_id].copy()
        p2_orig = points[p2_id].copy()
        midpoint = points_centroid([p1_orig, p2_orig])

        # --- Perform Sacrifice ---
        # Deleting the point will also remove the line.
        sacrificed_point_data = self.game._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId, allow_regeneration=True)
        if not sacrificed_point_data:
             return {'success': False, 'reason': 'failed to sacrifice line endpoint'}

        # --- Fire Projectiles ---
        destroyed_lines = []
        created_points = []
        attack_rays = []
        
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        team_has_cross_rune = len(self.state.get('runes', {}).get(teamId, {}).get('cross', [])) > 0
        bastion_line_ids = self.game.query.get_bastion_line_ids()

        vx_ext, vy_ext = p2_orig['x'] - p1_orig['x'], p2_orig['y'] - p1_orig['y']
        vectors_to_try = [(vx_ext, vy_ext), (-vy_ext, vx_ext)]

        for vx, vy in vectors_to_try:
            if vx == 0 and vy == 0: continue

            dummy_end_point = {'x': midpoint['x'] + vx, 'y': midpoint['y'] + vy}
            border_point = get_extended_border_point(
                midpoint, dummy_end_point, self.state['grid_size'],
                self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])
            )
            if not border_point: continue
            
            attack_ray_p1 = midpoint
            attack_ray_p2 = border_point

            closest_hit = self.game._find_first_ray_hit(
                attack_ray_p1, attack_ray_p2, enemy_lines,
                can_bypass_shields=team_has_cross_rune, ignored_line_ids=bastion_line_ids
            )

            if closest_hit:
                if closest_hit['target_line'] not in destroyed_lines:
                    self.game._delete_line(closest_hit['target_line'])
                    destroyed_lines.append(closest_hit['target_line'])
                    attack_rays.append({'p1': attack_ray_p1, 'p2': closest_hit['intersection_point']})
                    if closest_hit['target_line'] in enemy_lines:
                        enemy_lines.remove(closest_hit['target_line'])
            else:
                new_point = self.game._helper_spawn_on_border(teamId, border_point)
                if new_point:
                    created_points.append(new_point)
                    attack_rays.append({'p1': attack_ray_p1, 'p2': border_point})

        if not destroyed_lines and not created_points:
            return {
                'success': True,
                'type': 'line_retaliation_fizzle',
                'sacrificed_point': sacrificed_point_data,
                'unraveled_line': line_to_unravel
            }

        return {
            'success': True,
            'type': 'line_retaliation',
            'destroyed_lines': destroyed_lines,
            'created_points': created_points,
            'attack_rays': attack_rays,
            'sacrificed_point': sacrificed_point_data,
            'unraveled_line': line_to_unravel
        }

    def bastion_pulse(self, teamId):
        """[SACRIFICE ACTION]: A bastion sacrifices a prong to destroy crossing enemy lines. If it fizzles, it creates a shockwave."""
        possible_bastions = self.game.query.find_possible_bastion_pulses(teamId)
        if not possible_bastions:
            return {'success': False, 'reason': 'no bastion with crossing lines found'}
        
        bastion_to_pulse = random.choice(possible_bastions)
        bastion_id = bastion_to_pulse['id']
        prong_to_sac_id = random.choice(bastion_to_pulse['prong_ids'])
        
        points_map = self.state['points']
        if prong_to_sac_id not in points_map:
            return {'success': False, 'reason': 'prong point to sacrifice no longer exists'}
            
        sac_point_coords = points_map[prong_to_sac_id].copy()

        # --- Perform sacrifice ---
        # This will also trigger the cleanup logic in game_logic, which may dissolve the bastion.
        sacrificed_point_data = self.game._delete_point_and_connections(prong_to_sac_id, aggressor_team_id=teamId)
        if not sacrificed_point_data:
            return {'success': False, 'reason': 'failed to sacrifice bastion prong'}

        # --- Check for fizzle (bastion was dissolved) ---
        if bastion_id not in self.state.get('bastions', {}):
            # --- Fizzle Effect: Shockwave ---
            blast_radius_sq = (self.state['grid_size'] * 0.15)**2
            points_to_push = list(self.state['points'].values())
            pushed_points = self.game._push_points_in_radius(sac_point_coords, blast_radius_sq, 2.0, points_to_push)
            
            return {
                'success': True,
                'type': 'bastion_pulse_fizzle_shockwave',
                'sacrificed_point': sacrificed_point_data,
                'pushed_points_count': len(pushed_points)
            }
        else:
            # --- Primary Effect: Destroy Crossing Lines ---
            # We need to find them again as the points may have changed.
            remaining_bastion = self.state['bastions'][bastion_id]
            prong_points = [points_map[pid] for pid in remaining_bastion['prong_ids'] if pid in points_map]
            
            lines_destroyed = []
            if len(prong_points) >= 2:
                centroid = points_centroid(prong_points)
                prong_points.sort(key=lambda p: math.atan2(p['y'] - centroid['y'], p['x'] - centroid['x']))
                
                enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
                for enemy_line in enemy_lines:
                    if enemy_line['p1_id'] not in points_map or enemy_line['p2_id'] not in points_map: continue
                    ep1, ep2 = points_map[enemy_line['p1_id']], points_map[enemy_line['p2_id']]
                    
                    for i in range(len(prong_points)):
                        perimeter_p1 = prong_points[i]
                        perimeter_p2 = prong_points[(i + 1) % len(prong_points)]
                        if segments_intersect(ep1, ep2, perimeter_p1, perimeter_p2):
                            lines_destroyed.append(enemy_line)
                            break # Move to next enemy line
            
            for line in set(lines_destroyed): # use set to avoid duplicates
                self.game._delete_line(line)

            return {
                'success': True,
                'type': 'bastion_pulse',
                'sacrificed_point': sacrificed_point_data,
                'lines_destroyed': lines_destroyed,
                'bastion_id': bastion_id
            }

    def attune_nexus(self, teamId):
        """[SACRIFICE ACTION]: Sacrifices a diagonal from a Nexus to energize it for several turns."""
        team_nexuses = self.state.get('runes', {}).get(teamId, {}).get('nexus', [])
        if not team_nexuses: return {'success': False, 'reason': 'no active nexuses'}
        
        attuned_nexus_pids = {frozenset(an['point_ids']) for an in self.state.get('attuned_nexuses', {}).values()}
        unattuned_nexuses = [n for n in team_nexuses if frozenset(n['point_ids']) not in attuned_nexus_pids]
        if not unattuned_nexuses: return {'success': False, 'reason': 'all nexuses are already attuned'}

        # Attune the nexus closest to the enemy centroid
        enemy_points = [p for p in self.state['points'].values() if p['teamId'] != teamId]
        enemy_centroid = points_centroid(enemy_points) if enemy_points else {'x': self.state['grid_size']/2, 'y': self.state['grid_size']/2}
        nexus_to_attune = min(unattuned_nexuses, key=lambda n: distance_sq(n['center'], enemy_centroid))
        points = self.state['points']
        pids = nexus_to_attune['point_ids']
        if not all(pid in points for pid in pids): return {'success': False, 'reason': 'nexus points no longer exist'}
        
        p_list = [points[pid] for pid in pids]
        edge_data = get_edges_by_distance(p_list)
        
        all_team_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.game.query.get_team_lines(teamId)}

        line_to_sac = None
        for d_p1_id, d_p2_id in edge_data['diagonals']:
            diag_key = tuple(sorted((d_p1_id, d_p2_id)))
            if diag_key in all_team_lines_by_points:
                line_to_sac = all_team_lines_by_points[diag_key]
                break
        
        if not line_to_sac: return {'success': False, 'reason': 'nexus is missing its diagonal line'}

        self.game._delete_line(line_to_sac)

        nexus_id = self.game._generate_id('an')
        attuned_nexus = {
            'id': nexus_id, 'teamId': teamId, 'turns_left': 5,
            'center': nexus_to_attune['center'],
            'point_ids': nexus_to_attune['point_ids'],
            'radius_sq': (self.state['grid_size'] * 0.3)**2
        }
        self.state['attuned_nexuses'][nexus_id] = attuned_nexus

        return {
            'success': True, 'type': 'attune_nexus',
            'nexus_id': nexus_id, 'sacrificed_line': line_to_sac, 'attuned_nexus': attuned_nexus
        }



    def build_chronos_spire(self, teamId):
        """[SACRIFICE ACTION]: Sacrifices a Star Rune to build the Chronos Spire Wonder."""
        # A team can only have one wonder.
        if any(w['teamId'] == teamId for w in self.state.get('wonders', {}).values()):
            return {'success': False, 'reason': 'team already has a Wonder'}

        team_star_runes = self.state.get('runes', {}).get(teamId, {}).get('star', [])
        if not team_star_runes:
            return {'success': False, 'reason': 'no active star runes to sacrifice'}
        
        # Sacrifice the smallest star rune, as it's the "cheapest" way to get a wonder
        points_map = self.state['points']
        rune_to_sacrifice = min(team_star_runes, key=lambda r: polygon_area([points_map[pid] for pid in r['cycle_ids'] if pid in points_map]))
        points_map = self.state['points']
        
        # Check if all points of the rune exist before trying to use them
        if not all(pid in points_map for pid in rune_to_sacrifice['all_points']):
            return {'success': False, 'reason': 'star rune points for sacrifice no longer exist'}
        
        # Calculate center for the wonder
        rune_points = [points_map[pid] for pid in rune_to_sacrifice['all_points']]
        wonder_coords = points_centroid(rune_points)

        # --- Sacrifice the rune ---
        sacrificed_points_data = []
        for pid in rune_to_sacrifice['all_points']:
            # The _delete_point_and_connections will also remove connected lines.
            sac_data = self.game._delete_point_and_connections(pid, aggressor_team_id=teamId)
            if sac_data:
                sacrificed_points_data.append(sac_data)

        if len(sacrificed_points_data) == 0:
             return {'success': False, 'reason': 'failed to sacrifice any points for the wonder'}

        # --- Create the Wonder ---
        wonder_id = self.game._generate_id('w')
        new_wonder = {
            'id': wonder_id,
            'teamId': teamId,
            'type': 'ChronosSpire',
            'coords': wonder_coords,
            'turns_to_victory': 10
        }
        self.state['wonders'][wonder_id] = new_wonder

        return {
            'success': True,
            'type': 'build_chronos_spire',
            'wonder': new_wonder,
            'sacrificed_points_count': len(sacrificed_points_data),
            'sacrificed_points': sacrificed_points_data,
        }

    def chain_lightning(self, teamId):
        """[SACRIFICE ACTION]: An I-Rune sacrifices an internal point to destroy the nearest enemy point."""
        team_i_runes = self.state.get('runes', {}).get(teamId, {}).get('i_shape', [])
        possible_runes = [r for r in team_i_runes if r.get('internal_points')]
        if not possible_runes:
            return {'success': False, 'reason': 'no I-Runes with an internal point found'}

        # Use the Conduit that is closest to a vulnerable enemy
        vulnerable_enemies = self.game.query.get_vulnerable_enemy_points(teamId)
        points_map = self.state['points']

        def get_conduit_proximity(conduit_rune):
            if not vulnerable_enemies: return float('inf')
            center = points_centroid([points_map[pid] for pid in conduit_rune['point_ids'] if pid in points_map])
            if not center: return float('inf')
            return min(distance_sq(center, ep) for ep in vulnerable_enemies)
        
        rune = min(possible_runes, key=get_conduit_proximity)
        # Ensure the point to be sacrificed exists
        sac_candidates = [pid for pid in rune.get('internal_points', []) if pid in self.state['points']]
        if not sac_candidates:
            return {'success': False, 'reason': 'I-Rune internal point for sacrifice no longer exists'}
        
        # Sacrifice the most central internal point of the chosen conduit
        internal_points = [points_map[pid] for pid in rune['internal_points'] if pid in points_map]
        if not internal_points:
             return {'success': False, 'reason': 'internal points for sacrifice no longer exist'}
        center = points_centroid(internal_points)
        sac_point = min(internal_points, key=lambda p: distance_sq(p, center))
        p_to_sac_id = sac_point['id']
        p_to_sac = self.state['points'][p_to_sac_id]

        # --- Find Target ---
        vulnerable_enemies = self.game.query.get_vulnerable_enemy_points(teamId)
        if vulnerable_enemies:
            target_point = min(vulnerable_enemies, key=lambda p: distance_sq(p_to_sac, p))
            
            # --- Sacrifice and Primary Effect ---
            sacrificed_point_data = self.game._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId, allow_regeneration=True)
            if not sacrificed_point_data:
                return {'success': False, 'reason': 'failed to sacrifice point for chain lightning'}
            
            destroyed_point_data = self.game._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
            if not destroyed_point_data:
                # Sacrifice happened, but target disappeared.
                return {
                    'success': True, 'type': 'chain_lightning', 'destroyed_team_name': 'Unknown (target vanished)',
                    'sacrificed_point': sacrificed_point_data, 'destroyed_point': None
                }

            destroyed_team_name = self.state['teams'][destroyed_point_data['teamId']]['name']
            return {
                'success': True, 'type': 'chain_lightning',
                'destroyed_team_name': destroyed_team_name,
                'sacrificed_point': sacrificed_point_data,
                'destroyed_point': destroyed_point_data
            }
        else:
            # --- Sacrifice and Fizzle Effect (Mini-Nova) ---
            sacrificed_point_data = self.game._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId, allow_regeneration=True)
            if not sacrificed_point_data:
                return {'success': False, 'reason': 'failed to sacrifice point for fizzle effect'}

            blast_radius_sq = (self.state['grid_size'] * 0.15)**2 # Smaller radius for mini-nova
            
            lines_to_destroy = []
            points_map = self.state['points']
            enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
            
            for line in enemy_lines:
                if not (line['p1_id'] in points_map and line['p2_id'] in points_map): continue
                p1, p2 = points_map[line['p1_id']], points_map[line['p2_id']]
                if distance_sq(sacrificed_point_data, p1) < blast_radius_sq or distance_sq(sacrificed_point_data, p2) < blast_radius_sq:
                    lines_to_destroy.append(line)
            
            for line in lines_to_destroy:
                self.game._delete_line(line)
                
            return {
                'success': True, 'type': 'chain_lightning_fizzle_nova',
                'sacrificed_point': sacrificed_point_data,
                'lines_destroyed_count': len(lines_to_destroy)
            }

    def cultivate_heartwood(self, teamId):
        """[SACRIFICE ACTION]: Sacrifices a central point and its branches to create a Heartwood."""
        candidates = self.game.query.find_heartwood_candidates(teamId)
        if not candidates:
            return {'success': False, 'reason': 'no valid formation for Heartwood found'}

        # Choose the candidate formation whose center is closest to the team's centroid
        team_centroid = self.game.query.get_team_centroid(teamId)
        points_map = self.state['points']
        formation = min(candidates, key=lambda f: distance_sq(points_map[f['center_id']], team_centroid))
        center_id = formation['center_id']
        branch_ids = formation['branch_ids']
        
        # We only need 5 branches, if there are more, pick 5.
        if len(branch_ids) > 5:
            branch_ids = random.sample(branch_ids, 5)

        points_to_sac_ids = [center_id] + branch_ids
        
        # --- Perform Sacrifice ---
        sacrificed_points_data = []
        points_map = self.state['points']
        center_coords_before_sac = points_map[center_id].copy()

        for pid in points_to_sac_ids:
            sac_data = self.game._delete_point_and_connections(pid, aggressor_team_id=teamId)
            if sac_data:
                sacrificed_points_data.append(sac_data)
        
        if len(sacrificed_points_data) == 0:
            return {'success': False, 'reason': 'failed to sacrifice any points for the heartwood'}

        # --- Create Heartwood ---
        heartwood_id = self.game._generate_id('hw')
        new_heartwood = {
            'id': heartwood_id,
            'center_coords': center_coords_before_sac,
            'growth_counter': 0,
            'growth_interval': 5, # Generate a point every 5 turns
            'aura_radius_sq': (self.state['grid_size'] * 0.2)**2
        }
        
        self.state.setdefault('heartwoods', {})[teamId] = new_heartwood
        
        return {
            'success': True,
            'type': 'cultivate_heartwood',
            'heartwood': new_heartwood,
            'sacrificed_points': sacrificed_points_data
        }