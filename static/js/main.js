document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('grid');
    const ctx = canvas.getContext('2d');
    const gridSize = 10;
    const cellSize = canvas.width / gridSize;

    // Game state
    let teams = {};
    let points = [];
    let lines = [];
    let selectedTeam = null;

    // UI Elements
    const teamsList = document.getElementById('teams-list');
    const newTeamNameInput = document.getElementById('new-team-name');
    const newTeamColorInput = document.getElementById('new-team-color');
    const addTeamBtn = document.getElementById('add-team-btn');
    const nextTurnBtn = document.getElementById('next-turn-btn');
    const autoPlayBtn = document.getElementById('auto-play-btn');
    const resetBtn = document.getElementById('reset-btn');
    const maxTurnsInput = document.getElementById('max-turns');
    const statsDiv = document.getElementById('stats');
    const logDiv = document.getElementById('log');

    function drawGrid() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = '#ccc';
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

    function renderTeams() {
        teamsList.innerHTML = '';
        for (const teamId in teams) {
            const team = teams[teamId];
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

            if (selectedTeam === teamId) {
                li.style.fontWeight = 'bold';
            }

            li.addEventListener('click', () => {
                selectedTeam = teamId;
                renderTeams();
            });

            teamsList.appendChild(li);
        }
    }

    addTeamBtn.addEventListener('click', () => {
        const teamName = newTeamNameInput.value.trim();
        if (teamName) {
            const teamId = `team-${Object.keys(teams).length + 1}`;
            teams[teamId] = {
                name: teamName,
                color: newTeamColorInput.value
            };
            newTeamNameInput.value = '';
            renderTeams();
        }
    });

    canvas.addEventListener('click', (e) => {
        if (!selectedTeam) {
            alert('Please select a team first!');
            return;
        }
        const rect = canvas.getBoundingClientRect();
        const x = Math.floor((e.clientX - rect.left) / cellSize);
        const y = Math.floor((e.clientY - rect.top) / cellSize);

        points.push({ x, y, teamId: selectedTeam });
        drawPoints();
    });

    function drawPoints() {
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

    function init() {
        drawGrid();
        renderTeams();
    }

    init();
});