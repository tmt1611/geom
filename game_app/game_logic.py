import random
import math
import uuid  # For unique point IDs
import copy
from itertools import combinations
from collections import defaultdict
from .geometry import (
    distance_sq, on_segment, orientation, segments_intersect,
    get_segment_intersection_point, is_ray_blocked, get_extended_border_point,
    polygon_area, points_centroid, polygon_perimeter, get_convex_hull,
    is_spawn_location_valid as geom_is_spawn_location_valid,
    clamp_and_round_point_coords
)
from .formations import FormationManager
from . import game_data
from . import action_data
from . import structure_data
from .actions.expand_actions import ExpandActionsHandler
from .actions.fortify_actions import FortifyActionsHandler
from .actions.fight_actions import FightActionsHandler
from .actions.sacrifice_actions import SacrificeActionsHandler
from .actions.rune_actions import RuneActionsHandler
from .actions.terraform_actions import TerraformActionsHandler
from .turn_processor import TurnProcessor

# --- Game Class ---
class Game:
    """Encapsulates the entire game state and logic."""

    def __init__(self):
        self.formation_manager = FormationManager()
        self.reset()
        # Action handlers
        self.expand_handler = ExpandActionsHandler(self)
        self.fortify_handler = FortifyActionsHandler(self)
        self.fight_handler = FightActionsHandler(self)
        self.sacrifice_handler = SacrificeActionsHandler(self)
        self.rune_handler = RuneActionsHandler(self)
        self.terraform_handler = TerraformActionsHandler(self)
        self.turn_processor = TurnProcessor(self)
        self._init_action_preconditions()
        self._log_generators = game_data.get_log_generators()

    def _init_action_preconditions(self):
        """Dynamically maps action names to their precondition check methods based on ACTION_MAP."""
        self.action_preconditions = {}
        for action_name, data in action_data.ACTIONS.items():
            handler_name, method_name = data['handler'], data['method']
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
        default_teams = {t['id']: t.copy() for t in game_data.DEFAULT_TEAMS}
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
            "runes": {}, # {teamId: {rune_type: [rune_data, ...]}}. Populated by _update_structures_for_team.
            "attuned_nexuses": {}, # {nexus_id: {teamId, turns_left, center, point_ids, radius_sq}}
            "barricades": [], # {id, teamId, p1, p2, turns_left}
            "heartwoods": {}, # {teamId: {id, center_coords, growth_counter}}
            "whirlpools": [], # {id, teamId, coords, turns_left, strength, radius_sq}
            "monoliths": {}, # {monolith_id: {teamId, point_ids, ...}}
            "purifiers": {}, # {teamId: [purifier1, ...]}
            "rift_spires": {}, # {spire_id: {teamId, coords, charge}}
            "rift_traps": [], # {id, teamId, coords, turns_left, radius_sq}
            "fissures": [], # {id, p1, p2, turns_left}
            "scorched_zones": [], # {teamId, points, turns_left}
            "wonders": {}, # {wonder_id: {teamId, type, turns_to_victory, ...}}
            "ley_lines": {}, # {ley_line_id: {teamId, point_ids, turns_left, bonus_radius_sq}}
            "line_strengths": {}, # {line_id: strength}
            "regenerating_points": {}, # {point_id: {data: point_data, turns_left: N}}
            "game_log": [{'message': "Welcome! Default teams Alpha and Beta are ready. Place points to begin.", 'short_message': '[READY]'}],
            "turn": 0,
            "max_turns": 100,
            "game_phase": "SETUP", # SETUP, RUNNING, FINISHED
            "victory_condition": None,
            "interpretation": {},
            "last_action_details": {}, # For frontend visualization
            "initial_state": None, # Store the setup config for restarts
            "new_turn_events": [], # For visualizing things that happen at turn start
            "action_in_turn": 0, # Which action index in the current turn's queue
            "actions_queue_this_turn": [], # List of action dicts {teamId, is_bonus} for the current turn
            "no_cost_action_used_by_team_this_turn": set(), # Tracks which teams used a no-cost action
            "action_events": [] # For visualizing secondary effects of an action
        }

    def get_state(self):
        """Returns the current game state, augmenting with transient data for frontend."""
        if self.state['game_phase'] == 'FINISHED' and not self.state['interpretation']:
            self.state['interpretation'] = self.calculate_interpretation()

        state_copy = self.state.copy()
        
        # Convert sets to lists for JSON serialization
        if 'no_cost_action_used_by_team_this_turn' in state_copy:
            state_copy['no_cost_action_used_by_team_this_turn'] = list(state_copy['no_cost_action_used_by_team_this_turn'])

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
        point_flags = self._get_all_point_flags()
        
        # Get all unique flag names that can be applied to a point
        all_flag_names = list(point_flags.keys())

        augmented_points = {}
        for pid, point in points.items():
            augmented_point = point.copy()
            for flag_name in all_flag_names:
                # Set the flag to true if the point ID is in the set for that flag
                if pid in point_flags[flag_name]:
                    augmented_point[flag_name] = True
            augmented_points[pid] = augmented_point
        return augmented_points

    def _helper_spawn_on_border(self, teamId, border_point):
        """Helper to create a new point on the border if the location is valid. Returns the new point or None."""
        if not border_point:
            return None
        is_valid, _ = self.is_spawn_location_valid(border_point, teamId)
        if is_valid:
            new_point_id = self._generate_id('p')
            new_point = {**border_point, "teamId": teamId, "id": new_point_id}
            self.state['points'][new_point_id] = new_point
            # Check for ley line bonus on any border spawn
            self._check_and_apply_ley_line_bonus(new_point)
            return new_point
        return None

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

    def _find_first_ray_hit(self, ray_p1, ray_p2, target_lines, can_bypass_shields=False, ignored_line_ids=None):
        """
        Finds the closest intersection of a ray with a list of target lines.
        Returns a dictionary with hit details or None.
        """
        if ignored_line_ids is None:
            ignored_line_ids = set()

        points = self.state['points']
        closest_hit = None
        min_dist_sq = float('inf')

        for target_line in target_lines:
            is_shielded = target_line.get('id') in self.state['shields']
            if is_shielded and not can_bypass_shields:
                continue
            
            if target_line.get('id') in ignored_line_ids:
                continue
            
            if target_line['p1_id'] not in points or target_line['p2_id'] not in points:
                continue
            
            ep1 = points[target_line['p1_id']]
            ep2 = points[target_line['p2_id']]

            intersection_point = get_segment_intersection_point(ray_p1, ray_p2, ep1, ep2)
            if intersection_point:
                dist_sq = distance_sq(ray_p1, intersection_point)
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_hit = {
                        'target_line': target_line,
                        'intersection_point': intersection_point,
                        'bypassed_shield': is_shielded and can_bypass_shields
                    }
        return closest_hit

    def _iterate_structures(self, definition, teamId_filter=None):
        """
        A generator that yields structures from the game state based on a definition
        from the structure registry. Can optionally filter by teamId.
        """
        state_key = definition['state_key']
        storage = self.state.get(state_key)
        if not storage:
            return

        storage_type = definition['storage_type']

        if storage_type == 'dict_keyed_by_pid':
            # This type is special, yield (pid, data)
            for pid, data in storage.items():
                if teamId_filter is None or data.get('teamId') == teamId_filter:
                    yield (pid, data)
            return

        structures_to_process = []
        if storage_type == 'list':
            structures_to_process = storage
        elif storage_type == 'dict':
            structures_to_process = storage.values()
        elif storage_type == 'team_dict_list':
            if teamId_filter:
                structures_to_process = storage.get(teamId_filter, [])
            else: # All teams
                for team_list in storage.values():
                    structures_to_process.extend(team_list)
        elif storage_type == 'team_dict_of_structures':
            subtype_key = definition['structure_subtype_key']
            if teamId_filter:
                structures_to_process = storage.get(teamId_filter, {}).get(subtype_key, [])
            else: # All teams
                for team_structs in storage.values():
                    structures_to_process.extend(team_structs.get(subtype_key, []))

        is_already_team_filtered = (
            teamId_filter is not None and
            storage_type in ['team_dict_list', 'team_dict_of_structures']
        )
        for struct in structures_to_process:
            # If we've already filtered by teamId when getting the list,
            # we don't need to check again. This also handles cases where
            # the structure itself is a list (e.g., Cross Rune) and has no 'teamId' key.
            if is_already_team_filtered or teamId_filter is None or struct.get('teamId') == teamId_filter:
                yield struct

    def _get_pids_from_struct(self, struct, key_info_list):
        """Helper to extract all point IDs from a structure dict based on a list of key_info."""
        pids = set()
        for key_info in key_info_list:
            if isinstance(key_info, tuple):
                key_type, key_name = key_info
                if key_type == 'list':
                    pids_from_key = struct.get(key_name)
                    if pids_from_key: pids.update(pids_from_key)
                elif key_type == 'list_of_lists':
                    if isinstance(struct, list):
                        pids.update(struct)
            else: # string
                point_id = struct.get(key_info)
                if point_id:
                    pids.add(point_id)
        return pids

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
            'teams': {tid: t.copy() for tid, t in self.state['teams'].items()},
            'points': points, # Use original point list before IDs are added
            'max_turns': max_turns,
            'grid_size': grid_size
        }

    def augment_state_for_frontend(self, historical_state):
        """
        Augments a single historical state object with transient data for frontend display.
        This method is designed to be called on a raw state from the simulation history.
        It temporarily sets the game's state to the historical one to use its helper methods.
        """
        # Temporarily swap state to use helper methods that rely on self.state
        original_live_state = self.state
        self.state = historical_state
        try:
            state_copy = self.state.copy()
            
            # --- Calculate action probabilities for the team about to act in this state ---
            next_team_id = None
            if state_copy['game_phase'] == 'RUNNING' and state_copy.get('actions_queue_this_turn'):
                action_idx = state_copy['action_in_turn']
                queue = state_copy['actions_queue_this_turn']
                if action_idx < len(queue):
                    next_team_id = queue[action_idx]['teamId']
            
            if next_team_id:
                state_copy['action_probabilities'] = self.get_action_probabilities(next_team_id, include_invalid=False)
            else:
                state_copy['action_probabilities'] = None

            if state_copy['game_phase'] == 'FINISHED' and not state_copy.get('interpretation'):
                state_copy['interpretation'] = self.calculate_interpretation()
            
            if 'no_cost_action_used_by_team_this_turn' in state_copy:
                state_copy['no_cost_action_used_by_team_this_turn'] = list(state_copy['no_cost_action_used_by_team_this_turn'])

            state_copy['lines'] = self._augment_lines_for_frontend(self.state['lines'])
            state_copy['points'] = self._augment_points_for_frontend(self.state['points'])
            state_copy['live_stats'] = self._calculate_live_stats()

            return state_copy
        finally:
            self.state = original_live_state # Ensure we restore state

    def run_full_simulation_streamed(self, teams, points, max_turns, grid_size):
        """
        Runs a complete game simulation, yielding updates for streaming.
        Yields dicts with 'type' ('progress' or 'state') and 'data'.
        """
        self.start_game(teams, points, max_turns, grid_size)
        
        yield {"type": "state", "data": copy.deepcopy(self.state)}
        
        step = 0
        while self.state['game_phase'] == 'RUNNING':
            self.run_next_action()
            step += 1
            
            # Progress calculation
            turn = self.state['turn']
            action_in_turn = self.state['action_in_turn']
            actions_this_turn = len(self.state['actions_queue_this_turn'])
            
            if max_turns > 0:
                completed_turns = max(0, turn - 1)
                turn_progress = completed_turns / max_turns
                action_progress_in_turn = actions_this_turn > 0 and (action_in_turn / actions_this_turn) or 0
                total_progress = round((turn_progress + action_progress_in_turn / max_turns) * 100)
            else:
                total_progress = 0

            yield {"type": "progress", "data": {"progress": total_progress, "turn": turn, "max_turns": max_turns, "step": step}}
            yield {"type": "state", "data": copy.deepcopy(self.state)}
            
    def run_full_simulation(self, teams, points, max_turns, grid_size):
        """
        Runs a complete game simulation from a given setup and returns the raw history of states.
        This is a non-streaming version for Pyodide.
        """
        raw_history = []
        for update in self.run_full_simulation_streamed(teams, points, max_turns, grid_size):
            if update['type'] == 'state':
                raw_history.append(update['data'])
        return { "raw_history": raw_history }

    def restart_game_and_run_simulation_streamed(self):
        """Restarts the game with its initial settings and yields simulation updates."""
        initial_state = self.state.get('initial_state')
        if not initial_state:
            yield {"type": "error", "data": "No initial state saved to restart from."}
            return

        # The 'yield from' keyword is perfect here.
        yield from self.run_full_simulation_streamed(
            initial_state['teams'],
            initial_state['points'],
            initial_state['max_turns'],
            initial_state['grid_size']
        )

    def _get_all_point_flags(self):
        """
        Returns a dictionary mapping frontend flag names to sets of point IDs that have that flag.
        This is driven by the STRUCTURE_DEFINITIONS registry.
        """
        flags = defaultdict(set)

        for definition in structure_data.STRUCTURE_DEFINITIONS.values():
            flag_key = definition.get('frontend_flag_key')
            flag_keys_map = definition.get('frontend_flag_keys')
            if not flag_key and not flag_keys_map:
                continue

            if definition['storage_type'] == 'dict_keyed_by_pid':
                if flag_key:
                    for pid, _ in self._iterate_structures(definition):
                        flags[flag_key].add(pid)
                continue

            for struct in self._iterate_structures(definition):
                if flag_key:
                    pids = self._get_pids_from_struct(struct, definition.get('point_id_keys', []))
                    flags[flag_key].update(pids)
                elif flag_keys_map:
                    for internal_key, generated_keys in flag_keys_map.items():
                        point_ids_val = struct.get(internal_key, [])
                        pids_to_flag = set(point_ids_val) if isinstance(point_ids_val, list) else {point_ids_val} if point_ids_val else set()
                        
                        flag_names = [generated_keys] if isinstance(generated_keys, str) else generated_keys
                        for name in flag_names:
                            if name:
                                flags[name].update(pids_to_flag)
        return flags

    def get_team_point_ids(self, teamId):
        """Returns IDs of points belonging to a team."""
        # Iterating over a copy of items to prevent "dictionary changed size during iteration" errors
        # that can occur if this function is called from within another loop over the points dictionary.
        return [pid for pid, p in list(self.state['points'].items()) if p['teamId'] == teamId]

    def get_team_lines(self, teamId):
        """Returns lines belonging to a team."""
        return [l for l in self.state['lines'] if l['teamId'] == teamId]

    def _get_territory_boundary_line_keys(self, territory):
        """Returns a list of line keys for a single territory's boundaries."""
        p_ids = territory.get('point_ids', [])
        if len(p_ids) == 3:
            return [
                tuple(sorted((p_ids[0], p_ids[1]))),
                tuple(sorted((p_ids[1], p_ids[2]))),
                tuple(sorted((p_ids[2], p_ids[0])))
            ]
        return []

    def _get_all_territory_boundary_line_keys(self, teamId):
        """Returns a set of all line keys for a team's territory boundaries."""
        boundary_keys = set()
        team_territories = [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        for t in team_territories:
            boundary_keys.update(self._get_territory_boundary_line_keys(t))
        return boundary_keys

    def _reinforce_territory_boundaries(self, territory):
        """Strengthens the boundary lines of a given territory. Returns list of strengthened lines."""
        teamId = territory['teamId']
        boundary_lines_keys = self._get_territory_boundary_line_keys(territory)
        strengthened_lines = []
        for line in self.get_team_lines(teamId):
            if tuple(sorted((line['p1_id'], line['p2_id']))) in boundary_lines_keys:
                if self._strengthen_line(line):
                    strengthened_lines.append(line)
        return strengthened_lines

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

        log_msg = f"The destruction of a Nexus from {nexus_owner_name} by {aggressor_name} caused a violent energy discharge!"
        self.state['game_log'].append({'message': log_msg, 'short_message': '[NEXUS BOOM!]', 'teamId': nexus_owner_teamId, 'is_event': True})
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
                self._delete_line(line)
                destroyed_lines_count += 1

        if destroyed_points_count > 0 or destroyed_lines_count > 0:
            log_msg = f"The blast destroyed {destroyed_points_count} points and {destroyed_lines_count} lines."
            self.state['game_log'].append({'message': log_msg, 'short_message': '[CASCADE]', 'teamId': nexus_owner_teamId, 'is_event': True})

    def _delete_line(self, line_to_delete):
        """Removes a line from the state, along with any associated shield or strength."""
        if line_to_delete in self.state['lines']:
            self.state['lines'].remove(line_to_delete)
            line_id = line_to_delete.get('id')
            if line_id:
                self.state['shields'].pop(line_id, None)
                self.state['line_strengths'].pop(line_id, None)

    def _create_temporary_barricade(self, teamId, p1, p2, turns_left):
        """Creates a temporary barricade and adds it to the game state."""
        barricade_id = self._generate_id('bar')
        new_barricade = {
            'id': barricade_id, 'teamId': teamId,
            'p1': {'x': p1['x'], 'y': p1['y']}, 'p2': {'x': p2['x'], 'y': p2['y']},
            'turns_left': turns_left
        }
        self.state.setdefault('barricades', []).append(new_barricade)
        return new_barricade

    def _create_random_fissure(self, center_coords, length, turns_left):
        """Creates a fissure of a given length, centered at given coordinates."""
        grid_size = self.state['grid_size']
        fissure_id = self._generate_id('f')
        angle = random.uniform(0, math.pi)

        half_len = length / 2
        p1 = {
            'x': center_coords['x'] - half_len * math.cos(angle),
            'y': center_coords['y'] - half_len * math.sin(angle)
        }
        p2 = {
            'x': center_coords['x'] + half_len * math.cos(angle),
            'y': center_coords['y'] + half_len * math.sin(angle)
        }

        p1_clamped = clamp_and_round_point_coords(p1, grid_size)
        p2_clamped = clamp_and_round_point_coords(p2, grid_size)

        new_fissure = {'id': fissure_id, 'p1': p1_clamped, 'p2': p2_clamped, 'turns_left': turns_left}
        self.state.setdefault('fissures', []).append(new_fissure)
        return new_fissure

    def _push_points_in_radius(self, center, radius_sq, push_distance, points_to_check):
        """
        Pushes points from a given list within a radius away from a center point.
        Modifies points in-place.
        Returns a list of points that were moved.
        """
        pushed_points = []
        grid_size = self.state['grid_size']

        for point in points_to_check:
            if distance_sq(center, point) < radius_sq:
                dx = point['x'] - center['x']
                dy = point['y'] - center['y']
                dist = math.sqrt(dx**2 + dy**2)
                if dist < 0.1: continue

                new_x = point['x'] + (dx / dist) * push_distance
                new_y = point['y'] + (dy / dist) * push_distance
                
                new_coords = clamp_and_round_point_coords({'x': new_x, 'y': new_y}, grid_size)
                point['x'], point['y'] = new_coords['x'], new_coords['y']
                pushed_points.append(point.copy())
                
        return pushed_points

    def _cleanup_structures_for_point(self, point_id):
        """Helper to remove a point from all associated secondary structures after it has been deleted."""
        # Remove connected lines (and their shields/strength)
        lines_to_remove = [l for l in self.state['lines'] if point_id in (l['p1_id'], l['p2_id'])]
        for l in lines_to_remove:
            self._delete_line(l)

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

    def _delete_point_and_connections(self, point_id, aggressor_team_id=None, allow_regeneration=False):
        """A robust helper to delete a point and handle all cascading effects."""
        if point_id not in self.state['points']:
            return None # Point already gone

        point_data = self.state['points'][point_id]

        # Check for regeneration condition.
        # A point can regenerate if it's being sacrificed (allow_regeneration=True),
        # is not a critical articulation point, and is part of at least one line.
        is_articulation = point_id in self._find_articulation_points(point_data['teamId'])[0]
        is_on_line = any(point_id in (l['p1_id'], l['p2_id']) for l in self.get_team_lines(point_data['teamId']))
        
        if allow_regeneration and is_on_line and not is_articulation:
            # Point will be regenerated. Move it from `points` to `regenerating_points`.
            # Lines and structures are not cleaned up; they just become temporarily inactive
            # because the frontend/logic won't find the point in the main `points` dict.
            deleted_point_data = self.state['points'].pop(point_id)
            self.state['regenerating_points'][point_id] = {
                'data': deleted_point_data,
                'turns_left': 3
            }
            team_name = self.state['teams'][deleted_point_data['teamId']]['name']
            log_msg = f"A point from {team_name} was sacrificed and will attempt to regenerate in 3 turns."
            self.state['game_log'].append({'message': log_msg, 'short_message': '[SAC->REGEN]', 'teamId': deleted_point_data['teamId'], 'is_event': True})
            self.state['action_events'].append({'type': 'point_regenerate_start', 'point': deleted_point_data})
            return deleted_point_data

        # --- Standard (permanent) Deletion Logic ---

        # 1. Pre-deletion checks for cascades (e.g., Nexus detonation)
        nexus_to_detonate = None
        all_nexuses = [n for team_runes in self.state.get('runes', {}).values() for n in team_runes.get('nexus', [])]
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

    def _get_all_immune_point_ids(self):
        """Returns a set of all point IDs that are currently immune to standard attacks."""
        fortified_point_ids = self._get_fortified_point_ids()
        bastion_point_ids = self._get_bastion_point_ids()
        stasis_point_ids = set(self.state.get('stasis_points', {}).keys())
        return fortified_point_ids.union(
            bastion_point_ids['cores'], bastion_point_ids['prongs'], stasis_point_ids
        )

    def _get_vulnerable_enemy_points(self, teamId, immune_point_ids=None):
        """
        Returns a list of enemy points that are not immune to standard attacks.
        Can accept a pre-calculated set of immune point IDs for optimization.
        """
        if immune_point_ids is None:
            immune_point_ids = self._get_all_immune_point_ids()
        return [p for p in self.state['points'].values() if p['teamId'] != teamId and p['id'] not in immune_point_ids]

    def is_spawn_location_valid(self, new_point_coords, teamId, min_dist_sq=1.0, points_override=None):
        """A wrapper for the geometry function to pass game state automatically."""
        points = points_override if points_override is not None else self.state['points']
        return geom_is_spawn_location_valid(
            new_point_coords, teamId, self.state['grid_size'], points,
            self.state.get('fissures', []),
            self.state.get('heartwoods', {}),
            scorched_zones=self.state.get('scorched_zones', []),
            min_dist_sq=min_dist_sq
        )

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

    def _get_critical_structure_point_ids(self, teamId):
        """Returns a set of point IDs that are part of critical structures for a team, using the structure registry."""
        critical_pids = set()
        
        for definition in structure_data.STRUCTURE_DEFINITIONS.values():
            if not definition.get('is_critical'):
                continue
            
            if definition['storage_type'] == 'dict_keyed_by_pid':
                for pid, data in self._iterate_structures(definition, teamId):
                    critical_pids.add(pid)
                continue

            for struct in self._iterate_structures(definition, teamId):
                pids = self._get_pids_from_struct(struct, definition.get('point_id_keys', []))
                critical_pids.update(pids)
        
        return critical_pids

    def _find_repositionable_point(self, teamId):
        """
        Finds a point that can be freely moved without breaking critical formations.
        A "free" point is not part of a critical structure. The check for articulation points
        is omitted for these non-destructive actions to improve performance.
        Returns a point_id or None.
        """
        team_point_ids = self.get_team_point_ids(teamId)
        if not team_point_ids:
            return None

        critical_pids = self._get_critical_structure_point_ids(teamId)

        repositionable_pids = [
            pid for pid in team_point_ids 
            if pid not in critical_pids
        ]

        if not repositionable_pids:
            return None

        return random.choice(repositionable_pids)

    def _find_non_critical_sacrificial_point(self, teamId):
        """
        Finds a point that can be sacrificed without crippling the team.
        A non-critical point is not part of a major structure and is not an articulation point.
        A team must have more than 2 points to be able to sacrifice one.
        Returns a point_id or None.
        """
        team_point_ids = self.get_team_point_ids(teamId)
        if len(team_point_ids) <= 2:
            return None

        # 1. Exclude points from critical structures
        critical_structure_pids = self._get_critical_structure_point_ids(teamId)
        candidate_pids = [pid for pid in team_point_ids if pid not in critical_structure_pids]

        if not candidate_pids:
            return None

        # 2. Find and exclude articulation points. Also get the adjacency list.
        articulation_points, adj = self._find_articulation_points(teamId)
        articulation_point_pids = set(articulation_points)
        safe_candidates = [pid for pid in candidate_pids if pid not in articulation_point_pids]
        
        # Fallback: if all non-critical points are articulation points (e.g., in a line or simple cycle),
        # allow sacrificing them to prevent actions from being blocked.
        if not safe_candidates:
            safe_candidates = candidate_pids

        if not safe_candidates:
            return None
            
        # 3. Prioritize points with fewer connections (leaves are degree 1, which is best).
        safe_candidates.sort(key=lambda pid: len(adj.get(pid, [])), reverse=False)

        # To add some randomness but still prefer safer points, we pick from the top N safest.
        num_choices = min(3, len(safe_candidates))
        return random.choice(safe_candidates[:num_choices])

    def _get_team_adjacency_list(self, teamId):
        """Builds and returns an adjacency list for a team's graph by calling the formation manager."""
        return self.formation_manager.get_adjacency_list(
            self.get_team_point_ids(teamId),
            self.get_team_lines(teamId)
        )

    def _get_team_degrees(self, teamId):
        """Calculates point degrees for a team's graph by calling the formation manager."""
        return self.formation_manager.get_degrees(
            self.get_team_point_ids(teamId),
            self.get_team_lines(teamId)
        )

    def _find_articulation_points(self, teamId):
        """Finds all articulation points (cut vertices) for a team's graph. Returns (points, adj_list)."""
        team_point_ids = self.get_team_point_ids(teamId)
        adj = self._get_team_adjacency_list(teamId)
        
        if len(team_point_ids) < 3:
            return [], adj

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
        
        return list(articulation_points), adj


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
        exclude_actions = exclude_actions or []
        all_statuses = self._get_all_actions_status(teamId)
        return [
            name for name, status_info in all_statuses.items()
            if status_info['valid'] and name not in exclude_actions
        ]


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
        valid_actions_by_group = defaultdict(list)
        for action_name, status in all_action_statuses.items():
            if status['valid']:
                group = action_data.ACTIONS[action_name]['group']
                valid_actions_by_group[group].append(action_name)
        
        # Determine group weights based on trait and valid actions
        team_trait = self.state['teams'][teamId].get('trait', 'Balanced')
        group_multipliers = game_data.TRAIT_GROUP_MULTIPLIERS.get(team_trait, {})
        
        final_group_weights = {}
        for group_name, actions in valid_actions_by_group.items():
            if actions: # Only consider groups that have at least one valid action
                base_weight = game_data.GROUP_BASE_WEIGHTS.get(group_name, 0)
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
                        action_info = action_data.ACTIONS[action_name]
                        action_list.append({
                            'name': action_name,
                            'display_name': action_info.get('display_name', action_name),
                            'probability': round(action_prob, 1),
                            'no_cost': action_info.get('no_cost', False)
                        })

                if action_list:
                     response['groups'][group_name] = {
                        'group_probability': round(group_prob, 1),
                        'actions': sorted(action_list, key=lambda x: x['display_name'])
                     }

        if include_invalid:
            for name, status in all_action_statuses.items():
                if not status['valid']:
                    action_info = action_data.ACTIONS[name]
                    response['invalid'].append({
                        'name': name,
                        'display_name': action_info.get('display_name', name),
                        'reason': status['reason'],
                        'group': action_info.get('group', 'Other'),
                        'no_cost': action_info.get('no_cost', False)
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
        valid_actions_by_group = defaultdict(list)
        for action_name in possible_actions:
            group = action_data.ACTIONS[action_name]['group']
            valid_actions_by_group[group].append(action_name)

        # --- 3. Determine final group weights based on trait and which groups are actually possible ---
        team_trait = self.state['teams'][teamId].get('trait', 'Balanced')
        group_multipliers = game_data.TRAIT_GROUP_MULTIPLIERS.get(team_trait, {})
        
        final_group_weights = {}
        for group_name, actions in valid_actions_by_group.items():
            if actions: # Only consider groups that have at least one valid action
                base_weight = game_data.GROUP_BASE_WEIGHTS.get(group_name, 0)
                multiplier = group_multipliers.get(group_name, 1.0)
                final_group_weights[group_name] = base_weight * multiplier
        
        if not final_group_weights: return None, None # No valid groups to choose from

        # --- 4. Choose a group, then choose an action from that group ---
        group_names = list(final_group_weights.keys())
        group_weights = list(final_group_weights.values())
        
        chosen_group = random.choices(group_names, weights=group_weights, k=1)[0]
        chosen_action_name = random.choice(valid_actions_by_group[chosen_group])
        
        # --- 5. Return the chosen action name and its function ---
        action_details = action_data.ACTIONS.get(chosen_action_name)
        if not action_details:
            return chosen_action_name, None
            
        handler_name, method_name = action_details['handler'], action_details['method']
        handler = getattr(self, handler_name, None)
        if not handler:
            return chosen_action_name, None
            
        action_func = getattr(handler, method_name, None)
        return chosen_action_name, action_func


    # --- Start of Turn Processing ---

    def _build_action_queue(self):
        """Builds the action queue for the current turn, respecting team turns."""
        self.state['game_log'].append({'message': f"--- Turn {self.state['turn']} ---", 'short_message': f"~ T{self.state['turn']} ~"})
        
        # Determine the order of teams for this turn
        active_teams_ordered = [teamId for teamId in self.state['teams'] if len(self.get_team_point_ids(teamId)) > 0]
        random.shuffle(active_teams_ordered)
        
        final_actions_queue = []
        for teamId in active_teams_ordered:
            team_actions = []
            # Each team gets one base action
            team_actions.append({'teamId': teamId, 'is_bonus': False})

            # Update structures to check for bonus-granting ones like Nexuses at the start of the turn.
            self._update_structures_for_team(teamId)
            
            # Add bonus actions from Nexuses
            num_nexuses = len(self.state.get('runes', {}).get(teamId, {}).get('nexus', []))
            if num_nexuses > 0:
                team_name = self.state['teams'][teamId]['name']
                plural = "s" if num_nexuses > 1 else ""
                self.state['game_log'].append({'message': f"{team_name} gains {num_nexuses} bonus action{plural} from its Nexus{plural}.", 'short_message': f'[NEXUS:+{num_nexuses}ACT]'})
                for _ in range(num_nexuses):
                    team_actions.append({'teamId': teamId, 'is_bonus': True})

            # Add bonus actions from Wonders
            num_wonders = sum(1 for w in self.state.get('wonders', {}).values() if w['teamId'] == teamId)
            if num_wonders > 0:
                team_name = self.state['teams'][teamId]['name']
                plural = "s" if num_wonders > 1 else ""
                self.state['game_log'].append({'message': f"{team_name} gains {num_wonders} bonus action{plural} from its Wonder{plural}.", 'short_message': f'[WONDER:+{num_wonders}ACT]'})
                for _ in range(num_wonders):
                    team_actions.append({'teamId': teamId, 'is_bonus': True})
            
            # Add this team's block of actions to the final queue
            final_actions_queue.extend(team_actions)

        self.state['actions_queue_this_turn'] = final_actions_queue

    def _start_new_turn(self):
        """Performs start-of-turn maintenance and sets up the action queue for the new turn."""
        self.state['turn'] += 1
        self.state['action_in_turn'] = 0
        self.state['last_action_details'] = {}
        self.state['new_turn_events'] = []
        self.state['no_cost_action_used_by_team_this_turn'] = set()
        
        game_ended = self.turn_processor.process_turn_start_effects()
        if game_ended:
            return

        self._build_action_queue()
        
    def _check_end_of_turn_victory_conditions(self):
        """Checks for victory conditions that are evaluated at the end of a full turn."""
        
        # Check based on current point counts, not the action queue from the start of the turn.
        teams_with_points = [teamId for teamId in self.state['teams'] if len(self.get_team_point_ids(teamId)) > 0]
        
        # 1. Sole Survivor Victory (triggers immediately when only one team is left)
        if len(teams_with_points) == 1:
            winner_id = teams_with_points[0]
            self.state['game_phase'] = 'FINISHED'
            team_name = self.state['teams'][winner_id]['name']
            self.state['victory_condition'] = f"'{team_name}' is the sole survivor."
            self.state['game_log'].append({'message': self.state['victory_condition'], 'short_message': '[VICTORY]'})
            return

        # 2. Extinction (mutual destruction)
        if len(teams_with_points) == 0:
            self.state['game_phase'] = 'FINISHED'
            self.state['victory_condition'] = "Extinction"
            self.state['game_log'].append({'message': "All teams have been eliminated. Game over.", 'short_message': '[EXTINCTION]'})
            return

        # 3. Max Turns Reached
        if self.state['turn'] >= self.state['max_turns']:
            self.state['game_phase'] = 'FINISHED'
            self.state['victory_condition'] = "Max turns reached."
            self.state['game_log'].append({'message': "Max turns reached. Game finished.", 'short_message': '[END]'})

    def _get_action_log_messages(self, result):
        """Generates the long and short log messages for a given action result."""
        action_type = result.get('type')

        if action_type in self._log_generators:
            long_msg, short_msg = self._log_generators[action_type](result)
            return long_msg, short_msg
        
        # Fallback for any action that might not have a custom message
        return "performed a successful action.", "[ACTION]"

    def _update_structures_for_team(self, teamId):
        """
        A helper to update all complex structures for a given team by delegating to the FormationManager.
        This is called before determining actions or executing an action to ensure
        the game state is based on the latest formations.
        It uses the STRUCTURE_DEFINITIONS registry to determine which checks to run.
        """
        # --- Pre-fetch common inputs for formation checkers ---
        formation_inputs = {
            'team_point_ids': self.get_team_point_ids(teamId),
            'team_lines': self.get_team_lines(teamId),
            'all_points': self.state['points'],
            'team_territories': [t for t in self.state.get('territories', []) if t['teamId'] == teamId]
        }

        # --- Update structures based on the registry ---
        for definition in structure_data.STRUCTURE_DEFINITIONS.values():
            checker_name = definition.get('formation_checker')
            if not checker_name:
                continue

            state_key = definition['state_key']
            
            checker_func = getattr(self.formation_manager, checker_name, None)
            if not checker_func or not callable(checker_func):
                continue
            
            # Assemble arguments for the checker function
            required_inputs = definition.get('formation_inputs', [])
            args = [formation_inputs[key] for key in required_inputs]

            # Call the checker and update the state
            result = checker_func(*args)
            
            storage_type = definition['storage_type']
            if storage_type == 'team_dict_list':
                self.state.setdefault(state_key, {})[teamId] = result
            elif storage_type == 'team_dict_of_structures':
                self.state.setdefault(state_key, {}).setdefault(teamId, {})
                subtype_key = definition['structure_subtype_key']
                self.state[state_key][teamId][subtype_key] = result

    def run_next_action(self):
        """Runs a single successful action for the next team in the current turn."""
        if self.state['game_phase'] != 'RUNNING':
            return

        self.state['action_events'] = [] # Clear events from the previous action

        # If the current turn's action queue is exhausted, it's the end of the turn.
        if (not self.state.get('actions_queue_this_turn') or
                self.state['action_in_turn'] >= len(self.state['actions_queue_this_turn'])):
            # 1. Check for victory conditions based on the state at the end of the turn.
            self._check_end_of_turn_victory_conditions()
            if self.state['game_phase'] != 'RUNNING':
                return
            
            # 2. Start the next turn (which includes start-of-turn effects and building a new action queue).
            self._start_new_turn()
            # 3. Check if start-of-turn effects ended the game (e.g., Wonder victory).
            if self.state['game_phase'] != 'RUNNING':
                return

        # If, after starting a new turn, the action queue is *still* empty, it means no teams had points.
        # This is the definitive condition for extinction.
        if not self.state.get('actions_queue_this_turn'):
            if self.state['game_phase'] == 'RUNNING':
                # This should only happen if no teams had points when _build_action_queue was called.
                self.state['game_phase'] = 'FINISHED'
                self.state['victory_condition'] = "Extinction"
                self.state['game_log'].append({'message': "All teams have been eliminated. Game over.", 'short_message': '[EXTINCTION]'})
            return
        
        # If action_in_turn is out of bounds for the new queue, it means the turn just started
        # and we should proceed with the first action. This can happen in rare edge cases.
        if self.state['action_in_turn'] >= len(self.state['actions_queue_this_turn']):
             self.state['action_in_turn'] = 0

        action_info = self.state['actions_queue_this_turn'][self.state['action_in_turn']]
        teamId = action_info['teamId']
        is_bonus_action = action_info['is_bonus']
        is_from_free_action = action_info.get('from_free', False)
        
        # Update all special structures for the current team right before it acts.
        # This ensures the team acts based on its most current state after other teams' actions.
        self._update_structures_for_team(teamId)

        team_name = self.state['teams'][teamId]['name']
        
        # --- Perform a successful action for this team, trying until one succeeds ---
        result = None
        failed_actions = []
        action_name = None
        
        for _ in range(game_data.GAME_PARAMETERS['MAX_ACTION_ATTEMPTS']):
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

            is_no_cost_action = action_data.ACTIONS.get(action_name, {}).get('no_cost', False)

            # Issue 2: Grant a single bonus action on the first no-cost action per turn.
            if is_no_cost_action:
                if teamId not in self.state.get('no_cost_action_used_by_team_this_turn', set()):
                    self.state.setdefault('no_cost_action_used_by_team_this_turn', set()).add(teamId)
                    
                    # Insert a bonus action for the same team right after the current one
                    bonus_action = {'teamId': teamId, 'is_bonus': True, 'from_free': True}
                    self.state['actions_queue_this_turn'].insert(self.state['action_in_turn'] + 1, bonus_action)
        else:
            self.state['last_action_details'] = {}
        
        # --- Log the final result using the new helper method ---
        log_message = ""
        short_log_message = "[ACTION]"

        gained_bonus_this_action = False
        is_no_cost_action = result.get('success') and action_data.ACTIONS.get(action_name, {}).get('no_cost', False)

        if is_no_cost_action:
            # Check if this action resulted in a bonus action being queued
            next_action_index = self.state['action_in_turn'] + 1
            if next_action_index < len(self.state['actions_queue_this_turn']):
                next_action = self.state['actions_queue_this_turn'][next_action_index]
                if next_action.get('from_free') and next_action.get('teamId') == teamId:
                    gained_bonus_this_action = True
        
        if is_bonus_action and not is_from_free_action:
            log_message += "[BONUS] "

        log_message += f"{team_name} "

        if result.get('success'):
            long_msg_part, short_log_message = self._get_action_log_messages(result)
            log_message += long_msg_part

            if is_no_cost_action:
                if gained_bonus_this_action:
                    log_message += " This action is free and grants a bonus action."
                    short_log_message += " [FREE+BONUS]"
                else:
                    log_message += " This action is free."
                    short_log_message += " [FREE]"
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





# --- Global Game Instance ---
# This is a singleton pattern. The Flask app will interact with this instance.
game = Game()