import os
import hashlib

# --- File Hashing for Live Update Detection ---
# Note: If you move files, you need to update this list.
WATCHED_FILES = [
    # Python source
    'game_app/__init__.py',
    'game_app/routes.py',
    'game_app/game_logic.py',
    'game_app/geometry.py',
    'game_app/formations.py',
    'game_app/game_data.py',
    'game_app/structure_data.py',
    'game_app/action_data.py',
    'game_app/turn_processor.py',
    'game_app/game_state_query.py',
    'game_app/actions/expand_actions.py',
    'game_app/actions/fight_actions.py',
    'game_app/actions/fortify_actions.py',
    'game_app/actions/rune_actions.py',
    'game_app/actions/sacrifice_actions.py',
    'game_app/actions/terraform_actions.py',
    # Frontend
    'static/js/main.js',
    'static/js/api.js',
    'static/js/renderer.js',
    'static/js/visuals.js',
    'static/js/illustration_generator.js',
    'static/css/style.css',
    'index.html',
    # Docs
    'rules.md'
]
STARTUP_HASH = ''

def get_files_hash():
    """Calculates a hash of the watched files."""
    hasher = hashlib.md5()
    for filepath in WATCHED_FILES:
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                buf = f.read()
                hasher.update(buf)
    return hasher.hexdigest()

def calculate_startup_hash():
    """Calculates and stores the hash of watched files at startup."""
    global STARTUP_HASH
    STARTUP_HASH = get_files_hash()