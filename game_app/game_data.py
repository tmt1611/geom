# game_app/game_data.py
from .action_data import ACTIONS

DEFAULT_TEAMS = {
    'team_alpha_default': {'id': 'team_alpha_default', 'name': 'Team Alpha', 'color': '#ff4b4b', 'trait': 'Aggressive'},
    'team_beta_default': {'id': 'team_beta_default', 'name': 'Team Beta', 'color': '#4b4bff', 'trait': 'Defensive'}
}

# --- Structures built dynamically from ACTIONS for backward compatibility ---

ACTION_GROUPS = {}
ACTION_NAME_TO_GROUP = {}
ACTION_MAP = {}
ACTION_DESCRIPTIONS = {}
ACTION_VERBOSE_DESCRIPTIONS = {}
ACTION_LOG_GENERATORS = {}

for action_name, data in ACTIONS.items():
    group = data['group']
    if group not in ACTION_GROUPS:
        ACTION_GROUPS[group] = []
    ACTION_GROUPS[group].append(action_name)
    
    ACTION_NAME_TO_GROUP[action_name] = group
    ACTION_MAP[action_name] = (data['handler'], data['method'])
    ACTION_DESCRIPTIONS[action_name] = data['display_name']
    ACTION_VERBOSE_DESCRIPTIONS[action_name] = data['description']
    
    if 'log_generators' in data:
        ACTION_LOG_GENERATORS.update(data['log_generators'])

# --- Static Game Data ---

GROUP_BASE_WEIGHTS = {
    'Expand': 30,
    'Fight': 30,
    'Fortify': 20,
    'Sacrifice': 10,
    'Rune': 10
}

TRAIT_GROUP_MULTIPLIERS = {
    'Aggressive': {'Fight': 2.0, 'Sacrifice': 1.5, 'Fortify': 0.5, 'Expand': 0.8},
    'Expansive':  {'Expand': 2.0, 'Fight': 0.6, 'Fortify': 0.7},
    'Defensive':  {'Fortify': 2.5, 'Fight': 0.5, 'Sacrifice': 0.5},
    'Balanced':   {} # Uses base weights
}

def get_all_actions_data():
    """Returns a structured list of all possible actions with their descriptions for the action guide."""
    actions_data = []
    for action_name, action_info in ACTIONS.items():
        actions_data.append({
            'name': action_name,
            'display_name': action_info['display_name'],
            'group': action_info['group'],
            'description': action_info['description']
        })
    # Sort by group, then by display name, for consistent UI presentation.
    return sorted(actions_data, key=lambda x: (x['group'], x['display_name']))