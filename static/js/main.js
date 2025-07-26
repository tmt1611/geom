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

    // --- Drawing & Illustration Helpers ---
    const illustrationHelpers = {
        drawJaggedLine: (ctx, p1, p2, segments, jag_amount) => {
            const dx = p2.x - p1.x;
            const dy = p2.y - p1.y;
            const len = Math.sqrt(dx * dx + dy * dy);
            if (len < 1) return;
            const angle = Math.atan2(dy, dx);

            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);

            for (let i = 1; i < segments; i++) {
                const lateral = (Math.random() - 0.5) * jag_amount;
                const along = (i / segments) * len;
                const x = p1.x + Math.cos(angle) * along - Math.sin(angle) * lateral;
                const y = p1.y + Math.sin(angle) * along + Math.cos(angle) * lateral;
                ctx.lineTo(x, y);
            }
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
        },
        drawPoints: (ctx, points, color) => {
            points.forEach(p => {
                ctx.beginPath();
                ctx.arc(p.x, p.y, 5, 0, 2 * Math.PI);
                ctx.fillStyle = color;
                ctx.fill();
            });
        },
        drawLines: (ctx, lines, color, width = 2) => {
            ctx.strokeStyle = color;
            ctx.lineWidth = width;
            lines.forEach(line => {
                ctx.beginPath();
                ctx.moveTo(line.p1.x, line.p1.y);
                ctx.lineTo(line.p2.x, line.p2.y);
                ctx.stroke();
            });
        },
        drawArrow: (ctx, p1, p2, color) => {
            const headlen = 15;
            const dx = p2.x - p1.x;
            const dy = p2.y - p1.y;
            const angle = Math.atan2(dy, dx);
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.lineTo(p2.x - headlen * Math.cos(angle - Math.PI / 6), p2.y - headlen * Math.sin(angle - Math.PI / 6));
            ctx.moveTo(p2.x, p2.y);
            ctx.lineTo(p2.x - headlen * Math.cos(angle + Math.PI / 6), p2.y - headlen * Math.sin(angle + Math.PI / 6));
            ctx.stroke();
        },
        drawDashedLine: (ctx, p1, p2, color) => {
            ctx.save();
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
            ctx.restore();
        },
        drawExplosion: (ctx, x, y, color = 'red', radius = 15) => {
            ctx.save();
            ctx.fillStyle = color;
            ctx.strokeStyle = 'rgba(255, 255, 150, 0.8)'; // yellow
            ctx.lineWidth = 2;
            const spikes = 8;
            ctx.beginPath();
            for (let i = 0; i < spikes; i++) {
                const angle = (i / spikes) * 2 * Math.PI;
                const outerX = x + Math.cos(angle) * radius;
                const outerY = y + Math.sin(angle) * radius;
                ctx.lineTo(outerX, outerY);
                const innerAngle = angle + Math.PI / spikes;
                const innerRadius = radius * 0.5;
                const innerX = x + Math.cos(innerAngle) * innerRadius;
                const innerY = y + Math.sin(innerAngle) * innerRadius;
                ctx.lineTo(innerX, innerY);
            }
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            ctx.restore();
        },
        drawFortifiedPoint: (ctx, p, color) => {
            ctx.fillStyle = color;
            const radius = 5;
            const size = radius * 1.7;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y - size);
            ctx.lineTo(p.x + size, p.y);
            ctx.lineTo(p.x, p.y + size);
            ctx.lineTo(p.x - size, p.y);
            ctx.closePath();
            ctx.fill();
        }
    };

    const illustrationDrawers = {
        'default': (ctx, w, h) => {
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#ccc';
            ctx.font = '16px Arial';
            ctx.fillText('No Illustration', w / 2, h / 2);
        },
        'fortify_shield': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const p1 = { x: w * 0.3, y: h * 0.5 };
            const p2 = { x: w * 0.7, y: h * 0.5 };

            illustrationHelpers.drawLines(ctx, [{ p1, p2 }], team1_color);
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = 'rgba(173, 216, 230, 0.9)';
            ctx.lineWidth = 12;
            ctx.stroke();
            ctx.restore();
            illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
        },
        'expand_add': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const p1 = { x: w * 0.3, y: h * 0.5 };
            const p2 = { x: w * 0.7, y: h * 0.5 };
            illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
            illustrationHelpers.drawDashedLine(ctx, p1, p2, team1_color);
        },
        'expand_extend': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const p1 = { x: w * 0.2, y: h * 0.5 };
            const p2 = { x: w * 0.5, y: h * 0.5 };
            const p3 = { x: w * 0.9, y: h * 0.5 };
            illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1, p2 }], team1_color);
            illustrationHelpers.drawDashedLine(ctx, p2, p3, team1_color);
            illustrationHelpers.drawPoints(ctx, [p3], team1_color);
        },
        'expand_fracture': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const p1 = { x: w * 0.2, y: h * 0.5 };
            const p2 = { x: w * 0.8, y: h * 0.5 };
            const p_new = { x: w * 0.5, y: h * 0.5 };
            illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1, p2 }], team1_color);

            ctx.save();
            ctx.beginPath();
            ctx.arc(p_new.x, p_new.y, 15, 0, 2 * Math.PI);
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 6;
            ctx.stroke();
            ctx.fillStyle = team1_color;
            ctx.fill();
            ctx.restore();
        },
        'expand_orbital': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const center = { x: w * 0.5, y: h * 0.5 };
            illustrationHelpers.drawPoints(ctx, [center], team1_color);

            const radius = w * 0.3;
            const num_satellites = 5;
            const satellites = [];
            for (let i = 0; i < num_satellites; i++) {
                const angle = (i / num_satellites) * 2 * Math.PI;
                const p = {
                    x: center.x + Math.cos(angle) * radius,
                    y: center.y + Math.sin(angle) * radius,
                };
                satellites.push(p);
                illustrationHelpers.drawDashedLine(ctx, center, p, team1_color);
            }
            illustrationHelpers.drawPoints(ctx, satellites, team1_color);
        },
        'expand_spawn': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const p1 = { x: w * 0.4, y: h * 0.5 };
            const p2 = { x: w * 0.6, y: h * 0.5 };
            illustrationHelpers.drawPoints(ctx, [p1], team1_color);
            illustrationHelpers.drawDashedLine(ctx, p1, p2, team1_color);
            illustrationHelpers.drawPoints(ctx, [p2], team1_color);
        },
        'fight_attack': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const p1 = { x: w * 0.1, y: h * 0.3 };
            const p2 = { x: w * 0.4, y: h * 0.3 };
            const ep1 = { x: w * 0.7, y: h * 0.1 };
            const ep2 = { x: w * 0.7, y: h * 0.9 };
            const hit = { x: w * 0.7, y: h * 0.3 };

            illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1, p2 }], team1_color);
            illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
            illustrationHelpers.drawLines(ctx, [{ p1: ep1, p2: ep2 }], team2_color);
            illustrationHelpers.drawArrow(ctx, p2, hit, team1_color);

            illustrationHelpers.drawExplosion(ctx, hit.x, hit.y);
        },
        'fight_chain_lightning': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const p1 = { x: w * 0.2, y: h * 0.5 };
            const p_sac = { x: w * 0.4, y: h * 0.5 };
            const p3 = { x: w * 0.6, y: h * 0.5 };
            illustrationHelpers.drawPoints(ctx, [p1, p_sac, p3], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1: p1, p2: p_sac }, { p1: p_sac, p2: p3 }], team1_color);
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(p_sac.x - 8, p_sac.y - 8);
            ctx.lineTo(p_sac.x + 8, p_sac.y + 8);
            ctx.moveTo(p_sac.x - 8, p_sac.y + 8);
            ctx.lineTo(p_sac.x + 8, p_sac.y - 8);
            ctx.stroke();
            const ep1 = { x: w * 0.8, y: h * 0.3 };
            illustrationHelpers.drawPoints(ctx, [ep1], team2_color);
            ctx.save();
            ctx.strokeStyle = 'rgba(200, 230, 255, 0.9)';
            ctx.lineWidth = 2;
            illustrationHelpers.drawJaggedLine(ctx, p3, ep1, 7, 12);
            ctx.restore();
            illustrationHelpers.drawExplosion(ctx, ep1.x, ep1.y);
        },
        'sacrifice_convert_point': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';

            const p1 = { x: w * 0.2, y: h * 0.5 };
            const p2 = { x: w * 0.4, y: h * 0.5 };
            const ep1 = { x: w * 0.7, y: h * 0.5 };

            illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1, p2 }], team1_color, 1);
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(w * 0.25, h * 0.4);
            ctx.lineTo(w * 0.35, h * 0.6);
            ctx.moveTo(w * 0.25, h * 0.6);
            ctx.lineTo(w * 0.35, h * 0.4);
            ctx.stroke();
            illustrationHelpers.drawPoints(ctx, [ep1], team2_color);
            illustrationHelpers.drawArrow(ctx, { x: w * 0.5, y: h * 0.5 }, { x: w * 0.65, y: h * 0.5 }, '#f1c40f');
            ctx.beginPath();
            ctx.arc(ep1.x, ep1.y, 12, 0, 2 * Math.PI);
            ctx.fillStyle = team1_color;
            ctx.globalAlpha = 0.5;
            ctx.fill();
            ctx.globalAlpha = 1.0;
        },
        'fight_bastion_pulse': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const core = { x: w * 0.3, y: h * 0.5 };
            const p_sac = { x: w * 0.5, y: h * 0.2 };
            const prongs = [p_sac, { x: w * 0.5, y: h * 0.8 }, { x: w * 0.1, y: h * 0.5 }];
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(prongs[0].x, prongs[0].y);
            ctx.lineTo(prongs[1].x, prongs[1].y);
            ctx.lineTo(prongs[2].x, prongs[2].y);
            ctx.closePath();
            ctx.strokeStyle = team1_color;
            ctx.lineWidth = 4;
            ctx.globalAlpha = 0.4;
            ctx.stroke();
            ctx.restore();
            illustrationHelpers.drawPoints(ctx, [core, ...prongs], team1_color);
            prongs.forEach(p => illustrationHelpers.drawLines(ctx, [{ p1: core, p2: p }], team1_color));
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(p_sac.x - 8, p_sac.y - 8);
            ctx.lineTo(p_sac.x + 8, p_sac.y + 8);
            ctx.moveTo(p_sac.x - 8, p_sac.y + 8);
            ctx.lineTo(p_sac.x + 8, p_sac.y - 8);
            ctx.stroke();
            const ep1 = { x: w * 0.8, y: h * 0.1 };
            const ep2 = { x: w * 0.2, y: h * 0.9 };
            illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
            illustrationHelpers.drawLines(ctx, [{ p1: ep1, p2: ep2 }], team2_color, 1);
            illustrationHelpers.drawExplosion(ctx, w * 0.4, h * 0.7);
        },
        'fight_pincer_attack': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const p1 = { x: w * 0.3, y: h * 0.3 };
            const p2 = { x: w * 0.3, y: h * 0.7 };
            const ep1 = { x: w * 0.7, y: h * 0.5 };

            illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
            illustrationHelpers.drawPoints(ctx, [ep1], team2_color);
            illustrationHelpers.drawArrow(ctx, p1, ep1, team1_color);
            illustrationHelpers.drawArrow(ctx, p2, ep1, team1_color);
            illustrationHelpers.drawExplosion(ctx, ep1.x, ep1.y);
        },
        'fight_sentry_zap': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const p1 = { x: w * 0.2, y: h * 0.5 };
            const p2 = { x: w * 0.4, y: h * 0.5 };
            const p3 = { x: w * 0.6, y: h * 0.5 };
            const ep1 = { x: w * 0.4, y: h * 0.2 };

            illustrationHelpers.drawPoints(ctx, [p1, p2, p3], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1, p2 }, { p1: p2, p2: p3 }], team1_color);
            illustrationHelpers.drawPoints(ctx, [ep1], team2_color);
            const beam_end = { x: w * 0.4, y: h * 0.05 };
            illustrationHelpers.drawArrow(ctx, p2, beam_end, 'rgba(255, 100, 100, 1.0)');
            illustrationHelpers.drawExplosion(ctx, ep1.x, ep1.y);
        },
        'fight_refraction_beam': (ctx, w, h) => {
            const team1_color = 'hsl(240, 70%, 50%)';
            const team2_color = 'hsl(0, 70%, 50%)';
            const pA = { x: w * 0.3, y: h * 0.5 };
            const pB = { x: w * 0.5, y: h * 0.2 };
            const pC = { x: w * 0.5, y: h * 0.8 };
            const pD = { x: w * 0.7, y: h * 0.5 };
            const prism_points = [pA, pB, pC, pD];
            ctx.save();
            ctx.fillStyle = team1_color;
            ctx.globalAlpha = 0.2;
            ctx.beginPath();
            ctx.moveTo(pA.x, pA.y);
            ctx.lineTo(pB.x, pB.y);
            ctx.lineTo(pC.x, pC.y);
            ctx.closePath();
            ctx.fill();
            ctx.beginPath();
            ctx.moveTo(pD.x, pD.y);
            ctx.lineTo(pB.x, pB.y);
            ctx.lineTo(pC.x, pC.y);
            ctx.closePath();
            ctx.fill();
            ctx.restore();
            illustrationHelpers.drawPoints(ctx, prism_points, team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1: pA, p2: pB }, { p1: pA, p2: pC }, { p1: pB, p2: pC }], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1: pD, p2: pB }, { p1: pD, p2: pC }], team1_color);
            const ep1 = { x: w * 0.9, y: h * 0.2 };
            const ep2 = { x: w * 0.9, y: h * 0.8 };
            illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
            illustrationHelpers.drawLines(ctx, [{ p1: ep1, p2: ep2 }], team2_color);
            const source_point = { x: w * 0.1, y: h * 0.3 };
            const hit_prism = { x: w * 0.5, y: h * 0.4 };
            const hit_enemy = { x: w * 0.9, y: h * 0.5 };
            illustrationHelpers.drawArrow(ctx, source_point, hit_prism, 'rgba(255, 255, 150, 1.0)');
            illustrationHelpers.drawArrow(ctx, hit_prism, hit_enemy, 'rgba(255, 100, 100, 1.0)');
            illustrationHelpers.drawExplosion(ctx, hit_enemy.x, hit_enemy.y);
        },
        'fight_territory_strike': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const p1 = { x: w * 0.5, y: h * 0.2 };
            const p2 = { x: w * 0.2, y: h * 0.8 };
            const p3 = { x: w * 0.8, y: h * 0.8 };
            const center = { x: (p1.x + p2.x + p3.x) / 3, y: (p1.y + p2.y + p3.y) / 3 };
            const ep1 = { x: w * 0.8, y: h * 0.2 };
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.lineTo(p3.x, p3.y);
            ctx.closePath();
            ctx.fillStyle = team1_color;
            ctx.globalAlpha = 0.3;
            ctx.fill();
            ctx.globalAlpha = 1.0;
            illustrationHelpers.drawPoints(ctx, [p1, p2, p3], team1_color);
            illustrationHelpers.drawPoints(ctx, [ep1], team2_color);
            illustrationHelpers.drawArrow(ctx, center, ep1, 'rgba(100, 255, 100, 1.0)');
            illustrationHelpers.drawExplosion(ctx, ep1.x, ep1.y);
        },
        'fortify_anchor': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const p_sac = { x: w * 0.2, y: h * 0.5 };
            const p_anchor = { x: w * 0.4, y: h * 0.5 };
            const ep1 = { x: w * 0.8, y: h * 0.3 };
            const ep2 = { x: w * 0.8, y: h * 0.7 };
            illustrationHelpers.drawPoints(ctx, [p_sac], team1_color);
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(p_sac.x - 8, p_sac.y - 8);
            ctx.lineTo(p_sac.x + 8, p_sac.y + 8);
            ctx.moveTo(p_sac.x - 8, p_sac.y + 8);
            ctx.lineTo(p_sac.x + 8, p_sac.y - 8);
            ctx.stroke();
            ctx.fillStyle = team1_color;
            ctx.fillRect(p_anchor.x - 8, p_anchor.y - 8, 16, 16);
            illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
            illustrationHelpers.drawArrow(ctx, ep1, p_anchor, '#aaa');
            illustrationHelpers.drawArrow(ctx, ep2, p_anchor, '#aaa');
        },
        'fortify_claim': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const p1 = { x: w * 0.5, y: h * 0.2 };
            const p2 = { x: w * 0.2, y: h * 0.8 };
            const p3 = { x: w * 0.8, y: h * 0.8 };
            illustrationHelpers.drawPoints(ctx, [p1, p2, p3], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1: p1, p2: p2 }, { p1: p2, p2: p3 }, { p1: p3, p2: p1 }], team1_color);
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.lineTo(p3.x, p3.y);
            ctx.closePath();
            ctx.fillStyle = team1_color;
            ctx.globalAlpha = 0.3;
            ctx.fill();
            ctx.globalAlpha = 1.0;
        },
        'fortify_form_bastion': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const core = { x: w * 0.5, y: h * 0.5 };
            const prongs = [{ x: w * 0.7, y: h * 0.3 }, { x: w * 0.7, y: h * 0.7 }, { x: w * 0.3, y: h * 0.5 }];
            ctx.save();
            ctx.fillStyle = team1_color;
            const size = 18;
            ctx.translate(core.x, core.y);
            ctx.beginPath();
            ctx.moveTo(0, -size);
            ctx.lineTo(size, 0);
            ctx.lineTo(0, size);
            ctx.lineTo(-size, 0);
            ctx.closePath();
            ctx.fill();
            ctx.restore();
            illustrationHelpers.drawPoints(ctx, prongs, team1_color);
            prongs.forEach(p => illustrationHelpers.drawLines(ctx, [{ p1: core, p2: p }], team1_color));
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(prongs[0].x, prongs[0].y);
            ctx.lineTo(prongs[1].x, prongs[1].y);
            ctx.lineTo(prongs[2].x, prongs[2].y);
            ctx.closePath();
            ctx.strokeStyle = team1_color;
            ctx.lineWidth = 4;
            ctx.globalAlpha = 0.4;
            ctx.stroke();
            ctx.restore();
        },
        'fortify_form_monolith': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const p1 = { x: w * 0.4, y: h * 0.1 };
            const p2 = { x: w * 0.6, y: h * 0.1 };
            const p3 = { x: w * 0.6, y: h * 0.9 };
            const p4 = { x: w * 0.4, y: h * 0.9 };
            const points = [p1, p2, p3, p4];
            illustrationHelpers.drawPoints(ctx, points, team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1, p2 }, { p1: p2, p2: p3 }, { p1: p3, p2: p4 }, { p1: p4, p2: p1 }], team1_color);
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.lineTo(p3.x, p3.y);
            ctx.lineTo(p4.x, p4.y);
            ctx.closePath();
            ctx.fillStyle = team1_color;
            ctx.globalAlpha = 0.2;
            ctx.fill();
            ctx.globalAlpha = 1.0;
        },
        'fortify_mirror': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const axis1 = { x: w * 0.5, y: h * 0.1 };
            const axis2 = { x: w * 0.5, y: h * 0.9 };
            const p_orig = { x: w * 0.3, y: h * 0.3 };
            const p_refl = { x: w * 0.7, y: h * 0.3 };
            illustrationHelpers.drawPoints(ctx, [axis1, axis2], team1_color);
            illustrationHelpers.drawDashedLine(ctx, axis1, axis2, '#aaa');
            illustrationHelpers.drawPoints(ctx, [p_orig], team1_color);
            illustrationHelpers.drawDashedLine(ctx, p_orig, p_refl, '#aaa');
            ctx.save();
            ctx.globalAlpha = 0.5;
            illustrationHelpers.drawPoints(ctx, [p_refl], team1_color);
            ctx.restore();
        },
        'rune_area_shield': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const t1 = { x: w * 0.5, y: h * 0.1 };
            const t2 = { x: w * 0.1, y: h * 0.9 };
            const t3 = { x: w * 0.9, y: h * 0.9 };
            const core = { x: w * 0.5, y: h * 0.6 };
            illustrationHelpers.drawPoints(ctx, [t1, t2, t3, core], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1: t1, p2: t2 }, { p1: t2, p2: t3 }, { p1: t3, p2: t1 }], team1_color);
            ctx.beginPath();
            ctx.moveTo(t1.x, t1.y);
            ctx.lineTo(t2.x, t2.y);
            ctx.lineTo(t3.x, t3.y);
            ctx.closePath();
            ctx.fillStyle = 'rgba(173, 216, 230, 0.5)';
            ctx.fill();
            const l1 = { x: w * 0.4, y: h * 0.5 };
            const l2 = { x: w * 0.6, y: h * 0.7 };
            illustrationHelpers.drawPoints(ctx, [l1, l2], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1: l1, p2: l2 }], team1_color);
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(l1.x, l1.y);
            ctx.lineTo(l2.x, l2.y);
            ctx.strokeStyle = 'rgba(173, 216, 230, 0.9)';
            ctx.lineWidth = 12;
            ctx.stroke();
            ctx.restore();
        },
        'rune_shield_pulse': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const t1 = { x: w * 0.3, y: h * 0.2 };
            const t2 = { x: w * 0.1, y: h * 0.8 };
            const t3 = { x: w * 0.5, y: h * 0.8 };
            const core = { x: w * 0.3, y: h * 0.6 };
            const center = { x: (t1.x + t2.x + t3.x) / 3, y: (t1.y + t2.y + t3.y) / 3 };
            illustrationHelpers.drawPoints(ctx, [t1, t2, t3, core], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1: t1, p2: t2 }, { p1: t2, p2: t3 }, { p1: t3, p2: t1 }], team1_color);
            ctx.save();
            ctx.beginPath();
            ctx.arc(center.x, center.y, w * 0.3, 0, 2 * Math.PI);
            ctx.strokeStyle = 'rgba(173, 216, 230, 0.7)';
            ctx.setLineDash([4, 4]);
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.restore();
            const ep1 = { x: w * 0.8, y: h * 0.3 };
            const ep2 = { x: w * 0.7, y: h * 0.7 };
            illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
            illustrationHelpers.drawArrow(ctx, ep1, { x: w * 0.9, y: h * 0.2 }, '#aaa');
            illustrationHelpers.drawArrow(ctx, ep2, { x: w * 0.8, y: h * 0.8 }, '#aaa');
        },
        'rune_impale': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const p_handle = { x: w * 0.1, y: h * 0.5 };
            const p_apex = { x: w * 0.3, y: h * 0.5 };
            const p_p1 = { x: w * 0.4, y: h * 0.3 };
            const p_p2 = { x: w * 0.4, y: h * 0.7 };
            illustrationHelpers.drawPoints(ctx, [p_handle, p_apex, p_p1, p_p2], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1: p_handle, p2: p_apex }, { p1: p_apex, p2: p_p1 }, { p1: p_apex, p2: p_p2 }], team1_color);
            const hit_point = { x: w * 0.9, y: h * 0.5 };
            illustrationHelpers.drawArrow(ctx, p_apex, hit_point, 'rgba(255, 100, 255, 1.0)');
            const ep1 = { x: w * 0.7, y: h * 0.2 };
            const ep2 = { x: w * 0.7, y: h * 0.8 };
            illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
            illustrationHelpers.drawLines(ctx, [{ p1: ep1, p2: ep2 }], team2_color, 1);
        },
        'rune_shoot_bisector': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const p_v = { x: w * 0.2, y: h * 0.5 };
            const p_l1 = { x: w * 0.4, y: h * 0.2 };
            const p_l2 = { x: w * 0.4, y: h * 0.8 };
            illustrationHelpers.drawPoints(ctx, [p_v, p_l1, p_l2], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1: p_v, p2: p_l1 }, { p1: p_v, p2: p_l2 }], team1_color);
            const hit_point = { x: w * 0.9, y: h * 0.5 };
            illustrationHelpers.drawArrow(ctx, p_v, hit_point, 'rgba(100, 255, 255, 1.0)');
            const ep1 = { x: w * 0.7, y: h * 0.3 };
            const ep2 = { x: w * 0.7, y: h * 0.7 };
            illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
            illustrationHelpers.drawLines(ctx, [{ p1: ep1, p2: ep2 }], team2_color, 1);
        },
        'rune_t_hammer_slam': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const p_mid = { x: w * 0.3, y: h * 0.5 };
            const p_head = { x: w * 0.5, y: h * 0.5 };
            const p_s1 = { x: w * 0.3, y: h * 0.2 };
            const p_s2 = { x: w * 0.3, y: h * 0.8 };
            illustrationHelpers.drawPoints(ctx, [p_mid, p_head, p_s1, p_s2], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1: p_s1, p2: p_mid }, { p1: p_mid, p2: p_s2 }, { p1: p_mid, p2: p_head }], team1_color);
            const ep1 = { x: w * 0.7, y: h * 0.3 };
            const ep2 = { x: w * 0.7, y: h * 0.7 };
            illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
            illustrationHelpers.drawArrow(ctx, ep1, { x: w * 0.9, y: h * 0.3 }, '#aaa');
            illustrationHelpers.drawArrow(ctx, ep2, { x: w * 0.9, y: h * 0.7 }, '#aaa');
        },
        'sacrifice_nova': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const center = { x: w * 0.5, y: h * 0.5 };
            illustrationHelpers.drawPoints(ctx, [center], team1_color);
            illustrationHelpers.drawExplosion(ctx, center.x, center.y, 'red', 15);
            const ep1 = { x: w * 0.8, y: h * 0.3 };
            const ep2 = { x: w * 0.8, y: h * 0.7 };
            const ep3 = { x: w * 0.2, y: h * 0.2 };
            const ep4 = { x: w * 0.3, y: h * 0.8 };
            illustrationHelpers.drawPoints(ctx, [ep1, ep2, ep3, ep4], team2_color);
            illustrationHelpers.drawLines(ctx, [{ p1: ep1, p2: ep2 }, { p1: ep3, p2: ep4 }], team2_color, 1);
            ctx.save();
            ctx.beginPath();
            ctx.arc(center.x, center.y, w * 0.3, 0, 2 * Math.PI);
            ctx.strokeStyle = 'rgba(255, 100, 100, 0.5)';
            ctx.setLineDash([5, 5]);
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.restore();
        },
        'sacrifice_phase_shift': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const p1_orig = { x: w * 0.2, y: h * 0.5 };
            const p2 = { x: w * 0.5, y: h * 0.5 };
            const p1_new = { x: w * 0.8, y: h * 0.3 };
            illustrationHelpers.drawLines(ctx, [{ p1: p1_orig, p2: p2 }], team1_color, 1);
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(w * 0.3, h * 0.4);
            ctx.lineTo(w * 0.4, h * 0.6);
            ctx.moveTo(w * 0.3, h * 0.6);
            ctx.lineTo(w * 0.4, h * 0.4);
            ctx.stroke();
            illustrationHelpers.drawPoints(ctx, [p1_orig, p2], team1_color);
            ctx.globalAlpha = 0.3;
            illustrationHelpers.drawPoints(ctx, [p1_orig], team1_color);
            ctx.globalAlpha = 1.0;
            illustrationHelpers.drawDashedLine(ctx, p1_orig, p1_new, '#aaa');
            illustrationHelpers.drawPoints(ctx, [p1_new], team1_color);
        },
        'sacrifice_whirlpool': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const center = { x: w * 0.5, y: h * 0.5 };
            illustrationHelpers.drawExplosion(ctx, center.x, center.y);
            const pointsToPull = [{ x: w * 0.2, y: h * 0.2 }, { x: w * 0.8, y: h * 0.3 }, { x: w * 0.7, y: h * 0.8 }, { x: w * 0.3, y: h * 0.7 }];
            illustrationHelpers.drawPoints(ctx, pointsToPull, team2_color);
            pointsToPull.forEach(p => {
                ctx.beginPath();
                ctx.moveTo(p.x, p.y);
                ctx.quadraticCurveTo((p.x + center.x) / 2 + (p.y - center.y) * 0.3, (p.y + center.y) / 2 - (p.x - center.x) * 0.3, center.x, center.y);
                ctx.strokeStyle = '#aaa';
                ctx.setLineDash([3, 3]);
                ctx.stroke();
            });
            ctx.setLineDash([]);
        },
        'sacrifice_cultivate_heartwood': (ctx, w, h) => {
            const team1_color = 'hsl(120, 70%, 50%)';
            const center = { x: w * 0.5, y: h * 0.5 };
            const branches = [];
            const num_branches = 5;
            const radius = w * 0.3;
            for (let i = 0; i < num_branches; i++) {
                const angle = (i / num_branches) * 2 * Math.PI;
                branches.push({ x: center.x + Math.cos(angle) * radius, y: center.y + Math.sin(angle) * radius });
            }
            illustrationHelpers.drawPoints(ctx, [center, ...branches], team1_color);
            branches.forEach(b => illustrationHelpers.drawLines(ctx, [{ p1: center, p2: b }], team1_color));
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            [center, ...branches].forEach(p => {
                ctx.beginPath();
                ctx.moveTo(p.x - 6, p.y - 6);
                ctx.lineTo(p.x + 6, p.y + 6);
                ctx.moveTo(p.x - 6, p.y + 6);
                ctx.lineTo(p.x + 6, p.y - 6);
                ctx.stroke();
            });
            ctx.beginPath();
            ctx.arc(center.x, center.y, 15, 0, 2 * Math.PI);
            ctx.fillStyle = team1_color;
            ctx.fill();
            ctx.font = 'bold 24px Arial';
            ctx.fillStyle = 'white';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('❤', center.x, center.y + 1);
        },
        'fortify_form_purifier': (ctx, w, h) => {
            const team1_color = 'hsl(50, 80%, 60%)';
            const center = { x: w * 0.5, y: h * 0.5 };
            const radius = w * 0.35;
            const num_points = 5;
            const points = [];
            for (let i = 0; i < num_points; i++) {
                const angle = (i / num_points) * 2 * Math.PI - (Math.PI / 2);
                points.push({ x: center.x + Math.cos(angle) * radius, y: center.y + Math.sin(angle) * radius });
            }
            illustrationHelpers.drawPoints(ctx, points, team1_color);
            for (let i = 0; i < num_points; i++) {
                illustrationHelpers.drawLines(ctx, [{ p1: points[i], p2: points[(i + 1) % num_points] }], team1_color);
            }
        },
        'fight_launch_payload': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const apex = { x: w * 0.2, y: h * 0.3 };
            const b1 = { x: w * 0.3, y: h * 0.5 };
            const b2 = { x: w * 0.3, y: h * 0.1 };
            const cw = { x: w * 0.4, y: h * 0.3 };
            const target = { x: w * 0.8, y: h * 0.7 };
            illustrationHelpers.drawPoints(ctx, [apex, b1, b2, cw], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1: apex, p2: b1 }, { p1: b1, p2: cw }, { p1: cw, p2: b2 }, { p1: b2, p2: apex }, { p1: b1, p2: b2 }], team1_color);
            illustrationHelpers.drawFortifiedPoint(ctx, target, team2_color);
            ctx.beginPath();
            ctx.moveTo(apex.x, apex.y);
            ctx.quadraticCurveTo(w * 0.5, h * 0.1, target.x, target.y);
            ctx.setLineDash([4, 4]);
            ctx.strokeStyle = 'red';
            ctx.stroke();
            ctx.setLineDash([]);
            illustrationHelpers.drawExplosion(ctx, target.x, target.y);
        },
        'fortify_rotate_point': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const pivot = { x: w * 0.5, y: h * 0.5 };
            const p_orig = { x: w * 0.7, y: h * 0.3 };
            ctx.strokeStyle = '#aaa';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(pivot.x - 6, pivot.y);
            ctx.lineTo(pivot.x + 6, pivot.y);
            ctx.moveTo(pivot.x, pivot.y - 6);
            ctx.lineTo(pivot.x, pivot.y + 6);
            ctx.stroke();
            ctx.save();
            ctx.globalAlpha = 0.4;
            illustrationHelpers.drawPoints(ctx, [p_orig], team1_color);
            ctx.restore();
            const p_new = { x: w * 0.3, y: h * 0.7 };
            ctx.beginPath();
            const radius = Math.sqrt((p_orig.x - pivot.x) ** 2 + (p_orig.y - pivot.y) ** 2);
            const startAngle = Math.atan2(p_orig.y - pivot.y, p_orig.x - pivot.x);
            const endAngle = Math.atan2(p_new.y - pivot.y, p_new.x - pivot.x);
            ctx.arc(pivot.x, pivot.y, radius, startAngle, endAngle);
            ctx.setLineDash([3, 3]);
            ctx.stroke();
            ctx.setLineDash([]);
            illustrationHelpers.drawPoints(ctx, [p_new], team1_color);
        },
        'rune_hourglass_stasis': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const v = { x: w * 0.4, y: h * 0.5 };
            const t1 = [{ x: w * 0.2, y: h * 0.2 }, { x: w * 0.2, y: h * 0.8 }];
            const t2 = [{ x: w * 0.6, y: h * 0.3 }, { x: w * 0.6, y: h * 0.7 }];
            const ep = { x: w * 0.8, y: h * 0.5 };
            illustrationHelpers.drawPoints(ctx, [v, ...t1, ...t2], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1: t1[0], p2: v }, { p1: v, p2: t1[1] }, { p1: t1[0], p2: t1[1] }], team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1: t2[0], p2: v }, { p1: v, p2: t2[1] }, { p1: t2[0], p2: t2[1] }], team1_color);
            illustrationHelpers.drawPoints(ctx, [ep], team2_color);
            const cage_r = 15;
            ctx.strokeStyle = 'rgba(150, 220, 255, 0.9)';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(ep.x - cage_r, ep.y);
            ctx.lineTo(ep.x + cage_r, ep.y);
            ctx.moveTo(ep.x, ep.y - cage_r);
            ctx.lineTo(ep.x, ep.y + cage_r);
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(ep.x, ep.y, cage_r, 0, 2 * Math.PI);
            ctx.stroke();
        },
        'sacrifice_rift_trap': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const center = { x: w * 0.5, y: h * 0.5 };
            illustrationHelpers.drawPoints(ctx, [center], team1_color);
            illustrationHelpers.drawExplosion(ctx, center.x - 20, center.y - 20);
            const radius = 12;
            ctx.strokeStyle = team1_color;
            ctx.lineWidth = 2;
            ctx.globalAlpha = 0.6;
            ctx.beginPath();
            ctx.arc(center.x, center.y, radius, 0.2, Math.PI - 0.2);
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(center.x, center.y, radius, Math.PI + 0.2, 2 * Math.PI - 0.2);
            ctx.stroke();
            ctx.globalAlpha = 1.0;
        },
        'fight_purify_territory': (ctx, w, h) => {
            const team1_color = 'hsl(50, 80%, 60%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const purifier_center = { x: w * 0.3, y: h * 0.5 };
            const purifier_radius = w * 0.2;
            const purifier_points = [];
            for (let i = 0; i < 5; i++) {
                const angle = (i / 5) * 2 * Math.PI - (Math.PI / 2);
                purifier_points.push({ x: purifier_center.x + Math.cos(angle) * purifier_radius, y: purifier_center.y + Math.sin(angle) * purifier_radius });
            }
            illustrationHelpers.drawPoints(ctx, purifier_points, team1_color);
            for (let i = 0; i < 5; i++) {
                illustrationHelpers.drawLines(ctx, [{ p1: purifier_points[i], p2: purifier_points[(i + 1) % 5] }], team1_color);
            }
            const p1 = { x: w * 0.8, y: h * 0.2 };
            const p2 = { x: w * 0.6, y: h * 0.8 };
            const p3 = { x: w * 0.95, y: h * 0.8 };
            illustrationHelpers.drawPoints(ctx, [p1, p2, p3], team2_color);
            illustrationHelpers.drawLines(ctx, [{ p1, p2 }, { p1: p2, p2: p3 }, { p1: p3, p2: p1 }], team2_color);
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.lineTo(p3.x, p3.y);
            ctx.closePath();
            ctx.fillStyle = team2_color;
            ctx.globalAlpha = 0.3;
            ctx.fill();
            ctx.save();
            ctx.globalAlpha = 1.0;
            ctx.beginPath();
            ctx.arc(purifier_center.x, purifier_center.y, w * 0.4, 0, 2 * Math.PI);
            ctx.strokeStyle = team1_color;
            ctx.lineWidth = 2;
            ctx.setLineDash([4, 4]);
            ctx.stroke();
            ctx.restore();
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.lineTo(p3.x, p3.y);
            ctx.closePath();
            ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
            ctx.fill();
        },
        'sacrifice_build_wonder': (ctx, w, h) => {
            const team1_color = 'hsl(50, 80%, 60%)';
            const center = { x: w * 0.5, y: h * 0.5 };
            const radius = w * 0.3;
            const num_points = 5;
            const cycle_points = [];
            for (let i = 0; i < num_points; i++) {
                const angle = (i / num_points) * 2 * Math.PI - (Math.PI / 2);
                cycle_points.push({ x: center.x + Math.cos(angle) * radius, y: center.y + Math.sin(angle) * radius });
            }
            illustrationHelpers.drawPoints(ctx, [center, ...cycle_points], team1_color);
            cycle_points.forEach(p => illustrationHelpers.drawLines(ctx, [{ p1: center, p2: p }], team1_color));
            for (let i = 0; i < num_points; i++) {
                illustrationHelpers.drawLines(ctx, [{ p1: cycle_points[i], p2: cycle_points[(i + 1) % num_points] }], team1_color);
            }
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            [center, ...cycle_points].forEach(p => {
                ctx.beginPath();
                ctx.moveTo(p.x - 4, p.y - 4);
                ctx.lineTo(p.x + 4, p.y + 4);
                ctx.moveTo(p.x - 4, p.y + 4);
                ctx.lineTo(p.x + 4, p.y - 4);
                ctx.stroke();
            });
            ctx.save();
            ctx.fillStyle = team1_color;
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            const spire_base_w = 18;
            const spire_h = 37;
            ctx.beginPath();
            ctx.moveTo(center.x - spire_base_w, center.y + spire_h / 2);
            ctx.lineTo(center.x, center.y - spire_h / 2);
            ctx.lineTo(center.x + spire_base_w, center.y + spire_h / 2);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            ctx.restore();
        },
        'rune_raise_barricade': (ctx, w, h) => {
            const team1_color = 'hsl(30, 70%, 50%)';
            const p1 = { x: w * 0.2, y: h * 0.2 };
            const p2 = { x: w * 0.8, y: h * 0.2 };
            const p3 = { x: w * 0.8, y: h * 0.8 };
            const p4 = { x: w * 0.2, y: h * 0.8 };
            const points = [p1, p2, p3, p4];
            illustrationHelpers.drawPoints(ctx, points, team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1, p2 }, { p1: p2, p2: p3 }, { p1: p3, p2: p4 }, { p1: p4, p2: p1 }], team1_color);
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            points.forEach(p => {
                ctx.beginPath();
                ctx.moveTo(p.x - 4, p.y - 4);
                ctx.lineTo(p.x + 4, p.y + 4);
                ctx.moveTo(p.x - 4, p.y + 4);
                ctx.lineTo(p.x + 4, p.y - 4);
                ctx.stroke();
            });
            const mid1 = { x: (p1.x + p4.x) / 2, y: (p1.y + p4.y) / 2 };
            const mid2 = { x: (p2.x + p3.x) / 2, y: (p2.y + p3.y) / 2 };
            ctx.save();
            ctx.strokeStyle = team1_color;
            ctx.lineWidth = 6;
            ctx.lineCap = 'round';
            illustrationHelpers.drawJaggedLine(ctx, mid1, mid2, 10, 4);
            ctx.restore();
        },
        'terraform_create_fissure': (ctx, w, h) => {
            const team1_color = 'hsl(280, 70%, 60%)';
            const spire_center = { x: w * 0.2, y: h * 0.5 };
            ctx.save();
            ctx.translate(spire_center.x, spire_center.y);
            ctx.beginPath();
            const spikes = 7;
            const outerRadius = 12;
            const innerRadius = 6;
            for (let i = 0; i < spikes * 2; i++) {
                const radius = i % 2 === 0 ? outerRadius : innerRadius;
                const angle = (i * Math.PI) / spikes;
                ctx.lineTo(Math.cos(angle) * radius, Math.sin(angle) * radius);
            }
            ctx.closePath();
            ctx.fillStyle = team1_color;
            ctx.fill();
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 1;
            ctx.stroke();
            ctx.restore();
            const fissure_start = { x: w * 0.4, y: h * 0.3 };
            illustrationHelpers.drawDashedLine(ctx, spire_center, fissure_start, team1_color);
            const fissure_end = { x: w * 0.9, y: h * 0.7 };
            ctx.save();
            ctx.strokeStyle = 'rgba(30, 30, 30, 0.8)';
            ctx.lineWidth = 4;
            ctx.lineCap = 'round';
            illustrationHelpers.drawJaggedLine(ctx, fissure_start, fissure_end, 15, 6);
            ctx.restore();
        },
        'fortify_form_rift_spire': (ctx, w, h) => {
            const team1_color = 'hsl(280, 70%, 60%)';
            const center = { x: w * 0.5, y: h * 0.5 };
            const t1_p2 = { x: w * 0.2, y: h * 0.2 };
            const t1_p3 = { x: w * 0.8, y: h * 0.2 };
            const t2_p3 = { x: w * 0.2, y: h * 0.8 };
            const t3_p3 = { x: w * 0.8, y: h * 0.8 };
            ctx.save();
            ctx.fillStyle = team1_color;
            ctx.globalAlpha = 0.2;
            ctx.beginPath();
            ctx.moveTo(center.x, center.y);
            ctx.lineTo(t1_p2.x, t1_p2.y);
            ctx.lineTo(t1_p3.x, t1_p3.y);
            ctx.closePath();
            ctx.fill();
            ctx.beginPath();
            ctx.moveTo(center.x, center.y);
            ctx.lineTo(t1_p2.x, t1_p2.y);
            ctx.lineTo(t2_p3.x, t2_p3.y);
            ctx.closePath();
            ctx.fill();
            ctx.beginPath();
            ctx.moveTo(center.x, center.y);
            ctx.lineTo(t1_p3.x, t1_p3.y);
            ctx.lineTo(t3_p3.x, t3_p3.y);
            ctx.closePath();
            ctx.fill();
            ctx.restore();
            illustrationHelpers.drawPoints(ctx, [center, t1_p2, t1_p3, t2_p3, t3_p3], team1_color);
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(center.x - 5, center.y - 5);
            ctx.lineTo(center.x + 5, center.y + 5);
            ctx.moveTo(center.x - 5, center.y + 5);
            ctx.lineTo(center.x + 5, center.y - 5);
            ctx.stroke();
            ctx.save();
            ctx.translate(center.x, center.y);
            ctx.beginPath();
            const spikes = 7;
            const outerRadius = 12;
            const innerRadius = 6;
            for (let i = 0; i < spikes * 2; i++) {
                const radius = i % 2 === 0 ? outerRadius : innerRadius;
                const angle = (i * Math.PI) / spikes;
                ctx.lineTo(Math.cos(angle) * radius, Math.sin(angle) * radius);
            }
            ctx.closePath();
            ctx.fillStyle = team1_color;
            ctx.globalAlpha = 0.8;
            ctx.fill();
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 1;
            ctx.stroke();
            ctx.restore();
        },
        'rune_starlight_cascade': (ctx, w, h) => {
            const team1_color = 'hsl(50, 80%, 60%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const center = { x: w * 0.35, y: h * 0.5 };
            const radius = w * 0.25;
            const num_points = 5;
            const cycle_points = [];
            for (let i = 0; i < num_points; i++) {
                const angle = (i / num_points) * 2 * Math.PI - (Math.PI / 2);
                cycle_points.push({ x: center.x + Math.cos(angle) * radius, y: center.y + Math.sin(angle) * radius });
            }
            illustrationHelpers.drawPoints(ctx, [center, ...cycle_points], team1_color);
            cycle_points.forEach(p => illustrationHelpers.drawLines(ctx, [{ p1: center, p2: p }], team1_color));
            for (let i = 0; i < num_points; i++) {
                illustrationHelpers.drawLines(ctx, [{ p1: cycle_points[i], p2: cycle_points[(i + 1) % num_points] }], team1_color);
            }
            ctx.save();
            ctx.beginPath();
            ctx.arc(center.x, center.y, w * 0.3, 0, 2 * Math.PI);
            ctx.strokeStyle = 'rgba(255, 255, 150, 0.7)';
            ctx.setLineDash([4, 4]);
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.restore();
            const ep1 = { x: w * 0.8, y: h * 0.2 };
            const ep2 = { x: w * 0.8, y: h * 0.8 };
            const ep3 = { x: w * 0.6, y: h * 0.1 };
            const ep4 = { x: w * 0.9, y: h * 0.1 };
            illustrationHelpers.drawPoints(ctx, [ep1, ep2, ep3, ep4], team2_color);
            illustrationHelpers.drawLines(ctx, [{ p1: ep1, p2: ep2 }, { p1: ep3, p2: ep4 }], team2_color, 1);
            illustrationHelpers.drawExplosion(ctx, w * 0.8, h * 0.5, 'red', 12);
            illustrationHelpers.drawExplosion(ctx, w * 0.75, h * 0.1, 'red', 12);
        },
        'rune_focus_beam': (ctx, w, h) => {
            const team1_color = 'hsl(50, 80%, 60%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const center = { x: w * 0.3, y: h * 0.5 };
            const radius = w * 0.2;
            const num_points = 5;
            const cycle_points = [];
            for (let i = 0; i < num_points; i++) {
                const angle = (i / num_points) * 2 * Math.PI - (Math.PI / 2);
                cycle_points.push({ x: center.x + Math.cos(angle) * radius, y: center.y + Math.sin(angle) * radius });
            }
            illustrationHelpers.drawPoints(ctx, [center, ...cycle_points], team1_color);
            cycle_points.forEach(p => illustrationHelpers.drawLines(ctx, [{ p1: center, p2: p }], team1_color));
            for (let i = 0; i < num_points; i++) {
                illustrationHelpers.drawLines(ctx, [{ p1: cycle_points[i], p2: cycle_points[(i + 1) % num_points] }], team1_color);
            }
            const target = { x: w * 0.8, y: h * 0.5 };
            ctx.save();
            ctx.fillStyle = team2_color;
            const size = 12;
            ctx.translate(target.x, target.y);
            ctx.beginPath();
            ctx.moveTo(0, -size);
            ctx.lineTo(size, 0);
            ctx.lineTo(0, size);
            ctx.lineTo(-size, 0);
            ctx.closePath();
            ctx.fill();
            ctx.restore();
            illustrationHelpers.drawArrow(ctx, center, target, 'rgba(255, 255, 150, 1.0)');
            illustrationHelpers.drawExplosion(ctx, target.x, target.y, 'red', 20);
        },
        'rune_cardinal_pulse': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const center = { x: w * 0.5, y: h * 0.5 };
            const arms = [{ x: w * 0.5, y: h * 0.2 }, { x: w * 0.8, y: h * 0.5 }, { x: w * 0.5, y: h * 0.8 }, { x: w * 0.2, y: h * 0.5 }];
            const rune_points = [center, ...arms];
            illustrationHelpers.drawPoints(ctx, rune_points, team1_color);
            arms.forEach(p => illustrationHelpers.drawLines(ctx, [{ p1: center, p2: p }], team1_color));
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            rune_points.forEach(p => {
                ctx.beginPath();
                ctx.moveTo(p.x - 4, p.y - 4);
                ctx.lineTo(p.x + 4, p.y + 4);
                ctx.moveTo(p.x - 4, p.y + 4);
                ctx.lineTo(p.x + 4, p.y - 4);
                ctx.stroke();
            });
            const ep1 = { x: w * 0.9, y: h * 0.3 };
            const ep2 = { x: w * 0.9, y: h * 0.7 };
            illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
            illustrationHelpers.drawLines(ctx, [{ p1: ep1, p2: ep2 }], team2_color);
            const hit_point = { x: w * 0.9, y: h * 0.5 };
            illustrationHelpers.drawArrow(ctx, center, hit_point, team1_color);
            illustrationHelpers.drawExplosion(ctx, hit_point.x, hit_point.y, 'red', 12);
            const new_point = { x: w * 0.5, y: h * 0.05 };
            illustrationHelpers.drawDashedLine(ctx, center, new_point, team1_color);
            illustrationHelpers.drawPoints(ctx, [new_point], team1_color);
            illustrationHelpers.drawArrow(ctx, center, { x: w * 0.05, y: h * 0.5 }, team1_color);
            illustrationHelpers.drawArrow(ctx, center, { x: w * 0.5, y: h * 0.95 }, team1_color);
        },
        'rune_parallel_discharge': (ctx, w, h) => {
            const team1_color = 'hsl(0, 70%, 50%)';
            const team2_color = 'hsl(240, 70%, 50%)';
            const p1 = { x: w * 0.2, y: h * 0.2 };
            const p2 = { x: w * 0.6, y: h * 0.2 };
            const p3 = { x: w * 0.8, y: h * 0.8 };
            const p4 = { x: w * 0.4, y: h * 0.8 };
            const points = [p1, p2, p3, p4];
            illustrationHelpers.drawPoints(ctx, points, team1_color);
            illustrationHelpers.drawLines(ctx, [{ p1, p2 }, { p1: p2, p2: p3 }, { p1: p3, p2: p4 }, { p1: p4, p2: p1 }], team1_color);
            const ep1 = { x: w * 0.5, y: h * 0.1 };
            const ep2 = { x: w * 0.5, y: h * 0.9 };
            illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
            illustrationHelpers.drawLines(ctx, [{ p1: ep1, p2: ep2 }], team2_color);
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.lineTo(p3.x, p3.y);
            ctx.lineTo(p4.x, p4.y);
            ctx.closePath();
            ctx.fillStyle = 'rgba(255, 255, 150, 0.7)';
            ctx.fill();
            ctx.restore();
            illustrationHelpers.drawExplosion(ctx, w * 0.5, h * 0.5);
        },
    };

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

    function drawGrid() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = '#e0e0e0';
        const gridSize = currentGameState.grid_size || 10;
        cellSize = canvas.width / gridSize;
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

    function drawPoints(pointsDict, teams, isHighlightingActive = false) {
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

                // Highlight effect for last action
                if (isHighlightingActive && isHighlighted) {
                    ctx.globalAlpha = 1.0; // Ensure it's fully opaque if it's highlighted
                    ctx.fillStyle = 'rgba(255, 255, 0, 0.8)';
                    ctx.beginPath(); ctx.arc(cx, cy, radius + 5, 0, 2 * Math.PI); ctx.fill();
                }

                // Pre-draw effects
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

                // Main point drawing
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

                // Post-draw effects
                if (p.is_in_stasis) {
                    const pulse = Math.abs(Math.sin(Date.now() / 400));
                    ctx.strokeStyle = `rgba(150, 220, 255, ${0.5 + pulse * 0.4})`;
                    ctx.lineWidth = 1.5;
                    const cage_radius = radius + 3;
                    ctx.beginPath(); ctx.moveTo(cx - cage_radius, cy); ctx.lineTo(cx + cage_radius, cy);
                    ctx.moveTo(cx, cy - cage_radius); ctx.lineTo(cx, cy + cage_radius); ctx.stroke();
                    ctx.beginPath(); ctx.arc(cx, cy, cage_radius, 0, 2 * Math.PI); ctx.stroke();
                }

                if (uiState.debugOptions.showPointIds) {
                    ctx.fillStyle = '#000'; ctx.font = '10px Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
                    ctx.fillText(p.id, cx, cy - (radius + 2));
                }

                ctx.restore();
            }
        });
    }

    function drawLines(pointsDict, lines, teams, isHighlightingActive = false) {
        if (!pointsDict) return;
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

                    // Highlight effect
                    if (isHighlightingActive && isHighlighted) {
                        ctx.globalAlpha = 1.0;
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
                    if (line.strength > 0) {
                        base_width += line.strength * 1.5;
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

    function drawHulls(interpretation, teams) {
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
                
                if (hullPoints.length > 2) {
                    ctx.closePath();
                }

                ctx.strokeStyle = team.color;
                ctx.lineWidth = 3;
                ctx.setLineDash([5, 5]);
                ctx.stroke();
                ctx.setLineDash([]);
            }
        });
    }

    function drawTerritories(pointsDict, territories, teams, isHighlightingActive = false) {
        if (!pointsDict || !territories) return;
        territories.forEach(territory => {
            const isHighlighted = territory.point_ids.every(pid => uiState.lastActionHighlights.points.has(pid));
            
            ctx.save();
            const team = teams[territory.teamId];
            if (team) {
                const triPoints = territory.point_ids.map(id => pointsDict[id]);
                if (triPoints.length === 3 && triPoints.every(p => p)) {
                    ctx.fillStyle = team.color;
                    
                    if (isHighlightingActive) {
                        ctx.globalAlpha = isHighlighted ? 0.5 : 0.1;
                    } else {
                        ctx.globalAlpha = 0.3;
                    }

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

    function drawMonoliths(gameState, isHighlightingActive = false) {
        if (!gameState.monoliths) return;

        for (const monolithId in gameState.monoliths) {
            const monolith = gameState.monoliths[monolithId];
            const isHighlighted = monolith.point_ids.every(pid => uiState.lastActionHighlights.points.has(pid));

            ctx.save();
            if (isHighlightingActive && !isHighlighted) {
                ctx.globalAlpha = 0.2;
            } else if (isHighlightingActive && isHighlighted) {
                ctx.globalAlpha = 1.0;
            }

            const team = gameState.teams[monolith.teamId];
            if (!team) {
                ctx.restore();
                continue;
            }

            const points = monolith.point_ids.map(pid => gameState.points[pid]).filter(p => p);
            if (points.length !== 4) continue;

            const center = monolith.center_coords;
            points.sort((a, b) => Math.atan2(a.y - center.y, a.x - center.x) - Math.atan2(b.y - center.y, b.x - center.x));

            ctx.beginPath();
            ctx.moveTo((points[0].x + 0.5) * cellSize, (points[0].y + 0.5) * cellSize);
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo((points[i].x + 0.5) * cellSize, (points[i].y + 0.5) * cellSize);
            }
            ctx.closePath();
            
            ctx.fillStyle = team.color;
            ctx.globalAlpha = 0.15;
            ctx.fill();

            const pulse = Math.abs(Math.sin(Date.now() / 600));
            ctx.globalAlpha = 0.1 + pulse * 0.2;
            ctx.lineWidth = 1 + pulse;
            ctx.strokeStyle = '#fff';
            ctx.stroke();
            ctx.restore();
        }
    }

    function drawTrebuchets(gameState, isHighlightingActive = false) {
        if (!gameState.trebuchets) return;

        for (const teamId in gameState.trebuchets) {
            const teamTrebuchets = gameState.trebuchets[teamId];
            const team = gameState.teams[teamId];
            if (!team || !teamTrebuchets) continue;

            teamTrebuchets.forEach(trebuchet => {
                const isHighlighted = trebuchet.point_ids.every(pid => uiState.lastActionHighlights.points.has(pid));
                ctx.save();
                if (isHighlightingActive && !isHighlighted) {
                    ctx.globalAlpha = 0.2;
                } else if (isHighlightingActive && isHighlighted) {
                    ctx.globalAlpha = 1.0;
                }

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

    function drawWhirlpools(gameState, isHighlightingActive = false) {
        if (!gameState.whirlpools) return;
    
        gameState.whirlpools.forEach(wp => {
            const team = gameState.teams[wp.teamId];
            if (!team) return;

            const isHighlighted = uiState.lastActionHighlights.structures.has(wp.id);
            ctx.save();
            if (isHighlightingActive && !isHighlighted) {
                ctx.globalAlpha = 0.2;
            } else if (isHighlightingActive && isHighlighted) {
                ctx.globalAlpha = 1.0;
            }

            const cx = (wp.coords.x + 0.5) * cellSize;
            const cy = (wp.coords.y + 0.5) * cellSize;
            const radius = Math.sqrt(wp.radius_sq) * cellSize;
            const angle_offset = (Date.now() / 2000) % (2 * Math.PI);

            ctx.save();
            ctx.translate(cx, cy);

            const num_lines = 12;
            for (let i = 0; i < num_lines; i++) {
                const angle = angle_offset + (i * 2 * Math.PI / num_lines);
                const start_radius = radius * 0.2;
                const end_radius = radius * (1 - (wp.turns_left / 4) * 0.5);

                ctx.beginPath();
                ctx.moveTo(Math.cos(angle) * start_radius, Math.sin(angle) * start_radius);
                ctx.quadraticCurveTo(
                    Math.cos(angle + wp.swirl * 2) * radius * 0.6,
                    Math.sin(angle + wp.swirl * 2) * radius * 0.6,
                    Math.cos(angle + wp.swirl * 4) * end_radius,
                    Math.sin(angle + wp.swirl * 4) * end_radius
                );
                ctx.strokeStyle = team.color;
                ctx.lineWidth = 1.5;
                ctx.globalAlpha = 0.5 * (wp.turns_left / 4);
                ctx.stroke();
            }
            ctx.restore();
        });
    }

    function drawNexuses(gameState, isHighlightingActive = false) {
        const allNexuses = [];
        if (gameState.nexuses) {
            for (const teamId in gameState.nexuses) {
                gameState.nexuses[teamId].forEach(n => allNexuses.push({ ...n, teamId: teamId, is_attuned: false }));
            }
        }
        if (gameState.attuned_nexuses) {
            Object.values(gameState.attuned_nexuses).forEach(n => allNexuses.push({ ...n, is_attuned: true }));
        }
        if (allNexuses.length === 0) return;
    
        allNexuses.forEach(nexus => {
            const team = gameState.teams[nexus.teamId];
            if (!team) return;

            const isHighlighted = nexus.point_ids.every(pid => uiState.lastActionHighlights.points.has(pid));
            ctx.save();
            if (isHighlightingActive && !isHighlighted) {
                ctx.globalAlpha = 0.2;
            } else if (isHighlightingActive && isHighlighted) {
                ctx.globalAlpha = 1.0;
            }
            const points = nexus.point_ids.map(pid => gameState.points[pid]).filter(p => p);
            if (points.length !== 4) return;
            
            const center = nexus.center;
            points.sort((a, b) => Math.atan2(a.y - center.y, a.x - center.x) - Math.atan2(b.y - center.y, b.x - center.x));
            
            ctx.beginPath();
            ctx.moveTo((points[0].x + 0.5) * cellSize, (points[0].y + 0.5) * cellSize);
            for (let i = 1; i < points.length; i++) {
                 ctx.lineTo((points[i].x + 0.5) * cellSize, (points[i].y + 0.5) * cellSize);
            }
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
            ctx.globalAlpha = 1.0;
            ctx.beginPath();
            ctx.arc(orb_cx, orb_cy, glow_radius, 0, 2 * Math.PI);
            ctx.fill();

            ctx.fillStyle = team.color;
            ctx.beginPath();
            ctx.arc(orb_cx, orb_cy, (nexus.is_attuned ? 6 : 4) + pulse * 2, 0, 2 * Math.PI);
            ctx.fill();

            if (nexus.is_attuned) {
                ctx.beginPath();
                ctx.arc(orb_cx, orb_cy, Math.sqrt(nexus.radius_sq) * cellSize, 0, 2 * Math.PI);
                ctx.strokeStyle = team.color;
                ctx.globalAlpha = 0.1 + pulse * 0.15;
                ctx.lineWidth = 1 + pulse * 2;
                ctx.stroke();
            }

            ctx.restore();
        });
    }

    function drawRiftSpires(gameState, isHighlightingActive = false) {
        if (!gameState.rift_spires) return;

        for (const spireId in gameState.rift_spires) {
            const spire = gameState.rift_spires[spireId];
            const team = gameState.teams[spire.teamId];
            if (!team) continue;

            const isHighlighted = uiState.lastActionHighlights.structures.has(spire.id);
            ctx.save();
            if (isHighlightingActive && !isHighlighted) {
                ctx.globalAlpha = 0.2;
            } else if (isHighlightingActive && isHighlighted) {
                ctx.globalAlpha = 1.0;
            }

            const cx = (spire.coords.x + 0.5) * cellSize;
            const cy = (spire.coords.y + 0.5) * cellSize;
            const now = Date.now();
            const rotation = (now / 4000) % (2 * Math.PI);
            const pulse = Math.abs(Math.sin(now / 300));
            const charge_level = spire.charge / spire.charge_needed;

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

    function drawRiftTraps(gameState, isHighlightingActive = false) {
        if (!gameState.rift_traps) return;

        gameState.rift_traps.forEach(trap => {
            const team = gameState.teams[trap.teamId];
            if (!team) return;

            const isHighlighted = uiState.lastActionHighlights.structures.has(trap.id);
            ctx.save();
            if (isHighlightingActive && !isHighlighted) {
                ctx.globalAlpha = 0.2;
            } else if (isHighlightingActive && isHighlighted) {
                ctx.globalAlpha = 1.0;
            }

            const cx = (trap.coords.x + 0.5) * cellSize;
            const cy = (trap.coords.y + 0.5) * cellSize;
            const flicker = (Math.sin(Date.now() / 100) + Math.sin(Date.now() / 237)) / 2;
            const radius = Math.sqrt(trap.radius_sq) * cellSize;

            ctx.save();
            ctx.globalAlpha = 0.3 + flicker * 0.4;
            ctx.strokeStyle = team.color;
            ctx.lineWidth = 1.5;

            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0.2, Math.PI - 0.2);
            ctx.stroke();

            ctx.beginPath();
            ctx.arc(cx, cy, radius, Math.PI + 0.2, 2 * Math.PI - 0.2);
            ctx.stroke();

            ctx.restore();
        });
    }

    function drawScorchedZones(gameState, isHighlightingActive = false) {
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
                illustrationHelpers.drawJaggedLine(ctx,
                    {x: (triPoints[0].x + 0.5) * cellSize, y: (triPoints[0].y + 0.5) * cellSize},
                    {x: (triPoints[1].x + 0.5) * cellSize, y: (triPoints[1].y + 0.5) * cellSize},
                    10, 3
                );
                illustrationHelpers.drawJaggedLine(ctx,
                    {x: (triPoints[1].x + 0.5) * cellSize, y: (triPoints[1].y + 0.5) * cellSize},
                    {x: (triPoints[2].x + 0.5) * cellSize, y: (triPoints[2].y + 0.5) * cellSize},
                    10, 3
                );
                illustrationHelpers.drawJaggedLine(ctx,
                    {x: (triPoints[2].x + 0.5) * cellSize, y: (triPoints[2].y + 0.5) * cellSize},
                    {x: (triPoints[0].x + 0.5) * cellSize, y: (triPoints[0].y + 0.5) * cellSize},
                    10, 3
                );
            }
            ctx.restore();
        });
    }

    function drawBarricades(gameState, isHighlightingActive = false) {
        if (!gameState.barricades) return;
        gameState.barricades.forEach(barricade => {
            const team = gameState.teams[barricade.teamId];
            if (!team) return;
            const isHighlighted = uiState.lastActionHighlights.structures.has(barricade.id);
            ctx.save();
            if (isHighlightingActive && !isHighlighted) {
                ctx.globalAlpha = 0.2;
            } else if (isHighlightingActive && isHighlighted) {
                ctx.globalAlpha = 1.0;
            }
            const p1 = {x: (barricade.p1.x + 0.5) * cellSize, y: (barricade.p1.y + 0.5) * cellSize};
            const p2 = {x: (barricade.p2.x + 0.5) * cellSize, y: (barricade.p2.y + 0.5) * cellSize};
            ctx.strokeStyle = team.color;
            ctx.globalAlpha *= (0.5 + (barricade.turns_left / 5) * 0.5);
            ctx.lineWidth = 6;
            ctx.lineCap = 'round';
            illustrationHelpers.drawJaggedLine(ctx, p1, p2, 10, 4);
            ctx.globalAlpha *= 0.8;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
            ctx.lineCap = 'butt';
            ctx.restore();
        });
    }

    function drawLeyLines(gameState, isHighlightingActive = false) {
        if (!gameState.ley_lines) return;
        for (const leyLineId in gameState.ley_lines) {
            const ley_line = gameState.ley_lines[leyLineId];
            const team = gameState.teams[ley_line.teamId];
            if (!team) continue;
            const isHighlighted = ley_line.point_ids.every(pid => uiState.lastActionHighlights.points.has(pid));
            ctx.save();
            if (isHighlightingActive && !isHighlighted) {
                ctx.globalAlpha = 0.2;
            } else if (isHighlightingActive && isHighlighted) {
                ctx.globalAlpha = 1.0;
            }
            const points = ley_line.point_ids.map(pid => gameState.points[pid]).filter(p => p);
            if (points.length < 2) {
                ctx.restore();
                continue;
            }
            const p1 = points[0];
            const p2 = points[points.length - 1];
            const x1 = (p1.x + 0.5) * cellSize;
            const y1 = (p1.y + 0.5) * cellSize;
            const x2 = (p2.x + 0.5) * cellSize;
            const y2 = (p2.y + 0.5) * cellSize;
            const pulse = Math.abs(Math.sin(Date.now() / 600));
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.strokeStyle = team.color;
            ctx.lineWidth = 10 + pulse * 4;
            ctx.globalAlpha *= (0.3 + pulse * 0.2);
            ctx.filter = 'blur(5px)';
            ctx.stroke();
            ctx.restore();
        }
    }

    function drawWonders(gameState, isHighlightingActive = false) {
        if (!gameState.wonders) return;
        for (const wonderId in gameState.wonders) {
            const wonder = gameState.wonders[wonderId];
            const team = gameState.teams[wonder.teamId];
            if (!team || wonder.type !== 'ChronosSpire') continue;
            const isHighlighted = uiState.lastActionHighlights.structures.has(wonder.id);
            ctx.save();
            if (isHighlightingActive && !isHighlighted) {
                ctx.globalAlpha = 0.2;
            } else if (isHighlightingActive && isHighlighted) {
                ctx.globalAlpha = 1.0;
            }
            const cx = (wonder.coords.x + 0.5) * cellSize;
            const cy = (wonder.coords.y + 0.5) * cellSize;
            const now = Date.now();
            const pulse = Math.abs(Math.sin(now / 500));
            const rotation = (now / 5000) % (2 * Math.PI);
            const baseRadius = 20;
            ctx.beginPath();
            ctx.arc(cx, cy, baseRadius, 0, 2 * Math.PI);
            const currentAlpha = ctx.globalAlpha;
            const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, baseRadius);
            gradient.addColorStop(0, team.color + "99");
            gradient.addColorStop(1, team.color + "00");
            ctx.fillStyle = gradient;
            ctx.globalAlpha = currentAlpha * (0.3 + pulse * 0.2);
            ctx.fill();
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(rotation);
            ctx.strokeStyle = team.color;
            ctx.lineWidth = 1.5;
            ctx.globalAlpha = currentAlpha * 0.8;
            ctx.beginPath();
            ctx.arc(0, 0, baseRadius * 0.7, 0, 2 * Math.PI);
            ctx.stroke();
            ctx.rotate(Math.PI / 2);
            ctx.beginPath();
            ctx.arc(0, 0, baseRadius * 1.2, 0, 1.5 * Math.PI);
            ctx.stroke();
            ctx.restore();
            ctx.beginPath();
            ctx.arc(cx, cy, 5 + pulse * 2, 0, 2 * Math.PI);
            ctx.fillStyle = '#fff';
            ctx.fill();
            ctx.beginPath();
            ctx.arc(cx, cy, 2 + pulse, 0, 2 * Math.PI);
            ctx.fillStyle = team.color;
            ctx.fill();
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 14px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.shadowColor = 'black';
            ctx.shadowBlur = 4;
            ctx.fillText(wonder.turns_to_victory, cx, cy);
            ctx.shadowBlur = 0;
            ctx.restore();
        }
    }

    function drawPrisms(gameState, isHighlightingActive = false) {
        if (!gameState.prisms) return;
        for (const teamId in gameState.prisms) {
            const teamPrisms = gameState.prisms[teamId];
            const team = gameState.teams[teamId];
            if (!team || !teamPrisms) continue;
            teamPrisms.forEach(prism => {
                const isHighlighted = prism.all_point_ids.every(pid => uiState.lastActionHighlights.points.has(pid));
                ctx.save();
                if (isHighlightingActive && !isHighlighted) {
                    ctx.globalAlpha = 0.2;
                } else if (isHighlightingActive && isHighlighted) {
                    ctx.globalAlpha = 1.0;
                }
                const p1 = gameState.points[prism.shared_p1_id];
                const p2 = gameState.points[prism.shared_p2_id];
                if (p1 && p2) {
                    const x1 = (p1.x + 0.5) * cellSize;
                    const y1 = (p1.y + 0.5) * cellSize;
                    const x2 = (p2.x + 0.5) * cellSize;
                    const y2 = (p2.y + 0.5) * cellSize;
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.strokeStyle = team.color;
                    ctx.lineWidth = 8;
                    ctx.globalAlpha *= 0.5;
                    ctx.filter = 'blur(4px)';
                    ctx.stroke();
                    ctx.filter = 'none';
                }
                ctx.restore();
            });
        }
    }
    
    function drawHeartwoods(gameState, isHighlightingActive = false) {
        if (!gameState.heartwoods) return;

        for (const teamId in gameState.heartwoods) {
            const heartwood = gameState.heartwoods[teamId];
            const team = gameState.teams[teamId];
            if (!team) continue;

            const isHighlighted = uiState.lastActionHighlights.structures.has(heartwood.id);
            ctx.save();
            if (isHighlightingActive && !isHighlighted) {
                ctx.globalAlpha = 0.2;
            } else if (isHighlightingActive && isHighlighted) {
                ctx.globalAlpha = 1.0;
            }

            const cx = (heartwood.center_coords.x + 0.5) * cellSize;
            const cy = (heartwood.center_coords.y + 0.5) * cellSize;
            const radius = 15;
            
            // Aura
            const pulse = Math.abs(Math.sin(Date.now() / 800));
            const aura_radius = Math.sqrt(heartwood.aura_radius_sq) * cellSize;
            ctx.beginPath();
            ctx.arc(cx, cy, aura_radius, 0, 2 * Math.PI);
            ctx.fillStyle = team.color;
            ctx.globalAlpha *= (0.1 + pulse * 0.1);
            ctx.fill();

            // Core
            ctx.globalAlpha = isHighlightingActive && !isHighlighted ? 0.2 : 1.0;
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
            ctx.fillStyle = team.color;
            ctx.fill();
            
            // Symbol
            ctx.font = 'bold 24px Arial';
            ctx.fillStyle = 'white';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('❤', cx, cy + 1);

            ctx.restore();
        }
    }

    // --- Data-Driven Drawing ---
    
    const drawOrchestrator = {
        // Defines the render order. Functions receive (gameState, isHighlightingActive).
        renderLayers: [
            drawTerritories, drawMonoliths, drawTrebuchets, drawPrisms,
            drawRunes, drawNexuses, drawHeartwoods, drawWonders, drawRiftSpires,
            drawRiftTraps, drawFissures, drawBarricades, drawScorchedZones,
            drawLeyLines, drawLines, drawPoints,
            (gs) => drawHulls(gs.interpretation, gs.teams)
        ],
        // Defines how to draw specific rune types.
        runeDrawers: {
            'v_shape': (rune, team, gameState) => {
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
                ctx.globalAlpha *= 0.4;
                ctx.stroke();
            },
            'trident': (rune, team, gameState) => {
                const p_apex = gameState.points[rune.apex_id];
                const p_h = gameState.points[rune.handle_id];
                const p_p1 = gameState.points[rune.prong_ids[0]];
                const p_p2 = gameState.points[rune.prong_ids[1]];
                if (!p_apex || !p_h || !p_p1 || !p_p2) return;
                ctx.beginPath();
                ctx.moveTo((p_h.x + 0.5) * cellSize, (p_h.y + 0.5) * cellSize);
                ctx.lineTo((p_apex.x + 0.5) * cellSize, (p_apex.y + 0.5) * cellSize);
                ctx.moveTo((p_p1.x + 0.5) * cellSize, (p_p1.y + 0.5) * cellSize);
                ctx.lineTo((p_apex.x + 0.5) * cellSize, (p_apex.y + 0.5) * cellSize);
                ctx.lineTo((p_p2.x + 0.5) * cellSize, (p_p2.y + 0.5) * cellSize);
                ctx.strokeStyle = team.color;
                ctx.lineWidth = 8;
                ctx.globalAlpha *= 0.4;
                ctx.filter = 'blur(2px)';
                ctx.stroke();
                ctx.filter = 'none';
            },
            'cross': (rune_p_ids, team, gameState) => {
                const points = rune_p_ids.map(pid => gameState.points[pid]).filter(p => p);
                if (points.length !== 4) return;
                const centroid = { x: points.reduce((acc, p) => acc + p.x, 0) / 4, y: points.reduce((acc, p) => acc + p.y, 0) / 4 };
                points.sort((a, b) => Math.atan2(a.y - centroid.y, a.x - centroid.x) - Math.atan2(b.y - centroid.y, b.x - centroid.x));
                ctx.beginPath();
                ctx.moveTo((points[0].x + 0.5) * cellSize, (points[0].y + 0.5) * cellSize);
                for (let i = 1; i < points.length; i++) {
                     ctx.lineTo((points[i].x + 0.5) * cellSize, (points[i].y + 0.5) * cellSize);
                }
                ctx.closePath();
                ctx.fillStyle = team.color;
                ctx.globalAlpha *= 0.2;
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
                ctx.fillStyle = team.color;
                ctx.globalAlpha = currentAlpha * 0.25;
                ctx.fill();
                const pulse = Math.abs(Math.sin(Date.now() / 500));
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 1 + pulse * 2;
                ctx.globalAlpha = currentAlpha * (0.3 + pulse * 0.4);
                ctx.stroke();
            },
            'hourglass': (rune, team, gameState) => {
                const p_v = gameState.points[rune.vertex_id];
                if (!p_v) return;
                const all_points = rune.all_points.map(pid => gameState.points[pid]);
                if (all_points.some(p => !p)) return;
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
                ctx.strokeStyle = team.color;
                ctx.lineWidth = 6;
                ctx.globalAlpha *= 0.4;
                ctx.stroke();
            }
        }
    };

    function drawRunes(gameState, isHighlightingActive = false) {
        if (!gameState.runes) return;
        for (const teamId in gameState.runes) {
            const teamRunes = gameState.runes[teamId];
            const team = gameState.teams[teamId];
            if (!team) continue;
    
            for (const runeType in teamRunes) {
                const drawer = drawOrchestrator.runeDrawers[runeType];
                if (!drawer) continue;
    
                teamRunes[runeType].forEach(rune => {
                    const pointIds = rune.point_ids || rune.all_points || (Array.isArray(rune) ? rune : null);
                    if (!pointIds) return;
                    
                    const isHighlighted = pointIds.every(pid => uiState.lastActionHighlights.points.has(pid));
                    ctx.save();
                    if (isHighlightingActive && !isHighlighted) {
                        ctx.globalAlpha = 0.2;
                    } else if (isHighlightingActive && isHighlighted) {
                        ctx.globalAlpha = 1.0;
                    }
                    drawer(rune, team, gameState);
                    ctx.restore();
                });
            }
        }
    }
    
    function drawFissures(gameState, isHighlightingActive = false) {
        if (!gameState.fissures) return;
        gameState.fissures.forEach(fissure => {
            const isHighlighted = uiState.lastActionHighlights.structures.has(fissure.id);
            ctx.save();
            if (isHighlightingActive && !isHighlighted) {
                ctx.globalAlpha = 0.2;
            } else if (isHighlightingActive && isHighlighted) {
                ctx.globalAlpha = 1.0;
            }
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

    function fullRender() {
        if (!currentGameState) return;

        drawGrid();

        const isHighlightingActive = uiState.debugOptions.highlightLastAction && 
            (uiState.lastActionHighlights.points.size > 0 || uiState.lastActionHighlights.lines.size > 0 || uiState.lastActionHighlights.structures.size > 0);

        if (currentGameState.game_phase === 'SETUP') {
             const tempPointsDict = {};
             uiState.initialPoints.forEach((p, i) => tempPointsDict[`p_${i}`] = {...p, id: `p_${i}`});
             drawPoints(tempPointsDict, uiState.localTeams, isHighlightingActive);
        } else if (currentGameState.teams) {
            // Render all layers in their defined order
            drawOrchestrator.renderLayers.forEach(drawFn => {
                if(drawFn.name === 'drawLines' || drawFn.name === 'drawPoints') {
                     drawFn(currentGameState.points, currentGameState[drawFn.name.substring(4).toLowerCase()], currentGameState.teams, isHighlightingActive);
                } else if(drawFn.name === 'drawHulls') {
                    if (currentGameState.game_phase === 'FINISHED') {
                         drawFn(currentGameState.interpretation, currentGameState.teams);
                    }
                }
                else {
                    drawFn(currentGameState, isHighlightingActive);
                }
            });
        }
        drawVisualEffects();
    }

    // Main animation loop
    function animationLoop() {
        fullRender();
        requestAnimationFrame(animationLoop);
    }
    
    const actionVisualsMap = {
        'isolate_point': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.isolated_point.id);
            uiState.lastActionHighlights.points.add(details.projector_point.id);
            if (details.projector_point && details.isolated_point) {
                uiState.visualEffects.push({
                    type: 'animated_ray',
                    p1: details.projector_point,
                    p2: details.isolated_point,
                    startTime: Date.now(),
                    duration: 800,
                    color: 'rgba(200, 100, 255, 1.0)',
                    lineWidth: 3
                });
            }
        },
        'isolate_fizzle_barricade': (details, gameState) => {
            uiState.lastActionHighlights.structures.add(details.barricade.id);
            uiState.visualEffects.push({
                type: 'growing_wall',
                barricade: details.barricade,
                color: gameState.teams[details.barricade.teamId].color,
                startTime: Date.now(),
                duration: 800
            });
        },
        'nova_burst': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.sacrificed_point.id);
            let particles = [];
            for(let i=0; i<20; i++) {
                particles.push({angle: Math.random() * 2 * Math.PI, speed: (150 + Math.random() * 50) * (cellSize/10)});
            }
            uiState.visualEffects.push({
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
            uiState.lastActionHighlights.lines.add(details.line.id);
            uiState.lastActionHighlights.points.add(details.line.p1_id);
            uiState.lastActionHighlights.points.add(details.line.p2_id);
            uiState.visualEffects.push({
                type: 'new_line', line: details.line, startTime: Date.now(), duration: 500
            });
        },
        'add_line_fizzle_strengthen': (details, gameState) => {
            uiState.lastActionHighlights.lines.add(details.strengthened_line.id);
            uiState.visualEffects.push({ type: 'line_flash', line: details.strengthened_line, startTime: Date.now(), duration: 800 });
        },
        'fracture_line': (details, gameState) => {
            uiState.visualEffects.push({
                type: 'line_crack',
                old_line: details.old_line,
                new_point: details.new_point,
                color: gameState.teams[details.new_point.teamId].color,
                startTime: Date.now(),
                duration: 800,
            });
            uiState.lastActionHighlights.points.add(details.new_point.id);
            uiState.lastActionHighlights.lines.add(details.new_line1.id);
            uiState.lastActionHighlights.lines.add(details.new_line2.id);
        },
        'convert_point': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.converted_point.id);
            const line = details.sacrificed_line;
            const p1 = gameState.points[line.p1_id];
            const p2 = gameState.points[line.p2_id];
            if (p1 && p2) {
                 const midpoint = {x: (p1.x+p2.x)/2, y: (p1.y+p2.y)/2};
                 uiState.visualEffects.push({
                     type: 'energy_spiral',
                     start: midpoint,
                     end: details.converted_point,
                     color: gameState.teams[details.converted_point.teamId].color,
                     startTime: Date.now(),
                     duration: 1000
                 });
            }
        },
        'convert_fizzle_push': (details, gameState) => {
            uiState.visualEffects.push({
                type: 'shield_pulse',
                center: details.pulse_center,
                radius_sq: details.radius_sq,
                color: 'rgba(255, 180, 50, 0.9)',
                startTime: Date.now(),
                duration: 800,
            });
        },
        'attack_line': (details, gameState) => {
            uiState.lastActionHighlights.lines.add(details.attacker_line.id);
            uiState.visualEffects.push({
                type: 'animated_ray',
                p1: details.attack_ray.p1,
                p2: details.attack_ray.p2,
                startTime: Date.now(),
                duration: 600,
                color: details.bypassed_shield ? 'rgba(255, 100, 255, 1.0)' : 'rgba(255, 0, 0, 1.0)'
            });
        },
        'attack_line_energized': (details, gameState) => {
            uiState.lastActionHighlights.lines.add(details.attacker_line.id);
            uiState.visualEffects.push({
                type: 'animated_ray',
                p1: details.attack_ray.p1,
                p2: details.attack_ray.p2,
                startTime: Date.now(),
                duration: 600,
                color: 'rgba(255, 255, 100, 1.0)',
                lineWidth: 5
            });
            details.destroyed_points.forEach(p => {
                uiState.visualEffects.push({ type: 'point_explosion', x: p.x, y: p.y, startTime: Date.now() + 200, duration: 500 });
            });
        },
        'rune_shoot_bisector': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.visualEffects.push({
                type: 'animated_ray',
                p1: details.attack_ray.p1,
                p2: details.attack_ray.p2,
                startTime: Date.now(),
                duration: 800,
                color: 'rgba(100, 255, 255, 1.0)',
                lineWidth: 4,
            });
        },
        'vbeam_miss_fissure': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.visualEffects.push({ type: 'animated_ray', p1: details.attack_ray.p1, p2: details.attack_ray.p2, startTime: Date.now(), duration: 800, color: 'rgba(100, 255, 255, 1.0)', lineWidth: 4});
            uiState.visualEffects.push({ type: 'growing_wall', barricade: details.fissure, color: 'rgba(50, 50, 50, 0.8)', startTime: Date.now() + 200, duration: 1000 });
        },
        'rune_area_shield': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            const tri_points = details.rune_triangle_ids.map(pid => gameState.points[pid]).filter(p=>p);
            if(tri_points.length === 3) {
                uiState.visualEffects.push({
                    type: 'polygon_flash',
                    points: tri_points,
                    color: 'rgba(173, 216, 230, 0.9)',
                    startTime: Date.now(),
                    duration: 1000
                });
            }
        },
        'area_shield_fizzle_push': (details, gameState) => {
             details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
             uiState.visualEffects.push({ type: 'shield_pulse', center: details.pulse_center, radius_sq: details.pulse_radius_sq, color: `rgba(173, 216, 230, 0.9)`, startTime: Date.now(), duration: 800 });
        },
        'rune_shield_pulse': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.visualEffects.push({
                type: 'shield_pulse',
                center: details.pulse_center,
                radius_sq: details.pulse_radius_sq,
                color: `rgba(173, 216, 230, 0.9)`,
                startTime: Date.now(),
                duration: 800,
            });
        },
        'shield_pulse_fizzle_pull': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            // The payload contains the *final* positions. For a correct visual, we'd need
            // the start positions. This is a best-effort visual using the data available.
            uiState.visualEffects.push({
                type: 'point_pull',
                center: details.pulse_center,
                points: details.pulled_points,
                startTime: Date.now(),
                duration: 1000,
            });
        },
        'extend_line': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.new_point.id);
            const origin_point = gameState.points[details.origin_point_id];
            if (origin_point) {
                const teamColor = gameState.teams[details.new_point.teamId].color;
                uiState.visualEffects.push({
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
                uiState.lastActionHighlights.lines.add(details.new_line.id);
            }
        },
        'shield_line': (details, gameState) => {
            uiState.lastActionHighlights.lines.add(details.shielded_line.id);
             uiState.visualEffects.push({
                type: 'bastion_formation',
                line_ids: [details.shielded_line.id],
                startTime: Date.now(),
                duration: 800
            });
        },
        'claim_territory': (details, gameState) => {
            details.territory.point_ids.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            const triPoints = details.territory.point_ids.map(id => gameState.points[id]).filter(Boolean);
            if (triPoints.length === 3) {
                uiState.visualEffects.push({
                    type: 'territory_fill',
                    points: triPoints,
                    color: gameState.teams[details.territory.teamId].color,
                    startTime: Date.now(),
                    duration: 1000,
                });
            }
        },
        'create_anchor': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.anchor_point.id);
            if(details.sacrificed_point) {
                 uiState.visualEffects.push({
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
            uiState.visualEffects.push({
                type: 'point_implosion',
                x: details.sacrificed_point.x,
                y: details.sacrificed_point.y,
                startTime: Date.now(),
                duration: 1200,
                color: currentGameState.teams[details.sacrificed_point.teamId]?.color || `rgba(150, 220, 255, 1)`
            });
        },
        'mirror_structure': (details, gameState) => {
            details.new_points.forEach(p => uiState.lastActionHighlights.points.add(p.id));
            uiState.lastActionHighlights.points.add(details.axis_p1_id);
            uiState.lastActionHighlights.points.add(details.axis_p2_id);
            uiState.visualEffects.push({
                type: 'mirror_axis',
                p1_id: details.axis_p1_id,
                p2_id: details.axis_p2_id,
                startTime: Date.now(),
                duration: 1500
            });
        },
        'mirror_fizzle_strengthen': (details, gameState) => {
            details.strengthened_lines.forEach(line => {
                uiState.lastActionHighlights.lines.add(line.id);
                uiState.visualEffects.push({ type: 'line_flash', line: line, startTime: Date.now(), duration: 800 });
            });
        },
        'create_orbital': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.center_point_id);
            const center_point = gameState.points[details.center_point_id];

            details.new_points.forEach((p, i) => {
                uiState.lastActionHighlights.points.add(p.id);
                uiState.visualEffects.push({
                    type: 'energy_spiral',
                    start: center_point,
                    end: p,
                    color: gameState.teams[p.teamId].color,
                    startTime: Date.now() + i * 50,
                    duration: 800
                });
            });
            details.new_lines.forEach(l => uiState.lastActionHighlights.lines.add(l.id));
        },
        'form_bastion': (details, gameState) => {
            uiState.visualEffects.push({
                type: 'bastion_formation',
                line_ids: details.line_ids,
                color: gameState.teams[details.bastion.teamId].color,
                startTime: Date.now(),
                duration: 1200
            });
        },
        'attune_nexus': (details, gameState) => {
            details.attuned_nexus.point_ids.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.lastActionHighlights.structures.add(details.attuned_nexus.id);
            const line = details.sacrificed_line;
            const p1 = gameState.points[line.p1_id];
            const p2 = gameState.points[line.p2_id];
            if (p1 && p2) {
                 uiState.visualEffects.push({
                     type: 'point_pull',
                     center: details.attuned_nexus.center,
                     points: [p1, p2],
                     startTime: Date.now(),
                     duration: 1000,
                 });
            }
        },
        'form_monolith': (details, gameState) => {
            uiState.visualEffects.push({
                type: 'monolith_formation',
                center: details.monolith.center_coords,
                color: gameState.teams[details.monolith.teamId].color,
                startTime: Date.now(),
                duration: 1500
            });
        },
        'chain_lightning': (details, gameState) => {
            if (details.rune_points) { // It may not exist if structure was destroyed
                details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            }
            uiState.visualEffects.push({
                type: 'chain_lightning',
                point_ids: details.rune_points,
                destroyed_point: details.destroyed_point,
                startTime: Date.now(),
                duration: 1000
            });
            if (details.destroyed_point) {
                uiState.visualEffects.push({
                    type: 'point_explosion',
                    x: details.destroyed_point.x,
                    y: details.destroyed_point.y,
                    startTime: Date.now() + 400,
                    duration: 500
                });
            }
        },
        'refraction_beam': (details, gameState) => {
            details.prism_point_ids.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.visualEffects.push({
                type: 'attack_ray', p1: details.source_ray.p1, p2: details.source_ray.p2, startTime: Date.now(), duration: 1200, color: `rgba(255, 255, 150, 1)`, lineWidth: 2
            });
            uiState.visualEffects.push({
                type: 'attack_ray', p1: details.refracted_ray.p1, p2: details.refracted_ray.p2, startTime: Date.now() + 200, duration: 1000, color: `rgba(255, 100, 100, 1)`, lineWidth: 4
            });
        },
        'bastion_pulse': (details, gameState) => {
            const bastion = gameState.bastions[details.bastion_id];
            if(bastion) {
                uiState.lastActionHighlights.points.add(bastion.core_id);
                bastion.prong_ids.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            }
            uiState.visualEffects.push({
                type: 'point_implosion', x: details.sacrificed_point.x, y: details.sacrificed_point.y, startTime: Date.now(), duration: 800, color: currentGameState.teams[details.sacrificed_point.teamId]?.color
            });
        },
        'sentry_zap': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
             uiState.visualEffects.push({
                type: 'attack_ray', p1: details.attack_ray.p1, p2: details.attack_ray.p2, startTime: Date.now(), duration: 400, color: `rgba(255, 100, 100, 1)`, lineWidth: 2
            });
            uiState.visualEffects.push({
                type: 'point_explosion', x: details.destroyed_point.x, y: details.destroyed_point.y, startTime: Date.now(), duration: 600
            });
        },
        'cultivate_heartwood': (details, gameState) => {
            details.sacrificed_points.forEach(p => uiState.lastActionHighlights.points.add(p.id));
            uiState.visualEffects.push({
                type: 'heartwood_creation', sacrificed_points: details.sacrificed_points, center_coords: details.heartwood.center_coords, startTime: Date.now(), duration: 1500
            });
        },
        'form_purifier': (details, gameState) => {
            details.purifier.point_ids.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            const points = details.purifier.point_ids.map(pid => gameState.points[pid]).filter(Boolean);
            if(points.length === 5) {
                uiState.visualEffects.push({
                    type: 'polygon_flash',
                    points: points,
                    color: 'rgba(255, 255, 220, 1.0)',
                    startTime: Date.now(),
                    duration: 1200
                });
            }
        },
        'launch_payload': (details, gameState) => {
            details.trebuchet_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            const launch_point = gameState.points[details.launch_point_id];
            if (launch_point) {
                uiState.visualEffects.push({
                    type: 'arc_projectile', start: launch_point, end: details.destroyed_point, startTime: Date.now(), duration: 1200
                });
            }
            uiState.visualEffects.push({
                type: 'point_explosion', x: details.destroyed_point.x, y: details.destroyed_point.y, startTime: Date.now() + 1200, duration: 800
            });
        },
        'rune_hourglass_stasis': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.lastActionHighlights.points.add(details.target_point.id);
        },
        'create_rift_trap': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.sacrificed_point.id);
            uiState.visualEffects.push({
                type: 'point_implosion',
                x: details.sacrificed_point.x,
                y: details.sacrificed_point.y,
                startTime: Date.now(),
                duration: 800,
                color: currentGameState.teams[details.sacrificed_point.teamId]?.color
            });
        },
        'phase_shift': (details, gameState) => {
            const teamColor = gameState.teams[details.sacrificed_line.teamId].color;
            if (details.original_coords) {
                uiState.visualEffects.push({
                    type: 'portal_link',
                    p1: details.original_coords,
                    p2: details.new_coords,
                    color: teamColor,
                    startTime: Date.now(),
                    duration: 1000
                });
            }
            uiState.lastActionHighlights.points.add(details.moved_point_id);
        },
        'pincer_attack': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.attacker_p1_id);
            uiState.lastActionHighlights.points.add(details.attacker_p2_id);
            const p1 = gameState.points[details.attacker_p1_id];
            const p2 = gameState.points[details.attacker_p2_id];
            const target = details.destroyed_point;

            if (p1 && target) {
                 uiState.visualEffects.push({ type: 'animated_ray', p1: p1, p2: target, startTime: Date.now(), duration: 500, color: 'rgba(255,0,0,1.0)' });
            }
            if (p2 && target) {
                uiState.visualEffects.push({ type: 'animated_ray', p1: p2, p2: target, startTime: Date.now(), duration: 500, color: 'rgba(255,0,0,1.0)' });
            }
            uiState.visualEffects.push({ type: 'point_explosion', x: target.x, y: target.y, startTime: Date.now(), duration: 600 });
        },
        'rune_impale': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.visualEffects.push({
                type: 'animated_ray',
                p1: details.attack_ray.p1,
                p2: details.attack_ray.p2,
                startTime: Date.now(),
                duration: 500,
                color: 'rgba(255, 100, 255, 1.0)',
                lineWidth: 6,
            });
            details.intersection_points.forEach(p_intersect => {
                uiState.visualEffects.push({
                    type: 'point_explosion',
                    x: p_intersect.x,
                    y: p_intersect.y,
                    startTime: Date.now(),
                    duration: 400
                });
            });
        },
        'territory_strike': (details, gameState) => {
            details.territory_point_ids.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.visualEffects.push({
                type: 'attack_ray', p1: details.attack_ray.p1, p2: details.attack_ray.p2, startTime: Date.now(), duration: 900, color: 'rgba(100, 255, 100, 1.0)', lineWidth: 3
            });
            uiState.visualEffects.push({
                type: 'point_explosion', x: details.destroyed_point.x, y: details.destroyed_point.y, startTime: Date.now() + 500, duration: 600
            });
        },
        'purify_territory': (details, gameState) => {
            details.purifier_point_ids.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.visualEffects.push({
                type: 'territory_fade', territory: details.cleansed_territory, startTime: Date.now(), duration: 1500
            });
        },
        'build_chronos_spire': (details, gameState) => {
            uiState.visualEffects.push({
                type: 'point_implosion', x: details.wonder.coords.x, y: details.wonder.coords.y, startTime: Date.now(), duration: 2000, color: `rgba(255, 255, 150, 1)`
            });
        },
        'form_rift_spire': (details, gameState) => {
            uiState.visualEffects.push({
                type: 'point_implosion', x: details.spire.coords.x, y: details.spire.coords.y, startTime: Date.now(), duration: 1500, color: `rgba(200, 100, 255, 1)`
            });
        },
        'raise_barricade': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.visualEffects.push({
                type: 'growing_wall',
                barricade: details.barricade,
                color: gameState.teams[details.barricade.teamId].color,
                startTime: Date.now(),
                duration: 1000
            });
        },
        'attack_miss_spawn': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.new_point.id);
            uiState.lastActionHighlights.lines.add(details.attacker_line.id);
            const origin_point = details.attack_ray.p1;
            if (origin_point) {
                uiState.visualEffects.push({
                    type: 'animated_ray',
                    p1: origin_point,
                    p2: details.new_point,
                    startTime: Date.now(),
                    duration: 700,
                    color: gameState.teams[details.new_point.teamId].color,
                    lineWidth: 2
                });
            }
        },
        'nova_shockwave': (details, gameState) => {
            uiState.visualEffects.push({
                type: 'shield_pulse',
                center: details.sacrificed_point,
                radius_sq: (gameState.grid_size * 0.25)**2,
                color: 'rgba(255, 180, 50, 0.9)',
                startTime: Date.now(),
                duration: 800,
            });
        },
        'whirlpool_fizzle_fissure': (details, gameState) => {
             uiState.visualEffects.push({
                type: 'growing_wall',
                barricade: details.fissure,
                color: 'rgba(50, 50, 50, 0.8)',
                startTime: Date.now(),
                duration: 1000
            });
        },
        'pincer_fizzle_barricade': (details, gameState) => {
            details.pincer_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.visualEffects.push({
                type: 'growing_wall',
                barricade: details.barricade,
                color: gameState.teams[details.barricade.teamId].color,
                startTime: Date.now(),
                duration: 800,
            });
        },
        'rotate_point': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.moved_point.id);
            if (details.pivot_point && !details.is_grid_center) {
                uiState.lastActionHighlights.points.add(details.pivot_point.id);
            }
        },
        'impale_fizzle_barricade': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.visualEffects.push({
                type: 'animated_ray',
                p1: details.attack_ray.p1, p2: details.attack_ray.p2,
                startTime: Date.now(), duration: 500,
                color: 'rgba(255, 100, 255, 1.0)', lineWidth: 6,
            });
            uiState.visualEffects.push({
                type: 'growing_wall',
                barricade: details.barricade,
                color: gameState.teams[details.barricade.teamId].color,
                startTime: Date.now() + 200,
                duration: 800,
            });
        },
        'territory_fizzle_reinforce': (details, gameState) => {
            details.strengthened_lines.forEach(line => {
                uiState.lastActionHighlights.lines.add(line.id);
                uiState.visualEffects.push({ type: 'line_flash', line: line, startTime: Date.now(), duration: 800 });
            });
            details.territory_point_ids.forEach(pid => uiState.lastActionHighlights.points.add(pid));
        },
        'sentry_zap_miss_spawn': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.lastActionHighlights.points.add(details.new_point.id);
            uiState.visualEffects.push({
                type: 'attack_ray',
                p1: details.attack_ray.p1,
                p2: details.attack_ray.p2,
                startTime: Date.now(),
                duration: 700,
                color: `rgba(255, 100, 100, 1)`,
                lineWidth: 2
            });
        }
    };
    
    function processActionVisuals(gameState) {
        const details = gameState.last_action_details;
        if (!details || !details.type) return;

        if (details.action_events) {
            details.action_events.forEach(event => {
                if (event.type === 'nexus_detonation') {
                    uiState.visualEffects.push({
                        type: 'nexus_detonation',
                        center: event.center,
                        radius_sq: event.radius_sq,
                        color: event.color,
                        startTime: Date.now(),
                        duration: 900
                    });
                }
            });
        }

        clearTimeout(uiState.lastActionHighlights.clearTimeout);
        uiState.lastActionHighlights.points.clear();
        uiState.lastActionHighlights.lines.clear();
        uiState.lastActionHighlights.structures.clear();

        const visualizer = actionVisualsMap[details.type];
        if (visualizer) {
            visualizer(details, gameState);
        }

        if (details.bonus_line) {
            uiState.lastActionHighlights.lines.add(details.bonus_line.id);
            uiState.visualEffects.push({
                type: 'new_line', line: details.bonus_line, startTime: Date.now(), duration: 800
            });
        }
        if (details.bonus_lines) {
            details.bonus_lines.forEach(line => {
                uiState.lastActionHighlights.lines.add(line.id);
                uiState.visualEffects.push({
                    type: 'new_line', line: line, startTime: Date.now(), duration: 800
                });
            });
        }

        uiState.lastActionHighlights.clearTimeout = setTimeout(() => {
            uiState.lastActionHighlights.points.clear();
            uiState.lastActionHighlights.lines.clear();
            uiState.lastActionHighlights.structures.clear();
        }, 2000);
    }

    function processTurnEvents(events, gameState) {
        if (!events || events.length === 0) return;

        events.forEach(event => {
            const teamColor = gameState.teams[event.new_point?.teamId]?.color ||
                              gameState.teams[event.trap?.teamId]?.color ||
                              gameState.teams[event.nexus?.teamId]?.color ||
                              'rgba(200, 200, 200, 0.9)';

            switch (event.type) {
                case 'point_collapse':
                    uiState.visualEffects.push({ type: 'point_implosion', x: event.point.x, y: event.point.y, startTime: Date.now(), duration: 800, color: 'rgba(100, 100, 100, 0.9)' });
                    break;
                case 'heartwood_growth':
                    uiState.visualEffects.push({ type: 'heartwood_growth_ray', heartwood: gameState.heartwoods[event.new_point.teamId], new_point: event.new_point, startTime: Date.now(), duration: 1500 });
                    break;
                case 'monolith_wave':
                    uiState.visualEffects.push({ type: 'monolith_wave', center: event.center_coords, radius_sq: event.radius_sq, startTime: Date.now(), duration: 1200 });
                    break;
                case 'rift_trap_trigger':
                    uiState.visualEffects.push({ type: 'point_explosion', x: event.destroyed_point.x, y: event.destroyed_point.y, startTime: Date.now(), duration: 800 });
                    uiState.visualEffects.push({ type: 'point_implosion', x: event.trap.coords.x, y: event.trap.coords.y, startTime: Date.now(), duration: 800, color: teamColor });
                    break;
                case 'rift_trap_expire':
                    uiState.lastActionHighlights.points.add(event.new_point.id);
                    uiState.visualEffects.push({ type: 'point_implosion', x: event.trap.coords.x, y: event.trap.coords.y, startTime: Date.now(), duration: 1000, color: 'rgba(220, 220, 255, 0.9)' });
                    break;
                case 'attuned_nexus_fade':
                    uiState.visualEffects.push({ type: 'point_implosion', x: event.nexus.center.x, y: event.nexus.center.y, startTime: Date.now(), duration: 800, color: teamColor });
                    break;
                case 'ley_line_fade':
                    const points = event.ley_line.point_ids.map(pid => gameState.points[pid]).filter(p => p);
                    if (points.length >= 2) {
                        uiState.visualEffects.push({ type: 'line_flash', line: { p1_id: points[0].id, p2_id: points[points.length - 1].id }, startTime: Date.now(), duration: 1000 });
                    }
                    break;
            }
        });
    }

    function updateStateAndRender(gameState) {
        if (!gameState || !gameState.teams) return;
        
        const isFirstUpdate = !currentGameState.game_phase;
        currentGameState = gameState;

        processTurnEvents(gameState.new_turn_events, gameState);
        
        if (isFirstUpdate) {
            renderTeamsList();
        }

        processActionVisuals(gameState);
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
        let statsHTML = '<h4>Live Stats</h4>';
        if (teams && Object.keys(teams).length > 0 && live_stats) {
            for (const teamId in teams) {
                const team = teams[teamId];
                const stats = live_stats[teamId];
                if (!stats) continue;

                let teamHTML = `<div style="margin-bottom: 5px;">
                    <strong style="color:${team.color};">${team.name}</strong>: 
                    ${stats.point_count} pts, ${stats.line_count} lines, ${stats.controlled_area} area`;
                
                const allStructures = ['I-Rune', 'Cross', 'V-Rune', 'Prism', 'Nexus', 'Bastion', 'Monolith', 'Trebuchet', 'Purifier', 'Rift Spire', 'Wonder'];
                const structureStrings = allStructures.map(name => {
                    const stateKey = name.toLowerCase().replace('-', '_');
                    let count = 0;
                    if (gameState.runes?.[teamId]?.[stateKey]) count = gameState.runes[teamId][stateKey].length;
                    else if (gameState[stateKey + 's']?.[teamId]) count = gameState[stateKey + 's'][teamId].length;
                    else if (gameState[stateKey + 's']) count = Object.values(gameState[stateKey + 's']).filter(s => s.teamId === teamId).length;
                    return count > 0 ? `${name}(${count})` : '';
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
        if (canvas.clientWidth === 0 || canvas.clientHeight === 0) return;
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;
        const gridSize = currentGameState.grid_size || 10;
        cellSize = canvas.width / gridSize;
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
                card.innerHTML = `
                    <canvas width="150" height="150"></canvas>
                    <div class="action-card-text">
                         <div class="action-card-header">
                            <h4>${action.display_name}</h4>
                            <span class="action-group action-group--${action.group.toLowerCase()}">${action.group}</span>
                        </div>
                        <div class="action-card-description">${action.description}</div>
                    </div>`;
                grid.appendChild(card);

                const canvas = card.querySelector('canvas');
                const drawer = illustrationDrawers[action.name] || illustrationDrawers['default'];
                drawer(canvas.getContext('2d'), canvas.width, canvas.height);
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

    async function initActionGuide() {
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
        initActionGuide();
        animationLoop();
    }

    init();
});