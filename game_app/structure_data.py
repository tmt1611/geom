# game_app/structure_data.py

# A central registry for all game structures and turn-based effects.
# This helps to generify logic for things like point deletion, state updates, etc.

# 'storage_type' defines how the structure is stored in the game state:
# - 'list': state[key] is a list of structure dicts.
# - 'dict': state[key] is a dict where keys are structure IDs and values are structure dicts.
# - 'team_dict_list': state[key] is a dict {teamId: [list of struct dicts]}.
# - 'dict_keyed_by_pid': state[key] is a dict where keys are point_ids.

# 'point_id_keys' is a list of keys within a structure's dict that hold point IDs.
# - A string value (e.g., 'core_id') means it's a single point ID.
# - A tuple ('list', 'key_name') means it's a list of point IDs under that key.

STRUCTURE_DEFINITIONS = {
    # --- Major Structures made of points ---
    'territories': {
        'state_key': 'territories', 'storage_type': 'list',
        'point_id_keys': [('list', 'point_ids')],
        'is_critical': True,
        'frontend_flag_key': 'is_fortified',
    },
    'bastions': {
        'state_key': 'bastions', 'storage_type': 'dict',
        'point_id_keys': ['core_id', ('list', 'prong_ids')],
        'is_critical': True,
        'cleanup_logic': 'custom', # Requires special handling in _cleanup_structures_for_point
        'frontend_flag_keys': {
            'core_id': 'is_bastion_core',
            'prong_ids': 'is_bastion_prong'
        },
    },
    'monoliths': {
        'state_key': 'monoliths', 'storage_type': 'dict',
        'point_id_keys': [('list', 'point_ids')],
        'is_critical': True,
        'frontend_flag_key': 'is_monolith_point',
    },
    'purifiers': {
        'state_key': 'purifiers', 'storage_type': 'team_dict_list',
        'point_id_keys': [('list', 'point_ids')],
        'is_critical': True,
        'frontend_flag_key': 'is_purifier_point',
    },
    'rift_spires': {
        'state_key': 'rift_spires', 'storage_type': 'dict',
        'point_id_keys': ['point_id'],
        'is_critical': True,
        'frontend_flag_key': 'is_rift_spire_point',
    },
    'attuned_nexuses': {
        'state_key': 'attuned_nexuses', 'storage_type': 'dict',
        'point_id_keys': [('list', 'point_ids')],
        'is_critical': True,
    },
    'ley_lines': {
        'state_key': 'ley_lines', 'storage_type': 'dict',
        'point_id_keys': [('list', 'point_ids')],
        'is_critical': True,
    },

    # --- Structures/Effects NOT made of points, or keyed by point_id ---
    'anchors': {
        'state_key': 'anchors', 'storage_type': 'dict_keyed_by_pid',
        'is_critical': True, # The point itself is critical while it's an anchor
        'frontend_flag_key': 'is_anchor',
    },
    'stasis_points': {
        'state_key': 'stasis_points', 'storage_type': 'dict_keyed_by_pid',
        'is_critical': True, # A point in stasis cannot be used, so it's critical
        'frontend_flag_key': 'is_in_stasis',
    },
    'isolated_points': {
        'state_key': 'isolated_points', 'storage_type': 'dict_keyed_by_pid',
        'is_critical': False, # An isolated point is vulnerable, not necessarily critical
        'frontend_flag_key': 'is_isolated',
    },
    'heartwoods': {
        'state_key': 'heartwoods', 'storage_type': 'dict', # keyed by teamId
        'is_critical': True, # It's a major team structure even without points
    },
    'wonders': {
        'state_key': 'wonders', 'storage_type': 'dict',
        'is_critical': True,
    },
    # --- Runes ---
    # Runes are stored under state['runes'][teamId][rune_type]
    'rune_nexus': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 'nexus',
        'point_id_keys': [('list', 'point_ids')],
        'is_critical': True,
        'formation_checker': 'check_nexuses',
        'formation_inputs': ['team_point_ids', 'team_lines', 'all_points'],
        'frontend_flag_key': 'is_nexus_point',
    },
    'rune_prism': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 'prism',
        'point_id_keys': [('list', 'all_point_ids')],
        'is_critical': True,
        'formation_checker': 'check_prisms',
        'formation_inputs': ['team_territories'],
        'frontend_flag_key': 'is_prism_point',
    },
    'rune_trebuchet': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 'trebuchet',
        'point_id_keys': [('list', 'point_ids')],
        'is_critical': True,
        'formation_checker': 'check_trebuchets',
        'formation_inputs': ['team_point_ids', 'team_lines', 'all_points'],
        'frontend_flag_key': 'is_trebuchet_point',
    },
    'rune_cross': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 'cross',
        'is_critical': True,
        'formation_checker': 'check_cross_rune',
        'formation_inputs': ['team_point_ids', 'team_lines', 'all_points'],
        'point_id_keys': [('list_of_lists', None)], # The structure instance itself is a list of pids
    },
    'rune_v_shape': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 'v_shape',
        'is_critical': True,
        'formation_checker': 'check_v_rune',
        'formation_inputs': ['team_point_ids', 'team_lines', 'all_points'],
        'point_id_keys': ['vertex_id', 'leg1_id', 'leg2_id'],
    },
    'rune_shield': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 'shield',
        'is_critical': True,
        'formation_checker': 'check_shield_rune',
        'formation_inputs': ['team_point_ids', 'team_lines', 'all_points'],
        'point_id_keys': [('list', 'triangle_ids'), 'core_id'],
    },
    'rune_trident': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 'trident',
        'is_critical': True,
        'formation_checker': 'check_trident_rune',
        'formation_inputs': ['team_point_ids', 'team_lines', 'all_points'],
        'point_id_keys': ['apex_id', ('list', 'prong_ids'), 'handle_id'],
    },
    'rune_hourglass': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 'hourglass',
        'is_critical': True,
        'formation_checker': 'check_hourglass_rune',
        'formation_inputs': ['team_point_ids', 'team_lines', 'all_points'],
        'point_id_keys': [('list', 'all_points')],
    },
    'rune_star': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 'star',
        'is_critical': True,
        'formation_checker': 'check_star_rune',
        'formation_inputs': ['team_point_ids', 'team_lines', 'all_points'],
        'point_id_keys': [('list', 'all_points')],
    },
    'rune_barricade': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 'barricade',
        'is_critical': True,
        'formation_checker': 'check_barricade_rune',
        'formation_inputs': ['team_point_ids', 'team_lines', 'all_points'],
        'point_id_keys': [('list_of_lists', None)],
    },
    'rune_t_shape': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 't_shape',
        'is_critical': True,
        'formation_checker': 'check_t_rune',
        'formation_inputs': ['team_point_ids', 'team_lines', 'all_points'],
        'point_id_keys': [('list', 'all_points')],
    },
    'rune_plus_shape': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 'plus_shape',
        'is_critical': True,
        'formation_checker': 'check_plus_rune',
        'formation_inputs': ['team_point_ids', 'team_lines', 'all_points'],
        'point_id_keys': [('list', 'all_points')],
    },
    'rune_i_shape': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 'i_shape',
        'is_critical': True,
        'formation_checker': 'check_i_rune',
        'formation_inputs': ['team_point_ids', 'team_lines', 'all_points'],
        'point_id_keys': [('list', 'point_ids'), ('list', 'internal_points'), ('list', 'endpoints')],
        'frontend_flag_keys': {
            'point_ids': ['is_i_rune_point', 'is_conduit_point'],
            'internal_points': 'is_sentry_eye',
            'endpoints': 'is_sentry_post'
        },
    },
    'rune_parallel': {
        'state_key': 'runes', 'storage_type': 'team_dict_of_structures',
        'structure_subtype_key': 'parallel',
        'is_critical': True,
        'formation_checker': 'check_parallel_rune',
        'formation_inputs': ['team_point_ids', 'team_lines', 'all_points'],
        'point_id_keys': [('list_of_lists', None)],
    },
}

# Order in which start-of-turn effects should be processed.
# This list contains the method names from TurnProcessor.
TURN_PROCESSING_ORDER = [
    '_process_regenerating_points',
    '_process_shields_and_stasis',
    '_process_isolated_points',
    '_process_rift_traps',
    '_process_anchors',
    '_process_whirlpools',
    '_process_scorched_zones',
    '_process_heartwoods',
    '_process_monoliths',
    '_process_attuned_nexuses',
    '_process_ley_lines',
    '_process_wonders',
    '_process_spires_fissures_barricades',
]