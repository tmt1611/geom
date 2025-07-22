import random
import math
import uuid  # For unique point IDs
from itertools import combinations
from .geometry import (
    distance_sq, on_segment, orientation, segments_intersect,
    get_segment_intersection_point, is_rectangle, is_parallelogram,
    get_isosceles_triangle_info, is_regular_pentagon
)
from .formations import FormationManager
from . import game_data
from .actions.expand_actions import ExpandActionsHandler

# --- Game Class ---
class Game:
    """Encapsulates the entire game state and logic."""

    ACTION_GROUPS = game_data.ACTION_GROUPS
    ACTION_NAME_TO_GROUP = game_data.ACTION_NAME_TO_GROUP
    GROUP_BASE_WEIGHTS = game_data.GROUP_BASE_WEIGHTS
    TRAIT_GROUP_MULTIPLIERS = game_data.TRAIT_GROUP_MULTIPLIERS
    ACTION_DESCRIPTIONS = game_data.ACTION_DESCRIPTIONS
    ACTION_VERBOSE_DESCRIPTIONS = game_data.ACTION_VERBOSE_DESCRIPTIONS
    ACTION_MAP = game_data.ACTION_MAP
    ACTION_LOG_GENERATORS = game_data.ACTION_LOG_GENERATORS


    def __init__(self):
        self.formation_manager = FormationManager()
        self.reset()
        # Action handlers
        self.expand_handler = ExpandActionsHandler(self)

    def reset(self):
        """Initializes or resets the game state with default teams."""
        # Using fixed IDs for default teams ensures they can be referenced consistently.
        default_teams = {
            'team_alpha_default': {'id': 'team_alpha_default', 'name': 'Team Alpha', 'color': '#ff4b4b', 'trait': 'Aggressive'},
            'team_beta_default': {'id': 'team_beta_default', 'name': 'Team Beta', 'color': '#4b4bff', 'trait': 'Defensive'}
        }
        self.state = {
            "grid_size": 10,
            "teams": default_teams,
            "points": {},
            "lines": [],  # Each line will now get a unique ID
            "shields": {}, # {line_id: turns_left}
            "anchors": {}, # {point_id: {teamId: teamId, turns_left: N}}
            "stasis_points": {}, # {point_id: turns_left}
            "territories": [], # Added for claimed triangles
            "bastions": {}, # {bastion_id: {teamId, core_id, prong_ids}}
            "runes": {}, # {teamId: {'cross': [], 'v_shape': [], 'shield': [], 'trident': [], 'hourglass': [], 'star': [], 'barricade': [], 't_shape': [], 'plus_shape': [], 'i_shape': [], 'parallel': []}}
            "nexuses": {}, # {teamId: [nexus1, nexus2, ...]}
            "prisms": {}, # {teamId: [prism1, prism2, ...]}
            "barricades": [], # {id, teamId, p1, p2, turns_left}
            "heartwoods": {}, # {teamId: {id, center_coords, growth_counter}}
            "whirlpools": [], # {id, teamId, coords, turns_left, strength, radius_sq}
            "monoliths": {}, # {monolith_id: {teamId, point_ids, ...}}
            "trebuchets": {}, # {teamId: [trebuchet1, ...]}
            "purifiers": {}, # {teamId: [purifier1, ...]}
            "rift_spires": {}, # {spire_id: {teamId, coords, charge}}
            "rift_traps": [], # {id, teamId, coords, turns_left, radius_sq}
            "fissures": [], # {id, p1, p2, turns_left}
            "wonders": {}, # {wonder_id: {teamId, type, turns_to_victory, ...}}
            "line_strengths": {}, # {line_id: strength}
            "game_log": [{'message': "Welcome! Default teams Alpha and Beta are ready. Place points to begin.", 'short_message': '[READY]'}],
            "turn": 0,
            "max_turns": 100,
            "game_phase": "SETUP", # SETUP, RUNNING, FINISHED
            "victory_condition": None,
            "sole_survivor_tracker": {'teamId': None, 'turns': 0},
            "interpretation": {},
            "last_action_details": {}, # For frontend visualization
            "initial_state": None, # Store the setup config for restarts
            "new_turn_events": [], # For visualizing things that happen at turn start
            "action_in_turn": 0, # Which action index in the current turn's queue
            "actions_queue_this_turn": [], # List of action dicts {teamId, is_bonus} for the current turn
            "action_events": [] # For visualizing secondary effects of an action
        }

    def get_state(self):
        """Returns the current game state, augmenting with transient data for frontend."""
        if self.state['game_phase'] == 'FINISHED' and not self.state['interpretation']:
            self.state['interpretation'] = self.calculate_interpretation()

        state_copy = self.state.copy()
        
        state_copy['lines'] = self._augment_lines_for_frontend(self.state['lines'])
        state_copy['points'] = self._augment_points_for_frontend(self.state['points'])
        state_copy['live_stats'] = self._calculate_live_stats()
        
        return state_copy

    def _augment_lines_for_frontend(self, lines):
        """Adds transient frontend-specific data to lines."""
        bastion_line_ids = self._get_bastion_line_ids()
        augmented_lines = []
        for line in lines:
            augmented_line = line.copy()
            line_id = line.get('id')
            augmented_line['is_shielded'] = line_id in self.state['shields']
            augmented_line['is_bastion_line'] = line_id in bastion_line_ids
            augmented_line['strength'] = self.state.get('line_strengths', {}).get(line_id, 0)
            augmented_lines.append(augmented_line)
        return augmented_lines

    def _augment_points_for_frontend(self, points):
        """Adds transient frontend-specific data to points."""
        fortified_point_ids = self._get_fortified_point_ids()
        bastion_point_ids = self._get_bastion_point_ids()
        structure_pids = self._get_structure_point_ids_by_type()
        
        augmented_points = {}
        for pid, point in points.items():
            augmented_point = point.copy()
            augmented_point['is_anchor'] = pid in self.state['anchors']
            augmented_point['is_fortified'] = pid in fortified_point_ids
            augmented_point['is_bastion_core'] = pid in bastion_point_ids['cores']
            augmented_point['is_bastion_prong'] = pid in bastion_point_ids['prongs']
            augmented_point['is_i_rune_point'] = pid in structure_pids['i_rune']
            augmented_point['is_sentry_eye'] = pid in structure_pids['i_rune_sentry_eye']
            augmented_point['is_sentry_post'] = pid in structure_pids['i_rune_sentry_post']
            augmented_point['is_conduit_point'] = pid in structure_pids['i_rune'] # I-Runes are also Conduits
            augmented_point['is_nexus_point'] = pid in structure_pids['nexus']
            augmented_point['is_monolith_point'] = pid in structure_pids['monolith']
            augmented_point['is_trebuchet_point'] = pid in structure_pids['trebuchet']
            augmented_point['is_purifier_point'] = pid in structure_pids['purifier']
            augmented_point['is_in_stasis'] = pid in self.state.get('stasis_points', {})
            augmented_points[pid] = augmented_point
        return augmented_points

    def _calculate_live_stats(self):
        """Calculates and returns live stats for all teams."""
        live_stats = {}
        all_points = self.state['points']
        for teamId, team_data in self.state['teams'].items():
            team_point_ids = self.get_team_point_ids(teamId)
            team_lines = self.get_team_lines(teamId)
            team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]

            controlled_area = 0
            for territory in team_territories:
                triangle_point_ids = territory['point_ids']
                if all(pid in all_points for pid in triangle_point_ids):
                    triangle_points = [all_points[pid] for pid in triangle_point_ids]
                    if len(triangle_points) == 3:
                        controlled_area += self._polygon_area(triangle_points)

            live_stats[teamId] = {
                'point_count': len(team_point_ids),
                'line_count': len(team_lines),
                'controlled_area': round(controlled_area, 2)
            }
        return live_stats

    def start_game(self, teams, points, max_turns, grid_size):
        """Starts a new game with the given parameters."""
        self.reset()
        
        # Process team traits, handling 'Random' selection
        available_traits = ['Aggressive', 'Expansive', 'Defensive', 'Balanced']
        for team_id, team_data in teams.items():
            if team_data.get('trait') == 'Random' or 'trait' not in team_data:
                team_data['trait'] = random.choice(available_traits)
            team_data['id'] = team_id # Ensure team object contains its own ID

        self.state['teams'] = teams
        self.state['max_turns'] = max_turns
        self.state['grid_size'] = grid_size
        
        # Validate and convert points list to a dictionary with unique IDs
        valid_points = [p for p in points if 
                        isinstance(p.get('x'), int) and isinstance(p.get('y'), int) and
                        0 <= p['x'] < grid_size and 0 <= p['y'] < grid_size]

        for p in valid_points:
            point_id = f"p_{uuid.uuid4().hex[:6]}"
            self.state['points'][point_id] = {**p, 'id': point_id}
        
        self.state['game_phase'] = "RUNNING" if len(self.state['points']) > 0 else "SETUP"
        self.state['game_log'].append({'message': "Game initialized.", 'short_message': '[INIT]'})
        self.state['action_in_turn'] = 0
        self.state['actions_queue_this_turn'] = []
        
        # Store the initial state for restarting
        self.state['initial_state'] = {
            'teams': self.state['teams'],
            'points': points, # Use original point list before IDs are added
            'max_turns': max_turns,
            'grid_size': grid_size
        }

    def _get_structure_point_ids_by_type(self):
        """Returns a dictionary mapping structure types to sets of point IDs for frontend augmentation."""
        ids = {
            'i_rune': set(), 'i_rune_sentry_eye': set(), 'i_rune_sentry_post': set(),
            'nexus': set(), 'monolith': set(), 'trebuchet': set(), 'purifier': set()
        }

        if self.state.get('runes'):
            for team_runes in self.state['runes'].values():
                for i_rune in team_runes.get('i_shape', []):
                    ids['i_rune'].update(i_rune.get('point_ids', []))
                    ids['i_rune_sentry_eye'].update(i_rune.get('internal_points', []))
                    ids['i_rune_sentry_post'].update(i_rune.get('endpoints', []))
        
        # Structures that are dicts of lists {teamId: [item, ...]}
        list_structures = {'nexus': 'nexuses', 'trebuchet': 'trebuchets', 'purifier': 'purifiers'}
        for key, state_key in list_structures.items():
            if self.state.get(state_key):
                for team_list in self.state[state_key].values():
                    for struct in team_list:
                        ids[key].update(struct.get('point_ids', []))

        # Structures that are dicts of dicts {itemId: {..., point_ids: [...]}}
        dict_structures = {'monolith': 'monoliths'}
        for key, state_key in dict_structures.items():
            if self.state.get(state_key):
                for struct in self.state[state_key].values():
                    ids[key].update(struct.get('point_ids', []))

        return ids

    def get_team_point_ids(self, teamId):
        """Returns IDs of points belonging to a team."""
        return [pid for pid, p in self.state['points'].items() if p['teamId'] == teamId]

    def get_team_lines(self, teamId):
        """Returns lines belonging to a team."""
        return [l for l in self.state['lines'] if l['teamId'] == teamId]

    def _get_fortified_point_ids(self):
        """Returns a set of all point IDs that are part of any claimed territory."""
        fortified_ids = set()
        for territory in self.state.get('territories', []):
            for point_id in territory['point_ids']:
                fortified_ids.add(point_id)
        return fortified_ids

    def _get_bastion_point_ids(self):
        """Returns a dict of bastion core and prong point IDs."""
        core_ids = set()
        prong_ids = set()
        for bastion in self.state.get('bastions', {}).values():
            core_ids.add(bastion['core_id'])
            for pid in bastion['prong_ids']:
                prong_ids.add(pid)
        return {'cores': core_ids, 'prongs': prong_ids}

    def _get_bastion_line_ids(self):
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

    def _trigger_nexus_detonation(self, nexus, aggressor_team_id):
        """Handles the logic for a Nexus exploding when one of its points is destroyed."""
        center = nexus['center']
        radius_sq = (self.state['grid_size'] * 0.2)**2
        nexus_owner_teamId = nexus['teamId']
        nexus_owner_name = self.state['teams'][nexus_owner_teamId]['name']
        aggressor_name = self.state['teams'][aggressor_team_id]['name'] if aggressor_team_id and aggressor_team_id in self.state['teams'] else "an unknown force"

        log_msg = f"The destruction of a Nexus from Team {nexus_owner_name} by Team {aggressor_name} caused a violent energy discharge!"
        self.state['game_log'].append({'message': log_msg, 'short_message': '[NEXUS BOOM!]', 'teamId': nexus_owner_teamId})
        self.state['action_events'].append({
            'type': 'nexus_detonation',
            'center': center,
            'radius_sq': radius_sq,
            'color': self.state['teams'][nexus_owner_teamId]['color']
        })

        points_to_destroy_ids = []
        lines_to_destroy = []
        # Target enemies of the nexus owner
        for pid, p in list(self.state['points'].items()):
            if p['teamId'] != nexus_owner_teamId and distance_sq(center, p) < radius_sq:
                points_to_destroy_ids.append(pid)

        for line in list(self.state['lines']):
            if line['teamId'] != nexus_owner_teamId:
                p1 = self.state['points'].get(line['p1_id'])
                p2 = self.state['points'].get(line['p2_id'])
                if p1 and p2 and (distance_sq(center, p1) < radius_sq or distance_sq(center, p2) < radius_sq):
                    lines_to_destroy.append(line)
        
        destroyed_points_count = 0
        for pid in points_to_destroy_ids:
            if pid in self.state['points']:
                self._delete_point_and_connections(pid, aggressor_team_id)
                destroyed_points_count += 1
        
        destroyed_lines_count = 0
        for line in lines_to_destroy:
            if line in self.state['lines']:
                self.state['lines'].remove(line)
                self.state['shields'].pop(line.get('id'), None)
                destroyed_lines_count += 1

        if destroyed_points_count > 0 or destroyed_lines_count > 0:
            log_msg = f"The blast destroyed {destroyed_points_count} points and {destroyed_lines_count} lines."
            self.state['game_log'].append({'message': log_msg, 'short_message': '[CASCADE]', 'teamId': nexus_owner_teamId})

    def _cleanup_structures_for_point(self, point_id):
        """Helper to remove a point from all associated secondary structures after it has been deleted."""
        # Remove connected lines (and their shields)
        lines_before = self.state['lines'][:]
        self.state['lines'] = []
        for l in lines_before:
            if point_id in (l['p1_id'], l['p2_id']):
                self.state['shields'].pop(l.get('id'), None)
                self.state.get('line_strengths', {}).pop(l.get('id'), None)
            else:
                self.state['lines'].append(l)

        # Remove territories that used this point
        self.state['territories'] = [t for t in self.state['territories'] if point_id not in t['point_ids']]

        # Handle anchors
        self.state['anchors'].pop(point_id, None)

        # Handle bastions
        bastions_to_dissolve = []
        for bastion_id, bastion in list(self.state['bastions'].items()):
            if bastion['core_id'] == point_id:
                bastions_to_dissolve.append(bastion_id)
            elif point_id in bastion['prong_ids']:
                bastion['prong_ids'].remove(point_id)
                if len(bastion['prong_ids']) < 2:
                    bastions_to_dissolve.append(bastion_id)
        
        for bastion_id in bastions_to_dissolve:
            if bastion_id in self.state['bastions']: del self.state['bastions'][bastion_id]
        
        # Handle Stasis
        self.state.get('stasis_points', {}).pop(point_id, None)

        # Handle other structures that are just lists of point IDs
        structures_to_clean = ['trebuchets', 'purifiers', 'nexuses', 'prisms']
        for struct_key in structures_to_clean:
            if self.state.get(struct_key):
                for teamId in list(self.state[struct_key].keys()):
                    # Filter out any structure that contained the deleted point
                    self.state[struct_key][teamId] = [
                        s for s in self.state[struct_key][teamId] if point_id not in s.get('point_ids', []) and point_id not in s.get('all_point_ids', [])
                    ]

    def _delete_point_and_connections(self, point_id, aggressor_team_id=None):
        """A robust helper to delete a point and handle all cascading effects."""
        if point_id not in self.state['points']:
            return None # Point already gone

        # 1. Pre-deletion checks for cascades (e.g., Nexus detonation)
        nexus_to_detonate = None
        all_nexuses = [n for team_nexuses in self.state.get('nexuses', {}).values() for n in team_nexuses]
        for nexus in all_nexuses:
            if point_id in nexus.get('point_ids', []):
                nexus_to_detonate = nexus
                break
        
        # 2. Delete the point object itself, returning its data
        deleted_point_data = self.state['points'].pop(point_id)

        # 3. Trigger cascade effects AFTER the point is deleted
        if nexus_to_detonate and aggressor_team_id:
            self._trigger_nexus_detonation(nexus_to_detonate, aggressor_team_id)

        # 4. Clean up all other structures that might reference this point
        self._cleanup_structures_for_point(point_id)
        
        return deleted_point_data

    def _points_centroid(self, points):
        """Calculates the geometric centroid of a list of points."""
        if not points:
            return None
        num_points = len(points)
        x_sum = sum(p['x'] for p in points)
        y_sum = sum(p['y'] for p in points)
        return {'x': x_sum / num_points, 'y': y_sum / num_points}

    def _is_spawn_location_valid(self, new_point_coords, new_point_teamId, min_dist_sq=1.0):
        """Checks if a new point can be spawned at the given coordinates."""
        # Check if point is within grid boundaries
        grid_size = self.state['grid_size']
        if not (0 <= new_point_coords['x'] < grid_size and 0 <= new_point_coords['y'] < grid_size):
            return False, 'outside of grid boundaries'

        # Check proximity to existing points
        for existing_p in self.state['points'].values():
            if distance_sq(new_point_coords, existing_p) < min_dist_sq:
                return False, 'too close to an existing point'
        
        # Check proximity to fissures (a simple bounding box check for performance)
        for fissure in self.state.get('fissures', []):
            p1 = fissure['p1']
            p2 = fissure['p2']
            # Bounding box of the fissure segment
            box_x_min = min(p1['x'], p2['x']) - 1
            box_x_max = max(p1['x'], p2['x']) + 1
            box_y_min = min(p1['y'], p2['y']) - 1
            box_y_max = max(p1['y'], p2['y']) + 1
            
            if (new_point_coords['x'] >= box_x_min and new_point_coords['x'] <= box_x_max and
                new_point_coords['y'] >= box_y_min and new_point_coords['y'] <= box_y_max):
                # A more precise check can be done here if needed, but this is a good first pass
                return False, 'too close to a fissure'

        # Check against enemy Heartwood defensive aura
        if self.state.get('heartwoods'):
            for teamId, heartwood in self.state['heartwoods'].items():
                if teamId != new_point_teamId:
                    aura_radius_sq = (self.state['grid_size'] * 0.2)**2
                    if distance_sq(new_point_coords, heartwood['center_coords']) < aura_radius_sq:
                        return False, 'blocked by an enemy Heartwood aura'
        
        return True, 'valid'

    def _get_vulnerable_enemy_points(self, teamId):
        """Returns a list of enemy points that are not immune to standard attacks."""
        fortified_point_ids = self._get_fortified_point_ids()
        bastion_point_ids = self._get_bastion_point_ids()
        stasis_point_ids = set(self.state.get('stasis_points', {}).keys())
        immune_point_ids = fortified_point_ids.union(
            bastion_point_ids['cores'], bastion_point_ids['prongs'], stasis_point_ids
        )
        return [p for p in self.state['points'].values() if p['teamId'] != teamId and p['id'] not in immune_point_ids]

    def _strengthen_line(self, line):
        """Helper to strengthen a single line, returns if it was strengthened."""
        line_id = line.get('id')
        if not line_id: return False
        max_strength = 3
        current_strength = self.state.get('line_strengths', {}).get(line_id, 0)
        if current_strength < max_strength:
            self.state['line_strengths'][line_id] = current_strength + 1
            return True
        return False

    def _fallback_strengthen_random_line(self, teamId, action_type_prefix):
        """Generic fallback to strengthen a random line."""
        team_lines = self.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to perform action on or strengthen'}
        
        line_to_strengthen = random.choice(team_lines)
        self._strengthen_line(line_to_strengthen) # It's okay if it fails (already maxed)
        return {
            'success': True,
            'type': f'{action_type_prefix}_fizzle_strengthen',
            'strengthened_line': line_to_strengthen
        }

    def _find_non_critical_sacrificial_point(self, teamId):
        """
        Finds a point that can be sacrificed without crippling the team.
        A non-critical point is not part of a major structure and is not an articulation point.
        Returns a point_id or None.
        """
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) <= 2:
            return None

        # 1. Identify points in critical structures.
        fortified_point_ids = self._get_fortified_point_ids()
        bastion_pids = self._get_bastion_point_ids()
        monolith_pids = {pid for m in self.state.get('monoliths', {}).values() for pid in m.get('point_ids', [])}
        nexus_pids = {pid for nexus_list in self.state.get('nexuses', {}).values() for nexus in nexus_list for pid in nexus.get('point_ids', [])}
        trebuchet_pids = {pid for trebuchet_list in self.state.get('trebuchets', {}).values() for trebuchet in trebuchet_list for pid in trebuchet.get('point_ids', [])}
        purifier_pids = {pid for purifier_list in self.state.get('purifiers', {}).values() for purifier in purifier_list for pid in purifier.get('point_ids', [])}
        
        rune_pids = set()
        team_runes_data = self.state.get('runes', {}).get(teamId, {})
        for rune_category in team_runes_data.values():
            for rune_instance in rune_category:
                if isinstance(rune_instance, list):
                    rune_pids.update(rune_instance)
                elif isinstance(rune_instance, dict):
                    for key in ['point_ids', 'all_points', 'cycle_ids', 'triangle_ids', 'prong_ids', 'arm_ids']:
                        if key in rune_instance and rune_instance[key]: rune_pids.update(rune_instance[key])
                    for key in ['core_id', 'vertex_id', 'handle_id', 'apex_id', 'center_id', 'mid_id', 'stem1_id', 'stem2_id', 'head_id']:
                        if key in rune_instance and rune_instance[key]: rune_pids.add(rune_instance[key])
        
        critical_structure_pids = fortified_point_ids.union(
            bastion_pids['cores'], bastion_pids['prongs'],
            monolith_pids, nexus_pids, trebuchet_pids, purifier_pids, rune_pids
        )
        
        candidate_pids = [pid for pid in team_point_ids if pid not in critical_structure_pids]

        if not candidate_pids:
            return None

        # 2. Build adjacency list to check for articulation points.
        adj = {pid: set() for pid in team_point_ids}
        for line in self.get_team_lines(teamId):
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])
        
        # Prefer points with degree 1 (leaves), which are never articulation points.
        degree_one_candidates = [pid for pid in candidate_pids if len(adj.get(pid, set())) == 1]
        if degree_one_candidates:
            return random.choice(degree_one_candidates)

        # Check other candidates for being articulation points.
        def count_components(nodes, adjacency_list):
            if not nodes: return 0
            visited, count = set(), 0
            for node in nodes:
                if node not in visited:
                    count += 1
                    stack = [node]
                    visited.add(node)
                    while stack:
                        curr = stack.pop()
                        for neighbor in adjacency_list.get(curr, set()):
                            if neighbor in nodes and neighbor not in visited:
                                visited.add(neighbor)
                                stack.append(neighbor)
            return count

        initial_components = count_components(set(team_point_ids), adj)
        
        non_articulation_points = []
        for pid in candidate_pids:
            if len(adj.get(pid, set())) > 1:
                remaining_nodes = set(team_point_ids) - {pid}
                if count_components(remaining_nodes, adj) <= initial_components:
                    non_articulation_points.append(pid)
        
        if non_articulation_points:
            return random.choice(non_articulation_points)

        # All remaining candidates are articulation points. Don't sacrifice.
        return None

    # --- Game Actions ---

    def expand_action_add_line(self, teamId):
        return self.expand_handler.add_line(teamId)

    def _get_extended_border_point(self, p1, p2):
        """
        Extends a line segment p1-p2 from p1 outwards through p2 to the border.
        Returns the border point dictionary or None.
        """
        grid_size = self.state['grid_size']
        x1, y1 = p1['x'], p1['y']
        x2, y2 = p2['x'], p2['y']
        dx, dy = x2 - x1, y2 - y1

        if dx == 0 and dy == 0: return None

        # Check if extension is blocked by a fissure
        # Create a very long ray for intersection test
        ray_end_point = {'x': p2['x'] + dx * grid_size * 2, 'y': p2['y'] + dy * grid_size * 2}
        if self._is_ray_blocked(p2, ray_end_point):
            return None # Extension is blocked

        # We are calculating p_new = p1 + t * (p2 - p1) for t > 1
        t_values = []
        if dx != 0:
            t_values.append((0 - x1) / dx)
            t_values.append((grid_size - 1 - x1) / dx)
        if dy != 0:
            t_values.append((0 - y1) / dy)
            t_values.append((grid_size - 1 - y1) / dy)

        # Use a small epsilon to avoid floating point issues with the point itself
        valid_t = [t for t in t_values if t > 1.0001]
        if not valid_t: return None

        t = min(valid_t)
        ix, iy = x1 + t * dx, y1 + t * dy
        ix = round(max(0, min(grid_size - 1, ix)))
        iy = round(max(0, min(grid_size - 1, iy)))
        return {"x": ix, "y": iy}

    def expand_action_extend_line(self, teamId):
        return self.expand_handler.extend_line(teamId)

    def expand_action_fracture_line(self, teamId):
        return self.expand_handler.fracture_line(teamId)


    def _is_ray_blocked(self, p_start, p_end):
        """Checks if a segment is blocked by a fissure or barricade."""
        for fissure in self.state.get('fissures', []):
            if get_segment_intersection_point(p_start, p_end, fissure['p1'], fissure['p2']):
                 return True
        for barricade in self.state.get('barricades', []):
            if get_segment_intersection_point(p_start, p_end, barricade['p1'], barricade['p2']):
                 return True
        return False

    def fight_action_attack_line(self, teamId):
        """[FIGHT ACTION]: Extend a line to hit an enemy line. If it misses, it creates a new point on the border."""
        team_lines = self.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to attack from'}
        
        points = self.state['points']
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        team_has_cross_rune = len(self.state.get('runes', {}).get(teamId, {}).get('cross', [])) > 0
        
        # Try a few random lines to find a successful action
        random.shuffle(team_lines)
        for line in team_lines:
            if line['p1_id'] not in points or line['p2_id'] not in points: continue
            
            p1 = points[line['p1_id']]
            p2 = points[line['p2_id']]
            
            # Pick a random direction
            p_start, p_end = random.choice([(p1, p2), (p2, p1)])

            border_point = self._get_extended_border_point(p_start, p_end)
            if not border_point: continue

            attack_segment_p1 = p_end
            attack_segment_p2 = border_point

            if self._is_ray_blocked(attack_segment_p1, attack_segment_p2):
                continue

            # Check for hits
            closest_hit = None
            min_dist_sq = float('inf')

            for enemy_line in enemy_lines:
                is_shielded = enemy_line.get('id') in self.state['shields']
                if is_shielded and not team_has_cross_rune:
                    continue
                
                bastion_line_ids = self._get_bastion_line_ids()
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
            
            # --- Execute Action ---
            if closest_hit:
                # HIT! Destroy the line.
                enemy_line = closest_hit['target_line']
                
                # Check for Monolith strength
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

                # Line is not strengthened, destroy it
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
                # MISS! Create a point on the border.
                is_valid, _ = self._is_spawn_location_valid(border_point, teamId)
                if is_valid:
                    new_point_id = f"p_{uuid.uuid4().hex[:6]}"
                    new_point = {**border_point, "teamId": teamId, "id": new_point_id}
                    self.state['points'][new_point_id] = new_point
                    return {
                        'success': True,
                        'type': 'attack_miss_spawn',
                        'new_point': new_point,
                        'attacker_line': line,
                        'attack_ray': {'p1': attack_segment_p1, 'p2': border_point}
                    }
        
        # If loop finishes without finding a valid action
        return {'success': False, 'reason': 'no valid attack or spawn opportunity found'}

    def _find_possible_nova_bursts(self, teamId):
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) <= 2:
            return []

        blast_radius_sq = (self.state['grid_size'] * 0.25)**2
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        if not enemy_lines:
            return []

        points = self.state['points']
        bastion_line_ids = self._get_bastion_line_ids()
        
        potential_sac_points = []
        for pid in team_point_ids:
            sac_point_coords = points[pid]
            has_target = False
            for line in enemy_lines:
                if line.get('id') in bastion_line_ids: continue
                if not (line['p1_id'] in points and line['p2_id'] in points): continue
                
                p1 = points[line['p1_id']]
                p2 = points[line['p2_id']]

                if distance_sq(sac_point_coords, p1) < blast_radius_sq or distance_sq(sac_point_coords, p2) < blast_radius_sq:
                    potential_sac_points.append(pid)
                    has_target = True
                    break
            if has_target:
                continue
        return potential_sac_points

    def sacrifice_action_nova_burst(self, teamId):
        """[SACRIFICE ACTION]: A point is destroyed. If near enemy lines, it destroys them. Otherwise, it pushes all nearby points away."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) <= 2:
            return {'success': False, 'reason': 'not enough points to sacrifice'}

        # Use the existing helper to find IDEAL sacrifice points (those that will destroy lines)
        ideal_sac_points = self._find_possible_nova_bursts(teamId)

        sac_point_id = None
        if ideal_sac_points:
            sac_point_id = random.choice(ideal_sac_points)
        else:
            # If no ideal point, pick any non-critical point for the fallback effect.
            sac_point_id = self._find_non_critical_sacrificial_point(teamId)
            if not sac_point_id:
                return {'success': False, 'reason': 'no non-critical points to sacrifice'}

        sac_point_coords = self.state['points'][sac_point_id].copy()
        blast_radius_sq = (self.state['grid_size'] * 0.25)**2

        # --- Perform Sacrifice ---
        self._delete_point_and_connections(sac_point_id, aggressor_team_id=teamId)
        
        # --- Check for Primary Effect (Line Destruction) ---
        lines_to_remove_by_proximity = []
        points_to_check = self.state['points']
        bastion_line_ids = self._get_bastion_line_ids()
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
                if l in self.state['lines']: # Check if it wasn't already removed by cascade
                    self.state['lines'].remove(l)
                    self.state['shields'].pop(l.get('id'), None)
            
            return {
                'success': True,
                'type': 'nova_burst',
                'sacrificed_point': sac_point_coords,
                'lines_destroyed': len(lines_to_remove_by_proximity)
            }
        else:
            # Fallback Effect: Push points
            pushed_points = []
            push_distance = 2.0
            grid_size = self.state['grid_size']
            for point in self.state['points'].values():
                if distance_sq(sac_point_coords, point) < blast_radius_sq:
                    dx = point['x'] - sac_point_coords['x']
                    dy = point['y'] - sac_point_coords['y']
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist < 0.1: continue

                    push_vx = dx / dist
                    push_vy = dy / dist

                    new_x = point['x'] + push_vx * push_distance
                    new_y = point['y'] + push_vy * push_distance
                    
                    point['x'] = round(max(0, min(grid_size - 1, new_x)))
                    point['y'] = round(max(0, min(grid_size - 1, new_y)))
                    pushed_points.append(point.copy())
            
            return {
                'success': True,
                'type': 'nova_shockwave',
                'sacrificed_point': sac_point_coords,
                'pushed_points_count': len(pushed_points)
            }

    def sacrifice_action_create_whirlpool(self, teamId):
        """[SACRIFICE ACTION]: A point is destroyed. If points are nearby, it creates a vortex. Otherwise, it creates a small fissure."""
        if len(self.get_team_point_ids(teamId)) <= 1:
            return {'success': False, 'reason': 'not enough points to sacrifice'}

        p_to_sac_id = self._find_non_critical_sacrificial_point(teamId)
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
        sacrificed_point_data = self._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
        if not sacrificed_point_data:
            return {'success': False, 'reason': 'failed to sacrifice point'}

        # --- Determine Outcome ---
        if has_targets:
            # Primary Effect: Create Whirlpool
            whirlpool_id = f"wp_{uuid.uuid4().hex[:6]}"
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
            fissure_id = f"f_{uuid.uuid4().hex[:6]}"
            fissure_len = self.state['grid_size'] * 0.2
            angle = random.uniform(0, math.pi)
            p1 = {'x': sac_point_coords['x'] - (fissure_len / 2) * math.cos(angle), 'y': sac_point_coords['y'] - (fissure_len / 2) * math.sin(angle)}
            p2 = {'x': sac_point_coords['x'] + (fissure_len / 2) * math.cos(angle), 'y': sac_point_coords['y'] + (fissure_len / 2) * math.sin(angle)}

            grid_size = self.state['grid_size']
            p1['x'] = round(max(0, min(grid_size - 1, p1['x'])))
            p1['y'] = round(max(0, min(grid_size - 1, p1['y'])))
            p2['x'] = round(max(0, min(grid_size - 1, p2['x'])))
            p2['y'] = round(max(0, min(grid_size - 1, p2['y'])))

            new_fissure = {'id': fissure_id, 'p1': p1, 'p2': p2, 'turns_left': 3}
            if 'fissures' not in self.state: self.state['fissures'] = []
            self.state['fissures'].append(new_fissure)
            return {
                'success': True, 'type': 'whirlpool_fizzle_fissure',
                'fissure': new_fissure, 'sacrificed_point': sacrificed_point_data
            }

    def _get_eligible_phase_shift_lines(self, teamId):
        """Helper to find lines eligible for phase shift sacrifice."""
        team_lines = self.get_team_lines(teamId)
        team_point_ids = self.get_team_point_ids(teamId)
        
        adj_degree = {pid: 0 for pid in team_point_ids}
        for line in team_lines:
            if line['p1_id'] in adj_degree: adj_degree[line['p1_id']] += 1
            if line['p2_id'] in adj_degree: adj_degree[line['p2_id']] += 1

        fortified_point_ids = self._get_fortified_point_ids()
        bastion_point_ids = self._get_bastion_point_ids()
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

    def sacrifice_action_phase_shift(self, teamId):
        """[SACRIFICE ACTION]: Sacrifice a line to teleport one of its points. If teleport fails, the other point becomes a temporary anchor."""
        team_lines = self.get_team_lines(teamId)
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
        self.state['lines'].remove(line_to_sac)
        self.state['shields'].pop(line_to_sac.get('id'), None)

        # --- Try to find a new valid location ---
        new_coords = None
        grid_size = self.state['grid_size']
        for _ in range(25): # Try several times
            candidate_coords = {'x': random.randint(0, grid_size - 1), 'y': random.randint(0, grid_size - 1)}
            is_valid, _ = self._is_spawn_location_valid(candidate_coords, teamId, min_dist_sq=1.0)
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

    def sacrifice_action_rift_trap(self, teamId):
        """[SACRIFICE ACTION]: Sacrifices a point to create a temporary trap. If an enemy enters, it's destroyed. If not, the trap becomes a new point."""
        if len(self.get_team_point_ids(teamId)) <= 1:
            return {'success': False, 'reason': 'not enough points to sacrifice'}

        # Find a non-critical point to sacrifice
        p_to_sac_id = self._find_non_critical_sacrificial_point(teamId)
        if not p_to_sac_id:
            return {'success': False, 'reason': 'no non-critical points available to sacrifice'}
        sac_point_coords = self.state['points'][p_to_sac_id].copy()
        
        # Perform Sacrifice
        sacrificed_point_data = self._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
        if not sacrificed_point_data:
            return {'success': False, 'reason': 'failed to sacrifice point for trap'}

        # Create the trap
        trap_id = f"rt_{uuid.uuid4().hex[:6]}"
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

    def expand_action_spawn_point(self, teamId):
        return self.expand_handler.spawn_point(teamId)

    def expand_action_create_orbital(self, teamId):
        return self.expand_handler.create_orbital(teamId)

    def shield_action_protect_line(self, teamId):
        """[DEFEND ACTION]: Applies a temporary shield to a line. If all lines are shielded, it overcharges one."""
        team_lines = self.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to shield'}

        # Find lines that are not already shielded
        unshielded_lines = [l for l in team_lines if l.get('id') not in self.state['shields']]

        if unshielded_lines:
            # --- Primary Effect: Shield a new line ---
            line_to_shield = random.choice(unshielded_lines)
            shield_duration = 3 # in turns
            self.state['shields'][line_to_shield['id']] = shield_duration
            return {'success': True, 'type': 'shield_line', 'shielded_line': line_to_shield}
        else:
            # --- Fallback Effect: Overcharge an existing shield ---
            line_to_overcharge = random.choice(team_lines)
            line_id = line_to_overcharge.get('id')
            if line_id and line_id in self.state['shields']:
                max_shield_duration = 6
                current_duration = self.state['shields'][line_id]
                if current_duration < max_shield_duration:
                    self.state['shields'][line_id] += 2 # Add 2 turns
                
                return {
                    'success': True, 
                    'type': 'shield_overcharge', 
                    'overcharged_line': line_to_overcharge,
                    'new_duration': self.state['shields'][line_id]
                }
            
            # This should be very rare (e.g., lines have no IDs)
            return {'success': False, 'reason': 'no valid shield to overcharge'}

    def expand_action_grow_line(self, teamId):
        return self.expand_handler.grow_line(teamId)

    def _find_claimable_triangles(self, teamId):
        """Finds all triangles for a team that have not yet been claimed."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 3:
            return []

        adj = {pid: set() for pid in team_point_ids}
        for line in self.get_team_lines(teamId):
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])

        all_triangles = set()
        sorted_point_ids = sorted(list(team_point_ids))
        for i in sorted_point_ids:
            for j in adj.get(i, set()):
                if j > i:
                    for k in adj.get(j, set()):
                        if k > j and k in adj.get(i, set()):
                            all_triangles.add(tuple(sorted((i, j, k))))
        
        if not all_triangles:
            return []

        claimed_triangles = set(tuple(sorted(t['point_ids'])) for t in self.state['territories'])
        return list(all_triangles - claimed_triangles)

    def fortify_action_claim_territory(self, teamId):
        """[FORTIFY ACTION]: Find a triangle and claim it. If not possible, reinforces an existing territory."""
        newly_claimable_triangles = self._find_claimable_triangles(teamId)

        if newly_claimable_triangles:
            # --- Primary Effect: Claim Territory ---
            triangle_to_claim = random.choice(newly_claimable_triangles)
            new_territory = {
                'teamId': teamId,
                'point_ids': list(triangle_to_claim)
            }
            self.state['territories'].append(new_territory)
            return {'success': True, 'type': 'claim_territory', 'territory': new_territory}
        else:
            # --- Fallback Effect: Reinforce an existing territory ---
            team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
            if not team_territories:
                return {'success': False, 'reason': 'no new triangles to claim and no existing territories to reinforce'}
            
            territory_to_reinforce = random.choice(team_territories)
            p_ids = territory_to_reinforce['point_ids']
            boundary_lines_keys = [tuple(sorted((p_ids[0], p_ids[1]))), tuple(sorted((p_ids[1], p_ids[2]))), tuple(sorted((p_ids[2], p_ids[0])))]
            
            strengthened_lines = []
            max_strength = 3
            all_team_lines = self.get_team_lines(teamId)
            
            for line in all_team_lines:
                if tuple(sorted((line['p1_id'], line['p2_id']))) in boundary_lines_keys:
                    line_id = line.get('id')
                    if line_id:
                        current_strength = self.state['line_strengths'].get(line_id, 0)
                        if current_strength < max_strength:
                            self.state['line_strengths'][line_id] = current_strength + 1
                            strengthened_lines.append(line)
            
            # The action is 'successful' even if no lines were strengthened (they might be maxed out)
            # The log message will reflect if lines were strengthened or not.
            return {
                'success': True, 'type': 'claim_fizzle_reinforce',
                'territory_point_ids': p_ids, 'strengthened_lines': strengthened_lines
            }

    def _find_possible_bastions(self, teamId):
        """Finds all valid formations for creating a new bastion."""
        fortified_point_ids = self._get_fortified_point_ids()
        if not fortified_point_ids:
            return []

        team_point_ids = self.get_team_point_ids(teamId)
        adj = {pid: set() for pid in team_point_ids}
        for line in self.get_team_lines(teamId):
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])
        
        existing_bastion_points = self._get_bastion_point_ids()
        used_points = existing_bastion_points['cores'].union(existing_bastion_points['prongs'])

        possible_bastions = []
        for core_candidate_id in fortified_point_ids:
            if core_candidate_id not in team_point_ids or core_candidate_id in used_points:
                continue
            
            prong_candidates = [
                pid for pid in adj.get(core_candidate_id, set())
                if pid not in fortified_point_ids and pid not in used_points
            ]

            if len(prong_candidates) >= 3:
                possible_bastions.append({
                    'core_id': core_candidate_id,
                    'prong_ids': prong_candidates
                })
        return possible_bastions

    def fortify_action_form_bastion(self, teamId):
        """[FORTIFY ACTION]: Converts a fortified point and its connections into a defensive bastion. If not possible, reinforces a key point."""
        possible_bastions = self._find_possible_bastions(teamId)

        if not possible_bastions:
            # --- Fallback: Reinforce most connected fortified point ---
            fortified_point_ids = self._get_fortified_point_ids().intersection(self.get_team_point_ids(teamId))
            if not fortified_point_ids:
                return {'success': False, 'reason': 'no valid bastion formation and no fortified points to reinforce'}
            
            adj = {pid: 0 for pid in self.get_team_point_ids(teamId)}
            for line in self.get_team_lines(teamId):
                if line['p1_id'] in adj: adj[line['p1_id']] += 1
                if line['p2_id'] in adj: adj[line['p2_id']] += 1

            # Find the fortified point with the highest degree
            point_to_reinforce_id = max(fortified_point_ids, key=lambda pid: adj.get(pid, 0), default=None)

            if not point_to_reinforce_id:
                return {'success': False, 'reason': 'could not find a fortified point to reinforce'}
            
            lines_to_strengthen = [l for l in self.get_team_lines(teamId) if l['p1_id'] == point_to_reinforce_id or l['p2_id'] == point_to_reinforce_id]
            
            strengthened_lines = []
            max_strength = 3
            for line in lines_to_strengthen:
                line_id = line.get('id')
                if line_id:
                    current_strength = self.state['line_strengths'].get(line_id, 0)
                    if current_strength < max_strength:
                        self.state['line_strengths'][line_id] = current_strength + 1
                        strengthened_lines.append(line)
            
            return {
                'success': True, 'type': 'bastion_fizzle_reinforce',
                'reinforced_point_id': point_to_reinforce_id, 'strengthened_lines': strengthened_lines
            }
        
        # --- Primary Action: Form Bastion ---
        chosen_bastion = random.choice(possible_bastions)
        bastion_id = f"b_{uuid.uuid4().hex[:6]}"
        new_bastion = {
            'id': bastion_id,
            'teamId': teamId,
            **chosen_bastion
        }
        self.state['bastions'][bastion_id] = new_bastion

        # Collect line IDs for the visual effect
        all_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l['id'] for l in self.state['lines']}
        bastion_line_ids = []
        core_id = new_bastion['core_id']
        for prong_id in new_bastion['prong_ids']:
            line_key = tuple(sorted((core_id, prong_id)))
            if line_key in all_lines_by_points:
                bastion_line_ids.append(all_lines_by_points[line_key])

        return {'success': True, 'type': 'form_bastion', 'bastion': new_bastion, 'point_ids': [core_id] + new_bastion['prong_ids'], 'line_ids': bastion_line_ids}

    def fortify_action_form_monolith(self, teamId):
        """[FORTIFY ACTION]: Forms a Monolith from a tall, thin rectangle. If not possible, reinforces a regular rectangle."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 4:
            return {'success': False, 'reason': 'not enough points'}

        points = self.state['points']
        existing_lines_by_points = {tuple(sorted((l['p1_id'], l['p2_id']))): l for l in self.get_team_lines(teamId)}
        existing_monolith_points = {pid for m in self.state.get('monoliths', {}).values() for pid in m['point_ids']}

        possible_monoliths = []
        fallback_candidates = []
        
        for p_ids_tuple in combinations(team_point_ids, 4):
            if any(pid in existing_monolith_points for pid in p_ids_tuple):
                continue
            
            p_list = [points[pid] for pid in p_ids_tuple]
            is_rect, aspect_ratio = is_rectangle(*p_list)

            if is_rect:
                # Check for the 4 outer perimeter lines
                all_pairs = list(combinations(p_ids_tuple, 2))
                all_pair_dists = {pair: distance_sq(points[pair[0]], points[pair[1]]) for pair in all_pairs}
                sorted_pairs = sorted(all_pair_dists.keys(), key=lambda pair: all_pair_dists[pair])
                side_pairs = sorted_pairs[0:4]

                if all(tuple(sorted(pair)) in existing_lines_by_points for pair in side_pairs):
                    # Monolith requires a thin rectangle, aspect ratio > 3.0
                    if aspect_ratio > 3.0:
                        center_x = sum(p['x'] for p in p_list) / 4
                        center_y = sum(p['y'] for p in p_list) / 4
                        possible_monoliths.append({
                            'point_ids': list(p_ids_tuple),
                            'center_coords': {'x': center_x, 'y': center_y}
                        })
                    else:
                        fallback_candidates.append({'point_ids': list(p_ids_tuple), 'side_pairs': side_pairs})
        
        if not possible_monoliths:
            # --- Fallback: Reinforce a regular rectangle ---
            if not fallback_candidates:
                return {'success': False, 'reason': 'no valid monolith or rectangle formation found'}
            
            candidate = random.choice(fallback_candidates)
            strengthened_lines = []
            for pair in candidate['side_pairs']:
                line = existing_lines_by_points.get(tuple(sorted(pair)))
                if line and self._strengthen_line(line):
                    strengthened_lines.append(line)
            
            return {
                'success': True,
                'type': 'monolith_fizzle_reinforce',
                'reinforced_point_ids': candidate['point_ids'],
                'strengthened_lines': strengthened_lines
            }

        # --- Primary Action: Form Monolith ---
        chosen_monolith_data = random.choice(possible_monoliths)
        monolith_id = f"m_{uuid.uuid4().hex[:6]}"
        new_monolith = {
            'id': monolith_id,
            'teamId': teamId,
            'point_ids': chosen_monolith_data['point_ids'],
            'center_coords': chosen_monolith_data['center_coords'],
            'charge_counter': 0,
            'charge_interval': 4, # Emits wave every 4 turns
            'wave_radius_sq': (self.state['grid_size'] * 0.3)**2
        }
        
        if 'monoliths' not in self.state: self.state['monoliths'] = {}
        self.state['monoliths'][monolith_id] = new_monolith
        
        return {'success': True, 'type': 'form_monolith', 'monolith': new_monolith}

    def fortify_action_cultivate_heartwood(self, teamId):
        """[FORTIFY ACTION]: Cultivates a Heartwood from a point with many connections."""
        team_point_ids = self.get_team_point_ids(teamId)
        # A heartwood for a team is unique.
        if teamId in self.state.get('heartwoods', {}):
            return {'success': False, 'reason': 'team already has a heartwood'}
        
        HEARTWOOD_MIN_BRANCHES = 5
        
        adj = {pid: set() for pid in team_point_ids}
        for line in self.get_team_lines(teamId):
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])
        
        possible_formations = []
        for center_pid, connections in adj.items():
            if len(connections) >= HEARTWOOD_MIN_BRANCHES:
                # All connected points must also belong to the team (already ensured by get_team_lines)
                possible_formations.append({
                    'center_id': center_pid,
                    'branch_ids': list(connections)
                })

        if not possible_formations:
            return {'success': False, 'reason': f'no point with at least {HEARTWOOD_MIN_BRANCHES} connections found'}
        
        chosen_formation = random.choice(possible_formations)
        center_id = chosen_formation['center_id']
        branch_ids = chosen_formation['branch_ids']
        
        # Get coordinates of center point before deleting it
        center_coords = self.state['points'][center_id].copy()
        
        # --- Sacrifice all points in the formation ---
        all_points_to_sac_ids = [center_id] + branch_ids
        sacrificed_points_data = []
        for pid in all_points_to_sac_ids:
            # Note: _delete_point_and_connections also removes connected lines,
            # so we don't need to worry about them separately.
            sac_data = self._delete_point_and_connections(pid, aggressor_team_id=teamId)
            if sac_data:
                sacrificed_points_data.append(sac_data)

        if not sacrificed_points_data:
            return {'success': False, 'reason': 'failed to sacrifice points for heartwood'}

        # --- Create the Heartwood ---
        heartwood_id = f"hw_{uuid.uuid4().hex[:6]}"
        new_heartwood = {
            'id': heartwood_id,
            'teamId': teamId,
            'center_coords': {'x': center_coords['x'], 'y': center_coords['y']},
            'growth_counter': 0,
            'growth_interval': 3, # spawns a point every 3 turns
        }
        
        if 'heartwoods' not in self.state: self.state['heartwoods'] = {}
        self.state['heartwoods'][teamId] = new_heartwood
        
        return {
            'success': True,
            'type': 'cultivate_heartwood',
            'heartwood': new_heartwood,
            'sacrificed_points': sacrificed_points_data
        }

    def _find_star_formations(self, teamId, min_cycle=5, max_cycle=6):
        """
        Finds "star" formations for a team.
        A star is a central point connected to all points in a cycle of N points.
        Returns a list of dicts, each describing a star formation.
        e.g., [{'center_id': p_id, 'cycle_ids': [p1_id, p2_id, ...]}]
        """
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < min_cycle + 1:
            return []

        adj = {pid: set() for pid in team_point_ids}
        for line in self.get_team_lines(teamId):
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])

        found_stars = []
        
        # Avoid reusing points for multiple stars in one turn
        used_points = set()

        for center_candidate_id in team_point_ids:
            if center_candidate_id in used_points:
                continue
                
            neighbors = list(adj.get(center_candidate_id, set()))
            if len(neighbors) < min_cycle:
                continue

            # Check all combinations of neighbors to form a cycle
            for cycle_len in range(min_cycle, max_cycle + 1):
                if len(neighbors) < cycle_len:
                    continue
                
                for cycle_candidate_ids in combinations(neighbors, cycle_len):
                    # Check if these points form a cycle among themselves.
                    # Build a sub-adjacency list for only the candidates.
                    sub_adj = {pid: [] for pid in cycle_candidate_ids}
                    for i, p_id in enumerate(cycle_candidate_ids):
                        # Check connections within the cycle candidate points
                        for j in range(i + 1, len(cycle_candidate_ids)):
                            other_p_id = cycle_candidate_ids[j]
                            if other_p_id in adj.get(p_id, set()):
                                sub_adj[p_id].append(other_p_id)
                                sub_adj[other_p_id].append(p_id)
                    
                    # Each node in a simple cycle must have exactly 2 neighbors in the cycle.
                    if not all(len(sub_adj[pid]) == 2 for pid in cycle_candidate_ids):
                        continue

                    # We found a valid degree-2 subgraph. Now, confirm it is a single connected cycle
                    # by walking it, not two disjoint cycles (e.g., 2 triangles for N=6).
                    start_node = cycle_candidate_ids[0]
                    ordered_cycle = [start_node]
                    prev_node = start_node
                    curr_node = sub_adj[start_node][0] 
                    is_valid_cycle = True
                    
                    while curr_node != start_node and len(ordered_cycle) < cycle_len:
                        ordered_cycle.append(curr_node)
                        next_node_options = [n for n in sub_adj[curr_node] if n != prev_node]
                        if not next_node_options:
                            is_valid_cycle = False; break
                        prev_node = curr_node
                        curr_node = next_node_options[0]

                    if not is_valid_cycle or len(ordered_cycle) != cycle_len:
                        continue

                    # Check if any points are already used in another star found this turn
                    all_star_points = set(ordered_cycle) | {center_candidate_id}
                    if not used_points.intersection(all_star_points):
                        found_stars.append({
                            'center_id': center_candidate_id,
                            'cycle_ids': ordered_cycle,
                            'all_points': list(all_star_points)
                        })
                        used_points.update(all_star_points)
                        # Break from inner loops to not find smaller stars with the same center
                        break
                if center_candidate_id in used_points:
                    break
        
        return found_stars

    def fortify_action_form_rift_spire(self, teamId):
        """[FORTIFY ACTION]: Forms a Rift Spire from a point that is a vertex of 3 territories."""
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        if len(team_territories) < 3:
            return {'success': False, 'reason': 'not enough claimed territories'}

        # Count how many territories each point belongs to
        point_territory_count = {}
        for territory in team_territories:
            for pid in territory['point_ids']:
                if pid not in self.state['points']: continue
                point_territory_count[pid] = point_territory_count.get(pid, 0) + 1
        
        # Find points that are part of 3 or more territories
        existing_spire_coords = { (s['coords']['x'], s['coords']['y']) for s in self.state.get('rift_spires', {}).values() }

        possible_spires = []
        for pid, count in point_territory_count.items():
            if count >= 3:
                point_coords = self.state['points'][pid]
                if (point_coords['x'], point_coords['y']) not in existing_spire_coords:
                    possible_spires.append(pid)
        
        if not possible_spires:
            return {'success': False, 'reason': 'no point is a vertex of 3+ territories'}

        p_to_sac_id = random.choice(possible_spires)
        sacrificed_point_data = self._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
        
        if not sacrificed_point_data:
            return {'success': False, 'reason': 'failed to sacrifice point for spire'}

        spire_id = f"rs_{uuid.uuid4().hex[:6]}"
        new_spire = {
            'id': spire_id,
            'teamId': teamId,
            'coords': { 'x': sacrificed_point_data['x'], 'y': sacrificed_point_data['y'] },
            'charge': 0,
            'charge_needed': 3 # Takes 3 turns to charge up
        }
        if 'rift_spires' not in self.state: self.state['rift_spires'] = {}
        self.state['rift_spires'][spire_id] = new_spire

        return {
            'success': True,
            'type': 'form_rift_spire',
            'spire': new_spire,
            'sacrificed_point': sacrificed_point_data
        }

    def terraform_action_create_fissure(self, teamId):
        """[TERRAFORM ACTION]: A Rift Spire creates a fissure on the map."""
        team_spires = [s for s in self.state.get('rift_spires', {}).values() if s['teamId'] == teamId and s.get('charge', 0) >= s.get('charge_needed', 3)]
        if not team_spires:
            return {'success': False, 'reason': 'no charged rift spires available'}

        spire = random.choice(team_spires)
        grid_size = self.state['grid_size']
        
        # Create a long fissure, e.g., from one border to another
        borders = [
            {'x': 0, 'y': random.randint(0, grid_size - 1)},
            {'x': grid_size - 1, 'y': random.randint(0, grid_size - 1)},
            {'x': random.randint(0, grid_size - 1), 'y': 0},
            {'x': random.randint(0, grid_size - 1), 'y': grid_size - 1}
        ]
        p1 = random.choice(borders)
        
        opposite_borders = []
        if p1['x'] == 0: opposite_borders.append({'x': grid_size - 1, 'y': random.randint(0, grid_size - 1)})
        if p1['x'] == grid_size - 1: opposite_borders.append({'x': 0, 'y': random.randint(0, grid_size - 1)})
        if p1['y'] == 0: opposite_borders.append({'x': random.randint(0, grid_size - 1), 'y': grid_size - 1})
        if p1['y'] == grid_size - 1: opposite_borders.append({'x': random.randint(0, grid_size - 1), 'y': 0})
        
        p2 = random.choice(opposite_borders) if opposite_borders else random.choice(borders)

        fissure_id = f"f_{uuid.uuid4().hex[:6]}"
        new_fissure = { 'id': fissure_id, 'p1': p1, 'p2': p2, 'turns_left': 8 }
        self.state['fissures'].append(new_fissure)
        
        spire['charge'] = 0 # Reset charge

        return {
            'success': True,
            'type': 'create_fissure',
            'fissure': new_fissure,
            'spire_id': spire['id']
        }

    def terraform_action_raise_barricade(self, teamId):
        """[TERRAFORM ACTION]: Consumes a Barricade Rune to create a barricade."""
        active_barricade_runes = self.state.get('runes', {}).get(teamId, {}).get('barricade', [])
        if not active_barricade_runes:
            return {'success': False, 'reason': 'no active Barricade Runes'}

        rune_p_ids_tuple = random.choice(active_barricade_runes)
        points = self.state['points']
        
        if not all(pid in points for pid in rune_p_ids_tuple):
            return {'success': False, 'reason': 'rune points no longer exist'}
        
        p_list = [points[pid] for pid in rune_p_ids_tuple]
        
        # Sacrifice the rune points
        sacrificed_points_data = []
        for pid in rune_p_ids_tuple:
            sac_data = self._delete_point_and_connections(pid, aggressor_team_id=teamId)
            if sac_data:
                sacrificed_points_data.append(sac_data)

        # Determine barricade from midpoints of an opposite pair of sides of the rectangle
        # Use the original coordinates from p_list for this.
        all_pairs = list(combinations(p_list, 2))
        all_pair_dists = {tuple(p['id'] for p in pair): distance_sq(pair[0], pair[1]) for pair in all_pairs}
        sorted_pair_ids = sorted(all_pair_dists.keys(), key=lambda pair_ids: all_pair_dists[pair_ids])

        # The two longest pairs are diagonals, the other four are sides.
        side_pair_ids = sorted_pair_ids[0:4]

        # Pick one side
        side1_ids = set(side_pair_ids[0])
        # Find its opposite
        side2_ids = None
        for i in range(1, 4):
            candidate_side_ids = set(side_pair_ids[i])
            if not side1_ids.intersection(candidate_side_ids):
                side2_ids = candidate_side_ids
                break
        
        if not side2_ids:
            # Fallback for weird geometry, this should be rare for a valid rect.
            side1_ids = set(side_pair_ids[2])
            side2_ids = set()
            for i in [0,1,3]:
                candidate_side_ids = set(side_pair_ids[i])
                if not side1_ids.intersection(candidate_side_ids):
                    side2_ids = candidate_side_ids
                    break
        
        id_to_point = {p['id']: p for p in p_list}
        side1_pts = [id_to_point[pid] for pid in list(side1_ids)]
        side2_pts = [id_to_point[pid] for pid in list(side2_ids)]
        
        mid1 = self._points_centroid(side1_pts)
        mid2 = self._points_centroid(side2_pts)

        barricade_id = f"bar_{uuid.uuid4().hex[:6]}"
        new_barricade = {
            'id': barricade_id,
            'teamId': teamId,
            'p1': mid1,
            'p2': mid2,
            'turns_left': 5
        }

        if 'barricades' not in self.state: self.state['barricades'] = []
        self.state['barricades'].append(new_barricade)

        return {
            'success': True,
            'type': 'raise_barricade',
            'barricade': new_barricade,
            'rune_points': list(rune_p_ids_tuple),
            'sacrificed_points_count': len(sacrificed_points_data)
        }

    def fortify_action_build_chronos_spire(self, teamId):
        """[WONDER ACTION]: Build the Chronos Spire."""
        # Check if this team already has a wonder. Limit one per team for now.
        if any(w['teamId'] == teamId for w in self.state.get('wonders', {}).values()):
            return {'success': False, 'reason': 'team already has a wonder'}

        star_formations = self._find_star_formations(teamId)
        if not star_formations:
            return {'success': False, 'reason': 'no star formation found'}

        # Choose a formation to build on
        formation = random.choice(star_formations)
        
        center_point = self.state['points'][formation['center_id']]
        spire_coords = {'x': center_point['x'], 'y': center_point['y']}
        
        # Sacrifice all points in the formation
        points_to_sacrifice = formation['all_points']
        sacrificed_points_data = []
        for pid in points_to_sacrifice:
            sac_data = self._delete_point_and_connections(pid, aggressor_team_id=teamId)
            if sac_data:
                sacrificed_points_data.append(sac_data)
        
        if len(sacrificed_points_data) != len(points_to_sacrifice):
            return {'success': False, 'reason': 'failed to sacrifice all formation points'}
            
        # Create the Wonder
        wonder_id = f"w_{uuid.uuid4().hex[:6]}"
        new_wonder = {
            'id': wonder_id,
            'teamId': teamId,
            'type': 'ChronosSpire',
            'coords': spire_coords,
            'turns_to_victory': 10,
            'creation_turn': self.state['turn']
        }
        
        if 'wonders' not in self.state: self.state['wonders'] = {}
        self.state['wonders'][wonder_id] = new_wonder
        
        return {
            'success': True,
            'type': 'build_chronos_spire',
            'wonder': new_wonder,
            'sacrificed_points_count': len(sacrificed_points_data)
        }

    def _reflect_point(self, point, p1_axis, p2_axis):
        """Reflects a point across the line defined by p1_axis and p2_axis."""
        px, py = point['x'], point['y']
        x1, y1 = p1_axis['x'], p1_axis['y']
        x2, y2 = p2_axis['x'], p2_axis['y']

        # Line equation ax + by + c = 0
        a = y2 - y1
        b = x1 - x2
        
        if a == 0 and b == 0: # The axis points are the same, no line.
            return None

        c = -a * x1 - b * y1
        
        den = a**2 + b**2
        if den == 0: return None
        
        val = -2 * (a * px + b * py + c) / den
        
        rx = px + val * a
        ry = py + val * b
        
        return {'x': rx, 'y': ry}

    def fortify_action_mirror_structure(self, teamId):
        """[FORTIFY ACTION]: Reflects points to create symmetry. If not possible, reinforces the structure."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 3:
            return {'success': False, 'reason': 'not enough points to mirror'}
        
        points_to_strengthen_ids = set()

        # Try a few times to find a good axis and points to mirror
        for _ in range(5):
            # 1. Select two distinct points for the axis of symmetry
            axis_p_ids = random.sample(team_point_ids, 2)
            p_axis1 = self.state['points'][axis_p_ids[0]]
            p_axis2 = self.state['points'][axis_p_ids[1]]

            # Ensure axis points are not too close
            if distance_sq(p_axis1, p_axis2) < 4.0:
                continue

            # 2. Select points to mirror
            other_point_ids = [pid for pid in team_point_ids if pid not in axis_p_ids]
            if not other_point_ids:
                continue
            
            num_to_mirror = min(len(other_point_ids), 2)
            points_to_mirror_ids = random.sample(other_point_ids, num_to_mirror)
            points_to_strengthen_ids.update(points_to_mirror_ids)
            
            new_points_to_create = []
            grid_size = self.state['grid_size']
            all_reflections_valid = True

            # 3. Reflect points and check validity
            for pid in points_to_mirror_ids:
                point_to_mirror = self.state['points'][pid]
                reflected_p = self._reflect_point(point_to_mirror, p_axis1, p_axis2)
                
                if not reflected_p or not (0 <= reflected_p['x'] < grid_size and 0 <= reflected_p['y'] < grid_size):
                    all_reflections_valid = False; break
                
                reflected_p_int = {'x': round(reflected_p['x']), 'y': round(reflected_p['y'])}
                is_valid, _ = self._is_spawn_location_valid(reflected_p_int, teamId)
                if not is_valid:
                    all_reflections_valid = False; break
                
                new_point_id = f"p_{uuid.uuid4().hex[:6]}"
                new_points_to_create.append({**reflected_p_int, "teamId": teamId, "id": new_point_id})
            
            if all_reflections_valid and new_points_to_create:
                # --- Primary Effect: Create Mirrored Points ---
                for p in new_points_to_create:
                    self.state['points'][p['id']] = p
                
                return {
                    'success': True, 'type': 'mirror_structure',
                    'new_points': new_points_to_create, 'axis_p1_id': axis_p_ids[0], 'axis_p2_id': axis_p_ids[1],
                }
        
        # --- Fallback Effect: Strengthen Lines ---
        if not points_to_strengthen_ids:
            # Fallback failed because we couldn't even pick points to mirror.
            return {'success': False, 'reason': 'could not select points to mirror'}

        strengthened_lines = []
        max_strength = 3
        all_team_lines = self.get_team_lines(teamId)
        
        for line in all_team_lines:
            if line['p1_id'] in points_to_strengthen_ids or line['p2_id'] in points_to_strengthen_ids:
                line_id = line.get('id')
                if line_id:
                    current_strength = self.state['line_strengths'].get(line_id, 0)
                    if current_strength < max_strength:
                        self.state['line_strengths'][line_id] = current_strength + 1
                        strengthened_lines.append(line)
        
        if not strengthened_lines:
            # This can happen if the chosen points have no lines or their lines are max strength.
            # To be truly "never useless", we can add a line between the last chosen axis points.
            last_axis_pids = random.sample(team_point_ids, 2)
            existing_lines_keys = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in all_team_lines}
            if tuple(sorted(last_axis_pids)) not in existing_lines_keys:
                line_id = f"l_{uuid.uuid4().hex[:6]}"
                new_line = {"id": line_id, "p1_id": last_axis_pids[0], "p2_id": last_axis_pids[1], "teamId": teamId}
                self.state['lines'].append(new_line)
                return {'success': True, 'type': 'add_line', 'line': new_line} # Reuse add_line type
            else:
                return {'success': False, 'reason': 'mirroring failed and structure is already fully connected/strengthened'}

        return {
            'success': True, 'type': 'mirror_fizzle_strengthen',
            'strengthened_lines': strengthened_lines
        }

    def fortify_action_create_anchor(self, teamId):
        """[FORTIFY ACTION]: Sacrifice a point to turn another into a gravity well."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 3: # Requires at least 3 points to not cripple the team.
            return {'success': False, 'reason': 'not enough points to create anchor'}

        # Find a point to sacrifice and a point to turn into an anchor
        # Ensure they are not the same point
        p_to_sac_id, p_to_anchor_id = random.sample(team_point_ids, 2)
        
        # 1. Sacrifice the first point using the robust helper
        sacrificed_point_data = self._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
        if not sacrificed_point_data:
             return {'success': False, 'reason': 'failed to sacrifice point'}

        # 2. Create the anchor
        anchor_duration = 5 # turns
        self.state['anchors'][p_to_anchor_id] = {'teamId': teamId, 'turns_left': anchor_duration}

        anchor_point = self.state['points'][p_to_anchor_id]

        return {
            'success': True, 
            'type': 'create_anchor', 
            'anchor_point': anchor_point,
            'sacrificed_point': sacrificed_point_data
        }

    def fortify_action_form_purifier(self, teamId):
        """[FORTIFY ACTION]: Forms a Purifier from a regular pentagon of points."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 5:
            return {'success': False, 'reason': 'not enough points'}

        points = self.state['points']
        existing_lines = {tuple(sorted((l['p1_id'], l['p2_id']))) for l in self.get_team_lines(teamId)}
        
        # Get points already used in other major structures
        existing_purifier_points = {pid for p_list in self.state.get('purifiers', {}).values() for p in p_list for pid in p['point_ids']}

        possible_purifiers = []
        for p_ids_tuple in combinations(team_point_ids, 5):
            if any(pid in existing_purifier_points for pid in p_ids_tuple):
                continue

            p_list = [points[pid] for pid in p_ids_tuple]
            if is_regular_pentagon(*p_list):
                # To be a valid formation, the 5 outer "side" lines must exist.
                all_pairs = list(combinations(p_ids_tuple, 2))
                all_pair_dists = {pair: distance_sq(points[pair[0]], points[pair[1]]) for pair in all_pairs}
                sorted_pairs = sorted(all_pair_dists.keys(), key=lambda pair: all_pair_dists[pair])
                side_pairs = sorted_pairs[0:5]

                if all(tuple(sorted(pair)) in existing_lines for pair in side_pairs):
                    possible_purifiers.append({'point_ids': list(p_ids_tuple)})
        
        if not possible_purifiers:
            return {'success': False, 'reason': 'no valid pentagon formation found'}

        chosen_purifier_data = random.choice(possible_purifiers)
        
        if teamId not in self.state.get('purifiers', {}):
            self.state['purifiers'][teamId] = []
            
        self.state['purifiers'][teamId].append(chosen_purifier_data)
        
        return {'success': True, 'type': 'form_purifier', 'purifier': chosen_purifier_data}

    def fight_action_convert_point(self, teamId):
        """[FIGHT ACTION]: Sacrifice a line to convert a nearby enemy point. If no target, creates a repulsive pulse."""
        team_lines = self.get_team_lines(teamId)
        if not team_lines:
            return {'success': False, 'reason': 'no lines to sacrifice'}

        line_to_sac = random.choice(team_lines)
        points_map = self.state['points']
        
        if line_to_sac['p1_id'] not in points_map or line_to_sac['p2_id'] not in points_map:
             return {'success': False, 'reason': 'sacrificial line points do not exist'}

        p1 = points_map[line_to_sac['p1_id']]
        p2 = points_map[line_to_sac['p2_id']]
        midpoint = {'x': (p1['x'] + p2['x']) / 2, 'y': (p1['y'] + p2['y']) / 2}
        
        # --- Find Primary Target ---
        enemy_points = self._get_vulnerable_enemy_points(teamId)
        conversion_range_sq = (self.state['grid_size'] * 0.3)**2
        
        targets_in_range = []
        for enemy_point in enemy_points:
            if distance_sq(midpoint, enemy_point) < conversion_range_sq:
                targets_in_range.append(enemy_point)
        
        # --- Sacrifice the line BEFORE executing effect ---
        self.state['lines'].remove(line_to_sac)
        self.state['shields'].pop(line_to_sac.get('id'), None)

        if targets_in_range:
            # --- Primary Effect: Convert Point ---
            point_to_convert = min(targets_in_range, key=lambda p: distance_sq(midpoint, p))
            
            original_team_id = point_to_convert['teamId']
            original_team_name = self.state['teams'][original_team_id]['name']
            point_to_convert['teamId'] = teamId

            return {
                'success': True,
                'type': 'convert_point',
                'converted_point': point_to_convert,
                'sacrificed_line': line_to_sac,
                'original_team_name': original_team_name
            }
        else:
            # --- Fallback Effect: Repulsive Pulse ---
            pushed_points = []
            push_distance = 2.0
            grid_size = self.state['grid_size']
            # We only push enemy points
            for point in [p for p in self.state['points'].values() if p['teamId'] != teamId]:
                if distance_sq(midpoint, point) < conversion_range_sq:
                    dx = point['x'] - midpoint['x']
                    dy = point['y'] - midpoint['y']
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist < 0.1: continue

                    push_vx = dx / dist
                    push_vy = dy / dist

                    new_x = point['x'] + push_vx * push_distance
                    new_y = point['y'] + push_vy * push_distance
                    
                    point['x'] = round(max(0, min(grid_size - 1, new_x)))
                    point['y'] = round(max(0, min(grid_size - 1, new_y)))
                    pushed_points.append(point.copy())

            return {
                'success': True,
                'type': 'convert_fizzle_push',
                'sacrificed_line': line_to_sac,
                'pulse_center': midpoint,
                'radius_sq': conversion_range_sq,
                'pushed_points_count': len(pushed_points)
            }

    def _find_possible_bastion_pulses(self, teamId):
        team_bastions = [b for b in self.state.get('bastions', {}).values() if b['teamId'] == teamId and len(b['prong_ids']) > 0]
        if not team_bastions: return []

        points_map = self.state['points']
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        if not enemy_lines: return []

        possible_pulses = []
        for bastion in team_bastions:
            prong_points = [points_map[pid] for pid in bastion['prong_ids'] if pid in points_map]
            if len(prong_points) < 2: continue

            centroid = self._points_centroid(prong_points)
            prong_points.sort(key=lambda p: math.atan2(p['y'] - centroid['y'], p['x'] - centroid['x']))
            
            has_crossing_line = False
            for enemy_line in enemy_lines:
                if enemy_line['p1_id'] not in points_map or enemy_line['p2_id'] not in points_map: continue
                ep1 = points_map[enemy_line['p1_id']]
                ep2 = points_map[enemy_line['p2_id']]
                for i in range(len(prong_points)):
                    perimeter_p1 = prong_points[i]
                    perimeter_p2 = prong_points[(i + 1) % len(prong_points)]
                    if segments_intersect(ep1, ep2, perimeter_p1, perimeter_p2):
                        possible_pulses.append(bastion)
                        has_crossing_line = True
                        break
                if has_crossing_line:
                    break
        return possible_pulses

    def fight_action_bastion_pulse(self, teamId):
        """[FIGHT ACTION]: A bastion sacrifices a prong to destroy crossing enemy lines. If it fizzles, it creates a shockwave."""
        possible_bastions = self._find_possible_bastion_pulses(teamId)
        if not possible_bastions:
            return {'success': False, 'reason': 'no active bastions with crossing enemy lines'}

        bastion_to_pulse = random.choice(possible_bastions)
        if not bastion_to_pulse['prong_ids']:
            return {'success': False, 'reason': 'bastion has no prongs to sacrifice'}

        prong_to_sac_id = random.choice(bastion_to_pulse['prong_ids'])
        sacrificed_prong_data = self._delete_point_and_connections(prong_to_sac_id, aggressor_team_id=teamId)
        if not sacrificed_prong_data:
            return {'success': False, 'reason': 'selected prong point does not exist'}
        
        current_bastion_state = self.state['bastions'].get(bastion_to_pulse['id'])
        points_map = self.state['points']
        
        # If bastion is still valid and has prongs, proceed with primary effect
        if current_bastion_state and len(current_bastion_state.get('prong_ids', [])) >= 2:
            prong_points = [points_map[pid] for pid in current_bastion_state['prong_ids'] if pid in points_map]
            
            # Sort points angularly to form a correct simple polygon
            centroid = self._points_centroid(prong_points)
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

    def fight_action_launch_payload(self, teamId):
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
        fortified_ids = self._get_fortified_point_ids()
        bastion_cores = self._get_bastion_point_ids()['cores']
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
            destroyed_point_data = self._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
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

    def fight_action_sentry_zap(self, teamId):
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
            destroyed_point_data = self._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
            if not destroyed_point_data:
                return {'success': False, 'reason': 'failed to destroy target point'}
            
            zap_ray_end = self._get_extended_border_point(p_eye, target_point) or target_point
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
            border_point = self._get_extended_border_point(p_eye, dummy_end_point)
            
            if not border_point or self._is_ray_blocked(p_eye, border_point):
                 return {'success': False, 'reason': 'zap path to border was blocked'}
            
            is_valid, _ = self._is_spawn_location_valid(border_point, teamId)
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

    def fight_action_chain_lightning(self, teamId):
        """[FIGHT ACTION]: An I-Rune sacrifices an internal point to strike an enemy. If it fizzles, it creates a mini-nova."""
        team_i_runes = self.state.get('runes', {}).get(teamId, {}).get('i_shape', [])
        # Requires an internal point to sacrifice
        valid_runes = [r for r in team_i_runes if r.get('internal_points')]
        if not valid_runes:
            return {'success': False, 'reason': 'no I-Runes with sacrificial points'}

        chosen_rune = random.choice(valid_runes)
        p_to_sac_id = random.choice(chosen_rune['internal_points'])
        sacrificed_point_data = self._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
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
            destroyed_point_data = self._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
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
                if line.get('id') in self._get_bastion_line_ids() or line.get('id') in self.state['shields']: continue
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

    def _pincer_attack_fallback_barricade(self, teamId, p1_id, p2_id):
        """Fallback for pincer attack: create a temporary barricade."""
        points = self.state['points']
        p1 = points.get(p1_id)
        p2 = points.get(p2_id)

        if not p1 or not p2:
            return {'success': False, 'reason': 'points for fallback barricade do not exist'}
        
        barricade_id = f"bar_{uuid.uuid4().hex[:6]}"
        new_barricade = {
            'id': barricade_id, 'teamId': teamId,
            'p1': {'x': p1['x'], 'y': p1['y']},
            'p2': {'x': p2['x'], 'y': p2['y']},
            'turns_left': 2 # A short-lived barricade
        }
        self.state['barricades'].append(new_barricade)
        
        return {
            'success': True, 'type': 'pincer_fizzle_barricade',
            'barricade': new_barricade,
            'pincer_points': [p1_id, p2_id]
        }

    def fight_action_pincer_attack(self, teamId):
        """[FIGHT ACTION]: Two points flank and destroy an enemy point. If not possible, they form a defensive barricade."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 2:
            return {'success': False, 'reason': 'not enough points for pincer attack'}

        enemy_points = self._get_vulnerable_enemy_points(teamId)
        if not enemy_points:
             # No vulnerable enemies, go straight to fallback
             p1_id, p2_id = random.sample(team_point_ids, 2)
             return self._pincer_attack_fallback_barricade(teamId, p1_id, p2_id)

        points_map = self.state['points']
        max_range_sq = (self.state['grid_size'] * 0.4)**2
        pincer_angle_threshold = -0.866  # cos(150 deg)
        
        # Try a few random pairs of points to find a pincer
        pincer_candidates = list(combinations(team_point_ids, 2))
        random.shuffle(pincer_candidates)
        for p1_id, p2_id in pincer_candidates[:10]: # Try up to 10 random pairs
            p1 = points_map[p1_id]
            p2 = points_map[p2_id]
            
            possible_targets = []
            for ep in enemy_points:
                if distance_sq(p1, ep) > max_range_sq or distance_sq(p2, ep) > max_range_sq:
                    continue
                v1 = {'x': p1['x'] - ep['x'], 'y': p1['y'] - ep['y']}
                v2 = {'x': p2['x'] - ep['x'], 'y': p2['y'] - ep['y']}
                mag1_sq = v1['x']**2 + v1['y']**2
                mag2_sq = v2['x']**2 + v2['y']**2
                if mag1_sq < 0.1 or mag2_sq < 0.1: continue
                dot_product = v1['x'] * v2['x'] + v1['y'] * v2['y']
                cos_theta = dot_product / (math.sqrt(mag1_sq) * math.sqrt(mag2_sq))

                if cos_theta < pincer_angle_threshold:
                    possible_targets.append(ep)

            if possible_targets:
                # --- Primary Effect: Pincer Attack ---
                # Choose the best target (e.g., closest to the midpoint of the attackers)
                midpoint = self._points_centroid([p1, p2])
                target_point = min(possible_targets, key=lambda p: distance_sq(midpoint, p))

                destroyed_point_data = self._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
                if not destroyed_point_data: continue # Try another pincer if deletion failed for some reason
                
                destroyed_team_name = self.state['teams'][destroyed_point_data['teamId']]['name']
                return {
                    'success': True, 'type': 'pincer_attack',
                    'destroyed_point': destroyed_point_data,
                    'attacker_p1_id': p1_id,
                    'attacker_p2_id': p2_id,
                    'destroyed_team_name': destroyed_team_name
                }
        
        # If loop finishes with no successful pincer, execute fallback with a random pair
        p1_id, p2_id = random.sample(team_point_ids, 2)
        return self._pincer_attack_fallback_barricade(teamId, p1_id, p2_id)

    def _get_large_territories(self, teamId):
        """Helper to find all large territories for a team."""
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        if not team_territories:
            return []

        points_map = self.state['points']
        MIN_AREA = 10.0
        large_territories = []
        for territory in team_territories:
            p_ids = territory['point_ids']
            if all(pid in points_map for pid in p_ids):
                triangle_points = [points_map[pid] for pid in p_ids]
                if len(triangle_points) == 3 and self._polygon_area(triangle_points) >= MIN_AREA:
                    large_territories.append(territory)
        return large_territories

    def fight_action_territory_strike(self, teamId):
        """[FIGHT ACTION]: Launches an attack from a large territory. If no targets, reinforces the territory."""
        large_territories = self._get_large_territories(teamId)
        if not large_territories:
            return {'success': False, 'reason': 'no large territories to strike from'}

        territory = random.choice(large_territories)
        points_map = self.state['points']
        
        if not all(pid in points_map for pid in territory['point_ids']):
            return {'success': False, 'reason': 'territory points no longer exist'}
        
        triangle_points = [points_map[pid] for pid in territory['point_ids']]
        centroid = self._points_centroid(triangle_points)

        # --- Find Primary Target ---
        enemy_points = self._get_vulnerable_enemy_points(teamId)
        if enemy_points:
            target_point = min(enemy_points, key=lambda p: distance_sq(centroid, p))

            destroyed_point_data = self._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
            if not destroyed_point_data:
                 return {'success': False, 'reason': 'failed to destroy target point'}
            
            destroyed_team_name = self.state['teams'][destroyed_point_data['teamId']]['name']

            return {
                'success': True, 'type': 'territory_strike',
                'destroyed_point': destroyed_point_data,
                'territory_point_ids': territory['point_ids'],
                'attack_ray': {'p1': centroid, 'p2': target_point},
                'destroyed_team_name': destroyed_team_name
            }
        
        # --- Fallback: Reinforce Territory ---
        else:
            p_ids = territory['point_ids']
            boundary_lines_keys = [tuple(sorted((p_ids[0], p_ids[1]))), tuple(sorted((p_ids[1], p_ids[2]))), tuple(sorted((p_ids[2], p_ids[0])))]
            
            strengthened_lines = []
            max_strength = 3
            all_team_lines = self.get_team_lines(teamId)
            
            for line in all_team_lines:
                if not (line['p1_id'] in points_map and line['p2_id'] in points_map): continue
                line_key = tuple(sorted((line['p1_id'], line['p2_id'])))
                if line_key in boundary_lines_keys:
                    line_id = line.get('id')
                    if line_id:
                        current_strength = self.state['line_strengths'].get(line_id, 0)
                        if current_strength < max_strength:
                            self.state['line_strengths'][line_id] = current_strength + 1
                            strengthened_lines.append(line)
            
            if not strengthened_lines:
                return {'success': True, 'type': 'territory_fizzle_reinforce', 'territory_point_ids': territory['point_ids'], 'strengthened_lines': []}

            return {
                'success': True, 'type': 'territory_fizzle_reinforce',
                'territory_point_ids': territory['point_ids'],
                'strengthened_lines': strengthened_lines
            }

    def fight_action_refraction_beam(self, teamId):
        """[FIGHT ACTION]: Uses a Prism to refract an attack beam. If it misses, it creates a new point on the border."""
        team_prisms = self.state.get('prisms', {}).get(teamId, [])
        if not team_prisms:
            return {'success': False, 'reason': 'no active prisms'}
        
        points = self.state['points']
        
        prism_point_ids = {pid for p in team_prisms for pid in p['all_point_ids']}
        source_lines = [l for l in self.get_team_lines(teamId) if l['p1_id'] not in prism_point_ids and l['p2_id'] not in prism_point_ids]
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
            
            source_ray_end = self._get_extended_border_point(ls1, ls2)
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
                refracted_ray_end = self._get_extended_border_point(intersection_point, refracted_end_dummy)
                if not refracted_ray_end: continue
                
                refracted_ray = {'p1': intersection_point, 'p2': refracted_ray_end}

                # Check this ray for hits
                hit_found = False
                if enemy_lines:
                    bastion_line_ids = self._get_bastion_line_ids()
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
            is_valid, _ = self._is_spawn_location_valid(border_point, teamId)
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

    def fight_action_purify_territory(self, teamId):
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
                purifier_center = self._points_centroid(purifier_points)
                if not purifier_center: continue
                
                for territory in enemy_territories:
                    if not all(pid in points_map for pid in territory['point_ids']): continue
                    territory_points = [points_map[pid] for pid in territory['point_ids']]
                    if len(territory_points) != 3: continue
                    territory_center = self._points_centroid(territory_points)

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
        pulse_center = self._points_centroid(purifier_points)
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

    def _update_nexuses_for_team(self, teamId):
        """Checks for Nexus formations by delegating to the FormationManager."""
        if 'nexuses' not in self.state: self.state['nexuses'] = {}
        
        team_point_ids = self.get_team_point_ids(teamId)
        team_lines = self.get_team_lines(teamId)
        
        self.state['nexuses'][teamId] = self.formation_manager.check_nexuses(
            team_point_ids, team_lines, self.state['points']
        )

    def rune_action_shoot_bisector(self, teamId):
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
        border_point = self._get_extended_border_point(p_vertex, p_end)
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

    def rune_action_area_shield(self, teamId):
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
        for line in self.get_team_lines(teamId):
            if line.get('id') in self.state['shields']: continue
            line_p1, line_p2 = points.get(line['p1_id']), points.get(line['p2_id'])
            if line_p1 and line_p2 and line_p1['id'] not in rune['triangle_ids'] and line_p2['id'] not in rune['triangle_ids']:
                if self._is_point_inside_triangle(line_p1, p1, p2, p3) and self._is_point_inside_triangle(line_p2, p1, p2, p3):
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
            rune_center = self._points_centroid(tri_points)
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

    def rune_action_shield_pulse(self, teamId):
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
        rune_center = self._points_centroid(tri_points)
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

    def rune_action_impale(self, teamId):
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
        border_point = self._get_extended_border_point(p_handle, p_apex)
        if not border_point:
            return {'success': False, 'reason': 'impale attack does not hit border'}
            
        attack_ray_p1 = p_apex
        attack_ray_p2 = border_point
        
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        lines_to_destroy = []
        intersection_points = []
        bastion_line_ids = self._get_bastion_line_ids()
        
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

    def _get_all_actions_status(self, teamId):
        """
        Checks all available actions and returns a dictionary with their validity
        and a reason for invalidity.
        """
        team_point_ids = self.get_team_point_ids(teamId)
        num_team_points = len(team_point_ids)
        num_team_lines = len(self.get_team_lines(teamId))
        num_enemy_points = len(self.state['points']) - num_team_points
        num_enemy_lines = len(self.state['lines']) - num_team_lines
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        
        # A dictionary mapping action names to a tuple of (lambda -> bool, "reason for failure").
        # These checks are more precise than before, using the find_possible_* helpers.
        preconditions = {
            'expand_add': (lambda: num_team_points >= 2, "Requires at least 2 points."),
            'expand_extend': (lambda: len(self.expand_handler._find_possible_extensions(teamId)) > 0, "No lines can be validly extended."),
            'expand_grow': (lambda: num_team_lines > 0, "Requires at least 1 line to grow from."),
            'expand_fracture': (lambda: len(self.expand_handler._find_fracturable_lines(teamId)) > 0, "No non-territory lines long enough to fracture."),
            'expand_spawn': (lambda: num_team_points > 0, "Requires at least 1 point to spawn from."),
            'expand_orbital': (lambda: num_team_points >= 5, "Requires at least 5 points."),
            'fight_attack': (lambda: num_team_lines > 0, "Requires at least 1 line to attack from."),
            'fight_convert': (lambda: num_team_lines > 0, "Requires at least 1 line to sacrifice."),
            'fight_pincer_attack': (lambda: len(self.get_team_point_ids(teamId)) >= 2, "Requires at least 2 points."),
            'fight_territory_strike': (lambda: len(self._get_large_territories(teamId)) > 0, "No large territories available."),
            'fight_bastion_pulse': (lambda: len(self._find_possible_bastion_pulses(teamId)) > 0, "No bastion has crossing enemy lines to pulse."),
            'fight_sentry_zap': (lambda: any(r.get('internal_points') for r in self.state.get('runes', {}).get(teamId, {}).get('i_shape', [])), "Requires an I-Rune with at least 3 points."),
            'fight_chain_lightning': (lambda: any(r.get('internal_points') for r in self.state.get('runes', {}).get(teamId, {}).get('i_shape', [])), "Requires an I-Rune with internal points."),
            'fight_refraction_beam': (lambda: bool(self.state.get('prisms', {}).get(teamId, [])) and num_enemy_lines > 0, "Requires a Prism and enemy lines."),
            'fight_launch_payload': (lambda: bool(self.state.get('trebuchets', {}).get(teamId, [])), "Requires a Trebuchet."),
            'fight_purify_territory': (lambda: bool(self.state.get('purifiers', {}).get(teamId, [])) and any(t['teamId'] != teamId for t in self.state.get('territories', [])), "Requires a Purifier and an enemy territory."),
            'defend_shield': (lambda: num_team_lines > 0, "Requires at least one line to shield or overcharge."),
            'fortify_claim': (lambda: len(self._find_claimable_triangles(teamId)) > 0, "No new triangles available to claim."),
            'fortify_anchor': (lambda: num_team_points >= 3, "Requires at least 3 points to sacrifice one."),
            'fortify_mirror': (lambda: num_team_points >= 3, "Requires at least 3 points to mirror."),
            'fortify_form_bastion': (lambda: len(self._find_possible_bastions(teamId)) > 0, "No valid bastion formation found."),
            'fortify_form_monolith': (lambda: num_team_points >= 4, "Requires at least 4 points."),
            'fortify_form_purifier': (lambda: num_team_points >= 5, "Requires at least 5 points."),
            'fortify_cultivate_heartwood': (lambda: num_team_points >= 6 and teamId not in self.state.get('heartwoods', {}), "Requires >= 6 points and no existing Heartwood."),
            'fortify_form_rift_spire': (lambda: len(team_territories) >= 3, "Requires at least 3 territories."),
            'terraform_create_fissure': (lambda: any(s['teamId'] == teamId and s.get('charge', 0) >= s.get('charge_needed', 3) for s in self.state.get('rift_spires', {}).values()), "Requires a charged Rift Spire."),
            'terraform_raise_barricade': (lambda: bool(self.state.get('runes', {}).get(teamId, {}).get('barricade', [])), "Requires an active Barricade Rune."),
            'fortify_build_wonder': (lambda: num_team_points >= 6 and not any(w['teamId'] == teamId for w in self.state.get('wonders', {}).values()), "Requires >= 6 points and no existing Wonder."),
            'sacrifice_nova': (lambda: num_team_points > 2, "Requires more than 2 points to sacrifice one."),
            'sacrifice_whirlpool': (lambda: num_team_points > 1, "Requires more than 1 point to sacrifice one."),
            'sacrifice_phase_shift': (lambda: num_team_lines > 0, "Requires a line to sacrifice."),
            'sacrifice_rift_trap': (lambda: num_team_points > 1, "Requires more than 1 point to sacrifice."),
            'rune_shoot_bisector': (lambda: bool(self.state.get('runes', {}).get(teamId, {}).get('v_shape', [])), "Requires an active V-Rune."),
            'rune_area_shield': (lambda: bool(self.state.get('runes', {}).get(teamId, {}).get('shield', [])), "Requires an active Shield Rune."),
            'rune_shield_pulse': (lambda: bool(self.state.get('runes', {}).get(teamId, {}).get('shield', [])), "Requires an active Shield Rune."),
            'rune_impale': (lambda: bool(self.state.get('runes', {}).get(teamId, {}).get('trident', [])), "Requires an active Trident Rune."),
            'rune_hourglass_stasis': (lambda: bool(self.state.get('runes', {}).get(teamId, {}).get('hourglass', [])), "Requires an active Hourglass Rune."),
            'rune_starlight_cascade': (lambda: len(self._find_possible_starlight_cascades(teamId)) > 0, "No Star Rune has a valid target in range."),
            'rune_focus_beam': (lambda: bool(self.state.get('runes', {}).get(teamId, {}).get('star', [])) and num_enemy_points > 0, "Requires a Star Rune and an enemy point."),
            'rune_t_hammer_slam': (lambda: bool(self.state.get('runes', {}).get(teamId, {}).get('t_shape', [])), "Requires an active T-Rune."),
            'rune_cardinal_pulse': (lambda: bool(self.state.get('runes', {}).get(teamId, {}).get('plus_shape', [])), "Requires an active Plus-Rune."),
            'rune_parallel_discharge': (lambda: bool(self.state.get('runes', {}).get(teamId, {}).get('parallel', [])), "Requires an active Parallelogram Rune."),
        }

        status = {}
        # Ensure all actions have a precondition check
        all_actions = self.ACTION_NAME_TO_GROUP.keys()
        for name in all_actions:
            if name in preconditions:
                is_possible_func, reason = preconditions[name]
                is_valid = is_possible_func()
                status[name] = {
                    'valid': is_valid,
                    'reason': "" if is_valid else reason
                }
            else:
                # Fallback for any action that might be in weights but not preconditions
                status[name] = {
                    'valid': False,
                    'reason': 'Precondition not defined.'
                }
        
        return status

    def _get_possible_actions(self, teamId, exclude_actions=None):
        """
        Checks all available actions and returns a list of names of actions
        that the given team can currently perform.
        """
        if exclude_actions is None:
            exclude_actions = []

        all_statuses = self._get_all_actions_status(teamId)
        possible_actions = []
        for name, status_info in all_statuses.items():
            if name not in exclude_actions and status_info['valid']:
                possible_actions.append(name)
        
        return possible_actions


    def get_action_probabilities(self, teamId, include_invalid=False):
        """
        Calculates the probability of each possible action for a team,
        based on their trait and the current game state, organized by group.
        Optionally includes invalid actions and their reasons.
        """
        if teamId not in self.state['teams']:
            return {"error": "Team not found"}

        # Update structures for the team to get the most accurate list of possible actions
        self._update_runes_for_team(teamId)
        self._update_prisms_for_team(teamId)
        self._update_trebuchets_for_team(teamId)
        self._update_nexuses_for_team(teamId)

        all_action_statuses = self._get_all_actions_status(teamId)
        
        # Group valid actions by category
        valid_actions_by_group = {group: [] for group in self.ACTION_GROUPS.keys()}
        for action_name, status in all_action_statuses.items():
            if status['valid']:
                group = self.ACTION_NAME_TO_GROUP.get(action_name)
                if group:
                    valid_actions_by_group[group].append(action_name)
        
        # Determine group weights based on trait and valid actions
        team_trait = self.state['teams'][teamId].get('trait', 'Balanced')
        group_multipliers = self.TRAIT_GROUP_MULTIPLIERS.get(team_trait, {})
        
        final_group_weights = {}
        for group_name, actions in valid_actions_by_group.items():
            if actions: # Only consider groups that have at least one valid action
                base_weight = self.GROUP_BASE_WEIGHTS.get(group_name, 0)
                multiplier = group_multipliers.get(group_name, 1.0)
                final_group_weights[group_name] = base_weight * multiplier

        total_group_weight = sum(final_group_weights.values())

        # Build response structure
        response = {
            'team_name': self.state['teams'][teamId]['name'], 
            'color': self.state['teams'][teamId]['color'], 
            'groups': {},
            'invalid': []
        }

        if total_group_weight > 0:
            for group_name, group_weight in final_group_weights.items():
                group_prob = (group_weight / total_group_weight) * 100
                valid_actions = valid_actions_by_group[group_name]
                num_valid_actions = len(valid_actions)
                
                action_list = []
                if num_valid_actions > 0:
                    action_prob = group_prob / num_valid_actions
                    for action_name in valid_actions:
                        action_list.append({
                            'name': action_name,
                            'display_name': self.ACTION_DESCRIPTIONS.get(action_name, action_name),
                            'probability': round(action_prob, 1)
                        })

                if action_list:
                     response['groups'][group_name] = {
                        'group_probability': round(group_prob, 1),
                        'actions': sorted(action_list, key=lambda x: x['display_name'])
                     }

        if include_invalid:
            for name, status in all_action_statuses.items():
                if not status['valid']:
                    response['invalid'].append({
                        'name': name,
                        'display_name': self.ACTION_DESCRIPTIONS.get(name, name),
                        'reason': status['reason'],
                        'group': self.ACTION_NAME_TO_GROUP.get(name, 'Other')
                    })
            response['invalid'].sort(key=lambda x: (x['group'], x['display_name']))

        return response

    def _choose_action_for_team(self, teamId, exclude_actions=None):
        """Chooses an action for a team based on group probabilities, excluding any that have already failed this turn."""
        if exclude_actions is None: exclude_actions = []

        # --- 1. Get all valid actions, excluding ones that have already failed ---
        possible_actions = self._get_possible_actions(teamId, exclude_actions)
        if not possible_actions: return None, None

        # --- 2. Group these valid actions by category ---
        valid_actions_by_group = {group: [] for group in self.ACTION_GROUPS.keys()}
        for action_name in possible_actions:
            group = self.ACTION_NAME_TO_GROUP.get(action_name)
            if group:
                valid_actions_by_group[group].append(action_name)

        # --- 3. Determine final group weights based on trait and which groups are actually possible ---
        team_trait = self.state['teams'][teamId].get('trait', 'Balanced')
        group_multipliers = self.TRAIT_GROUP_MULTIPLIERS.get(team_trait, {})
        
        final_group_weights = {}
        for group_name, actions in valid_actions_by_group.items():
            if actions: # Only consider groups that have at least one valid action
                base_weight = self.GROUP_BASE_WEIGHTS.get(group_name, 0)
                multiplier = group_multipliers.get(group_name, 1.0)
                final_group_weights[group_name] = base_weight * multiplier
        
        if not final_group_weights: return None, None # No valid groups to choose from

        # --- 4. Choose a group, then choose an action from that group ---
        group_names = list(final_group_weights.keys())
        group_weights = list(final_group_weights.values())
        
        chosen_group = random.choices(group_names, weights=group_weights, k=1)[0]
        chosen_action_name = random.choice(valid_actions_by_group[chosen_group])
        
        # --- 5. Return the chosen action name and its function ---
        action_func_name = self.ACTION_MAP.get(chosen_action_name)
        action_func = getattr(self, action_func_name) if action_func_name else None
        return chosen_action_name, action_func


    def restart_game(self):
        """Restarts the game from its initial configuration."""
        if not self.state.get('initial_state'):
            return {"error": "No initial state saved to restart from."}
        
        initial_config = self.state['initial_state']
        
        # We need to create fresh copies of mutable objects
        teams = {tid: t.copy() for tid, t in initial_config['teams'].items()}
        points = [p.copy() for p in initial_config['points']]

        self.start_game(
            teams=teams,
            points=points,
            max_turns=initial_config['max_turns'],
            grid_size=initial_config['grid_size']
        )
        return self.get_state()

    # --- Start of Turn Processing ---

    def _process_shields_and_stasis(self):
        """Handles decay of shields and stasis effects."""
        self.state['shields'] = {lid: turns - 1 for lid, turns in self.state['shields'].items() if turns - 1 > 0}
        if self.state.get('stasis_points'):
            self.state['stasis_points'] = {pid: turns - 1 for pid, turns in self.state['stasis_points'].items() if turns - 1 > 0}

    def _process_rift_traps(self):
        """Handles rift trap triggers, expiration, and spawning."""
        if not self.state.get('rift_traps'):
            return

        remaining_traps = []
        for trap in self.state['rift_traps']:
            triggered_point_id = None
            for pid, point in self.state['points'].items():
                if point['teamId'] != trap['teamId'] and distance_sq(trap['coords'], point) < trap['radius_sq']:
                    triggered_point_id = pid
                    break
            
            if triggered_point_id:
                destroyed_point = self._delete_point_and_connections(triggered_point_id, aggressor_team_id=trap['teamId'])
                if destroyed_point:
                    team_name = self.state['teams'][trap['teamId']]['name']
                    enemy_team_name = self.state['teams'][destroyed_point['teamId']]['name']
                    log_msg = { 'teamId': trap['teamId'], 'message': f"A Rift Trap from Team {team_name} snared and destroyed a point from Team {enemy_team_name}!", 'short_message': '[TRAP!]'}
                    self.state['game_log'].append(log_msg)
                    self.state['new_turn_events'].append({ 'type': 'rift_trap_trigger', 'trap': trap, 'destroyed_point': destroyed_point })
                continue

            trap['turns_left'] -= 1
            if trap['turns_left'] <= 0:
                is_valid, _ = self._is_spawn_location_valid(trap['coords'], trap['teamId'])
                if is_valid:
                    new_point_id = f"p_{uuid.uuid4().hex[:6]}"
                    new_point = {"x": round(trap['coords']['x']), "y": round(trap['coords']['y']), "teamId": trap['teamId'], "id": new_point_id}
                    self.state['points'][new_point_id] = new_point
                    
                    team_name = self.state['teams'][trap['teamId']]['name']
                    log_msg = { 'teamId': trap['teamId'], 'message': f"An unused Rift Trap from Team {team_name} stabilized into a new point.", 'short_message': '[TRAP->SPAWN]' }
                    self.state['game_log'].append(log_msg)
                    self.state['new_turn_events'].append({ 'type': 'rift_trap_expire', 'trap': trap, 'new_point': new_point })
                continue
            
            remaining_traps.append(trap)
        
        self.state['rift_traps'] = remaining_traps

    def _process_anchors(self):
        """Handles anchor point pulls and expiration."""
        expired_anchors = []
        pull_strength = 0.2
        grid_size = self.state['grid_size']
        for anchor_pid, anchor_data in list(self.state['anchors'].items()):
            if anchor_pid not in self.state['points']:
                expired_anchors.append(anchor_pid)
                continue
            
            anchor_point = self.state['points'][anchor_pid]
            anchor_radius_sq = (grid_size * 0.4)**2
            for point in self.state['points'].values():
                if point['teamId'] != anchor_data['teamId'] and distance_sq(anchor_point, point) < anchor_radius_sq:
                    dx, dy = anchor_point['x'] - point['x'], anchor_point['y'] - point['y']
                    new_x = point['x'] + dx * pull_strength
                    new_y = point['y'] + dy * pull_strength
                    point['x'] = round(max(0, min(grid_size - 1, new_x)))
                    point['y'] = round(max(0, min(grid_size - 1, new_y)))

            anchor_data['turns_left'] -= 1
            if anchor_data['turns_left'] <= 0:
                expired_anchors.append(anchor_pid)
        for anchor_pid in expired_anchors:
            if anchor_pid in self.state['anchors']: del self.state['anchors'][anchor_pid]
    
    def _process_heartwoods(self):
        """Handles Heartwood point generation."""
        if not self.state.get('heartwoods'):
            return

        for teamId, heartwood in self.state['heartwoods'].items():
            heartwood['growth_counter'] += 1
            if heartwood['growth_counter'] >= heartwood['growth_interval']:
                heartwood['growth_counter'] = 0
                
                for _ in range(10):
                    angle = random.uniform(0, 2 * math.pi)
                    radius = self.state['grid_size'] * random.uniform(0.05, 0.15)
                    
                    new_x = heartwood['center_coords']['x'] + math.cos(angle) * radius
                    new_y = heartwood['center_coords']['y'] + math.sin(angle) * radius
                    
                    grid_size = self.state['grid_size']
                    final_x = round(max(0, min(grid_size - 1, new_x)))
                    final_y = round(max(0, min(grid_size - 1, new_y)))
                    
                    new_p_coords = {'x': final_x, 'y': final_y}
                    if not self._is_spawn_location_valid(new_p_coords, teamId)[0]: continue

                    new_point_id = f"p_{uuid.uuid4().hex[:6]}"
                    new_point = {"x": final_x, "y": final_y, "teamId": teamId, "id": new_point_id}
                    self.state['points'][new_point_id] = new_point
                    
                    team_name = self.state['teams'][teamId]['name']
                    log_msg = {'teamId': teamId, 'message': f"The Heartwood of Team {team_name} birthed a new point.", 'short_message': '[HW:GROWTH]'}
                    self.state['game_log'].append(log_msg)
                    self.state['new_turn_events'].append({'type': 'heartwood_growth', 'new_point': new_point, 'heartwood_id': heartwood['id']})
                    break

    def _process_whirlpools(self):
        """Handles whirlpool pulls and expiration."""
        if not self.state.get('whirlpools'):
            return

        active_whirlpools = []
        grid_size = self.state['grid_size']
        for whirlpool in self.state['whirlpools']:
            whirlpool['turns_left'] -= 1
            if whirlpool['turns_left'] > 0:
                active_whirlpools.append(whirlpool)
                wp_coords, wp_radius_sq, wp_strength, wp_swirl = whirlpool['coords'], whirlpool['radius_sq'], whirlpool['strength'], whirlpool['swirl']

                for point in self.state['points'].values():
                    if distance_sq(wp_coords, point) < wp_radius_sq:
                        dx, dy = wp_coords['x'] - point['x'], wp_coords['y'] - point['y']
                        dist = math.sqrt(dx**2 + dy**2)
                        if dist < 0.1: continue
                        
                        angle = math.atan2(dy, dx)
                        new_dist, new_angle = dist * (1 - wp_strength), angle + wp_swirl
                        new_dx, new_dy = math.cos(new_angle) * new_dist, math.sin(new_angle) * new_dist
                        new_x, new_y = wp_coords['x'] - new_dx, wp_coords['y'] - new_dy
                        point['x'] = round(max(0, min(grid_size - 1, new_x)))
                        point['y'] = round(max(0, min(grid_size - 1, new_y)))

        self.state['whirlpools'] = active_whirlpools

    def _process_monoliths(self):
        """Handles Monolith resonance waves."""
        if not self.state.get('monoliths'):
            return

        for monolith_id, monolith in list(self.state['monoliths'].items()):
            monolith['charge_counter'] += 1
            if monolith['charge_counter'] >= monolith['charge_interval']:
                monolith['charge_counter'] = 0
                
                team_name = self.state['teams'][monolith['teamId']]['name']
                log_msg = {'teamId': monolith['teamId'], 'message': f"A Monolith from Team {team_name} emits a reinforcing wave.", 'short_message': '[MONOLITH:WAVE]'}
                self.state['game_log'].append(log_msg)
                self.state['new_turn_events'].append({'type': 'monolith_wave', 'monolith_id': monolith_id, 'center_coords': monolith['center_coords'], 'radius_sq': monolith['wave_radius_sq']})

                center, radius_sq = monolith['center_coords'], monolith['wave_radius_sq']
                for line in self.get_team_lines(monolith['teamId']):
                    if line['p1_id'] not in self.state['points'] or line['p2_id'] not in self.state['points']: continue
                    p1, p2 = self.state['points'][line['p1_id']], self.state['points'][line['p2_id']]
                    midpoint = {'x': (p1['x'] + p2['x']) / 2, 'y': (p1['y'] + p2['y']) / 2}
                    if distance_sq(center, midpoint) < radius_sq:
                        self._strengthen_line(line)

    def _process_wonders(self):
        """Handles Wonder countdowns and checks for Wonder victory. Returns True if game ends."""
        if not self.state.get('wonders'):
            return False

        for wonder in list(self.state['wonders'].values()):
            if wonder['type'] == 'ChronosSpire':
                wonder['turns_to_victory'] -= 1
                team_name = self.state['teams'][wonder['teamId']]['name']
                log_msg = {'teamId': wonder['teamId'], 'message': f"The Chronos Spire of Team {team_name} pulses. Victory in {wonder['turns_to_victory']} turns.", 'short_message': f'[SPIRE: T-{wonder["turns_to_victory"]}]'}
                self.state['game_log'].append(log_msg)
                
                if wonder['turns_to_victory'] <= 0:
                    self.state['game_phase'] = 'FINISHED'
                    self.state['victory_condition'] = f"Team '{team_name}' achieved victory with the Chronos Spire."
                    self.state['game_log'].append({'message': self.state['victory_condition'], 'short_message': '[WONDER VICTORY]'})
                    self.state['actions_queue_this_turn'] = []
                    return True
        return False

    def _process_spires_fissures_barricades(self):
        """Handles charging of spires and decay of fissures and barricades."""
        if self.state.get('rift_spires'):
            for spire in self.state['rift_spires'].values():
                if spire.get('charge', 0) < spire.get('charge_needed', 3):
                    spire['charge'] += 1
        
        for key in ['fissures', 'barricades']:
            if self.state.get(key):
                active_items = []
                for item in self.state[key]:
                    item['turns_left'] -= 1
                    if item['turns_left'] > 0:
                        active_items.append(item)
                self.state[key] = active_items

    def _build_action_queue(self):
        """Builds and shuffles the action queue for the current turn."""
        self.state['game_log'].append({'message': f"--- Turn {self.state['turn']} ---", 'short_message': f"~ T{self.state['turn']} ~"})
        active_teams = [teamId for teamId in self.state['teams'] if len(self.get_team_point_ids(teamId)) > 0]
        
        actions_queue = []
        for teamId in active_teams:
            actions_queue.append({'teamId': teamId, 'is_bonus': False})

            self._update_nexuses_for_team(teamId)
            num_nexuses = len(self.state.get('nexuses', {}).get(teamId, []))
            if num_nexuses > 0:
                team_name = self.state['teams'][teamId]['name']
                plural = "s" if num_nexuses > 1 else ""
                self.state['game_log'].append({'message': f"Team {team_name} gains {num_nexuses} bonus action{plural} from its Nexus{plural}.", 'short_message': f'[NEXUS:+{num_nexuses}ACT]'})
                for _ in range(num_nexuses):
                    actions_queue.append({'teamId': teamId, 'is_bonus': True})

            num_wonders = sum(1 for w in self.state.get('wonders', {}).values() if w['teamId'] == teamId)
            if num_wonders > 0:
                team_name = self.state['teams'][teamId]['name']
                plural = "s" if num_wonders > 1 else ""
                self.state['game_log'].append({'message': f"Team {team_name} gains {num_wonders} bonus action{plural} from its Wonder{plural}.", 'short_message': f'[WONDER:+{num_wonders}ACT]'})
                for _ in range(num_wonders):
                    actions_queue.append({'teamId': teamId, 'is_bonus': True})

        random.shuffle(actions_queue)
        self.state['actions_queue_this_turn'] = actions_queue

    def _start_new_turn(self):
        """Performs start-of-turn maintenance and sets up the action queue for the new turn."""
        self.state['turn'] += 1
        self.state['action_in_turn'] = 0
        self.state['last_action_details'] = {}
        self.state['new_turn_events'] = []
        
        self._process_shields_and_stasis()
        self._process_rift_traps()
        self._process_anchors()
        self._process_heartwoods()
        self._process_whirlpools()
        self._process_monoliths()
        
        if self._process_wonders():
            return # Game ended via Wonder victory

        self._process_spires_fissures_barricades()
        self._build_action_queue()
        
    def _check_end_of_turn_victory_conditions(self):
        """Checks for victory conditions that are evaluated at the end of a full turn."""
        # Get unique team IDs that had actions this turn
        active_teams = list(set(info['teamId'] for info in self.state['actions_queue_this_turn'] if info))
        
        # 1. Dominance Victory
        DOMINANCE_TURNS_REQUIRED = 3
        if len(active_teams) == 1:
            sole_survivor_id = active_teams[0]
            tracker = self.state['sole_survivor_tracker']
            if tracker['teamId'] == sole_survivor_id:
                tracker['turns'] += 1
            else:
                tracker['teamId'] = sole_survivor_id
                tracker['turns'] = 1
            
            if tracker['turns'] >= DOMINANCE_TURNS_REQUIRED:
                self.state['game_phase'] = 'FINISHED'
                team_name = self.state['teams'][sole_survivor_id]['name']
                self.state['victory_condition'] = f"Team '{team_name}' achieved dominance."
                self.state['game_log'].append({'message': self.state['victory_condition'], 'short_message': '[VICTORY]'})
                return
        else:
            self.state['sole_survivor_tracker'] = {'teamId': None, 'turns': 0}

        # 2. Max Turns Reached
        if self.state['turn'] >= self.state['max_turns']:
            self.state['game_phase'] = 'FINISHED'
            self.state['victory_condition'] = "Max turns reached."
            self.state['game_log'].append({'message': "Max turns reached. Game finished.", 'short_message': '[END]'})

    def _get_action_log_messages(self, result):
        """Generates the long and short log messages for a given action result."""
        action_type = result.get('type')

        if action_type in self.ACTION_LOG_GENERATORS:
            long_msg, short_msg = self.ACTION_LOG_GENERATORS[action_type](result)
            return long_msg, short_msg
        
        # Fallback for any action that might not have a custom message
        return "performed a successful action.", "[ACTION]"

    def run_next_action(self):
        """Runs a single successful action for the next team in the current turn."""
        if self.state['game_phase'] != 'RUNNING':
            return

        self.state['action_events'] = [] # Clear events from the previous action

        # Check if we need to start a new turn.
        is_turn_over = not self.state.get('actions_queue_this_turn') or \
                       self.state['action_in_turn'] >= len(self.state['actions_queue_this_turn'])

        if is_turn_over:
            self._start_new_turn()
            
            # After starting a new turn, the game might have ended (e.g., Wonder victory)
            if self.state['game_phase'] != 'RUNNING':
                return

            # Or, the new turn might have no actions (extinction)
            if not self.state['actions_queue_this_turn']:
                self.state['game_phase'] = 'FINISHED'
                self.state['victory_condition'] = "Extinction"
                self.state['game_log'].append({'message': "All teams have been eliminated. Game over.", 'short_message': '[EXTINCTION]'})
                return

        # If we reach here, we are guaranteed to be in a turn with a valid action to perform.
        action_info = self.state['actions_queue_this_turn'][self.state['action_in_turn']]
        teamId = action_info['teamId']
        is_bonus_action = action_info['is_bonus']
        
        # Update all special structures for the current team right before it acts.
        # This ensures the team acts based on its most current state.
        self._update_runes_for_team(teamId)
        self._update_prisms_for_team(teamId)
        self._update_trebuchets_for_team(teamId)
        # We also re-update nexuses here mainly so the frontend display is accurate
        # if a nexus is created or destroyed mid-turn. Bonus actions for this turn
        # are already locked in from _start_new_turn.
        self._update_nexuses_for_team(teamId)

        team_name = self.state['teams'][teamId]['name']
        
        # --- Perform a successful action for this team, trying until one succeeds ---
        result = None
        failed_actions = []
        MAX_ACTION_ATTEMPTS = 15 # Avoid infinite loops if no action can ever succeed
        
        for _ in range(MAX_ACTION_ATTEMPTS):
            action_name, action_func = self._choose_action_for_team(teamId, exclude_actions=failed_actions)
            
            if not action_func:
                result = {'success': False, 'reason': 'no possible actions'}
                break # No more actions available to try
            
            attempt_result = action_func(teamId)
            
            if attempt_result.get('success'):
                result = attempt_result
                break # Success, action is done
            else:
                # Action failed, add its name to the exclusion list for the next attempt
                failed_actions.append(action_name)
        else:
            # This 'else' belongs to the 'for' loop, running if it finishes without a 'break'
            result = {'success': False, 'reason': 'all attempted actions failed'}
            
        if result.get('success'):
            if self.state['action_events']:
                result['action_events'] = self.state['action_events'][:]
            self.state['last_action_details'] = result
        else:
            self.state['last_action_details'] = {}
        
        # --- Log the final result using the new helper method ---
        log_message = f"Team {team_name} "
        short_log_message = "[ACTION]"

        if is_bonus_action:
            log_message = f"[BONUS] Team {team_name} "

        if result.get('success'):
            long_msg_part, short_log_message = self._get_action_log_messages(result)
            log_message += long_msg_part
        else:
            log_message += "could not find a valid move and passed its turn."
            short_log_message = "[PASS]"
            
        self.state['game_log'].append({'teamId': teamId, 'message': log_message, 'short_message': short_log_message})
        
        # Increment for next action
        self.state['action_in_turn'] += 1
        
        # If this was the last action of the turn, check for victory conditions
        if self.state['action_in_turn'] >= len(self.state['actions_queue_this_turn']):
            self._check_end_of_turn_victory_conditions()
    
    # --- Interpretation ---

    def _generate_divination_text(self, stats):
        """Generates a short, horoscope-like text based on team stats."""
        if stats['point_count'] == 0:
            return "Faded from existence, a whisper in the cosmos."

        # Ratios
        line_density = stats['line_count'] / stats['point_count'] if stats['point_count'] > 0 else 0
        area_efficiency = stats['controlled_area'] / stats['hull_area'] if stats['hull_area'] > 0 else 0

        # Dominance checks
        if stats.get('aggression_score', 0) > 2: # Made-up stat for now
             return "A path of conflict and dominance, shaping destiny through force."
        if area_efficiency > 0.6 and stats['triangles'] > 2:
            return "A builder of empires, turning chaotic space into ordered, controlled territory."
        if stats['hull_area'] > 50 and area_efficiency < 0.2:
            return "An expansive and ambitious spirit, reaching for the outer edges of possibility."
        if line_density > 1.4: # Very interconnected
            return "An intricate and thoughtful strategist, weaving a complex web of influence."
        if stats['line_length'] > 100:
            return "A far-reaching presence, connecting distant ideas and holding vast influence."
        
        return "A balanced force, showing steady and stable development."


    def calculate_interpretation(self):
        """Calculates geometric properties for each team."""
        interpretation = {}
        all_points = self.state['points']
        for teamId, team_data in self.state['teams'].items():
            team_point_ids = self.get_team_point_ids(teamId)
            team_points_dict = {pid: all_points[pid] for pid in team_point_ids if pid in all_points}
            team_points_list = list(team_points_dict.values())
            
            team_lines = self.get_team_lines(teamId)
            team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]

            if len(team_points_list) < 1:
                 interpretation[teamId] = { 'point_count': 0, 'line_count': 0, 'line_length': 0, 'triangles': 0, 'controlled_area': 0, 'hull_area': 0, 'hull_perimeter': 0, 'hull_points': [], 'divination_text': 'Faded from existence.'}
                 continue

            # 1. Total Line Length
            total_length = 0
            for line in team_lines:
                if line['p1_id'] in all_points and line['p2_id'] in all_points:
                    p1 = all_points[line['p1_id']]
                    p2 = all_points[line['p2_id']]
                    total_length += math.sqrt(distance_sq(p1, p2))

            # 2. Triangle Count
            adj = {pid: set() for pid in team_point_ids}
            for line in team_lines:
                if line['p1_id'] in adj and line['p2_id'] in adj:
                    adj[line['p1_id']].add(line['p2_id'])
                    adj[line['p2_id']].add(line['p1_id'])
            
            triangles = 0
            sorted_point_ids = sorted(list(team_point_ids))
            for i in sorted_point_ids:
                for j in adj.get(i, set()):
                    if j > i:
                        for k in adj.get(j, set()):
                            if k > j and k in adj.get(i, set()):
                                triangles += 1
            
            # 3. Convex Hull and its properties (using Graham Scan)
            hull_points = self._get_convex_hull(team_points_list)
            hull_area = 0
            hull_perimeter = 0
            if len(hull_points) >= 3:
                hull_area = self._polygon_area(hull_points)
                hull_perimeter = self._polygon_perimeter(hull_points)

            # 4. Total Controlled Area from territories
            controlled_area = 0
            for territory in team_territories:
                triangle_point_ids = territory['point_ids']
                if all(pid in all_points for pid in triangle_point_ids):
                    triangle_points = [all_points[pid] for pid in triangle_point_ids]
                    if len(triangle_points) == 3:
                        controlled_area += self._polygon_area(triangle_points)


            stats = {
                'point_count': len(team_points_list),
                'line_count': len(team_lines),
                'line_length': round(total_length, 2),
                'triangles': triangles,
                'controlled_area': round(controlled_area, 2),
                'hull_area': round(hull_area, 2),
                'hull_perimeter': round(hull_perimeter, 2),
                'hull_points': hull_points
            }
            stats['divination_text'] = self._generate_divination_text(stats)
            interpretation[teamId] = stats
            
        return interpretation

    def _get_convex_hull(self, points):
        """Computes the convex hull of a set of points using Graham Scan."""
        if len(points) < 3:
            return points
        
        # Find pivot (lowest y, then lowest x)
        pivot = min(points, key=lambda p: (p['y'], p['x']))
        
        # Sort points by polar angle with pivot
        sorted_points = sorted(
            [p for p in points if p != pivot], 
            key=lambda p: (math.atan2(p['y'] - pivot['y'], p['x'] - pivot['x']), distance_sq(p, pivot))
        )
        
        hull = [pivot]
        for p in sorted_points:
            while len(hull) >= 2 and orientation(hull[-2], hull[-1], p) != 2: # 2 = counter-clockwise
                hull.pop()
            hull.append(p)
            
        return hull

    def _is_point_inside_triangle(self, point, tri_p1, tri_p2, tri_p3):
        """Checks if a point is inside a triangle defined by three other points."""
        main_area = self._polygon_area([tri_p1, tri_p2, tri_p3])
        if main_area < 0.01: # Degenerate triangle
            return False

        area1 = self._polygon_area([point, tri_p2, tri_p3])
        area2 = self._polygon_area([tri_p1, point, tri_p3])
        area3 = self._polygon_area([tri_p1, tri_p2, point])
        
        # Check if sum of sub-triangle areas equals the main triangle area (with tolerance)
        return abs((area1 + area2 + area3) - main_area) < 0.01

    def _polygon_area(self, points):
        """Calculates area of a polygon using Shoelace formula."""
        area = 0.0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i]['x'] * points[j]['y']
            area -= points[j]['x'] * points[i]['y']
        return abs(area) / 2.0

    def _polygon_perimeter(self, points):
        """Calculates the perimeter of a polygon."""
        perimeter = 0.0
        n = len(points)
        for i in range(n):
            p1 = points[i]
            p2 = points[(i + 1) % n]
            perimeter += math.sqrt(distance_sq(p1, p2))
        return perimeter

    # --- Rune System ---
    
    def _update_runes_for_team(self, teamId):
        """Checks and updates all rune states for a given team by delegating to the FormationManager."""
        if teamId not in self.state['runes']:
            self.state['runes'][teamId] = {}

        team_point_ids = self.get_team_point_ids(teamId)
        team_lines = self.get_team_lines(teamId)
        all_points = self.state['points']
        fm = self.formation_manager

        self.state['runes'][teamId] = {
            'cross': fm.check_cross_rune(team_point_ids, team_lines, all_points),
            'v_shape': fm.check_v_rune(team_point_ids, team_lines, all_points),
            'shield': fm.check_shield_rune(team_point_ids, team_lines, all_points),
            'trident': fm.check_trident_rune(team_point_ids, team_lines, all_points),
            'hourglass': fm.check_hourglass_rune(team_point_ids, team_lines, all_points),
            'star': fm.check_star_rune(team_point_ids, team_lines, all_points),
            'barricade': fm.check_barricade_rune(team_point_ids, team_lines, all_points),
            't_shape': fm.check_t_rune(team_point_ids, team_lines, all_points),
            'plus_shape': fm.check_plus_rune(team_point_ids, team_lines, all_points),
            'i_shape': fm.check_i_rune(team_point_ids, team_lines, all_points),
            'parallel': fm.check_parallel_rune(team_point_ids, team_lines, all_points),
        }

    def rune_action_parallel_discharge(self, teamId):
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
            mid1 = self._points_centroid([d1_p1, d1_p2])
            mid2 = self._points_centroid([d2_p1, d2_p2])
            
            grid_size = self.state['grid_size']
            p1_coords = {
                'x': round(max(0, min(grid_size - 1, mid1['x']))),
                'y': round(max(0, min(grid_size - 1, mid1['y'])))
            }
            p2_coords = {
                'x': round(max(0, min(grid_size - 1, mid2['x']))),
                'y': round(max(0, min(grid_size - 1, mid2['y'])))
            }
            
            is_valid1, _ = self._is_spawn_location_valid(p1_coords, teamId)
            is_valid2, _ = self._is_spawn_location_valid(p2_coords, teamId)
            
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

    def rune_action_hourglass_stasis(self, teamId):
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
        
        enemy_points = self._get_vulnerable_enemy_points(teamId)
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
            
            sacrificed_point_data = self._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
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
        bastion_line_ids = self._get_bastion_line_ids()
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

    def rune_action_starlight_cascade(self, teamId):
        """[RUNE ACTION]: A Star Rune sacrifices a point to damage nearby enemy lines."""
        possible_cascades = self._find_possible_starlight_cascades(teamId)
        if not possible_cascades:
            return {'success': False, 'reason': 'no valid targets for starlight cascade'}

        chosen_cascade = random.choice(possible_cascades)
        rune = chosen_cascade['rune']
        p_to_sac_id = chosen_cascade['sac_point_id']
        sacrificed_point_data = self._delete_point_and_connections(p_to_sac_id, aggressor_team_id=teamId)
        
        if not sacrificed_point_data:
            return {'success': False, 'reason': 'failed to sacrifice rune point'}
            
        # Define damage area
        damage_radius_sq = (self.state['grid_size'] * 0.3)**2
        
        # Find enemy lines within the area
        enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
        bastion_line_ids = self._get_bastion_line_ids()
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

    def rune_action_focus_beam(self, teamId):
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
                p for p in self._get_vulnerable_enemy_points(teamId) if 
                p['id'] in self._get_bastion_point_ids()['cores'] or 
                p['id'] in {pid for m in self.state.get('monoliths', {}).values() for pid in m['point_ids']}
            ]
            if high_value_points:
                target_point = min(high_value_points, key=lambda p: distance_sq(center_point, p))
                target_type = 'high_value_point'
        
        # 2. Fallback to any vulnerable enemy
        if not target_type:
            vulnerable_targets = self._get_vulnerable_enemy_points(teamId)
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
                destroyed_point_data = self._delete_point_and_connections(target_point['id'], aggressor_team_id=teamId)
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
            enemy_centroid = self._points_centroid(enemy_team_points[largest_enemy_team_id])

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

    def _update_prisms_for_team(self, teamId):
        """Checks for Prism formations by delegating to the FormationManager."""
        if 'prisms' not in self.state: self.state['prisms'] = {}
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        self.state['prisms'][teamId] = self.formation_manager.check_prisms(team_territories)

    def rune_action_cardinal_pulse(self, teamId):
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
            sac_data = self._delete_point_and_connections(pid, aggressor_team_id=teamId)
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

            border_point = self._get_extended_border_point(center_point, arm_point_data)
            if not border_point: continue

            attack_ray = {'p1': center_point, 'p2': border_point}
            attack_rays.append(attack_ray)
            
            # This is complex because points/lines are being removed as we iterate.
            # We need to check against the current state of the board for each beam.
            enemy_lines = [l for l in self.state['lines'] if l['teamId'] != teamId]
            hits = []
            for enemy_line in enemy_lines:
                 # Cardinal Pulse is powerful, it bypasses shields but not bastions.
                if enemy_line.get('id') in self._get_bastion_line_ids(): continue
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
                is_valid, _ = self._is_spawn_location_valid(border_point, teamId)
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

    def rune_action_t_hammer_slam(self, teamId):
        """[RUNE ACTION]: A T-Rune sacrifices its head to push points away from its stem."""
        active_t_runes = self.state.get('runes', {}).get(teamId, {}).get('t_shape', [])
        if not active_t_runes:
            return {'success': False, 'reason': 'no active T-Runes'}
            
        rune = random.choice(active_t_runes)
        points = self.state['points']
        
        if not all(pid in points for pid in rune['all_points']):
            return {'success': False, 'reason': 'rune points no longer exist'}
            
        # Sacrifice the head point
        sacrificed_point_data = self._delete_point_and_connections(rune['head_id'], aggressor_team_id=teamId)
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
            for line in self.get_team_lines(teamId):
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

    def _update_trebuchets_for_team(self, teamId):
        """Checks for Trebuchet formations by delegating to the FormationManager."""
        if 'trebuchets' not in self.state: self.state['trebuchets'] = {}

        team_point_ids = self.get_team_point_ids(teamId)
        team_lines = self.get_team_lines(teamId)
        
        self.state['trebuchets'][teamId] = self.formation_manager.check_trebuchets(
            team_point_ids, team_lines, self.state['points']
        )


# --- Global Game Instance ---
# This is a singleton pattern. The Flask app will interact with this instance.
game = Game()