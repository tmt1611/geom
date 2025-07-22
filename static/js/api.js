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
            
            // Fetch and run the python game logic file.
            // The path is relative to the root of the web server.
            console.log('Fetching Python game logic...');
            const gameLogicCode = await (await fetch('game_app/game_logic.py')).text();
            
            console.log('Executing Python game logic...');
            this._pyodide.runPython(gameLogicCode);

            // Get a reference to the global 'game' instance in python
            this._game = this._pyodide.globals.get('game');
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