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
                    'action_data.py', 'game_data.py', 'game_logic.py', 'geometry.py',
                    'formations.py', 'structure_data.py', 'turn_processor.py'
                ],
                'game_app/actions': [
                    'expand_actions.py', 'fight_actions.py', 'fortify_actions.py', 'rune_actions.py', 'sacrifice_actions.py', 'terraform_actions.py'
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
            // This is the synchronous version for dev tools, etc.
            const result_py = this._game.run_full_simulation(
                this._pyodide.toPy(payload.teams),
                this._pyodide.toPy(payload.points),
                payload.maxTurns,
                payload.gridSize
            );
            const result_js = this._pyProxyToJs(result_py);
            return { raw_history: result_js.raw_history };
        }
        // HTTP mode gets pre-augmented history. This is always "async" from the client's perspective.
        return this._fetchJson('/api/game/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    },

    async startGameAsync(payload, progressCallback) {
        if (this._mode !== 'pyodide') {
            // Fallback for http mode - it doesn't support progress streaming this way.
            return this.startGame(payload);
        }

        // This is a new method for pyodide that runs the simulation asynchronously.
        this._game.start_game(
            this._pyodide.toPy(payload.teams),
            this._pyodide.toPy(payload.points),
            payload.maxTurns,
            payload.gridSize
        );

        const raw_history = [this._pyProxyToJs(this._game.state.copy())];

        return new Promise((resolve) => {
            const step = () => {
                const game_phase = this._game.state.get('game_phase');
                
                if (game_phase === 'RUNNING') {
                    this._game.run_next_action();
                    raw_history.push(this._pyProxyToJs(this._game.state.copy()));
                    
                    if (progressCallback) {
                        const turn = this._game.state.get('turn');
                        const max_turns = this._game.state.get('max_turns');
                        const action_in_turn = this._game.state.get('action_in_turn');
                        const queue_py = this._game.state.get('actions_queue_this_turn');
                        const actions_this_turn = queue_py ? queue_py.length : 0;
                        queue_py?.destroy();

                        // Progress based on completed turns + fraction of current turn
                        const completed_turns = Math.max(0, turn - 1);
                        const turn_progress = completed_turns / max_turns;
                        const action_progress_in_turn = actions_this_turn > 0 ? (action_in_turn / actions_this_turn) : 0;
                        const total_progress = Math.round((turn_progress + action_progress_in_turn / max_turns) * 100);
                        
                        const currentStep = raw_history.length - 1;
                        progressCallback(total_progress, currentStep);
                    }

                    setTimeout(step, 0); // Yield to event loop to update UI
                } else {
                    if (progressCallback) {
                         const currentStep = raw_history.length - 1;
                         progressCallback(100, currentStep);
                    }
                    resolve({ raw_history });
                }
            };
            setTimeout(step, 0);
        });
    },

    async startGameAsync(payload, progressCallback) {
        if (this._mode !== 'pyodide') {
            // Fallback for http mode - it doesn't support progress streaming this way.
            return this.startGame(payload);
        }

        // This is a new method for pyodide that runs the simulation asynchronously.
        this._game.start_game(
            this._pyodide.toPy(payload.teams),
            this._pyodide.toPy(payload.points),
            payload.maxTurns,
            payload.gridSize
        );

        const raw_history = [this._pyProxyToJs(this._game.state.copy())];

        return new Promise((resolve) => {
            const step = () => {
                const game_phase = this._game.state.get('game_phase');
                
                if (game_phase === 'RUNNING') {
                    this._game.run_next_action();
                    raw_history.push(this._pyProxyToJs(this._game.state.copy()));
                    
                    if (progressCallback) {
                        const turn = this._game.state.get('turn');
                        const max_turns = this._game.state.get('max_turns');
                        const action_in_turn = this._game.state.get('action_in_turn');
                        const queue_py = this._game.state.get('actions_queue_this_turn');
                        const actions_this_turn = queue_py ? queue_py.length : 0;
                        queue_py?.destroy();

                        // Progress based on completed turns + fraction of current turn
                        const completed_turns = Math.max(0, turn - 1);
                        const turn_progress = completed_turns / max_turns;
                        const action_progress_in_turn = actions_this_turn > 0 ? (action_in_turn / actions_this_turn) : 0;
                        const total_progress = Math.round((turn_progress + action_progress_in_turn / max_turns) * 100);
                        
                        progressCallback(total_progress, turn, max_turns);
                    }

                    setTimeout(step, 0); // Yield to event loop to update UI
                } else {
                    if (progressCallback) {
                         const max_turns = this._game.state.get('max_turns');
                         progressCallback(100, max_turns, max_turns);
                    }
                    resolve({ raw_history });
                }
            };
            setTimeout(step, 0);
        });
    },

    async restart() {
        if (this._mode === 'pyodide') {
            const result_py = this._game.restart_game_and_run_simulation();
            const result_js = this._pyProxyToJs(result_py);
            if (result_js.error) return result_js;
            return { raw_history: result_js.raw_history };
        }
        return this._fetchJson('/api/game/restart', { method: 'POST' });
    },

    async augmentState(state) {
        if (this._mode === 'pyodide') {
            const augmented_state_py = this._game.augment_state_for_frontend(this._pyodide.toPy(state));
            return this._pyProxyToJs(augmented_state_py);
        }
        // This is not needed for HTTP mode, as augmentation is done on the server.
        // We can just return the state as is.
        return state;
    },

    async reset() {
        if (this._mode === 'pyodide') {
            this._game.reset();
            return this.getState();
        }
        return this._fetchJson('/api/game/reset', { method: 'POST' });
    },



    async getAllActions() {
        if (this._mode === 'pyodide') {
            // Call the centralized Python function to get the data structure.
            const all_actions_py = this._game_data.get_all_actions_data();
            return this._pyProxyToJs(all_actions_py);
        }
        return this._fetchJson('/api/actions/all');
    },

    async saveIllustration(actionName, imageDataUrl) {
        if (this._mode === 'pyodide') {
            console.warn("Saving illustrations is not supported in Pyodide mode.");
            return { success: false, error: "Not supported in Pyodide mode" };
        }
        return this._fetchJson('/api/dev/save_illustration', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action_name: actionName, image_data: imageDataUrl })
        });
    }
};