import random
import math
import uuid  # For unique point IDs
from itertools import combinations
from .geometry import (
    distance_sq, on_segment, orientation, segments_intersect,
    get_segment_intersection_point, is_ray_blocked, get_extended_border_point,
    polygon_area, points_centroid, polygon_perimeter, get_convex_hull
)
from .formations import FormationManager
from . import game_data
from . import structure_data
from .actions.expand_actions import ExpandActionsHandler
from .actions.fortify_actions import FortifyActionsHandler
from .actions.fight_actions import FightActionsHandler
from .actions.sacrifice_actions import SacrificeActionsHandler
from .actions.rune_actions import RuneActionsHandler
from .turn_processor import TurnProcessor

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
        self.fortify_handler = FortifyActionsHandler(self)
        self.fight_handler = FightActionsHandler(self)
        self.sacrifice_handler = SacrificeActionsHandler(self)
        self.rune_handler = RuneActionsHandler(self)
        self.turn_processor = TurnProcessor(self)
        self._init_action_preconditions()

    def _init_action_preconditions(self):
        """Dynamically maps action names to their precondition check methods based on ACTION_MAP."""
        self.action_preconditions = {}
        for action_name, (handler_name, method_name) in self.ACTION_MAP.items():
            handler = getattr(self, handler_name, None)
            if handler:
                precondition_method_name = f"can_perform_{method_name}"
                precondition_method = getattr(handler, precondition_method_name, None)
                if precondition_method and callable(precondition_method):
                    self.action_preconditions[action_name] = precondition_method
                else:
                    # This can be used for debugging missing precondition methods.
                    # For now, we silently ignore missing ones.
                    pass

    def reset(self):
        """Initializes or resets the game state with default teams."""
        # Using fixed IDs for default teams ensures they can be referenced consistently.
        default_teams = {tid: t.copy() for tid, t in game_data.DEFAULT_TEAMS.items()}
        self.state = {
            "grid_size": 10,
            "teams": default_teams,
            "points": {},
            "lines": [],  # Each line will now get a unique ID
            "shields": {}, # {line_id: turns_left}
            "anchors": {}, # {point_id: {teamId: teamId, turns_left: N}}
            "stasis_points": {}, # {point_id: turns_left}
            "isolated_points": {}, # {point_id: turns_left}
            "territories": [], # Added for claimed triangles
            "bastions": {}, # {bastion_id: {teamId, core_id, prong_ids}}
            "runes": {}, # {teamId: {'cross': [], 'v_shape': [], 'shield': [], 'trident': [], 'hourglass': [], 'star': [], 'barricade': [], 't_shape': [], 'plus_shape': [], 'i_shape': [], 'parallel': []}}
            "nexuses": {}, # {teamId: [nexus1, nexus2, ...]}
            "attuned_nexuses": {}, # {nexus_id: {teamId, turns_left, center, point_ids, radius_sq}}
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
            "scorched_zones": [], # {teamId, points, turns_left}
            "wonders": {}, # {wonder_id: {teamId, type, turns_to_victory, ...}}
            "ley_lines": {}, # {ley_line_id: {teamId, point_ids, turns_left, bonus_radius_sq}}
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
            augmented_point['is_isolated'] = pid in self.state.get('isolated_points', {})
            augmented_points[pid] = augmented_point
        return augmented_points

    def _check_and_apply_ley_line_bonus(self, new_point):
        """Checks if a newly created point is near a friendly Ley Line and applies the bonus if so."""
        if not self.state.get('ley_lines'):
            return None

        team_ley_lines = [ll for ll in self.state['ley_lines'].values() if ll['teamId'] == new_point['teamId']]
        if not team_ley_lines:
            return None

        closest_ley_line_point = None
        min_dist_sq_to_ley_line = float('inf')

        for ley_line in team_ley_lines:
            # Broad phase check: Check if the new point is roughly within the bounding box + radius of the ley line
            points_on_line = [self.state['points'][pid] for pid in ley_line['point_ids'] if pid in self.state['points']]
            if not points_on_line: continue
            
            centroid = points_centroid(points_on_line)
            # A very rough check to see if the point is anywhere near the ley line's general area
            if distance_sq(new_point, centroid) > (polygon_perimeter(points_on_line)**2 / 4) + ley_line['bonus_radius_sq']:
                 continue

            for pid in ley_line['point_ids']:
                if pid not in self.state['points']: continue
                ley_point = self.state['points'][pid]
                dist_sq = distance_sq(new_point, ley_point)
                
                if dist_sq < ley_line['bonus_radius_sq']:
                    if dist_sq < min_dist_sq_to_ley_line:
                        min_dist_sq_to_ley_line = dist_sq
                        closest_ley_line_point = ley_point

        if closest_ley_line_point:
            # Apply bonus: create a new line to the closest point on the ley line
            line_id = self._generate_id('l')
            bonus_line = {"id": line_id, "p1_id": new_point['id'], "p2_id": closest_ley_line_point['id'], "teamId": new_point['teamId']}
            self.state['lines'].append(bonus_line)

            # Log this bonus event
            team_name = self.state['teams'][new_point['teamId']]['name']
            log_msg = f"A new point for Team {team_name} was empowered by a nearby Ley Line, creating a bonus connection!"
            self.state['game_log'].append({'message': log_msg, 'short_message': '[LEY LINE BONUS!]', 'teamId': new_point['teamId']})
            self.state['action_events'].append({
                'type': 'ley_line_bonus',
                'bonus_line': bonus_line
            })

            return bonus_line
        
        return None

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
                        controlled_area += polygon_area(triangle_points)

            live_stats[teamId] = {
                'point_count': len(team_point_ids),
                'line_count': len(team_lines),
                'controlled_area': round(controlled_area, 2)
            }
        return live_stats

    def _generate_id(self, prefix):
        """Generates a unique ID with a given prefix."""
        return f"{prefix}_{uuid.uuid4().hex[:6]}"

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
            point_id = self._generate_id('p')
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

        for team_runes in self.state.get('runes', {}).values():
            for i_rune in team_runes.get('i_shape', []):
                ids['i_rune'].update(i_rune.get('point_ids', []))
                ids['i_rune_sentry_eye'].update(i_rune.get('internal_points', []))
                ids['i_rune_sentry_post'].update(i_rune.get('endpoints', []))
        
        # Structures that are dicts of lists {teamId: [item, ...]}
        list_structures = {'nexus': 'nexuses', 'trebuchet': 'trebuchets', 'purifier': 'purifiers'}
        for key, state_key in list_structures.items():
            for team_list in self.state.get(state_key, {}).values():
                for struct in team_list:
                    ids[key].update(struct.get('point_ids', []))

        # Structures that are dicts of dicts {itemId: {..., point_ids: [...]}}
        dict_structures = {'monolith': 'monoliths'}
        for key, state_key in dict_structures.items():
            for struct in self.state.get(state_key, {}).values():
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
        return {pid for t in self.state.get('territories', []) for pid in t['point_ids']}

    def _is_line_energized(self, line):
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

    def _get_bastion_point_ids(self):
        """Returns a dict of bastion core and prong point IDs."""
        bastions = self.state.get('bastions', {}).values()
        core_ids = {b['core_id'] for b in bastions if 'core_id' in b}
        prong_ids = {pid for b in bastions if 'prong_ids' in b for pid in b['prong_ids']}
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
        # Remove connected lines (and their shields/strength)
        lines_to_remove = [l for l in self.state['lines'] if point_id in (l['p1_id'], l['p2_id'])]
        self.state['lines'] = [l for l in self.state['lines'] if l not in lines_to_remove]
        for l in lines_to_remove:
            self.state['shields'].pop(l.get('id'), None)
            self.state['line_strengths'].pop(l.get('id'), None)

        # --- Generic and Custom Structure Cleanup from Registry ---
        for definition in structure_data.STRUCTURE_DEFINITIONS.values():
            state_key = definition['state_key']
            storage = self.state.get(state_key)
            if not storage:
                continue

            # Handle custom logic first
            if definition.get('cleanup_logic') == 'custom':
                if state_key == 'bastions':
                    bastions_to_dissolve = []
                    for bastion_id, bastion in list(storage.items()):
                        if bastion.get('core_id') == point_id:
                            bastions_to_dissolve.append(bastion_id)
                        elif point_id in bastion.get('prong_ids', []):
                            bastion['prong_ids'].remove(point_id)
                            if len(bastion['prong_ids']) < 2:
                                bastions_to_dissolve.append(bastion_id)
                    for bastion_id in bastions_to_dissolve:
                        if bastion_id in storage: del storage[bastion_id]
                continue

            # Generic handling for other structures that dissolve if a point is lost
            storage_type = definition['storage_type']

            if storage_type == 'dict_keyed_by_pid':
                storage.pop(point_id, None)
                continue
            
            def structure_contains_point(struct_dict):
                if not struct_dict: return False
                for key_info in definition.get('point_id_keys', []):
                    if isinstance(key_info, tuple):
                        _, key_name = key_info
                        if point_id in struct_dict.get(key_name, []):
                            return True
                    else: # It's a string
                        if struct_dict.get(key_info) == point_id:
                            return True
                return False

            if storage_type == 'list':
                self.state[state_key] = [s for s in storage if not structure_contains_point(s)]
            elif storage_type == 'dict':
                ids_to_remove = [sid for sid, s in storage.items() if structure_contains_point(s)]
                for sid in ids_to_remove:
                    del storage[sid]
            elif storage_type == 'team_dict_list':
                for teamId in list(storage.keys()):
                    storage[teamId] = [s for s in storage[teamId] if not structure_contains_point(s)]

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

    def _get_vulnerable_enemy_points(self, teamId, immune_point_ids=None):
        """
        Returns a list of enemy points that are not immune to standard attacks.
        Can accept a pre-calculated set of immune point IDs for optimization.
        """
        if immune_point_ids is None:
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

    def _get_all_rune_point_ids(self, teamId):
        """
        Helper to get a set of all point IDs involved in any rune for a team.
        It inspects rune data structures to find point IDs dynamically.
        """
        rune_pids = set()
        team_runes_data = self.state.get('runes', {}).get(teamId, {})
        if not team_runes_data:
            return rune_pids

        for rune_category in team_runes_data.values():
            for rune_instance in rune_category:
                if isinstance(rune_instance, list):
                    rune_pids.update(rune_instance)
                elif isinstance(rune_instance, dict):
                    for value in rune_instance.values():
                        if isinstance(value, str) and value.startswith('p_'):
                            rune_pids.add(value)
                        elif isinstance(value, list) and value and isinstance(value[0], str) and value[0].startswith('p_'):
                            rune_pids.update(value)
        return rune_pids

    def _get_critical_structure_point_ids(self, teamId):
        """Returns a set of point IDs that are part of critical structures for a team, using the structure registry."""
        critical_pids = set()
        
        for definition in structure_data.STRUCTURE_DEFINITIONS.values():
            if not definition.get('is_critical'):
                continue

            state_key = definition['state_key']
            storage = self.state.get(state_key)
            if not storage:
                continue
                
            structures_to_check = []
            if definition['storage_type'] == 'list':
                structures_to_check = [s for s in storage if s.get('teamId') == teamId]
            elif definition['storage_type'] == 'dict':
                structures_to_check = [s for s in storage.values() if s.get('teamId') == teamId]
            elif definition['storage_type'] == 'team_dict_list':
                structures_to_check = storage.get(teamId, [])
            elif definition['storage_type'] == 'dict_keyed_by_pid':
                for pid, data in storage.items():
                    if data.get('teamId') == teamId:
                        critical_pids.add(pid)
                continue

            for struct in structures_to_check:
                for key_info in definition.get('point_id_keys', []):
                    if isinstance(key_info, tuple):
                        _, key_name = key_info
                        pids = struct.get(key_name)
                        if pids: critical_pids.update(pids)
                    else: # It's a string
                        point_id = struct.get(key_info)
                        if point_id:
                            critical_pids.add(point_id)

        # Runes are handled separately as they are complex and already have a helper
        critical_pids.update(self._get_all_rune_point_ids(teamId))
        
        return critical_pids

    def _find_non_critical_sacrificial_point(self, teamId):
        """
        Finds a point that can be sacrificed without crippling the team.
        A non-critical point is not part of a major structure and is not an articulation point.
        Returns a point_id or None.
        """
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) <= 2:
            return None

        critical_structure_pids = self._get_critical_structure_point_ids(teamId)
        
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

    def _find_articulation_points(self, teamId):
        """Finds all articulation points (cut vertices) for a team's graph."""
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) < 3:
            return []

        adj = {pid: set() for pid in team_point_ids}
        for line in self.get_team_lines(teamId):
            if line['p1_id'] in adj and line['p2_id'] in adj:
                adj[line['p1_id']].add(line['p2_id'])
                adj[line['p2_id']].add(line['p1_id'])

        # Standard algorithm for finding articulation points using DFS
        tin = {}  # discovery times
        low = {}  # lowest discovery time reachable
        timer = 0
        visited = set()
        articulation_points = set()

        def dfs(v, p=None):
            nonlocal timer
            visited.add(v)
            tin[v] = low[v] = timer
            timer += 1
            children = 0
            for to in adj.get(v, set()):
                if to == p:
                    continue
                if to in visited:
                    low[v] = min(low[v], tin[to])
                else:
                    dfs(to, v)
                    low[v] = min(low[v], low[to])
                    if low[to] >= tin[v] and p is not None:
                        articulation_points.add(v)
                    children += 1
            if p is None and children > 1:
                articulation_points.add(v)

        for pid in team_point_ids:
            if pid not in visited:
                dfs(pid)
        
        return list(articulation_points)

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

            centroid = points_centroid(prong_points)
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

    def _update_nexuses_for_team(self, teamId):
        """Checks for Nexus formations by delegating to the FormationManager."""
        if 'nexuses' not in self.state: self.state['nexuses'] = {}
        
        team_point_ids = self.get_team_point_ids(teamId)
        team_lines = self.get_team_lines(teamId)
        
        self.state['nexuses'][teamId] = self.formation_manager.check_nexuses(
            team_point_ids, team_lines, self.state['points']
        )

    def _get_all_actions_status(self, teamId):
        """
        Checks all available actions and returns a dictionary with their validity
        and a reason for invalidity, using the centralized precondition checks.
        """
        status = {}
        for action_name, precon_func in self.action_preconditions.items():
            is_valid, reason = precon_func(teamId)
            status[action_name] = {'valid': is_valid, 'reason': "" if is_valid else reason}
        
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
        self._update_structures_for_team(teamId)

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
        action_map_entry = self.ACTION_MAP.get(chosen_action_name)
        if not action_map_entry:
            return chosen_action_name, None
            
        handler_name, method_name = action_map_entry
        handler = getattr(self, handler_name, None)
        if not handler:
            return chosen_action_name, None
            
        action_func = getattr(handler, method_name, None)
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
        
        game_ended = self.turn_processor.process_turn_start_effects()
        if game_ended:
            return

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

    def _update_structures_for_team(self, teamId):
        """
        A helper to update all complex structures for a given team.
        This is called before determining actions or executing an action to ensure
        the game state is based on the latest formations.
        """
        self._update_runes_for_team(teamId)
        self._update_prisms_for_team(teamId)
        self._update_trebuchets_for_team(teamId)
        self._update_nexuses_for_team(teamId)

    def run_next_action(self):
        """Runs a single successful action for the next team in the current turn."""
        if self.state['game_phase'] != 'RUNNING':
            return

        self.state['action_events'] = [] # Clear events from the previous action

        # If the current turn is over, start a new one. This might change game state.
        if (not self.state.get('actions_queue_this_turn') or
                self.state['action_in_turn'] >= len(self.state['actions_queue_this_turn'])):
            self._start_new_turn()

        # After any potential state change from starting a new turn, we perform final checks.
        # If the game is no longer running, or if there are no more actions, we stop.
        if self.state['game_phase'] != 'RUNNING':
            return

        if not self.state.get('actions_queue_this_turn') or \
           self.state['action_in_turn'] >= len(self.state['actions_queue_this_turn']):
            # This handles extinction or other end-of-game scenarios where no actions are possible.
            if self.state['game_phase'] == 'RUNNING': # Only log if not already ended by another condition
                self.state['game_phase'] = 'FINISHED'
                self.state['victory_condition'] = "Extinction"
                self.state['game_log'].append({'message': "All teams have been eliminated. Game over.", 'short_message': '[EXTINCTION]'})
            return

        action_info = self.state['actions_queue_this_turn'][self.state['action_in_turn']]
        teamId = action_info['teamId']
        is_bonus_action = action_info['is_bonus']
        
        # Update all special structures for the current team right before it acts.
        # This ensures the team acts based on its most current state.
        self._update_structures_for_team(teamId)

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
            all_triangles = self.formation_manager._find_all_triangles(team_point_ids, team_lines)
            triangles = len(all_triangles)
            
            # 3. Convex Hull and its properties (using Graham Scan)
            hull_points = get_convex_hull(team_points_list)
            hull_area = 0
            hull_perimeter = 0
            if len(hull_points) >= 3:
                hull_area = polygon_area(hull_points)
                hull_perimeter = polygon_perimeter(hull_points)

            # 4. Total Controlled Area from territories
            controlled_area = 0
            for territory in team_territories:
                triangle_point_ids = territory['point_ids']
                if all(pid in all_points for pid in triangle_point_ids):
                    triangle_points = [all_points[pid] for pid in triangle_point_ids]
                    if len(triangle_points) == 3:
                        controlled_area += polygon_area(triangle_points)


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


    def _update_prisms_for_team(self, teamId):
        """Checks for Prism formations by delegating to the FormationManager."""
        if 'prisms' not in self.state: self.state['prisms'] = {}
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        self.state['prisms'][teamId] = self.formation_manager.check_prisms(team_territories)



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