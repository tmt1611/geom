import os
import hashlib

# --- File Hashing for Live Update Detection ---
# Note: If you move files, you need to update this list.
WATCHED_FILES = [
    'game_app/__init__.py',
    'game_app/routes.py',
    'game_app/game_logic.py',
    'static/js/main.js',
    'templates/index.html'
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