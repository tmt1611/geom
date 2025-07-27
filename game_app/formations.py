import math
from itertools import combinations
from .geometry import (distance_sq, get_isosceles_triangle_info, is_rectangle,
                       is_parallelogram, orientation, is_point_in_polygon,
                       get_edges_by_distance)

class FormationManager:
    """
    A stateless manager responsible for detecting geometric formations (Runes, Structures)
    from the game state. It operates on data passed to its methods.
    """
    def __init__(self):
        pass # This manager is stateless.

    def get_adjacency_list(self, team_point_ids, team_lines):
        """Builds an adjacency list (pid -> set of neighbor pids)."""
        adj = {pid: set() for pid in team_point_ids}
        for line in team_lines:
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])
        return adj

    def get_degrees(self, team_point_ids, team_lines):
        """Calculates the degree for each point (number of connected lines)."""
        adj = self.get_adjacency_list(team_point_ids, team_lines)
        return {pid: len(neighbors) for pid, neighbors in adj.items()}

    def check_nexuses(self, team_point_ids, team_lines, all_points):
        """Checks for Nexus formations (a square of points with outer lines and one diagonal)."""
        if len(team_point_ids) < 4:
            return []

        existing_lines = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in team_lines}
        nexuses = []

        for rect_data in self.find_all_rectangles(team_point_ids, team_lines, all_points):
            # Nexus needs to be a square
            if abs(rect_data['aspect_ratio'] - 1.0) < 0.05:
                edge_data = get_edges_by_distance(rect_data['points'])
                # Nexus needs at least one diagonal line
                if any(tuple(sorted(pair)) in existing_lines for pair in edge_data['diagonals']):
                    center_x = sum(p['x'] for p in rect_data['points']) / 4
                    center_y = sum(p['y'] for p in rect_data['points']) / 4
                    nexuses.append({'point_ids': rect_data['point_ids'], 'center': {'x': center_x, 'y': center_y}})
        return nexuses

    def find_all_rectangles(self, team_point_ids, team_lines, all_points):
        """
        A helper generator to find all unique rectangles in a team's structure.
        This is a common pattern for multiple formation checks. It ensures the 4 points
        form a rectangle geometrically and that all 4 side lines exist.
        Yields a dictionary containing point IDs, the list of points, and aspect ratio.
        """
        adj = self.get_adjacency_list(team_point_ids, team_lines)
        
        checked_quads = set()
        # Iterate through points to find potential right-angle corners
        for p1_id in team_point_ids:
            if len(adj.get(p1_id, [])) < 2:
                continue
            
            p1 = all_points[p1_id]
            neighbors_of_p1 = list(adj[p1_id])

            # Check pairs of neighbors for a right angle
            for i in range(len(neighbors_of_p1)):
                for j in range(i + 1, len(neighbors_of_p1)):
                    p2_id, p3_id = neighbors_of_p1[i], neighbors_of_p1[j]
                    
                    p2, p3 = all_points[p2_id], all_points[p3_id]
                    v1 = {'x': p2['x'] - p1['x'], 'y': p2['y'] - p1['y']}
                    v2 = {'x': p3['x'] - p1['x'], 'y': p3['y'] - p1['y']}
                    # Check for a right angle at p1 with dot product (tolerance)
                    if abs(v1['x'] * v2['x'] + v1['y'] * v2['y']) > 0.1:
                        continue

                    # Potential rectangle found, calculate expected p4
                    # p4 = p1 + (p2-p1) + (p3-p1) = p2 + p3 - p1
                    p4_coords = {'x': p2['x'] + p3['x'] - p1['x'], 'y': p2['y'] + p3['y'] - p1['y']}
                    
                    # Find a point close to p4_coords that completes the quad
                    p4_id = None
                    # The fourth point must be connected to both p2 and p3
                    p4_candidates = adj.get(p2_id, set()).intersection(adj.get(p3_id, set()))
                    for pid_candidate in p4_candidates:
                        if pid_candidate != p1_id:
                            p_candidate = all_points.get(pid_candidate)
                            # Check if the candidate point is where we expect it
                            if p_candidate and distance_sq(p_candidate, p4_coords) < 0.5:
                                p4_id = pid_candidate
                                break
                    
                    if p4_id:
                        p_ids_tuple = tuple(sorted((p1_id, p2_id, p3_id, p4_id)))
                        if p_ids_tuple in checked_quads:
                            continue
                        checked_quads.add(p_ids_tuple)
                        
                        p_list = [p1, p2, p3, all_points[p4_id]]
                        is_rect, aspect_ratio = is_rectangle(*p_list)

                        if is_rect:
                            yield {
                                'point_ids': list(p_ids_tuple),
                                'points': p_list,
                                'aspect_ratio': aspect_ratio
                            }

    def check_i_rune(self, team_point_ids, team_lines, all_points):
        """Finds I-Runes: a line of 3 or more collinear points, connected by lines."""
        if len(team_point_ids) < 3:
            return []

        adj = self.get_adjacency_list(team_point_ids, team_lines)
        
        i_runes = []
        endpoints = {pid for pid, neighbors in adj.items() if len(neighbors) == 1}
        visited_in_a_path = set()

        for start_pid in endpoints:
            if start_pid in visited_in_a_path: continue
            
            path = [start_pid]
            visited_in_a_path.add(start_pid)
            
            curr_pid, prev_pid = start_pid, None

            while True:
                neighbors = adj.get(curr_pid, set())
                next_candidates = [nid for nid in neighbors if nid != prev_pid]
                
                if len(next_candidates) != 1: break
                
                next_pid = next_candidates[0]
                if len(path) >= 2:
                    p1, p2, p3 = all_points.get(path[-2]), all_points.get(path[-1]), all_points.get(next_pid)
                    if not p1 or not p2 or not p3 or orientation(p1, p2, p3) != 0: break
                
                if next_pid in visited_in_a_path: break

                path.append(next_pid)
                visited_in_a_path.add(next_pid)
                prev_pid, curr_pid = curr_pid, next_pid

            if len(path) >= 3:
                i_runes.append({'point_ids': path, 'endpoints': [path[0], path[-1]], 'internal_points': path[1:-1]})
        return i_runes

    def check_barricade_rune(self, team_point_ids, team_lines, all_points):
        """Finds Barricade Runes: a rectangle with all four sides present as lines."""
        if len(team_point_ids) < 4: return []
        
        # The find_all_rectangles method already ensures the 4 side lines exist.
        return [rect['point_ids'] for rect in self.find_all_rectangles(team_point_ids, team_lines, all_points)]

    def _find_all_triangles(self, team_point_ids, team_lines):
        """Finds all triangles (as tuples of point IDs) for a given set of points and lines."""
        if len(team_point_ids) < 3:
            return set()

        adj = self.get_adjacency_list(team_point_ids, team_lines)

        all_triangles = set()
        sorted_point_ids = sorted(list(team_point_ids))
        for i in sorted_point_ids:
            for j in adj.get(i, set()):
                if j > i:
                    for k in adj.get(j, set()):
                        if k > j and k in adj.get(i, set()):
                            all_triangles.add(tuple(sorted((i, j, k))))
        return all_triangles

    def check_v_rune(self, team_point_ids, team_lines, all_points):
        """Finds all 'V' shapes for a team."""
        adj_lines = {pid: [] for pid in team_point_ids}
        for line in team_lines:
            if line['p1_id'] in adj_lines and line['p2_id'] in adj_lines:
                adj_lines[line['p1_id']].append(line)
                adj_lines[line['p2_id']].append(line)

        v_runes = []
        for vertex_id, connected_lines in adj_lines.items():
            if len(connected_lines) < 2: continue

            for line1, line2 in combinations(connected_lines, 2):
                leg1_id = line1['p1_id'] if line1['p2_id'] == vertex_id else line1['p2_id']
                leg2_id = line2['p1_id'] if line2['p2_id'] == vertex_id else line2['p2_id']

                p_vertex = all_points.get(vertex_id)
                p_leg1 = all_points.get(leg1_id)
                p_leg2 = all_points.get(leg2_id)
                if not all([p_vertex, p_leg1, p_leg2]):
                    continue

                len1_sq = distance_sq(p_vertex, p_leg1)
                len2_sq = distance_sq(p_vertex, p_leg2)

                if len1_sq > 0 and len2_sq > 0 and 0.8 < (len1_sq / len2_sq) < 1.2:
                    v_runes.append({'vertex_id': vertex_id, 'leg1_id': leg1_id, 'leg2_id': leg2_id})
        return v_runes

    def check_shield_rune(self, team_point_ids, team_lines, all_points):
        """Finds Shield Runes: a triangle with another friendly point inside."""
        if len(team_point_ids) < 4: return []
        
        used_points, shield_runes = set(), []

        all_triangles_pids = self._find_all_triangles(team_point_ids, team_lines)

        for tri_ids in all_triangles_pids:
            if any(pid in used_points for pid in tri_ids): continue
            
            tri_points = [all_points.get(pid) for pid in tri_ids]
            if not all(tri_points): continue
            p1, p2, p3 = tri_points
            
            other_point_ids = [pid for pid in team_point_ids if pid not in tri_ids and pid not in used_points]
            
            for core_id in other_point_ids:
                p_core = all_points.get(core_id)
                if not p_core: continue
                if is_point_in_polygon(p_core, [p1, p2, p3]):
                    rune_points = set(tri_ids) | {core_id}
                    shield_runes.append({'triangle_ids': list(tri_ids), 'core_id': core_id})
                    used_points.update(rune_points)
                    break 
        return shield_runes
    
    def check_star_rune(self, team_point_ids, team_lines, all_points):
        """Finds all 'Star' runes for a team."""
        return self._find_star_formations(team_point_ids, team_lines, all_points, min_cycle=5, max_cycle=6)

    def _find_star_formations(self, team_point_ids, team_lines, all_points, min_cycle=5, max_cycle=6):
        """Finds "star" formations for a team."""
        if len(team_point_ids) < min_cycle + 1: return []
        
        adj = {pid: set() for pid in team_point_ids}
        for line in team_lines:
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])

        found_stars, used_points = [], set()

        for center_candidate_id in team_point_ids:
            if center_candidate_id in used_points: continue
            neighbors = list(adj.get(center_candidate_id, set()))
            if len(neighbors) < min_cycle: continue

            for cycle_len in range(min_cycle, max_cycle + 1):
                if len(neighbors) < cycle_len: continue
                
                for cycle_candidate_ids in combinations(neighbors, cycle_len):
                    sub_adj = {pid: [opid for opid in adj.get(pid, set()) if opid in cycle_candidate_ids] for pid in cycle_candidate_ids}
                    if not all(len(sub_adj[pid]) == 2 for pid in cycle_candidate_ids): continue

                    start_node, ordered_cycle, prev_node = cycle_candidate_ids[0], [], None
                    curr_node = start_node
                    is_valid_cycle = True
                    
                    while len(ordered_cycle) < cycle_len:
                        ordered_cycle.append(curr_node)
                        next_node_options = [n for n in sub_adj[curr_node] if n != prev_node]
                        if not next_node_options or (len(ordered_cycle) < cycle_len and not next_node_options):
                            is_valid_cycle = False; break
                        prev_node, curr_node = curr_node, next_node_options[0] if next_node_options else start_node
                    
                    if not is_valid_cycle or len(ordered_cycle) != cycle_len or curr_node != start_node: continue
                    
                    all_star_points = set(ordered_cycle) | {center_candidate_id}
                    if not used_points.intersection(all_star_points):
                        found_stars.append({'center_id': center_candidate_id, 'cycle_ids': ordered_cycle, 'all_points': list(all_star_points)})
                        used_points.update(all_star_points)
                        break
                if center_candidate_id in used_points: break
        return found_stars

    def check_trident_rune(self, team_point_ids, team_lines, all_points):
        """Finds Trident Runes."""
        if len(team_point_ids) < 4: return []

        adj = self.get_adjacency_list(team_point_ids, team_lines)
        existing_lines_set = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in team_lines}

        trident_runes, used_points = [], set()

        for p_ids_tuple in combinations(team_point_ids, 3):
            points_to_check = [all_points.get(pid) for pid in p_ids_tuple]
            if not all(points_to_check): continue
            p1, p2, p3 = points_to_check
            iso_info = get_isosceles_triangle_info(p1, p2, p3)
            if not iso_info: continue
                
            p_apex, p_base = iso_info['apex'], iso_info['base']
            if not (tuple(sorted((p_apex['id'], p_base[0]['id']))) in existing_lines_set and tuple(sorted((p_apex['id'], p_base[1]['id']))) in existing_lines_set):
                continue
            
            for handle_candidate_id in adj.get(p_apex['id'], set()):
                if handle_candidate_id in (p_base[0]['id'], p_base[1]['id']): continue
                
                p_handle = all_points.get(handle_candidate_id)
                if not p_handle: continue
                base_midpoint_x, base_midpoint_y = (p_base[0]['x'] + p_base[1]['x']) / 2, (p_base[0]['y'] + p_base[1]['y']) / 2
                
                val = (p_apex['y'] - p_handle['y']) * (base_midpoint_x - p_apex['x']) - (p_apex['x'] - p_handle['x']) * (base_midpoint_y - p_apex['y'])
                if abs(val) > 0.1: continue

                v_apex_handle = (p_handle['x'] - p_apex['x'], p_handle['y'] - p_apex['y'])
                v_apex_mid = (base_midpoint_x - p_apex['x'], base_midpoint_y - p_apex['y'])
                if v_apex_handle[0] * v_apex_mid[0] + v_apex_handle[1] * v_apex_mid[1] < 0:
                    rune_points = {p_apex['id'], p_base[0]['id'], p_base[1]['id'], p_handle['id']}
                    if not used_points.intersection(rune_points):
                        trident_runes.append({'apex_id': p_apex['id'], 'prong_ids': [p_base[0]['id'], p_base[1]['id']], 'handle_id': p_handle['id']})
                        used_points.update(rune_points)
                        break
        return trident_runes

    def check_cross_rune(self, team_point_ids, team_lines, all_points):
        """Finds all 'Cross' runes."""
        if len(team_point_ids) < 4: return []
        
        existing_lines = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in team_lines}
        cross_runes, checked_quads = [], set()

        for p_ids_tuple in combinations(team_point_ids, 4):
            # Sort to ensure we only check each unique combination once
            sorted_p_ids = tuple(sorted(p_ids_tuple))
            if sorted_p_ids in checked_quads: continue
            checked_quads.add(sorted_p_ids)
            
            p_list = [all_points.get(pid) for pid in p_ids_tuple]
            if not all(p_list): continue
            is_rect, _ = is_rectangle(*p_list)
            if not is_rect: continue
            
            edge_data = get_edges_by_distance(p_list)
            diag1_pair, diag2_pair = edge_data['diagonals']

            if tuple(sorted(diag1_pair)) in existing_lines and tuple(sorted(diag2_pair)) in existing_lines:
                cross_runes.append(list(p_ids_tuple))
        return cross_runes

    def check_t_rune(self, team_point_ids, team_lines, all_points):
        """Finds T-Runes."""
        if len(team_point_ids) < 4: return []

        adj = self.get_adjacency_list(team_point_ids, team_lines)
        
        t_runes, used_points = [], set()
        for mid_id, neighbors_set in adj.items():
            if len(neighbors_set) < 3 or mid_id in used_points: continue
            p_mid = all_points.get(mid_id)
            if not p_mid: continue
            
            neighbors = list(neighbors_set)

            for p_stem1_id, p_stem2_id in combinations(neighbors, 2):
                p_stem1, p_stem2 = all_points.get(p_stem1_id), all_points.get(p_stem2_id)
                if not p_stem1 or not p_stem2: continue
                if orientation(p_stem1, p_mid, p_stem2) != 0: continue
                
                v_mid_s1 = {'x': p_stem1['x'] - p_mid['x'], 'y': p_stem1['y'] - p_mid['y']}
                v_mid_s2 = {'x': p_stem2['x'] - p_mid['x'], 'y': p_stem2['y'] - p_mid['y']}
                if v_mid_s1['x'] * v_mid_s2['x'] + v_mid_s1['y'] * v_mid_s2['y'] >= 0: continue
                
                for p_head_id in [nid for nid in neighbors if nid not in (p_stem1_id, p_stem2_id)]:
                    p_head = all_points.get(p_head_id)
                    if not p_head: continue
                    v_stem_x, v_stem_y = p_stem2['x'] - p_stem1['x'], p_stem2['y'] - p_stem1['y']
                    v_head_x, v_head_y = p_head['x'] - p_mid['x'], p_head['y'] - p_mid['y']
                    
                    mag_stem_sq = v_stem_x**2 + v_stem_y**2
                    mag_head_sq = v_head_x**2 + v_head_y**2
                    if mag_stem_sq < 0.1 or mag_head_sq < 0.1: continue

                    cos_theta_sq = (v_stem_x * v_head_x + v_stem_y * v_head_y)**2 / (mag_stem_sq * mag_head_sq)
                    
                    if cos_theta_sq < 0.05:
                        rune_points = {mid_id, p_stem1_id, p_stem2_id, p_head_id}
                        if not used_points.intersection(rune_points):
                            t_runes.append({'mid_id': mid_id, 'stem1_id': p_stem1_id, 'stem2_id': p_stem2_id, 'head_id': p_head_id, 'all_points': list(rune_points)})
                            used_points.update(rune_points)
                            break
                if mid_id in used_points: break
            if mid_id in used_points: continue
        return t_runes

    def check_plus_rune(self, team_point_ids, team_lines, all_points):
        """Finds Plus-Runes."""
        if len(team_point_ids) < 5: return []

        adj = self.get_adjacency_list(team_point_ids, team_lines)

        plus_runes, used_points = [], set()
        for center_id in team_point_ids:
            if center_id in used_points: continue
            neighbors = list(adj.get(center_id, set()))
            if len(neighbors) < 4: continue

            p_center = all_points.get(center_id)
            if not p_center: continue
            
            for arm_candidates_ids in combinations(neighbors, 4):
                arm_points_with_ids = {pid: all_points.get(pid) for pid in arm_candidates_ids}
                if not all(arm_points_with_ids.values()): continue
                
                p_arm1_id = arm_candidates_ids[0]
                p_arm1 = arm_points_with_ids[p_arm1_id]
                for i in range(1, 4):
                    p_arm2_id = arm_candidates_ids[i]
                    p_arm2 = arm_points_with_ids[p_arm2_id]
                    if orientation(p_arm1, p_center, p_arm2) != 0: continue
                    
                    v_center_a1 = {'x': p_arm1['x'] - p_center['x'], 'y': p_arm1['y'] - p_center['y']}
                    v_center_a2 = {'x': p_arm2['x'] - p_center['x'], 'y': p_arm2['y'] - p_center['y']}
                    if v_center_a1['x'] * v_center_a2['x'] + v_center_a1['y'] * v_center_a2['y'] >= 0: continue

                    other_arms_ids = [pid for pid in arm_candidates_ids if pid not in (p_arm1_id, p_arm2_id)]
                    p_arm3_id, p_arm4_id = other_arms_ids[0], other_arms_ids[1]
                    p_arm3 = arm_points_with_ids[p_arm3_id]
                    p_arm4 = arm_points_with_ids[p_arm4_id]
                    if orientation(p_arm3, p_center, p_arm4) != 0: continue
                    
                    v_line1_x, v_line1_y = p_arm2['x'] - p_arm1['x'], p_arm2['y'] - p_arm1['y']
                    v_line2_x, v_line2_y = p_arm4['x'] - p_arm3['x'], p_arm4['y'] - p_arm3['y']
                    
                    mag1_sq, mag2_sq = v_line1_x**2 + v_line1_y**2, v_line2_x**2 + v_line2_y**2
                    if mag1_sq < 0.1 or mag2_sq < 0.1: continue

                    if (v_line1_x * v_line2_x + v_line1_y * v_line2_y)**2 / (mag1_sq * mag2_sq) < 0.05:
                        rune_points = {center_id, p_arm1_id, p_arm2_id, p_arm3_id, p_arm4_id}
                        if not used_points.intersection(rune_points):
                            plus_runes.append({'center_id': center_id, 'arm_ids': list(arm_candidates_ids), 'all_points': list(rune_points)})
                            used_points.update(rune_points)
                            break
                if center_id in used_points: break
        return plus_runes

    def check_parallel_rune(self, team_point_ids, team_lines, all_points):
        """Finds Parallel Runes: a non-rectangular parallelogram with all four sides."""
        if len(team_point_ids) < 4: return []
        
        adj = self.get_adjacency_list(team_point_ids, team_lines)
        
        parallel_runes, checked_quads = [], set()

        for p1_id in team_point_ids:
            if len(adj.get(p1_id, [])) < 2: continue
            
            p1 = all_points[p1_id]
            neighbors_of_p1 = list(adj[p1_id])
            
            for i in range(len(neighbors_of_p1)):
                for j in range(i + 1, len(neighbors_of_p1)):
                    p2_id, p3_id = neighbors_of_p1[i], neighbors_of_p1[j]
                    
                    p2, p3 = all_points[p2_id], all_points[p3_id]
                    # Expected p4 = p1 + (p2-p1) + (p3-p1) = p2+p3-p1
                    p4_coords = {'x': p2['x'] + p3['x'] - p1['x'], 'y': p2['y'] + p3['y'] - p1['y']}

                    p4_id = None
                    p4_candidates = adj.get(p2_id, set()).intersection(adj.get(p3_id, set()))
                    for pid_candidate in p4_candidates:
                        if pid_candidate != p1_id:
                            p_candidate = all_points.get(pid_candidate)
                            if p_candidate and distance_sq(p_candidate, p4_coords) < 0.5:
                                p4_id = pid_candidate; break

                    if p4_id:
                        p_ids_tuple = tuple(sorted((p1_id, p2_id, p3_id, p4_id)))
                        if p_ids_tuple in checked_quads: continue
                        checked_quads.add(p_ids_tuple)

                        p_list = [p1, p2, p3, all_points[p4_id]]
                        is_para, is_rect = is_parallelogram(*p_list)
                        if is_para and not is_rect:
                            parallel_runes.append(list(p_ids_tuple))
        return parallel_runes

    def check_hourglass_rune(self, team_point_ids, team_lines, all_points):
        """Finds Hourglass Runes: two triangles sharing a single vertex."""
        if len(team_point_ids) < 5: return []

        adj = self.get_adjacency_list(team_point_ids, team_lines)

        hourglass_runes, used_points = [], set()
        for vertex_id in team_point_ids:
            if vertex_id in used_points: continue
            
            neighbors = list(adj.get(vertex_id, []))
            if len(neighbors) < 4: continue

            triangles_from_vertex = [set([p1_id, p2_id]) for p1_id, p2_id in combinations(neighbors, 2) if p2_id in adj.get(p1_id, set())]
            if len(triangles_from_vertex) < 2: continue
            
            for tri1_others, tri2_others in combinations(triangles_from_vertex, 2):
                if not tri1_others.intersection(tri2_others):
                    all_rune_points = {vertex_id}.union(tri1_others).union(tri2_others)
                    if not used_points.intersection(all_rune_points):
                        hourglass_runes.append({'vertex_id': vertex_id, 'all_points': list(all_rune_points)})
                        used_points.update(all_rune_points)
                        break
            if vertex_id in used_points: continue
        return hourglass_runes

    def check_prisms(self, team_territories):
        """Checks for Prism formations (two territories sharing an edge)."""
        if len(team_territories) < 2: return []
        
        prisms = []
        edge_to_territories = {}
        for i, territory in enumerate(team_territories):
            p_ids = territory['point_ids']
            edges = [tuple(sorted((p_ids[0], p_ids[1]))), tuple(sorted((p_ids[1], p_ids[2]))), tuple(sorted((p_ids[2], p_ids[0])))]
            for edge in edges:
                if edge not in edge_to_territories: edge_to_territories[edge] = []
                edge_to_territories[edge].append(i)

        for edge, ter_indices in edge_to_territories.items():
            if len(ter_indices) == 2:
                ter1, ter2 = team_territories[ter_indices[0]], team_territories[ter_indices[1]]
                all_points = set(ter1['point_ids']).union(set(ter2['point_ids']))
                if len(all_points) == 4:
                    prisms.append({'shared_p1_id': edge[0], 'shared_p2_id': edge[1], 'all_point_ids': list(all_points)})
        return prisms

    def check_trebuchets(self, team_point_ids, team_lines, all_points):
        """Checks for Trebuchet formations (a specific kite shape)."""
        if len(team_point_ids) < 4: return []

        adj = self.get_adjacency_list(team_point_ids, team_lines)
        
        used_points, possible_trebuchets = set(), []
        for apex_id in team_point_ids:
            if apex_id in used_points: continue
            
            neighbors = list(adj.get(apex_id, set()))
            if len(neighbors) < 2: continue

            for base1_id, base2_id in combinations(neighbors, 2):
                if base1_id in used_points or base2_id in used_points: continue

                p_apex = all_points.get(apex_id)
                p_base1 = all_points.get(base1_id)
                p_base2 = all_points.get(base2_id)
                if not all([p_apex, p_base1, p_base2]): continue
                
                leg1_sq, leg2_sq = distance_sq(p_apex, p_base1), distance_sq(p_apex, p_base2)

                if abs(leg1_sq - leg2_sq) > 0.01 or leg1_sq < 1.0: continue
                if distance_sq(p_base1, p_base2) > leg1_sq: continue
                if base2_id not in adj.get(base1_id, set()): continue

                for cw_id in adj.get(base1_id, set()).intersection(adj.get(base2_id, set())):
                    if cw_id == apex_id or cw_id in used_points: continue
                    
                    p_cw = all_points.get(cw_id)
                    if not p_cw: continue
                    base_midpoint = {'x': (p_base1['x'] + p_base2['x']) / 2, 'y': (p_base1['y'] + p_base2['y']) / 2}
                    v_apex = {'x': p_apex['x'] - base_midpoint['x'], 'y': p_apex['y'] - base_midpoint['y']}
                    v_cw = {'x': p_cw['x'] - base_midpoint['x'], 'y': p_cw['y'] - base_midpoint['y']}
                    
                    if abs(v_apex['x'] * v_cw['y'] - v_apex['y'] * v_cw['x']) > 1.0: continue
                    if (v_apex['x'] * v_cw['x'] + v_apex['y'] * v_cw['y']) >= 0: continue
                    
                    all_p_ids = {apex_id, base1_id, base2_id, cw_id}
                    if not used_points.intersection(all_p_ids):
                        possible_trebuchets.append({'point_ids': list(all_p_ids), 'apex_id': apex_id, 'base_ids': [base1_id, base2_id], 'counterweight_id': cw_id})
                        used_points.update(all_p_ids)
        return possible_trebuchets