document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('grid');
    const ctx = canvas.getContext('2d');
    const gridSize = 10; // This will be updated from backend state
    let cellSize = canvas.width / gridSize;

    // Game state - The single source of truth will be the backend
    let localTeams = {};
    let initialPoints = []; // Still a list for setup phase
    let selectedTeamId = null;
    let autoPlayInterval = null;
    let debugOptions = {
        showPointIds: false,
        showLineIds: false,
        highlightLastAction: false
    };
    let currentGameState = {}; // Cache the latest game state
    let visualEffects = []; // For temporary animations
    let lastActionHighlights = {
        points: new Set(),
        lines: new Set(),
        clearTimeout: null
    };

    // UI Elements
    const teamsList = document.getElementById('teams-list');
    const newTeamNameInput = document.getElementById('new-team-name');
    const newTeamColorInput = document.getElementById('new-team-color');
    const newTeamTraitSelect = document.getElementById('new-team-trait');
    const addTeamBtn = document.getElementById('add-team-btn');
    const startGameBtn = document.getElementById('start-game-btn');
    const nextTurnBtn = document.getElementById('next-turn-btn');
    const autoPlayBtn = document.getElementById('auto-play-btn');
    const autoPlaySpeedSlider = document.getElementById('auto-play-speed');
    const speedValueSpan = document.getElementById('speed-value');
    const resetBtn = document.getElementById('reset-btn');
    const undoPointBtn = document.getElementById('undo-point-btn');
    const randomizePointsBtn = document.getElementById('randomize-points-btn');
    const maxTurnsInput = document.getElementById('max-turns');
    const gridSizeInput = document.getElementById('grid-size');
    const statsDiv = document.getElementById('stats');
    const logDiv = document.getElementById('log');
    const turnCounter = document.getElementById('turn-counter');
    const statusBar = document.getElementById('status-bar');
    const finalInterpDiv = document.getElementById('final-interpretation');
    const finalInterpContent = document.getElementById('final-stats-content');
    const finalInterpDiv = document.getElementById('final-interpretation');
    const finalInterpContent = document.getElementById('final-stats-content');

    // Debug Toggles
    const debugPointIdsToggle = document.getElementById('debug-point-ids');
    const debugLineIdsToggle = document.getElementById('debug-line-ids');
    const debugLastActionToggle = document.getElementById('debug-last-action');

    // --- Core Functions ---

    function drawGrid() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = '#e0e0e0';
        for (let i = 0; i <= gridSize; i++) {
            ctx.beginPath();
            ctx.moveTo(i * cellSize, 0);
            ctx.lineTo(i * cellSize, canvas.height);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(0, i * cellSize);
            ctx.lineTo(canvas.width, i * cellSize);
            ctx.stroke();
        }
    }

    function drawPoints(pointsDict, teams) {
        if (!pointsDict) return;
        Object.values(pointsDict).forEach(p => {
            const team = teams[p.teamId];
            if (team) {
                const cx = (p.x + 0.5) * cellSize;
                const cy = (p.y + 0.5) * cellSize;
                const radius = 5;

                // Highlight effect
                if (debugOptions.highlightLastAction && lastActionHighlights.points.has(p.id)) {
                    ctx.fillStyle = 'rgba(255, 255, 0, 0.8)';
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius + 4, 0, 2 * Math.PI);
                    ctx.fill();
                }

                ctx.fillStyle = team.color;
                ctx.beginPath();
                ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
                ctx.fill();

                if (debugOptions.showPointIds) {
                    ctx.fillStyle = '#000';
                    ctx.font = '10px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'bottom';
                    // Display the point's unique ID
                    ctx.fillText(p.id, cx, cy - (radius + 2));
                }
            }
        });
    }

    function drawLines(pointsDict, lines, teams) {
        if (!pointsDict) return;
        lines.forEach(line => {
            const team = teams[line.teamId];
            if (team) {
                const p1 = pointsDict[line.p1_id];
                const p2 = pointsDict[line.p2_id];
                if (p1 && p2) {
                    const x1 = (p1.x + 0.5) * cellSize;
                    const y1 = (p1.y + 0.5) * cellSize;
                    const x2 = (p2.x + 0.5) * cellSize;
                    const y2 = (p2.y + 0.5) * cellSize;

                    // Highlight effect
                    if (debugOptions.highlightLastAction && lastActionHighlights.lines.has(line.id)) {
                        ctx.strokeStyle = 'rgba(255, 255, 0, 0.8)'; // Yellow halo
                        ctx.lineWidth = 8;
                        ctx.beginPath();
                        ctx.moveTo(x1, y1);
                        ctx.lineTo(x2, y2);
                        ctx.stroke();
                    }

                    // Draw shield effect first (underneath the main line)
                    if (line.is_shielded) {
                        ctx.strokeStyle = 'rgba(173, 216, 230, 0.9)'; // Light blue halo
                        ctx.lineWidth = 6;
                        ctx.beginPath();
                        ctx.moveTo(x1, y1);
                        ctx.lineTo(x2, y2);
                        ctx.stroke();
                    }

                    // Draw the main line
                    ctx.strokeStyle = team.color;
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.stroke();

                    // Draw Line ID
                    if (debugOptions.showLineIds && line.id) {
                        ctx.save();
                        ctx.translate((x1 + x2) / 2, (y1 + y2) / 2);
                        ctx.fillStyle = '#000';
                        ctx.font = '9px Arial';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
                        ctx.fillRect(-15, -7, 30, 14);
                        ctx.fillStyle = '#000';
                        ctx.fillText(line.id, 0, 0);
                        ctx.restore();
                    }
                }
            }
        });
    }

    function drawTerritories(pointsDict, territories, teams) {
        if (!pointsDict) return;
        territories.forEach(territory => {
            const team = teams[territory.teamId];
            if (team) {
                const triPoints = territory.point_ids.map(id => pointsDict[id]);
                if (triPoints.length === 3 && triPoints.every(p => p)) {
                    ctx.fillStyle = team.color;
                    ctx.globalAlpha = 0.3; // semi-transparent
                    ctx.beginPath();
                    ctx.moveTo((triPoints[0].x + 0.5) * cellSize, (triPoints[0].y + 0.5) * cellSize);
                    ctx.lineTo((triPoints[1].x + 0.5) * cellSize, (triPoints[1].y + 0.5) * cellSize);
                    ctx.lineTo((triPoints[2].x + 0.5) * cellSize, (triPoints[2].y + 0.5) * cellSize);
                    ctx.closePath();
                    ctx.fill();
                    ctx.globalAlpha = 1.0; // reset alpha
                }
            }
        });
    }

    function drawVisualEffects() {
        const now = Date.now();
        visualEffects = visualEffects.filter(effect => {
            const age = now - effect.startTime;
            if (age > effect.duration) return false; // Remove expired effects

            const progress = age / effect.duration;

            if (effect.type === 'nova_burst') {
                ctx.beginPath();
                ctx.arc(
                    (effect.x + 0.5) * cellSize,
                    (effect.y + 0.5) * cellSize,
                    effect.radius * progress, // Radius grows
                    0, 2 * Math.PI
                );
                ctx.strokeStyle = `rgba(255, 100, 100, ${1 - progress})`; // Fade out
                ctx.lineWidth = 3;
                ctx.stroke();
            } else if (effect.type === 'new_line') {
                const p1 = currentGameState.points[effect.line.p1_id];
                const p2 = currentGameState.points[effect.line.p2_id];
                if(p1 && p2) {
                    ctx.beginPath();
                    ctx.moveTo((p1.x + 0.5) * cellSize, (p1.y + 0.5) * cellSize);
                    ctx.lineTo((p2.x + 0.5) * cellSize, (p2.y + 0.5) * cellSize);
                    ctx.strokeStyle = `rgba(255, 255, 255, ${0.8 * (1 - progress)})`; // White flash
                    ctx.lineWidth = 5;
                    ctx.stroke();
                }
            } else if (effect.type === 'attack_ray') {
                const x1 = (effect.p1.x + 0.5) * cellSize;
                const y1 = (effect.p1.y + 0.5) * cellSize;
                const x2 = (effect.p2.x + 0.5) * cellSize;
                const y2 = (effect.p2.y + 0.5) * cellSize;
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.strokeStyle = `rgba(255, 0, 0, ${1 - progress})`; // Red, fading out
                ctx.lineWidth = 3;
                ctx.stroke();
            }
            
            return true; // Keep active effects
        });
    }

    function fullRender() {
        if (!currentGameState || !currentGameState.teams) return;
        
        // Update grid scaling
        cellSize = canvas.width / currentGameState.grid_size;

        // Drawing functions
        drawGrid();
        drawTerritories(currentGameState.points, currentGameState.territories || [], currentGameState.teams);
        drawLines(currentGameState.points, currentGameState.lines, currentGameState.teams);
        drawPoints(currentGameState.points, currentGameState.teams);
        drawVisualEffects();

        // UI update functions are less frequent, no need to be in animation loop
    }

    // Main animation loop
    function animationLoop() {
        fullRender();
        requestAnimationFrame(animationLoop);
    }
    
    function processActionVisuals(gameState) {
        const details = gameState.last_action_details;
        if (!details || !details.type) return;

        // Clear previous highlights
        clearTimeout(lastActionHighlights.clearTimeout);
        lastActionHighlights.points.clear();
        lastActionHighlights.lines.clear();

        if (details.type === 'nova_burst' && details.sacrificed_point) {
            lastActionHighlights.points.add(details.sacrificed_point.id);
            visualEffects.push({
                type: 'nova_burst',
                x: details.sacrificed_point.x,
                y: details.sacrificed_point.y,
                radius: (gameState.grid_size * 0.25) * cellSize,
                startTime: Date.now(),
                duration: 750 // ms
            });
        }
        if (details.type === 'add_line' && details.line) {
            lastActionHighlights.lines.add(details.line.id);
            lastActionHighlights.points.add(details.line.p1_id);
            lastActionHighlights.points.add(details.line.p2_id);
            visualEffects.push({
                type: 'new_line',
                line: details.line,
                startTime: Date.now(),
                duration: 500 // ms
            });
        }
        if (details.type === 'attack_line' && details.attack_ray) {
            lastActionHighlights.lines.add(details.attacker_line.id);
            // Highlight the line that *was* destroyed, even though it's gone from state
            // We can't do this easily as it's already removed. Highlighting the attacker is enough.
            visualEffects.push({
                type: 'attack_ray',
                p1: details.attack_ray.p1,
                p2: details.attack_ray.p2,
                startTime: Date.now(),
                duration: 600 // ms
            });
        }
        if (details.type === 'extend_line' && details.new_point) {
            lastActionHighlights.points.add(details.new_point.id);
        }
        if (details.type === 'shield_line' && details.shielded_line) {
            lastActionHighlights.lines.add(details.shielded_line.id);
        }
        if (details.type === 'claim_territory' && details.territory) {
            details.territory.point_ids.forEach(pid => lastActionHighlights.points.add(pid));
        }

        // Set a timer to clear the highlights
        lastActionHighlights.clearTimeout = setTimeout(() => {
            lastActionHighlights.points.clear();
            lastActionHighlights.lines.clear();
        }, 2000); // Highlight for 2 seconds
    }

    function updateStateAndRender(gameState) {
        if (!gameState || !gameState.teams) return;
        currentGameState = gameState; // Cache state
        
        processActionVisuals(gameState);

        // UI update functions (don't need to be in every frame)
        updateLog(gameState.game_log, gameState.teams);
        updateInterpretationPanel(gameState);
        updateControls(gameState);
        // The animation loop will handle the drawing
    }

    // --- UI Update Functions ---

    function renderTeamsList() {
        teamsList.innerHTML = '';
        const inSetupPhase = currentGameState.game_phase === 'SETUP';

        // Use local setup teams during setup, otherwise use teams from game state
        const teamsToRender = inSetupPhase && Object.keys(localTeams).length > 0 ? localTeams : currentGameState.teams;

        for (const teamId in teamsToRender) {
            const team = teamsToRender[teamId];
            const li = document.createElement('li');
            li.dataset.teamId = teamId;

            if (selectedTeamId === teamId && inSetupPhase) {
                li.classList.add('selected');
            }

            const colorBox = document.createElement('div');
            colorBox.className = 'team-color-box';
            colorBox.style.backgroundColor = team.color;
            li.appendChild(colorBox);

            const teamInfo = document.createElement('div');
            teamInfo.className = 'team-info';
            const teamName = document.createElement('span');
            teamName.className = 'team-name';
            teamName.textContent = team.name;
            teamInfo.appendChild(teamName);

            if (team.trait) {
                const teamTrait = document.createElement('span');
                teamTrait.className = 'team-trait';
                teamTrait.textContent = `(${team.trait})`;
                teamInfo.appendChild(teamTrait);
            }
            li.appendChild(teamInfo);

            if (inSetupPhase) {
                li.style.cursor = 'pointer';
                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = '×';
                deleteBtn.className = 'delete-team-btn';
                deleteBtn.dataset.teamId = teamId;
                li.appendChild(deleteBtn);
            }

            teamsList.appendChild(li);
        }
    }

    function updateLog(log, teams) {
        logDiv.innerHTML = ''; // Clear previous logs
        if (!log) return;

        let lastMessage = 'Game log is empty.';
        log.forEach(entry => {
            const logEntryDiv = document.createElement('div');
            logEntryDiv.className = 'log-entry';
            logEntryDiv.textContent = entry.message;
            if (entry.teamId && teams[entry.teamId]) {
                logEntryDiv.style.borderLeftColor = teams[entry.teamId].color;
            }
            logDiv.appendChild(logEntryDiv);
            lastMessage = entry.message;
        });
        logDiv.scrollTop = logDiv.scrollHeight;

        // Update status bar
        if (currentGameState.game_phase === 'RUNNING') {
            statusBar.textContent = lastMessage;
            statusBar.style.opacity = '1';
        } else {
            statusBar.style.opacity = '0';
        }
    }

    function updateInterpretationPanel(gameState) {
        const { turn, max_turns, teams, points, lines, game_phase, interpretation, victory_condition } = gameState;

        turnCounter.textContent = `Turn: ${turn} / ${max_turns}`;

        // Live stats
        let statsHTML = '<h4>Live Stats</h4>';
        if (teams && Object.keys(teams).length > 0) {
             for (const teamId in teams) {
                const team = teams[teamId];
                const pointCount = points ? Object.values(points).filter(p => p.teamId === teamId).length : 0;
                const lineCount = lines.filter(l => l.teamId === teamId).length;
                statsHTML += `<div><strong style="color:${team.color};">${team.name}</strong>: ${pointCount} points, ${lineCount} lines</div>`;
            }
        } else {
            statsHTML += '<p>No teams yet.</p>';
        }
        statsDiv.innerHTML = statsHTML;
    
        // Final interpretation
        if (game_phase === 'FINISHED' && interpretation) {
            finalInterpContent.innerHTML = ''; // Clear previous content

            // Display victory condition
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

                const cardHeader = document.createElement('div');
                cardHeader.className = 'interp-card-header';
                cardHeader.style.backgroundColor = team.color;
                cardHeader.textContent = team.name;
                card.appendChild(cardHeader);

                const statsList = document.createElement('ul');
                statsList.className = 'interp-stats-list';

                const allStats = {
                    'Points': teamData.point_count,
                    'Lines': teamData.line_count,
                    'Total Line Length': teamData.line_length,
                    'Triangles': teamData.triangles,
                    'Territory Area': teamData.controlled_area,
                    'Influence Area (Hull)': teamData.hull_area,
                    'Hull Perimeter': teamData.hull_perimeter
                };

                let hasStats = false;
                for (const [statName, statValue] of Object.entries(allStats)) {
                    if (statValue > 0) {
                        hasStats = true;
                        const li = document.createElement('li');
                        li.innerHTML = `<strong>${statName}:</strong> ${statValue}`;
                        statsList.appendChild(li);
                    }
                }
                
                if (hasStats) {
                    card.appendChild(statsList);
                }

                const divinationText = document.createElement('p');
                divinationText.className = 'interp-divination';
                divinationText.textContent = `"${teamData.divination_text}"`;
                card.appendChild(divinationText);

                cardsContainer.appendChild(card);
            }
            finalInterpContent.appendChild(cardsContainer);
            finalInterpDiv.style.display = 'block';
        } else {
            finalInterpDiv.style.display = 'none';
        }
    }

    function updateControls(gameState) {
        const gamePhase = gameState.game_phase;
        document.getElementById('setup-phase').style.display = gamePhase === 'SETUP' ? 'block' : 'none';
        document.getElementById('action-phase').style.display = gamePhase === 'RUNNING' ? 'block' : 'none';

        const isFinished = gamePhase === 'FINISHED';
        nextTurnBtn.disabled = isFinished;
        autoPlayBtn.disabled = isFinished;

        if (isFinished) {
            if (autoPlayInterval) stopAutoPlay();
            autoPlayBtn.textContent = 'Auto-Play';
        }
    }

    // --- Event Handlers & API Calls ---

    debugPointIdsToggle.addEventListener('click', () => {
        debugOptions.showPointIds = debugPointIdsToggle.checked;
    });
    debugLineIdsToggle.addEventListener('click', () => {
        debugOptions.showLineIds = debugLineIdsToggle.checked;
    });
    debugLastActionToggle.addEventListener('click', () => {
        debugOptions.highlightLastAction = debugLastActionToggle.checked;
    });

    // A single listener for team list interactions (selection and deletion)
    teamsList.addEventListener('click', (e) => {
        if (currentGameState.game_phase !== 'SETUP') return;

        const li = e.target.closest('li');
        if (!li) return;

        const teamId = li.dataset.teamId;

        // Handle team deletion
        if (e.target.classList.contains('delete-team-btn')) {
            const teamName = localTeams[teamId]?.name || 'this team';
            if (!confirm(`Are you sure you want to remove ${teamName}?`)) return;

            // If the deleted team was selected, deselect it or pick another
            if (selectedTeamId === teamId) {
                selectedTeamId = null;
                const remainingTeamIds = Object.keys(localTeams).filter(id => id !== teamId);
                if (remainingTeamIds.length > 0) {
                    selectedTeamId = remainingTeamIds[0];
                }
            }

            // Remove team from local state
            delete localTeams[teamId];
            // Remove points associated with that team
            initialPoints = initialPoints.filter(p => p.teamId !== teamId);
            
            // Re-render teams list and the grid
            renderTeamsList();
            drawGrid(); // Redraw grid and points
            const tempPointsDict = {};
            initialPoints.forEach((p, i) => tempPointsDict[`p_${i}`] = {...p, id: `p_${i}`});
            drawPoints(tempPointsDict, localTeams);
            return;
        }

        // Handle team selection
        selectedTeamId = teamId;
        renderTeamsList();
    });

    addTeamBtn.addEventListener('click', () => {
        const teamName = newTeamNameInput.value.trim();
        const trait = newTeamTraitSelect.value;
        if (teamName && !Object.values(localTeams).some(t => t.name === teamName)) {
            const teamId = `team-${Date.now()}`; // More unique ID
            
            localTeams[teamId] = {
                name: teamName,
                color: newTeamColorInput.value,
                trait: trait
            };
            newTeamNameInput.value = '';
            // Auto-select the new team
            selectedTeamId = teamId;
            renderTeamsList();
        } else if (teamName) {
            alert('A team with this name already exists.');
        }
    });

    undoPointBtn.addEventListener('click', () => {
        if (initialPoints.length > 0) {
            initialPoints.pop();
            // Draw immediately for responsiveness
            drawGrid();
            // We need to convert the initialPoints list to a dictionary for drawing
            const tempPointsDict = {};
            initialPoints.forEach((p, i) => tempPointsDict[`p_${i}`] = {...p, id: `p_${i}`});
            drawPoints(tempPointsDict, localTeams);
        }
    });

    randomizePointsBtn.addEventListener('click', () => {
        if (Object.keys(localTeams).length === 0) {
            alert("Please add at least one team before randomizing points.");
            return;
        }
        const pointsPerTeam = parseInt(prompt("How many points per team?", "5"));
        if (isNaN(pointsPerTeam) || pointsPerTeam <= 0) return;

        initialPoints = []; // Clear existing points
        const currentGridSize = parseInt(gridSizeInput.value) || 10;

        for (const teamId in localTeams) {
            for (let i = 0; i < pointsPerTeam; i++) {
                let x, y, isUnique;
                do {
                    x = Math.floor(Math.random() * currentGridSize);
                    y = Math.floor(Math.random() * currentGridSize);
                    isUnique = !initialPoints.some(p => p.x === x && p.y === y);
                } while (!isUnique);
                initialPoints.push({ x, y, teamId });
            }
        }
        // Draw immediately
        drawGrid();
        const tempPointsDict = {};
        initialPoints.forEach((p, i) => tempPointsDict[`p_${i}`] = {...p, id: `p_${i}`});
        drawPoints(tempPointsDict, localTeams);
    });

    canvas.addEventListener('click', (e) => {
        if (currentGameState.game_phase !== 'SETUP') {
            return;
        }
        if (!selectedTeamId) {
            alert('Please add and select a team first!');
            return;
        }

        const rect = canvas.getBoundingClientRect();
        const x = Math.floor((e.clientX - rect.left) / cellSize);
        const y = Math.floor((e.clientY - rect.top) / cellSize);

        // Avoid duplicate points
        if (!initialPoints.some(p => p.x === x && p.y === y)) {
            initialPoints.push({ x, y, teamId: selectedTeamId });
            // Draw immediately for responsiveness
            drawGrid();
            // We need to convert the initialPoints list to a dictionary for drawing
            const tempPointsDict = {};
            initialPoints.forEach((p, i) => tempPointsDict[`p_${i}`] = {...p, id: `p_${i}`});
            drawPoints(tempPointsDict, localTeams);
        }
    });

    startGameBtn.addEventListener('click', async () => {
        if (initialPoints.length === 0) {
            alert("Please add some points to the grid before starting.");
            return;
        }
        const payload = {
            teams: localTeams,
            points: initialPoints,
            maxTurns: parseInt(maxTurnsInput.value),
            gridSize: parseInt(gridSizeInput.value)
        };
        const response = await fetch('/api/game/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const gameState = await response.json();
        initialPoints = []; // Clear setup points after game starts
        updateStateAndRender(gameState);
    });

    nextTurnBtn.addEventListener('click', async () => {
        const response = await fetch('/api/game/next_turn', { method: 'POST' });
        const gameState = await response.json();
        updateStateAndRender(gameState);
    });

    function stopAutoPlay() {
        if (autoPlayInterval) {
            clearInterval(autoPlayInterval);
            autoPlayInterval = null;
            autoPlayBtn.textContent = 'Auto-Play';
        }
    }

    function startAutoPlay() {
        stopAutoPlay(); // Ensure no multiple intervals are running
        autoPlayBtn.textContent = 'Stop';
        const delay = parseInt(autoPlaySpeedSlider.value, 10);
        autoPlayInterval = setInterval(async () => {
            // Check if game is still running before fetching
            if (currentGameState.game_phase === 'FINISHED') {
                 stopAutoPlay();
                 return;
            }
            const response = await fetch('/api/game/next_turn', { method: 'POST' });
            const gameState = await response.json();
            updateStateAndRender(gameState);
            if (gameState.game_phase === 'FINISHED') {
                stopAutoPlay();
            }
        }, delay);
    }

    autoPlayBtn.addEventListener('click', () => {
        if (autoPlayInterval) {
            stopAutoPlay();
        } else {
            startAutoPlay();
        }
    });

    autoPlaySpeedSlider.addEventListener('input', () => {
        const delay = autoPlaySpeedSlider.value;
        speedValueSpan.textContent = `${delay}ms`;
        // If auto-play is already running, restart it with the new speed
        if (autoPlayInterval) {
            startAutoPlay();
        }
    });

    resetBtn.addEventListener('click', () => {
        stopAutoPlay();
        // Easiest way to reset everything is to just reload the page.
        // The server will re-initialize the game state on the '/' route.
        window.location.reload();
    });

    // --- Initialization and Update Checker ---

    function checkForUpdates() {
        setInterval(async () => {
            try {
                const response = await fetch('/api/check_updates');
                const data = await response.json();
                if (data.updated) {
                    alert(data.message);
                    // Stop any running game loops
                    stopAutoPlay();
                }
            } catch (error) {
                console.error('Update check failed:', error);
                // Could mean server is down for restart
                stopAutoPlay();
            }
        }, 5000); // Check every 5 seconds
    }

    async function init() {
        const response = await fetch('/api/game/state');
        const gameState = await response.json();
        currentGameState = gameState; // Initial cache
        
        // If page is refreshed during setup, reconstruct state to allow editing
        if (gameState.game_phase === 'SETUP') {
             localTeams = gameState.teams || {};
             initialPoints = Object.values(gameState.points);
        } else {
             localTeams = gameState.teams || {};
             initialPoints = [];
        }
        
        gridSizeInput.value = gameState.grid_size;
        maxTurnsInput.value = gameState.max_turns;
        updateStateAndRender(gameState);
        renderTeamsList();
        checkForUpdates();
        animationLoop(); // Start the animation loop
    }

    init();
});