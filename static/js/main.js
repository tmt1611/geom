document.addEventListener('DOMContentLoaded', () => {
    // This global 'api' object is defined in api.js
    const canvas = document.getElementById('grid');
    const ctx = canvas.getContext('2d');
    let cellSize; // Calculated based on canvas size and grid size

    // --- State Management ---
    // Centralized object for frontend-specific state.
    const uiState = {
        localTeams: {},
        initialPoints: [], // For setup phase
        selectedTeamId: null,
        autoPlayInterval: null,
        debugOptions: {
            showPointIds: false,
            showLineIds: false,
            highlightLastAction: false,
            showHulls: false,
            compactLog: false
        },
        visualEffects: [], // For temporary animations
        lastActionHighlights: { // For highlighting the last action's components
            points: new Set(),
            lines: new Set(),
            structures: new Set(),
            clearTimeout: null
        }
    };
    let currentGameState = {}; // Cache of the latest game state from the backend

    // --- UI Elements ---
    const teamsList = document.getElementById('teams-list');
    const newTeamNameInput = document.getElementById('new-team-name');
    const newTeamColorInput = document.getElementById('new-team-color');
    const newTeamTraitSelect = document.getElementById('new-team-trait');
    const addTeamBtn = document.getElementById('add-team-btn');
    const startGameBtn = document.getElementById('start-game-btn');
    const nextActionBtn = document.getElementById('next-action-btn');
    const autoPlayBtn = document.getElementById('auto-play-btn');
    const autoPlaySpeedSlider = document.getElementById('auto-play-speed');
    const speedValueSpan = document.getElementById('speed-value');
    const resetBtn = document.getElementById('reset-btn');
    const restartSimulationBtn = document.getElementById('restart-simulation-btn');
    const undoPointBtn = document.getElementById('undo-point-btn');
    const clearPointsBtn = document.getElementById('clear-points-btn');
    const randomizePointsBtn = document.getElementById('randomize-points-btn');
    const maxTurnsInput = document.getElementById('max-turns');
    const gridSizeInput = document.getElementById('grid-size');
    const statsDiv = document.getElementById('stats');
    const logDiv = document.getElementById('log');
    const turnCounter = document.getElementById('turn-counter');
    const statusBar = document.getElementById('status-bar');
    const finalInterpDiv = document.getElementById('final-interpretation');
    const finalInterpContent = document.getElementById('final-stats-content');
    const actionPreviewPanel = document.getElementById('action-preview-panel');
    const compactLogToggle = document.getElementById('compact-log-toggle');
    const copyLogBtn = document.getElementById('copy-log-btn');
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');
    const actionGuideContent = document.getElementById('action-guide-content');
    const debugPointIdsToggle = document.getElementById('debug-point-ids');
    const debugLineIdsToggle = document.getElementById('debug-line-ids');
    const debugLastActionToggle = document.getElementById('debug-last-action');
    const showHullsToggle = document.getElementById('show-hulls-toggle');
    const finalAnalysisOptions = document.getElementById('final-analysis-options');
    const copyStateBtn = document.getElementById('copy-state-btn');
    const restartServerBtn = document.getElementById('restart-server-btn');

    // --- Helper Functions ---
    function getRandomHslColor() {
        const hue = Math.floor(Math.random() * 360);
        return `hsl(${hue}, 70%, 50%)`;
    }

    function setNewTeamDefaults() {
        newTeamNameInput.value = '';
        newTeamColorInput.value = getRandomHslColor();
        newTeamTraitSelect.value = 'Random';
    }

    function showTemporaryButtonFeedback(button, message, duration = 1500) {
        const originalText = button.innerHTML;
        button.innerHTML = message;
        button.disabled = true;
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, duration);
    }

    // --- Core Functions ---



    // Main animation loop
    function animationLoop() {
        // The main loop is simple: it asks the renderer to draw the current state.
        // The renderer itself will handle all the complex drawing logic.
        if (currentGameState) {
            renderer.render(currentGameState, uiState);
        }
        // Request the next frame.
        requestAnimationFrame(animationLoop);
    }

    function updateStateAndRender(gameState) {
        if (!gameState || !gameState.teams) return;
        
        const isFirstUpdate = !currentGameState.game_phase;
        currentGameState = gameState;

        // Delegate visual effect creation to the specialized manager
        visualEffectsManager.processTurnEvents(gameState.new_turn_events, gameState, uiState);
        visualEffectsManager.processActionVisuals(gameState, uiState, cellSize);
        
        if (isFirstUpdate) {
            renderTeamsList();
        }

        updateLog(gameState.game_log, gameState.teams);
        updateInterpretationPanel(gameState);
        updateActionPreview(gameState);
        updateControls(gameState);
    }

    // --- UI Update Functions ---

    /** Creates a single team list item, handling view and edit modes. */
    function createTeamListItem(team, teamId, inSetupPhase) {
        const li = document.createElement('li');
        li.dataset.teamId = teamId;
        if (uiState.selectedTeamId === teamId && inSetupPhase) li.classList.add('selected');

        // --- View Mode Elements ---
        const colorBox = document.createElement('div');
        colorBox.className = 'team-color-box';
        colorBox.style.backgroundColor = team.color;

        const teamInfo = document.createElement('div');
        teamInfo.className = 'team-info';
        teamInfo.innerHTML = `<span class="team-name">${team.name}</span><span class="team-trait">(${team.trait})</span>`;
        if (inSetupPhase) {
            li.style.cursor = 'pointer';
            teamInfo.onclick = () => { uiState.selectedTeamId = teamId; renderTeamsList(); };
        }

        // --- Edit Mode Elements ---
        const editControls = document.createElement('div');
        editControls.className = 'team-edit-controls';
        const traits = ['Random', 'Balanced', 'Aggressive', 'Expansive', 'Defensive'];
        editControls.innerHTML = `
            <input type="color" value="${team.color}">
            <input type="text" value="${team.name}" placeholder="Team Name">
            <select>${traits.map(t => `<option value="${t}" ${team.trait === t ? 'selected' : ''}>${t}</option>`).join('')}</select>
            <button class="save-team-btn" title="Save changes">&#10003;</button>
            <button class="cancel-team-btn" title="Cancel edit">&times;</button>
        `;
        editControls.querySelector('.save-team-btn').onclick = () => {
            const newName = editControls.querySelector('input[type="text"]').value.trim();
            if (newName) {
                uiState.localTeams[teamId].name = newName;
                uiState.localTeams[teamId].color = editControls.querySelector('input[type="color"]').value;
                uiState.localTeams[teamId].trait = editControls.querySelector('select').value;
                uiState.localTeams[teamId].isEditing = false;
                renderTeamsList();
            }
        };
        editControls.querySelector('.cancel-team-btn').onclick = () => {
            uiState.localTeams[teamId].isEditing = false;
            renderTeamsList();
        };

        // --- Action Buttons (Edit/Delete) ---
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'team-actions';
        if (inSetupPhase) {
            actionsDiv.innerHTML = `<button class="edit-team-btn" title="Edit team">&#9998;</button><button class="delete-team-btn" title="Delete team">&times;</button>`;
            actionsDiv.querySelector('.edit-team-btn').onclick = () => {
                Object.values(uiState.localTeams).forEach(t => t.isEditing = false);
                uiState.localTeams[teamId].isEditing = true;
                renderTeamsList();
            };
            actionsDiv.querySelector('.delete-team-btn').dataset.teamId = teamId;
        }

        li.append(colorBox, teamInfo, editControls, actionsDiv);

        // Toggle visibility based on edit mode
        const isEditing = inSetupPhase && team.isEditing;
        teamInfo.style.display = isEditing ? 'none' : 'flex';
        colorBox.style.display = isEditing ? 'none' : 'block';
        actionsDiv.style.display = isEditing ? 'none' : 'flex';
        editControls.style.display = isEditing ? 'flex' : 'none';
        
        return li;
    }

    function renderTeamsList() {
        teamsList.innerHTML = '';
        const inSetupPhase = currentGameState.game_phase === 'SETUP';
        const teamsToRender = inSetupPhase ? uiState.localTeams : currentGameState.teams;
    
        for (const teamId in teamsToRender) {
            const team = teamsToRender[teamId];
            teamsList.appendChild(createTeamListItem(team, teamId, inSetupPhase));
        }
    }

    function updateLog(log, teams) {
        logDiv.innerHTML = '';
        if (!log) return;

        let lastMessageEntry = log.slice().reverse().find(entry => entry.teamId && teams[entry.teamId]);

        log.forEach(entry => {
            const logEntryDiv = document.createElement('div');
            logEntryDiv.className = 'log-entry';
            const message = (uiState.debugOptions.compactLog && entry.short_message) ? entry.short_message : entry.message;
            if (entry.teamId && teams[entry.teamId]) {
                const team = teams[entry.teamId];
                logEntryDiv.style.borderLeftColor = team.color;
                if (!uiState.debugOptions.compactLog && message.includes(team.name)) {
                    let finalMessage = message;
                    for (const otherTeamId in teams) {
                        const otherTeam = teams[otherTeamId];
                        finalMessage = finalMessage.replace(new RegExp(`\\b${otherTeam.name}\\b`, 'g'), `<strong style="color: ${otherTeam.color};">${otherTeam.name}</strong>`);
                    }
                    logEntryDiv.innerHTML = finalMessage;
                } else {
                    logEntryDiv.textContent = message;
                }
                if (uiState.debugOptions.compactLog) {
                    logEntryDiv.style.color = team.color;
                    logEntryDiv.style.fontWeight = 'bold';
                }
            } else {
                logEntryDiv.textContent = message;
                logEntryDiv.style.textAlign = 'center';
                logEntryDiv.style.borderLeftColor = '#ccc';
                logEntryDiv.style.background = '#f0f0f0';
                if (uiState.debugOptions.compactLog) {
                    logEntryDiv.style.fontWeight = 'bold';
                }
            }
            logDiv.prepend(logEntryDiv);
        });
        logDiv.scrollTop = 0;

        if (currentGameState.game_phase === 'RUNNING') {
            if (lastMessageEntry) {
                let finalMessage = lastMessageEntry.message;
                for (const teamId in teams) {
                    finalMessage = finalMessage.replace(new RegExp(`\\b${teams[teamId].name}\\b`, 'g'), `<strong style="color: ${teams[teamId].color};">${teams[teamId].name}</strong>`);
                }
                statusBar.innerHTML = finalMessage;
            } else {
                statusBar.textContent = 'Starting game...';
            }
            statusBar.style.opacity = '1';
        } else {
            statusBar.style.opacity = '0';
        }
    }

    function updateLiveStats(teams, live_stats, gameState) {
        const structureUiMap = {
            // UI Name: [state key in gameState, subtype key (if applicable)]
            'Nexus': ['runes', 'nexus'],
            'Prism': ['runes', 'prism'],
            'Trebuchet-Rune': ['runes', 'trebuchet'],
            'Star-Rune': ['runes', 'star'],
            'I-Rune': ['runes', 'i_shape'],
            'V-Rune': ['runes', 'v_shape'],
            'Shield-Rune': ['runes', 'shield'],
            'Trident-Rune': ['runes', 'trident'],
            'Cross-Rune': ['runes', 'cross'],
            'Plus-Rune': ['runes', 'plus_shape'],
            'T-Rune': ['runes', 't_shape'],
            'Hourglass-Rune': ['runes', 'hourglass'],
            'Barricade-Rune': ['runes', 'barricade'],
            'Parallelogram-Rune': ['runes', 'parallel'],
            'Bastion': ['bastions'],
            'Monolith': ['monoliths'],
            'Purifier': ['purifiers'],
            'Rift Spire': ['rift_spires'],
            'Wonder': ['wonders'],
        };

        let statsHTML = '<h4>Live Stats</h4>';
        if (teams && Object.keys(teams).length > 0 && live_stats) {
            for (const teamId in teams) {
                const team = teams[teamId];
                const stats = live_stats[teamId];
                if (!stats) continue;

                let teamHTML = `<div style="margin-bottom: 5px;">
                    <strong style="color:${team.color};">${team.name}</strong>: 
                    ${stats.point_count} pts, ${stats.line_count} lines, ${stats.controlled_area} area`;
                
                const structureStrings = Object.entries(structureUiMap).map(([uiName, keys]) => {
                    const [stateKey, subtypeKey] = keys;
                    let count = 0;
                    const stateObject = gameState[stateKey];
                    if (!stateObject) return '';

                    if (subtypeKey) { // Stored in runes dict e.g. state.runes[teamId][subtypeKey]
                        count = stateObject[teamId]?.[subtypeKey]?.length || 0;
                    } else if (stateKey === 'purifiers') { // Special case: {teamId: [list]}
                        count = stateObject[teamId]?.length || 0;
                    } else { // Stored as list or dict of objects at top level, needs filtering by teamId
                        count = Object.values(stateObject).filter(s => s.teamId === teamId).length;
                    }
                    return count > 0 ? `${uiName}(${count})` : '';
                }).filter(Boolean);

                if (structureStrings.length > 0) {
                    teamHTML += `<br/><span style="font-size: 0.9em; padding-left: 10px;">Formations: ${structureStrings.join(', ')}</span>`;
                }
                teamHTML += `</div>`;
                statsHTML += teamHTML;
            }
        } else {
            statsHTML += '<p>No teams yet.</p>';
        }
        statsDiv.innerHTML = statsHTML;
    }

    function updateInterpretationPanel(gameState) {
        const { turn, max_turns, teams, game_phase, interpretation, victory_condition, live_stats, action_in_turn, actions_queue_this_turn } = gameState;

        let turnText = `Turn: ${turn} / ${max_turns}`;
        if (game_phase === 'RUNNING' && actions_queue_this_turn?.length > 0) {
            const currentActionNum = Math.min(action_in_turn + 1, actions_queue_this_turn.length);
            turnText += ` (Action ${currentActionNum} / ${actions_queue_this_turn.length})`;
        }
        turnCounter.textContent = turnText;

        updateLiveStats(teams, live_stats, gameState);
    
        if (game_phase === 'FINISHED' && interpretation) {
            finalInterpContent.innerHTML = '';
            finalAnalysisOptions.style.display = 'block';
            if(victory_condition) {
                const victoryTitle = document.createElement('h4');
                victoryTitle.className = 'victory-condition';
                victoryTitle.textContent = `Game Over: ${victory_condition}`;
                finalInterpContent.appendChild(victoryTitle);
            }
            const cardsContainer = document.createElement('div');
            cardsContainer.className = 'interp-cards-container';
            for (const teamId in teams) {
                const team = teams[teamId];
                const teamData = interpretation[teamId];
                if (!teamData) continue;
                const card = document.createElement('div');
                card.className = 'interp-card';
                card.style.borderColor = team.color;
                card.innerHTML = `
                    <div class="interp-card-header" style="background-color: ${team.color};">${team.name}</div>
                    <ul class="interp-stats-list">
                        ${Object.entries({
                            'Points': teamData.point_count, 'Lines': teamData.line_count, 'Total Line Length': teamData.line_length,
                            'Triangles': teamData.triangles, 'Territory Area': teamData.controlled_area, 'Influence Area (Hull)': teamData.hull_area,
                            'Hull Perimeter': teamData.hull_perimeter
                        }).map(([statName, statValue]) => statValue > 0 ? `<li><strong>${statName}:</strong> ${statValue}</li>` : '').join('')}
                    </ul>
                    <p class="interp-divination">"${teamData.divination_text}"</p>
                `;
                cardsContainer.appendChild(card);
            }
            finalInterpContent.appendChild(cardsContainer);
            finalInterpDiv.style.display = 'block';
        } else {
            finalInterpDiv.style.display = 'none';
            finalAnalysisOptions.style.display = 'none';
        }
    }

    function updateActionPreview(gameState) {
        const content = document.getElementById('action-preview-content');
        const showInvalid = document.getElementById('show-invalid-actions').checked;
    
        if (gameState.game_phase !== 'RUNNING' || !gameState.actions_queue_this_turn) {
            actionPreviewPanel.style.display = 'none';
            return;
        }
        actionPreviewPanel.style.display = 'block';
        
        const actionIndex = gameState.action_in_turn;
        let teamIdForPreview, titlePrefix;

        if (actionIndex >= gameState.actions_queue_this_turn.length) {
            titlePrefix = "Next Turn Preview";
            const activeTeamIds = Object.keys(gameState.teams).filter(id => gameState.live_stats[id]?.point_count > 0);
            if (activeTeamIds.length > 0) {
                teamIdForPreview = activeTeamIds[0];
            } else {
                content.innerHTML = '<h5>Turn Over</h5><p>No active teams remain.</p>';
                return;
            }
        } else {
            titlePrefix = "Now:";
            teamIdForPreview = gameState.actions_queue_this_turn[actionIndex].teamId;
        }
    
        api.getActionProbabilities(teamIdForPreview, showInvalid).then(data => {
            if (data.error) {
                content.innerHTML = `<p>Error loading actions for ${data.team_name || 'team'}.</p>`;
                return;
            }
            let html = `<h5 style="border-color:${data.color};">${titlePrefix} ${data.team_name}'s Turn</h5>`;
            const groupOrder = ['Fight', 'Expand', 'Fortify', 'Sacrifice', 'Rune'];
            let hasValidActions = false;
            for (const groupName of groupOrder) {
                const group = data.groups[groupName];
                if (group && group.actions.length > 0) {
                    hasValidActions = true;
                    html += `<div class="action-category"><h6>${groupName} (${group.group_probability}%)</h6><ul class="action-prob-list">`;
                    group.actions.forEach(action => {
                        html += `<li><span>${action.display_name}</span><div class="action-prob-bar-container"><div class="action-prob-bar" style="width: ${action.probability}%; background-color:${data.color};"></div></div><span class="action-prob-percent">${action.probability}%</span></li>`;
                    });
                    html += '</ul></div>';
                }
            }
            if (!hasValidActions) html += '<p>No valid actions found. Passing turn.</p>';
            if (showInvalid && data.invalid.length > 0) {
                html += `<div class="action-category"><h6>Invalid Actions</h6><ul class="action-prob-list">`;
                data.invalid.forEach(action => {
                    html += `<li class="invalid-action" title="${action.reason} (${action.group})"><span>${action.display_name}</span><div class="action-prob-bar-container"></div></li>`;
                });
                html += '</ul></div>';
            }
            content.innerHTML = html;
        }).catch(err => {
            console.error("Failed to fetch action probabilities:", err);
            content.innerHTML = `<p>Could not load action preview.</p>`;
        });
    }

    function updateControls(gameState) {
        const gamePhase = gameState.game_phase;
        const inSetup = gamePhase === 'SETUP';
        const isRunning = gamePhase === 'RUNNING';
        const isFinished = gamePhase === 'FINISHED';
        
        document.body.classList.toggle('game-running', isRunning || isFinished);
        document.body.classList.toggle('game-finished', isFinished);

        if (isFinished) {
            if (uiState.autoPlayInterval) stopAutoPlay();
            autoPlayBtn.textContent = 'Auto-Play';
            nextActionBtn.disabled = true;
            autoPlayBtn.disabled = true;
        } else if (isRunning) {
             nextActionBtn.disabled = false;
             autoPlayBtn.disabled = false;
        }
    }

    // --- Event Handlers & API Calls ---

    document.getElementById('show-invalid-actions').addEventListener('change', () => updateActionPreview(currentGameState));
    compactLogToggle.addEventListener('click', () => {
        uiState.debugOptions.compactLog = compactLogToggle.checked;
        updateLog(currentGameState.game_log, currentGameState.teams);
    });
    debugPointIdsToggle.addEventListener('click', () => uiState.debugOptions.showPointIds = debugPointIdsToggle.checked);
    debugLineIdsToggle.addEventListener('click', () => uiState.debugOptions.showLineIds = debugLineIdsToggle.checked);
    debugLastActionToggle.addEventListener('click', () => uiState.debugOptions.highlightLastAction = debugLastActionToggle.checked);
    showHullsToggle.addEventListener('click', () => uiState.debugOptions.showHulls = showHullsToggle.checked);

    copyLogBtn.addEventListener('click', () => {
        if (navigator.clipboard) {
            const logText = Array.from(logDiv.querySelectorAll('.log-entry')).map(entry => entry.textContent).reverse().join('\n');
            navigator.clipboard.writeText(logText).then(() => showTemporaryButtonFeedback(copyLogBtn, 'Copied!'));
        }
    });

    copyStateBtn.addEventListener('click', async () => {
        if (navigator.clipboard) {
            try {
                const stateString = JSON.stringify(await api.getState(), null, 2);
                await navigator.clipboard.writeText(stateString);
                showTemporaryButtonFeedback(copyStateBtn, 'State Copied!');
            } catch (err) { console.error('Failed to copy game state: ', err); }
        }
    });

    restartServerBtn.addEventListener('click', async () => {
        if (confirm("This will restart the server. The page will reload after a few seconds. Are you sure?")) {
            try {
                await api.restartServer();
                statusBar.textContent = 'Server is restarting... The page will reload shortly.';
                statusBar.style.opacity = '1';
                document.querySelectorAll('button, input, select').forEach(el => el.disabled = true);
                setTimeout(() => location.reload(), 5000);
            } catch (error) { console.error("Error sending restart command:", error); }
        }
    });

    teamsList.addEventListener('click', (e) => {
        if (currentGameState.game_phase !== 'SETUP') return;
        const deleteButton = e.target.closest('.delete-team-btn');
        if (deleteButton) {
            const teamId = deleteButton.dataset.teamId;
            if (!confirm(`Are you sure you want to remove ${uiState.localTeams[teamId]?.name || 'this team'}? This will also delete its points.`)) return;
            if (uiState.selectedTeamId === teamId) {
                const remainingTeamIds = Object.keys(uiState.localTeams).filter(id => id !== teamId);
                uiState.selectedTeamId = remainingTeamIds.length > 0 ? remainingTeamIds[0] : null;
            }
            delete uiState.localTeams[teamId];
            uiState.initialPoints = uiState.initialPoints.filter(p => p.teamId !== teamId);
            renderTeamsList();
        }
    });

    addTeamBtn.addEventListener('click', () => {
        const teamName = newTeamNameInput.value.trim();
        if (teamName && !Object.values(uiState.localTeams).some(t => t.name === teamName)) {
            const teamId = `team-${Date.now()}`;
            uiState.localTeams[teamId] = { id: teamId, name: teamName, color: newTeamColorInput.value, trait: newTeamTraitSelect.value, isEditing: false };
            setNewTeamDefaults();
            uiState.selectedTeamId = teamId;
            renderTeamsList();
        } else if (teamName) {
            alert('A team with this name already exists.');
        }
    });

    newTeamNameInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); addTeamBtn.click(); } });
    undoPointBtn.addEventListener('click', () => { if (uiState.initialPoints.length > 0) uiState.initialPoints.pop(); });
    clearPointsBtn.addEventListener('click', () => { if (confirm("Clear all points?")) uiState.initialPoints = []; });

    randomizePointsBtn.addEventListener('click', () => {
        if (Object.keys(uiState.localTeams).length === 0) return alert("Please add at least one team.");
        if (uiState.initialPoints.length > 0 && !confirm("Replace all existing points?")) return;
        const pointsPerTeam = parseInt(prompt("How many points per team?", "5"));
        if (isNaN(pointsPerTeam) || pointsPerTeam <= 0) return;
        uiState.initialPoints = [];
        const currentGridSize = parseInt(gridSizeInput.value) || 10;
        for (const teamId in uiState.localTeams) {
            for (let i = 0; i < pointsPerTeam; i++) {
                let x, y, isUnique;
                do {
                    x = Math.floor(Math.random() * currentGridSize);
                    y = Math.floor(Math.random() * currentGridSize);
                    isUnique = !uiState.initialPoints.some(p => p.x === x && p.y === y);
                } while (!isUnique);
                uiState.initialPoints.push({ x, y, teamId });
            }
        }
    });

    canvas.addEventListener('click', (e) => {
        if (currentGameState.game_phase !== 'SETUP') return;
        const rect = canvas.getBoundingClientRect();
        const clickX = e.clientX - rect.left, clickY = e.clientY - rect.top;
        if (clickX < 0 || clickY < 0 || clickX > canvas.width || clickY > canvas.height) return;
        
        const gridSize = currentGameState.grid_size || 10;
        const x = Math.floor(clickX / cellSize), y = Math.floor(clickY / cellSize);
        if (x < 0 || x >= gridSize || y < 0 || y >= gridSize) return;

        const pointIndex = uiState.initialPoints.findIndex(p => p.x === x && p.y === y);
        if (pointIndex !== -1) {
            uiState.initialPoints.splice(pointIndex, 1);
        } else {
            if (!uiState.selectedTeamId) return alert('Please add and select a team first!');
            uiState.initialPoints.push({ x, y, teamId: uiState.selectedTeamId });
        }
    });

    startGameBtn.addEventListener('click', async () => {
        if (uiState.initialPoints.length === 0) return alert("Please add points to the grid.");
        try {
            const gameState = await api.startGame({
                teams: uiState.localTeams, points: uiState.initialPoints,
                maxTurns: parseInt(maxTurnsInput.value), gridSize: parseInt(gridSizeInput.value)
            });
            uiState.initialPoints = [];
            updateStateAndRender(gameState);
        } catch (error) { throw error; }
    });

    restartSimulationBtn.addEventListener('click', async () => {
        if (!confirm("Restart the simulation with the same setup?")) return;
        stopAutoPlay();
        try {
            const gameState = await api.restart();
            if (gameState.error) throw new Error(`Failed to restart game: ${gameState.error}`);
            updateStateAndRender(gameState);
        } catch (error) { throw error; }
    });

    nextActionBtn.addEventListener('click', async () => {
        try {
            updateStateAndRender(await api.nextAction());
        } catch (error) {
            stopAutoPlay();
            throw error;
        }
    });

    function stopAutoPlay() {
        if (uiState.autoPlayInterval) {
            clearInterval(uiState.autoPlayInterval);
            uiState.autoPlayInterval = null;
            autoPlayBtn.textContent = 'Auto-Play';
        }
    }

    autoPlayBtn.addEventListener('click', () => {
        if (uiState.autoPlayInterval) {
            stopAutoPlay();
        } else {
            stopAutoPlay();
            autoPlayBtn.textContent = 'Stop';
            const delay = parseInt(autoPlaySpeedSlider.value, 10);
            uiState.autoPlayInterval = setInterval(() => {
                if (currentGameState.game_phase !== 'RUNNING') return stopAutoPlay();
                (async () => {
                    const gameState = await api.nextAction();
                    updateStateAndRender(gameState);
                    if (gameState.game_phase === 'FINISHED') stopAutoPlay();
                })().catch(e => { stopAutoPlay(); throw e; });
            }, delay);
        }
    });

    autoPlaySpeedSlider.addEventListener('input', () => {
        speedValueSpan.textContent = `${autoPlaySpeedSlider.value}ms`;
        if (uiState.autoPlayInterval) autoPlayBtn.click(); // Stop
        // The user has to click play again to start with the new speed.
    });

    resetBtn.addEventListener('click', async () => {
        stopAutoPlay();
        if (confirm("End the current game and return to setup?")) {
            try {
                const gameState = await api.reset();
                uiState.localTeams = gameState.teams || {};
                Object.values(uiState.localTeams).forEach(t => t.isEditing = false);
                uiState.initialPoints = [];
                const teamIds = Object.keys(uiState.localTeams);
                uiState.selectedTeamId = teamIds.length > 0 ? teamIds[0] : null;
                gridSizeInput.value = gameState.grid_size;
                maxTurnsInput.value = gameState.max_turns;
                setNewTeamDefaults();
                updateStateAndRender(gameState);
                renderTeamsList();
            } catch (error) { throw error; }
        }
    });

    function resizeCanvas() {
        const gridSize = currentGameState.grid_size || 10;
        // Delegate resizing to the renderer
        renderer.resize(gridSize);
        // Update local cellSize for non-rendering calculations (like click handling)
        cellSize = (canvas.clientWidth) / gridSize;
    }

    tabLinks.forEach(link => {
        link.addEventListener('click', () => {
            const tabId = link.dataset.tab;
            tabLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            link.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });

    function createActionGuideFilters(allActions) {
        const togglesContainer = document.getElementById('guide-group-toggles');
        const groupCounts = allActions.reduce((acc, action) => ({ ...acc, [action.group]: (acc[action.group] || 0) + 1 }), {});
        const groups = Object.keys(groupCounts).sort();

        let buttonsHTML = `<button class="active" data-group="All">All (${allActions.length})</button>`;
        groups.forEach(group => {
            buttonsHTML += `<button data-group="${group}">${group} (${groupCounts[group]})</button>`;
        });
        togglesContainer.innerHTML = buttonsHTML;

        togglesContainer.addEventListener('click', e => {
            if (e.target.tagName === 'BUTTON') {
                togglesContainer.querySelector('button.active').classList.remove('active');
                e.target.classList.add('active');
                filterActionGuide();
            }
        });
    }

    function populateActionGuideContent(allActions) {
        const groups = [...new Set(allActions.map(a => a.group))].sort();
        const actionsByGroup = allActions.reduce((acc, action) => {
            if (!acc[action.group]) acc[action.group] = [];
            acc[action.group].push(action);
            return acc;
        }, {});

        actionGuideContent.innerHTML = '';
        for (const group of groups) {
            const section = document.createElement('div');
            section.className = 'guide-group-section';
            section.dataset.group = group;
            section.innerHTML = `<h3 class="guide-group-header">${group}</h3>`;
            const grid = document.createElement('div');
            grid.className = 'action-guide-grid';
            
            actionsByGroup[group].forEach(action => {
                const card = document.createElement('div');
                card.className = 'action-card';
                card.dataset.name = action.name;
                card.dataset.group = action.group;
                card.dataset.displayName = action.display_name;
                card.dataset.description = action.description;
                // Use an <img> tag now
                card.innerHTML = `
                    <img src="static/illustrations/${action.name}.png" alt="Illustration for ${action.display_name}" width="150" height="150" class="action-card-illustration">
                    <div class="action-card-text">
                         <div class="action-card-header">
                            <h4>${action.display_name}</h4>
                            <span class="action-group action-group--${action.group.toLowerCase()}">${action.group}</span>
                        </div>
                        <div class="action-card-description">${action.description}</div>
                    </div>`;
                grid.appendChild(card);
            });

            section.appendChild(grid);
            actionGuideContent.appendChild(section);
        }
    }

    function filterActionGuide() {
        const searchInput = document.getElementById('guide-search');
        const togglesContainer = document.getElementById('guide-group-toggles');
        const searchTerm = searchInput.value.toLowerCase();
        const activeGroup = togglesContainer.querySelector('button.active').dataset.group;

        actionGuideContent.querySelectorAll('.guide-group-section').forEach(section => {
            const sectionGroup = section.dataset.group;
            const groupMatch = activeGroup === 'All' || sectionGroup === activeGroup;
            if (!groupMatch) {
                section.style.display = 'none';
                return;
            }

            section.style.display = 'block';
            let hasVisibleCard = false;
            section.querySelectorAll('.action-card').forEach(card => {
                const searchMatch = card.dataset.displayName.toLowerCase().includes(searchTerm) || card.dataset.description.toLowerCase().includes(searchTerm);
                if (searchMatch) {
                    card.style.display = 'flex';
                    hasVisibleCard = true;
                } else {
                    card.style.display = 'none';
                }
            });
            section.style.display = hasVisibleCard || !searchTerm ? 'block' : 'none';
        });
    }

    // --- Global Functions (for access from other scripts like illustration_generator.js) ---
    window.initActionGuide = async function() {
        try {
            const allActions = await api.getAllActions();
            createActionGuideFilters(allActions);
            populateActionGuideContent(allActions);
            document.getElementById('guide-search').addEventListener('input', filterActionGuide);
        } catch (error) {
            actionGuideContent.innerHTML = '<p>Could not load action guide.</p>';
            console.error("Failed to initialize action guide:", error);
        }
    }

    function setupErrorHandling() {
        const errorOverlay = document.getElementById('error-overlay');
        const errorDetails = document.getElementById('error-details');
        const copyErrorBtn = document.getElementById('copy-error-btn');
        const closeErrorBtn = document.getElementById('close-error-btn');
    
        const showError = (errorText) => {
            stopAutoPlay();
            errorDetails.textContent = errorText;
            errorOverlay.style.display = 'flex';
        };

        window.onerror = (message, source, lineno, colno, error) => {
            showError(`Error: ${message}\nSource: ${source}\nLine: ${lineno}, Column: ${colno}\nStack: ${error ? error.stack : 'N/A'}`);
            return true;
        };
        
        window.addEventListener('unhandledrejection', event => {
            let errorContent = `Unhandled Promise Rejection:\nReason: ${event.reason.stack || event.reason}`;
            if (event.reason?.response_text) {
                const tracebackMatch = event.reason.response_text.match(/<pre>([\s\S]*)<\/pre>/);
                errorContent += `\n\n--- Server Response ---\n${tracebackMatch ? tracebackMatch[1].trim() : 'Could not extract traceback.'}`;
            }
            showError(errorContent);
        });
    
        closeErrorBtn.addEventListener('click', () => errorOverlay.style.display = 'none');
        copyErrorBtn.addEventListener('click', () => {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(errorDetails.textContent).then(() => showTemporaryButtonFeedback(copyErrorBtn, 'Copied!', 1000));
            }
        });
    }

    async function init() {
        setNewTeamDefaults();
        setupErrorHandling();

        // Initialize the renderer with the canvas element
        renderer.init(canvas);

        let apiMode = 'http';
        if (window.location.hostname.endsWith('github.io') || window.location.protocol === 'file:') {
            apiMode = 'pyodide';
        } else {
            try {
                const response = await fetch('/api/check_updates', { method: 'HEAD', cache: 'no-cache' });
                if (!response.ok) apiMode = 'pyodide';
            } catch (error) {
                apiMode = 'pyodide';
            }
        }

        if (apiMode === 'pyodide') {
            statusBar.textContent = 'Loading Python interpreter (Pyodide)...';
            statusBar.style.opacity = '1';
            restartServerBtn.style.display = 'none';
        }

        try {
            await api.initialize(apiMode);
        } catch(e) {
            statusBar.textContent = `Error: Failed to initialize application backend. See console.`;
            statusBar.style.backgroundColor = 'red';
            throw e;
        }

        if (apiMode === 'pyodide') {
            statusBar.textContent = 'Pyodide loaded. Initializing game...';
        }

        gridSizeInput.addEventListener('input', () => {
            if (currentGameState.game_phase === 'SETUP') {
                const newSize = parseInt(gridSizeInput.value, 10);
                if (newSize >= 5 && newSize <= 50) {
                    const outOfBoundsPoints = uiState.initialPoints.filter(p => p.x >= newSize || p.y >= newSize);
                    if (outOfBoundsPoints.length > 0 && !confirm(`Changing grid size will remove ${outOfBoundsPoints.length} out-of-bounds point(s). Continue?`)) {
                        gridSizeInput.value = currentGameState.grid_size;
                        return;
                    }
                    currentGameState.grid_size = newSize;
                    uiState.initialPoints = uiState.initialPoints.filter(p => p.x < newSize && p.y < newSize);
                    resizeCanvas();
                }
            }
        });

        const resizeObserver = new ResizeObserver(() => requestAnimationFrame(() => {
            if(currentGameState && currentGameState.grid_size) resizeCanvas();
        }));
        resizeObserver.observe(document.querySelector('.grid-container'));

        const gameState = await api.getState();
        
        if (gameState.game_phase === 'SETUP') {
             uiState.localTeams = gameState.teams || {};
             Object.values(uiState.localTeams).forEach(t => t.isEditing = false);
             uiState.initialPoints = Object.values(gameState.points);
             const teamIds = Object.keys(uiState.localTeams);
             if (teamIds.length > 0) uiState.selectedTeamId = teamIds[0];
        } else {
             uiState.localTeams = gameState.teams || {};
             uiState.initialPoints = [];
        }
        
        gridSizeInput.value = gameState.grid_size;
        maxTurnsInput.value = gameState.max_turns;

        updateStateAndRender(gameState);
        setTimeout(() => resizeCanvas(), 50);
        window.initActionGuide(); // Use the global function now
        
        // Add event listener for the new button
        document.getElementById('generate-illustrations-btn').addEventListener('click', () => {
             if (typeof generateAndSaveAllIllustrations === 'function') {
                if(confirm('This will generate and save all illustration PNGs to static/illustrations/. This is a developer feature. Continue?')) {
                    generateAndSaveAllIllustrations();
                }
            } else {
                alert('Illustration generation function not found.');
            }
        });
        
        // Start the main animation loop
        animationLoop();
    }

    init();
});