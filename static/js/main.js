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
    const actionPreviewPanel = document.getElementById('action-preview-panel');
    const compactLogToggle = document.getElementById('compact-log-toggle');
    const copyLogBtn = document.getElementById('copy-log-btn');

    // --- Helper Functions ---
    function getRandomHslColor() {
        const hue = Math.floor(Math.random() * 360);
        // Using 70% saturation and 50% lightness for bright, but not neon, colors.
        return `hsl(${hue}, 70%, 50%)`;
    }

    function setNewTeamDefaults() {
        newTeamNameInput.value = '';
        newTeamColorInput.value = getRandomHslColor();
        newTeamTraitSelect.value = 'Random'; // Set default trait
    }

    // Debug Toggles
    const debugPointIdsToggle = document.getElementById('debug-point-ids');
    const debugLineIdsToggle = document.getElementById('debug-line-ids');
    const debugLastActionToggle = document.getElementById('debug-last-action');
    const showHullsToggle = document.getElementById('show-hulls-toggle');
    const finalAnalysisOptions = document.getElementById('final-analysis-options');
    const copyStateBtn = document.getElementById('copy-state-btn');
    const restartServerBtn = document.getElementById('restart-server-btn');

    // --- Core Functions ---

    function drawJaggedLine(p1_coords, p2_coords, segments, jag_amount) {
        const dx = p2_coords.x - p1_coords.x;
        const dy = p2_coords.y - p1_coords.y;
        const len = Math.sqrt(dx*dx + dy*dy);
        if (len < 1) return; // Avoid issues with zero-length lines
        const angle = Math.atan2(dy, dx);
        
        ctx.beginPath();
        ctx.moveTo(p1_coords.x, p1_coords.y);
    
        // Only draw internal segments to avoid going past endpoints
        for (let i = 1; i < segments; i++) {
            const lateral = (Math.random() - 0.5) * jag_amount;
            const along = (i / segments) * len;
            const x = p1_coords.x + Math.cos(angle) * along - Math.sin(angle) * lateral;
            const y = p1_coords.y + Math.sin(angle) * along + Math.cos(angle) * lateral;
            ctx.lineTo(x, y);
        }
        ctx.lineTo(p2_coords.x, p2_coords.y);
        ctx.stroke();
    }

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

                // Conduit point visualization (glow)
                if (p.is_conduit_point) {
                    ctx.fillStyle = `rgba(200, 230, 255, 0.7)`;
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius + 3, 0, 2 * Math.PI);
                    ctx.fill();
                }

                // Main point drawing
                ctx.fillStyle = team.color;
                ctx.beginPath();
                if (p.is_bastion_core) {
                    // Draw bastion cores as large outlined squares
                    const squareSize = radius * 2.5;
                    ctx.rect(cx - squareSize / 2, cy - squareSize / 2, squareSize, squareSize);
                    ctx.fill();
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                } else if (p.is_bastion_prong) {
                    // Draw bastion prongs as small squares
                    const squareSize = radius * 1.5;
                    ctx.rect(cx - squareSize / 2, cy - squareSize / 2, squareSize, squareSize);
                    ctx.fill();
                } else if (p.is_fortified) {
                    // Draw fortified points as diamonds
                    const size = radius * 1.7;
                    ctx.moveTo(cx, cy - size); // Top
                    ctx.lineTo(cx + size, cy); // Right
                    ctx.lineTo(cx, cy + size); // Bottom
                    ctx.lineTo(cx - size, cy); // Left
                    ctx.closePath();
                    ctx.fill();
                } else if (p.is_sentry_eye) {
                    // Draw Sentry eyes as a circle with a dot
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
                    ctx.fill();
                    ctx.fillStyle = '#fff';
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius * 0.4, 0, 2 * Math.PI);
                    ctx.fill();
                } else if (p.is_sentry_post) {
                    // Draw Sentry posts as smaller circles
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius * 0.7, 0, 2 * Math.PI);
                    ctx.fill();
                } else if (p.is_monolith_point) {
                    // Draw monolith points as tall thin rects
                    const w = radius * 0.8;
                    const h = radius * 2.5;
                    ctx.rect(cx - w / 2, cy - h / 2, w, h);
                    ctx.fill();
                } else if (p.is_purifier_point) {
                    // Draw purifier points as stars
                    ctx.beginPath();
                    const spikes = 5;
                    const outerRadius = radius * 2.2;
                    const innerRadius = radius * 1.1;
                    ctx.moveTo(cx, cy - outerRadius);
                    for (let i = 0; i < spikes; i++) {
                        let x_outer = cx + Math.cos(i * 2 * Math.PI / spikes - Math.PI/2) * outerRadius;
                        let y_outer = cy + Math.sin(i * 2 * Math.PI / spikes - Math.PI/2) * outerRadius;
                        ctx.lineTo(x_outer, y_outer);
                        let x_inner = cx + Math.cos((i + 0.5) * 2 * Math.PI / spikes - Math.PI/2) * innerRadius;
                        let y_inner = cy + Math.sin((i + 0.5) * 2 * Math.PI / spikes - Math.PI/2) * innerRadius;
                        ctx.lineTo(x_inner, y_inner);
                    }
                    ctx.closePath();
                    ctx.fill();
                } else if (p.is_trebuchet_point) {
                    // Draw trebuchet points distinctively (as a pentagon)
                    ctx.beginPath();
                    const pointCount = 5;
                    ctx.moveTo(cx + radius, cy);
                    for (let i = 1; i <= pointCount; i++) {
                        const angle = i * 2 * Math.PI / pointCount;
                        ctx.lineTo(cx + radius * Math.cos(angle), cy + radius * Math.sin(angle));
                    }
                    ctx.closePath();
                    ctx.fill();
                } else if (p.is_anchor) {
                    // Draw anchors as squares
                    const squareSize = radius * 1.8;
                    ctx.rect(cx - squareSize / 2, cy - squareSize / 2, squareSize, squareSize);
                    ctx.fill();
                } else if (p.is_nexus_point) {
                    // Draw Nexus points as concentric circles
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
                    ctx.fill();
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius * 0.5, 0, 2 * Math.PI);
                    ctx.fill();
                } else {
                    // Draw normal points as circles
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
                    ctx.fill();
                }

                // Stasis effect (drawn on top of point)
                if (p.is_in_stasis) {
                    const pulse = Math.abs(Math.sin(Date.now() / 400));
                    ctx.strokeStyle = `rgba(150, 220, 255, ${0.5 + pulse * 0.4})`;
                    ctx.lineWidth = 1.5;
                    // Draw a cage-like effect
                    const cage_radius = radius + 3;
                    ctx.beginPath(); // Vertical bars
                    ctx.moveTo(cx - cage_radius, cy);
                    ctx.lineTo(cx + cage_radius, cy);
                    ctx.moveTo(cx, cy - cage_radius);
                    ctx.lineTo(cx, cy + cage_radius);
                    ctx.stroke();
                    ctx.beginPath(); // Circle
                    ctx.arc(cx, cy, cage_radius, 0, 2 * Math.PI);
                    ctx.stroke();
                }


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
                    let base_width = line.is_bastion_line ? 4 : 2;
                    if (line.empower_strength > 0) {
                        base_width += line.empower_strength * 1.5;
                        // Add a subtle glow/pulse to empowered lines
                        const pulse = Math.abs(Math.sin(Date.now() / 400));
                        ctx.strokeStyle = `rgba(255,255,255, ${pulse * 0.5})`;
                        ctx.lineWidth = base_width + 2;
                        ctx.beginPath();
                        ctx.moveTo(x1, y1);
                        ctx.lineTo(x2, y2);
                        ctx.stroke();
                        ctx.strokeStyle = team.color;
                    }
                    ctx.lineWidth = base_width;
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

    function drawConduits(gameState) {
        if (!gameState.conduits) return;
    
        for (const teamId in gameState.conduits) {
            const teamConduits = gameState.conduits[teamId];
            const team = gameState.teams[teamId];
            if (!team || !teamConduits) continue;
    
            teamConduits.forEach(conduit => {
                const p1 = gameState.points[conduit.endpoint1_id];
                const p2 = gameState.points[conduit.endpoint2_id];
    
                if (p1 && p2) {
                    ctx.beginPath();
                    ctx.moveTo((p1.x + 0.5) * cellSize, (p1.y + 0.5) * cellSize);
                    ctx.lineTo((p2.x + 0.5) * cellSize, (p2.y + 0.5) * cellSize);
                    ctx.strokeStyle = team.color;
                    ctx.lineWidth = 10; // Thick line
                    ctx.globalAlpha = 0.15; // Very translucent
                    ctx.lineCap = 'round';
                    ctx.stroke();
                    ctx.globalAlpha = 1.0;
                    ctx.lineCap = 'butt';
                }
            });
        }
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

    function drawMonoliths(gameState) {
        if (!gameState.monoliths) return;

        for (const monolithId in gameState.monoliths) {
            const monolith = gameState.monoliths[monolithId];
            const team = gameState.teams[monolith.teamId];
            if (!team) continue;

            const points = monolith.point_ids.map(pid => gameState.points[pid]).filter(p => p);
            if (points.length !== 4) continue;

            // Sort points to draw polygon correctly
            const center = monolith.center_coords;
            points.sort((a, b) => {
                return Math.atan2(a.y - center.y, a.x - center.x) - Math.atan2(b.y - center.y, b.x - center.x);
            });

            ctx.beginPath();
            ctx.moveTo((points[0].x + 0.5) * cellSize, (points[0].y + 0.5) * cellSize);
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo((points[i].x + 0.5) * cellSize, (points[i].y + 0.5) * cellSize);
            }
            ctx.closePath();
            
            ctx.fillStyle = team.color;
            ctx.globalAlpha = 0.15;
            ctx.fill();

            // Add some "energy" effect inside
            const pulse = Math.abs(Math.sin(Date.now() / 600));
            ctx.globalAlpha = 0.1 + pulse * 0.2;
            ctx.lineWidth = 1 + pulse;
            ctx.strokeStyle = '#fff';
            ctx.stroke();

            ctx.globalAlpha = 1.0;
        }
    }

    function drawTrebuchets(gameState) {
        if (!gameState.trebuchets) return;

        for (const teamId in gameState.trebuchets) {
            const teamTrebuchets = gameState.trebuchets[teamId];
            const team = gameState.teams[teamId];
            if (!team || !teamTrebuchets) continue;

            teamTrebuchets.forEach(trebuchet => {
                const apex = gameState.points[trebuchet.apex_id];
                const cw = gameState.points[trebuchet.counterweight_id];

                if (apex && cw) {
                    // Draw the arm of the trebuchet
                    ctx.beginPath();
                    ctx.moveTo((apex.x + 0.5) * cellSize, (apex.y + 0.5) * cellSize);
                    ctx.lineTo((cw.x + 0.5) * cellSize, (cw.y + 0.5) * cellSize);
                    ctx.strokeStyle = team.color;
                    ctx.lineWidth = 4;
                    ctx.globalAlpha = 0.4;
                    ctx.stroke();
                    ctx.globalAlpha = 1.0;
                }
            });
        }
    }

    function drawWhirlpools(gameState) {
        if (!gameState.whirlpools) return;
    
        gameState.whirlpools.forEach(wp => {
            const team = gameState.teams[wp.teamId];
            if (!team) return;

            const cx = (wp.coords.x + 0.5) * cellSize;
            const cy = (wp.coords.y + 0.5) * cellSize;
            const radius = Math.sqrt(wp.radius_sq) * cellSize;
            const now = Date.now();
            const angle_offset = (now / 2000) % (2 * Math.PI); // Full rotation every 2 seconds

            ctx.save();
            ctx.translate(cx, cy);

            const num_lines = 12;
            for (let i = 0; i < num_lines; i++) {
                const angle = angle_offset + (i * 2 * Math.PI / num_lines);
                const start_radius = radius * 0.2;
                const end_radius = radius * (1 - (wp.turns_left / 4) * 0.5); // Shrinks as it expires

                ctx.beginPath();
                ctx.moveTo(
                    Math.cos(angle) * start_radius,
                    Math.sin(angle) * start_radius
                );
                // Swirly quadratic curve
                ctx.quadraticCurveTo(
                    Math.cos(angle + wp.swirl * 2) * radius * 0.6,
                    Math.sin(angle + wp.swirl * 2) * radius * 0.6,
                    Math.cos(angle + wp.swirl * 4) * end_radius,
                    Math.sin(angle + wp.swirl * 4) * end_radius
                );
                ctx.strokeStyle = team.color;
                ctx.lineWidth = 1.5;
                ctx.globalAlpha = 0.5 * (wp.turns_left / 4); // Fade out as it expires
                ctx.stroke();
            }
            ctx.restore();
        });
    }

    function drawNexuses(gameState) {
        if (!gameState.nexuses) return;
    
        for (const teamId in gameState.nexuses) {
            const teamNexuses = gameState.nexuses[teamId];
            const team = gameState.teams[teamId];
            if (!team || !teamNexuses) continue;
    
            teamNexuses.forEach(nexus => {
                const points = nexus.point_ids.map(pid => gameState.points[pid]).filter(p => p);
                if (points.length !== 4) return;
                
                // Draw the square fill
                ctx.beginPath();
                // Sort points to draw polygon correctly. Angular sort around center is robust.
                const center = nexus.center;
                points.sort((a, b) => {
                    return Math.atan2(a.y - center.y, a.x - center.x) - Math.atan2(b.y - center.y, b.x - center.x);
                });
                
                ctx.moveTo((points[0].x + 0.5) * cellSize, (points[0].y + 0.5) * cellSize);
                for (let i = 1; i < points.length; i++) {
                     ctx.lineTo((points[i].x + 0.5) * cellSize, (points[i].y + 0.5) * cellSize);
                }
                ctx.closePath();
                ctx.fillStyle = team.color;
                ctx.globalAlpha = 0.25;
                ctx.fill();
    
                // Draw the central orb
                const orb_cx = (nexus.center.x + 0.5) * cellSize;
                const orb_cy = (nexus.center.y + 0.5) * cellSize;
                const pulse = Math.abs(Math.sin(Date.now() / 800)); // Faster pulse
                
                // Outer glow
                const gradient = ctx.createRadialGradient(orb_cx, orb_cy, 0, orb_cx, orb_cy, 10 + pulse * 5);
                gradient.addColorStop(0, `rgba(255, 255, 255, ${0.8 - pulse * 0.3})`);
                gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
                ctx.fillStyle = gradient;
                ctx.globalAlpha = 1.0;
                ctx.beginPath();
                ctx.arc(orb_cx, orb_cy, 10 + pulse * 5, 0, 2 * Math.PI);
                ctx.fill();
    
                // Inner core
                ctx.fillStyle = team.color;
                ctx.beginPath();
                ctx.arc(orb_cx, orb_cy, 4 + pulse * 2, 0, 2 * Math.PI);
                ctx.fill();
    
                ctx.globalAlpha = 1.0;
            });
        }
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

            // Draw Trident Runes
            if (teamRunes.trident) {
                teamRunes.trident.forEach(rune => {
                    const p_apex = gameState.points[rune.apex_id];
                    const p_h = gameState.points[rune.handle_id];
                    const p_p1 = gameState.points[rune.prong_ids[0]];
                    const p_p2 = gameState.points[rune.prong_ids[1]];
                    if (!p_apex || !p_h || !p_p1 || !p_p2) return;

                    ctx.beginPath();
                    // Handle to Apex
                    ctx.moveTo((p_h.x + 0.5) * cellSize, (p_h.y + 0.5) * cellSize);
                    ctx.lineTo((p_apex.x + 0.5) * cellSize, (p_apex.y + 0.5) * cellSize);
                    // Apex to Prongs
                    ctx.moveTo((p_p1.x + 0.5) * cellSize, (p_p1.y + 0.5) * cellSize);
                    ctx.lineTo((p_apex.x + 0.5) * cellSize, (p_apex.y + 0.5) * cellSize);
                    ctx.lineTo((p_p2.x + 0.5) * cellSize, (p_p2.y + 0.5) * cellSize);
                    
                    ctx.strokeStyle = team.color;
                    ctx.lineWidth = 8;
                    ctx.globalAlpha = 0.4;
                    ctx.filter = 'blur(2px)';
                    ctx.stroke();
                    ctx.filter = 'none';
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

            // Draw Shield Runes
            if (teamRunes.shield) {
                teamRunes.shield.forEach(rune => {
                    const tri_points = rune.triangle_ids.map(pid => gameState.points[pid]).filter(p => p);
                    const core_point = gameState.points[rune.core_id];
                    if (tri_points.length !== 3 || !core_point) return;

                    // Draw the filled triangle
                    ctx.beginPath();
                    ctx.moveTo((tri_points[0].x + 0.5) * cellSize, (tri_points[0].y + 0.5) * cellSize);
                    ctx.lineTo((tri_points[1].x + 0.5) * cellSize, (tri_points[1].y + 0.5) * cellSize);
                    ctx.lineTo((tri_points[2].x + 0.5) * cellSize, (tri_points[2].y + 0.5) * cellSize);
                    ctx.closePath();
                    
                    ctx.fillStyle = team.color;
                    ctx.globalAlpha = 0.25;
                    ctx.fill();

                    // Draw an outline pulse
                    const pulse = Math.abs(Math.sin(Date.now() / 500));
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 1 + pulse * 2;
                    ctx.globalAlpha = 0.3 + pulse * 0.4;
                    ctx.stroke();

                    ctx.globalAlpha = 1.0;
                });
            }

            // Draw Hourglass Runes
            if (teamRunes.hourglass) {
                teamRunes.hourglass.forEach(rune => {
                    const p_v = gameState.points[rune.vertex_id];
                    if (!p_v) return;

                    const all_points = rune.all_points.map(pid => gameState.points[pid]);
                    if (all_points.some(p => !p)) return;

                    const tri1_pts = all_points.filter(p => p.id !== p_v.id).slice(0, 2);
                    const tri2_pts = all_points.filter(p => p.id !== p_v.id).slice(2, 4);
                    if (tri1_pts.length < 2 || tri2_pts.length < 2) return;

                    ctx.beginPath();
                    // tri 1
                    ctx.moveTo((tri1_pts[0].x + 0.5) * cellSize, (tri1_pts[0].y + 0.5) * cellSize);
                    ctx.lineTo((p_v.x + 0.5) * cellSize, (p_v.y + 0.5) * cellSize);
                    ctx.lineTo((tri1_pts[1].x + 0.5) * cellSize, (tri1_pts[1].y + 0.5) * cellSize);
                    // tri 2
                    ctx.moveTo((tri2_pts[0].x + 0.5) * cellSize, (tri2_pts[0].y + 0.5) * cellSize);
                    ctx.lineTo((p_v.x + 0.5) * cellSize, (p_v.y + 0.5) * cellSize);
                    ctx.lineTo((tri2_pts[1].x + 0.5) * cellSize, (tri2_pts[1].y + 0.5) * cellSize);
                    
                    ctx.strokeStyle = team.color;
                    ctx.lineWidth = 6;
                    ctx.globalAlpha = 0.4;
                    ctx.stroke();
                    ctx.globalAlpha = 1.0;
                });
            }
        }
    }

    function drawHeartwoods(gameState) {
        if (!gameState.heartwoods) return;

        for (const teamId in gameState.heartwoods) {
            const heartwood = gameState.heartwoods[teamId];
            const team = gameState.teams[teamId];
            if (!team || !heartwood) continue;

            const cx = (heartwood.center_coords.x + 0.5) * cellSize;
            const cy = (heartwood.center_coords.y + 0.5) * cellSize;
            const pulse = Math.abs(Math.sin(Date.now() / 1200)); // Slow, deep pulse
            const baseRadius = 10;
            const radius = baseRadius + pulse * 5;

            // Draw the aura
            ctx.beginPath();
            ctx.arc(cx, cy, (gameState.grid_size * 0.2) * cellSize, 0, 2 * Math.PI);
            ctx.fillStyle = team.color;
            ctx.globalAlpha = 0.05 + pulse * 0.05;
            ctx.fill();
            ctx.globalAlpha = 1.0;

            // Draw the core
            // Outer ring
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
            ctx.strokeStyle = team.color;
            ctx.lineWidth = 2 + pulse * 2;
            ctx.globalAlpha = 0.5 + pulse * 0.5;
            ctx.stroke();
            
            // Inner core
            ctx.beginPath();
            ctx.arc(cx, cy, baseRadius * 0.5, 0, 2 * Math.PI);
            ctx.fillStyle = team.color;
            ctx.globalAlpha = 1.0;
            ctx.fill();

            // Maybe draw some 'roots'
            ctx.save();
            ctx.translate(cx, cy);
            ctx.lineWidth = 1;
            ctx.globalAlpha = 0.4;
            for(let i=0; i < 5; i++) {
                ctx.rotate( (2 * Math.PI / 5) + (pulse * 0.1) );
                ctx.beginPath();
                ctx.moveTo(0, radius * 0.5);
                ctx.quadraticCurveTo(radius, radius, radius * 1.5, radius * 0.5);
                ctx.stroke();
            }
            ctx.restore();
        }
    }

    function drawFissures(gameState) {
        if (!gameState.fissures) return;

        gameState.fissures.forEach(fissure => {
            const p1 = {x: (fissure.p1.x + 0.5) * cellSize, y: (fissure.p1.y + 0.5) * cellSize};
            const p2 = {x: (fissure.p2.x + 0.5) * cellSize, y: (fissure.p2.y + 0.5) * cellSize};
            
            ctx.strokeStyle = `rgba(30, 30, 30, ${0.4 + (fissure.turns_left / 8) * 0.4})`;
            ctx.lineWidth = 4;
            ctx.lineCap = 'round';
            // Jagged line effect
            drawJaggedLine(p1, p2, 15, 6);
            ctx.lineCap = 'butt';
        });
    }

    function drawRiftSpires(gameState) {
        if (!gameState.rift_spires) return;

        for (const spireId in gameState.rift_spires) {
            const spire = gameState.rift_spires[spireId];
            const team = gameState.teams[spire.teamId];
            if (!team) continue;

            const cx = (spire.coords.x + 0.5) * cellSize;
            const cy = (spire.coords.y + 0.5) * cellSize;
            const now = Date.now();
            const rotation = (now / 4000) % (2 * Math.PI);
            const pulse = Math.abs(Math.sin(now / 300));
            const charge_level = spire.charge / spire.charge_needed;

            // Draw a spiky star shape
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(rotation);
            
            ctx.beginPath();
            const spikes = 7;
            const outerRadius = 12 + pulse * 2;
            const innerRadius = 6;
            for (let i = 0; i < spikes * 2; i++) {
                const radius = i % 2 === 0 ? outerRadius : innerRadius;
                const angle = (i * Math.PI) / spikes;
                ctx.lineTo(Math.cos(angle) * radius, Math.sin(angle) * radius);
            }
            ctx.closePath();

            ctx.fillStyle = team.color;
            ctx.fill();
            
            // Draw charge level indicator
            if (charge_level < 1) {
                ctx.strokeStyle = `rgba(255, 255, 255, 0.5)`;
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.arc(0, 0, outerRadius + 2, -Math.PI/2, -Math.PI/2 + (2*Math.PI * charge_level), false);
                ctx.stroke();
            } else {
                // Glow when fully charged
                ctx.fillStyle = `rgba(255, 255, 255, ${pulse * 0.3})`;
                ctx.fill();
            }

            ctx.restore();
        }
    }

    function drawBarricades(gameState) {
        if (!gameState.barricades) return;

        gameState.barricades.forEach(barricade => {
            const team = gameState.teams[barricade.teamId];
            if (!team) return;

            const p1 = {x: (barricade.p1.x + 0.5) * cellSize, y: (barricade.p1.y + 0.5) * cellSize};
            const p2 = {x: (barricade.p2.x + 0.5) * cellSize, y: (barricade.p2.y + 0.5) * cellSize};
            
            // Draw a thick, "rocky" looking line
            ctx.strokeStyle = team.color; // Use team color to show who built it
            ctx.globalAlpha = 0.5 + (barricade.turns_left / 5) * 0.5; // Fade as it expires
            ctx.lineWidth = 6;
            ctx.lineCap = 'round';
            drawJaggedLine(p1, p2, 10, 4);
            
            // Add a solid "core" to it
            ctx.globalAlpha = 0.8;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();

            ctx.lineCap = 'butt';
            ctx.globalAlpha = 1.0;
        });
    }

    function drawWonders(gameState) {
        if (!gameState.wonders) return;
    
        for (const wonderId in gameState.wonders) {
            const wonder = gameState.wonders[wonderId];
            const team = gameState.teams[wonder.teamId];
            if (!team || wonder.type !== 'ChronosSpire') continue;
    
            const cx = (wonder.coords.x + 0.5) * cellSize;
            const cy = (wonder.coords.y + 0.5) * cellSize;
            const now = Date.now();
            const pulse = Math.abs(Math.sin(now / 500)); // Faster, more energetic pulse
            const rotation = (now / 5000) % (2 * Math.PI);
    
            // Base
            const baseRadius = 20;
            ctx.beginPath();
            ctx.arc(cx, cy, baseRadius, 0, 2 * Math.PI);
            const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, baseRadius);
            gradient.addColorStop(0, team.color + "99");
            gradient.addColorStop(1, team.color + "00");
            ctx.fillStyle = gradient;
            ctx.globalAlpha = 0.3 + pulse * 0.2;
            ctx.fill();
            ctx.globalAlpha = 1.0;
    
            // Rotating rings
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(rotation);
            ctx.strokeStyle = team.color;
            ctx.lineWidth = 1.5;
            ctx.globalAlpha = 0.8;
            ctx.beginPath();
            ctx.arc(0, 0, baseRadius * 0.7, 0, 2 * Math.PI);
            ctx.stroke();
            ctx.rotate(Math.PI / 2); // Rotate second ring
            ctx.beginPath();
            ctx.arc(0, 0, baseRadius * 1.2, 0, 1.5 * Math.PI); // Incomplete ring
            ctx.stroke();
            ctx.restore();
    
            // Central core
            ctx.beginPath();
            ctx.arc(cx, cy, 5 + pulse * 2, 0, 2 * Math.PI);
            ctx.fillStyle = '#fff';
            ctx.fill();
            ctx.beginPath();
            ctx.arc(cx, cy, 2 + pulse, 0, 2 * Math.PI);
            ctx.fillStyle = team.color;
            ctx.fill();
    
            // Countdown timer
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 14px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.shadowColor = 'black';
            ctx.shadowBlur = 4;
            ctx.fillText(wonder.turns_to_victory, cx, cy);
            ctx.shadowBlur = 0;
        }
    }

    function drawPrisms(gameState) {
        if (!gameState.prisms) return;

        for (const teamId in gameState.prisms) {
            const teamPrisms = gameState.prisms[teamId];
            const team = gameState.teams[teamId];
            if (!team || !teamPrisms) continue;

            teamPrisms.forEach(prism => {
                const p1 = gameState.points[prism.shared_p1_id];
                const p2 = gameState.points[prism.shared_p2_id];

                if (p1 && p2) {
                    const x1 = (p1.x + 0.5) * cellSize;
                    const y1 = (p1.y + 0.5) * cellSize;
                    const x2 = (p2.x + 0.5) * cellSize;
                    const y2 = (p2.y + 0.5) * cellSize;
                    
                    // Draw a glowing line for the shared edge
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.strokeStyle = team.color;
                    ctx.lineWidth = 8;
                    ctx.globalAlpha = 0.5;
                    ctx.filter = 'blur(4px)'; // Glow effect
                    ctx.stroke();
                    
                    // Reset filters
                    ctx.filter = 'none';
                    ctx.globalAlpha = 1.0;
                }
            });
        }
    }

    function drawVisualEffects() {
        const now = Date.now();
        visualEffects = visualEffects.filter(effect => {
            const age = now - effect.startTime;
            if (age > effect.duration) return false; // Remove expired effects

            const progress = age / effect.duration;

            if (effect.type === 'growing_wall') {
                const p1 = {x: effect.barricade.p1.x * cellSize, y: effect.barricade.p1.y * cellSize};
                const p2 = {x: effect.barricade.p2.x * cellSize, y: effect.barricade.p2.y * cellSize};
                
                ctx.strokeStyle = effect.color;
                ctx.globalAlpha = progress;
                ctx.lineWidth = 2 + progress * 4;
                ctx.lineCap = 'round';
                drawJaggedLine(p1, p2, 10, 4 * progress);

                ctx.lineCap = 'butt';
                ctx.globalAlpha = 1.0;
            } else if (effect.type === 'line_crack') {
                const p1 = currentGameState.points[effect.old_line.p1_id];
                const p2 = currentGameState.points[effect.old_line.p2_id];
                if (p1 && p2) {
                    const p1_coords = {x: (p1.x + 0.5) * cellSize, y: (p1.y + 0.5) * cellSize};
                    const p2_coords = {x: (p2.x + 0.5) * cellSize, y: (p2.y + 0.5) * cellSize};
                    const new_p_coords = {x: (effect.new_point.x + 0.5) * cellSize, y: (effect.new_point.y + 0.5) * cellSize};
                    
                    // Draw old line fading out
                    ctx.beginPath();
                    ctx.moveTo(p1_coords.x, p1_coords.y);
                    ctx.lineTo(p2_coords.x, p2_coords.y);
                    ctx.strokeStyle = effect.color;
                    ctx.globalAlpha = 1 - progress;
                    ctx.lineWidth = 2;
                    ctx.stroke();

                    // Draw crack effect
                    if (progress < 0.5) {
                        const crack_progress = progress * 2;
                        ctx.beginPath();
                        ctx.arc(new_p_coords.x, new_p_coords.y, 10 * crack_progress, 0, 2*Math.PI);
                        ctx.strokeStyle = `rgba(255, 255, 255, ${1 - crack_progress})`;
                        ctx.lineWidth = 3 * (1 - crack_progress);
                        ctx.stroke();
                    }
                    ctx.globalAlpha = 1.0;
                }
            } else if (effect.type === 'territory_fill') {
                ctx.save();
                ctx.beginPath();
                ctx.moveTo((effect.points[0].x + 0.5) * cellSize, (effect.points[0].y + 0.5) * cellSize);
                ctx.lineTo((effect.points[1].x + 0.5) * cellSize, (effect.points[1].y + 0.5) * cellSize);
                ctx.lineTo((effect.points[2].x + 0.5) * cellSize, (effect.points[2].y + 0.5) * cellSize);
                ctx.closePath();
                
                // Create a clip path that grows from the center out
                const center = {
                    x: (effect.points[0].x + effect.points[1].x + effect.points[2].x) / 3 * cellSize + (0.5*cellSize),
                    y: (effect.points[0].y + effect.points[1].y + effect.points[2].y) / 3 * cellSize + (0.5*cellSize),
                };
                const max_dist = Math.max(...effect.points.map(p => Math.sqrt((p.x*cellSize-center.x)**2 + (p.y*cellSize-center.y)**2)));
                
                ctx.clip(); 
                
                // Draw a circle that expands to fill the clip
                ctx.beginPath();
                ctx.arc(center.x, center.y, max_dist * progress * 1.5, 0, 2*Math.PI);
                ctx.fillStyle = effect.color;
                ctx.globalAlpha = 0.3;
                ctx.fill();
                
                ctx.restore();
                ctx.globalAlpha = 1.0;

            } else if (effect.type === 'nexus_detonation') {
                ctx.beginPath();
                ctx.arc(
                    (effect.center.x + 0.5) * cellSize,
                    (effect.center.y + 0.5) * cellSize,
                    Math.sqrt(effect.radius_sq) * cellSize * progress, // Radius grows
                    0, 2 * Math.PI
                );
                ctx.strokeStyle = effect.color;
                ctx.globalAlpha = (1 - progress);
                ctx.lineWidth = 4;
                ctx.stroke();
                ctx.globalAlpha = 1.0;
            } else if (effect.type === 'monolith_wave' || effect.type === 'shield_pulse') {
                const progress = age / effect.duration;
                ctx.beginPath();
                ctx.arc(
                    (effect.center.x + 0.5) * cellSize,
                    (effect.center.y + 0.5) * cellSize,
                    Math.sqrt(effect.radius_sq) * cellSize * progress,
                    0, 2 * Math.PI
                );
                ctx.strokeStyle = effect.color || `rgba(220, 220, 255, ${0.8 * (1 - progress)})`; // White-blue wave
                ctx.lineWidth = 4 * (1 - progress);
                ctx.stroke();
            } else if (effect.type === 'nova_burst') {
                const num_particles = 20;
                const radius = effect.radius * progress;
                // Expanding shockwave
                ctx.beginPath();
                ctx.arc((effect.x + 0.5) * cellSize, (effect.y + 0.5) * cellSize, radius, 0, 2 * Math.PI);
                ctx.strokeStyle = `rgba(255, 100, 100, ${1 - progress})`;
                ctx.lineWidth = 3;
                ctx.stroke();
                // Particles
                for(let i=0; i < num_particles; i++) {
                    const angle = effect.particles[i].angle;
                    const speed = effect.particles[i].speed;
                    const dist = speed * age / 1000;
                    ctx.beginPath();
                    ctx.arc(
                        (effect.x + 0.5) * cellSize + Math.cos(angle) * dist,
                        (effect.y + 0.5) * cellSize + Math.sin(angle) * dist,
                        Math.max(0, 2 * (1-progress)), 0, 2*Math.PI
                    );
                    ctx.fillStyle = `rgba(255, 150, 100, ${1 - progress})`;
                    ctx.fill();
                }
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
            } else if (effect.type === 'animated_ray') {
                const start_x = (effect.p1.x + 0.5) * cellSize;
                const start_y = (effect.p1.y + 0.5) * cellSize;
                const end_x = (effect.p2.x + 0.5) * cellSize;
                const end_y = (effect.p2.y + 0.5) * cellSize;

                const current_x = start_x + (end_x - start_x) * progress;
                const current_y = start_y + (end_y - start_y) * progress;

                // Draw a fading tail
                const tail_length = 40;
                const dx = end_x - start_x;
                const dy = end_y - start_y;
                const len = Math.sqrt(dx*dx + dy*dy);
                const tail_x = current_x - (dx/len) * tail_length;
                const tail_y = current_y - (dy/len) * tail_length;

                const gradient = ctx.createLinearGradient(current_x, current_y, tail_x, tail_y);
                gradient.addColorStop(0, effect.color);
                gradient.addColorStop(1, 'rgba(255, 0, 0, 0)');
                
                ctx.strokeStyle = gradient;
                ctx.lineWidth = effect.lineWidth || 3;
                ctx.beginPath();
                ctx.moveTo(tail_x, tail_y);
                ctx.lineTo(current_x, current_y);
                ctx.stroke();

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
            } else if (effect.type === 'polygon_flash') {
                const progress = age / effect.duration;
                if (effect.points && effect.points.length >= 3) {
                    ctx.beginPath();
                    ctx.moveTo((effect.points[0].x + 0.5) * cellSize, (effect.points[0].y + 0.5) * cellSize);
                    for (let i = 1; i < effect.points.length; i++) {
                        ctx.lineTo((effect.points[i].x + 0.5) * cellSize, (effect.points[i].y + 0.5) * cellSize);
                    }
                    ctx.closePath();
                    ctx.fillStyle = effect.color;
                    ctx.globalAlpha = 0.7 * (1 - progress); // Fade out
                    ctx.fill();
                    ctx.globalAlpha = 1.0;
                }
            } else if (effect.type === 'chain_lightning') {
                const points = effect.point_ids.map(pid => currentGameState.points[pid]).filter(p => p);
                if (points.length < 2) return true;
                
                ctx.lineWidth = 1 + Math.random() * 2; // Flickering width
                ctx.strokeStyle = `rgba(180, 220, 255, ${0.9 * (1 - progress)})`;
            
                // Draw lightning along the conduit path
                for (let i = 0; i < points.length - 1; i++) {
                    const p1 = points[i];
                    const p2 = points[i+1];
                    const p1_coords = { x: (p1.x + 0.5) * cellSize, y: (p1.y + 0.5) * cellSize };
                    const p2_coords = { x: (p2.x + 0.5) * cellSize, y: (p2.y + 0.5) * cellSize };
                    drawJaggedLine(p1_coords, p2_coords, 5, 8);
                }
            
                // Draw jump to target if it exists and after a delay
                const jump_progress = (age - 400) / (effect.duration - 400);
                if (effect.destroyed_point && jump_progress > 0) {
                     ctx.lineWidth = 2 + Math.random() * 2;
                     ctx.strokeStyle = `rgba(200, 230, 255, ${0.9 * (1 - jump_progress)})`;
                    // Jump from one of the endpoints. Let's find the one closest to the target.
                    const endpoint1 = points[0];
                    const endpoint2 = points[points.length-1];
                    const d_sq_1 = (endpoint1.x - effect.destroyed_point.x)**2 + (endpoint1.y - effect.destroyed_point.y)**2;
                    const d_sq_2 = (endpoint2.x - effect.destroyed_point.x)**2 + (endpoint2.y - effect.destroyed_point.y)**2;
                    const jump_origin_point = d_sq_1 < d_sq_2 ? endpoint1 : endpoint2;

                    const p1_coords = {x: (jump_origin_point.x + 0.5)*cellSize, y: (jump_origin_point.y + 0.5)*cellSize};
                    const p2_coords = {x: (effect.destroyed_point.x + 0.5)*cellSize, y: (effect.destroyed_point.y + 0.5)*cellSize};
                    drawJaggedLine(p1_coords, p2_coords, 7, 10);
                }

            } else if (effect.type === 'heartwood_creation') {
                const progress = age / effect.duration;
                effect.sacrificed_points.forEach(p => {
                    const start_x = (p.x + 0.5) * cellSize;
                    const start_y = (p.y + 0.5) * cellSize;
                    const end_x = (effect.center_coords.x + 0.5) * cellSize;
                    const end_y = (effect.center_coords.y + 0.5) * cellSize;
                    
                    const current_x = start_x + (end_x - start_x) * progress;
                    const current_y = start_y + (end_y - start_y) * progress;

                    ctx.beginPath();
                    ctx.arc(current_x, current_y, Math.max(0, 8 * (1 - progress)), 0, 2*Math.PI);
                    ctx.fillStyle = `rgba(150, 255, 150, ${1 - progress})`;
                    ctx.fill();
                });
            } else if (effect.type === 'bastion_formation') {
                const progress = age / effect.duration;
                const pulse = Math.abs(Math.sin(progress * Math.PI)); // Curve from 0 -> 1 -> 0. Abs to prevent negative line width.
                ctx.globalAlpha = pulse * 0.9;
                ctx.lineWidth = 2 + pulse * 8; // Shield widens
                ctx.strokeStyle = `rgba(173, 216, 230, ${pulse * 0.8})`; // Shield blue color
                ctx.lineCap = 'round';
                effect.line_ids.forEach(line_id => {
                    const line = currentGameState.lines.find(l => l.id === line_id);
                    if (line && currentGameState.points[line.p1_id] && currentGameState.points[line.p2_id]) {
                        const p1 = currentGameState.points[line.p1_id];
                        const p2 = currentGameState.points[line.p2_id];
                        ctx.beginPath();
                        ctx.moveTo((p1.x + 0.5) * cellSize, (p1.y + 0.5) * cellSize);
                        ctx.lineTo((p2.x + 0.5) * cellSize, (p2.y + 0.5) * cellSize);
                        ctx.stroke();
                    }
                });
                ctx.globalAlpha = 1.0;
                ctx.lineCap = 'butt';
            } else if (effect.type === 'monolith_formation') {
                const progress = age / effect.duration;
                const cx = (effect.center.x + 0.5) * cellSize;
                const top_y = -20;
                const ground_y = (effect.center.y + 0.5) * cellSize;
                const beam_height = ground_y - top_y;
                
                // Animate beam descending
                const current_bottom_y = top_y + beam_height * progress;

                const gradient = ctx.createLinearGradient(cx, top_y, cx, current_bottom_y);
                gradient.addColorStop(0, 'rgba(255, 255, 255, 0)');
                gradient.addColorStop(0.8, `rgba(255, 255, 255, ${1 - progress})`);
                gradient.addColorStop(1, effect.color);

                ctx.fillStyle = gradient;
                ctx.fillRect(cx - 10, top_y, 20, current_bottom_y - top_y); // The beam
                
                // Impact ring on the ground
                if (progress > 0.5) {
                    const impact_progress = (progress - 0.5) * 2;
                    ctx.beginPath();
                    ctx.arc(cx, ground_y, 30 * impact_progress, 0, 2 * Math.PI);
                    ctx.strokeStyle = `rgba(255, 255, 255, ${1 - impact_progress})`;
                    ctx.lineWidth = 3 * (1 - impact_progress);
                    ctx.stroke();
                }

            } else if (effect.type === 'energy_spiral') {
                const ease_progress = Math.sin(progress * Math.PI / 2); // Ease-out curve
                const start_x = (effect.start.x + 0.5) * cellSize;
                const start_y = (effect.start.y + 0.5) * cellSize;
                const end_x = (effect.end.x + 0.5) * cellSize;
                const end_y = (effect.end.y + 0.5) * cellSize;

                const num_particles = 15;
                for (let i = 0; i < num_particles; i++) {
                    const particle_progress = (ease_progress + i / num_particles / 5) % 1.0;
                    const current_x = start_x + (end_x - start_x) * particle_progress;
                    const current_y = start_y + (end_y - start_y) * particle_progress;

                    // Add swirl
                    const swirl_angle = particle_progress * Math.PI * 4 + (i / num_particles * Math.PI * 2);
                    const swirl_radius = Math.sin(particle_progress * Math.PI) * 20;
                    
                    const final_x = current_x + Math.cos(swirl_angle) * swirl_radius;
                    const final_y = current_y + Math.sin(swirl_angle) * swirl_radius;

                    ctx.beginPath();
                    ctx.arc(final_x, final_y, 2, 0, 2 * Math.PI);
                    ctx.fillStyle = `rgba(255, 255, 255, ${1 - particle_progress})`;
                    ctx.fill();
                }

            } else if (effect.type === 'portal_link') {
                const progress = age / effect.duration;
                const p1_x = (effect.p1.x + 0.5) * cellSize;
                const p1_y = (effect.p1.y + 0.5) * cellSize;
                const p2_x = (effect.p2.x + 0.5) * cellSize;
                const p2_y = (effect.p2.y + 0.5) * cellSize;

                // Draw two swirling portals
                const portal_radius = 15 * Math.abs(Math.sin(progress * Math.PI)); // Grow and shrink pulse.
                [ {x: p1_x, y: p1_y}, {x: p2_x, y: p2_y} ].forEach(p => {
                    ctx.beginPath();
                    // Defensively ensure radius is non-negative to prevent IndexSizeError.
                    ctx.arc(p.x, p.y, Math.max(0, portal_radius), 0, 2 * Math.PI);
                    ctx.strokeStyle = effect.color;
                    ctx.lineWidth = 2;
                    ctx.globalAlpha = 0.8;
                    ctx.stroke();
                });

                // Draw a shimmering connector
                if (progress > 0.1 && progress < 0.9) {
                    ctx.beginPath();
                    ctx.moveTo(p1_x, p1_y);
                    ctx.lineTo(p2_x, p2_y);
                    ctx.lineWidth = 1.5;
                    ctx.strokeStyle = `rgba(255,255,255, ${Math.random() * 0.5 + 0.3})`;
                    ctx.stroke();
                }

                ctx.globalAlpha = 1.0;
            } else if (effect.type === 'heartwood_growth_ray') {
                if (effect.heartwood && effect.new_point) {
                    const start_x = (effect.heartwood.center_coords.x + 0.5) * cellSize;
                    const start_y = (effect.heartwood.center_coords.y + 0.5) * cellSize;
                    const end_x = (effect.new_point.x + 0.5) * cellSize;
                    const end_y = (effect.new_point.y + 0.5) * cellSize;

                    ctx.beginPath();
                    ctx.moveTo(start_x, start_y);
                    ctx.lineTo(end_x, end_y);
                    ctx.strokeStyle = `rgba(150, 255, 150, ${0.7 * (1 - progress)})`;
                    ctx.lineWidth = 3;
                    ctx.stroke();
                }
            } else if (effect.type === 'point_explosion') {
                ctx.beginPath();
                const startRadius = 5;
                const endRadius = 15;
                const currentRadius = startRadius + (endRadius - startRadius) * progress;
                ctx.arc(
                    (effect.x + 0.5) * cellSize,
                    (effect.y + 0.5) * cellSize,
                    currentRadius,
                    0, 2 * Math.PI
                );
                ctx.fillStyle = `rgba(255, 180, 50, ${1 - progress})`; // Orange-ish fade out
                ctx.fill();
            } else if (effect.type === 'point_implosion') {
                ctx.beginPath();
                const startRadius = 15;
                const endRadius = 3;
                const currentRadius = startRadius - (startRadius - endRadius) * progress;
                ctx.arc(
                    (effect.x + 0.5) * cellSize,
                    (effect.y + 0.5) * cellSize,
                    Math.max(0, currentRadius), // Prevent negative radius
                    0, 2 * Math.PI
                );
                ctx.fillStyle = effect.color || `rgba(200, 180, 255, ${1 - progress})`; // Purple-ish fade out
                ctx.fill();
            } else if (effect.type === 'territory_fade') {
                const team = currentGameState.teams[effect.territory.teamId];
                const triPoints = effect.territory.point_ids.map(id => currentGameState.points[id]);
                if (team && triPoints.length === 3 && triPoints.every(p => p)) {
                    ctx.fillStyle = team.color;
                    ctx.globalAlpha = 0.3 * (1 - progress); // Fade out alpha
                    ctx.beginPath();
                    ctx.moveTo((triPoints[0].x + 0.5) * cellSize, (triPoints[0].y + 0.5) * cellSize);
                    ctx.lineTo((triPoints[1].x + 0.5) * cellSize, (triPoints[1].y + 0.5) * cellSize);
                    ctx.lineTo((triPoints[2].x + 0.5) * cellSize, (triPoints[2].y + 0.5) * cellSize);
                    ctx.closePath();
                    ctx.fill();
                    ctx.globalAlpha = 1.0; // reset alpha
                }
            } else if (effect.type === 'arc_projectile') {
                const startX = (effect.start.x + 0.5) * cellSize;
                const startY = (effect.start.y + 0.5) * cellSize;
                const endX = (effect.end.x + 0.5) * cellSize;
                const endY = (effect.end.y + 0.5) * cellSize;

                // Simple parabolic arc using a quadratic bezier curve
                const controlX = (startX + endX) / 2;
                const controlY = Math.min(startY, endY) - 50; // Arc height

                // Calculate current position along the curve
                const t = progress;
                const currentX = (1 - t) * (1 - t) * startX + 2 * (1 - t) * t * controlX + t * t * endX;
                const currentY = (1 - t) * (1 - t) * startY + 2 * (1 - t) * t * controlY + t * t * endY;
                
                ctx.beginPath();
                ctx.arc(currentX, currentY, 5, 0, 2*Math.PI);
                ctx.fillStyle = `rgba(255, 100, 50, ${1 - progress * 0.5})`;
                ctx.fill();
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
                drawMonoliths(currentGameState);
                drawTrebuchets(currentGameState);
                drawPrisms(currentGameState);
                drawRunes(currentGameState);
                drawConduits(currentGameState);
                drawNexuses(currentGameState);
                drawHeartwoods(currentGameState);
                drawWonders(currentGameState);
                drawRiftSpires(currentGameState);
                drawFissures(currentGameState);
                drawBarricades(currentGameState);
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
    
    const actionVisualsMap = {
        'nova_burst': (details, gameState) => {
            lastActionHighlights.points.add(details.sacrificed_point.id);
            // Pre-calculate particle directions for the effect
            let particles = [];
            for(let i=0; i<20; i++) {
                particles.push({angle: Math.random() * 2 * Math.PI, speed: (150 + Math.random() * 50) * (cellSize/10)});
            }
            visualEffects.push({
                type: 'nova_burst',
                x: details.sacrificed_point.x,
                y: details.sacrificed_point.y,
                radius: (gameState.grid_size * 0.25) * cellSize,
                particles: particles,
                startTime: Date.now(),
                duration: 750
            });
        },
        'add_line': (details, gameState) => {
            lastActionHighlights.lines.add(details.line.id);
            lastActionHighlights.points.add(details.line.p1_id);
            lastActionHighlights.points.add(details.line.p2_id);
            visualEffects.push({
                type: 'new_line', line: details.line, startTime: Date.now(), duration: 500
            });
        },
        'fracture_line': (details, gameState) => {
            visualEffects.push({
                type: 'line_crack',
                old_line: details.old_line,
                new_point: details.new_point,
                color: gameState.teams[details.new_point.teamId].color,
                startTime: Date.now(),
                duration: 800,
            });
            lastActionHighlights.points.add(details.new_point.id);
            lastActionHighlights.lines.add(details.new_line1.id);
            lastActionHighlights.lines.add(details.new_line2.id);
        },
        'convert_point': (details, gameState) => {
            lastActionHighlights.points.add(details.converted_point.id);
            const line = details.sacrificed_line;
            const p1 = gameState.points[line.p1_id];
            const p2 = gameState.points[line.p2_id];
            if (p1 && p2) {
                 const midpoint = {x: (p1.x+p2.x)/2, y: (p1.y+p2.y)/2};
                 visualEffects.push({
                     type: 'energy_spiral',
                     start: midpoint,
                     end: details.converted_point,
                     color: gameState.teams[details.converted_point.teamId].color,
                     startTime: Date.now(),
                     duration: 1000
                 });
            }
        },
        'attack_line': (details, gameState) => {
            lastActionHighlights.lines.add(details.attacker_line.id);
            visualEffects.push({
                type: 'animated_ray',
                p1: details.attack_ray.p1,
                p2: details.attack_ray.p2,
                startTime: Date.now(),
                duration: 600,
                color: details.bypassed_shield ? 'rgba(255, 100, 255, 1.0)' : 'rgba(255, 0, 0, 1.0)'
            });
        },
        'rune_shoot_bisector': (details, gameState) => {
            details.rune_points.forEach(pid => lastActionHighlights.points.add(pid));
            visualEffects.push({
                type: 'animated_ray',
                p1: details.attack_ray.p1,
                p2: details.attack_ray.p2,
                startTime: Date.now(),
                duration: 800,
                color: 'rgba(100, 255, 255, 1.0)',
                lineWidth: 4,
            });
        },
        'rune_area_shield': (details, gameState) => {
            details.rune_points.forEach(pid => lastActionHighlights.points.add(pid));
            const tri_points = details.rune_triangle_ids.map(pid => gameState.points[pid]).filter(p=>p);
            if(tri_points.length === 3) {
                visualEffects.push({
                    type: 'polygon_flash',
                    points: tri_points,
                    color: 'rgba(173, 216, 230, 0.9)', // Light blue shield color
                    startTime: Date.now(),
                    duration: 1000
                });
            }
        },
        'rune_shield_pulse': (details, gameState) => {
            details.rune_points.forEach(pid => lastActionHighlights.points.add(pid));
            visualEffects.push({
                type: 'shield_pulse',
                center: details.pulse_center,
                radius_sq: details.pulse_radius_sq,
                color: `rgba(173, 216, 230, 0.9)`,
                startTime: Date.now(),
                duration: 800,
            });
        },
        'extend_line': (details, gameState) => {
            lastActionHighlights.points.add(details.new_point.id);
            const origin_point = gameState.points[details.origin_point_id];
            if (origin_point) {
                const teamColor = gameState.teams[details.new_point.teamId].color;
                visualEffects.push({
                    type: 'animated_ray',
                    p1: origin_point,
                    p2: details.new_point,
                    startTime: Date.now(),
                    duration: 700,
                    color: details.is_empowered ? 'rgba(255, 255, 255, 1.0)' : teamColor,
                    lineWidth: details.is_empowered ? 5 : 2
                });
            }
            if (details.is_empowered && details.new_line) {
                lastActionHighlights.lines.add(details.new_line.id);
            }
        },
        'shield_line': (details, gameState) => {
            lastActionHighlights.lines.add(details.shielded_line.id);
             visualEffects.push({
                type: 'bastion_formation', // Reusing this for a shield-up effect
                line_ids: [details.shielded_line.id],
                startTime: Date.now(),
                duration: 800
            });
        },
        'claim_territory': (details, gameState) => {
            details.territory.point_ids.forEach(pid => lastActionHighlights.points.add(pid));
            const triPoints = details.territory.point_ids.map(id => gameState.points[id]).filter(Boolean);
            if (triPoints.length === 3) {
                visualEffects.push({
                    type: 'territory_fill',
                    points: triPoints,
                    color: gameState.teams[details.territory.teamId].color,
                    startTime: Date.now(),
                    duration: 1000,
                });
            }
        },
        'create_anchor': (details, gameState) => {
            lastActionHighlights.points.add(details.anchor_point.id);
            if(details.sacrificed_point) {
                 visualEffects.push({
                    type: 'point_implosion',
                    x: details.sacrificed_point.x,
                    y: details.sacrificed_point.y,
                    startTime: Date.now(),
                    duration: 800,
                    color: currentGameState.teams[details.sacrificed_point.teamId]?.color
                });
            }
        },
        'create_whirlpool': (details, gameState) => {
            visualEffects.push({
                type: 'point_implosion',
                x: details.sacrificed_point.x,
                y: details.sacrificed_point.y,
                startTime: Date.now(),
                duration: 1200,
                color: currentGameState.teams[details.sacrificed_point.teamId]?.color || `rgba(150, 220, 255, ${1-0})` // Blueish for water
            });
        },
        'mirror_structure': (details, gameState) => {
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
        },
        'create_orbital': (details, gameState) => {
            lastActionHighlights.points.add(details.center_point_id);
            const center_point = gameState.points[details.center_point_id];

            details.new_points.forEach((p, i) => {
                lastActionHighlights.points.add(p.id);
                visualEffects.push({
                    type: 'energy_spiral',
                    start: center_point,
                    end: p,
                    color: gameState.teams[p.teamId].color,
                    startTime: Date.now() + i * 50, // Stagger start times
                    duration: 800
                });
            });
            details.new_lines.forEach(l => lastActionHighlights.lines.add(l.id));
        },
        'form_bastion': (details, gameState) => {
            visualEffects.push({
                type: 'bastion_formation',
                line_ids: details.line_ids,
                color: gameState.teams[details.bastion.teamId].color,
                startTime: Date.now(),
                duration: 1200
            });
        },
        'form_monolith': (details, gameState) => {
            visualEffects.push({
                type: 'monolith_formation',
                center: details.monolith.center_coords,
                color: gameState.teams[details.monolith.teamId].color,
                startTime: Date.now(),
                duration: 1500
            });
        },
        'chain_lightning': (details, gameState) => {
            details.conduit_point_ids.forEach(pid => lastActionHighlights.points.add(pid));
            visualEffects.push({
                type: 'chain_lightning',
                point_ids: details.conduit_point_ids,
                destroyed_point: details.destroyed_point,
                startTime: Date.now(),
                duration: 1000 // ms
            });
            if (details.destroyed_point) {
                visualEffects.push({
                    type: 'point_explosion',
                    x: details.destroyed_point.x,
                    y: details.destroyed_point.y,
                    startTime: Date.now() + 400, // delayed explosion
                    duration: 500
                });
            }
        },
        'refraction_beam': (details, gameState) => {
            details.prism_point_ids.forEach(pid => lastActionHighlights.points.add(pid));
            visualEffects.push({
                type: 'attack_ray', p1: details.source_ray.p1, p2: details.source_ray.p2, startTime: Date.now(), duration: 1200, color: `rgba(255, 255, 150, ${1-0})`, lineWidth: 2
            });
            visualEffects.push({
                type: 'attack_ray', p1: details.refracted_ray.p1, p2: details.refracted_ray.p2, startTime: Date.now() + 200, duration: 1000, color: `rgba(255, 100, 100, ${1-0})`, lineWidth: 4
            });
        },
        'bastion_pulse': (details, gameState) => {
            const bastion = gameState.bastions[details.bastion_id];
            if(bastion) {
                lastActionHighlights.points.add(bastion.core_id);
                bastion.prong_ids.forEach(pid => lastActionHighlights.points.add(pid));
            }
            visualEffects.push({
                type: 'point_implosion', x: details.sacrificed_prong.x, y: details.sacrificed_prong.y, startTime: Date.now(), duration: 800, color: currentGameState.teams[details.sacrificed_prong.teamId]?.color
            });
        },
        'sentry_zap': (details, gameState) => {
            details.sentry_points.forEach(pid => lastActionHighlights.points.add(pid));
             visualEffects.push({
                type: 'attack_ray', p1: details.attack_ray.p1, p2: details.attack_ray.p2, startTime: Date.now(), duration: 400, color: `rgba(255, 100, 100, ${1-0})`, lineWidth: 2
            });
            visualEffects.push({
                type: 'point_explosion', x: details.destroyed_point.x, y: details.destroyed_point.y, startTime: Date.now(), duration: 600
            });
        },
        'cultivate_heartwood': (details, gameState) => {
            details.sacrificed_points.forEach(p => lastActionHighlights.points.add(p.id));
            visualEffects.push({
                type: 'heartwood_creation', sacrificed_points: details.sacrificed_points, center_coords: details.heartwood.center_coords, startTime: Date.now(), duration: 1500
            });
        },
        'phase_shift': (details, gameState) => {
            const teamColor = gameState.teams[details.sacrificed_line.teamId].color;
            if (details.original_coords) {
                visualEffects.push({
                    type: 'portal_link',
                    p1: details.original_coords,
                    p2: details.new_coords,
                    color: teamColor,
                    startTime: Date.now(),
                    duration: 1000
                });
            }
            lastActionHighlights.points.add(details.moved_point_id);
        },
        'pincer_attack': (details, gameState) => {
            lastActionHighlights.points.add(details.attacker_p1_id);
            lastActionHighlights.points.add(details.attacker_p2_id);
            const p1 = gameState.points[details.attacker_p1_id];
            const p2 = gameState.points[details.attacker_p2_id];
            const target = details.destroyed_point;

            if (p1 && target) {
                 visualEffects.push({ type: 'animated_ray', p1: p1, p2: target, startTime: Date.now(), duration: 500, color: 'rgba(255,0,0,1.0)' });
            }
            if (p2 && target) {
                visualEffects.push({ type: 'animated_ray', p1: p2, p2: target, startTime: Date.now(), duration: 500, color: 'rgba(255,0,0,1.0)' });
            }
            visualEffects.push({ type: 'point_explosion', x: target.x, y: target.y, startTime: Date.now(), duration: 600 });
        },
        'rune_impale': (details, gameState) => {
            details.rune_points.forEach(pid => lastActionHighlights.points.add(pid));
            visualEffects.push({
                type: 'animated_ray',
                p1: details.attack_ray.p1,
                p2: details.attack_ray.p2,
                startTime: Date.now(),
                duration: 500,
                color: 'rgba(255, 100, 255, 1.0)',
                lineWidth: 6,
            });
            // Add explosion effects at intersection points
            details.intersection_points.forEach(p_intersect => {
                visualEffects.push({
                    type: 'point_explosion',
                    x: p_intersect.x,
                    y: p_intersect.y,
                    startTime: Date.now(), // No delay, explode as the beam passes
                    duration: 400
                });
            });
        },
        'territory_strike': (details, gameState) => {
            details.territory_point_ids.forEach(pid => lastActionHighlights.points.add(pid));
            visualEffects.push({
                type: 'attack_ray', p1: details.attack_ray.p1, p2: details.attack_ray.p2, startTime: Date.now(), duration: 900, color: 'rgba(100, 255, 100, 1.0)', lineWidth: 3
            });
            visualEffects.push({
                type: 'point_explosion', x: details.destroyed_point.x, y: details.destroyed_point.y, startTime: Date.now() + 500, duration: 600
            });
        },
        'launch_payload': (details, gameState) => {
            details.trebuchet_points.forEach(pid => lastActionHighlights.points.add(pid));
            const launch_point = gameState.points[details.launch_point_id];
            if (launch_point) {
                visualEffects.push({
                    type: 'arc_projectile', start: launch_point, end: details.destroyed_point, startTime: Date.now(), duration: 1200
                });
            }
            visualEffects.push({
                type: 'point_explosion', x: details.destroyed_point.x, y: details.destroyed_point.y, startTime: Date.now() + 1200, duration: 800
            });
        },
        'form_purifier': (details, gameState) => {
            details.purifier.point_ids.forEach(pid => lastActionHighlights.points.add(pid));
            const points = details.purifier.point_ids.map(pid => gameState.points[pid]).filter(Boolean);
            if(points.length === 5) {
                visualEffects.push({
                    type: 'polygon_flash',
                    points: points,
                    color: 'rgba(255, 255, 220, 1.0)', // Light yellow
                    startTime: Date.now(),
                    duration: 1200
                });
            }
        },
        'purify_territory': (details, gameState) => {
            details.purifier_point_ids.forEach(pid => lastActionHighlights.points.add(pid));
            visualEffects.push({
                type: 'territory_fade', territory: details.cleansed_territory, startTime: Date.now(), duration: 1500
            });
        },
        'build_chronos_spire': (details, gameState) => {
            visualEffects.push({
                type: 'point_implosion', x: details.wonder.coords.x, y: details.wonder.coords.y, startTime: Date.now(), duration: 2000, color: `rgba(255, 255, 150, ${1-0})`
            });
        },
        'form_rift_spire': (details, gameState) => {
            visualEffects.push({
                type: 'point_implosion', x: details.sacrificed_point.x, y: details.sacrificed_point.y, startTime: Date.now(), duration: 1500, color: `rgba(200, 100, 255, ${1-0})`
            });
        },
        'raise_barricade': (details, gameState) => {
            details.rune_points.forEach(pid => lastActionHighlights.points.add(pid));
            visualEffects.push({
                type: 'growing_wall',
                barricade: details.barricade,
                color: gameState.teams[details.barricade.teamId].color,
                startTime: Date.now(),
                duration: 1000
            });
        }
        // 'create_fissure' has no special effect beyond the fissure appearing.
    };
    
    function processActionVisuals(gameState) {
        const details = gameState.last_action_details;
        if (!details || !details.type) return;

        // Process secondary visual events first
        if (details.action_events) {
            details.action_events.forEach(event => {
                if (event.type === 'nexus_detonation') {
                    visualEffects.push({
                        type: 'nexus_detonation',
                        center: event.center,
                        radius_sq: event.radius_sq,
                        color: event.color,
                        startTime: Date.now(),
                        duration: 900 // ms
                    });
                }
            });
        }

        // Clear previous highlights
        clearTimeout(lastActionHighlights.clearTimeout);
        lastActionHighlights.points.clear();
        lastActionHighlights.lines.clear();

        const visualizer = actionVisualsMap[details.type];
        if (visualizer) {
            visualizer(details, gameState);
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

        // Process turn start events for visuals
        if (gameState.new_turn_events && gameState.new_turn_events.length > 0) {
            gameState.new_turn_events.forEach(event => {
                if (event.type === 'heartwood_growth') {
                    visualEffects.push({
                        type: 'heartwood_growth_ray',
                        heartwood: gameState.heartwoods[event.new_point.teamId],
                        new_point: event.new_point,
                        startTime: Date.now(),
                        duration: 1500,
                    });
                } else if (event.type === 'monolith_wave') {
                     visualEffects.push({
                        type: 'monolith_wave',
                        center_coords: event.center_coords,
                        radius_sq: event.radius_sq,
                        startTime: Date.now(),
                        duration: 1200,
                    });
                }
            });
        }
        
        if (isFirstUpdate) {
            // After the first state load, ensure the teams list and controls are correctly rendered
            renderTeamsList();
        }

        processActionVisuals(gameState);

        // UI update functions (don't need to be in every frame)
        updateLog(gameState.game_log, gameState.teams);
        updateInterpretationPanel(gameState);
        updateActionPreview(gameState);
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
    
            // --- Create ALL elements for both modes ---
    
            // Color Box (always visible)
            const colorBox = document.createElement('div');
            colorBox.className = 'team-color-box';
            colorBox.style.backgroundColor = team.color;
            li.appendChild(colorBox);
    
            // --- Normal Display Mode Elements ---
            const teamInfo = document.createElement('div');
            teamInfo.className = 'team-info';
            teamInfo.onclick = () => {
                if (inSetupPhase) {
                    selectedTeamId = teamId;
                    renderTeamsList();
                }
            };
            const teamNameSpan = document.createElement('span');
            teamNameSpan.className = 'team-name';
            teamNameSpan.textContent = team.name;
            teamInfo.appendChild(teamNameSpan);
    
            if (team.trait) {
                const teamTraitSpan = document.createElement('span');
                teamTraitSpan.className = 'team-trait';
                teamTraitSpan.textContent = `(${team.trait})`;
                teamInfo.appendChild(teamTraitSpan);
            }
            li.appendChild(teamInfo);
    
            // --- Edit Mode Elements ---
            const editControls = document.createElement('div');
            editControls.className = 'team-edit-controls';
    
            const editColorInput = document.createElement('input');
            editColorInput.type = 'color';
            editColorInput.value = team.color;
    
            const editNameInput = document.createElement('input');
            editNameInput.type = 'text';
            editNameInput.value = team.name;
            editNameInput.placeholder = 'Team Name';
    
            const editTraitSelect = document.createElement('select');
            const traits = ['Random', 'Balanced', 'Aggressive', 'Expansive', 'Defensive'];
            traits.forEach(traitValue => {
                const option = document.createElement('option');
                option.value = traitValue;
                option.textContent = traitValue;
                if (team.trait === traitValue) {
                    option.selected = true;
                }
                editTraitSelect.appendChild(option);
            });
    
            const saveBtn = document.createElement('button');
            saveBtn.innerHTML = '&#10003;'; // Checkmark
            saveBtn.title = 'Save changes';
            saveBtn.className = 'save-team-btn';
            saveBtn.onclick = () => {
                const newName = editNameInput.value.trim();
                if (newName) {
                    localTeams[teamId].name = newName;
                    localTeams[teamId].color = editColorInput.value;
                    localTeams[teamId].trait = editTraitSelect.value;
                    localTeams[teamId].isEditing = false;
                    renderTeamsList();
                }
            };
    
            const cancelBtn = document.createElement('button');
            cancelBtn.innerHTML = '&times;'; // Cross
            cancelBtn.title = 'Cancel edit';
            cancelBtn.className = 'cancel-team-btn';
            cancelBtn.onclick = () => {
                localTeams[teamId].isEditing = false;
                renderTeamsList();
            };
    
            editControls.append(editColorInput, editNameInput, editTraitSelect, saveBtn, cancelBtn);
            li.appendChild(editControls);
    
            // --- Action Buttons ---
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'team-actions';
            if (inSetupPhase) {
                li.style.cursor = 'pointer';
                const editBtn = document.createElement('button');
                editBtn.innerHTML = '&#9998;'; // Pencil icon
                editBtn.title = 'Edit team';
                editBtn.onclick = () => {
                    Object.values(localTeams).forEach(t => t.isEditing = false);
                    localTeams[teamId].isEditing = true;
                    renderTeamsList();
                };
    
                const deleteBtn = document.createElement('button');
                deleteBtn.innerHTML = '&times;';
                deleteBtn.title = 'Delete team';
                deleteBtn.className = 'delete-team-btn';
                deleteBtn.dataset.teamId = teamId;
    
                actionsDiv.append(editBtn, deleteBtn);
            }
            li.appendChild(actionsDiv);
    
            // --- Set visibility based on state ---
            if (inSetupPhase && team.isEditing) {
                colorBox.style.display = 'none';
                teamInfo.style.display = 'none';
                actionsDiv.style.display = 'none';
                editControls.style.display = 'flex';
            } else {
                colorBox.style.display = 'block';
                teamInfo.style.display = 'flex';
                actionsDiv.style.display = 'flex';
                editControls.style.display = 'none';
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
        const { turn, max_turns, teams, game_phase, interpretation, victory_condition, live_stats, action_in_turn, actions_queue_this_turn, runes, prisms, sentries, conduits, nexuses, bastions, monoliths, wonders, purifiers } = gameState;

        let turnText = `Turn: ${turn} / ${max_turns}`;
        if (game_phase === 'RUNNING' && actions_queue_this_turn && actions_queue_this_turn.length > 0) {
            // Use action_in_turn + 1 for a 1-based count for the user
            turnText += ` (Action ${action_in_turn + 1} / ${actions_queue_this_turn.length})`;
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
                    const allStructures = {
                        'Cross': teamRunes.cross ? teamRunes.cross.length : 0,
                        'V-Rune': teamRunes.v_shape ? teamRunes.v_shape.length : 0,
                        'Prism': (prisms && prisms[teamId]) ? prisms[teamId].length : 0,
                        'Sentry': (sentries && sentries[teamId]) ? sentries[teamId].length : 0,
                        'Conduit': (conduits && conduits[teamId]) ? conduits[teamId].length : 0,
                        'Nexus': (nexuses && nexuses[teamId]) ? nexuses[teamId].length : 0,
                        'Bastion': Object.values(bastions || {}).filter(b => b.teamId === teamId).length,
                        'Monolith': Object.values(monoliths || {}).filter(m => m.teamId === teamId).length,
                        'Trebuchet': (gameState.trebuchets && gameState.trebuchets[teamId]) ? gameState.trebuchets[teamId].length : 0,
                        'Purifier': (purifiers && purifiers[teamId]) ? purifiers[teamId].length : 0,
                        'Rift Spire': Object.values(gameState.rift_spires || {}).filter(s => s.teamId === teamId).length,
                        'Wonder': Object.values(wonders || {}).filter(w => w.teamId === teamId).length
                    };

                    let structureStrings = [];
                    for (const [name, count] of Object.entries(allStructures)) {
                        if (count > 0) {
                            structureStrings.push(`${name}(${count})`);
                        }
                    }

                    if (structureStrings.length > 0) {
                        teamHTML += `<br/><span style="font-size: 0.9em; padding-left: 10px;">Formations: ${structureStrings.join(', ')}</span>`;
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

    function getActionCategory(actionName) {
        if (actionName.startsWith('rune_')) return 'Rune';
        if (actionName.startsWith('expand_')) return 'Expand';
        if (actionName.startsWith('fight_')) return 'Fight';
        if (actionName.startsWith('fortify_') || actionName.startsWith('defend_') || actionName.startsWith('terraform_')) return 'Fortify / Defend';
        if (actionName.startsWith('sacrifice_')) return 'Sacrifice';
        return 'Other';
    }

    function updateActionPreview(gameState) {
        const panel = document.getElementById('action-preview-panel');
        const content = document.getElementById('action-preview-content');
        const showInvalid = document.getElementById('show-invalid-actions').checked;
    
        if (gameState.game_phase !== 'RUNNING' || !gameState.actions_queue_this_turn || gameState.actions_queue_this_turn.length === 0) {
            panel.style.display = 'none';
            return;
        }
        
        panel.style.display = 'block';
        
        const actionIndex = gameState.action_in_turn;
        if (actionIndex >= gameState.actions_queue_this_turn.length) {
            content.innerHTML = '<h5>Turn Over</h5><p>Click "Next Action" to start the new turn.</p>';
            return;
        }
    
        const currentActionInfo = gameState.actions_queue_this_turn[actionIndex];
        const teamId = currentActionInfo.teamId;
    
        const fetchUrl = `/api/game/action_probabilities?teamId=${teamId}&include_invalid=${showInvalid}`;
    
        fetch(fetchUrl)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    content.innerHTML = `<p>Error loading actions for ${data.team_name || 'team'}.</p>`;
                    return;
                }
    
                let html = `<h5 style="border-color:${data.color};">Now: ${data.team_name}'s Turn</h5>`;
    
                const actionGroups = {
                    'Fight': { valid: [], invalid: [] },
                    'Expand': { valid: [], invalid: [] },
                    'Fortify / Defend': { valid: [], invalid: [] },
                    'Sacrifice': { valid: [], invalid: [] },
                    'Rune': { valid: [], invalid: [] },
                };
    
                if (data.valid) {
                    data.valid.forEach(action => {
                        const category = getActionCategory(action.name);
                        if (actionGroups[category]) actionGroups[category].valid.push(action);
                    });
                }
                if (data.invalid) {
                     data.invalid.forEach(action => {
                        const category = getActionCategory(action.name);
                        if (actionGroups[category]) actionGroups[category].invalid.push(action);
                    });
                }
    
                let hasAnyActions = (data.valid && data.valid.length > 0) || (data.invalid && data.invalid.length > 0);

                if (hasAnyActions) {
                     for (const categoryName in actionGroups) {
                        const group = actionGroups[categoryName];
                        if (group.valid.length > 0 || group.invalid.length > 0) {
                            html += `<div class="action-category"><h6>${categoryName}</h6><ul class="action-prob-list">`;
                            group.valid.forEach(action => {
                                html += `
                                    <li>
                                        <span>${action.display_name}</span>
                                        <div class="action-prob-bar-container">
                                            <div class="action-prob-bar" style="width: ${action.probability}%; background-color:${data.color};"></div>
                                        </div>
                                        <span class="action-prob-percent">${action.probability}%</span>
                                    </li>
                                `;
                            });
                            group.invalid.forEach(action => {
                                html += `
                                    <li class="invalid-action" title="${action.reason}">
                                        <span>${action.display_name}</span>
                                        <div class="action-prob-bar-container"></div>
                                    </li>
                                `;
                            });
                            html += '</ul></div>';
                        }
                     }
                } else {
                     html += '<p>No valid actions found. Passing turn.</p>';
                }
    
                content.innerHTML = html;
            })
            .catch(err => {
                console.error("Failed to fetch action probabilities:", err);
                content.innerHTML = `<p>Could not load action preview.</p>`;
            });
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

    document.getElementById('show-invalid-actions').addEventListener('change', () => {
        updateActionPreview(currentGameState);
    });

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

    function showTemporaryButtonFeedback(button, message, duration = 1500) {
        const originalText = button.innerHTML;
        button.innerHTML = message;
        button.disabled = true;
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, duration);
    }

    copyLogBtn.addEventListener('click', () => {
        if (navigator.clipboard) {
            const logEntries = logDiv.querySelectorAll('.log-entry');
            const logText = Array.from(logEntries)
                .map(entry => entry.textContent)
                .reverse() // Entries are prepended, so reverse to get chronological order
                .join('\n');
            navigator.clipboard.writeText(logText).then(() => {
                showTemporaryButtonFeedback(copyLogBtn, 'Copied!');
            }).catch(err => {
                console.error('Failed to copy log: ', err);
                alert('Could not copy log.');
            });
        } else {
            alert('Clipboard API not available in this browser.');
        }
    });
    showHullsToggle.addEventListener('click', () => {
        debugOptions.showHulls = showHullsToggle.checked;
    });

    copyStateBtn.addEventListener('click', async () => {
        if (navigator.clipboard) {
            try {
                // Fetch the latest state to ensure it's current
                const response = await fetch('/api/game/state');
                const gameState = await response.json();
                const stateString = JSON.stringify(gameState, null, 2);
                await navigator.clipboard.writeText(stateString);
                showTemporaryButtonFeedback(copyStateBtn, 'State Copied!');
            } catch (err) {
                console.error('Failed to copy game state: ', err);
                alert('Could not copy game state to clipboard. See console for details.');
            }
        } else {
            alert('Clipboard API not available in this browser.');
        }
    });

    restartServerBtn.addEventListener('click', () => {
        if (!confirm("This will restart the server. The page will reload after a few seconds. Are you sure?")) {
            return;
        }

        // Send the request. We don't care about the response because the server will restart and
        // likely interrupt the connection.
        fetch('/api/dev/restart', { method: 'POST' }).catch(err => {
            // This error is expected as the server goes down. We can ignore it.
            console.log("Restart request sent. Fetch failed as expected due to server restart.");
        });

        // Display a message to the user and disable controls
        statusBar.textContent = 'Server is restarting... The page will reload shortly.';
        statusBar.style.opacity = '1';
        document.querySelectorAll('button, input, select').forEach(el => el.disabled = true);


        // Wait a few seconds for the server to come back up, then reload the page.
        setTimeout(() => {
            location.reload();
        }, 5000); // 5 seconds should be enough for the reloader.
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
            const teamId = `team-${Date.now()}`;
            
            localTeams[teamId] = {
                id: teamId,
                name: teamName,
                color: newTeamColorInput.value,
                trait: trait,
                isEditing: false
            };
            
            // Set new random defaults for the next team to be added
            setNewTeamDefaults(); 

            // Auto-select the newly created team
            selectedTeamId = teamId;
            renderTeamsList();

        } else if (teamName) {
            alert('A team with this name already exists.');
        }
    });

    newTeamNameInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTeamBtn.click();
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
        try {
            const response = await fetch('/api/game/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to start game. Server returned ${response.status}: ${errorText}`);
            }
            const gameState = await response.json();
            initialPoints = []; // Clear setup points after game starts
            updateStateAndRender(gameState);
        } catch (error) {
            // Let the global handler catch and display it
            throw error;
        }
    });

    restartSimulationBtn.addEventListener('click', async () => {
        if (!confirm("This will restart the simulation from the beginning with the same setup. Continue?")) {
            return;
        }
        stopAutoPlay();
        try {
            const response = await fetch('/api/game/restart', { method: 'POST' });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to restart game. Server returned ${response.status}: ${errorText}`);
            }
            const gameState = await response.json();
            updateStateAndRender(gameState);
        } catch (error) {
            // Let the global handler catch and display it
            throw error;
        }
    });

    nextActionBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/game/next_action', { method: 'POST' });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to run next action. Server returned ${response.status}: ${errorText}`);
            }
            const gameState = await response.json();
            updateStateAndRender(gameState);
        } catch (error) {
            stopAutoPlay();
            // Let the global handler catch and display it
            throw error;
        }
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
            try {
                const response = await fetch('/api/game/next_action', { method: 'POST' });
                if (!response.ok) {
                    const errorText = await response.text();
                    // Don't throw here, as it would be unhandled inside setInterval.
                    // Instead, stop autoplay and show the error.
                    stopAutoPlay();
                    const errorOverlay = document.getElementById('error-overlay');
                    const errorDetails = document.getElementById('error-details');
                    errorDetails.textContent = `Auto-play stopped. Server Error (${response.status}):\n\n${errorText}`;
                    errorOverlay.style.display = 'flex';
                    return;
                }
                const gameState = await response.json();
                updateStateAndRender(gameState);
                if (gameState.game_phase === 'FINISHED') {
                    stopAutoPlay();
                }
            } catch (error) {
                stopAutoPlay();
                const errorOverlay = document.getElementById('error-overlay');
                const errorDetails = document.getElementById('error-details');
                errorDetails.textContent = `Auto-play stopped. Fetch/Parse Error:\n\n${error.stack}`;
                errorOverlay.style.display = 'flex';
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
                    const gameState = await response.json();
                    
                    // Reset local setup state
                    // The state from the server contains the default teams.
                    localTeams = gameState.teams || {}; 
                    Object.values(localTeams).forEach(t => { t.isEditing = false; }); // Ensure no edit mode
                    initialPoints = []; // Clear points
                    const teamIds = Object.keys(localTeams);
                    if (teamIds.length > 0) {
                        selectedTeamId = teamIds[0];
                    } else {
                        selectedTeamId = null;
                    }
                    
                    // Reset inputs to default
                    gridSizeInput.value = gameState.grid_size;
                    maxTurnsInput.value = gameState.max_turns;
                    setNewTeamDefaults();
    
                    // Update the state cache and render all UI components based on the new state
                    updateStateAndRender(gameState);
                    // Manually call renderTeamsList because it's only called on first update inside updateStateAndRender
                    renderTeamsList(); 
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

    function setupErrorHandling() {
        const errorOverlay = document.getElementById('error-overlay');
        const errorDetails = document.getElementById('error-details');
        const copyErrorBtn = document.getElementById('copy-error-btn');
        const closeErrorBtn = document.getElementById('close-error-btn');
    
        window.onerror = function (message, source, lineno, colno, error) {
            // Stop any game loops
            stopAutoPlay();
            
            const errorText = `Error: ${message}\nSource: ${source}\nLine: ${lineno}, Column: ${colno}\nStack: ${error ? error.stack : 'N/A'}`;
            errorDetails.textContent = errorText;
            errorOverlay.style.display = 'flex';
            return true; // Prevents the default browser error handling
        };
        
        // Also catch promise rejections
        window.addEventListener('unhandledrejection', event => {
            stopAutoPlay();
            const errorText = `Unhandled Promise Rejection:\nReason: ${event.reason.stack || event.reason}`;
            errorDetails.textContent = errorText;
            errorOverlay.style.display = 'flex';
        });
    
        closeErrorBtn.addEventListener('click', () => {
            errorOverlay.style.display = 'none';
        });
    
        copyErrorBtn.addEventListener('click', () => {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(errorDetails.textContent).then(() => {
                    showTemporaryButtonFeedback(copyErrorBtn, 'Copied!', 1000);
                }).catch(err => {
                    alert('Could not copy error details.');
                });
            }
        });
    }

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
        setNewTeamDefaults();
        setupErrorHandling();

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