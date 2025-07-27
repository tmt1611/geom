/**
 * visuals.js
 * 
 * Manages the creation of visual effect data based on game state events.
 * This module translates game logic events (like 'add_line', 'nova_burst') 
 * into a structured format that the renderer can use to draw temporary animations.
 */
const visualEffectsManager = (() => {

    function processStateChange(previousState, currentState, uiState, cellSize) {
        if (!previousState || !currentState) return;

        // 1. Process Turn Start Events
        // These are only present in the state right after a turn starts.
        // We compare turn numbers to ensure we only process them once.
        if (currentState.turn > previousState.turn && currentState.new_turn_events) {
            processTurnEvents(currentState.new_turn_events, currentState, uiState);
        }

        // 2. Process the main action visual for this state change
        // The `last_action_details` in the current state tells us what just happened.
        processActionVisuals(currentState, uiState, cellSize);
    }

    // This is a factory function because some visuals need access to the UI state
    // and renderer-specific values like cellSize.
    const getActionVisualsMap = (cellSize, uiState) => ({
        'isolate_fizzle_push': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.projector_point.id);
            uiState.visualEffects.push({
                type: 'shield_pulse',
                center: details.pulse_center,
                radius_sq: details.pulse_radius_sq,
                color: gameState.teams[details.projector_point.teamId].color,
                startTime: Date.now(),
                duration: 600
            });
        },
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
        'bisect_angle': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.new_point.id);
            uiState.lastActionHighlights.lines.add(details.new_line.id);
            const vertex = gameState.points[details.new_line.p1_id] || gameState.points[details.new_line.p2_id];
            if(vertex) {
                 uiState.visualEffects.push({
                    type: 'animated_ray',
                    p1: vertex,
                    p2: details.new_point,
                    startTime: Date.now(),
                    duration: 600,
                    color: gameState.teams[details.new_point.teamId].color,
                    lineWidth: 2
                });
            }
        },
        'bisect_fizzle_strengthen': (details, gameState) => {
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
        'spawn_point': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.new_point.id);
            uiState.visualEffects.push({
                type: 'point_formation',
                x: details.new_point.x,
                y: details.new_point.y,
                color: gameState.teams[details.new_point.teamId].color,
                startTime: Date.now(),
                duration: 600
            });
        },
        'spawn_fizzle_strengthen': (details, gameState) => {
            uiState.lastActionHighlights.lines.add(details.strengthened_line.id);
            uiState.visualEffects.push({ type: 'line_flash', line: details.strengthened_line, startTime: Date.now(), duration: 800 });
        },
        'spawn_fizzle_border_spawn': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.new_point.id);
            if (details.origin_point) {
                 uiState.visualEffects.push({
                    type: 'animated_ray',
                    p1: details.origin_point,
                    p2: details.new_point,
                    startTime: Date.now(),
                    duration: 700,
                    color: gameState.teams[details.new_point.teamId].color,
                    lineWidth: 2
                });
            } else {
                 uiState.visualEffects.push({
                    type: 'point_formation',
                    x: details.new_point.x,
                    y: details.new_point.y,
                    color: gameState.teams[details.new_point.teamId].color,
                    startTime: Date.now(),
                    duration: 800
                });
            }
        },
         'mirror_point': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.new_point.id);
            uiState.lastActionHighlights.points.add(details.source_point_id);
            uiState.lastActionHighlights.points.add(details.pivot_point_id);

            const source = gameState.points[details.source_point_id];
            const pivot = gameState.points[details.pivot_point_id];
            const teamColor = gameState.teams[details.new_point.teamId].color;

            if (source && pivot) {
                uiState.visualEffects.push({
                    type: 'animated_ray',
                    p1: source, p2: pivot, startTime: Date.now(), duration: 500, color: teamColor, lineWidth: 1.5
                });
                 uiState.visualEffects.push({
                    type: 'animated_ray',
                    p1: pivot, p2: details.new_point, startTime: Date.now() + 200, duration: 500, color: teamColor, lineWidth: 3
                });
            }
        },
        'mirror_point_fizzle_strengthen': (details, gameState) => {
             uiState.lastActionHighlights.lines.add(details.strengthened_line.id);
             uiState.visualEffects.push({ type: 'line_flash', line: details.strengthened_line, startTime: Date.now(), duration: 800 });
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
            uiState.visualEffects.push({
                type: 'point_explosion',
                x: details.attack_ray.p2.x,
                y: details.attack_ray.p2.y,
                startTime: Date.now() + 200,
                duration: 500
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
        'rune_v_beam': (details, gameState) => {
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
                type: 'line_flash',
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
            // Add an implosion/formation effect on the point becoming an anchor
            uiState.visualEffects.push({
                type: 'point_implosion',
                x: details.anchor_point.x,
                y: details.anchor_point.y,
                color: gameState.teams[details.anchor_point.teamId].color,
                startTime: Date.now(),
                duration: 800
            });
        },
        'create_whirlpool': (details, gameState) => {
            uiState.visualEffects.push({
                type: 'point_implosion',
                x: details.sacrificed_point.x,
                y: details.sacrificed_point.y,
                startTime: Date.now(),
                duration: 1200,
                color: gameState.teams[details.sacrificed_point.teamId]?.color || `rgba(150, 220, 255, 1)`
            });
        },
        'mirror_structure': (details, gameState) => {
            if (details.axis_p1_id) uiState.lastActionHighlights.points.add(details.axis_p1_id);
            if (details.axis_p2_id) uiState.lastActionHighlights.points.add(details.axis_p2_id);

            if (details.axis_p1_id && details.axis_p2_id) {
                uiState.visualEffects.push({
                    type: 'mirror_axis',
                    p1_id: details.axis_p1_id,
                    p2_id: details.axis_p2_id,
                    startTime: Date.now(),
                    duration: 1500
                });
            }
            
            // Add effects for new points and lines
            if (Array.isArray(details.new_points)) {
                details.new_points.forEach((p, i) => {
                    uiState.lastActionHighlights.points.add(p.id);
                    const team = gameState.teams[p.teamId];
                    if (!team) {
                        console.warn(`Visuals: could not find team with ID ${p.teamId} for mirror_structure point formation.`);
                        return; // Skip this effect if team is missing
                    }
                    uiState.visualEffects.push({
                        type: 'point_formation',
                        x: p.x,
                        y: p.y,
                        color: team.color,
                        startTime: Date.now() + i * 100,
                        duration: 600
                    });
                });
            }
            
            if (Array.isArray(details.new_lines)) {
                details.new_lines.forEach(line => {
                    uiState.lastActionHighlights.lines.add(line.id);
                    uiState.visualEffects.push({ type: 'new_line', line, startTime: Date.now() + 400, duration: 800 });
                });
            }
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
        'orbital_fizzle_strengthen': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.center_point_id);
            details.strengthened_lines.forEach(line => {
                uiState.lastActionHighlights.lines.add(line.id);
                uiState.visualEffects.push({ type: 'line_flash', line: line, startTime: Date.now(), duration: 800 });
            });
        },
        'form_bastion': (details, gameState) => {
            uiState.visualEffects.push({
                type: 'line_flash',
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
        'create_ley_line': (details, gameState) => {
            if (!details.ley_line || !details.ley_line.point_ids) return;
            const ley_line_points = details.ley_line.point_ids;

            ley_line_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            if (details.ley_line_line_ids && ley_line_points.length > 0) {
                const first_point = gameState.points[ley_line_points[0]];
                if (!first_point) return;
                const team = gameState.teams[first_point.teamId];
                if (!team) return;

                uiState.visualEffects.push({
                    type: 'line_flash',
                    line_ids: details.ley_line_line_ids,
                    color: team.color,
                    startTime: Date.now(),
                    duration: 1200
                });
            }
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
            uiState.visualEffects.push({
                type: 'point_explosion',
                x: details.refracted_ray.p2.x,
                y: details.refracted_ray.p2.y,
                startTime: Date.now() + 400,
                duration: 500
            });
        },
        'bastion_pulse': (details, gameState) => {
            const bastion = gameState.bastions[details.bastion_id];
            if(bastion) {
                uiState.lastActionHighlights.points.add(bastion.core_id);
                bastion.prong_ids.forEach(pid => uiState.lastActionHighlights.points.add(pid));
                
                const prong_points = bastion.prong_ids.map(pid => gameState.points[pid]).filter(Boolean);
                if (prong_points.length >= 3) {
                     uiState.visualEffects.push({
                        type: 'polygon_flash',
                        points: prong_points,
                        color: gameState.teams[bastion.teamId].color,
                        startTime: Date.now(),
                        duration: 800
                    });
                }
            }
            // Show sacrificed point imploding
            uiState.visualEffects.push({
                type: 'point_implosion', x: details.sacrificed_point.x, y: details.sacrificed_point.y, startTime: Date.now(), duration: 800, color: gameState.teams[details.sacrificed_point.teamId]?.color
            });

            // Show destroyed lines exploding
            details.destroyed_lines.forEach((line, i) => {
                 const p1 = gameState.points[line.p1_id];
                 const p2 = gameState.points[line.p2_id];
                 if(p1 && p2) {
                     const midpoint = {x: (p1.x+p2.x)/2, y: (p1.y+p2.y)/2};
                     uiState.visualEffects.push({
                         type: 'point_explosion',
                         x: midpoint.x,
                         y: midpoint.y,
                         startTime: Date.now() + 200 + i * 50,
                         duration: 500
                     });
                 }
            });
        },
        'sentry_zap': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
             uiState.visualEffects.push({
                type: 'jagged_ray',
                p1: details.attack_ray.p1,
                p2: details.attack_ray.p2,
                startTime: Date.now(),
                duration: 400,
                color: 'rgba(255, 255, 100, 1)',
                lineWidth: 2
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
        'line_retaliation': (details, gameState) => {
            const p_sac = details.sacrificed_point;
            const target1 = details.target1;
            const target2 = details.target2;
            const teamColor = gameState.teams[p_sac.teamId].color;

            uiState.lastActionHighlights.points.add(details.sacrificed_point.id);
            if (details.other_endpoint_id) {
                uiState.lastActionHighlights.points.add(details.other_endpoint_id);
            }

            uiState.visualEffects.push({
                type: 'attack_ray',
                p1: p_sac,
                p2: target1,
                startTime: Date.now(),
                duration: 700,
                color: teamColor
            });
            uiState.visualEffects.push({
                type: 'attack_ray',
                p1: p_sac,
                p2: target2,
                startTime: Date.now(),
                duration: 700,
                color: teamColor
            });
        },
        'rune_time_stasis': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.lastActionHighlights.points.add(details.target_point.id);
            const vertex_point = gameState.points[details.vertex_id];
            if (vertex_point) {
                uiState.visualEffects.push({
                    type: 'energy_spiral',
                    start: vertex_point,
                    end: details.target_point,
                    color: 'rgba(150, 220, 255, 0.9)',
                    startTime: Date.now(),
                    duration: 1000
                });
            }
        },
        'rune_cardinal_pulse': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            const teamColor = gameState.teams[details.team_id].color;
            details.rays.forEach(ray => {
                uiState.visualEffects.push({
                    type: 'attack_ray',
                    p1: ray.p1,
                    p2: ray.p2,
                    startTime: Date.now(),
                    duration: 600,
                    color: teamColor
                });
            });
        },
        'rune_t_hammer_slam': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.visualEffects.push({
                type: 'line_flash',
                line_ids: [details.stem_line_id],
                color: gameState.teams[details.team_id].color,
                startTime: Date.now(),
                duration: 800
            });
        },
        'rune_parallel_discharge': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            const points = details.rune_points.map(pid => gameState.points[pid]).filter(Boolean);
            if(points.length === 4) {
                uiState.visualEffects.push({
                    type: 'polygon_flash',
                    points: points,
                    color: gameState.teams[details.team_id].color,
                    startTime: Date.now(),
                    duration: 1000
                });
            }
        },
        'rune_focus_beam': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.visualEffects.push({
                type: 'attack_ray',
                p1: details.center_point,
                p2: details.target_point,
                startTime: Date.now(),
                duration: 800,
                color: 'rgba(255, 255, 150, 1.0)',
                lineWidth: 5,
            });
            uiState.visualEffects.push({
                type: 'point_explosion',
                x: details.target_point.x,
                y: details.target_point.y,
                startTime: Date.now() + 400,
                duration: 800
            });
        },
        'rune_starlight_cascade': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            let particles = [];
            for(let i=0; i<30; i++) {
                particles.push({
                    angle: Math.random() * 2 * Math.PI, 
                    speed: (50 + Math.random() * 100) * (cellSize/10),
                    flicker_speed: 50 + Math.random() * 100
                });
            }
            uiState.visualEffects.push({
                type: 'starlight_cascade',
                center: details.center_point,
                radius: details.radius,
                particles: particles,
                startTime: Date.now(),
                duration: 1200
            });
        },
        'rune_gravity_well': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.visualEffects.push({
                type: 'shield_pulse',
                center: details.center_point,
                radius_sq: details.radius_sq,
                color: gameState.teams[details.team_id].color,
                startTime: Date.now(),
                duration: 1000
            });
        },
        'create_rift_trap': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.sacrificed_point.id);
            uiState.visualEffects.push({
                type: 'point_implosion',
                x: details.sacrificed_point.x,
                y: details.sacrificed_point.y,
                startTime: Date.now(),
                duration: 800,
                color: gameState.teams[details.sacrificed_point.teamId]?.color
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
        'parallel_strike': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.source_point.id);
            uiState.lastActionHighlights.lines.add(details.parallel_line.id);
            uiState.lastActionHighlights.points.add(details.destroyed_point.id);
            uiState.visualEffects.push({
                type: 'attack_ray',
                p1: details.source_point,
                p2: details.destroyed_point,
                startTime: Date.now(),
                duration: 700,
                color: gameState.teams[details.source_point.teamId].color
            });
            uiState.visualEffects.push({
                type: 'point_explosion',
                x: details.destroyed_point.x,
                y: details.destroyed_point.y,
                startTime: Date.now() + 300,
                duration: 600
            });
        },
        'territory_tri_beam': (details, gameState) => {
            details.territory_point_ids.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            const teamColor = gameState.teams[details.team_id].color;
            details.rays.forEach(ray => {
                uiState.visualEffects.push({
                    type: 'attack_ray',
                    p1: ray.p1,
                    p2: ray.p2,
                    startTime: Date.now(),
                    duration: 800,
                    color: teamColor
                });
            });
            details.hit_points.forEach(hit => {
                 uiState.visualEffects.push({
                    type: 'point_explosion',
                    x: hit.x,
                    y: hit.y,
                    startTime: Date.now() + 400,
                    duration: 500
                });
            });
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
            // Add shockwave from purifier to match illustration
            const purifier_points = details.purifier_point_ids.map(pid => gameState.points[pid]).filter(Boolean);
            if (purifier_points.length > 0) {
                const center = {
                    x: purifier_points.reduce((sum, p) => sum + p.x, 0) / purifier_points.length,
                    y: purifier_points.reduce((sum, p) => sum + p.y, 0) / purifier_points.length
                };
                const radius_sq = (gameState.grid_size * 0.3)**2;
                uiState.visualEffects.push({
                    type: 'shield_pulse',
                    center: center,
                    radius_sq: radius_sq,
                    color: 'rgba(255, 255, 220, 1.0)', // Purifier yellow
                    startTime: Date.now(),
                    duration: 1000,
                });
            }
        },
        'sacrifice_build_wonder': (details, gameState) => {
            if(details.sacrificed_point_ids) {
                const sacrificed_points = details.sacrificed_point_ids.map(pid => gameState.points[pid]).filter(Boolean);
                sacrificed_points.forEach(p => uiState.lastActionHighlights.points.add(p.id));
                uiState.visualEffects.push({
                    type: 'heartwood_creation', // Re-using this effect type for a dramatic build-up
                    sacrificed_points: sacrificed_points,
                    center_coords: details.wonder.coords,
                    color: gameState.teams[details.wonder.teamId].color,
                    startTime: Date.now(),
                    duration: 2000
                });
            }
            // Add a secondary flash for more impact
            uiState.visualEffects.push({
                type: 'starlight_cascade', // Re-using this for a bright flash
                center: details.wonder.coords,
                radius: gameState.grid_size * 0.1,
                particles: [], // No particles, just the flash
                startTime: Date.now() + 1500, // After the build-up
                duration: 1000
            });
        },
        'create_fissure': (details, gameState) => {
            uiState.lastActionHighlights.structures.add(details.spire_id);
            uiState.lastActionHighlights.structures.add(details.fissure.id);
            const spire = gameState.rift_spires[details.spire_id];
            if (spire) {
                uiState.visualEffects.push({
                    type: 'jagged_ray',
                    p1: spire.coords,
                    p2: details.fissure.p1,
                    startTime: Date.now(),
                    duration: 600,
                    color: gameState.teams[spire.teamId].color
                });
            }
            uiState.visualEffects.push({
                type: 'growing_wall',
                barricade: details.fissure, // growing_wall uses barricade object structure
                color: 'rgba(50, 50, 50, 0.8)',
                startTime: Date.now() + 200,
                duration: 1200
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
        'hull_breach_convert': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.converted_point.id);
            details.hull_points.forEach(p => uiState.lastActionHighlights.points.add(p.id));
            uiState.visualEffects.push({
                type: 'polygon_flash',
                points: details.hull_points,
                color: gameState.teams[details.converted_point.teamId].color,
                startTime: Date.now(),
                duration: 1000
            });
            uiState.visualEffects.push({
                type: 'energy_spiral',
                start: {x: details.hull_points.reduce((a,b)=>a+b.x,0)/details.hull_points.length, y: details.hull_points.reduce((a,b)=>a+b.y,0)/details.hull_points.length},
                end: details.converted_point,
                color: gameState.teams[details.converted_point.teamId].color,
                startTime: Date.now() + 200,
                duration: 800
            });
        },
        'hull_breach_fizzle_reinforce': (details, gameState) => {
            details.hull_points.forEach(p => uiState.lastActionHighlights.points.add(p.id));
            uiState.visualEffects.push({
                type: 'polygon_flash',
                points: details.hull_points,
                color: gameState.teams[details.hull_points[0].teamId].color,
                startTime: Date.now(),
                duration: 1000
            });
            (details.strengthened_lines || []).forEach(line => {
                uiState.lastActionHighlights.lines.add(line.id);
                uiState.visualEffects.push({ type: 'line_flash', line: line, startTime: Date.now() + 200, duration: 800 });
            });
            (details.created_lines || []).forEach(line => {
                uiState.lastActionHighlights.lines.add(line.id);
                uiState.visualEffects.push({ type: 'new_line', line: line, startTime: Date.now() + 200, duration: 800 });
            });
        },
        'hull_breach_fizzle_push': (details, gameState) => {
            details.hull_points.forEach(p => uiState.lastActionHighlights.points.add(p.id));
            const center = {x: details.hull_points.reduce((a,b)=>a+b.x,0)/details.hull_points.length, y: details.hull_points.reduce((a,b)=>a+b.y,0)/details.hull_points.length};
            uiState.visualEffects.push({
                type: 'polygon_flash',
                points: details.hull_points,
                color: gameState.teams[details.hull_points[0].teamId].color,
                startTime: Date.now(),
                duration: 1000
            });
            uiState.visualEffects.push({
                type: 'shield_pulse',
                center: center,
                radius_sq: (gameState.grid_size * 0.2)**2,
                color: gameState.teams[details.hull_points[0].teamId].color,
                startTime: Date.now() + 200,
                duration: 800,
            });
        },
        'reposition_point': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.moved_point.id);
            if (details.original_coords) {
                uiState.visualEffects.push({
                    type: 'reposition_trail',
                    p1: details.original_coords,
                    p2: details.moved_point,
                    color: gameState.teams[details.moved_point.teamId].color,
                    startTime: Date.now(),
                    duration: 600
                });
            }
        },
        'rotate_point': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.moved_point.id);
            if (details.pivot_point && !details.is_grid_center) {
                uiState.lastActionHighlights.points.add(details.pivot_point.id);
            }
            if (details.original_coords) {
                uiState.visualEffects.push({
                    type: 'rotation_arc',
                    start: details.original_coords,
                    end: details.moved_point,
                    pivot: details.pivot_point,
                    is_grid_center: details.is_grid_center,
                    grid_size: gameState.grid_size,
                    color: gameState.teams[details.moved_point.teamId].color,
                    startTime: Date.now(),
                    duration: 800
                });
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
        'parallel_strike_miss_spawn': (details, gameState) => {
            uiState.lastActionHighlights.points.add(details.source_point.id);
            uiState.lastActionHighlights.lines.add(details.parallel_line.id);
            uiState.lastActionHighlights.points.add(details.new_point.id);
            uiState.visualEffects.push({
                type: 'attack_ray',
                p1: details.source_point,
                p2: details.new_point,
                startTime: Date.now(),
                duration: 700,
                color: gameState.teams[details.source_point.teamId].color
            });
        },
        'sentry_zap_miss_spawn': (details, gameState) => {
            details.rune_points.forEach(pid => uiState.lastActionHighlights.points.add(pid));
            uiState.lastActionHighlights.points.add(details.new_point.id);
            if (details.attack_ray.p1 && details.new_point) {
                uiState.visualEffects.push({
                    type: 'attack_ray',
                    p1: details.attack_ray.p1,
                    p2: details.new_point, // Use new_point which is guaranteed to exist
                    startTime: Date.now(),
                    duration: 700,
                    color: `rgba(255, 100, 100, 1)`,
                    lineWidth: 2
                });
            }
        },
        'scorch_territory': (details, gameState) => {
            const points = details.territory.points.map(p => gameState.points[p.id]).filter(Boolean);
            if (points.length === 3) {
                 points.forEach(p => uiState.lastActionHighlights.points.add(p.id));
                 uiState.visualEffects.push({
                    type: 'polygon_flash',
                    points: points,
                    color: 'rgba(255, 80, 0, 0.8)', // Fiery orange
                    startTime: Date.now(),
                    duration: 1000,
                });
            }
        },
    });

    function processActionVisuals(gameState, uiState, cellSize) {
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

        const actionVisualsMap = getActionVisualsMap(cellSize, uiState);
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

    function processTurnEvents(events, gameState, uiState) {
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
                    const heartwood = gameState.heartwoods[event.new_point.teamId];
                    if (heartwood) {
                        uiState.visualEffects.push({
                            type: 'animated_ray',
                            p1: heartwood.center_coords,
                            p2: event.new_point,
                            color: gameState.teams[event.new_point.teamId].color,
                            startTime: Date.now(),
                            duration: 1500,
                        });
                    }
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

    return {
        processStateChange,
    };
})();