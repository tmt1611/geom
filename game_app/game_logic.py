import random
import math
import uuid  # For unique point IDs
from itertools import combinations
from .geometry import (
    distance_sq, on_segment, orientation, segments_intersect,
    get_segment_intersection_point
)
from .formations import FormationManager
from . import game_data
from .actions.expand_actions import ExpandActionsHandler
from .actions.fortify_actions import FortifyActionsHandler
from .actions.fight_actions import FightActionsHandler
from .actions.sacrifice_actions import SacrificeActionsHandler
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
        self.turn_processor = TurnProcessor(self)
        self._init_action_preconditions()

    def _init_action_preconditions(self):
        """Maps action names to their precondition check methods for cleaner validation."""
        self.action_preconditions = {
            # Expand Actions
            'expand_add': self.expand_handler.can_perform_add_line,
            'expand_extend': self.expand_handler.can_perform_extend_line,
            'expand_grow': self.expand_handler.can_perform_grow_line,
            'expand_fracture': self.expand_handler.can_perform_fracture_line,
            'expand_spawn': self.expand_handler.can_perform_spawn_point,
            'expand_orbital': self.expand_handler.can_perform_create_orbital,
            # Fight Actions
            'fight_attack': self.fight_handler.can_perform_attack_line,
            'fight_convert': self.fight_handler.can_perform_convert_point,
            'fight_pincer_attack': self.fight_handler.can_perform_pincer_attack,
            'fight_territory_strike': self.fight_handler.can_perform_territory_strike,
            'fight_bastion_pulse': self.fight_handler.can_perform_bastion_pulse,
            'fight_sentry_zap': self.fight_handler.can_perform_sentry_zap,
            'fight_chain_lightning': self.fight_handler.can_perform_chain_lightning,
            'fight_refraction_beam': self.fight_handler.can_perform_refraction_beam,
            'fight_launch_payload': self.fight_handler.can_perform_launch_payload,
            'fight_purify_territory': self.fight_handler.can_perform_purify_territory,
            # Fortify Actions
            'defend_shield': self.fortify_handler.can_perform_protect_line,
            'fortify_claim': self.fortify_handler.can_perform_claim_territory,
            'fortify_anchor': self.fortify_handler.can_perform_create_anchor,
            'fortify_mirror': self.fortify_handler.can_perform_mirror_structure,
            'fortify_form_bastion': self.fortify_handler.can_perform_form_bastion,
            'fortify_form_monolith': self.fortify_handler.can_perform_form_monolith,
            'fortify_form_purifier': self.fortify_handler.can_perform_form_purifier,
            'fortify_cultivate_heartwood': self.fortify_handler.can_perform_cultivate_heartwood,
            'fortify_form_rift_spire': self.fortify_handler.can_perform_form_rift_spire,
            'terraform_create_fissure': self.fortify_handler.can_perform_create_fissure,
            'terraform_raise_barricade': self.fortify_handler.can_perform_raise_barricade,
            'fortify_build_wonder': self.fortify_handler.can_perform_build_chronos_spire,
            # Sacrifice Actions
            'sacrifice_nova': self.sacrifice_handler.can_perform_nova_burst,
            'sacrifice_whirlpool': self.sacrifice_handler.can_perform_create_whirlpool,
            'sacrifice_phase_shift': self.sacrifice_handler.can_perform_phase_shift,
            'sacrifice_rift_trap': self.sacrifice_handler.can_perform_rift_trap,
            # Rune Actions
            'rune_shoot_bisector': self._can_perform_rune_shoot_bisector,
            'rune_area_shield': self._can_perform_rune_area_shield,
            'rune_shield_pulse': self._can_perform_rune_shield_pulse,
            'rune_impale': self._can_perform_rune_impale,
            'rune_hourglass_stasis': self._can_perform_rune_hourglass_stasis,
            'rune_starlight_cascade': self._can_perform_rune_starlight_cascade,
            'rune_focus_beam': self._can_perform_rune_focus_beam,
            'rune_t_hammer_slam': self._can_perform_rune_t_hammer_slam,
            'rune_cardinal_pulse': self._can_perform_rune_cardinal_pulse,
            'rune_parallel_discharge': self._can_perform_rune_parallel_discharge,
        }

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
        return {pid for t in self.state.get('territories', []) for pid in t['point_ids']}

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

    # --- Precondition Checks for Rune Actions (interim state before full refactor) ---

    def _can_perform_rune_shoot_bisector(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('v_shape', []))
        return can_perform, "Requires an active V-Rune."
    
    def _can_perform_rune_area_shield(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('shield', []))
        return can_perform, "Requires an active Shield Rune."

    def _can_perform_rune_shield_pulse(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('shield', []))
        return can_perform, "Requires an active Shield Rune."

    def _can_perform_rune_impale(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('trident', []))
        return can_perform, "Requires an active Trident Rune."

    def _can_perform_rune_hourglass_stasis(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('hourglass', []))
        return can_perform, "Requires an active Hourglass Rune."

    def _can_perform_rune_starlight_cascade(self, teamId):
        can_perform = len(self._find_possible_starlight_cascades(teamId)) > 0
        return can_perform, "No Star Rune has a valid target in range."

    def _can_perform_rune_focus_beam(self, teamId):
        has_star_rune = bool(self.state.get('runes', {}).get(teamId, {}).get('star', []))
        num_enemy_points = len(self.state['points']) - len(self.get_team_point_ids(teamId))
        can_perform = has_star_rune and num_enemy_points > 0
        return can_perform, "Requires a Star Rune and an enemy point."

    def _can_perform_rune_t_hammer_slam(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('t_shape', []))
        return can_perform, "Requires an active T-Rune."

    def _can_perform_rune_cardinal_pulse(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('plus_shape', []))
        return can_perform, "Requires an active Plus-Rune."

    def _can_perform_rune_parallel_discharge(self, teamId):
        can_perform = bool(self.state.get('runes', {}).get(teamId, {}).get('parallel', []))
        return can_perform, "Requires an active Parallelogram Rune."

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
        return self.fight_handler.attack_line(teamId)

    def sacrifice_action_nova_burst(self, teamId):
        return self.sacrifice_handler.nova_burst(teamId)

    def sacrifice_action_create_whirlpool(self, teamId):
        return self.sacrifice_handler.create_whirlpool(teamId)

    def sacrifice_action_phase_shift(self, teamId):
        return self.sacrifice_handler.phase_shift(teamId)

    def sacrifice_action_rift_trap(self, teamId):
        return self.sacrifice_handler.rift_trap(teamId)

    def expand_action_spawn_point(self, teamId):
        return self.expand_handler.spawn_point(teamId)

    def expand_action_create_orbital(self, teamId):
        return self.expand_handler.create_orbital(teamId)

    def shield_action_protect_line(self, teamId):
        return self.fortify_handler.protect_line(teamId)

    def expand_action_grow_line(self, teamId):
        return self.expand_handler.grow_line(teamId)

    def fortify_action_claim_territory(self, teamId):
        return self.fortify_handler.claim_territory(teamId)

    def fortify_action_form_bastion(self, teamId):
        return self.fortify_handler.form_bastion(teamId)

    def fortify_action_form_monolith(self, teamId):
        return self.fortify_handler.form_monolith(teamId)

    def fortify_action_cultivate_heartwood(self, teamId):
        return self.fortify_handler.cultivate_heartwood(teamId)

    def fortify_action_form_rift_spire(self, teamId):
        return self.fortify_handler.form_rift_spire(teamId)

    def terraform_action_create_fissure(self, teamId):
        return self.fortify_handler.create_fissure(teamId)

    def terraform_action_raise_barricade(self, teamId):
        return self.fortify_handler.raise_barricade(teamId)

    def fortify_action_build_chronos_spire(self, teamId):
        return self.fortify_handler.build_chronos_spire(teamId)

    def fortify_action_mirror_structure(self, teamId):
        return self.fortify_handler.mirror_structure(teamId)

    def fortify_action_create_anchor(self, teamId):
        return self.fortify_handler.create_anchor(teamId)

    def fortify_action_form_purifier(self, teamId):
        return self.fortify_handler.form_purifier(teamId)

    def fight_action_convert_point(self, teamId):
        return self.fight_handler.convert_point(teamId)

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
        return self.fight_handler.bastion_pulse(teamId)

    def fight_action_launch_payload(self, teamId):
        return self.fight_handler.launch_payload(teamId)

    def fight_action_sentry_zap(self, teamId):
        return self.fight_handler.sentry_zap(teamId)

    def fight_action_chain_lightning(self, teamId):
        return self.fight_handler.chain_lightning(teamId)

    def fight_action_pincer_attack(self, teamId):
        return self.fight_handler.pincer_attack(teamId)

    def fight_action_territory_strike(self, teamId):
        return self.fight_handler.territory_strike(teamId)

    def fight_action_refraction_beam(self, teamId):
        return self.fight_handler.refraction_beam(teamId)

    def fight_action_purify_territory(self, teamId):
        return self.fight_handler.purify_territory(teamId)

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
            all_triangles = self.formation_manager._find_all_triangles(team_point_ids, team_lines)
            triangles = len(all_triangles)
            
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