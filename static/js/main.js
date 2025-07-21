document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('grid');
    const ctx = canvas.getContext('2d');
    const gridSize = 10; // This should match the backend grid size
    let cellSize = canvas.width / gridSize;

    // Game state - The single source of truth will be the backend
    let localTeams = {};
    let initialPoints = [];
    let selectedTeamId = null;
    let autoPlayInterval = null;

    // UI Elements
    const teamsList = document.getElementById('teams-list');
    const newTeamNameInput = document.getElementById('new-team-name');
    const newTeamColorInput = document.getElementById('new-team-color');
    const addTeamBtn = document.getElementById('add-team-btn');
    const startGameBtn = document.getElementById('start-game-btn');
    const nextTurnBtn = document.getElementById('next-turn-btn');
    const autoPlayBtn = document.getElementById('auto-play-btn');
    const resetBtn = document.getElementById('reset-btn');
    const maxTurnsInput = document.getElementById('max-turns');
    const statsDiv = document.getElementById('stats');
    const logDiv = document.getElementById('log');
    const turnCounter = document.getElementById('turn-counter');

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

    function drawPoints(points, teams) {
        points.forEach(p => {
            const team = teams[p.teamId];
            if (team) {
                ctx.fillStyle = team.color;
                ctx.beginPath();
                ctx.arc((p.x + 0.5) * cellSize, (p.y + 0.5) * cellSize, 5, 0, 2 * Math.PI);
                ctx.fill();
            }
        });
    }

    function drawLines(points, lines, teams) {
        lines.forEach(line => {
            const team = teams[line.teamId];
            if (team) {
                const p1 = points[line.p1_idx];
                const p2 = points[line.p2_idx];
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

    function render(gameState) {
        drawGrid();
        if (!gameState || !gameState.teams) return;

        // Update UI elements based on game state
        cellSize = canvas.width / gameState.grid_size;
        drawLines(gameState.points, gameState.lines, gameState.teams);
        drawPoints(gameState.points, gameState.teams);
        updateLog(gameState.game_log);
        updateStats(gameState);
        updateControls(gameState);
    }

    // --- UI Update Functions ---

    function renderTeamsList() {
        teamsList.innerHTML = '';
        for (const teamId in localTeams) {
            const team = localTeams[teamId];
            const li = document.createElement('li');
            li.style.cursor = 'pointer';
            li.dataset.teamId = teamId;

            const colorBox = document.createElement('div');
            colorBox.className = 'team-color-box';
            colorBox.style.backgroundColor = team.color;
            li.appendChild(colorBox);

            const teamName = document.createElement('span');
            teamName.textContent = team.name;
            li.appendChild(teamName);

            if (selectedTeamId === teamId) {
                li.style.fontWeight = 'bold';
                li.style.border = '1px solid #000';
            }

            li.addEventListener('click', () => {
                selectedTeamId = teamId;
                renderTeamsList();
            });

            teamsList.appendChild(li);
        }
    }

    function updateLog(log) {
        logDiv.innerHTML = log.join('<br>');
        logDiv.scrollTop = logDiv.scrollHeight;
    }

    function updateStats(gameState) {
        turnCounter.textContent = `Turn: ${gameState.turn} / ${gameState.max_turns}`;
        let statsHTML = '<h4>Team Stats</h4>';
        for (const teamId in gameState.teams) {
            const team = gameState.teams[teamId];
            const pointCount = gameState.points.filter(p => p.teamId === teamId).length;
            const lineCount = gameState.lines.filter(l => l.teamId === teamId).length;
            statsHTML += `<div><strong style="color:${team.color};">${team.name}</strong>: ${pointCount} points, ${lineCount} lines</div>`;
        }
        statsDiv.innerHTML = statsHTML;
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
            drawPoints(initialPoints, localTeams);
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
            maxTurns: maxTurnsInput.value
        };
        const response = await fetch('/api/game/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const gameState = await response.json();
        render(gameState);
    });

    nextTurnBtn.addEventListener('click', async () => {
        const response = await fetch('/api/game/next_turn', { method: 'POST' });
        const gameState = await response.json();
        render(gameState);
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
                render(gameState);
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
        cellSize = canvas.width / gameState.grid_size;
        render(gameState);
        renderTeamsList();
        checkForUpdates();
    }

    init();
});