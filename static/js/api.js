/**
 * API wrapper to switch between HTTP backend and Pyodide (WASM) backend.
 */
const api = {
    _mode: 'http', // 'http' or 'pyodide'
    _pyodide: null,
    _game: null,

    /**
     * Initializes the API, loading Pyodide if specified.
     * @param {string} mode - 'http' or 'pyodide'
     */
    async initialize(mode = 'http') {
        if (mode === 'pyodide') {
            this._mode = 'pyodide';
            console.log('Initializing Pyodide backend...');
            this._pyodide = await loadPyodide();
            
            // game_logic.py only uses standard libraries, so we don't need to load any packages.
            
            // To ensure the Pyodide environment is as close to the server environment as possible,
            // we will reconstruct the package structure in the virtual filesystem by fetching all python files.
            console.log('Fetching Python source files for Pyodide...');
            // We fetch all .py files except __init__.py, which has server-specific dependencies (Flask).
            const pyFiles = ['game_logic.py', 'routes.py', 'utils.py'];
            this._pyodide.FS.mkdir('/game_app');

            for (const file of pyFiles) {
                const response = await fetch(`game_app/${file}`);
                if (!response.ok) throw new Error(`Failed to fetch ${file}: ${response.statusText}`);
                const code = await response.text();
                this._pyodide.FS.writeFile(`/game_app/${file}`, code, { encoding: 'utf8' });
            }
            
            // Create a pyodide-specific __init__.py to make `game_app` a package.
            // Its only job is to import game_logic, which creates the singleton `game` instance.
            console.log('Creating Pyodide package initializer...');
            this._pyodide.FS.writeFile('/game_app/__init__.py', 'from . import game_logic', { encoding: 'utf8' });

            console.log('Importing Python game logic and getting instance...');
            // Add root to path, import the module, and expose the 'game' instance globally for JS.
            // This is more direct than importing the package and traversing attributes via JS proxies,
            // which was causing a ModuleNotFoundError.
            this._pyodide.runPython(`
import sys
sys.path.append('/')
from game_app import game_logic
# Make the game instance available on Python's global scope under a specific name
js_game_instance = game_logic.game
            `);

            // Get a proxy to the game instance from the Python global scope.
            this._game = this._pyodide.globals.get('js_game_instance');
            console.log('Pyodide backend ready.');
        } else {
            this._mode = 'http';
            console.log('Using HTTP backend.');
        }
    },

    /**
     * Converts a Pyodide proxy to a JS object, handling nested structures.
     * @param {PyProxy} pyProxy - The Pyodide proxy object.
     * @returns {object} A deep copy as a JavaScript object.
     */
    _pyProxyToJs(pyProxy) {
        if (!pyProxy) return null;
        // The dict_converter is essential for nested objects
        return pyProxy.toJs({ dict_converter: Object.fromEntries });
    },

    // --- MOCKED API calls for dev-only features ---
    async checkUpdates() {
        if (this._mode === 'pyodide') {
            return { updated: false };
        }
        const response = await fetch('/api/check_updates');
        return response.json();
    },

    async restartServer() {
        if (this._mode === 'pyodide') {
            alert("Server restart is not available in GitHub Pages mode.");
            return { message: "Not available." };
        }
        const response = await fetch('/api/dev/restart', { method: 'POST' });
        return response.json();
    },


    // --- GAME API calls ---
    async getState() {
        if (this._mode === 'pyodide') {
            const state = this._game.get_state();
            return this._pyProxyToJs(state);
        }
        const response = await fetch('/api/game/state');
        return response.json();
    },

    async startGame(payload) {
        if (this._mode === 'pyodide') {
            this._game.start_game(
                this._pyodide.toPy(payload.teams),
                this._pyodide.toPy(payload.points),
                payload.maxTurns,
                payload.gridSize
            );
            return this.getState();
        }
        const response = await fetch('/api/game/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return response.json();
    },

    async restart() {
        if (this._mode === 'pyodide') {
            const result = this._game.restart_game();
            return this._pyProxyToJs(result);
        }
        const response = await fetch('/api/game/restart', { method: 'POST' });
        return response.json();
    },

    async reset() {
        if (this._mode === 'pyodide') {
            this._game.reset();
            return this.getState();
        }
        const response = await fetch('/api/game/reset', { method: 'POST' });
        return response.json();
    },

    async nextAction() {
        if (this._mode === 'pyodide') {
            this._game.run_next_action();
            return this.getState();
        }
        const response = await fetch('/api/game/next_action', { method: 'POST' });
        return response.json();
    },

    async getActionProbabilities(teamId, includeInvalid) {
        if (this._mode === 'pyodide') {
            const probabilities = this._game.get_action_probabilities(teamId, includeInvalid);
            return this._pyProxyToJs(probabilities);
        }
        const response = await fetch(`/api/game/action_probabilities?teamId=${teamId}&include_invalid=${includeInvalid}`);
        return response.json();
    },

    async getAllActions() {
        if (this._mode === 'pyodide') {
            // This is more complex in Pyodide as we need to replicate the server logic.
            const game = this._game;
            const action_groups = this._pyProxyToJs(game.ACTION_GROUPS);
            const action_descs = this._pyProxyToJs(game.ACTION_DESCRIPTIONS);
            const action_verbose_descs = this._pyProxyToJs(game.ACTION_VERBOSE_DESCRIPTIONS);
            
            let actions_data = [];
            for (const group in action_groups) {
                const actions = action_groups[group];
                actions.sort(); // Sort for consistency
                for (const action_name of actions) {
                    actions_data.push({
                        'name': action_name,
                        'display_name': action_descs[action_name] || action_name,
                        'group': group,
                        'description': action_verbose_descs[action_name] || 'No description available.'
                    });
                }
            }
            // Sort by group, then by name
            actions_data.sort((a, b) => {
                if (a.group < b.group) return -1;
                if (a.group > b.group) return 1;
                if (a.display_name < b.display_name) return -1;
                if (a.display_name > b.display_name) return 1;
                return 0;
            });
            return actions_data;
        }
        const response = await fetch('/api/actions/all');
        return response.json();
    }
};