import random
import math
from ..geometry import distance_sq, clamp_and_round_point_coords

class SacrificeActionsHandler:
    def __init__(self, game):
        self.game = game

    # --- Action Precondition Checks ---

    def can_perform_nova_burst(self, teamId):
        # Action is possible if either an "ideal" target exists (guaranteeing primary effect)
        # or if a "non-critical" point exists to sacrifice for the fallback effect.
        has_ideal_target = len(self._find_possible_nova_bursts(teamId)) > 0
        has_fallback_target = self.game._find_non_critical_sacrificial_point(teamId) is not None
        can_perform = has_ideal_target or has_fallback_target
        return can_perform, "No suitable point to sacrifice for Nova Burst."

    def can_perform_create_whirlpool(self, teamId):
        return len(self.game.get_team_point_ids(teamId)) > 1, "Requires more than 1 point to sacrifice one."

    def can_perform_phase_shift(self, teamId):
        return len(self.game.get_team_lines(teamId)) > 0, "Requires a line to sacrifice."

    def can_perform_rift_trap(self, teamId):
        return len(self.game.get_team_point_ids(teamId)) > 1, "Requires more than 1 point to sacrifice."

    def can_perform_scorch_territory(self, teamId):
        can_perform = any(t['teamId'] == teamId for t in self.state.get('territories', []))
        return can_perform, "Requires at least one claimed territory to sacrifice."

    # --- End Precondition Checks ---

    @property
    def state(self):
        """Provides direct access to the game's current state dictionary."""
        return self.game.state

    def _find_possible_nova_bursts(self, teamId):
        """Finds non-critical points that are also 'ideal' for a nova burst (i.e., have an enemy line in range)."""
        # First, find all points that are eligible for sacrifice at all.
        critical_pids = self.game._get_critical_structure_point_ids(teamId)
        all_team_pids = self.game.get_team_point_ids(teamId)
        non_critical_pids = [pid for pid in all_team_pids if pid not in critical_pids]

        if len(non_critical_pids) == 0:
            return []

        blast_radius_sq = (self.state['grid_size'] * 0.25)**2
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        if not enemy_lines:
            return []

        points = self.state['points']
        bastion_line_ids = self.game._get_bastion_line_ids()
        
        ideal_sac_points = []
        for pid in non_critical_pids:
            if pid not in points: continue # Defensive check
            sac_point_coords = points[pid]
            
            for line in enemy_lines:
                if line.get('id') in bastion_line_ids: continue
                if not (line['p1_id'] in points and line['p2_id'] in points): continue
                
                p1 = points[line['p1_id']]
                p2 = points[line['p2_id']]

                if distance_sq(sac_point_coords, p1) < blast_radius_sq or distance_sq(sac_point_coords, p2) < blast_radius_sq:
                    ideal_sac_points.append(pid)
                    # Found a target for this point, no need to check other lines for it.
                    break 
        return ideal_sac_points

    def nova_burst(self, teamId):
        """[SACRIFICE ACTION]: A point is destroyed. If near enemy lines, it destroys them. Otherwise, it pushes all nearby points away."""
        # Find ideal sacrifice points (guarantee primary effect)
        ideal_sac_points = self._find_possible_nova_bursts(teamId)
        
        sac_point_id = None
        if ideal_sac_points:
            sac_point_id = random.choice(ideal_sac_points)
        else:
            # If no ideal point, find a non-critical point for the fallback effect.
            sac_point_id = self.game._find_non_critical_sacrificial_point(teamId)

        if not sac_point_id or sac_point_id not in self.state['points']:
            return {'success': False, 'reason': 'no suitable point found to sacrifice'}

        sac_point_coords = self.state['points'][sac_point_id].copy()
        blast_radius_sq = (self.state['grid_size'] * 0.25)**2

        # --- Perform Sacrifice ---
        self.game._delete_point_and_connections(sac_point_id, aggressor_team_id=teamId)
        
        # --- Check for Primary Effect (Line Destruction) ---
        lines_to_remove_by_proximity = []
        points_to_check = self.state['points']
        bastion_line_ids = self.game._get_bastion_line_ids()
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
        if len(self.game.get_team_point_ids(teamId)) <= 1:
            return {'success': False, 'reason': 'not enough points to sacrifice'}

        p_to_sac_id = self.game._find_non_critical_sacrificial_point(teamId)
        if not p_to_sac_id:
            return {'success': False, 'reason': 'no non-critical points available to sacrifice'}
        sac_point_coords = self.state['points'][p_to_sac_id].copy()
        
        # Check for nearby points BEFORE sacrificing to decide the outcome
        whirlpool_radius_sq = (self.state['grid_size'] * 0.3)**2
        has_targets = any(
            p['id'] != p_to_sac_id and distance_sq(sac_point_coords, p) < whirlpool_radius_sq
            for p in self.state['points'].values()
        )

        # --- Perform Sacrifice ---
        sacrificed_point_data = self.game._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
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

    def _get_eligible_phase_shift_lines(self, teamId):
        """Helper to find lines eligible for phase shift sacrifice."""
        team_lines = self.game.get_team_lines(teamId)
        team_point_ids = self.game.get_team_point_ids(teamId)
        
        adj_degree = {pid: 0 for pid in team_point_ids}
        for line in team_lines:
            if line['p1_id'] in adj_degree: adj_degree[line['p1_id']] += 1
            if line['p2_id'] in adj_degree: adj_degree[line['p2_id']] += 1

        fortified_point_ids = self.game._get_fortified_point_ids()
        bastion_point_ids = self.game._get_bastion_point_ids()
        monolith_point_ids = {pid for m in self.state.get('monoliths', {}).values() for pid in m.get('point_ids', [])}
        nexus_point_ids = {pid for nexus_list in self.state.get('nexuses', {}).values() for nexus in nexus_list for pid in nexus.get('point_ids', [])}
        critical_point_ids = fortified_point_ids.union(
            bastion_point_ids['cores'], bastion_point_ids['prongs'],
            monolith_point_ids, nexus_point_ids
        )

        eligible_lines = [
            line for line in team_lines
            if adj_degree.get(line['p1_id'], 0) > 1 and \
               adj_degree.get(line['p2_id'], 0) > 1 and \
               line['p1_id'] not in critical_point_ids and \
               line['p2_id'] not in critical_point_ids
        ]
        if not eligible_lines:
            eligible_lines = [
                line for line in team_lines
                if line['p1_id'] not in critical_point_ids and line['p2_id'] not in critical_point_ids
            ]
        if not eligible_lines and len(team_point_ids) > 3:
            eligible_lines = team_lines
        
        return eligible_lines

    def phase_shift(self, teamId):
        """[SACRIFICE ACTION]: Sacrifice a line to teleport one of its points. If teleport fails, the other point becomes a temporary anchor."""
        team_lines = self.game.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to sacrifice'}

        eligible_lines = self._get_eligible_phase_shift_lines(teamId)
        if not eligible_lines:
            return {'success': False, 'reason': 'no non-critical/safe lines to sacrifice'}

        line_to_sac = random.choice(eligible_lines)
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
        if len(self.game.get_team_point_ids(teamId)) <= 1:
            return {'success': False, 'reason': 'not enough points to sacrifice'}

        # Find a non-critical point to sacrifice
        p_to_sac_id = self.game._find_non_critical_sacrificial_point(teamId)
        if not p_to_sac_id:
            return {'success': False, 'reason': 'no non-critical points available to sacrifice'}
        sac_point_coords = self.state['points'][p_to_sac_id].copy()
        
        # Perform Sacrifice
        sacrificed_point_data = self.game._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
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
        
        territory_to_scorch = random.choice(team_territories)
        
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