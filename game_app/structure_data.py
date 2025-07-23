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
    },
    'bastions': {
        'state_key': 'bastions', 'storage_type': 'dict',
        'point_id_keys': ['core_id', ('list', 'prong_ids')],
        'is_critical': True,
        'cleanup_logic': 'custom', # Requires special handling in _cleanup_structures_for_point
    },
    'monoliths': {
        'state_key': 'monoliths', 'storage_type': 'dict',
        'point_id_keys': [('list', 'point_ids')],
        'is_critical': True,
    },
    'purifiers': {
        'state_key': 'purifiers', 'storage_type': 'team_dict_list',
        'point_id_keys': [('list', 'point_ids')],
        'is_critical': True,
    },
    'nexuses': {
        'state_key': 'nexuses', 'storage_type': 'team_dict_list',
        'point_id_keys': [('list', 'point_ids')],
        'is_critical': True,
    },
    'attuned_nexuses': {
        'state_key': 'attuned_nexuses', 'storage_type': 'dict',
        'point_id_keys': [('list', 'point_ids')],
        'is_critical': True,
    },
    'prisms': {
        'state_key': 'prisms', 'storage_type': 'team_dict_list',
        'point_id_keys': [('list', 'all_point_ids')],
        'is_critical': True,
    },
    'trebuchets': {
        'state_key': 'trebuchets', 'storage_type': 'team_dict_list',
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
    },
    'heartwoods': {
        'state_key': 'heartwoods', 'storage_type': 'dict', # keyed by teamId
        'is_critical': True, # It's a major team structure even without points
    },
    'wonders': {
        'state_key': 'wonders', 'storage_type': 'dict',
        'is_critical': True,
    },
}

# Order in which start-of-turn effects should be processed.
# This list contains the method names from TurnProcessor.
TURN_PROCESSING_ORDER = [
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