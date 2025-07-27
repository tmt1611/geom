/**
 * renderer.js
 * 
 * Encapsulates all canvas drawing logic for the game.
 * It's designed as an IIFE to create a singleton renderer object.
 */
const renderer = (() => {
    let ctx;
    let canvas;
    let cellSize;

    // --- Private Drawing Functions ---

    function drawGrid(gridSize) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = '#e0e0e0';
        const totalGridSize = gridSize * cellSize;

        for (let i = 0; i <= gridSize; i++) {
            const pos = i * cellSize;
            ctx.beginPath();
            ctx.moveTo(pos, 0);
            ctx.lineTo(pos, totalGridSize);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(0, pos);
            ctx.lineTo(totalGridSize, pos);
            ctx.stroke();
        }
    }

    const pointRenderers = {
        'is_bastion_core': (p, cx, cy, radius) => {
            const squareSize = radius * 2.5;
            ctx.rect(cx - squareSize / 2, cy - squareSize / 2, squareSize, squareSize);
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();
        },
        'is_bastion_prong': (p, cx, cy, radius) => {
            const squareSize = radius * 1.5;
            ctx.rect(cx - squareSize / 2, cy - squareSize / 2, squareSize, squareSize);
            ctx.fill();
        },
        'is_fortified': (p, cx, cy, radius) => {
            const size = radius * 1.7;
            ctx.moveTo(cx, cy - size); ctx.lineTo(cx + size, cy); ctx.lineTo(cx, cy + size); ctx.lineTo(cx - size, cy);
            ctx.closePath();
            ctx.fill();
        },
        'is_sentry_eye': (p, cx, cy, radius) => {
            ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
            ctx.fill();
            ctx.fillStyle = '#fff';
            ctx.beginPath();
            ctx.arc(cx, cy, radius * 0.4, 0, 2 * Math.PI);
            ctx.fill();
        },
        'is_sentry_post': (p, cx, cy, radius) => {
            ctx.arc(cx, cy, radius * 0.7, 0, 2 * Math.PI);
            ctx.fill();
        },
        'is_monolith_point': (p, cx, cy, radius) => {
            const w = radius * 0.8; const h = radius * 2.5;
            ctx.rect(cx - w / 2, cy - h / 2, w, h);
            ctx.fill();
        },
        'is_purifier_point': (p, cx, cy, radius) => {
            const spikes = 5; const outerRadius = radius * 2.2; const innerRadius = radius * 1.1;
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
        },
        'is_trebuchet_point': (p, cx, cy, radius) => {
            const pointCount = 5;
            ctx.moveTo(cx + radius, cy);
            for (let i = 1; i <= pointCount; i++) ctx.lineTo(cx + radius * Math.cos(i * 2 * Math.PI / pointCount), cy + radius * Math.sin(i * 2 * Math.PI / pointCount));
            ctx.closePath();
            ctx.fill();
        },
        'is_anchor': (p, cx, cy, radius) => {
            const squareSize = radius * 1.8;
            ctx.rect(cx - squareSize / 2, cy - squareSize / 2, squareSize, squareSize);
            ctx.fill();
        },
        'is_nexus_point': (p, cx, cy, radius) => {
            ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
            ctx.fill();
            ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
            ctx.beginPath();
            ctx.arc(cx, cy, radius * 0.5, 0, 2 * Math.PI);
            ctx.fill();
        },
        'default': (p, cx, cy, radius) => {
            ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
            ctx.fill();
        }
    };

    function drawPoints(pointsDict, teams, isHighlightingActive, uiState) {
        if (!pointsDict) return;
        Object.values(pointsDict).forEach(p => {
            const team = teams[p.teamId];
            if (team) {
                const isHighlighted = uiState.lastActionHighlights.points.has(p.id);

                ctx.save();
                if (isHighlightingActive && !isHighlighted) {
                    ctx.globalAlpha = 0.2;
                }

                const cx = (p.x + 0.5) * cellSize;
                const cy = (p.y + 0.5) * cellSize;
                let radius = p.is_anchor ? 7 : 5;

                if (isHighlightingActive && isHighlighted) {
                    ctx.globalAlpha = 1.0;
                    ctx.fillStyle = 'rgba(255, 255, 0, 0.8)';
                    ctx.beginPath(); ctx.arc(cx, cy, radius + 5, 0, 2 * Math.PI); ctx.fill();
                }

                if (p.is_anchor) {
                    const pulse = Math.abs(Math.sin(Date.now() / 1500));
                    ctx.beginPath(); ctx.arc(cx, cy, radius + 4 + (pulse * 4), 0, 2 * Math.PI);
                    ctx.strokeStyle = `rgba(200, 200, 255, ${0.7 - (pulse * 0.5)})`;
                    ctx.lineWidth = 3; ctx.stroke();
                }
                if (p.is_conduit_point) {
                    ctx.fillStyle = `rgba(200, 230, 255, 0.7)`;
                    ctx.beginPath(); ctx.arc(cx, cy, radius + 3, 0, 2 * Math.PI); ctx.fill();
                }

                ctx.fillStyle = team.color;
                ctx.beginPath();

                let rendered = false;
                const render_order = [
                    'is_bastion_core', 'is_purifier_point', 'is_sentry_eye', 'is_bastion_prong', 'is_monolith_point',
                    'is_fortified', 'is_sentry_post', 'is_trebuchet_point', 'is_anchor', 'is_nexus_point'
                ];
                for (const key of render_order) {
                    if (p[key]) {
                        pointRenderers[key](p, cx, cy, radius);
                        rendered = true;
                        break;
                    }
                }
                if (!rendered) {
                    pointRenderers['default'](p, cx, cy, radius);
                }

                if (p.is_in_stasis) {
                    const pulse = Math.abs(Math.sin(Date.now() / 400));
                    ctx.strokeStyle = `rgba(150, 220, 255, ${0.5 + pulse * 0.4})`;
                    ctx.lineWidth = 1.5;
                    const cage_radius = radius + 3;
                    ctx.beginPath(); ctx.moveTo(cx - cage_radius, cy); ctx.lineTo(cx + cage_radius, cy);
                    ctx.moveTo(cx, cy - cage_radius); ctx.lineTo(cx, cy + cage_radius); ctx.stroke();
                    ctx.beginPath(); ctx.arc(cx, cy, cage_radius, 0, 2 * Math.PI); ctx.stroke();
                }

                if (p.is_isolated) {
                    const pulse = Math.abs(Math.sin(Date.now() / 300));
                    ctx.strokeStyle = `rgba(200, 100, 255, ${0.5 + pulse * 0.4})`;
                    ctx.lineWidth = 2;
                    const cage_r = radius + 4;
                    ctx.beginPath();
                    ctx.moveTo(cx - cage_r, cy - cage_r); ctx.lineTo(cx + cage_r, cy + cage_r);
                    ctx.moveTo(cx - cage_r, cy + cage_r); ctx.lineTo(cx + cage_r, cy - cage_r);
                    ctx.stroke();
                }

                if (uiState.debugOptions.showPointIds) {
                    ctx.fillStyle = '#000'; ctx.font = '10px Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
                    ctx.fillText(p.id, cx, cy - (radius + 2));
                }

                ctx.restore();
            }
        });
    }

    function drawLines(pointsDict, lines, teams, isHighlightingActive, uiState) {
        if (!pointsDict || !lines) return;
        lines.forEach(line => {
            const team = teams[line.teamId];
            if (team) {
                const isHighlighted = uiState.lastActionHighlights.lines.has(line.id);

                ctx.save();
                if (isHighlightingActive && !isHighlighted) {
                    ctx.globalAlpha = 0.2;
                }

                const p1 = pointsDict[line.p1_id];
                const p2 = pointsDict[line.p2_id];
                if (p1 && p2) {
                    const x1 = (p1.x + 0.5) * cellSize;
                    const y1 = (p1.y + 0.5) * cellSize;
                    const x2 = (p2.x + 0.5) * cellSize;
                    const y2 = (p2.y + 0.5) * cellSize;

                    if (isHighlightingActive && isHighlighted) {
                        ctx.globalAlpha = 1.0;
                        ctx.strokeStyle = 'rgba(255, 255, 0, 0.8)';
                        ctx.lineWidth = 8;
                        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
                    }

                    if (line.is_shielded) {
                        ctx.strokeStyle = 'rgba(173, 216, 230, 0.9)';
                        ctx.lineWidth = 6;
                        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
                    }

                    ctx.strokeStyle = team.color;
                    let base_width = line.is_bastion_line ? 4 : 2;
                    if (line.strength > 0) {
                        base_width += line.strength * 1.5;
                        const pulse = Math.abs(Math.sin(Date.now() / 400));
                        ctx.strokeStyle = `rgba(255,255,255, ${pulse * 0.5})`;
                        ctx.lineWidth = base_width + 2;
                        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
                        ctx.strokeStyle = team.color;
                    }
                    ctx.lineWidth = base_width;
                    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();

                    if (uiState.debugOptions.showLineIds && line.id) {
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
                ctx.restore();
            }
        });
    }

    function drawHulls(interpretation, teams, uiState) {
        if (!interpretation || !uiState.debugOptions.showHulls) return;

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
                
                if (hullPoints.length > 2) ctx.closePath();

                ctx.strokeStyle = team.color;
                ctx.lineWidth = 3;
                ctx.setLineDash([5, 5]);
                ctx.stroke();
                ctx.setLineDash([]);
            }
        });
    }

    function drawTerritories(pointsDict, territories, teams, isHighlightingActive, uiState) {
        if (!pointsDict || !territories) return;
        territories.forEach(territory => {
            const isHighlighted = territory.point_ids.every(pid => uiState.lastActionHighlights.points.has(pid));
            
            ctx.save();
            const team = teams[territory.teamId];
            if (team) {
                const triPoints = territory.point_ids.map(id => pointsDict[id]);
                if (triPoints.length === 3 && triPoints.every(p => p)) {
                    ctx.fillStyle = team.color;
                    ctx.globalAlpha = isHighlightingActive ? (isHighlighted ? 0.5 : 0.1) : 0.3;
                    ctx.beginPath();
                    ctx.moveTo((triPoints[0].x + 0.5) * cellSize, (triPoints[0].y + 0.5) * cellSize);
                    ctx.lineTo((triPoints[1].x + 0.5) * cellSize, (triPoints[1].y + 0.5) * cellSize);
                    ctx.lineTo((triPoints[2].x + 0.5) * cellSize, (triPoints[2].y + 0.5) * cellSize);
                    ctx.closePath();
                    ctx.fill();
                }
            }
            ctx.restore();
        });
    }

    function drawMonoliths(gameState, isHighlightingActive, uiState) {
        if (!gameState.monoliths) return;
        for (const monolith of Object.values(gameState.monoliths)) {
            const isHighlighted = monolith.point_ids.every(pid => uiState.lastActionHighlights.points.has(pid));
            ctx.save();
            if (isHighlightingActive) ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;
            const team = gameState.teams[monolith.teamId];
            if (!team) { ctx.restore(); continue; }
            const points = monolith.point_ids.map(pid => gameState.points[pid]).filter(p => p);
            if (points.length !== 4) continue;
            points.sort((a, b) => Math.atan2(a.y - monolith.center_coords.y, a.x - monolith.center_coords.x) - Math.atan2(b.y - monolith.center_coords.y, b.x - monolith.center_coords.x));
            ctx.beginPath();
            ctx.moveTo((points[0].x + 0.5) * cellSize, (points[0].y + 0.5) * cellSize);
            for (let i = 1; i < points.length; i++) ctx.lineTo((points[i].x + 0.5) * cellSize, (points[i].y + 0.5) * cellSize);
            ctx.closePath();
            ctx.fillStyle = team.color;
            ctx.globalAlpha *= 0.15;
            ctx.fill();
            const pulse = Math.abs(Math.sin(Date.now() / 600));
            ctx.globalAlpha = (isHighlightingActive && !isHighlighted ? 0.2 : 1.0) * (0.1 + pulse * 0.2);
            ctx.lineWidth = 1 + pulse;
            ctx.strokeStyle = '#fff';
            ctx.stroke();
            ctx.restore();
        }
    }

    function drawTrebuchets(gameState, isHighlightingActive, uiState) {
        if (!gameState.trebuchets) return;
        for (const teamTrebuchets of Object.values(gameState.trebuchets)) {
            const team = gameState.teams[teamTrebuchets[0]?.teamId];
            if (!team || !teamTrebuchets) continue;
            teamTrebuchets.forEach(trebuchet => {
                const isHighlighted = trebuchet.point_ids.every(pid => uiState.lastActionHighlights.points.has(pid));
                ctx.save();
                if (isHighlightingActive) ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;
                const apex = gameState.points[trebuchet.apex_id];
                const cw = gameState.points[trebuchet.counterweight_id];
                if (apex && cw) {
                    ctx.beginPath();
                    ctx.moveTo((apex.x + 0.5) * cellSize, (apex.y + 0.5) * cellSize);
                    ctx.lineTo((cw.x + 0.5) * cellSize, (cw.y + 0.5) * cellSize);
                    ctx.strokeStyle = team.color;
                    ctx.lineWidth = 4;
                    ctx.globalAlpha *= 0.4;
                    ctx.stroke();
                }
                ctx.restore();
            });
        }
    }

    function drawWhirlpools(gameState, isHighlightingActive, uiState) {
        if (!gameState.whirlpools) return;
        gameState.whirlpools.forEach(wp => {
            const team = gameState.teams[wp.teamId];
            if (!team) return;
            const isHighlighted = uiState.lastActionHighlights.structures.has(wp.id);
            ctx.save();
            if (isHighlightingActive) ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;
            const cx = (wp.coords.x + 0.5) * cellSize;
            const cy = (wp.coords.y + 0.5) * cellSize;
            const radius = Math.sqrt(wp.radius_sq) * cellSize;
            const angle_offset = (Date.now() / 2000) % (2 * Math.PI);
            ctx.translate(cx, cy);
            const num_lines = 12;
            for (let i = 0; i < num_lines; i++) {
                const angle = angle_offset + (i * 2 * Math.PI / num_lines);
                const start_radius = radius * 0.2;
                const end_radius = radius * (1 - (wp.turns_left / 4) * 0.5);
                ctx.beginPath();
                ctx.moveTo(Math.cos(angle) * start_radius, Math.sin(angle) * start_radius);
                ctx.quadraticCurveTo(
                    Math.cos(angle + wp.swirl * 2) * radius * 0.6, Math.sin(angle + wp.swirl * 2) * radius * 0.6,
                    Math.cos(angle + wp.swirl * 4) * end_radius, Math.sin(angle + wp.swirl * 4) * end_radius
                );
                ctx.strokeStyle = team.color;
                ctx.lineWidth = 1.5;
                ctx.globalAlpha *= 0.5 * (wp.turns_left / 4);
                ctx.stroke();
            }
            ctx.restore();
        });
    }

    function drawNexuses(gameState, isHighlightingActive, uiState) {
        const allNexuses = [];
        if (gameState.nexuses) Object.values(gameState.nexuses).flat().forEach(n => allNexuses.push({ ...n, is_attuned: false }));
        if (gameState.attuned_nexuses) Object.values(gameState.attuned_nexuses).forEach(n => allNexuses.push({ ...n, is_attuned: true }));
        if (allNexuses.length === 0) return;
        allNexuses.forEach(nexus => {
            const team = gameState.teams[nexus.teamId];
            if (!team) return;
            const isHighlighted = nexus.point_ids.every(pid => uiState.lastActionHighlights.points.has(pid));
            ctx.save();
            if (isHighlightingActive) ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;
            const points = nexus.point_ids.map(pid => gameState.points[pid]).filter(p => p);
            if (points.length !== 4) return;
            points.sort((a, b) => Math.atan2(a.y - nexus.center.y, a.x - nexus.center.x) - Math.atan2(b.y - nexus.center.y, b.x - nexus.center.x));
            ctx.beginPath();
            ctx.moveTo((points[0].x + 0.5) * cellSize, (points[0].y + 0.5) * cellSize);
            for (let i = 1; i < points.length; i++) ctx.lineTo((points[i].x + 0.5) * cellSize, (points[i].y + 0.5) * cellSize);
            ctx.closePath();
            ctx.fillStyle = team.color;
            ctx.globalAlpha *= (nexus.is_attuned ? 0.35 : 0.25);
            ctx.fill();
            const orb_cx = (nexus.center.x + 0.5) * cellSize;
            const orb_cy = (nexus.center.y + 0.5) * cellSize;
            const pulse = Math.abs(Math.sin(Date.now() / (nexus.is_attuned ? 400 : 800)));
            const glow_radius = (nexus.is_attuned ? 15 : 10) + pulse * 5;
            const gradient = ctx.createRadialGradient(orb_cx, orb_cy, 0, orb_cx, orb_cy, glow_radius);
            gradient.addColorStop(0, `rgba(255, 255, 255, ${0.8 - pulse * 0.3})`);
            gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
            ctx.fillStyle = gradient;
            ctx.globalAlpha = isHighlightingActive && !isHighlighted ? 0.2 : 1.0;
            ctx.beginPath(); ctx.arc(orb_cx, orb_cy, glow_radius, 0, 2 * Math.PI); ctx.fill();
            ctx.fillStyle = team.color;
            ctx.beginPath(); ctx.arc(orb_cx, orb_cy, (nexus.is_attuned ? 6 : 4) + pulse * 2, 0, 2 * Math.PI); ctx.fill();
            if (nexus.is_attuned) {
                ctx.beginPath(); ctx.arc(orb_cx, orb_cy, Math.sqrt(nexus.radius_sq) * cellSize, 0, 2 * Math.PI);
                ctx.strokeStyle = team.color;
                ctx.globalAlpha *= 0.1 + pulse * 0.15;
                ctx.lineWidth = 1 + pulse * 2;
                ctx.stroke();
            }
            ctx.restore();
        });
    }

    function drawRiftSpires(gameState, isHighlightingActive, uiState) {
        if (!gameState.rift_spires) return;
        for (const spire of Object.values(gameState.rift_spires)) {
            const team = gameState.teams[spire.teamId];
            if (!team) continue;
            const isHighlighted = uiState.lastActionHighlights.structures.has(spire.id);
            ctx.save();
            if (isHighlightingActive) ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;
            const cx = (spire.coords.x + 0.5) * cellSize;
            const cy = (spire.coords.y + 0.5) * cellSize;
            const now = Date.now();
            const rotation = (now / 4000) % (2 * Math.PI);
            const pulse = Math.abs(Math.sin(now / 300));
            const charge_level = spire.charge / spire.charge_needed;
            ctx.translate(cx, cy); ctx.rotate(rotation);
            ctx.beginPath();
            const spikes = 7; const outerRadius = 12 + pulse * 2; const innerRadius = 6;
            for (let i = 0; i < spikes * 2; i++) {
                const radius = i % 2 === 0 ? outerRadius : innerRadius;
                const angle = (i * Math.PI) / spikes;
                ctx.lineTo(Math.cos(angle) * radius, Math.sin(angle) * radius);
            }
            ctx.closePath();
            ctx.fillStyle = team.color;
            ctx.fill();
            if (charge_level < 1) {
                ctx.strokeStyle = `rgba(255, 255, 255, 0.5)`;
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.arc(0, 0, outerRadius + 2, -Math.PI/2, -Math.PI/2 + (2*Math.PI * charge_level), false);
                ctx.stroke();
            } else {
                ctx.fillStyle = `rgba(255, 255, 255, ${pulse * 0.3})`;
                ctx.fill();
            }
            ctx.restore();
        }
    }

    function drawRiftTraps(gameState, isHighlightingActive, uiState) {
        if (!gameState.rift_traps) return;
        gameState.rift_traps.forEach(trap => {
            const team = gameState.teams[trap.teamId];
            if (!team) return;
            const isHighlighted = uiState.lastActionHighlights.structures.has(trap.id);
            ctx.save();
            if (isHighlightingActive) ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;
            const cx = (trap.coords.x + 0.5) * cellSize;
            const cy = (trap.coords.y + 0.5) * cellSize;
            const flicker = (Math.sin(Date.now() / 100) + Math.sin(Date.now() / 237)) / 2;
            const radius = Math.sqrt(trap.radius_sq) * cellSize;
            ctx.globalAlpha *= 0.3 + flicker * 0.4;
            ctx.strokeStyle = team.color;
            ctx.lineWidth = 1.5;
            ctx.beginPath(); ctx.arc(cx, cy, radius, 0.2, Math.PI - 0.2); ctx.stroke();
            ctx.beginPath(); ctx.arc(cx, cy, radius, Math.PI + 0.2, 2 * Math.PI - 0.2); ctx.stroke();
            ctx.restore();
        });
    }

    function drawScorchedZones(gameState) {
        if (!gameState.scorched_zones) return;
        gameState.scorched_zones.forEach(zone => {
            ctx.save();
            const triPoints = zone.points;
            if (triPoints && triPoints.length === 3) {
                ctx.beginPath();
                ctx.moveTo((triPoints[0].x + 0.5) * cellSize, (triPoints[0].y + 0.5) * cellSize);
                ctx.lineTo((triPoints[1].x + 0.5) * cellSize, (triPoints[1].y + 0.5) * cellSize);
                ctx.lineTo((triPoints[2].x + 0.5) * cellSize, (triPoints[2].y + 0.5) * cellSize);
                ctx.closePath();
                ctx.fillStyle = `rgba(50, 50, 50, ${0.4 + (zone.turns_left / 5) * 0.2})`;
                ctx.fill();
                ctx.strokeStyle = `rgba(200, 80, 0, ${0.5 + (zone.turns_left / 5) * 0.3})`;
                ctx.lineWidth = 2;
                // Uses global illustrationHelpers
                illustrationHelpers.drawJaggedLine(ctx,
                    {x: (triPoints[0].x + 0.5) * cellSize, y: (triPoints[0].y + 0.5) * cellSize},
                    {x: (triPoints[1].x + 0.5) * cellSize, y: (triPoints[1].y + 0.5) * cellSize}, 10, 3 );
                illustrationHelpers.drawJaggedLine(ctx,
                    {x: (triPoints[1].x + 0.5) * cellSize, y: (triPoints[1].y + 0.5) * cellSize},
                    {x: (triPoints[2].x + 0.5) * cellSize, y: (triPoints[2].y + 0.5) * cellSize}, 10, 3 );
                illustrationHelpers.drawJaggedLine(ctx,
                    {x: (triPoints[2].x + 0.5) * cellSize, y: (triPoints[2].y + 0.5) * cellSize},
                    {x: (triPoints[0].x + 0.5) * cellSize, y: (triPoints[0].y + 0.5) * cellSize}, 10, 3 );
            }
            ctx.restore();
        });
    }

    function drawBarricades(gameState, isHighlightingActive, uiState) {
        if (!gameState.barricades) return;
        gameState.barricades.forEach(barricade => {
            const team = gameState.teams[barricade.teamId];
            if (!team) return;
            const isHighlighted = uiState.lastActionHighlights.structures.has(barricade.id);
            ctx.save();
            if (isHighlightingActive) ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;
            const p1 = {x: (barricade.p1.x + 0.5) * cellSize, y: (barricade.p1.y + 0.5) * cellSize};
            const p2 = {x: (barricade.p2.x + 0.5) * cellSize, y: (barricade.p2.y + 0.5) * cellSize};
            ctx.strokeStyle = team.color;
            ctx.globalAlpha *= (0.5 + (barricade.turns_left / 5) * 0.5);
            ctx.lineWidth = 6;
            ctx.lineCap = 'round';
            illustrationHelpers.drawJaggedLine(ctx, p1, p2, 10, 4);
            ctx.globalAlpha *= 0.8;
            ctx.lineWidth = 2;
            ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
            ctx.lineCap = 'butt';
            ctx.restore();
        });
    }

    function drawLeyLines(gameState, isHighlightingActive, uiState) {
        if (!gameState.ley_lines) return;
        for (const ley_line of Object.values(gameState.ley_lines)) {
            const team = gameState.teams[ley_line.teamId];
            if (!team) continue;
            const isHighlighted = ley_line.point_ids.every(pid => uiState.lastActionHighlights.points.has(pid));
            ctx.save();
            if (isHighlightingActive) ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;
            const points = ley_line.point_ids.map(pid => gameState.points[pid]).filter(p => p);
            if (points.length < 2) { ctx.restore(); continue; }
            const p1 = points[0], p2 = points[points.length - 1];
            const x1 = (p1.x + 0.5) * cellSize, y1 = (p1.y + 0.5) * cellSize;
            const x2 = (p2.x + 0.5) * cellSize, y2 = (p2.y + 0.5) * cellSize;
            const pulse = Math.abs(Math.sin(Date.now() / 600));
            ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
            ctx.strokeStyle = team.color;
            ctx.lineWidth = 10 + pulse * 4;
            ctx.globalAlpha *= (0.3 + pulse * 0.2);
            ctx.filter = 'blur(5px)';
            ctx.stroke();
            ctx.restore();
        }
    }

    function drawWonders(gameState, isHighlightingActive, uiState) {
        if (!gameState.wonders) return;
        for (const wonder of Object.values(gameState.wonders)) {
            const team = gameState.teams[wonder.teamId];
            if (!team || wonder.type !== 'ChronosSpire') continue;
            const isHighlighted = uiState.lastActionHighlights.structures.has(wonder.id);
            ctx.save();
            if (isHighlightingActive) ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;
            const cx = (wonder.coords.x + 0.5) * cellSize;
            const cy = (wonder.coords.y + 0.5) * cellSize;
            const now = Date.now();
            const pulse = Math.abs(Math.sin(now / 500));
            const rotation = (now / 5000) % (2 * Math.PI);
            const baseRadius = 20;
            const currentAlpha = ctx.globalAlpha;
            const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, baseRadius);
            gradient.addColorStop(0, team.color + "99"); gradient.addColorStop(1, team.color + "00");
            ctx.fillStyle = gradient;
            ctx.globalAlpha = currentAlpha * (0.3 + pulse * 0.2);
            ctx.beginPath(); ctx.arc(cx, cy, baseRadius, 0, 2 * Math.PI); ctx.fill();
            ctx.save();
            ctx.translate(cx, cy); ctx.rotate(rotation);
            ctx.strokeStyle = team.color; ctx.lineWidth = 1.5; ctx.globalAlpha = currentAlpha * 0.8;
            ctx.beginPath(); ctx.arc(0, 0, baseRadius * 0.7, 0, 2 * Math.PI); ctx.stroke();
            ctx.rotate(Math.PI / 2);
            ctx.beginPath(); ctx.arc(0, 0, baseRadius * 1.2, 0, 1.5 * Math.PI); ctx.stroke();
            ctx.restore();
            ctx.beginPath(); ctx.arc(cx, cy, 5 + pulse * 2, 0, 2 * Math.PI); ctx.fillStyle = '#fff'; ctx.fill();
            ctx.beginPath(); ctx.arc(cx, cy, 2 + pulse, 0, 2 * Math.PI); ctx.fillStyle = team.color; ctx.fill();
            ctx.fillStyle = '#fff'; ctx.font = 'bold 14px Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.shadowColor = 'black'; ctx.shadowBlur = 4;
            ctx.fillText(wonder.turns_to_victory, cx, cy); ctx.shadowBlur = 0;
            ctx.restore();
        }
    }

    function drawPrisms(gameState, isHighlightingActive, uiState) {
        if (!gameState.prisms) return;
        for (const teamPrisms of Object.values(gameState.prisms)) {
            teamPrisms.forEach(prism => {
                const team = gameState.teams[prism.teamId];
                if (!team) return;
                const isHighlighted = prism.all_point_ids.every(pid => uiState.lastActionHighlights.points.has(pid));
                ctx.save();
                if (isHighlightingActive) ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;
                const p1 = gameState.points[prism.shared_p1_id];
                const p2 = gameState.points[prism.shared_p2_id];
                if (p1 && p2) {
                    const x1 = (p1.x + 0.5) * cellSize; const y1 = (p1.y + 0.5) * cellSize;
                    const x2 = (p2.x + 0.5) * cellSize; const y2 = (p2.y + 0.5) * cellSize;
                    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
                    ctx.strokeStyle = team.color; ctx.lineWidth = 8;
                    ctx.globalAlpha *= 0.5; ctx.filter = 'blur(4px)'; ctx.stroke();
                    ctx.filter = 'none';
                }
                ctx.restore();
            });
        }
    }
    
    function drawHeartwoods(gameState, isHighlightingActive, uiState) {
        if (!gameState.heartwoods) return;
        for (const heartwood of Object.values(gameState.heartwoods)) {
            const team = gameState.teams[heartwood.teamId];
            if (!team) continue;
            const isHighlighted = uiState.lastActionHighlights.structures.has(heartwood.id);
            ctx.save();
            if (isHighlightingActive) ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;
            const cx = (heartwood.center_coords.x + 0.5) * cellSize;
            const cy = (heartwood.center_coords.y + 0.5) * cellSize;
            const pulse = Math.abs(Math.sin(Date.now() / 800));
            const aura_radius = Math.sqrt(heartwood.aura_radius_sq) * cellSize;
            ctx.beginPath(); ctx.arc(cx, cy, aura_radius, 0, 2 * Math.PI);
            ctx.fillStyle = team.color;
            ctx.globalAlpha *= (0.1 + pulse * 0.1);
            ctx.fill();
            ctx.globalAlpha = isHighlightingActive && !isHighlighted ? 0.2 : 1.0;
            ctx.beginPath(); ctx.arc(cx, cy, 15, 0, 2 * Math.PI); ctx.fillStyle = team.color; ctx.fill();
            ctx.font = 'bold 24px Arial'; ctx.fillStyle = 'white'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText('❤', cx, cy + 1);
            ctx.restore();
        }
    }
    
    const runeDrawers = {
        'barricade': (rune, team, gameState) => {
            const points = rune.point_ids.map(pid => gameState.points[pid]).filter(p => p);
            if (points.length !== 4) return;
            const centroid = { x: points.reduce((acc, p) => acc + p.x, 0) / 4, y: points.reduce((acc, p) => acc + p.y, 0) / 4 };
            points.sort((a, b) => Math.atan2(a.y - centroid.y, a.x - centroid.x) - Math.atan2(b.y - centroid.y, b.x - centroid.x));
            ctx.beginPath();
            ctx.moveTo((points[0].x + 0.5) * cellSize, (points[0].y + 0.5) * cellSize);
            for (let i = 1; i < points.length; i++) ctx.lineTo((points[i].x + 0.5) * cellSize, (points[i].y + 0.5) * cellSize);
            ctx.closePath();
            ctx.strokeStyle = team.color; ctx.lineWidth = 6; ctx.globalAlpha *= 0.4; ctx.stroke();
        },
        'cross': (rune_p_ids, team, gameState) => {
            const points = rune_p_ids.map(pid => gameState.points[pid]).filter(p => p);
            if (points.length !== 4) return;
            const centroid = { x: points.reduce((acc, p) => acc + p.x, 0) / 4, y: points.reduce((acc, p) => acc + p.y, 0) / 4 };
            points.sort((a, b) => Math.atan2(a.y - centroid.y, a.x - centroid.x) - Math.atan2(b.y - centroid.y, b.x - centroid.x));
            ctx.beginPath();
            ctx.moveTo((points[0].x + 0.5) * cellSize, (points[0].y + 0.5) * cellSize);
            for (let i = 1; i < points.length; i++) ctx.lineTo((points[i].x + 0.5) * cellSize, (points[i].y + 0.5) * cellSize);
            ctx.closePath();
            ctx.fillStyle = team.color; ctx.globalAlpha *= 0.2; ctx.fill();
        },
        'hourglass': (rune, team, gameState) => {
            const all_points = rune.all_points.map(pid => gameState.points[pid]);
            const p_v = all_points.find(p => p && p.id === rune.vertex_id);
            if (!p_v || all_points.some(p => !p)) return;
            const tri1_pts = all_points.filter(p => p.id !== p_v.id).slice(0, 2);
            const tri2_pts = all_points.filter(p => p.id !== p_v.id).slice(2, 4);
            if (tri1_pts.length < 2 || tri2_pts.length < 2) return;
            ctx.beginPath();
            ctx.moveTo((tri1_pts[0].x + 0.5) * cellSize, (tri1_pts[0].y + 0.5) * cellSize);
            ctx.lineTo((p_v.x + 0.5) * cellSize, (p_v.y + 0.5) * cellSize);
            ctx.lineTo((tri1_pts[1].x + 0.5) * cellSize, (tri1_pts[1].y + 0.5) * cellSize);
            ctx.moveTo((tri2_pts[0].x + 0.5) * cellSize, (tri2_pts[0].y + 0.5) * cellSize);
            ctx.lineTo((p_v.x + 0.5) * cellSize, (p_v.y + 0.5) * cellSize);
            ctx.lineTo((tri2_pts[1].x + 0.5) * cellSize, (tri2_pts[1].y + 0.5) * cellSize);
            ctx.strokeStyle = team.color; ctx.lineWidth = 6; ctx.globalAlpha *= 0.4; ctx.stroke();
        },
        'parallel': (rune, team, gameState) => {
            const points = rune.point_ids.map(pid => gameState.points[pid]).filter(p => p);
            if (points.length !== 4) return;
            const centroid = { x: points.reduce((acc, p) => acc + p.x, 0) / 4, y: points.reduce((acc, p) => acc + p.y, 0) / 4 };
            points.sort((a, b) => Math.atan2(a.y - centroid.y, a.x - centroid.x) - Math.atan2(b.y - centroid.y, b.x - centroid.x));
            ctx.beginPath();
            ctx.moveTo((points[0].x + 0.5) * cellSize, (points[0].y + 0.5) * cellSize);
            for (let i = 1; i < points.length; i++) ctx.lineTo((points[i].x + 0.5) * cellSize, (points[i].y + 0.5) * cellSize);
            ctx.closePath();
            ctx.fillStyle = team.color; ctx.globalAlpha *= 0.2; ctx.fill();
        },
        'plus_shape': (rune, team, gameState) => {
            const center_p = gameState.points[rune.center_id];
            if (!center_p) return;
            const cx = (center_p.x + 0.5) * cellSize;
            const cy = (center_p.y + 0.5) * cellSize;
            const pulse = Math.abs(Math.sin(Date.now() / 400));
            const radius = 10 + pulse * 5;
            const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
            gradient.addColorStop(0, team.color + "99");
            gradient.addColorStop(1, team.color + "00");
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, 2*Math.PI);
            ctx.fill();
        },
        'shield': (rune, team, gameState) => {
            const tri_points = rune.triangle_ids.map(pid => gameState.points[pid]).filter(p => p);
            if (tri_points.length !== 3) return;
            ctx.beginPath();
            ctx.moveTo((tri_points[0].x + 0.5) * cellSize, (tri_points[0].y + 0.5) * cellSize);
            ctx.lineTo((tri_points[1].x + 0.5) * cellSize, (tri_points[1].y + 0.5) * cellSize);
            ctx.lineTo((tri_points[2].x + 0.5) * cellSize, (tri_points[2].y + 0.5) * cellSize);
            ctx.closePath();
            const currentAlpha = ctx.globalAlpha;
            ctx.fillStyle = team.color; ctx.globalAlpha = currentAlpha * 0.25; ctx.fill();
            const pulse = Math.abs(Math.sin(Date.now() / 500));
            ctx.strokeStyle = '#fff'; ctx.lineWidth = 1 + pulse * 2;
            ctx.globalAlpha = currentAlpha * (0.3 + pulse * 0.4); ctx.stroke();
        },
        'star': (rune, team, gameState) => {
            const center_p = gameState.points[rune.center_id];
            if (!center_p) return;
            const cx = (center_p.x + 0.5) * cellSize;
            const cy = (center_p.y + 0.5) * cellSize;
            const pulse = Math.abs(Math.sin(Date.now() / 400));
            const radius = 15 + pulse * 8;
            const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
            gradient.addColorStop(0, team.color + "AA");
            gradient.addColorStop(1, team.color + "00");
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, 2*Math.PI);
            ctx.fill();
        },
        't_shape': (rune, team, gameState) => {
            const stem_p1 = gameState.points[rune.stem_p1_id];
            const stem_p2 = gameState.points[rune.stem_p2_id];
            if (!stem_p1 || !stem_p2) return;
            ctx.beginPath();
            ctx.moveTo((stem_p1.x + 0.5) * cellSize, (stem_p1.y + 0.5) * cellSize);
            ctx.lineTo((stem_p2.x + 0.5) * cellSize, (stem_p2.y + 0.5) * cellSize);
            ctx.strokeStyle = team.color;
            ctx.lineWidth = 6;
            ctx.globalAlpha *= 0.5;
            ctx.stroke();
        },
        'trident': (rune, team, gameState) => {
            const [p_apex, p_h, p_p1, p_p2] = [rune.apex_id, rune.handle_id, ...rune.prong_ids].map(id => gameState.points[id]);
            if (!p_apex || !p_h || !p_p1 || !p_p2) return;
            ctx.beginPath();
            ctx.moveTo((p_h.x + 0.5) * cellSize, (p_h.y + 0.5) * cellSize);
            ctx.lineTo((p_apex.x + 0.5) * cellSize, (p_apex.y + 0.5) * cellSize);
            ctx.moveTo((p_p1.x + 0.5) * cellSize, (p_p1.y + 0.5) * cellSize);
            ctx.lineTo((p_apex.x + 0.5) * cellSize, (p_apex.y + 0.5) * cellSize);
            ctx.lineTo((p_p2.x + 0.5) * cellSize, (p_p2.y + 0.5) * cellSize);
            ctx.strokeStyle = team.color; ctx.lineWidth = 8; ctx.globalAlpha *= 0.4;
            ctx.filter = 'blur(2px)'; ctx.stroke(); ctx.filter = 'none';
        },
        'v_shape': (rune, team, gameState) => {
            const [p_v, p_l1, p_l2] = [rune.vertex_id, rune.leg1_id, rune.leg2_id].map(id => gameState.points[id]);
            if (!p_v || !p_l1 || !p_l2) return;
            ctx.beginPath();
            ctx.moveTo((p_l1.x + 0.5) * cellSize, (p_l1.y + 0.5) * cellSize);
            ctx.lineTo((p_v.x + 0.5) * cellSize, (p_v.y + 0.5) * cellSize);
            ctx.lineTo((p_l2.x + 0.5) * cellSize, (p_l2.y + 0.5) * cellSize);
            ctx.strokeStyle = team.color; ctx.lineWidth = 6; ctx.globalAlpha *= 0.4; ctx.stroke();
        }
    };

    function drawRunes(gameState, isHighlightingActive, uiState) {
        if (!gameState.runes) return;
        for (const [teamId, teamRunes] of Object.entries(gameState.runes)) {
            const team = gameState.teams[teamId];
            if (!team) continue;
            for (const [runeType, runes] of Object.entries(teamRunes)) {
                const drawer = runeDrawers[runeType];
                if (!drawer) continue;
                runes.forEach(rune => {
                    const pointIds = rune.point_ids || rune.all_points || (Array.isArray(rune) ? rune : null);
                    if (!pointIds) return;
                    const isHighlighted = pointIds.every(pid => uiState.lastActionHighlights.points.has(pid));
                    ctx.save();
                    if (isHighlightingActive) ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;
                    drawer(rune, team, gameState);
                    ctx.restore();
                });
            }
        }
    }
    
    function drawFissures(gameState, isHighlightingActive, uiState) {
        if (!gameState.fissures) return;
        gameState.fissures.forEach(fissure => {
            const isHighlighted = uiState.lastActionHighlights.structures.has(fissure.id);
            ctx.save();
            if (isHighlightingActive) ctx.globalAlpha = isHighlighted ? 1.0 : 0.2;
            const p1 = {x: (fissure.p1.x + 0.5) * cellSize, y: (fissure.p1.y + 0.5) * cellSize};
            const p2 = {x: (fissure.p2.x + 0.5) * cellSize, y: (fissure.p2.y + 0.5) * cellSize};
            ctx.strokeStyle = `rgba(30, 30, 30, ${0.4 + (fissure.turns_left / 8) * 0.4})`;
            ctx.lineWidth = 4;
            ctx.lineCap = 'round';
            illustrationHelpers.drawJaggedLine(ctx, p1, p2, 15, 6);
            ctx.lineCap = 'butt';
            ctx.restore();
        });
    }

    function drawVisualEffects(uiState, gameState) {
        if (!uiState.visualEffects || !uiState.visualEffects.length) return;
    
        const now = Date.now();
        // Filter out expired effects. This is important to prevent memory leaks.
        uiState.visualEffects = uiState.visualEffects.filter(effect => now < effect.startTime + effect.duration);
        
        ctx.save();
        uiState.visualEffects.forEach(effect => {
            const progress = Math.min(1, (now - effect.startTime) / effect.duration);
            if (progress < 0) return;
    
            const easeOutQuad = t => t * (2 - t);
            const easeInQuad = t => t * t;
            const easedProgress = easeOutQuad(progress);
    
            switch (effect.type) {
                case 'jagged_ray': {
                    const p1 = { x: (effect.p1.x + 0.5) * cellSize, y: (effect.p1.y + 0.5) * cellSize };
                    const p2_full = { x: (effect.p2.x + 0.5) * cellSize, y: (effect.p2.y + 0.5) * cellSize };
                    const p2_current = {
                        x: p1.x + (p2_full.x - p1.x) * progress,
                        y: p1.y + (p2_full.y - p1.y) * progress,
                    };
                    ctx.strokeStyle = effect.color || 'yellow';
                    ctx.lineWidth = effect.lineWidth || 2;
                    ctx.globalAlpha = 1 - easeInQuad(progress);
                    illustrationHelpers.drawJaggedLine(ctx, p1, p2_current, 7, 10);
                    break;
                }
                case 'animated_ray':
                case 'attack_ray': {
                    const p1 = { x: (effect.p1.x + 0.5) * cellSize, y: (effect.p1.y + 0.5) * cellSize };
                    const p2_full = { x: (effect.p2.x + 0.5) * cellSize, y: (effect.p2.y + 0.5) * cellSize };
                    const p2_current = {
                        x: p1.x + (p2_full.x - p1.x) * progress,
                        y: p1.y + (p2_full.y - p1.y) * progress,
                    };
                    ctx.strokeStyle = effect.color || 'red';
                    ctx.lineWidth = effect.lineWidth || 2;
                    ctx.globalAlpha = 1 - easeInQuad(progress);
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2_current.x, p2_current.y);
                    ctx.stroke();
                    break;
                }
                case 'point_explosion': {
                    const cx = (effect.x + 0.5) * cellSize;
                    const cy = (effect.y + 0.5) * cellSize;
                    const radius = (10 + 20 * easedProgress) * (cellSize/10);
                    ctx.fillStyle = `rgba(255, 0, 0, ${1 - easedProgress})`;
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
                    ctx.fill();
                    break;
                }
                case 'point_formation': {
                    const cx = (effect.x + 0.5) * cellSize;
                    const cy = (effect.y + 0.5) * cellSize;
                    const radius = (15 * easedProgress) * (cellSize/10);
                    ctx.fillStyle = effect.color;
                    ctx.globalAlpha = 1 - easedProgress;
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
                    ctx.fill();
                    break;
                }
                case 'point_implosion': {
                    const cx = (effect.x + 0.5) * cellSize;
                    const cy = (effect.y + 0.5) * cellSize;
                    const radius = (30 * (1 - easedProgress)) * (cellSize/10);
                    ctx.strokeStyle = effect.color || `rgba(255, 255, 255, 1)`;
                    ctx.lineWidth = 3;
                    ctx.globalAlpha = easedProgress;
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
                    ctx.stroke();
                    break;
                }
                case 'shield_pulse':
                case 'nexus_detonation':
                case 'monolith_wave': {
                    const center = effect.center || effect.center_coords;
                    if (!center) break;
                    const cx = (center.x + 0.5) * cellSize;
                    const cy = (center.y + 0.5) * cellSize;
                    const maxRadius = Math.sqrt(effect.radius_sq) * cellSize;
                    const currentRadius = maxRadius * easedProgress;
    
                    ctx.strokeStyle = effect.color || 'rgba(173, 216, 230, 0.9)';
                    ctx.lineWidth = 4;
                    ctx.globalAlpha = 1 - easedProgress;
                    ctx.beginPath();
                    ctx.arc(cx, cy, currentRadius, 0, 2 * Math.PI);
                    ctx.stroke();
                    break;
                }
                case 'line_flash': {
                    const lines = effect.line ? [effect.line] : (effect.line_ids ? effect.line_ids.map(id => gameState.lines.find(l => l.id === id)).filter(Boolean) : []);
                    if (!gameState || !gameState.points || lines.length === 0) break;
                    lines.forEach(line => {
                        const p1 = gameState.points[line.p1_id];
                        const p2 = gameState.points[line.p2_id];
                        if (p1 && p2) {
                            const x1 = (p1.x + 0.5) * cellSize;
                            const y1 = (p1.y + 0.5) * cellSize;
                            const x2 = (p2.x + 0.5) * cellSize;
                            const y2 = (p2.y + 0.5) * cellSize;
                            ctx.strokeStyle = effect.color || '#fff';
                            ctx.lineWidth = 4 + 6 * (1 - easedProgress);
                            ctx.globalAlpha = 1 - easedProgress;
                            ctx.beginPath();
                            ctx.moveTo(x1, y1);
                            ctx.lineTo(x2, y2);
                            ctx.stroke();
                        }
                    });
                    break;
                }
                case 'growing_wall': {
                    const p1 = { x: (effect.barricade.p1.x + 0.5) * cellSize, y: (effect.barricade.p1.y + 0.5) * cellSize };
                    const p2_full = { x: (effect.barricade.p2.x + 0.5) * cellSize, y: (effect.barricade.p2.y + 0.5) * cellSize };
                    const p2_current = {
                        x: p1.x + (p2_full.x - p1.x) * easedProgress,
                        y: p1.y + (p2_full.y - p1.y) * easedProgress
                    };
                    ctx.strokeStyle = effect.color;
                    ctx.lineWidth = 6;
                    ctx.lineCap = 'round';
                    ctx.globalAlpha = 1 - progress;
                    illustrationHelpers.drawJaggedLine(ctx, p1, p2_current, 10, 4);
                    ctx.lineCap = 'butt';
                    break;
                }
                case 'nova_burst': {
                    const cx = (effect.x + 0.5) * cellSize;
                    const cy = (effect.y + 0.5) * cellSize;
                    // Outer shockwave
                    ctx.strokeStyle = 'rgba(255, 180, 50, 0.9)';
                    ctx.lineWidth = 4;
                    ctx.globalAlpha = 1 - easedProgress;
                    ctx.beginPath();
                    ctx.arc(cx, cy, effect.radius * easedProgress, 0, 2*Math.PI);
                    ctx.stroke();
                    // Particles
                    ctx.fillStyle = 'rgba(255, 255, 150, 0.8)';
                    effect.particles.forEach(p => {
                        const dist = p.speed * progress;
                        ctx.beginPath();
                        ctx.arc(cx + Math.cos(p.angle)*dist, cy + Math.sin(p.angle)*dist, 3, 0, 2*Math.PI);
                        ctx.fill();
                    });
                    break;
                }
                case 'starlight_cascade': {
                    const cx = (effect.center.x + 0.5) * cellSize;
                    const cy = (effect.center.y + 0.5) * cellSize;
                    const maxRadius = effect.radius * cellSize;
                    const currentRadius = maxRadius * easedProgress;

                    // Outer shockwave
                    const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, currentRadius);
                    gradient.addColorStop(0, 'rgba(255, 255, 150, 0)');
                    gradient.addColorStop(0.8, 'rgba(255, 255, 150, 0.5)');
                    gradient.addColorStop(1, 'rgba(255, 255, 150, 0)');
                    ctx.fillStyle = gradient;
                    ctx.globalAlpha = 1 - progress; // fade out the whole effect
                    ctx.beginPath();
                    ctx.arc(cx, cy, currentRadius, 0, 2 * Math.PI);
                    ctx.fill();

                    // Sparkling particles
                    ctx.fillStyle = '#fff';
                    effect.particles.forEach(p => {
                        const flicker = (Math.sin(now / p.flicker_speed) + 1) / 2;
                        if (flicker > 0.5) { // only draw some of the time
                            const dist = p.speed * easedProgress;
                            ctx.beginPath();
                            ctx.arc(cx + Math.cos(p.angle) * dist, cy + Math.sin(p.angle) * dist, flicker * 2, 0, 2 * Math.PI);
                            ctx.fill();
                        }
                    });
                    break;
                }
                case 'new_line': {
                    const p1 = gameState.points[effect.line.p1_id];
                    const p2 = gameState.points[effect.line.p2_id];
                    if(p1 && p2) {
                        const p1_coords = { x: (p1.x + 0.5) * cellSize, y: (p1.y + 0.5) * cellSize };
                        const p2_full = { x: (p2.x + 0.5) * cellSize, y: (p2.y + 0.5) * cellSize };
                        const p2_current = {
                            x: p1_coords.x + (p2_full.x - p1_coords.x) * easedProgress,
                            y: p1_coords.y + (p2_full.y - p1_coords.y) * easedProgress
                        };
                        ctx.strokeStyle = gameState.teams[effect.line.teamId].color;
                        ctx.lineWidth = 2;
                        ctx.globalAlpha = progress;
                        ctx.beginPath();
                        ctx.moveTo(p1_coords.x, p1_coords.y);
                        ctx.lineTo(p2_current.x, p2_current.y);
                        ctx.stroke();
                    }
                    break;
                }
                case 'polygon_flash':
                case 'territory_fill': {
                    if (effect.points && effect.points.length >= 3) {
                        ctx.fillStyle = effect.color;
                        ctx.globalAlpha = (1 - easedProgress) * 0.7;
                        ctx.beginPath();
                        ctx.moveTo((effect.points[0].x + 0.5) * cellSize, (effect.points[0].y + 0.5) * cellSize);
                        for(let i=1; i<effect.points.length; i++) {
                            ctx.lineTo((effect.points[i].x + 0.5) * cellSize, (effect.points[i].y + 0.5) * cellSize);
                        }
                        ctx.closePath();
                        ctx.fill();
                    }
                    break;
                }
                 case 'territory_fade': {
                    const points = effect.territory.point_ids.map(pid => gameState.points[pid]).filter(Boolean);
                    if (points.length === 3) {
                        ctx.fillStyle = gameState.teams[effect.territory.teamId].color;
                        ctx.globalAlpha = (1 - progress) * 0.3; // Fade out
                        ctx.beginPath();
                        ctx.moveTo((points[0].x + 0.5) * cellSize, (points[0].y + 0.5) * cellSize);
                        ctx.lineTo((points[1].x + 0.5) * cellSize, (points[1].y + 0.5) * cellSize);
                        ctx.lineTo((points[2].x + 0.5) * cellSize, (points[2].y + 0.5) * cellSize);
                        ctx.closePath();
                        ctx.fill();
                    }
                    break;
                }
                case 'arc_projectile': {
                    const p1 = { x: (effect.start.x + 0.5) * cellSize, y: (effect.start.y + 0.5) * cellSize };
                    const p2 = { x: (effect.end.x + 0.5) * cellSize, y: (effect.end.y + 0.5) * cellSize };
                    const midX = (p1.x + p2.x) / 2;
                    const midY = (p1.y + p2.y) / 2;
                    const dist = Math.sqrt((p2.x-p1.x)**2 + (p2.y-p1.y)**2);
                    const controlY = midY - dist*0.3; // arc height
                    
                    const t = easedProgress;
                    const currentX = (1-t)**2 * p1.x + 2*(1-t)*t*midX + t**2 * p2.x;
                    const currentY = (1-t)**2 * p1.y + 2*(1-t)*t*controlY + t**2 * p2.y;
                    
                    ctx.fillStyle = 'red';
                    ctx.beginPath();
                    ctx.arc(currentX, currentY, 5, 0, 2*Math.PI);
                    ctx.fill();
                    break;
                }
                 case 'chain_lightning': {
                    if(!effect.destroyed_point || !effect.point_ids) break;
                    const p_end = effect.destroyed_point;
                    // Find closest point on rune to target
                    const start_candidates = effect.point_ids.map(pid => gameState.points[pid]).filter(Boolean);
                    if(!start_candidates.length) break;
                    const p_start = start_candidates.reduce((closest, p) => distance_sq(p, p_end) < distance_sq(closest, p_end) ? p : closest, start_candidates[0]);
                    
                    const p1 = {x: (p_start.x + 0.5)*cellSize, y: (p_start.y + 0.5)*cellSize};
                    const p2 = {x: (p_end.x + 0.5)*cellSize, y: (p_end.y + 0.5)*cellSize};
                    ctx.strokeStyle = `rgba(200, 230, 255, ${1 - progress})`;
                    ctx.lineWidth = 3;
                    illustrationHelpers.drawJaggedLine(ctx, p1, p2, 7, 12);
                    break;
                 }
                 case 'line_crack': {
                    const p1 = gameState.points[effect.old_line.p1_id];
                    const p2 = gameState.points[effect.old_line.p2_id];
                    if(!p1 || !p2) break;
                    const p1_c = {x:(p1.x+0.5)*cellSize, y:(p1.y+0.5)*cellSize};
                    const p2_c = {x:(p2.x+0.5)*cellSize, y:(p2.y+0.5)*cellSize};
                    const mid_c = {x:(effect.new_point.x+0.5)*cellSize, y:(effect.new_point.y+0.5)*cellSize};
                    
                    ctx.globalAlpha = 1 - easedProgress;
                    ctx.strokeStyle = effect.color;
                    ctx.lineWidth = 2;
                    illustrationHelpers.drawJaggedLine(ctx, p1_c, mid_c, 5, 5);
                    illustrationHelpers.drawJaggedLine(ctx, p2_c, mid_c, 5, 5);
                    break;
                 }
                 case 'energy_spiral': {
                    const p_start = {x:(effect.start.x+0.5)*cellSize, y:(effect.start.y+0.5)*cellSize};
                    const p_end = {x:(effect.end.x+0.5)*cellSize, y:(effect.end.y+0.5)*cellSize};
                    const p_current = {
                        x: p_start.x + (p_end.x - p_start.x) * easedProgress,
                        y: p_start.y + (p_end.y - p_start.y) * easedProgress
                    };
                    const angle = progress * Math.PI * 6;
                    const radius = (1 - progress) * 15;
                    ctx.fillStyle = effect.color;
                    ctx.globalAlpha = 1 - progress;
                    ctx.beginPath();
                    ctx.arc(p_current.x + Math.cos(angle)*radius, p_current.y + Math.sin(angle)*radius, 3, 0, 2*Math.PI);
                    ctx.fill();
                    break;
                 }
                 case 'monolith_formation':
                 case 'heartwood_creation': {
                     const cx = (effect.center_coords.x + 0.5) * cellSize;
                     const cy = (effect.center_coords.y + 0.5) * cellSize;
                     const startPoints = effect.sacrificed_points || [effect.center_coords];
                     
                     ctx.strokeStyle = effect.color || '#fff';
                     ctx.lineWidth = 2;
                     ctx.globalAlpha = 1 - progress;
                     startPoints.forEach(p_start => {
                         const start_c = {x:(p_start.x+0.5)*cellSize, y:(p_start.y+0.5)*cellSize};
                         const end_c = {x:start_c.x + (cx - start_c.x)*easedProgress, y:start_c.y + (cy-start_c.y)*easedProgress};
                         ctx.beginPath();
                         ctx.moveTo(start_c.x, start_c.y);
                         ctx.lineTo(end_c.x, end_c.y);
                         ctx.stroke();
                     });
                     break;
                 }
                 case 'mirror_axis': {
                     const p1 = gameState.points[effect.p1_id];
                     const p2 = gameState.points[effect.p2_id];
                     if(p1 && p2){
                        const x1 = (p1.x + 0.5) * cellSize; const y1 = (p1.y + 0.5) * cellSize;
                        const x2 = (p2.x + 0.5) * cellSize; const y2 = (p2.y + 0.5) * cellSize;
                        const pulse = Math.abs(Math.sin(progress * Math.PI * 2));
                        ctx.strokeStyle = `rgba(255, 255, 255, ${pulse})`;
                        ctx.lineWidth = 1 + pulse * 4;
                        ctx.setLineDash([5,5]);
                        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
                        ctx.setLineDash([]);
                     }
                     break;
                 }
                 case 'point_pull': {
                     const center_c = {x:(effect.center.x+0.5)*cellSize, y:(effect.center.y+0.5)*cellSize};
                     effect.points.forEach(p_start_data => {
                         const p_start_c = {x:(p_start_data.x+0.5)*cellSize, y:(p_start_data.y+0.5)*cellSize};
                         const p_end_c = {
                            x: p_start_c.x + (center_c.x - p_start_c.x) * easedProgress,
                            y: p_start_c.y + (center_c.y - p_start_c.y) * easedProgress
                         };
                         ctx.strokeStyle = '#aaa';
                         ctx.lineWidth = 1.5;
                         ctx.globalAlpha = 1 - progress;
                         ctx.beginPath(); ctx.moveTo(p_start_c.x, p_start_c.y); ctx.lineTo(p_end_c.x, p_end_c.y); ctx.stroke();
                     });
                     break;
                 }
                 case 'portal_link': {
                     const p1_c = {x:(effect.p1.x+0.5)*cellSize, y:(effect.p1.y+0.5)*cellSize};
                     const p2_c = {x:(effect.p2.x+0.5)*cellSize, y:(effect.p2.y+0.5)*cellSize};
                     
                     ctx.strokeStyle = effect.color;
                     ctx.lineWidth = 3;
                     const radius1 = 15 * (1-progress);
                     const radius2 = 15 * progress;
                     
                     ctx.globalAlpha = 1 - progress;
                     ctx.beginPath(); ctx.arc(p1_c.x, p1_c.y, radius1, 0, 2*Math.PI); ctx.stroke();
                     
                     ctx.globalAlpha = progress;
                     ctx.beginPath(); ctx.arc(p2_c.x, p2_c.y, radius2, 0, 2*Math.PI); ctx.stroke();
                     break;
                 }
                 case 'reposition_trail': {
                    if (!effect.p1 || !effect.p2) break;
                    const p1_coords = { x: (effect.p1.x + 0.5) * cellSize, y: (effect.p1.y + 0.5) * cellSize };
                    const p2_coords = { x: (effect.p2.x + 0.5) * cellSize, y: (effect.p2.y + 0.5) * cellSize };
                    ctx.strokeStyle = effect.color;
                    ctx.lineWidth = 2;
                    ctx.globalAlpha = 1 - easedProgress;
                    ctx.setLineDash([5, 5]);
                    ctx.beginPath();
                    ctx.moveTo(p1_coords.x, p1_coords.y);
                    ctx.lineTo(p2_coords.x, p2_coords.y);
                    ctx.stroke();
                    ctx.setLineDash([]);
                    break;
                }
                case 'rotation_arc': {
                    const start_c = { x: (effect.start.x + 0.5) * cellSize, y: (effect.start.y + 0.5) * cellSize };
                    let pivot_c;
                    if (effect.is_grid_center) {
                        pivot_c = { x: (effect.grid_size / 2) * cellSize, y: (effect.grid_size / 2) * cellSize };
                    } else {
                        pivot_c = { x: (effect.pivot.x + 0.5) * cellSize, y: (effect.pivot.y + 0.5) * cellSize };
                    }
                    const radius = Math.sqrt((start_c.x - pivot_c.x)**2 + (start_c.y - pivot_c.y)**2);
                    const startAngle = Math.atan2(start_c.y - pivot_c.y, start_c.x - pivot_c.x);

                    const end_c = { x: (effect.end.x + 0.5) * cellSize, y: (effect.end.y + 0.5) * cellSize };
                    const endAngle = Math.atan2(end_c.y - pivot_c.y, end_c.x - pivot_c.x);
                    
                    let sweep = endAngle - startAngle;
                    if (Math.abs(sweep) > Math.PI) {
                        sweep = sweep - Math.sign(sweep) * 2 * Math.PI;
                    }

                    ctx.strokeStyle = effect.color;
                    ctx.lineWidth = 2;
                    ctx.globalAlpha = 1 - progress;
                    ctx.setLineDash([4, 4]);
                    ctx.beginPath();
                    ctx.arc(pivot_c.x, pivot_c.y, radius, startAngle, startAngle + sweep * easedProgress, sweep < 0);
                    ctx.stroke();
                    ctx.setLineDash([]);
                    break;
                }
            }
        });
        ctx.restore();
    }

    /**
     * The main rendering function, orchestrating all drawing operations.
     */
    function render(gameState, uiState) {
        if (!gameState || !canvas) return;

        drawGrid(gameState.grid_size || 10);

        const isHighlightingActive = uiState.debugOptions.highlightLastAction && 
            (uiState.lastActionHighlights.points.size > 0 || uiState.lastActionHighlights.lines.size > 0 || uiState.lastActionHighlights.structures.size > 0);

        if (gameState.game_phase === 'SETUP') {
             const tempPointsDict = {};
             uiState.initialPoints.forEach((p, i) => tempPointsDict[`p_${i}`] = {...p, id: `p_${i}`});
             drawPoints(tempPointsDict, uiState.localTeams, isHighlightingActive, uiState);
        } else if (gameState.teams) {
            const pointsDict = gameState.points;
            const teams = gameState.teams;

            // --- Render layers in order ---
            drawTerritories(pointsDict, gameState.territories, teams, isHighlightingActive, uiState);
            drawMonoliths(gameState, isHighlightingActive, uiState);
            drawTrebuchets(gameState, isHighlightingActive, uiState);
            drawPrisms(gameState, isHighlightingActive, uiState);
            drawRunes(gameState, isHighlightingActive, uiState);
            drawNexuses(gameState, isHighlightingActive, uiState);
            drawHeartwoods(gameState, isHighlightingActive, uiState);
            drawWonders(gameState, isHighlightingActive, uiState);
            drawRiftSpires(gameState, isHighlightingActive, uiState);
            drawRiftTraps(gameState, isHighlightingActive, uiState);
            drawFissures(gameState, isHighlightingActive, uiState);
            drawBarricades(gameState, isHighlightingActive, uiState);
            drawScorchedZones(gameState, isHighlightingActive, uiState);
            drawLeyLines(gameState, isHighlightingActive, uiState);
            drawLines(pointsDict, gameState.lines, teams, isHighlightingActive, uiState);
            drawPoints(pointsDict, teams, isHighlightingActive, uiState);

            if (gameState.game_phase === 'FINISHED') {
                drawHulls(gameState.interpretation, teams, uiState);
            }
        }
        drawVisualEffects(uiState, gameState);
    }

    // --- Public API ---
    return {
        init: (_canvas) => {
            canvas = _canvas;
            if (canvas) {
                ctx = canvas.getContext('2d');
            }
        },
        resize: (gridSize) => {
            if (!canvas || canvas.clientWidth === 0 || canvas.clientHeight === 0) return;
            canvas.width = canvas.clientWidth;
            canvas.height = canvas.clientHeight;
            cellSize = canvas.width / (gridSize || 10);
        },
        render
    };
})();