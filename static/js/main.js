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
        playbackInterval: null,
        debugOptions: {
            showPointIds: false,
            showLineIds: false,
            highlightLastAction: false,
            showHulls: false,
            compactLog: true
        },
        visualEffects: [], // For temporary animations
        lastActionHighlights: { // For highlighting the last action's components
            points: new Set(),
            lines: new Set(),
            structures: new Set(),
            clearTimeout: null
        }
    };
    let simulationHistory = []; // Full history of RAW game states
    let augmentedHistoryCache = {}; // Cache for augmented states { index: state }
    let playbackIndex = 0; // Current index in the simulationHistory
    let currentGameState = {}; // The AUGMENTED state object for the CURRENT playback index

    // --- UI Elements ---
    const teamsList = document.getElementById('teams-list');
    const newTeamNameInput = document.getElementById('new-team-name');
    const newTeamColorInput = document.getElementById('new-team-color');
    const newTeamTraitSelect = document.getElementById('new-team-trait');
    const addTeamBtn = document.getElementById('add-team-btn');
    const startGameBtn = document.getElementById('start-game-btn');
    const playbackPrevBtn = document.getElementById('playback-prev-btn');
    const playbackNextBtn = document.getElementById('playback-next-btn');
    const playbackPlayPauseBtn = document.getElementById('playback-play-pause-btn');
    const playbackProgressBar = document.getElementById('playback-progress-bar');
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

    /**
     * Determines if a hex color is dark.
     * @param {string} hexColor - The color in hex format (e.g., '#ff0000').
     * @returns {boolean} True if the color is dark, false otherwise.
     */
    function isColorDark(hexColor) {
        if (!hexColor) return false;
        const color = (hexColor.charAt(0) === '#') ? hexColor.substring(1, 7) : hexColor;
        if (color.length < 6) return false;
        const r = parseInt(color.substring(0, 2), 16);
        const g = parseInt(color.substring(2, 4), 16);
        const b = parseInt(color.substring(4, 6), 16);
        // Using the HSP (Highly Sensitive Poo) equation to determine perceived brightness
        const hsp = Math.sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b));
        return hsp < 127.5;
    }

    /**
     * Lightens or darkens a hex color.
     * @param {string} hex - The color in hex format (e.g., '#ff0000').
     * @param {number} percent - The percentage to lighten (positive) or darken (negative).
     * @returns {string} The new hex color.
     */
    function adjustColor(hex, percent) {
        const f = parseInt(hex.slice(1), 16);
        const t = percent < 0 ? 0 : 255;
        const p = percent < 0 ? percent * -1 : percent;
        const R = f >> 16;
        const G = (f >> 8) & 0x00ff;
        const B = f & 0x0000ff;
        const newR = Math.round((t - R) * p) + R;
        const newG = Math.round((t - G) * p) + G;
        const newB = Math.round((t - B) * p) + B;
        return `#${(0x1000000 + newR * 0x10000 + newG * 0x100 + newB).toString(16).slice(1)}`;
    }

    function colorizeTeamNames(message, teams) {
        let finalMessage = message;
        for (const teamId in teams) {
            const team = teams[teamId];
            // Use a regex with word boundaries to avoid replacing parts of words
            finalMessage = finalMessage.replace(new RegExp(`\\b${team.name}\\b`, 'g'), `<strong style="color: ${team.color};">${team.name}</strong>`);
        }
        return finalMessage;
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

    async function showStateAtIndex(index, previousIndex = null) {
        if (index < 0 || index >= simulationHistory.length) return;

        playbackIndex = index;
        let augmentedState = augmentedHistoryCache[index];
        let previousAugmentedState = previousIndex !== null ? augmentedHistoryCache[previousIndex] : null;

        if (!augmentedState) {
            const rawState = simulationHistory[index];
            augmentedState = await api.augmentState(rawState);
            augmentedHistoryCache[index] = augmentedState;
        }

        if (previousIndex !== null && !previousAugmentedState) {
            const rawPrevState = simulationHistory[previousIndex];
            previousAugmentedState = await api.augmentState(rawPrevState);
            augmentedHistoryCache[previousIndex] = previousAugmentedState;
        }
        
        currentGameState = augmentedState;

        visualEffectsManager.processStateChange(previousAugmentedState, augmentedState, uiState, cellSize);
        
        renderTeamsList();
        updateLog(augmentedState.game_log, augmentedState.teams);
        updateInterpretationPanel(augmentedState);
        updateActionPreview(augmentedState);
        updateControls(augmentedState);
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
            logEntryDiv.innerHTML = colorizeTeamNames(message, teams);

            // Standard action log: colored background
            if (entry.teamId && teams[entry.teamId] && !entry.is_event) {
                const team = teams[entry.teamId];
                logEntryDiv.classList.add('team-log');
                logEntryDiv.style.backgroundColor = team.color;
                logEntryDiv.style.color = isColorDark(team.color) ? '#fff' : '#333';

                if (uiState.debugOptions.compactLog) {
                    logEntryDiv.style.fontWeight = 'bold';
                }
            } else { // Environment or event log: default background
                if (message.startsWith('--- Turn')) {
                     logEntryDiv.style.textAlign = 'center';
                     logEntryDiv.style.background = '#e9ecef';
                     logEntryDiv.style.fontWeight = 'bold';
                } else {
                     logEntryDiv.style.background = '#f8f9fa';
                     logEntryDiv.style.borderLeft = `3px solid #ccc`;
                     // If it's an event associated with a team, color the border
                     if(entry.teamId && teams[entry.teamId]) {
                         logEntryDiv.style.borderLeftColor = teams[entry.teamId].color;
                     }
                }
            }
            logDiv.prepend(logEntryDiv);
        });
        logDiv.scrollTop = 0;

        if (currentGameState.game_phase === 'RUNNING' || currentGameState.game_phase === 'FINISHED') {
            if (lastMessageEntry) {
                const team = teams[lastMessageEntry.teamId];
                let finalMessage = lastMessageEntry.message;
                // Set the base color for the message to the team's color.
                statusBar.style.color = team.color;

                // Individually color any team names mentioned in the message for emphasis.
                statusBar.innerHTML = colorizeTeamNames(finalMessage, teams);
            } else {
                statusBar.textContent = currentGameState.game_phase === 'FINISHED' ? 'Simulation Complete.' : 'Starting game...';
                statusBar.style.color = '#333'; // Reset to default
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
        const probData = gameState.action_probabilities;

        if (gameState.game_phase === 'SETUP') {
            actionPreviewPanel.style.display = 'none';
            return;
        }
        actionPreviewPanel.style.display = 'block';

        if (!probData) {
            // This can happen at the very end of the simulation, or at the end of a turn
            // before the next turn's action queue is built.
            // Instead of showing "Simulation Complete", we just leave the last
            // valid preview visible, as requested.
            return;
        }

        let html = `<h5 style="border-color:${probData.color};">Action Probs: ${probData.team_name}</h5>`;
        
        const sortedGroups = Object.entries(probData.groups).sort(([, a], [, b]) => b.group_probability - a.group_probability);

        if (sortedGroups.length === 0) {
            html += '<p>No valid actions available.</p>';
        }

        let maxProb = 0;
        sortedGroups.forEach(([, groupData]) => {
            groupData.actions.forEach(action => {
                if (action.probability > maxProb) {
                    maxProb = action.probability;
                }
            });
        });
        if (maxProb === 0) maxProb = 1; // Avoid division by zero


        for (const [groupName, groupData] of sortedGroups) {
            html += `
                <div class="action-category">
                    <h6>${groupName} (${groupData.group_probability}%)</h6>
                    <ul class="action-prob-list">
                        ${groupData.actions.map(action => `
                            <li class="${action.no_cost ? 'free-action' : ''}">
                                <span>${action.display_name}</span>
                                <div class="action-prob-bar-container">
                                    <div class="action-prob-bar" style="width: ${action.probability / maxProb * 100}%; background-color: ${probData.color};"></div>
                                </div>
                                <span class="action-prob-percent">${action.probability}%</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }
        content.innerHTML = html;
    }

    function updateControls(gameState) {
        const { game_phase, actions_queue_this_turn, action_in_turn, teams } = gameState;
        const isRunning = game_phase === 'RUNNING' || game_phase === 'FINISHED';
        
        document.body.classList.toggle('game-running', isRunning);
        document.body.classList.toggle('game-finished', game_phase === 'FINISHED');
    
        const isAtStart = playbackIndex <= 0;
        const isAtEnd = playbackIndex >= simulationHistory.length - 1;
    
        if (game_phase === 'SETUP') {
             // Handled by the class toggles
        } else if (isRunning) {
            playbackPrevBtn.disabled = isAtStart;
            playbackNextBtn.disabled = isAtEnd;
            playbackPlayPauseBtn.disabled = isAtEnd;
            
            if (isAtEnd) {
                stopPlayback();
            }
    
            // Set progress bar color based on next team to act
            let actorTeamColor = '#3498db'; // default blue
            if (actions_queue_this_turn && actions_queue_this_turn.length > 0) {
                // action_in_turn points to the action that will be taken *from* this state.
                // If at the last state, there's no next action, so this might be out of bounds. Clamp it.
                const currentActionIndex = Math.min(action_in_turn, actions_queue_this_turn.length - 1);
                const actionInfo = actions_queue_this_turn[currentActionIndex];
    
                if (actionInfo && teams[actionInfo.teamId]) {
                    actorTeamColor = teams[actionInfo.teamId].color;
                }
            }
            document.documentElement.style.setProperty('--progress-bar-color', actorTeamColor);
    
            // Update progress bar value
            if (simulationHistory.length > 1) {
                playbackProgressBar.max = simulationHistory.length - 1;
                playbackProgressBar.value = playbackIndex;
            } else {
                playbackProgressBar.max = 1;
                playbackProgressBar.value = 1;
            }
        }
    }

    // --- Event Handlers & API Calls ---

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
        
        const pointsCountInput = document.getElementById('random-points-count');
        const pointsPerTeam = parseInt(pointsCountInput.value, 10);

        if (isNaN(pointsPerTeam) || pointsPerTeam <= 0) {
            alert("Please enter a valid number of points per team.");
            return;
        }

        uiState.initialPoints = [];
        const currentGridSize = parseInt(gridSizeInput.value) || 10;
        for (const teamId in uiState.localTeams) {
            for (let i = 0; i < pointsPerTeam; i++) {
                let x, y, isUnique;
                let attempts = 0;
                do {
                    x = Math.floor(Math.random() * currentGridSize);
                    y = Math.floor(Math.random() * currentGridSize);
                    isUnique = !uiState.initialPoints.some(p => p.x === x && p.y === y);
                    attempts++;
                } while (!isUnique && attempts < currentGridSize * currentGridSize);
                if(isUnique) {
                    uiState.initialPoints.push({ x, y, teamId });
                } else {
                    console.warn(`Could not find a unique spot for a point for team ${teamId} after ${attempts} attempts. Grid may be full.`);
                }
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
        
        // Explicitly clear any previous simulation data
        simulationHistory = [];
        augmentedHistoryCache = {};
        playbackIndex = 0;
        
        const loader = document.getElementById('simulation-loader');
        const loaderText = document.getElementById('loader-text');
        const loaderProgress = document.getElementById('loader-progress');
        loader.style.display = 'flex';
        loaderProgress.style.display = 'block';
        loaderProgress.value = 0;
        
        try {
            const payload = {
                teams: uiState.localTeams, points: uiState.initialPoints,
                maxTurns: parseInt(maxTurnsInput.value), gridSize: parseInt(gridSizeInput.value)
            };

            const progressCallback = (progress, turn, maxTurns, currentStep) => {
                loaderProgress.value = progress;
                const displayTurn = Math.max(1, turn);
                loaderText.textContent = `Simulating Turn ${displayTurn}/${maxTurns} (Step: ${currentStep})...`;
            };

            const simulationData = await api.startGameAsync(payload, progressCallback);

            uiState.initialPoints = [];
            simulationHistory = simulationData.history || simulationData.raw_history;
            augmentedHistoryCache = {};
            
            // If the API returned pre-augmented history (HTTP mode), cache it.
            if (simulationData.history) {
                simulationData.history.forEach((state, index) => {
                    augmentedHistoryCache[index] = state;
                });
            }
            
            await showStateAtIndex(0);

        } catch (error) {
            // Re-throw to be caught by global error handler
            throw error;
        } finally {
            loader.style.display = 'none';
        }
    });

    restartSimulationBtn.addEventListener('click', async () => {
        if (!confirm("Restart the simulation with the same setup?")) return;
        stopPlayback();
        
        // Explicitly clear history before starting new simulation
        simulationHistory = [];
        augmentedHistoryCache = {};
        playbackIndex = 0;

        const loader = document.getElementById('simulation-loader');
        const loaderText = document.getElementById('loader-text');
        const loaderProgress = document.getElementById('loader-progress');
        loader.style.display = 'flex';
        loaderProgress.style.display = 'block';
        loaderProgress.value = 0;

        try {
            const progressCallback = (progress, turn, maxTurns, currentStep) => {
                loaderProgress.value = progress;
                const displayTurn = Math.max(1, turn);
                loaderText.textContent = `Simulating Turn ${displayTurn}/${maxTurns} (Step: ${currentStep})...`;
            };

            const simulationData = await api.restartAsync(progressCallback);
            
            if (simulationData.error) throw new Error(`Failed to restart game: ${simulationData.error}`);
            
            simulationHistory = simulationData.history || simulationData.raw_history;
            augmentedHistoryCache = {};
            
            if (simulationData.history) { // Pre-fill cache for HTTP mode
                simulationData.history.forEach((state, index) => {
                    augmentedHistoryCache[index] = state;
                });
            }
            await showStateAtIndex(0);
        } catch (error) { 
            throw error; 
        } finally {
            loader.style.display = 'none';
        }
    });

    function setupHoldableButton(button, actionFn) {
        let timer;
        let interval;

        const startAction = (e) => {
            if (e.type === 'touchstart') e.preventDefault(); // prevent mouse events from firing
            stopPlayback();
            actionFn();
            // After an initial delay, start repeating
            timer = setTimeout(() => {
                interval = setInterval(actionFn, 60); // Repeat every 60ms
            }, 500); // 500ms initial delay
        };

        const stopAction = () => {
            clearTimeout(timer);
            clearInterval(interval);
        };

        button.addEventListener('mousedown', startAction);
        button.addEventListener('mouseup', stopAction);
        button.addEventListener('mouseleave', stopAction);
        button.addEventListener('touchstart', startAction);
        button.addEventListener('touchend', stopAction);
        button.addEventListener('touchcancel', stopAction);
    }

    setupHoldableButton(playbackPrevBtn, playbackPreviousStep);
    setupHoldableButton(playbackNextBtn, playbackNextStep);

    function stopPlayback() {
        if (uiState.playbackInterval) {
            clearInterval(uiState.playbackInterval);
            uiState.playbackInterval = null;
            playbackPlayPauseBtn.textContent = 'Play';
        }
    }

    function playbackPreviousStep() {
        if (playbackIndex > 0) {
            // When going back, we don't pass the "previous" state to avoid trying to animate backwards.
            // This just snaps to the previous state.
            showStateAtIndex(playbackIndex - 1, null);
        }
    }
    
    function playbackNextStep() {
        if (playbackIndex < simulationHistory.length - 1) {
            showStateAtIndex(playbackIndex + 1, playbackIndex);
        } else {
            stopPlayback(); // Reached the end
        }
    }

    playbackProgressBar.addEventListener('click', (e) => {
        if (simulationHistory.length > 1) {
            const rect = playbackProgressBar.getBoundingClientRect();
            const clickRatio = (e.clientX - rect.left) / rect.width;
            const targetIndex = Math.round(clickRatio * (simulationHistory.length - 1));
            stopPlayback();
            showStateAtIndex(targetIndex, playbackIndex); // Pass previous index for animations
        }
    });

    playbackPlayPauseBtn.addEventListener('click', () => {
        if (uiState.playbackInterval) {
            stopPlayback();
        } else {
            if (playbackIndex >= simulationHistory.length - 1) {
                // If at the end, restart playback from beginning
                showStateAtIndex(0);
            }
            playbackPlayPauseBtn.textContent = 'Pause';
            const delay = parseInt(autoPlaySpeedSlider.value, 10);
            uiState.playbackInterval = setInterval(playbackNextStep, delay);
        }
    });

    autoPlaySpeedSlider.addEventListener('input', () => {
        speedValueSpan.textContent = `${autoPlaySpeedSlider.value}ms`;
        // If playing, restart the interval with the new speed
        if (uiState.playbackInterval) {
            stopPlayback();
            playbackPlayPauseBtn.click();
        }
    });

    resetBtn.addEventListener('click', async () => {
        stopPlayback();
        if (confirm("End the current game and return to setup?")) {
            try {
                const gameState = await api.reset();
                simulationHistory = [];
                augmentedHistoryCache = {};
                playbackIndex = 0;
                uiState.localTeams = gameState.teams || {};
                Object.values(uiState.localTeams).forEach(t => t.isEditing = false);
                uiState.initialPoints = [];
                const teamIds = Object.keys(uiState.localTeams);
                uiState.selectedTeamId = teamIds.length > 0 ? teamIds[0] : null;
                gridSizeInput.value = gameState.grid_size;
                maxTurnsInput.value = gameState.max_turns;
                setNewTeamDefaults();
                currentGameState = gameState; // Manually set for setup phase
                updateLog(gameState.game_log, gameState.teams);
                updateInterpretationPanel(gameState);
                updateActionPreview(gameState);
                updateControls(gameState);
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
            stopPlayback();
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
        
        currentGameState = gameState; // Manually set for setup phase
        updateLog(gameState.game_log, gameState.teams);
        updateInterpretationPanel(gameState);
        updateActionPreview(gameState);
        updateControls(gameState);
        renderTeamsList();

        setTimeout(() => resizeCanvas(), 50);
        window.initActionGuide(); // Use the global function now
        uiState.debugOptions.compactLog = compactLogToggle.checked;
        
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