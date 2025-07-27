import math
import random
from itertools import combinations
from .geometry import (
    distance_sq, get_extended_border_point, is_ray_blocked,
    polygon_area, points_centroid
)
from . import game_data

class GameStateQuery:
    """
    A class dedicated to read-only operations and queries on the game state.
    It provides a clean interface for action handlers and other parts of the game
    to get information about the current state without modifying it.
    """
    def __init__(self, game):
        self.game = game

    @property
    def state(self):
        return self.game.state

    # --- Core State Getters ---

    def get_team_point_ids(self, teamId):
        """Returns IDs of points belonging to a team."""
        return [pid for pid, p in list(self.state['points'].items()) if p['teamId'] == teamId]

    def get_team_lines(self, teamId):
        """Returns lines belonging to a team."""
        return [l for l in self.state['lines'] if l['teamId'] == teamId]

    # --- Structure & Point Status Queries ---

    def get_fortified_point_ids(self):
        """Returns a set of all point IDs that are part of any claimed territory."""
        return {pid for t in self.state.get('territories', []) for pid in t['point_ids']}

    def is_line_energized(self, line):
        """Checks if a line is within range of a friendly Attuned Nexus."""
        if not self.state.get('attuned_nexuses'):
            return False
        
        if line['p1_id'] not in self.state['points'] or line['p2_id'] not in self.state['points']:
            return False
            
        p1 = self.state['points'][line['p1_id']]
        p2 = self.state['points'][line['p2_id']]
        midpoint = points_centroid([p1, p2])

        for nexus in self.state['attuned_nexuses'].values():
            if nexus['teamId'] == line['teamId']:
                if distance_sq(midpoint, nexus['center']) < nexus['radius_sq']:
                    return True
        return False

    def get_bastion_point_ids(self):
        """Returns a dict of bastion core and prong point IDs."""
        bastions = self.state.get('bastions', {}).values()
        core_ids = {b['core_id'] for b in bastions if 'core_id' in b}
        prong_ids = {pid for b in bastions if 'prong_ids' in b for pid in b['prong_ids']}
        return {'cores': core_ids, 'prongs': prong_ids}

    def get_bastion_line_ids(self):
        """Returns a set of line IDs that are part of any bastion."""
        bastion_lines = set()
        all_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l['id'] for l in self.state['lines']}

        for bastion in self.state.get('bastions', {}).values():
            core_id = bastion['core_id']
            for prong_id in bastion['prong_ids']:
                line_key = tuple(sorted((core_id, prong_id)))
                if line_key in all_lines_by_points:
                    bastion_lines.add(all_lines_by_points[line_key])
        return bastion_lines

    def get_all_immune_point_ids(self):
        """Returns a set of all point IDs that are currently immune to standard attacks."""
        fortified_point_ids = self.get_fortified_point_ids()
        bastion_point_ids = self.get_bastion_point_ids()
        stasis_point_ids = set(self.state.get('stasis_points', {}).keys())
        return fortified_point_ids.union(
            bastion_point_ids['cores'], bastion_point_ids['prongs'], stasis_point_ids
        )

    def get_vulnerable_enemy_points(self, teamId, immune_point_ids=None):
        """
        Returns a list of enemy points that are not immune to standard attacks.
        Can accept a pre-calculated set of immune point IDs for optimization.
        """
        if immune_point_ids is None:
            immune_point_ids = self.get_all_immune_point_ids()
        return [p for p in self.state['points'].values() if p['teamId'] != teamId and p['id'] not in immune_point_ids]
    
    def get_critical_structure_point_ids(self, teamId):
        """Returns a set of point IDs that are part of critical structures for a team, using the structure registry."""
        critical_pids = set()
        from . import structure_data # Local import to avoid circular dependency at module level
        
        for definition in structure_data.STRUCTURE_DEFINITIONS.values():
            if not definition.get('is_critical'):
                continue
            
            if definition['storage_type'] == 'dict_keyed_by_pid':
                for pid, data in self.game._iterate_structures(definition, teamId):
                    critical_pids.add(pid)
                continue

            for struct in self.game._iterate_structures(definition, teamId):
                pids = self.game._get_pids_from_struct(struct, definition.get('point_id_keys', []))
                critical_pids.update(pids)
        
        return critical_pids

    # --- Graph & Topology Queries ---

    def get_team_adjacency_list(self, teamId):
        """Builds and returns an adjacency list for a team's graph by calling the formation manager."""
        return self.game.formation_manager.get_adjacency_list(
            self.get_team_point_ids(teamId),
            self.get_team_lines(teamId)
        )

    def get_team_degrees(self, teamId):
        """Calculates point degrees for a team's graph by calling the formation manager."""
        return self.game.formation_manager.get_degrees(
            self.get_team_point_ids(teamId),
            self.get_team_lines(teamId)
        )

    def find_articulation_points(self, teamId):
        """Finds all articulation points (cut vertices) for a team's graph. Returns (points, adj_list)."""
        team_point_ids = self.get_team_point_ids(teamId)
        adj = self.get_team_adjacency_list(teamId)
        
        if len(team_point_ids) < 3:
            return [], adj

        tin, low, timer, visited, articulation_points = {}, {}, 0, set(), set()

        def dfs(v, p=None):
            nonlocal timer
            visited.add(v)
            tin[v] = low[v] = timer
            timer += 1
            children = 0
            for to in adj.get(v, set()):
                if to == p: continue
                if to in visited:
                    low[v] = min(low[v], tin[to])
                else:
                    dfs(to, v)
                    low[v] = min(low[v], low[to])
                    if low[to] >= tin[v] and p is not None: articulation_points.add(v)
                    children += 1
            if p is None and children > 1: articulation_points.add(v)

        for pid in team_point_ids:
            if pid not in visited: dfs(pid)
        
        return list(articulation_points), adj

    # --- Action-Specific Pre-computation Queries ---

    def find_possible_extensions(self, teamId):
        """Finds all possible line extensions to the border."""
        def check_and_add_extension(p_start, p_end, origin_point_id, teamId, extensions_list):
            border_point = get_extended_border_point(
                p_start, p_end, self.state['grid_size'],
                self.state.get('fissures', []), self.state.get('barricades', []), self.state.get('scorched_zones', [])
            )
            if border_point:
                is_valid, _ = self.game.is_spawn_location_valid(border_point, teamId)
                if is_valid: extensions_list.append({'origin_point_id': origin_point_id, 'border_point': border_point})
        
        possible_extensions = []
        for line in self.get_team_lines(teamId):
            if line['p1_id'] not in self.state['points'] or line['p2_id'] not in self.state['points']: continue
            p1, p2 = self.state['points'][line['p1_id']], self.state['points'][line['p2_id']]
            check_and_add_extension(p1, p2, p2['id'], teamId, possible_extensions)
            check_and_add_extension(p2, p1, p1['id'], teamId, possible_extensions)
        return possible_extensions

    def find_fracturable_lines(self, teamId):
        """Finds all lines that are eligible for fracturing."""
        territory_line_keys = self.game._get_all_territory_boundary_line_keys(teamId)
        fracturable_lines = []
        for line in self.get_team_lines(teamId):
            if tuple(sorted((line['p1_id'], line['p2_id']))) in territory_line_keys: continue
            if line['p1_id'] in self.state['points'] and line['p2_id'] in self.state['points']:
                p1, p2 = self.state['points'][line['p1_id']], self.state['points'][line['p2_id']]
                if distance_sq(p1, p2) >= game_data.GAME_PARAMETERS['FRACTURE_LINE_MIN_LENGTH_SQ']:
                    fracturable_lines.append(line)
        return fracturable_lines
    
    def get_large_territories(self, teamId):
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        if not team_territories: return []
        points_map = self.state['points']
        MIN_AREA = game_data.GAME_PARAMETERS['TERRITORY_STRIKE_MIN_AREA']
        large_territories = []
        for territory in team_territories:
            p_ids = territory['point_ids']
            if all(pid in points_map for pid in p_ids):
                triangle_points = [points_map[pid] for pid in p_ids]
                if len(triangle_points) == 3 and polygon_area(triangle_points) >= MIN_AREA:
                    large_territories.append(territory)
        return large_territories

    def find_claimable_triangles(self, teamId):
        """Finds all triangles for a team that have not yet been claimed."""
        all_triangles = self.game.formation_manager._find_all_triangles(self.get_team_point_ids(teamId), self.get_team_lines(teamId))
        if not all_triangles: return []
        claimed_triangles = {tuple(sorted(t['point_ids'])) for t in self.state.get('territories', [])}
        return list(all_triangles - claimed_triangles)

    def find_possible_bastions(self, teamId):
        fortified_point_ids = self.get_fortified_point_ids()
        if not fortified_point_ids: return []
        adj = self.get_team_adjacency_list(teamId)
        used_points = self.get_bastion_point_ids()['cores'].union(self.get_bastion_point_ids()['prongs'])
        possible_bastions = []
        for core_candidate_id in fortified_point_ids:
            if core_candidate_id not in self.get_team_point_ids(teamId) or core_candidate_id in used_points: continue
            prong_candidates = [pid for pid in adj.get(core_candidate_id, set()) if pid not in fortified_point_ids and pid not in used_points]
            if len(prong_candidates) >= 3: possible_bastions.append({'core_id': core_candidate_id, 'prong_ids': prong_candidates})
        return possible_bastions

    def has_sacrificial_point(self, teamId):
        """A cheaper check if any sacrificial point exists, without finding the specific one."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) <= 2: return False
        critical_pids = self.get_critical_structure_point_ids(teamId)
        return any(pid not in critical_pids for pid in team_point_ids)

    def find_heartwood_candidates(self, teamId):
        if teamId in self.state.get('heartwoods', {}): return [] # Can only have one heartwood
        adj = self.get_team_adjacency_list(teamId)
        return [{'center_id': pid, 'branch_ids': list(neighbors)} for pid, neighbors in adj.items() if len(neighbors) >= 5]

    def find_possible_nova_bursts(self, teamId):
        """Finds non-critical points that are also 'ideal' for a nova burst (i.e., have an enemy line in range)."""
        non_critical_pids = [pid for pid in self.get_team_point_ids(teamId) if pid not in self.get_critical_structure_point_ids(teamId)]
        if not non_critical_pids: return []
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        if not enemy_lines: return []
        
        blast_radius_sq = (self.state['grid_size'] * 0.25)**2
        points = self.state['points']
        bastion_line_ids = self.get_bastion_line_ids()
        
        ideal_sac_points = []
        for pid in non_critical_pids:
            if pid not in points: continue
            sac_point_coords = points[pid]
            for line in enemy_lines:
                if line.get('id') in bastion_line_ids: continue
                if not (line['p1_id'] in points and line['p2_id'] in points): continue
                p1, p2 = points[line['p1_id']], points[line['p2_id']]
                if distance_sq(sac_point_coords, p1) < blast_radius_sq or distance_sq(sac_point_coords, p2) < blast_radius_sq:
                    ideal_sac_points.append(pid)
                    break
        return ideal_sac_points

    def get_eligible_phase_shift_lines(self, teamId):
        adj_degree = self.get_team_degrees(teamId)
        critical_point_ids = self.get_critical_structure_point_ids(teamId)
        eligible_lines = [l for l in self.get_team_lines(teamId) if adj_degree.get(l['p1_id'], 0) > 1 and adj_degree.get(l['p2_id'], 0) > 1 and l['p1_id'] not in critical_point_ids and l['p2_id'] not in critical_point_ids]
        if not eligible_lines:
            eligible_lines = [l for l in self.get_team_lines(teamId) if l['p1_id'] not in critical_point_ids and l['p2_id'] not in critical_point_ids]
        if not eligible_lines and len(self.get_team_point_ids(teamId)) > 3:
            eligible_lines = self.get_team_lines(teamId)
        return eligible_lines

    def find_possible_bastion_pulses(self, teamId):
        team_bastions = [b for b in self.state.get('bastions', {}).values() if b['teamId'] == teamId and len(b['prong_ids']) > 0]
        if not team_bastions: return []
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        if not enemy_lines: return []
        
        from .geometry import segments_intersect
        points_map = self.state['points']
        possible_pulses = []
        for bastion in team_bastions:
            prong_points = [points_map[pid] for pid in bastion['prong_ids'] if pid in points_map]
            if len(prong_points) < 2: continue
            centroid = points_centroid(prong_points)
            prong_points.sort(key=lambda p: math.atan2(p['y'] - centroid['y'], p['x'] - centroid['x']))
            has_crossing_line = False
            for enemy_line in enemy_lines:
                if enemy_line['p1_id'] not in points_map or enemy_line['p2_id'] not in points_map: continue
                ep1, ep2 = points_map[enemy_line['p1_id']], points_map[enemy_line['p2_id']]
                for i in range(len(prong_points)):
                    if segments_intersect(ep1, ep2, prong_points[i], prong_points[(i + 1) % len(prong_points)]):
                        possible_pulses.append(bastion)
                        has_crossing_line = True
                        break
                if has_crossing_line: break
        return possible_pulses

    def find_rift_spire_candidates(self, teamId):
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        if len(team_territories) < 3: return []
        vertex_counts = {}
        for territory in team_territories:
            for pid in territory.get('point_ids', []):
                vertex_counts[pid] = vertex_counts.get(pid, 0) + 1
        existing_spire_pids = {spire['point_id'] for spire in self.state.get('rift_spires', {}).values()}
        return [pid for pid, count in vertex_counts.items() if count >= 3 and pid not in existing_spire_pids]

    def find_repositionable_point(self, teamId):
        """
        Finds a point that can be freely moved without breaking critical formations.
        Returns a point_id or None. Prefers the point furthest from the team's center.
        """
        team_point_ids = self.get_team_point_ids(teamId)
        if not team_point_ids: return None
        critical_pids = self.get_critical_structure_point_ids(teamId)
        repositionable_pids = [pid for pid in team_point_ids if pid not in critical_pids]
        if not repositionable_pids: return None

        # Choose the point furthest from the team's centroid to move, to bring it back in.
        team_centroid = self.get_team_centroid(teamId)
        if not team_centroid: return repositionable_pids[0]
        points_map = self.state['points']
        return max(repositionable_pids, key=lambda pid: distance_sq(points_map[pid], team_centroid))

    def find_non_critical_sacrificial_point(self, teamId):
        """
        Finds a point that can be sacrificed without crippling the team.
        Returns a point_id or None.
        """
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) <= 2: return None
        critical_structure_pids = self.get_critical_structure_point_ids(teamId)
        candidate_pids = [pid for pid in team_point_ids if pid not in critical_structure_pids]
        if not candidate_pids: return None
        articulation_points, adj = self.find_articulation_points(teamId)
        articulation_point_pids = set(articulation_points)
        safe_candidates = [pid for pid in candidate_pids if pid not in articulation_point_pids]
        if not safe_candidates: safe_candidates = candidate_pids
        if not safe_candidates: return None
        # Prioritize sacrificing the point with the lowest degree (fewest connections)
        safe_candidates.sort(key=lambda pid: len(adj.get(pid, [])))
        return safe_candidates[0]