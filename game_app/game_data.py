# game_app/game_data.py
from .action_data import ACTIONS
from collections import defaultdict

DEFAULT_TEAMS = [
    {'id': 'team_alpha_default', 'name': 'Alpha', 'color': '#ff4b4b', 'trait': 'Aggressive'},
    {'id': 'team_beta_default', 'name': 'Beta', 'color': '#4b4bff', 'trait': 'Defensive'}
]

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

def get_log_generators():
    """Returns a dictionary mapping result types to log generator functions."""
    generators = {}
    for _, data in ACTIONS.items():
        if 'log_generators' in data:
            generators.update(data['log_generators'])
    return generators

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