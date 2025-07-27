import random
import math

class TerraformActionsHandler:
    def __init__(self, game):
        self.game = game

    @property
    def state(self):
        """Provides direct access to the game's current state dictionary."""
        return self.game.state

    def create_fissure(self, teamId):
        """[TERRAFORM ACTION]: A Rift Spire creates a fissure on the map."""
        team_spires = [s for s in self.state.get('rift_spires', {}).values() if s['teamId'] == teamId and s.get('charge', 0) >= s.get('charge_needed', 3)]
        if not team_spires:
            return {'success': False, 'reason': 'no charged rift spires available'}

        spire = random.choice(team_spires)
        grid_size = self.state['grid_size']
        
        # Create a long fissure, e.g., from one border to another
        borders = [
            {'x': 0, 'y': random.randint(0, grid_size - 1)},
            {'x': grid_size - 1, 'y': random.randint(0, grid_size - 1)},
            {'x': random.randint(0, grid_size - 1), 'y': 0},
            {'x': random.randint(0, grid_size - 1), 'y': grid_size - 1}
        ]
        p1 = random.choice(borders)
        
        opposite_borders = []
        if p1['x'] == 0: opposite_borders.append({'x': grid_size - 1, 'y': random.randint(0, grid_size - 1)})
        if p1['x'] == grid_size - 1: opposite_borders.append({'x': 0, 'y': random.randint(0, grid_size - 1)})
        if p1['y'] == 0: opposite_borders.append({'x': random.randint(0, grid_size - 1), 'y': grid_size - 1})
        if p1['y'] == grid_size - 1: opposite_borders.append({'x': random.randint(0, grid_size - 1), 'y': 0})
        
        p2 = random.choice(opposite_borders) if opposite_borders else random.choice(borders)

        fissure_id = self.game._generate_id('f')
        new_fissure = { 'id': fissure_id, 'p1': p1, 'p2': p2, 'turns_left': 8 }
        self.state['fissures'].append(new_fissure)
        
        spire['charge'] = 0 # Reset charge

        return {
            'success': True,
            'type': 'create_fissure',
            'fissure': new_fissure,
            'spire_id': spire['id']
        }

    def form_rift_spire(self, teamId):
        """[TERRAFORM ACTION]: Erects a Rift Spire at a territorial nexus without sacrifice."""
        candidate_pids = self.game.query.find_rift_spire_candidates(teamId)
        if not candidate_pids:
            return {'success': False, 'reason': 'no valid location for a Rift Spire found'}

        nexus_point_id = random.choice(candidate_pids)
        nexus_point = self.state['points'].get(nexus_point_id)
        if not nexus_point:
            return {'success': False, 'reason': 'nexus point for spire disappeared'}

        spire_id = self.game._generate_id('rs')
        new_spire = {
            'id': spire_id,
            'teamId': teamId,
            'point_id': nexus_point_id,
            'coords': {'x': nexus_point['x'], 'y': nexus_point['y']},
            'charge': 0,
            'charge_needed': 3
        }
        
        self.state.setdefault('rift_spires', {})[spire_id] = new_spire

        return {
            'success': True,
            'type': 'form_rift_spire',
            'spire': new_spire
        }