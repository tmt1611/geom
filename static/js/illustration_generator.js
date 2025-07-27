const illustrationHelpers = {
    drawJaggedLine: (ctx, p1, p2, segments, jag_amount) => {
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        const len = Math.sqrt(dx*dx + dy*dy);
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
    drawSacrificeSymbol: (ctx, x, y, size = 8) => {
        ctx.save();
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x - size, y - size); ctx.lineTo(x + size, y + size);
        ctx.moveTo(x + size, y - size); ctx.lineTo(x - size, y + size);
        ctx.stroke();
        ctx.restore();
    },
    drawFortifiedPoint: (ctx, p, color) => {
        ctx.fillStyle = color;
        const radius = 5;
        const size = radius * 1.7;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y - size); ctx.lineTo(p.x + size, p.y); ctx.lineTo(p.x, p.y + size); ctx.lineTo(p.x - size, p.y);
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
    'fortify_shield_line': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p1 = {x: w*0.3, y: h*0.5};
        const p2 = {x: w*0.7, y: h*0.5};
        
        // Draw line first
        illustrationHelpers.drawLines(ctx, [{p1, p2}], team1_color);
        
        // Draw shield on top
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.strokeStyle = 'rgba(173, 216, 230, 0.9)';
        ctx.lineWidth = 12;
        ctx.stroke();
        ctx.restore();

        // Redraw points on top of shield
        illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
    },
    'expand_add_line': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p1 = {x: w*0.3, y: h*0.5};
        const p2 = {x: w*0.7, y: h*0.5};
        illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
        illustrationHelpers.drawDashedLine(ctx, p1, p2, team1_color);
    },
    'expand_mirror_point': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p_source = {x: w*0.3, y: h*0.3};
        const p_pivot = {x: w*0.5, y: h*0.5};
        const p_new = {x: w*0.7, y: h*0.7};

        // Draw source and pivot points
        illustrationHelpers.drawPoints(ctx, [p_source, p_pivot], team1_color);
        
        // Draw dashed line showing reflection
        illustrationHelpers.drawDashedLine(ctx, p_source, p_new, '#aaa');
        
        // Draw the new mirrored point
        illustrationHelpers.drawPoints(ctx, [p_new], team1_color);
    },
    'expand_bisect_angle': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p_v = {x: w*0.2, y: h*0.5};
        const p_l1 = {x: w*0.5, y: h*0.2};
        const p_l2 = {x: w*0.5, y: h*0.8};
        
        // V-shape
        illustrationHelpers.drawPoints(ctx, [p_v, p_l1, p_l2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1: p_v, p2: p_l1}, {p1: p_v, p2: p_l2}], team1_color);
        
        // Bisector line and new point
        const p_new = {x: w*0.8, y: h*0.5};
        illustrationHelpers.drawDashedLine(ctx, p_v, p_new, team1_color);
        illustrationHelpers.drawPoints(ctx, [p_new], team1_color);
    },
    'expand_extend_line': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p1 = {x: w*0.2, y: h*0.5};
        const p2 = {x: w*0.5, y: h*0.5};
        const p3 = {x: w*0.9, y: h*0.5};
        illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1, p2}], team1_color);
        illustrationHelpers.drawDashedLine(ctx, p2, p3, team1_color);
        illustrationHelpers.drawPoints(ctx, [p3], team1_color);
    },
    'expand_fracture_line': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p1 = {x: w*0.2, y: h*0.5};
        const p2 = {x: w*0.8, y: h*0.5};
        const p_new = {x: w*0.5, y: h*0.5};
        illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1, p2}], team1_color);
        
        ctx.save();
        ctx.beginPath();
        ctx.arc(p_new.x, p_new.y, 15, 0, 2*Math.PI);
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 6;
        ctx.stroke();
        ctx.fillStyle = team1_color;
        ctx.fill();
        ctx.restore();
    },
    'expand_create_orbital': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const center = {x: w*0.5, y: h*0.5};
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
    'expand_spawn_point': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p1 = {x: w*0.4, y: h*0.5};
        const p2 = {x: w*0.6, y: h*0.5};
        illustrationHelpers.drawPoints(ctx, [p1], team1_color);
        illustrationHelpers.drawDashedLine(ctx, p1, p2, team1_color);
        illustrationHelpers.drawPoints(ctx, [p2], team1_color);
    },
    'attack_line_energized': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const p1 = {x: w*0.1, y: h*0.5};
        const p2 = {x: w*0.3, y: h*0.5};

        illustrationHelpers.drawPoints(ctx, [p1,p2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1, p2}], team1_color);
        
        // Enemy points
        const ep1 = {x: w*0.6, y: h*0.5};
        const ep2 = {x: w*0.8, y: h*0.5};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
        
        // Energized ray
        ctx.beginPath();
        ctx.moveTo(p2.x, p2.y);
        ctx.lineTo(w*0.9, h*0.5);
        ctx.strokeStyle = 'rgba(255, 255, 100, 1.0)';
        ctx.lineWidth = 5;
        ctx.stroke();

        // Explosions on enemy points
        illustrationHelpers.drawExplosion(ctx, ep1.x, ep1.y, 'red', 12);
        illustrationHelpers.drawExplosion(ctx, ep2.x, ep2.y, 'red', 12);
    },
    'fight_attack_line': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const p1 = {x: w*0.1, y: h*0.3};
        const p2 = {x: w*0.4, y: h*0.3};
        const ep1 = {x: w*0.7, y: h*0.1};
        const ep2 = {x: w*0.7, y: h*0.9};
        const hit = {x: w*0.7, y: h*0.3};

        illustrationHelpers.drawPoints(ctx, [p1,p2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1, p2}], team1_color);
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1: ep1, p2: ep2}], team2_color);
        illustrationHelpers.drawArrow(ctx, p2, hit, team1_color);
        
        illustrationHelpers.drawExplosion(ctx, hit.x, hit.y);
    },
    'fight_parallel_strike': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';

        // Friendly point and line
        const p_source = {x: w*0.2, y: h*0.3};
        const l1 = {x: w*0.3, y: h*0.8};
        const l2 = {x: w*0.7, y: h*0.8};
        illustrationHelpers.drawPoints(ctx, [p_source, l1, l2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:l1, p2:l2}], team1_color);

        // Enemy point
        const ep1 = {x: w*0.6, y: h*0.3};
        illustrationHelpers.drawPoints(ctx, [ep1], team2_color);
        
        // Parallel strike
        illustrationHelpers.drawArrow(ctx, p_source, ep1, team1_color);

        // Explosion
        illustrationHelpers.drawExplosion(ctx, ep1.x, ep1.y);
    },
    'fight_territory_tri_beam': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const p1 = {x: w*0.5, y: h*0.1};
        const p2 = {x: w*0.1, y: h*0.8};
        const p3 = {x: w*0.9, y: h*0.8};

        // Draw territory
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.lineTo(p3.x, p3.y); ctx.closePath();
        ctx.fillStyle = team1_color;
        ctx.globalAlpha = 0.3;
        ctx.fill();
        ctx.globalAlpha = 1.0;
        illustrationHelpers.drawPoints(ctx, [p1, p2, p3], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1,p2},{p1:p2,p2:p3},{p1:p3,p2:p1}], team1_color);

        // Enemy lines
        const el1_p1 = {x: w*0.9, y: h*0.3};
        const el1_p2 = {x: w*0.9, y: h*0.6};
        const el2_p1 = {x: w*0.1, y: h*0.3};
        const el2_p2 = {x: w*0.1, y: h*0.6};
        const el3_p1 = {x: w*0.4, y: h*0.95};
        const el3_p2 = {x: w*0.6, y: h*0.95};
        illustrationHelpers.drawPoints(ctx, [el1_p1, el1_p2, el2_p1, el2_p2, el3_p1, el3_p2], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1:el1_p1,p2:el1_p2},{p1:el2_p1,p2:el2_p2},{p1:el3_p1,p2:el3_p2}], team2_color);
        
        // Beams from bisectors (approximated)
        const b1_target = {x: (el1_p1.x + el1_p2.x)/2, y: (el1_p1.y + el1_p2.y)/2};
        const b2_target = {x: (el2_p1.x + el2_p2.x)/2, y: (el2_p1.y + el2_p2.y)/2};
        const b3_target = {x: (el3_p1.x + el3_p2.x)/2, y: (el3_p1.y + el3_p2.y)/2};
        illustrationHelpers.drawArrow(ctx, p1, b1_target, team1_color);
        illustrationHelpers.drawArrow(ctx, p2, b2_target, team1_color);
        illustrationHelpers.drawArrow(ctx, p3, b3_target, team1_color);

        // Explosions
        illustrationHelpers.drawExplosion(ctx, b1_target.x, b1_target.y);
        illustrationHelpers.drawExplosion(ctx, b2_target.x, b2_target.y);
        illustrationHelpers.drawExplosion(ctx, b3_target.x, b3_target.y);
    },
    'sacrifice_chain_lightning': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        
        // I-Rune
        const p1 = {x: w*0.2, y: h*0.5};
        const p_sac = {x: w*0.4, y: h*0.5};
        const p3 = {x: w*0.6, y: h*0.5};
        illustrationHelpers.drawPoints(ctx, [p1, p_sac, p3], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:p1,p2:p_sac}, {p1:p_sac,p2:p3}], team1_color);

        // Sacrifice center point
        illustrationHelpers.drawSacrificeSymbol(ctx, p_sac.x, p_sac.y);

        // Enemy point
        const ep1 = {x: w*0.8, y: h*0.3};
        illustrationHelpers.drawPoints(ctx, [ep1], team2_color);
        
        // Lightning - jump from nearest endpoint
        const lightning_origin = p3;
        ctx.save();
        ctx.strokeStyle = 'rgba(200, 230, 255, 0.9)';
        ctx.lineWidth = 2;
        illustrationHelpers.drawJaggedLine(ctx, lightning_origin, ep1, 7, 12);
        ctx.restore();

        // Blast on enemy
        illustrationHelpers.drawExplosion(ctx, ep1.x, ep1.y);
    },
    'sacrifice_convert_point': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';

        const p1 = {x: w*0.2, y: h*0.5};
        const p2 = {x: w*0.4, y: h*0.5};
        const ep1 = {x: w*0.7, y: h*0.5};

        // Sacrificed line with 'X'
        illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1,p2}], team1_color, 1);
        const mid = {x: (p1.x+p2.x)/2, y: (p1.y+p2.y)/2};
        illustrationHelpers.drawSacrificeSymbol(ctx, mid.x, mid.y);

        // Enemy point
        illustrationHelpers.drawPoints(ctx, [ep1], team2_color);
        
        // Conversion effect matching 'energy_spiral'
        const start_pos = {x: mid.x, y: mid.y};
        const end_pos = ep1;
        ctx.fillStyle = '#f1c40f'; // yellow for conversion
        for (let i = 0; i < 5; i++) {
            const t = (i+1)/6.0;
            const x = start_pos.x * (1 - t) + end_pos.x * t;
            const y = start_pos.y * (1 - t) + end_pos.y * t;
            
            const angle = t * 2.5 * 2 * Math.PI; // number of turns
            const radius = (1 - t) * 10; // spiral gets tighter
            ctx.beginPath();
            ctx.arc(x + Math.cos(angle) * radius, y + Math.sin(angle) * radius, 2, 0, 2*Math.PI);
            ctx.fill();
        }
        
        // Converted point (draw a halo of new color)
        ctx.beginPath();
        ctx.arc(ep1.x, ep1.y, 12, 0, 2 * Math.PI);
        ctx.fillStyle = team1_color;
        ctx.globalAlpha = 0.5;
        ctx.fill();
        ctx.globalAlpha = 1.0;
    },
    'sacrifice_bastion_pulse': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        
        // Bastion
        const core = {x: w*0.3, y: h*0.5};
        const p_sac = {x: w*0.5, y: h*0.2};
        const prongs = [
            p_sac,
            {x: w*0.5, y: h*0.8},
            {x: w*0.1, y: h*0.5},
        ];
        // Draw bastion outline
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(prongs[0].x, prongs[0].y);
        ctx.lineTo(prongs[1].x, prongs[1].y);
        ctx.lineTo(prongs[2].x, prongs[2].y);
        ctx.closePath();
        
        // Add polygon flash to match effect
        ctx.fillStyle = team1_color;
        ctx.globalAlpha = 0.5;
        ctx.fill();

        ctx.strokeStyle = team1_color;
        ctx.lineWidth = 4;
        ctx.globalAlpha = 0.4;
        ctx.stroke();
        ctx.restore();

        // Draw bastion points
        illustrationHelpers.drawPoints(ctx, [core, ...prongs], team1_color);
        prongs.forEach(p => illustrationHelpers.drawLines(ctx, [{p1: core, p2: p}], team1_color));

        // Sacrificed point
        illustrationHelpers.drawSacrificeSymbol(ctx, p_sac.x, p_sac.y);

        // Enemy line crossing perimeter
        const ep1 = {x: w*0.8, y: h*0.1};
        const ep2 = {x: w*0.2, y: h*0.9};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1: ep1, p2: ep2}], team2_color, 1);

        // Pulse/blast
        illustrationHelpers.drawExplosion(ctx, w*0.4, h*0.7);
    },
    'fight_pincer_attack': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const p1 = {x: w*0.3, y: h*0.3};
        const p2 = {x: w*0.3, y: h*0.7};
        const ep1 = {x: w*0.7, y: h*0.5};

        illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
        illustrationHelpers.drawPoints(ctx, [ep1], team2_color);

        illustrationHelpers.drawArrow(ctx, p1, ep1, team1_color);
        illustrationHelpers.drawArrow(ctx, p2, ep1, team1_color);
        
        illustrationHelpers.drawExplosion(ctx, ep1.x, ep1.y);
    },
    'fight_hull_breach': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';

        // Friendly points for hull
        const hull_points = [
            {x: w*0.1, y: h*0.3},
            {x: w*0.3, y: h*0.9},
            {x: w*0.8, y: h*0.8},
            {x: w*0.9, y: h*0.4}
        ];
        illustrationHelpers.drawPoints(ctx, hull_points, team1_color);

        // Draw hull fill
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(hull_points[0].x, hull_points[0].y);
        for(let i=1; i<hull_points.length; i++) {
            ctx.lineTo(hull_points[i].x, hull_points[i].y);
        }
        ctx.closePath();
        ctx.fillStyle = team1_color;
        ctx.globalAlpha = 0.25;
        ctx.fill();
        ctx.restore();

        // Draw hull outline (dashed)
        for(let i=0; i<hull_points.length; i++) {
            illustrationHelpers.drawDashedLine(ctx, hull_points[i], hull_points[(i+1)%hull_points.length], team1_color);
        }

        // Enemy point to be converted
        const ep_convert = {x: w*0.5, y: h*0.5};
        illustrationHelpers.drawPoints(ctx, [ep_convert], team2_color);

        // Conversion effect
        const center = {x: w*0.5, y: h*0.6}; // Approx center of hull
        // Use particles to match the 'energy_spiral' visual effect
        ctx.fillStyle = '#f1c40f'; // yellow for conversion
        for (let i = 0; i < 5; i++) {
            const t = (i+1)/6.0;
            const x = center.x * (1 - t) + ep_convert.x * t;
            const y = center.y * (1 - t) + ep_convert.y * t;
            
            const angle = t * 2.5 * 2 * Math.PI; // number of turns
            const radius = (1 - t) * 10; // spiral gets tighter
            ctx.beginPath();
            ctx.arc(x + Math.cos(angle) * radius, y + Math.sin(angle) * radius, 2, 0, 2*Math.PI);
            ctx.fill();
        }
        
        // Converted point halo
        ctx.beginPath();
        ctx.arc(ep_convert.x, ep_convert.y, 12, 0, 2 * Math.PI);
        ctx.fillStyle = team1_color;
        ctx.globalAlpha = 0.5;
        ctx.fill();
        ctx.globalAlpha = 1.0;
    },
    'fight_isolate_point': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';

        // Friendly point projecting
        const p_source = {x: w*0.2, y: h*0.2};
        illustrationHelpers.drawPoints(ctx, [p_source], team1_color);

        // Enemy structure
        const ep1 = {x: w*0.8, y: h*0.8};
        const ep2 = {x: w*0.5, y: h*0.8}; // The target articulation point
        const ep3 = {x: w*0.5, y: h*0.5};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2, ep3], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1:ep1, p2:ep2}, {p1:ep2, p2:ep3}], team2_color);
        
        // Isolation beam
        illustrationHelpers.drawDashedLine(ctx, p_source, ep2, 'rgba(200, 100, 255, 1.0)');

        // Isolation effect on point
        const cage_r = 10;
        ctx.strokeStyle = 'rgba(200, 100, 255, 0.9)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(ep2.x - cage_r, ep2.y - cage_r); ctx.lineTo(ep2.x + cage_r, ep2.y + cage_r);
        ctx.moveTo(ep2.x - cage_r, ep2.y + cage_r); ctx.lineTo(ep2.x + cage_r, ep2.y - 8);
        ctx.stroke();
    },
    'fight_sentry_zap': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const p1 = {x: w*0.2, y: h*0.5};
        const p2 = {x: w*0.4, y: h*0.5};
        const p3 = {x: w*0.6, y: h*0.5};
        const ep1 = {x: w*0.4, y: h*0.2};
        
        illustrationHelpers.drawPoints(ctx, [p1, p2, p3], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1,p2}, {p1:p2,p2:p3}], team1_color);
        illustrationHelpers.drawPoints(ctx, [ep1], team2_color);

        // Use jagged line to match "zap" / "lightning" visual effect
        ctx.save();
        ctx.strokeStyle = 'rgba(255, 255, 100, 1.0)'; // Yellowish for electricity
        ctx.lineWidth = 2;
        illustrationHelpers.drawJaggedLine(ctx, p2, ep1, 5, 8);
        ctx.restore();

        illustrationHelpers.drawExplosion(ctx, ep1.x, ep1.y);
    },
    'fight_refraction_beam': (ctx, w, h) => {
        const team1_color = 'hsl(240, 70%, 50%)'; // Blue
        const team2_color = 'hsl(0, 70%, 50%)';   // Red
        
        // Prism structure (two adjacent triangles)
        const pA = {x: w*0.3, y: h*0.5};
        const pB = {x: w*0.5, y: h*0.2};
        const pC = {x: w*0.5, y: h*0.8};
        const pD = {x: w*0.7, y: h*0.5};
        const prism_points = [pA, pB, pC, pD];
        
        // Draw territory fills
        ctx.save();
        ctx.fillStyle = team1_color;
        ctx.globalAlpha = 0.2;
        ctx.beginPath();
        ctx.moveTo(pA.x, pA.y); ctx.lineTo(pB.x, pB.y); ctx.lineTo(pC.x, pC.y); ctx.closePath();
        ctx.fill();
        ctx.beginPath();
        ctx.moveTo(pD.x, pD.y); ctx.lineTo(pB.x, pB.y); ctx.lineTo(pC.x, pC.y); ctx.closePath();
        ctx.fill();
        ctx.restore();
        
        illustrationHelpers.drawPoints(ctx, prism_points, team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:pA,p2:pB},{p1:pA,p2:pC},{p1:pB,p2:pC}], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:pD,p2:pB},{p1:pD,p2:pC}], team1_color);

        // Enemy line
        const ep1 = {x: w*0.9, y: h*0.2};
        const ep2 = {x: w*0.9, y: h*0.8};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1:ep1, p2:ep2}], team2_color);

        // Beam
        const source_point = {x: w*0.1, y: h*0.3};
        const hit_prism = {x: w*0.5, y: h*0.4};
        const hit_enemy = {x: w*0.9, y: h*0.5};

        // Source ray
        illustrationHelpers.drawArrow(ctx, source_point, hit_prism, 'rgba(255, 255, 150, 1.0)');
        // Reflected ray
        illustrationHelpers.drawArrow(ctx, hit_prism, hit_enemy, 'rgba(255, 100, 100, 1.0)');

        // Explosion
        illustrationHelpers.drawExplosion(ctx, hit_enemy.x, hit_enemy.y);
    },
    'fight_territory_strike': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const p1 = {x: w*0.5, y: h*0.2};
        const p2 = {x: w*0.2, y: h*0.8};
        const p3 = {x: w*0.8, y: h*0.8};
        const center = {x: (p1.x+p2.x+p3.x)/3, y: (p1.y+p2.y+p3.y)/3};
        const ep1 = {x: w*0.8, y: h*0.2};

        // Draw territory
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.lineTo(p3.x, p3.y); ctx.closePath();
        ctx.fillStyle = team1_color;
        ctx.globalAlpha = 0.3;
        ctx.fill();
        ctx.globalAlpha = 1.0;
        illustrationHelpers.drawPoints(ctx, [p1, p2, p3], team1_color);
        
        // Draw enemy
        illustrationHelpers.drawPoints(ctx, [ep1], team2_color);
        
        // Draw strike
        illustrationHelpers.drawArrow(ctx, center, ep1, 'rgba(100, 255, 100, 1.0)');

        illustrationHelpers.drawExplosion(ctx, ep1.x, ep1.y);
    },
    'fortify_create_anchor': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const p_anchor = {x: w*0.4, y: h*0.5};
        const ep1 = {x: w*0.8, y: h*0.3};
        const ep2 = {x: w*0.8, y: h*0.7};

        // Anchor point (no sacrifice)
        ctx.fillStyle = team1_color;
        ctx.fillRect(p_anchor.x - 8, p_anchor.y - 8, 16, 16);

        // Add pulse effect to match renderer
        ctx.beginPath();
        ctx.arc(p_anchor.x, p_anchor.y, 20, 0, 2 * Math.PI);
        ctx.strokeStyle = `rgba(200, 200, 255, 0.7)`;
        ctx.lineWidth = 3;
        ctx.setLineDash([4,4]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Enemy points
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
        
        // Pull arrows
        illustrationHelpers.drawArrow(ctx, ep1, p_anchor, '#aaa');
        illustrationHelpers.drawArrow(ctx, ep2, p_anchor, '#aaa');
    },
    'fortify_reposition_point': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p_orig = {x: w*0.3, y: h*0.5};
        const p_new = {x: w*0.7, y: h*0.5};

        // Original point (faded)
        ctx.save();
        ctx.globalAlpha = 0.4;
        illustrationHelpers.drawPoints(ctx, [p_orig], team1_color);
        ctx.restore();

        // Arrow
        illustrationHelpers.drawDashedLine(ctx, p_orig, p_new, '#aaa');
        
        // New point
        illustrationHelpers.drawPoints(ctx, [p_new], team1_color);
    },
    'fortify_create_ley_line': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        
        // I-Rune
        const p1 = {x: w*0.2, y: h*0.5};
        const p2 = {x: w*0.5, y: h*0.5};
        const p3 = {x: w*0.8, y: h*0.5};
        const points = [p1, p2, p3];
        illustrationHelpers.drawLines(ctx, [{p1:p1,p2:p2}, {p1:p2,p2:p3}], team1_color);
        
        // Ley line glow effect
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p3.x, p3.y);
        ctx.strokeStyle = team1_color;
        ctx.lineWidth = 10;
        ctx.globalAlpha = 0.5;
        ctx.filter = 'blur(4px)';
        ctx.stroke();
        ctx.restore();

        // Redraw points on top of glow
        illustrationHelpers.drawPoints(ctx, points, team1_color);
    },
    'fortify_claim_territory': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p1 = {x: w*0.5, y: h*0.2};
        const p2 = {x: w*0.2, y: h*0.8};
        const p3 = {x: w*0.8, y: h*0.8};

        illustrationHelpers.drawPoints(ctx, [p1, p2, p3], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1: p1, p2: p2}, {p1: p2, p2: p3}, {p1: p3, p2: p1}], team1_color);

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
        const core = {x: w*0.5, y: h*0.5};
        const prongs = [
            {x: w*0.7, y: h*0.3},
            {x: w*0.7, y: h*0.7},
            {x: w*0.3, y: h*0.5},
        ];
        
        // Draw core as a square, matching the renderer for 'is_bastion_core'
        const core_size = 15;
        ctx.fillStyle = team1_color;
        ctx.fillRect(core.x - core_size / 2, core.y - core_size / 2, core_size, core_size);
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.strokeRect(core.x - core_size / 2, core.y - core_size / 2, core_size, core_size);

        // Draw prongs and lines
        const prong_size = 10;
        prongs.forEach(p => {
            ctx.fillStyle = team1_color;
            ctx.fillRect(p.x - prong_size / 2, p.y - prong_size / 2, prong_size, prong_size);
        });
        prongs.forEach(p => illustrationHelpers.drawLines(ctx, [{p1: core, p2: p}], team1_color, 4));

        // Draw bastion outline
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
        const p1 = {x: w*0.4, y: h*0.1};
        const p2 = {x: w*0.6, y: h*0.1};
        const p3 = {x: w*0.6, y: h*0.9};
        const p4 = {x: w*0.4, y: h*0.9};

        const points = [p1, p2, p3, p4];
        // Draw points as monolith pillars
        ctx.fillStyle = team1_color;
        const pillar_w = 4;
        const pillar_h = 12;
        points.forEach(p => {
            ctx.fillRect(p.x - pillar_w / 2, p.y - pillar_h / 2, pillar_w, pillar_h);
        });
        illustrationHelpers.drawLines(ctx, [{p1, p2}, {p1:p2,p2:p3}, {p1:p3,p2:p4}, {p1:p4,p2:p1}], team1_color);

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
    'fortify_mirror_structure': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const axis1 = {x: w*0.5, y: h*0.1};
        const axis2 = {x: w*0.5, y: h*0.9};
        
        // Original structure (a V-shape)
        const p_orig1 = {x: w*0.3, y: h*0.3};
        const p_orig2 = {x: w*0.2, y: h*0.5};
        const p_orig_structure = [p_orig1, p_orig2];

        // Reflected structure
        const p_refl1 = {x: w*0.7, y: h*0.3};
        const p_refl2 = {x: w*0.8, y: h*0.5};
        const p_refl_structure = [p_refl1, p_refl2];

        // Axis
        illustrationHelpers.drawPoints(ctx, [axis1, axis2], team1_color);
        illustrationHelpers.drawDashedLine(ctx, axis1, axis2, '#aaa');
        
        // Original line
        illustrationHelpers.drawPoints(ctx, p_orig_structure, team1_color);
        illustrationHelpers.drawLines(ctx, [{p1: p_orig1, p2: p_orig2}], team1_color);
        
        // Reflection lines
        illustrationHelpers.drawDashedLine(ctx, p_orig1, p_refl1, '#aaa');
        illustrationHelpers.drawDashedLine(ctx, p_orig2, p_refl2, '#aaa');
        
        // Reflected structure (faded)
        ctx.save();
        ctx.globalAlpha = 0.5;
        illustrationHelpers.drawPoints(ctx, p_refl_structure, team1_color);
        illustrationHelpers.drawLines(ctx, [{p1: p_refl1, p2: p_refl2}], team1_color);
        ctx.restore();
    },
    'rune_area_shield': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const t1 = {x: w*0.5, y: h*0.1};
        const t2 = {x: w*0.1, y: h*0.9};
        const t3 = {x: w*0.9, y: h*0.9};
        const core = {x: w*0.5, y: h*0.6};
        
        // Draw rune
        illustrationHelpers.drawPoints(ctx, [t1, t2, t3, core], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:t1,p2:t2},{p1:t2,p2:t3},{p1:t3,p2:t1}], team1_color);
        
        // Fill area
        ctx.beginPath();
        ctx.moveTo(t1.x, t1.y); ctx.lineTo(t2.x, t2.y); ctx.lineTo(t3.x, t3.y); ctx.closePath();
        ctx.fillStyle = 'rgba(173, 216, 230, 0.5)'; // Shield color
        ctx.fill();

        // Line inside
        const l1 = {x: w*0.4, y: h*0.5};
        const l2 = {x: w*0.6, y: h*0.7};
        illustrationHelpers.drawPoints(ctx, [l1, l2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:l1, p2:l2}], team1_color);
        
        // Shield on line
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(l1.x, l1.y); ctx.lineTo(l2.x, l2.y);
        ctx.strokeStyle = 'rgba(173, 216, 230, 0.9)';
        ctx.lineWidth = 12;
        ctx.stroke();
        ctx.restore();
    },
    'rune_shield_pulse': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        
        // Shield rune
        const t1 = {x: w*0.3, y: h*0.2};
        const t2 = {x: w*0.1, y: h*0.8};
        const t3 = {x: w*0.5, y: h*0.8};
        const core = {x: w*0.3, y: h*0.6};
        const center = {x: (t1.x+t2.x+t3.x)/3, y: (t1.y+t2.y+t3.y)/3};
        
        illustrationHelpers.drawPoints(ctx, [t1, t2, t3, core], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:t1,p2:t2},{p1:t2,p2:t3},{p1:t3,p2:t1}], team1_color);

        // Shockwave
        ctx.save();
        ctx.beginPath();
        ctx.arc(center.x, center.y, w*0.3, 0, 2*Math.PI);
        ctx.strokeStyle = 'rgba(173, 216, 230, 0.7)'; // shield blue
        ctx.setLineDash([4,4]);
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.restore();

        // Enemy points
        const ep1 = {x: w*0.8, y: h*0.3};
        const ep2 = {x: w*0.7, y: h*0.7};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);

        // Push arrows
        illustrationHelpers.drawArrow(ctx, ep1, {x: w*0.9, y: h*0.2}, '#aaa');
        illustrationHelpers.drawArrow(ctx, ep2, {x: w*0.8, y: h*0.8}, '#aaa');
    },
    'rune_impale': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        // Trident rune
        const p_handle = {x: w*0.1, y: h*0.5};
        const p_apex = {x: w*0.3, y: h*0.5};
        const p_p1 = {x: w*0.4, y: h*0.3};
        const p_p2 = {x: w*0.4, y: h*0.7};
        illustrationHelpers.drawPoints(ctx, [p_handle, p_apex, p_p1, p_p2], team1_color);
        
        // Draw rune highlight first
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(p_handle.x, p_handle.y); ctx.lineTo(p_apex.x, p_apex.y);
        ctx.moveTo(p_p1.x, p_p1.y); ctx.lineTo(p_apex.x, p_apex.y); ctx.lineTo(p_p2.x, p_p2.y);
        ctx.strokeStyle = team1_color;
        ctx.lineWidth = 8;
        ctx.globalAlpha = 0.4;
        ctx.filter = 'blur(2px)';
        ctx.stroke();
        ctx.restore();

        // Draw normal lines on top
        illustrationHelpers.drawLines(ctx, [{p1:p_handle, p2:p_apex}, {p1:p_apex, p2:p_p1}, {p1:p_apex, p2:p_p2}], team1_color);
        
        // Beam
        const hit_point = {x: w*0.9, y: h*0.5};
        ctx.beginPath();
        ctx.moveTo(p_apex.x, p_apex.y);
        ctx.lineTo(hit_point.x, hit_point.y);
        ctx.strokeStyle = 'rgba(255, 100, 255, 1.0)';
        ctx.lineWidth = 6;
        ctx.stroke();

        // Enemy lines
        const ep1 = {x: w*0.7, y: h*0.2};
        const ep2 = {x: w*0.7, y: h*0.8};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1: ep1, p2: ep2}], team2_color, 1);
        const ep3 = {x: w*0.8, y: h*0.4};
        const ep4 = {x: w*0.8, y: h*0.6};
        illustrationHelpers.drawPoints(ctx, [ep3, ep4], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1: ep3, p2: ep4}], team2_color, 1);
        
        // Explosions
        illustrationHelpers.drawExplosion(ctx, w*0.7, h*0.5, 'red', 10);
        illustrationHelpers.drawExplosion(ctx, w*0.8, h*0.5, 'red', 10);
    },
    'rune_v_beam': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        
        // V-Rune
        const p_v = {x: w*0.2, y: h*0.5};
        const p_l1 = {x: w*0.4, y: h*0.2};
        const p_l2 = {x: w*0.4, y: h*0.8};
        
        // Draw rune highlight first
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(p_l1.x, p_l1.y); ctx.lineTo(p_v.x, p_v.y); ctx.lineTo(p_l2.x, p_l2.y);
        ctx.strokeStyle = team1_color;
        ctx.lineWidth = 6;
        ctx.globalAlpha = 0.4;
        ctx.stroke();
        ctx.restore();
        
        illustrationHelpers.drawPoints(ctx, [p_v, p_l1, p_l2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1: p_v, p2: p_l1}, {p1: p_v, p2: p_l2}], team1_color);
        
        // Beam
        const hit_point = {x: w*0.9, y: h*0.5};
        illustrationHelpers.drawArrow(ctx, p_v, hit_point, 'rgba(100, 255, 255, 1.0)');

        // Enemy Line
        const ep1 = {x: w*0.7, y: h*0.3};
        const ep2 = {x: w*0.7, y: h*0.7};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1: ep1, p2: ep2}], team2_color, 1);
    },
    'rune_t_hammer_slam': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        // T-Rune
        const p_mid = {x: w*0.3, y: h*0.5};
        const p_head = {x: w*0.5, y: h*0.5};
        const p_s1 = {x: w*0.3, y: h*0.2};
        const p_s2 = {x: w*0.3, y: h*0.8};
        illustrationHelpers.drawPoints(ctx, [p_mid, p_head, p_s1, p_s2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:p_s1, p2:p_mid}, {p1:p_mid, p2:p_s2}, {p1:p_mid, p2:p_head}], team1_color);

        // Enemy points
        const ep1 = {x: w*0.7, y: h*0.3};
        const ep2 = {x: w*0.7, y: h*0.7};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);

        // Push arrows
        illustrationHelpers.drawArrow(ctx, ep1, {x:w*0.9, y:h*0.3}, '#aaa');
        illustrationHelpers.drawArrow(ctx, ep2, {x:w*0.9, y:h*0.7}, '#aaa');
    },
    'nova_shockwave': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const center = {x: w*0.5, y: h*0.5};
        
        // Sacrificed point
        illustrationHelpers.drawPoints(ctx, [center], team1_color);
        illustrationHelpers.drawSacrificeSymbol(ctx, center.x, center.y, 10);
        
        // Enemy points being pushed
        const ep1_orig = {x: w*0.7, y: h*0.3};
        const ep2_orig = {x: w*0.3, y: h*0.7};
        const ep1_new = {x: w*0.8, y: h*0.2};
        const ep2_new = {x: w*0.2, y: h*0.8};
        
        ctx.save();
        ctx.globalAlpha = 0.5;
        illustrationHelpers.drawPoints(ctx, [ep1_orig, ep2_orig], team2_color);
        ctx.restore();
        illustrationHelpers.drawPoints(ctx, [ep1_new, ep2_new], team2_color);
        
        illustrationHelpers.drawArrow(ctx, ep1_orig, ep1_new, '#aaa');
        illustrationHelpers.drawArrow(ctx, ep2_orig, ep2_new, '#aaa');
        
        // Blast radius
        ctx.save();
        ctx.beginPath();
        ctx.arc(center.x, center.y, w*0.3, 0, 2*Math.PI);
        ctx.strokeStyle = 'rgba(255, 180, 50, 0.9)';
        ctx.setLineDash([5,5]);
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.restore();
    },
    'sacrifice_nova_burst': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const center = {x: w*0.5, y: h*0.5};
        
        // Sacrificed point
        illustrationHelpers.drawPoints(ctx, [center], team1_color);
        illustrationHelpers.drawExplosion(ctx, center.x, center.y, 'red', 25);
        illustrationHelpers.drawSacrificeSymbol(ctx, center.x, center.y, 10);
        
        // Enemy lines being destroyed
        const ep1 = {x: w*0.8, y: h*0.3};
        const ep2 = {x: w*0.8, y: h*0.7};
        const ep3 = {x: w*0.2, y: h*0.2};
        const ep4 = {x: w*0.3, y: h*0.8};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2, ep3, ep4], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1: ep1, p2: ep2}, {p1: ep3, p2: ep4}], team2_color, 1);
        
        // Blast radius
        ctx.save();
        ctx.beginPath();
        ctx.arc(center.x, center.y, w*0.3, 0, 2*Math.PI);
        ctx.strokeStyle = 'rgba(255, 100, 100, 0.5)';
        ctx.setLineDash([5,5]);
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.restore();
    },
    'sacrifice_phase_shift': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p1_orig = {x: w*0.2, y: h*0.5};
        const p2 = {x: w*0.5, y: h*0.5};
        const p1_new = {x: w*0.8, y: h*0.3};

        // Sacrificed line
        illustrationHelpers.drawLines(ctx, [{p1:p1_orig, p2:p2}], team1_color, 1);
        const mid = {x: (p1_orig.x+p2.x)/2, y: (p1_orig.y+p2.y)/2};
        illustrationHelpers.drawSacrificeSymbol(ctx, mid.x, mid.y);

        // Original points
        illustrationHelpers.drawPoints(ctx, [p1_orig, p2], team1_color);
        ctx.globalAlpha = 0.3;
        illustrationHelpers.drawPoints(ctx, [p1_orig], team1_color); // Redraw to fade it
        ctx.globalAlpha = 1.0;

        // New point and path - use portals to match effect
        ctx.strokeStyle = team1_color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(p1_orig.x, p1_orig.y, 12, 0, 2*Math.PI);
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(p1_new.x, p1_new.y, 6, 0, 2*Math.PI);
        ctx.stroke();

        illustrationHelpers.drawDashedLine(ctx, p1_orig, p1_new, '#aaa');
        illustrationHelpers.drawPoints(ctx, [p1_new], team1_color);
    },
    'sacrifice_create_whirlpool': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const center = {x: w*0.5, y: h*0.5};

        // Sacrificed point
        illustrationHelpers.drawPoints(ctx, [center], team1_color);
        illustrationHelpers.drawSacrificeSymbol(ctx, center.x, center.y);

        const pointsToPull = [
            {x: w*0.2, y: h*0.2},
            {x: w*0.8, y: h*0.3},
            {x: w*0.7, y: h*0.8},
            {x: w*0.3, y: h*0.7},
        ];

        illustrationHelpers.drawPoints(ctx, pointsToPull, team2_color);

        // Draw curved lines to show pull
        pointsToPull.forEach(p => {
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            // control point to make it curve
            const cp_x = (p.x + center.x) / 2 + (center.y - p.y) * 0.4;
            const cp_y = (p.y + center.y) / 2 - (center.x - p.x) * 0.4;
            ctx.quadraticCurveTo(cp_x, cp_y, center.x, center.y);
            ctx.strokeStyle = '#aaa';
            ctx.lineWidth = 1.5;
            ctx.stroke();
            ctx.restore();
        });
    },
    'sacrifice_cultivate_heartwood': (ctx, w, h) => {
        const team1_color = 'hsl(120, 70%, 50%)'; // Green for nature
        const center = {x: w*0.5, y: h*0.5};
        const branches = [];
        const num_branches = 5;
        const radius = w * 0.3;

        for (let i = 0; i < num_branches; i++) {
            const angle = (i / num_branches) * 2 * Math.PI;
            branches.push({
                x: center.x + Math.cos(angle) * radius,
                y: center.y + Math.sin(angle) * radius,
            });
        }
        
        // Draw original points
        illustrationHelpers.drawPoints(ctx, [center, ...branches], team1_color);
        branches.forEach(b => illustrationHelpers.drawLines(ctx, [{p1: center, p2: b}], team1_color));
        
        // Draw sacrifice 'X' over them
        [center, ...branches].forEach(p => {
            illustrationHelpers.drawSacrificeSymbol(ctx, p.x, p.y, 6);
        });

        // Draw Heartwood symbol
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
        const team1_color = 'hsl(50, 80%, 60%)'; // Light yellow for purify
        const center = {x: w*0.5, y: h*0.5};
        const radius = w * 0.35;
        const num_points = 5;
        const points = [];

        for (let i = 0; i < num_points; i++) {
            const angle = (i / num_points) * 2 * Math.PI - (Math.PI / 2); // Start from top
            points.push({
                x: center.x + Math.cos(angle) * radius,
                y: center.y + Math.sin(angle) * radius,
            });
        }
        
        for (let i = 0; i < num_points; i++) {
            illustrationHelpers.drawLines(ctx, [{p1: points[i], p2: points[(i+1)%num_points]}], team1_color);
        }
        
        // Add fill to indicate structure
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < num_points; i++) {
            ctx.lineTo(points[i].x, points[i].y);
        }
        ctx.closePath();
        ctx.fillStyle = team1_color;
        ctx.globalAlpha = 0.2;
        ctx.fill();
        ctx.globalAlpha = 1.0;

        // Draw points as purifier stars on top
        const pointRadius = 5;
        points.forEach(p => {
            ctx.beginPath();
            const spikes = 5; const outerRadius = pointRadius * 2.2; const innerRadius = pointRadius * 1.1;
            ctx.moveTo(p.x, p.y - outerRadius);
            for (let i = 0; i < spikes; i++) {
                let x_outer = p.x + Math.cos(i * 2 * Math.PI / spikes - Math.PI/2) * outerRadius;
                let y_outer = p.y + Math.sin(i * 2 * Math.PI / spikes - Math.PI/2) * outerRadius;
                ctx.lineTo(x_outer, y_outer);
                let x_inner = p.x + Math.cos((i + 0.5) * 2 * Math.PI / spikes - Math.PI/2) * innerRadius;
                let y_inner = p.y + Math.sin((i + 0.5) * 2 * Math.PI / spikes - Math.PI/2) * innerRadius;
                ctx.lineTo(x_inner, y_inner);
            }
            ctx.closePath();
            ctx.fillStyle = team1_color;
            ctx.fill();
        });
    },
    'fight_launch_payload': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const apex = {x: w*0.2, y: h*0.3};
        const b1 = {x: w*0.3, y: h*0.5};
        const b2 = {x: w*0.3, y: h*0.1};
        const cw = {x: w*0.4, y: h*0.3};
        const target = {x: w*0.8, y: h*0.7};

        illustrationHelpers.drawPoints(ctx, [apex, b1, b2, cw], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:apex,p2:b1},{p1:b1,p2:cw},{p1:cw,p2:b2},{p1:b2,p2:apex},{p1:b1,p2:b2}], team1_color);
        
        // Draw a fortified point as the target
        illustrationHelpers.drawFortifiedPoint(ctx, target, team2_color);

        // Arc
        ctx.beginPath();
        ctx.moveTo(apex.x, apex.y);
        ctx.quadraticCurveTo(w*0.5, h*0.1, target.x, target.y);
        ctx.setLineDash([4,4]);
        ctx.strokeStyle = 'red';
        ctx.stroke();
        ctx.setLineDash([]);
        
        // Explosion on target
        illustrationHelpers.drawExplosion(ctx, target.x, target.y);
    },
    'fortify_rotate_point': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const pivot = {x: w*0.5, y: h*0.5};
        const p_orig = {x: w*0.7, y: h*0.3};
        
        // Pivot point (grid center)
        ctx.strokeStyle = '#aaa';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(pivot.x - 6, pivot.y); ctx.lineTo(pivot.x + 6, pivot.y);
        ctx.moveTo(pivot.x, pivot.y - 6); ctx.lineTo(pivot.x, pivot.y + 6);
        ctx.stroke();

        // Original point
        ctx.save();
        ctx.globalAlpha = 0.4;
        illustrationHelpers.drawPoints(ctx, [p_orig], team1_color);
        ctx.restore();

        const p_new = {x: w*0.3, y: h*0.7}; // Rotated
        
        // Arc path
        ctx.beginPath();
        const radius = Math.sqrt((p_orig.x - pivot.x)**2 + (p_orig.y - pivot.y)**2);
        const startAngle = Math.atan2(p_orig.y - pivot.y, p_orig.x - pivot.x);
        const endAngle = Math.atan2(p_new.y - pivot.y, p_new.x - pivot.x);
        ctx.arc(pivot.x, pivot.y, radius, startAngle, endAngle);
        ctx.setLineDash([3, 3]);
        ctx.stroke();
        ctx.setLineDash([]);
        
        // New point
        illustrationHelpers.drawPoints(ctx, [p_new], team1_color);
    },
    'rune_time_stasis': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const v = {x: w*0.4, y: h*0.5};
        const t1 = [{x: w*0.2, y: h*0.2}, {x: w*0.2, y: h*0.8}];
        const t2 = [{x: w*0.6, y: h*0.3}, {x: w*0.6, y: h*0.7}];
        const ep = {x: w*0.8, y: h*0.5};

        illustrationHelpers.drawPoints(ctx, [v, ...t1, ...t2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:t1[0],p2:v},{p1:v,p2:t1[1]},{p1:t1[0],p2:t1[1]}], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:t2[0],p2:v},{p1:v,p2:t2[1]},{p1:t2[0],p2:t2[1]}], team1_color);
        
        illustrationHelpers.drawPoints(ctx, [ep], team2_color);
        
        // Cage
        const cage_r = 15;
        ctx.strokeStyle = 'rgba(150, 220, 255, 0.9)';
        ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(ep.x - cage_r, ep.y); ctx.lineTo(ep.x + cage_r, ep.y);
        ctx.moveTo(ep.x, ep.y - cage_r); ctx.lineTo(ep.x, ep.y + cage_r); ctx.stroke();
        ctx.beginPath(); ctx.arc(ep.x, ep.y, cage_r, 0, 2 * Math.PI); ctx.stroke();
    },
    'sacrifice_create_rift_trap': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const center = {x: w*0.5, y: h*0.5};
        
        // Sacrificed point (implodes to create trap)
        illustrationHelpers.drawPoints(ctx, [center], team1_color);
        illustrationHelpers.drawSacrificeSymbol(ctx, center.x, center.y);

        // Trap symbol is shown near the sacrifice
        const trap_center = { x: center.x + 30, y: center.y };
        const radius = 12;
        ctx.save();
        ctx.strokeStyle = team1_color;
        ctx.lineWidth = 2;
        ctx.globalAlpha = 0.6;
        ctx.beginPath();
        ctx.arc(trap_center.x, trap_center.y, radius, 0.2, Math.PI - 0.2);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(trap_center.x, trap_center.y, radius, Math.PI + 0.2, 2 * Math.PI - 0.2);
        ctx.stroke();
        ctx.restore();
    },
    'fight_purify_territory': (ctx, w, h) => {
        const team1_color = 'hsl(50, 80%, 60%)'; // Light yellow for purify
        const team2_color = 'hsl(240, 70%, 50%)';
        
        // Purifier (pentagon)
        const purifier_center = {x: w*0.3, y: h*0.5};
        const purifier_radius = w * 0.2;
        const purifier_points = [];
        for (let i = 0; i < 5; i++) {
            const angle = (i / 5) * 2 * Math.PI - (Math.PI / 2);
            purifier_points.push({
                x: purifier_center.x + Math.cos(angle) * purifier_radius,
                y: purifier_center.y + Math.sin(angle) * purifier_radius,
            });
        }
        illustrationHelpers.drawPoints(ctx, purifier_points, team1_color);
        for (let i = 0; i < 5; i++) {
            illustrationHelpers.drawLines(ctx, [{p1: purifier_points[i], p2: purifier_points[(i+1)%5]}], team1_color);
        }

        // Enemy territory
        const p1 = {x: w*0.8, y: h*0.2};
        const p2 = {x: w*0.6, y: h*0.8};
        const p3 = {x: w*0.95, y: h*0.8};
        illustrationHelpers.drawPoints(ctx, [p1,p2,p3], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1,p2},{p1:p2,p2:p3},{p1:p3,p2:p1}], team2_color);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.lineTo(p3.x, p3.y); ctx.closePath();
        ctx.fillStyle = team2_color;
        ctx.globalAlpha = 0.3;
        ctx.fill();
        
        // Draw purification wave
        ctx.save();
        ctx.globalAlpha = 1.0;
        ctx.beginPath();
        ctx.arc(purifier_center.x, purifier_center.y, w * 0.4, 0, 2*Math.PI);
        ctx.strokeStyle = team1_color;
        ctx.lineWidth = 2;
        ctx.setLineDash([4,4]);
        ctx.stroke();
        ctx.restore();

        // Draw fading effect on enemy territory
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.lineTo(p3.x, p3.y); ctx.closePath();
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        ctx.fill();
    },
    'sacrifice_build_wonder': (ctx, w, h) => {
        const team1_color = 'hsl(50, 80%, 60%)'; // Gold for wonder
        const center = {x: w*0.5, y: h*0.5};
        const radius = w * 0.3;
        const num_points = 5;
        const cycle_points = [];

        for (let i = 0; i < num_points; i++) {
            const angle = (i / num_points) * 2 * Math.PI - (Math.PI / 2);
            cycle_points.push({
                x: center.x + Math.cos(angle) * radius,
                y: center.y + Math.sin(angle) * radius,
            });
        }
        
        // Draw original star rune
        illustrationHelpers.drawPoints(ctx, [center, ...cycle_points], team1_color);
        cycle_points.forEach(p => illustrationHelpers.drawLines(ctx, [{p1: center, p2: p}], team1_color));
        for (let i = 0; i < num_points; i++) {
            illustrationHelpers.drawLines(ctx, [{p1: cycle_points[i], p2: cycle_points[(i+1)%num_points]}], team1_color);
        }
        
        // Draw sacrifice 'X' over them
        [center, ...cycle_points].forEach(p => {
            illustrationHelpers.drawSacrificeSymbol(ctx, p.x, p.y, 4);
        });

        // Draw Spire symbol at center
        ctx.save();
        ctx.fillStyle = team1_color;
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        const spire_h = 40;
        const base_w = 12;
        const mid_w = 20;

        ctx.beginPath();
        // Main body
        ctx.moveTo(center.x - base_w/2, center.y + spire_h/2);
        ctx.lineTo(center.x - mid_w/2, center.y);
        ctx.lineTo(center.x, center.y - spire_h/2); // Tip
        ctx.lineTo(center.x + mid_w/2, center.y);
        ctx.lineTo(center.x + base_w/2, center.y + spire_h/2);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        ctx.restore();
    },
    'rune_raise_barricade': (ctx, w, h) => {
        const team1_color = 'hsl(30, 70%, 50%)'; // Brownish for earth/wall
        
        // 1. Draw Barricade Rune (rectangle)
        const p1 = {x: w*0.2, y: h*0.2};
        const p2 = {x: w*0.8, y: h*0.2};
        const p3 = {x: w*0.8, y: h*0.8};
        const p4 = {x: w*0.2, y: h*0.8};
        const points = [p1, p2, p3, p4];
        illustrationHelpers.drawPoints(ctx, points, team1_color);
        illustrationHelpers.drawLines(ctx, [{p1,p2},{p1:p2,p2:p3},{p1:p3,p2:p4},{p1:p4,p2:p1}], team1_color);
        
        // 2. Draw the resulting barricade (no consumption)
        const mid1 = {x: (p1.x+p3.x)/2, y: (p1.y+p3.y)/2};
        ctx.save();
        ctx.strokeStyle = team1_color;
        ctx.lineWidth = 6;
        ctx.lineCap = 'round';
        illustrationHelpers.drawJaggedLine(ctx, p1, p3, 10, 4);
        ctx.restore();
    },
    'terraform_create_fissure': (ctx, w, h) => {
        const team1_color = 'hsl(280, 70%, 60%)'; // Purple for rift
        
        // Rift Spire
        const spire_center = {x: w*0.2, y: h*0.5};
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

        // Beam from spire to fissure start
        const fissure_start = {x: w*0.4, y: h*0.3};
        illustrationHelpers.drawDashedLine(ctx, spire_center, fissure_start, team1_color);
        
        // Fissure
        const fissure_end = {x: w*0.9, y: h*0.7};
        ctx.save();
        ctx.strokeStyle = 'rgba(30, 30, 30, 0.8)';
        ctx.lineWidth = 4;
        ctx.lineCap = 'round';
        illustrationHelpers.drawJaggedLine(ctx, fissure_start, fissure_end, 15, 6);
        ctx.restore();
    },
    'terraform_form_rift_spire': (ctx, w, h) => {
        const team1_color = 'hsl(280, 70%, 60%)'; // Purple for rift
        const center = {x: w*0.5, y: h*0.5};

        // 3 territories meeting at 'center'
        const t1_p2 = {x: w*0.2, y: h*0.2};
        const t1_p3 = {x: w*0.8, y: h*0.2};
        const t2_p3 = {x: w*0.2, y: h*0.8};
        const t3_p3 = {x: w*0.8, y: h*0.8};

        // Draw territories
        ctx.save();
        ctx.fillStyle = team1_color;
        ctx.globalAlpha = 0.2;
        ctx.beginPath(); // T1
        ctx.moveTo(center.x, center.y); ctx.lineTo(t1_p2.x, t1_p2.y); ctx.lineTo(t1_p3.x, t1_p3.y); ctx.closePath();
        ctx.fill();
        ctx.beginPath(); // T2
        ctx.moveTo(center.x, center.y); ctx.lineTo(t1_p2.x, t1_p2.y); ctx.lineTo(t2_p3.x, t2_p3.y); ctx.closePath();
        ctx.fill();
        ctx.beginPath(); // T3
        ctx.moveTo(center.x, center.y); ctx.lineTo(t1_p3.x, t1_p3.y); ctx.lineTo(t3_p3.x, t3_p3.y); ctx.closePath();
        ctx.fill();
        ctx.restore();

        // Draw points
        illustrationHelpers.drawPoints(ctx, [center, t1_p2, t1_p3, t2_p3, t3_p3], team1_color);
        
        // Draw Spire symbol over it
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
        const team1_color = 'hsl(50, 80%, 60%)'; // Gold for star
        const team2_color = 'hsl(240, 70%, 50%)';

        const center = {x: w*0.35, y: h*0.5};
        const radius = w * 0.25;
        const num_points = 5;
        const cycle_points = [];

        for (let i = 0; i < num_points; i++) {
            const angle = (i / num_points) * 2 * Math.PI - (Math.PI / 2);
            cycle_points.push({
                x: center.x + Math.cos(angle) * radius,
                y: center.y + Math.sin(angle) * radius,
            });
        }
        
        // Draw star rune
        illustrationHelpers.drawPoints(ctx, [center, ...cycle_points], team1_color);
        cycle_points.forEach(p => illustrationHelpers.drawLines(ctx, [{p1: center, p2: p}], team1_color));
        for (let i = 0; i < num_points; i++) {
            illustrationHelpers.drawLines(ctx, [{p1: cycle_points[i], p2: cycle_points[(i+1)%num_points]}], team1_color);
        }

        // Draw cascade/blast from center
        ctx.save();
        ctx.beginPath();
        ctx.arc(center.x, center.y, w*0.4, 0, 2*Math.PI);
        const gradient = ctx.createRadialGradient(center.x, center.y, 0, center.x, center.y, w*0.4);
        gradient.addColorStop(0, `rgba(255, 255, 150, 0.8)`);
        gradient.addColorStop(1, 'rgba(255, 255, 150, 0)');
        ctx.fillStyle = gradient;
        ctx.fill();
        ctx.restore();
        
        // Enemy lines
        const ep1 = {x: w*0.8, y: h*0.2};
        const ep2 = {x: w*0.8, y: h*0.8};
        const ep3 = {x: w*0.6, y: h*0.1};
        const ep4 = {x: w*0.9, y: h*0.1};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2, ep3, ep4], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1: ep1, p2: ep2}, {p1: ep3, p2: ep4}], team2_color, 1);
        
        // Damage effect
        illustrationHelpers.drawExplosion(ctx, w*0.8, h*0.5, 'red', 12);
        illustrationHelpers.drawExplosion(ctx, w*0.75, h*0.1, 'red', 12);
    },
    'rune_focus_beam': (ctx, w, h) => {
        const team1_color = 'hsl(50, 80%, 60%)'; // Gold for star
        const team2_color = 'hsl(240, 70%, 50%)';

        // Star rune
        const center = {x: w*0.3, y: h*0.5};
        const radius = w * 0.2;
        const num_points = 5;
        const cycle_points = [];
        for (let i = 0; i < num_points; i++) {
            const angle = (i / num_points) * 2 * Math.PI - (Math.PI / 2);
            cycle_points.push({
                x: center.x + Math.cos(angle) * radius,
                y: center.y + Math.sin(angle) * radius,
            });
        }
        illustrationHelpers.drawPoints(ctx, [center, ...cycle_points], team1_color);
        cycle_points.forEach(p => illustrationHelpers.drawLines(ctx, [{p1: center, p2: p}], team1_color));
        for (let i = 0; i < num_points; i++) {
            illustrationHelpers.drawLines(ctx, [{p1: cycle_points[i], p2: cycle_points[(i+1)%num_points]}], team1_color);
        }

        // High-value enemy target (bastion core)
        const target = {x: w*0.8, y: h*0.5};
        const core_size = 15;
        ctx.fillStyle = team2_color;
        ctx.fillRect(target.x - core_size / 2, target.y - core_size / 2, core_size, core_size);
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.strokeRect(target.x - core_size / 2, target.y - core_size / 2, core_size, core_size);

        // Beam
        illustrationHelpers.drawArrow(ctx, center, target, 'rgba(255, 255, 150, 1.0)');

        // Explosion
        illustrationHelpers.drawExplosion(ctx, target.x, target.y, 'red', 20);
    },
    'rune_gravity_well': (ctx, w, h) => {
        const team1_color = 'hsl(50, 80%, 60%)'; // Gold for star
        const team2_color = 'hsl(240, 70%, 50%)';

        const center = {x: w*0.5, y: h*0.5};
        const radius = w * 0.3;
        const num_points = 5;
        const cycle_points = [];

        for (let i = 0; i < num_points; i++) {
            const angle = (i / num_points) * 2 * Math.PI - (Math.PI / 2);
            cycle_points.push({
                x: center.x + Math.cos(angle) * radius,
                y: center.y + Math.sin(angle) * radius,
            });
        }
        
        // Draw star rune
        illustrationHelpers.drawPoints(ctx, [center, ...cycle_points], team1_color);
        cycle_points.forEach(p => illustrationHelpers.drawLines(ctx, [{p1: center, p2: p}], team1_color));
        for (let i = 0; i < num_points; i++) {
            illustrationHelpers.drawLines(ctx, [{p1: cycle_points[i], p2: cycle_points[(i+1)%num_points]}], team1_color);
        }

        // Draw gravity well effect
        ctx.save();
        ctx.beginPath();
        ctx.arc(center.x, center.y, w*0.45, 0, 2*Math.PI);
        ctx.strokeStyle = team1_color;
        ctx.setLineDash([4,4]);
        ctx.lineWidth = 3;
        ctx.globalAlpha = 0.7;
        ctx.stroke();
        ctx.restore();

        // Enemy points
        const ep1 = {x: w*0.8, y: h*0.3};
        const ep2 = {x: w*0.7, y: h*0.7};
        const ep3 = {x: w*0.3, y: h*0.2};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2, ep3], team2_color);

        // Push arrows
        illustrationHelpers.drawArrow(ctx, ep1, {x: w*0.9, y: h*0.2}, '#aaa');
        illustrationHelpers.drawArrow(ctx, ep2, {x: w*0.8, y: h*0.8}, '#aaa');
        illustrationHelpers.drawArrow(ctx, ep3, {x: w*0.2, y: h*0.1}, '#aaa');
    },
    'rune_cardinal_pulse': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';

        // Plus rune
        const center = {x: w*0.5, y: h*0.5};
        const arms = [
            {x: w*0.5, y: h*0.2}, // top
            {x: w*0.8, y: h*0.5}, // right
            {x: w*0.5, y: h*0.8}, // bottom
            {x: w*0.2, y: h*0.5}  // left
        ];
        const rune_points = [center, ...arms];
        illustrationHelpers.drawPoints(ctx, rune_points, team1_color);
        arms.forEach(p => illustrationHelpers.drawLines(ctx, [{p1: center, p2: p}], team1_color));
        
        // Beams
        // 1. Right beam hits enemy line
        const ep1 = {x: w*0.9, y: h*0.3};
        const ep2 = {x: w*0.9, y: h*0.7};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1:ep1, p2:ep2}], team2_color);
        const hit_point = {x: w*0.9, y: h*0.5};
        illustrationHelpers.drawArrow(ctx, center, hit_point, team1_color);
        illustrationHelpers.drawExplosion(ctx, hit_point.x, hit_point.y, 'red', 12);

        // 2. Top beam misses, creates point
        const new_point = {x: w*0.5, y: h*0.05};
        illustrationHelpers.drawDashedLine(ctx, center, new_point, team1_color);
        illustrationHelpers.drawPoints(ctx, [new_point], team1_color);
        
        // 3 & 4. Other beams just flying off
        illustrationHelpers.drawArrow(ctx, center, {x:w*0.05, y:h*0.5}, team1_color);
        illustrationHelpers.drawArrow(ctx, center, {x:w*0.5, y:h*0.95}, team1_color);
    },
    'rune_parallel_discharge': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        
        // Parallelogram rune
        const p1 = {x: w*0.2, y: h*0.2};
        const p2 = {x: w*0.6, y: h*0.2};
        const p3 = {x: w*0.8, y: h*0.8};
        const p4 = {x: w*0.4, y: h*0.8};
        const points = [p1, p2, p3, p4];
        illustrationHelpers.drawPoints(ctx, points, team1_color);
        illustrationHelpers.drawLines(ctx, [{p1,p2},{p1:p2,p2:p3},{p1:p3,p2:p4},{p1:p4,p2:p1}], team1_color);
        
        // Crossing enemy line
        const ep1 = {x: w*0.5, y: h*0.1};
        const ep2 = {x: w*0.5, y: h*0.9};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1:ep1, p2:ep2}], team2_color);
        
        // Discharge effect
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.lineTo(p3.x, p3.y); ctx.lineTo(p4.x, p4.y);
        ctx.closePath();
        ctx.fillStyle = 'rgba(255, 255, 150, 0.7)'; // Yellowish glow
        ctx.fill();
        ctx.restore();

        // Blast on enemy line
        illustrationHelpers.drawExplosion(ctx, w*0.5, h*0.5);
    },
    'sacrifice_attune_nexus': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p1 = {x: w*0.2, y: h*0.2};
        const p2 = {x: w*0.8, y: h*0.2};
        const p3 = {x: w*0.8, y: h*0.8};
        const p4 = {x: w*0.2, y: h*0.8};
        const points = [p1, p2, p3, p4];
        const center = {x: w*0.5, y: h*0.5};

        // Draw Nexus
        illustrationHelpers.drawPoints(ctx, points, team1_color);
        illustrationHelpers.drawLines(ctx, [{p1,p2},{p1:p2,p2:p3},{p1:p3,p2:p4},{p1:p4,p2:p1}], team1_color);
        // Draw other diagonal as existing
        illustrationHelpers.drawLines(ctx, [{p1:p2, p2:p4}], team1_color);
        
        // Draw sacrificed diagonal
        illustrationHelpers.drawLines(ctx, [{p1:p1, p2:p3}], team1_color, 1);
        const mid_sac = {x: (p1.x+p3.x)/2, y: (p1.y+p3.y)/2};
        illustrationHelpers.drawSacrificeSymbol(ctx, mid_sac.x, mid_sac.y);

        // Draw attuned effect - arrows to match pull effect
        illustrationHelpers.drawArrow(ctx, p1, center, team1_color);
        illustrationHelpers.drawArrow(ctx, p3, center, team1_color);

        ctx.fillStyle = team1_color;
        ctx.beginPath(); ctx.arc(center.x, center.y, 6, 0, 2 * Math.PI); ctx.fill();
    },
    'sacrifice_line_retaliation': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const p1 = {x: w*0.2, y: h*0.5};
        const p_sac = {x: w*0.4, y: h*0.5};
        const p2 = {x: w*0.6, y: h*0.5};
        
        // Faded original line
        ctx.save();
        ctx.globalAlpha = 0.4;
        illustrationHelpers.drawPoints(ctx, [p1, p_sac, p2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:p1, p2:p2}], team1_color, 2);
        ctx.restore();

        // Sacrificed point
        illustrationHelpers.drawSacrificeSymbol(ctx, p_sac.x, p_sac.y);

        // Projectiles
        const target1 = {x: w*0.9, y: h*0.5}; // along the line
        const target2 = {x: w*0.4, y: h*0.1}; // perpendicular
        illustrationHelpers.drawArrow(ctx, p_sac, target1, team1_color);
        illustrationHelpers.drawArrow(ctx, p_sac, target2, team1_color);

        // Enemy line to hit
        const ep1 = {x: w*0.9, y: h*0.3};
        const ep2 = {x: w*0.9, y: h*0.7};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1:ep1, p2:ep2}], team2_color, 1);
        illustrationHelpers.drawExplosion(ctx, target1.x, target1.y);
    },
    'sacrifice_scorch_territory': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p1 = {x: w*0.5, y: h*0.1};
        const p2 = {x: w*0.1, y: h*0.8};
        const p3 = {x: w*0.9, y: h*0.8};
        const points = [p1, p2, p3];

        // Draw original territory
        illustrationHelpers.drawPoints(ctx, points, team1_color);
        illustrationHelpers.drawLines(ctx, [{p1,p2},{p1:p2,p2:p3},{p1:p3,p2:p1}], team1_color);
        
        // Draw sacrifice 'X' over points
        points.forEach(p => {
            illustrationHelpers.drawSacrificeSymbol(ctx, p.x, p.y);
        });

        // Draw scorched area
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.lineTo(p3.x, p3.y); ctx.closePath();
        ctx.fillStyle = 'rgba(50, 50, 50, 0.7)';
        ctx.fill();
        ctx.strokeStyle = `rgba(200, 80, 0, 0.8)`;
        ctx.lineWidth = 2;
        illustrationHelpers.drawJaggedLine(ctx, p1, p2, 10, 3);
        illustrationHelpers.drawJaggedLine(ctx, p2, p3, 10, 3);
        illustrationHelpers.drawJaggedLine(ctx, p3, p1, 10, 3);
        ctx.restore();
    },
    'attack_miss_spawn': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const p1 = {x: w*0.1, y: h*0.3};
        const p2 = {x: w*0.4, y: h*0.3};
        const ep1 = {x: w*0.7, y: h*0.6};
        const ep2 = {x: w*0.7, y: h*0.9};
        const p_new = {x: w*0.95, y: h*0.3};
        illustrationHelpers.drawPoints(ctx, [p1,p2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1, p2}], team1_color);
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1: ep1, p2: ep2}], team2_color);
        illustrationHelpers.drawDashedLine(ctx, p2, p_new, team1_color);
        illustrationHelpers.drawPoints(ctx, [p_new], team1_color);
    },
    'fight_parallel_strike_miss_spawn': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const p_source = {x: w*0.2, y: h*0.3};
        const l1 = {x: w*0.3, y: h*0.8};
        const l2 = {x: w*0.7, y: h*0.8};
        illustrationHelpers.drawPoints(ctx, [p_source, l1, l2], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:l1, p2:l2}], team1_color);
        const ep1 = {x: w*0.6, y: h*0.5};
        illustrationHelpers.drawPoints(ctx, [ep1], team2_color);
        const p_new = {x: w*0.95, y: h*0.3};
        illustrationHelpers.drawDashedLine(ctx, p_source, p_new, team1_color);
        illustrationHelpers.drawPoints(ctx, [p_new], team1_color);
    },
    'pincer_fizzle_barricade': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p1 = {x: w*0.3, y: h*0.3};
        const p2 = {x: w*0.3, y: h*0.7};
        illustrationHelpers.drawPoints(ctx, [p1, p2], team1_color);
        ctx.save();
        ctx.strokeStyle = team1_color;
        ctx.lineWidth = 6;
        ctx.lineCap = 'round';
        ctx.globalAlpha = 0.8;
        illustrationHelpers.drawJaggedLine(ctx, p1, p2, 8, 4);
        ctx.restore();
    },
    'territory_fizzle_reinforce': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const p1 = {x: w*0.5, y: h*0.2};
        const p2 = {x: w*0.2, y: h*0.8};
        const p3 = {x: w*0.8, y: h*0.8};
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.lineTo(p3.x, p3.y); ctx.closePath();
        ctx.fillStyle = team1_color;
        ctx.globalAlpha = 0.3;
        ctx.fill();
        ctx.globalAlpha = 1.0;
        illustrationHelpers.drawPoints(ctx, [p1, p2, p3], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1,p2},{p1:p2,p2:p3},{p1:p3,p2:p1}], team1_color, 4);
        ctx.save();
        ctx.globalAlpha = 0.5;
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 6;
        ctx.filter = 'blur(2px)';
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.lineTo(p3.x, p3.y); ctx.closePath();
        ctx.stroke();
        ctx.restore();
    },
    'fortify_point': (ctx, w, h) => {
        const team1_color = 'hsl(40, 70%, 50%)'; // Defensive color
        const p_orig = {x: w*0.3, y: h*0.5};
        const p_fortified = {x: w*0.7, y: h*0.5};

        // Original point (circle)
        illustrationHelpers.drawPoints(ctx, [p_orig], team1_color);
        
        // Arrow
        illustrationHelpers.drawArrow(ctx, {x:w*0.45, y:h*0.5}, {x:w*0.55, y:h*0.5}, '#aaa');
        
        // Fortified point (diamond)
        illustrationHelpers.drawFortifiedPoint(ctx, p_fortified, team1_color);
    },
    'fight_trigger_retaliation': (ctx, w, h) => {
        const team1_color = 'hsl(0, 70%, 50%)';
        const team2_color = 'hsl(240, 70%, 50%)';
        const p1 = {x: w*0.2, y: h*0.5};
        const p_trigger = {x: w*0.4, y: h*0.5};
        
        // The line
        illustrationHelpers.drawPoints(ctx, [p1, p_trigger], team1_color);
        illustrationHelpers.drawLines(ctx, [{p1:p1, p2:p_trigger}], team1_color, 2);

        // No sacrifice symbol on p_trigger
        // Just a glow to show it's the trigger
        ctx.beginPath();
        ctx.arc(p_trigger.x, p_trigger.y, 10, 0, 2 * Math.PI);
        ctx.fillStyle = 'rgba(255, 255, 150, 0.7)';
        ctx.fill();
        illustrationHelpers.drawPoints(ctx, [p_trigger], team1_color); // redraw on top

        // Projectiles
        const target1 = {x: w*0.8, y: h*0.5}; // along the line
        const target2 = {x: w*0.4, y: h*0.1}; // perpendicular
        illustrationHelpers.drawArrow(ctx, p_trigger, target1, team1_color);
        illustrationHelpers.drawArrow(ctx, p_trigger, target2, team1_color);

        // Enemy line to hit
        const ep1 = {x: w*0.8, y: h*0.3};
        const ep2 = {x: w*0.8, y: h*0.7};
        illustrationHelpers.drawPoints(ctx, [ep1, ep2], team2_color);
        illustrationHelpers.drawLines(ctx, [{p1:ep1, p2:ep2}], team2_color, 1);
        illustrationHelpers.drawExplosion(ctx, target1.x, target1.y);
    },
};

