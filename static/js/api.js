/**
 * API wrapper to switch between HTTP backend and Pyodide (WASM) backend.
 */
const api = {
    _mode: 'http', // 'http' or 'pyodide'
    _pyodide: null,
    _game: null,
    _game_data: null,

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
            // We fetch all .py files needed for the game logic to run in the browser.
            const pyodideFileStructure = {
                'game_app': [
                    'game_logic.py', 'geometry.py', 'formations.py', 'game_data.py',
                    'turn_processor.py', 'structure_data.py'
                ],
                'game_app/actions': [
                    'expand_actions.py', 'fight_actions.py', 'fortify_actions.py', 'rune_actions.py', 'sacrifice_actions.py'
                ]
            };

            for (const dir in pyodideFileStructure) {
                const pyodidePath = `/${dir}`;
                this._pyodide.FS.mkdir(pyodidePath);
                 // Create an __init__.py file in each directory to make it a package
                this._pyodide.FS.writeFile(`${pyodidePath}/__init__.py`, '', { encoding: 'utf8' });

                for (const file of pyodideFileStructure[dir]) {
                    const response = await fetch(`${dir}/${file}`);
                    if (!response.ok) throw new Error(`Failed to fetch ${dir}/${file}: ${response.statusText}`);
                    const code = await response.text();
                    this._pyodide.FS.writeFile(`${pyodidePath}/${file}`, code, { encoding: 'utf8' });
                }
            }

            // A custom __init__.py for the root game_app package to ensure game instance is created.
            this._pyodide.FS.writeFile('/game_app/__init__.py', 'from . import game_logic', { encoding: 'utf8' });
            console.log('Pyodide filesystem populated.');

            console.log('Importing Python game logic and getting instance...');
            // Add root to path, import the module, and expose the 'game' instance globally for JS.
            // This is more direct than importing the package and traversing attributes via JS proxies,
            // which was causing a ModuleNotFoundError.
            this._pyodide.runPython(`
import sys
sys.path.append('/')
from game_app import game_logic, game_data
# Make the game instance available on Python's global scope under a specific name
js_game_instance = game_logic.game
js_game_data = game_data
            `);

            // Get a proxy to the game instance from the Python global scope.
            this._game = this._pyodide.globals.get('js_game_instance');
            this._game_data = this._pyodide.globals.get('js_game_data');
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

    async _fetchJson(url, options) {
        const response = await fetch(url, options);
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API Error Response:', errorText);
            // Throwing an object allows us to pass more structured error information.
            // The HTML traceback is often in errorText.
            const error = new Error(`Server returned an error: ${response.status} ${response.statusText}`);
            error.response_text = errorText;
            throw error;
        }
        // Handle cases where the server returns 200 OK but with an empty body
        const text = await response.text();
        if (!text) {
            return null; // Or {}, depending on what's more convenient for the caller
        }
        try {
            return JSON.parse(text);
        } catch (e) {
            console.error('Failed to parse JSON from server response:', text);
            throw new Error('Server returned invalid JSON.');
        }
    },

    // --- MOCKED API calls for dev-only features ---
    async checkUpdates() {
        if (this._mode === 'pyodide') {
            return { updated: false };
        }
        return this._fetchJson('/api/check_updates');
    },

    async restartServer() {
        if (this._mode === 'pyodide') {
            alert("Server restart is not available in GitHub Pages mode.");
            return { message: "Not available." };
        }
        return this._fetchJson('/api/dev/restart', { method: 'POST' });
    },


    // --- GAME API calls ---
    async getState() {
        if (this._mode === 'pyodide') {
            const state = this._game.get_state();
            return this._pyProxyToJs(state);
        }
        return this._fetchJson('/api/game/state');
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
        return this._fetchJson('/api/game/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    },

    async restart() {
        if (this._mode === 'pyodide') {
            const result = this._game.restart_game();
            return this._pyProxyToJs(result);
        }
        return this._fetchJson('/api/game/restart', { method: 'POST' });
    },

    async reset() {
        if (this._mode === 'pyodide') {
            this._game.reset();
            return this.getState();
        }
        return this._fetchJson('/api/game/reset', { method: 'POST' });
    },

    async nextAction() {
        if (this._mode === 'pyodide') {
            this._game.run_next_action();
            return this.getState();
        }
        return this._fetchJson('/api/game/next_action', { method: 'POST' });
    },

    async getActionProbabilities(teamId, includeInvalid) {
        if (this._mode === 'pyodide') {
            const probabilities = this._game.get_action_probabilities(teamId, includeInvalid);
            return this._pyProxyToJs(probabilities);
        }
        return this._fetchJson(`/api/game/action_probabilities?teamId=${teamId}&include_invalid=${includeInvalid}`);
    },

    async getAllActions() {
        if (this._mode === 'pyodide') {
            // This is more complex in Pyodide as we need to replicate the server logic.
            const game_data = this._game_data;
            const action_groups = this._pyProxyToJs(game_data.ACTION_GROUPS);
            const action_descs = this._pyProxyToJs(game_data.ACTION_DESCRIPTIONS);
            const action_verbose_descs = this._pyProxyToJs(game_data.ACTION_VERBOSE_DESCRIPTIONS);
            
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
        return this._fetchJson('/api/actions/all');
    }
};