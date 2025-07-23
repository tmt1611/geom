import random
import math
import uuid

from .geometry import distance_sq, is_spawn_location_valid

class TurnProcessor:
    def __init__(self, game):
        self.game = game

    @property
    def state(self):
        """Provides direct access to the game's current state dictionary."""
        return self.game.state

    def process_turn_start_effects(self):
        """
        Processes all effects that happen at the start of a turn.
        Returns True if the game ended as a result of these effects (e.g., Wonder victory).
        """
        self._process_shields_and_stasis()
        self._process_rift_traps()
        self._process_anchors()
        self._process_heartwoods()
        self._process_whirlpools()
        self._process_monoliths()
        
        game_ended = self._process_wonders()
        if game_ended:
            return True

        self._process_spires_fissures_barricades()
        return False

    def _process_shields_and_stasis(self):
        """Handles decay of shields and stasis effects."""
        self.state['shields'] = {lid: turns - 1 for lid, turns in self.state['shields'].items() if turns - 1 > 0}
        if self.state.get('stasis_points'):
            self.state['stasis_points'] = {pid: turns - 1 for pid, turns in self.state['stasis_points'].items() if turns - 1 > 0}

    def _process_rift_traps(self):
        """Handles rift trap triggers, expiration, and spawning."""
        if not self.state.get('rift_traps'):
            return

        remaining_traps = []
        for trap in self.state['rift_traps']:
            triggered_point_id = None
            for pid, point in self.state['points'].items():
                if point['teamId'] != trap['teamId'] and distance_sq(trap['coords'], point) < trap['radius_sq']:
                    triggered_point_id = pid
                    break
            
            if triggered_point_id:
                destroyed_point = self.game._delete_point_and_connections(triggered_point_id, aggressor_team_id=trap['teamId'])
                if destroyed_point:
                    team_name = self.state['teams'][trap['teamId']]['name']
                    enemy_team_name = self.state['teams'][destroyed_point['teamId']]['name']
                    log_msg = { 'teamId': trap['teamId'], 'message': f"A Rift Trap from Team {team_name} snared and destroyed a point from Team {enemy_team_name}!", 'short_message': '[TRAP!]'}
                    self.state['game_log'].append(log_msg)
                    self.state['new_turn_events'].append({ 'type': 'rift_trap_trigger', 'trap': trap, 'destroyed_point': destroyed_point })
                continue

            trap['turns_left'] -= 1
            if trap['turns_left'] <= 0:
                is_valid, _ = is_spawn_location_valid(
                    trap['coords'], trap['teamId'], self.state['grid_size'], self.state['points'],
                    self.state.get('fissures', []), self.state.get('heartwoods', {})
                )
                if is_valid:
                    new_point_id = f"p_{uuid.uuid4().hex[:6]}"
                    new_point = {"x": round(trap['coords']['x']), "y": round(trap['coords']['y']), "teamId": trap['teamId'], "id": new_point_id}
                    self.state['points'][new_point_id] = new_point
                    
                    team_name = self.state['teams'][trap['teamId']]['name']
                    log_msg = { 'teamId': trap['teamId'], 'message': f"An unused Rift Trap from Team {team_name} stabilized into a new point.", 'short_message': '[TRAP->SPAWN]' }
                    self.state['game_log'].append(log_msg)
                    self.state['new_turn_events'].append({ 'type': 'rift_trap_expire', 'trap': trap, 'new_point': new_point })
                continue
            
            remaining_traps.append(trap)
        
        self.state['rift_traps'] = remaining_traps

    def _process_anchors(self):
        """Handles anchor point pulls and expiration."""
        expired_anchors = []
        pull_strength = 0.2
        grid_size = self.state['grid_size']
        for anchor_pid, anchor_data in list(self.state['anchors'].items()):
            if anchor_pid not in self.state['points']:
                expired_anchors.append(anchor_pid)
                continue
            
            anchor_point = self.state['points'][anchor_pid]
            anchor_radius_sq = (grid_size * 0.4)**2
            for point in self.state['points'].values():
                if point['teamId'] != anchor_data['teamId'] and distance_sq(anchor_point, point) < anchor_radius_sq:
                    dx, dy = anchor_point['x'] - point['x'], anchor_point['y'] - point['y']
                    new_x = point['x'] + dx * pull_strength
                    new_y = point['y'] + dy * pull_strength
                    point['x'] = round(max(0, min(grid_size - 1, new_x)))
                    point['y'] = round(max(0, min(grid_size - 1, new_y)))

            anchor_data['turns_left'] -= 1
            if anchor_data['turns_left'] <= 0:
                expired_anchors.append(anchor_pid)
        for anchor_pid in expired_anchors:
            if anchor_pid in self.state['anchors']: del self.state['anchors'][anchor_pid]
    
    def _process_heartwoods(self):
        """Handles Heartwood point generation."""
        if not self.state.get('heartwoods'):
            return

        for teamId, heartwood in self.state['heartwoods'].items():
            heartwood['growth_counter'] += 1
            if heartwood['growth_counter'] >= heartwood['growth_interval']:
                heartwood['growth_counter'] = 0
                
                for _ in range(10):
                    angle = random.uniform(0, 2 * math.pi)
                    radius = self.state['grid_size'] * random.uniform(0.05, 0.15)
                    
                    new_x = heartwood['center_coords']['x'] + math.cos(angle) * radius
                    new_y = heartwood['center_coords']['y'] + math.sin(angle) * radius
                    
                    grid_size = self.state['grid_size']
                    final_x = round(max(0, min(grid_size - 1, new_x)))
                    final_y = round(max(0, min(grid_size - 1, new_y)))
                    
                    new_p_coords = {'x': final_x, 'y': final_y}
                    if not is_spawn_location_valid(
                        new_p_coords, teamId, self.state['grid_size'], self.state['points'],
                        self.state.get('fissures', []), self.state.get('heartwoods', {})
                    )[0]: continue

                    new_point_id = f"p_{uuid.uuid4().hex[:6]}"
                    new_point = {"x": final_x, "y": final_y, "teamId": teamId, "id": new_point_id}
                    self.state['points'][new_point_id] = new_point
                    
                    team_name = self.state['teams'][teamId]['name']
                    log_msg = {'teamId': teamId, 'message': f"The Heartwood of Team {team_name} birthed a new point.", 'short_message': '[HW:GROWTH]'}
                    self.state['game_log'].append(log_msg)
                    self.state['new_turn_events'].append({'type': 'heartwood_growth', 'new_point': new_point, 'heartwood_id': heartwood['id']})
                    break

    def _process_whirlpools(self):
        """Handles whirlpool pulls and expiration."""
        if not self.state.get('whirlpools'):
            return

        active_whirlpools = []
        grid_size = self.state['grid_size']
        for whirlpool in self.state['whirlpools']:
            whirlpool['turns_left'] -= 1
            if whirlpool['turns_left'] > 0:
                active_whirlpools.append(whirlpool)
                wp_coords, wp_radius_sq, wp_strength, wp_swirl = whirlpool['coords'], whirlpool['radius_sq'], whirlpool['strength'], whirlpool['swirl']

                for point in self.state['points'].values():
                    if distance_sq(wp_coords, point) < wp_radius_sq:
                        dx, dy = wp_coords['x'] - point['x'], wp_coords['y'] - point['y']
                        dist = math.sqrt(dx**2 + dy**2)
                        if dist < 0.1: continue
                        
                        angle = math.atan2(dy, dx)
                        new_dist, new_angle = dist * (1 - wp_strength), angle + wp_swirl
                        new_dx, new_dy = math.cos(new_angle) * new_dist, math.sin(new_angle) * new_dist
                        new_x, new_y = wp_coords['x'] - new_dx, wp_coords['y'] - new_dy
                        point['x'] = round(max(0, min(grid_size - 1, new_x)))
                        point['y'] = round(max(0, min(grid_size - 1, new_y)))

        self.state['whirlpools'] = active_whirlpools

    def _process_monoliths(self):
        """Handles Monolith resonance waves."""
        if not self.state.get('monoliths'):
            return

        for monolith_id, monolith in list(self.state['monoliths'].items()):
            monolith['charge_counter'] += 1
            if monolith['charge_counter'] >= monolith['charge_interval']:
                monolith['charge_counter'] = 0
                
                team_name = self.state['teams'][monolith['teamId']]['name']
                log_msg = {'teamId': monolith['teamId'], 'message': f"A Monolith from Team {team_name} emits a reinforcing wave.", 'short_message': '[MONOLITH:WAVE]'}
                self.state['game_log'].append(log_msg)
                self.state['new_turn_events'].append({'type': 'monolith_wave', 'monolith_id': monolith_id, 'center_coords': monolith['center_coords'], 'radius_sq': monolith['wave_radius_sq']})

                center, radius_sq = monolith['center_coords'], monolith['wave_radius_sq']
                for line in self.game.get_team_lines(monolith['teamId']):
                    if line['p1_id'] not in self.state['points'] or line['p2_id'] not in self.state['points']: continue
                    p1, p2 = self.state['points'][line['p1_id']], self.state['points'][line['p2_id']]
                    midpoint = {'x': (p1['x'] + p2['x']) / 2, 'y': (p1['y'] + p2['y']) / 2}
                    if distance_sq(center, midpoint) < radius_sq:
                        self.game._strengthen_line(line)

    def _process_wonders(self):
        """Handles Wonder countdowns and checks for Wonder victory. Returns True if game ends."""
        if not self.state.get('wonders'):
            return False

        for wonder in list(self.state['wonders'].values()):
            if wonder['type'] == 'ChronosSpire':
                wonder['turns_to_victory'] -= 1
                team_name = self.state['teams'][wonder['teamId']]['name']
                log_msg = {'teamId': wonder['teamId'], 'message': f"The Chronos Spire of Team {team_name} pulses. Victory in {wonder['turns_to_victory']} turns.", 'short_message': f'[SPIRE: T-{wonder["turns_to_victory"]}]'}
                self.state['game_log'].append(log_msg)
                
                if wonder['turns_to_victory'] <= 0:
                    self.state['game_phase'] = 'FINISHED'
                    self.state['victory_condition'] = f"Team '{team_name}' achieved victory with the Chronos Spire."
                    self.state['game_log'].append({'message': self.state['victory_condition'], 'short_message': '[WONDER VICTORY]'})
                    self.state['actions_queue_this_turn'] = []
                    return True
        return False

    def _process_spires_fissures_barricades(self):
        """Handles charging of spires and decay of fissures and barricades."""
        if self.state.get('rift_spires'):
            for spire in self.state['rift_spires'].values():
                if spire.get('charge', 0) < spire.get('charge_needed', 3):
                    spire['charge'] += 1
        
        for key in ['fissures', 'barricades']:
            if self.state.get(key):
                active_items = []
                for item in self.state[key]:
                    item['turns_left'] -= 1
                    if item['turns_left'] > 0:
                        active_items.append(item)
                self.state[key] = active_items