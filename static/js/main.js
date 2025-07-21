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
    let isDebugMode = false;
    let currentGameState = {}; // Cache the latest game state
    let visualEffects = []; // For temporary animations

    // UI Elements
    const teamsList = document.getElementById('teams-list');
    const newTeamNameInput = document.getElementById('new-team-name');
    const newTeamColorInput = document.getElementById('new-team-color');
    const addTeamBtn = document.getElementById('add-team-btn');
    const startGameBtn = document.getElementById('start-game-btn');
    const nextTurnBtn = document.getElementById('next-turn-btn');
    const autoPlayBtn = document.getElementById('auto-play-btn');
    const resetBtn = document.getElementById('reset-btn');
    const undoPointBtn = document.getElementById('undo-point-btn');
    const randomizePointsBtn = document.getElementById('randomize-points-btn');
    const maxTurnsInput = document.getElementById('max-turns');
    const gridSizeInput = document.getElementById('grid-size');
    const statsDiv = document.getElementById('stats');
    const logDiv = document.getElementById('log');
    const turnCounter = document.getElementById('turn-counter');
    const debugToggle = document.getElementById('debug-mode-toggle');

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
                ctx.fillStyle = team.color;
                ctx.beginPath();
                ctx.arc((p.x + 0.5) * cellSize, (p.y + 0.5) * cellSize, 5, 0, 2 * Math.PI);
                ctx.fill();

                if (isDebugMode) {
                    ctx.fillStyle = '#000';
                    ctx.font = '10px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'bottom';
                    // Display the point's unique ID
                    ctx.fillText(p.id, (p.x + 0.5) * cellSize, (p.y + 0.5) * cellSize - 7);
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
                    ctx.strokeStyle = team.color;
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo((p1.x + 0.5) * cellSize, (p1.y + 0.5) * cellSize);
                    ctx.lineTo((p2.x + 0.5) * cellSize, (p2.y + 0.5) * cellSize);
                    ctx.stroke();
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

        if (details.type === 'nova_burst' && details.sacrificed_point) {
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
            visualEffects.push({
                type: 'new_line',
                line: details.line,
                startTime: Date.now(),
                duration: 500 // ms
            });
        }
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
        const inSetupPhase = !document.getElementById('action-phase') || document.getElementById('action-phase').style.display === 'none';

        for (const teamId in localTeams) {
            const team = localTeams[teamId];
            const li = document.createElement('li');
            li.dataset.teamId = teamId;

            if (selectedTeamId === teamId) {
                li.classList.add('selected');
            }

            const colorBox = document.createElement('div');
            colorBox.className = 'team-color-box';
            colorBox.style.backgroundColor = team.color;
            li.appendChild(colorBox);

            const teamName = document.createElement('span');
            teamName.textContent = team.name;
            li.appendChild(teamName);

            li.addEventListener('click', () => {
                // Allow selecting teams only during setup
                if (inSetupPhase) {
                    selectedTeamId = teamId;
                    renderTeamsList();
                }
            });

            teamsList.appendChild(li);
        }
    }

    function updateLog(log, teams) {
        logDiv.innerHTML = ''; // Clear previous logs
        if (!log) return;
        log.forEach(entry => {
            const logEntryDiv = document.createElement('div');
            logEntryDiv.className = 'log-entry';
            logEntryDiv.textContent = entry.message;
            if (entry.teamId && teams[entry.teamId]) {
                logEntryDiv.style.borderLeftColor = teams[entry.teamId].color;
            }
            logDiv.appendChild(logEntryDiv);
        });
        logDiv.scrollTop = logDiv.scrollHeight;
    }

    function updateInterpretationPanel(gameState) {
        const { turn, max_turns, teams, points, lines, is_finished, interpretation } = gameState;
    
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
        const finalInterpDiv = document.getElementById('final-interpretation');
        if (is_finished && interpretation && Object.keys(interpretation).length > 0) {
            let finalStatsHTML = '<table><tr><th>Team</th><th>Stat</th><th>Value</th></tr>';
            for (const teamId in interpretation) {
                const teamData = interpretation[teamId];
                if (!teams[teamId]) continue; // Skip if team data is missing
                const teamName = teams[teamId].name;
                const teamColor = teams[teamId].color;
                
                // Add Divination Text
                let divinationRow = `<td colspan="2" style="font-style: italic; background-color: #f8f9fa;">"${teamData.divination_text}"</td>`;

                const allStatRows = [
                    ['Points', teamData.point_count],
                    ['Lines', teamData.line_count],
                    ['Line Length', teamData.line_length],
                    ['Triangles', teamData.triangles],
                    ['Territory Area', teamData.controlled_area],
                    ['Hull Area', teamData.hull_area],
                    ['Hull Perimeter', teamData.hull_perimeter]
                ];

                // Filter out stats with a value of 0 or undefined
                const statRows = allStatRows.filter(row => row[1] > 0);
                
                const totalRows = statRows.length + (teamData.divination_text ? 1 : 0);

                if (totalRows > 0) {
                    finalStatsHTML += `<tr><td rowspan="${totalRows}" style="font-weight:bold; color:${teamColor};">${teamName}</td>`;

                    if (statRows.length > 0) {
                         finalStatsHTML += `<td>${statRows[0][0]}</td><td>${statRows[0][1]}</td></tr>`;
                        for(let i = 1; i < statRows.length; i++) {
                            finalStatsHTML += `<tr><td>${statRows[i][0]}</td><td>${statRows[i][1]}</td></tr>`;
                        }
                        if (teamData.divination_text) {
                            finalStatsHTML += `<tr>${divinationRow}</tr>`;
                        }
                    } else if (teamData.divination_text) {
                        finalStatsHTML += `${divinationRow}</tr>`;
                    }
                }
            }
            finalStatsHTML += '</table>';
            document.getElementById('final-stats-content').innerHTML = finalStatsHTML;
            finalInterpDiv.style.display = 'block';
        } else {
            finalInterpDiv.style.display = 'none';
        }
    }

    function updateControls(gameState) {
        const inSetupPhase = !gameState.is_running && !gameState.is_finished;
        document.getElementById('setup-phase').style.display = inSetupPhase ? 'block' : 'none';
        document.getElementById('action-phase').style.display = !inSetupPhase ? 'block' : 'none';
        
        nextTurnBtn.disabled = gameState.is_finished;
        autoPlayBtn.disabled = gameState.is_finished;

        if (gameState.is_finished) {
            stopAutoPlay();
            autoPlayBtn.textContent = 'Auto-Play';
        }
    }

    // --- Event Handlers & API Calls ---

    debugToggle.addEventListener('click', () => {
        isDebugMode = debugToggle.checked;
        // The animation loop will pick up the change, no need to force render
    });

    addTeamBtn.addEventListener('click', () => {
        const teamName = newTeamNameInput.value.trim();
        if (teamName && !Object.values(localTeams).some(t => t.name === teamName)) {
            const teamId = `team-${Object.keys(localTeams).length + 1}`;
            localTeams[teamId] = {
                name: teamName,
                color: newTeamColorInput.value
            };
            newTeamNameInput.value = '';
            renderTeamsList();
            if(!selectedTeamId) {
                selectedTeamId = teamId;
                renderTeamsList();
            }
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
        if (!selectedTeamId) {
            alert('Please add and select a team first!');
            return;
        }
        // Allow adding points only during setup phase
        if (autoPlayInterval || document.getElementById('action-phase').style.display === 'block') {
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

    autoPlayBtn.addEventListener('click', () => {
        if (autoPlayInterval) {
            stopAutoPlay();
        } else {
            autoPlayBtn.textContent = 'Stop';
            autoPlayInterval = setInterval(async () => {
                const response = await fetch('/api/game/next_turn', { method: 'POST' });
                const gameState = await response.json();
                updateStateAndRender(gameState);
                if (gameState.is_finished) {
                    stopAutoPlay();
                }
            }, 500); // 500ms delay between turns
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
        // Set local state based on potentially ongoing game
        if (gameState && gameState.teams && Object.keys(gameState.teams).length > 0) {
            localTeams = gameState.teams;
            if (!gameState.is_running && !gameState.is_finished) {
                // If game hasn't started, reconstruct initialPoints for editing
                initialPoints = Object.values(gameState.points);
            }
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