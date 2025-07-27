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
        initActionGuide();
        
        // Start the main animation loop
        animationLoop();
    }

    init();
});