/**
 * Generates PNGs for all illustrations and sends them to the server to be saved.
 * This is a developer-only utility.
 */
async function generateAndSaveAllIllustrations() {
    if (typeof api === 'undefined' || typeof api.getAllActions !== 'function' || typeof api.saveIllustration !== 'function') {
        alert("API is not ready. Cannot generate illustrations.");
        return;
    }

    const allActions = await api.getAllActions();
    const actionNames = allActions.map(a => a.name);

    console.log(`Starting generation of ${actionNames.length} illustrations...`);
    const statusDiv = document.createElement('div');
    statusDiv.style = "position: fixed; top: 10px; left: 10px; background: #333; color: white; padding: 10px; border-radius: 5px; z-index: 2000;";
    document.body.appendChild(statusDiv);

    let successCount = 0;
    let failCount = 0;

    for (const actionName of actionNames) {
        statusDiv.textContent = `Generating ${actionName}... (${successCount + failCount + 1}/${actionNames.length})`;

        const canvas = document.createElement('canvas');
        canvas.width = 150;
        canvas.height = 150;
        const ctx = canvas.getContext('2d');
        
        const drawer = illustrationDrawers[actionName] || illustrationDrawers['default'];
        
        // Clear canvas with a transparent background
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        drawer(ctx, canvas.width, canvas.height);
        
        const dataUrl = canvas.toDataURL('image/png');
        
        try {
            const response = await api.saveIllustration(actionName, dataUrl);
            if (response.success) {
                console.log(`Successfully saved ${actionName}.png`);
                successCount++;
            } else {
                console.error(`Failed to save ${actionName}.png:`, response.error);
                failCount++;
            }
        } catch (error) {
            console.error(`Error sending ${actionName}.png to server:`, error);
            failCount++;
        }
    }

    statusDiv.textContent = `Generation complete! Success: ${successCount}, Failed: ${failCount}. Reloading guide...`;
    
    // Refresh the action guide to show the new images
    if(typeof window.initActionGuide === 'function') {
        await window.initActionGuide();
    }
    
    setTimeout(() => {
        if(document.body.contains(statusDiv)) {
            document.body.removeChild(statusDiv);
        }
    }, 5000);
}