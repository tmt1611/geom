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
            console.log('Fetching Python source files...');
            const pyFiles = ['__init__.py', 'game_logic.py', 'routes.py', 'utils.py'];
            this._pyodide.FS.mkdir('/game_app');

            for (const file of pyFiles) {
                const response = await fetch(`game_app/${file}`);
                const code = await response.text();
                this._pyodide.FS.writeFile(`/game_app/${file}`, code, { encoding: 'utf8' });
            }

            // In Pyodide mode, we don't run the full Flask app from __init__.py.
            // We just need to import game_logic to instantiate the 'game' object.
            // The __init__.py we loaded has Flask imports which we can't satisfy without loading more packages.
            // So we will overwrite it with a simple one that just imports game_logic.
            // This ensures the singleton 'game' instance is created, mimicking the server behavior.
            console.log('Creating Pyodide-specific package initializer...');
            this._pyodide.FS.writeFile('/game_app/__init__.py', 'from . import game_logic', { encoding: 'utf8' });

            console.log('Importing Python game logic as a module...');
            // Add root to path and import the package. This will execute our custom __init__.py,
            // which in turn imports game_logic.py and creates the `game` instance.
            this._pyodide.runPython(`
import sys
sys.path.append('/')
import game_app
            `);

            // Get a reference to the 'game' instance from the game_logic module within the package
            this._game = this._pyodide.pyimport('game_app.game_logic.game');
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
    }
};