document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('grid');
    const ctx = canvas.getContext('2d');
    let gridSize = 10; // This will be updated from backend state
    let cellSize = canvas.width / gridSize;

    // Game state - The single source of truth will be the backend
    let localTeams = {};
    let initialPoints = []; // Still a list for setup phase
    let selectedTeamId = null;
    let autoPlayInterval = null;
    let debugOptions = {
        showPointIds: false,
        showLineIds: false,
        highlightLastAction: false,
        showHulls: false,
        compactLog: false
    };
    let currentGameState = {}; // Cache the latest game state
    let hasResizedInitially = false;
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
    const compactLogToggle = document.getElementById('compact-log-toggle'); // New element

    // Debug Toggles
    const debugPointIdsToggle = document.getElementById('debug-point-ids');
    const debugLineIdsToggle = document.getElementById('debug-line-ids');
    const debugLastActionToggle = document.getElementById('debug-last-action');
    const showHullsToggle = document.getElementById('show-hulls-toggle');
    const finalAnalysisOptions = document.getElementById('final-analysis-options');

    // --- Core Functions ---

    function drawGrid() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = '#e0e0e0';
        gridSize = currentGameState.grid_size || 10;
        cellSize = canvas.width / gridSize;
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
                let radius = 5;

                // Highlight effect for last action
                if (debugOptions.highlightLastAction && lastActionHighlights.points.has(p.id)) {
                    ctx.fillStyle = 'rgba(255, 255, 0, 0.8)';
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius + 5, 0, 2 * Math.PI);
                    ctx.fill();
                }

                // Anchor point visualization (drawn on top of highlight, below main point)
                if (p.is_anchor) {
                    radius = 7;
                    // Pulsing effect for anchor
                    const pulse_rate = 1500; // ms for one pulse cycle
                    const pulse = Math.abs(Math.sin(Date.now() / pulse_rate));
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius + 4 + (pulse * 4), 0, 2 * Math.PI);
                    ctx.strokeStyle = `rgba(200, 200, 255, ${0.7 - (pulse * 0.5)})`;
                    ctx.lineWidth = 3;
                    ctx.stroke();
                }

                // Main point drawing
                ctx.fillStyle = team.color;
                ctx.beginPath();
                if (p.is_fortified) {
                    // Draw fortified points as diamonds
                    const size = radius * 1.7;
                    ctx.moveTo(cx, cy - size); // Top
                    ctx.lineTo(cx + size, cy); // Right
                    ctx.lineTo(cx, cy + size); // Bottom
                    ctx.lineTo(cx - size, cy); // Left
                    ctx.closePath();
                } else if (p.is_anchor) {
                    // Draw anchors as squares
                    const squareSize = radius * 1.8;
                    ctx.rect(cx - squareSize / 2, cy - squareSize / 2, squareSize, squareSize);
                } else {
                    // Draw normal points as circles
                    ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
                }
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

    function drawHulls(interpretation, teams) {
        if (!interpretation || !debugOptions.showHulls) return;

        Object.values(teams).forEach(team => {
            const teamInterp = interpretation[team.id];
            if (teamInterp && teamInterp.hull_points && teamInterp.hull_points.length >= 2) {
                const hullPoints = teamInterp.hull_points;
                ctx.beginPath();
                const startPoint = hullPoints[0];
                ctx.moveTo((startPoint.x + 0.5) * cellSize, (startPoint.y + 0.5) * cellSize);

                for (let i = 1; i < hullPoints.length; i++) {
                    const p = hullPoints[i];
                    ctx.lineTo((p.x + 0.5) * cellSize, (p.y + 0.5) * cellSize);
                }
                
                // Close the hull
                if (hullPoints.length > 2) {
                    ctx.closePath();
                }

                ctx.strokeStyle = team.color;
                ctx.lineWidth = 3;
                ctx.setLineDash([5, 5]); // Dashed line for hull
                ctx.stroke();
                ctx.setLineDash([]); // Reset line dash
            }
        });
    }

    function drawTerritories(pointsDict, territories, teams) {
        if (!pointsDict || !territories) return;
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

    function drawRunes(gameState) {
        if (!gameState.runes) return;
    
        for (const teamId in gameState.runes) {
            const teamRunes = gameState.runes[teamId];
            const team = gameState.teams[teamId];
            if (!team) continue;
    
            // Draw V-Runes
            if (teamRunes.v_shape) {
                teamRunes.v_shape.forEach(rune => {
                    const p_v = gameState.points[rune.vertex_id];
                    const p_l1 = gameState.points[rune.leg1_id];
                    const p_l2 = gameState.points[rune.leg2_id];
                    if (!p_v || !p_l1 || !p_l2) return;
    
                    ctx.beginPath();
                    ctx.moveTo((p_l1.x + 0.5) * cellSize, (p_l1.y + 0.5) * cellSize);
                    ctx.lineTo((p_v.x + 0.5) * cellSize, (p_v.y + 0.5) * cellSize);
                    ctx.lineTo((p_l2.x + 0.5) * cellSize, (p_l2.y + 0.5) * cellSize);
                    ctx.strokeStyle = team.color;
                    ctx.lineWidth = 6;
                    ctx.globalAlpha = 0.4;
                    ctx.stroke();
                    ctx.globalAlpha = 1.0;
                });
            }
    
            // Draw Cross-Runes
            if (teamRunes.cross) {
                teamRunes.cross.forEach(rune_p_ids => {
                    const points = rune_p_ids.map(pid => gameState.points[pid]).filter(p => p);
                    if (points.length !== 4) return;
                    
                    // Sort points angularly around their centroid to draw the polygon correctly
                    const centroid = {
                        x: points.reduce((acc, p) => acc + p.x, 0) / 4,
                        y: points.reduce((acc, p) => acc + p.y, 0) / 4,
                    };
                    points.sort((a, b) => {
                        return Math.atan2(a.y - centroid.y, a.x - centroid.x) - Math.atan2(b.y - centroid.y, b.x - centroid.x);
                    });
    
                    ctx.beginPath();
                    ctx.moveTo((points[0].x + 0.5) * cellSize, (points[0].y + 0.5) * cellSize);
                    for (let i = 1; i < points.length; i++) {
                         ctx.lineTo((points[i].x + 0.5) * cellSize, (points[i].y + 0.5) * cellSize);
                    }
                    ctx.closePath();
                    ctx.fillStyle = team.color;
                    ctx.globalAlpha = 0.2;
                    ctx.fill();
                    ctx.globalAlpha = 1.0;
                });
            }
        }
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
                ctx.strokeStyle = effect.color || `rgba(255, 0, 0, ${1 - progress})`; // Red, fading out
                ctx.lineWidth = effect.lineWidth || 3;
                ctx.stroke();
            } else if (effect.type === 'mirror_axis') {
                const p1 = currentGameState.points[effect.p1_id];
                const p2 = currentGameState.points[effect.p2_id];
                if(p1 && p2) {
                    ctx.save();
                    ctx.beginPath();
                    ctx.moveTo((p1.x + 0.5) * cellSize, (p1.y + 0.5) * cellSize);
                    ctx.lineTo((p2.x + 0.5) * cellSize, (p2.y + 0.5) * cellSize);
                    ctx.strokeStyle = `rgba(200, 200, 255, ${0.7 * (1 - progress)})`; // Light blue, fading
                    ctx.lineWidth = 2;
                    ctx.setLineDash([5, 5]);
                    ctx.stroke();
                    ctx.restore();
                }
            }
            
            return true; // Keep active effects
        });
    }

    function fullRender() {
        if (!currentGameState) return;

        // Central drawing function, called every frame by animationLoop
        drawGrid();

        if (currentGameState.game_phase === 'SETUP') {
             // During setup, draw the temporary points from the local array
             const tempPointsDict = {};
             initialPoints.forEach((p, i) => tempPointsDict[`p_${i}`] = {...p, id: `p_${i}`});
             drawPoints(tempPointsDict, localTeams); // Use localTeams for colors
        } else {
            // During RUNNING or FINISHED, draw from the official game state
            if (currentGameState.teams) {
                drawTerritories(currentGameState.points, currentGameState.territories, currentGameState.teams);
                drawRunes(currentGameState);
                drawLines(currentGameState.points, currentGameState.lines, currentGameState.teams);
                drawPoints(currentGameState.points, currentGameState.teams);
                
                // Draw hulls if game is finished and toggled on
                if (currentGameState.game_phase === 'FINISHED') {
                    drawHulls(currentGameState.interpretation, currentGameState.teams);
                }
            }
        }

        drawVisualEffects();
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
        if (details.type === 'fracture_line' && details.new_point) {
            lastActionHighlights.points.add(details.new_point.id);
            lastActionHighlights.lines.add(details.new_line1.id);
            lastActionHighlights.lines.add(details.new_line2.id);
        }
        if (details.type === 'convert_point' && details.converted_point) {
            lastActionHighlights.points.add(details.converted_point.id);
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
                duration: 600, // ms
                color: details.bypassed_shield ? `rgba(255, 100, 255, ${1 - 0})` : `rgba(255, 0, 0, ${1 - 0})` // Magenta if shield bypass
            });
        }
        if (details.type === 'rune_shoot_bisector' && details.attack_ray) {
            details.rune_points.forEach(pid => lastActionHighlights.points.add(pid));
            visualEffects.push({
                type: 'attack_ray',
                p1: details.attack_ray.p1,
                p2: details.attack_ray.p2,
                startTime: Date.now(),
                duration: 800,
                color: `rgba(100, 255, 255, ${1-0})`, // Cyan for rune attack
                lineWidth: 4,
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
        if (details.type === 'create_anchor' && details.anchor_point) {
            lastActionHighlights.points.add(details.anchor_point.id);
        }
        if (details.type === 'mirror_structure' && details.new_points) {
            details.new_points.forEach(p => lastActionHighlights.points.add(p.id));
            lastActionHighlights.points.add(details.axis_p1_id);
            lastActionHighlights.points.add(details.axis_p2_id);
            visualEffects.push({
                type: 'mirror_axis',
                p1_id: details.axis_p1_id,
                p2_id: details.axis_p2_id,
                startTime: Date.now(),
                duration: 1500 // ms
            });
        }
        if (details.type === 'create_orbital' && details.new_points) {
            lastActionHighlights.points.add(details.center_point_id);
            details.new_points.forEach(p => lastActionHighlights.points.add(p.id));
            details.new_lines.forEach(l => lastActionHighlights.lines.add(l.id));
        }

        // Set a timer to clear the highlights
        lastActionHighlights.clearTimeout = setTimeout(() => {
            lastActionHighlights.points.clear();
            lastActionHighlights.lines.clear();
        }, 2000); // Highlight for 2 seconds
    }

    function updateStateAndRender(gameState) {
        if (!gameState || !gameState.teams) return;
        
        const isFirstUpdate = !currentGameState.game_phase;
        currentGameState = gameState; // Cache state
        
        if (isFirstUpdate) {
            // After the first state load, ensure the teams list and controls are correctly rendered
            renderTeamsList();
        }

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
        const teamsToRender = inSetupPhase ? localTeams : currentGameState.teams;

        for (const teamId in teamsToRender) {
            const team = teamsToRender[teamId];
            const li = document.createElement('li');
            li.dataset.teamId = teamId;

            if (selectedTeamId === teamId && inSetupPhase) {
                li.classList.add('selected');
            }

            if (inSetupPhase && team.isEditing) {
                // --- EDITING MODE ---
                const editControls = document.createElement('div');
                editControls.className = 'team-edit-controls';

                const colorInput = document.createElement('input');
                colorInput.type = 'color';
                colorInput.value = team.color;

                const nameInput = document.createElement('input');
                nameInput.type = 'text';
                nameInput.value = team.name;

                const saveBtn = document.createElement('button');
                saveBtn.textContent = 'Save';
                saveBtn.onclick = () => {
                    const newName = nameInput.value.trim();
                    if (newName) {
                        localTeams[teamId].name = newName;
                        localTeams[teamId].color = colorInput.value;
                        localTeams[teamId].isEditing = false;
                        renderTeamsList();
                        // No need to call redraw, animation loop will handle it
                    }
                };
                
                const cancelBtn = document.createElement('button');
                cancelBtn.textContent = 'Cancel';
                cancelBtn.onclick = () => {
                    localTeams[teamId].isEditing = false;
                    renderTeamsList();
                };

                editControls.append(colorInput, nameInput, saveBtn, cancelBtn);
                li.appendChild(editControls);

            } else {
                // --- NORMAL DISPLAY MODE ---
                const colorBox = document.createElement('div');
                colorBox.className = 'team-color-box';
                colorBox.style.backgroundColor = team.color;
                li.appendChild(colorBox);

                const teamInfo = document.createElement('div');
                teamInfo.className = 'team-info';
                teamInfo.onclick = () => { // Make the info part clickable for selection
                    if (inSetupPhase) {
                        selectedTeamId = teamId;
                        renderTeamsList();
                    }
                };
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
                    const actionsDiv = document.createElement('div');
                    actionsDiv.className = 'team-actions';

                    const editBtn = document.createElement('button');
                    editBtn.innerHTML = '&#9998;'; // Pencil icon
                    editBtn.title = 'Edit team';
                    editBtn.onclick = () => {
                        // Set editing flag on the specific team and re-render
                        Object.values(localTeams).forEach(t => t.isEditing = false); // Ensure only one is edited at a time
                        localTeams[teamId].isEditing = true;
                        renderTeamsList();
                    };

                    const deleteBtn = document.createElement('button');
                    deleteBtn.innerHTML = '&times;'; // Cross icon
                    deleteBtn.title = 'Delete team';
                    deleteBtn.className = 'delete-team-btn';
                    deleteBtn.dataset.teamId = teamId; // Keep this for the main listener

                    actionsDiv.append(editBtn, deleteBtn);
                    li.appendChild(actionsDiv);
                }
            }
            teamsList.appendChild(li);
        }
    }

    function updateLog(log, teams) {
        logDiv.innerHTML = ''; // Clear previous logs
        if (!log) return;

        let lastMessage = 'Game log is empty.';
        // Find the last message from a team for the status bar
        for(let i = log.length - 1; i >= 0; i--) {
            if (log[i].teamId) {
                lastMessage = log[i].message;
                break;
            }
        }

        log.forEach(entry => {
            const logEntryDiv = document.createElement('div');
            logEntryDiv.className = 'log-entry';

            const message = (debugOptions.compactLog && entry.short_message) ? entry.short_message : entry.message;
            logEntryDiv.textContent = message;

            if (entry.teamId && teams[entry.teamId]) {
                logEntryDiv.style.borderLeftColor = teams[entry.teamId].color;
                if (debugOptions.compactLog) {
                    // In compact mode, add team color to text for visibility
                    logEntryDiv.style.color = teams[entry.teamId].color;
                    logEntryDiv.style.fontWeight = 'bold';
                }
            } else { // Non-team messages (Turn counter, etc)
                 logEntryDiv.style.textAlign = 'center';
                 logEntryDiv.style.borderLeftColor = '#ccc';
                 logEntryDiv.style.background = '#f0f0f0';
                 if (debugOptions.compactLog) {
                     logEntryDiv.style.fontWeight = 'bold';
                 }
            }
            logDiv.prepend(logEntryDiv); // Prepend to put new entries on top
        });
        logDiv.scrollTop = 0; // Scroll to top to see latest entries

        // Update status bar
        if (currentGameState.game_phase === 'RUNNING') {
            statusBar.textContent = lastMessage;
            statusBar.style.opacity = '1';
        } else {
            statusBar.style.opacity = '0';
        }
    }

    function updateInterpretationPanel(gameState) {
        const { turn, max_turns, teams, game_phase, interpretation, victory_condition, live_stats, action_in_turn, active_teams_this_turn, runes } = gameState;

        let turnText = `Turn: ${turn} / ${max_turns}`;
        if (game_phase === 'RUNNING' && active_teams_this_turn && active_teams_this_turn.length > 0) {
            turnText += ` (Action ${action_in_turn} / ${active_teams_this_turn.length})`;
        }
        turnCounter.textContent = turnText;

        // Live stats
        let statsHTML = '<h4>Live Stats</h4>';
        if (teams && Object.keys(teams).length > 0 && live_stats) {
             for (const teamId in teams) {
                const team = teams[teamId];
                const stats = live_stats[teamId];
                if (stats) {
                    let teamHTML = `<div style="margin-bottom: 5px;">
                        <strong style="color:${team.color};">${team.name}</strong>: 
                        ${stats.point_count} pts, 
                        ${stats.line_count} lines,
                        ${stats.controlled_area} area`;
                    
                    const teamRunes = runes[teamId] || {};
                    const crossRunesCount = teamRunes.cross ? teamRunes.cross.length : 0;
                    const vRunesCount = teamRunes.v_shape ? teamRunes.v_shape.length : 0;
                    if (crossRunesCount > 0 || vRunesCount > 0) {
                        let runeStrings = [];
                        if (crossRunesCount > 0) runeStrings.push(`Cross (${crossRunesCount})`);
                        if (vRunesCount > 0) runeStrings.push(`V-Shape (${vRunesCount})`);
                        teamHTML += `<br/><span style="font-size: 0.9em; padding-left: 10px;">Runes: ${runeStrings.join(', ')}</span>`;
                    }

                    teamHTML += `</div>`;
                    statsHTML += teamHTML;
                }
            }
        } else {
            statsHTML += '<p>No teams yet.</p>';
        }
        statsDiv.innerHTML = statsHTML;
    
        // Final interpretation
        if (game_phase === 'FINISHED' && interpretation) {
            finalInterpContent.innerHTML = ''; // Clear previous content
            finalAnalysisOptions.style.display = 'block';

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
            finalAnalysisOptions.style.display = 'none';
        }
    }

    function updateControls(gameState) {
        const gamePhase = gameState.game_phase;
        const inSetup = gamePhase === 'SETUP';
        const isRunning = gamePhase === 'RUNNING';
        const isFinished = gamePhase === 'FINISHED';

        document.getElementById('setup-phase').style.display = inSetup ? 'block' : 'none';
        document.getElementById('simulation-controls').style.display = inSetup ? 'none' : 'block';
        
        // Only show live controls (next, auto-play) when the simulation is actually running
        const liveControls = document.getElementById('live-controls');
        liveControls.style.display = isRunning ? 'block' : 'none';

        // Restart button is available when running or finished
        restartSimulationBtn.style.display = isRunning || isFinished ? 'block' : 'none';

        if (isFinished) {
            if (autoPlayInterval) stopAutoPlay();
            autoPlayBtn.textContent = 'Auto-Play';
        }
    }

    // --- Event Handlers & API Calls ---

    compactLogToggle.addEventListener('click', () => {
        debugOptions.compactLog = compactLogToggle.checked;
        // We need to re-render the log with the new setting
        updateLog(currentGameState.game_log, currentGameState.teams);
    });

    debugPointIdsToggle.addEventListener('click', () => {
        debugOptions.showPointIds = debugPointIdsToggle.checked;
    });
    debugLineIdsToggle.addEventListener('click', () => {
        debugOptions.showLineIds = debugLineIdsToggle.checked;
    });
    debugLastActionToggle.addEventListener('click', () => {
        debugOptions.highlightLastAction = debugLastActionToggle.checked;
    });
    showHullsToggle.addEventListener('click', () => {
        debugOptions.showHulls = showHullsToggle.checked;
    });

    // Listener for team list - now only for deletion (selection and editing are handled on elements)
    teamsList.addEventListener('click', (e) => {
        if (currentGameState.game_phase !== 'SETUP') return;

        // Handle team deletion
        const deleteButton = e.target.closest('.delete-team-btn');
        if (deleteButton) {
            const teamId = deleteButton.dataset.teamId;
            const teamName = localTeams[teamId]?.name || 'this team';
            if (!confirm(`Are you sure you want to remove ${teamName}? This will also delete its points.`)) return;

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
            
            // Re-render teams list. Grid will update via animation loop.
            renderTeamsList();
        }
    });

    addTeamBtn.addEventListener('click', () => {
        const teamName = newTeamNameInput.value.trim();
        const trait = newTeamTraitSelect.value;
        if (teamName && !Object.values(localTeams).some(t => t.name === teamName)) {
            const teamId = `team-${Date.now()}`; // More unique ID
            
            localTeams[teamId] = {
                id: teamId, // Add id property to the object itself
                name: teamName,
                color: newTeamColorInput.value,
                trait: trait,
                isEditing: false
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
            // Grid updates via animation loop
        }
    });

    clearPointsBtn.addEventListener('click', () => {
        if (initialPoints.length > 0) {
            if (confirm("Are you sure you want to clear all points from the grid?")) {
                initialPoints = [];
                // Grid updates via animation loop
            }
        }
    });

    randomizePointsBtn.addEventListener('click', () => {
        if (Object.keys(localTeams).length === 0) {
            alert("Please add at least one team before randomizing points.");
            return;
        }

        if (initialPoints.length > 0) {
            if (!confirm("This will replace all existing points on the grid with new random ones. Are you sure?")) {
                return;
            }
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
        // Grid updates via animation loop
    });

    function findPointAtCoord(x, y) {
        // Find the index of the point in the initialPoints array
        return initialPoints.findIndex(p => p.x === x && p.y === y);
    }

    canvas.addEventListener('mousemove', (e) => {
        if (currentGameState.game_phase !== 'SETUP') {
            if (canvas.style.cursor !== 'default') canvas.style.cursor = 'default';
            return;
        }
        const rect = canvas.getBoundingClientRect();
        const x = Math.floor((e.clientX - rect.left) / cellSize);
        const y = Math.floor((e.clientY - rect.top) / cellSize);

        if (findPointAtCoord(x, y) !== -1) {
            if (canvas.style.cursor !== 'pointer') canvas.style.cursor = 'pointer';
        } else {
            if (canvas.style.cursor !== 'crosshair') canvas.style.cursor = 'crosshair';
        }
    });

    canvas.addEventListener('click', (e) => {
        if (currentGameState.game_phase !== 'SETUP') {
            return;
        }

        const rect = canvas.getBoundingClientRect();
        const x = Math.floor((e.clientX - rect.left) / cellSize);
        const y = Math.floor((e.clientY - rect.top) / cellSize);

        const pointIndex = findPointAtCoord(x, y);

        if (pointIndex !== -1) {
            // Point exists, so remove it
            initialPoints.splice(pointIndex, 1);
        } else {
            // Point does not exist, add a new one
            if (!selectedTeamId) {
                alert('Please add and select a team first!');
                return;
            }
            initialPoints.push({ x, y, teamId: selectedTeamId });
        }
        
        // Grid will update on the next frame via animation loop.
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

    restartSimulationBtn.addEventListener('click', async () => {
        if (!confirm("This will restart the simulation from the beginning with the same setup. Continue?")) {
            return;
        }
        stopAutoPlay();
        const response = await fetch('/api/game/restart', { method: 'POST' });
        if (response.ok) {
            const gameState = await response.json();
            updateStateAndRender(gameState);
        } else {
            const error = await response.json();
            alert(`Could not restart game: ${error.message || 'Unknown error'}`);
        }
    });

    nextActionBtn.addEventListener('click', async () => {
        const response = await fetch('/api/game/next_action', { method: 'POST' });
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
            if (currentGameState.game_phase !== 'RUNNING') {
                 stopAutoPlay();
                 return;
            }
            const response = await fetch('/api/game/next_action', { method: 'POST' });
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

    resetBtn.addEventListener('click', async () => {
        stopAutoPlay();
        if (confirm("This will erase all progress and return to the setup screen. Are you sure?")) {
            try {
                const response = await fetch('/api/game/reset', { method: 'POST' });
                if (response.ok) {
                    window.location.reload();
                } else {
                    alert('Failed to reset the game on the server.');
                }
            } catch (error) {
                alert('Error communicating with the server to reset the game.');
                console.error('Reset error:', error);
            }
        }
    });

    // --- Canvas Sizing & Responsiveness ---

    function resizeCanvas() {
        // Match the drawing surface size to the element's size in the layout
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;
        
        // Recalculate cell size, use width as it's a square
        gridSize = currentGameState.grid_size || 10;
        cellSize = canvas.width / gridSize;
    }
    
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
        // --- Live grid size update ---
        gridSizeInput.addEventListener('input', () => {
            if (currentGameState.game_phase === 'SETUP') {
                const newSize = parseInt(gridSizeInput.value, 10);
                if (newSize >= 5 && newSize <= 50) {
                    const oldSize = currentGameState.grid_size;
                    const outOfBoundsPoints = initialPoints.filter(p => p.x >= newSize || p.y >= newSize);

                    if (outOfBoundsPoints.length > 0) {
                        if (!confirm(`Changing grid size to ${newSize}x${newSize} will remove ${outOfBoundsPoints.length} point(s) that are now out of bounds. Continue?`)) {
                            gridSizeInput.value = oldSize; // Revert input
                            return;
                        }
                    }

                    // Update grid size and filter points
                    currentGameState.grid_size = newSize;
                    initialPoints = initialPoints.filter(p => p.x < newSize && p.y < newSize);
                    resizeCanvas();
                }
            }
        });

        // Setup resize observer
        const gridContainer = document.querySelector('.grid-container');
        const resizeObserver = new ResizeObserver(() => {
            if(currentGameState && currentGameState.grid_size) {
                resizeCanvas();
            }
        });
        resizeObserver.observe(gridContainer);

        const response = await fetch('/api/game/state');
        const gameState = await response.json();
        
        // If page is refreshed during setup, reconstruct state to allow editing
        if (gameState.game_phase === 'SETUP') {
             localTeams = gameState.teams || {};
             Object.values(localTeams).forEach(t => t.isEditing = false); // Ensure no edit mode on load
             initialPoints = Object.values(gameState.points);
             // Auto-select the first team if teams exist, for better UX
             const teamIds = Object.keys(localTeams);
             if (teamIds.length > 0) {
                 selectedTeamId = teamIds[0];
             }
        } else {
             localTeams = gameState.teams || {};
             initialPoints = [];
        }
        
        gridSizeInput.value = gameState.grid_size;
        maxTurnsInput.value = gameState.max_turns;

        // Perform initial render and resize
        updateStateAndRender(gameState);
        // A small delay lets the flexbox layout settle before the first canvas resize.
        setTimeout(() => {
            resizeCanvas();
            hasResizedInitially = true;
            // The animation loop will render the correctly sized canvas.
        }, 50);

        checkForUpdates();
        animationLoop(); // Start the animation loop
    }

    init();
});