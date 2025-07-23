# game_app/text_data.py

# This file contains static text data for the game to keep other files cleaner.

DEFAULT_TEAMS = {
    'team_alpha_default': {'id': 'team_alpha_default', 'name': 'Team Alpha', 'color': '#ff4b4b', 'trait': 'Aggressive'},
    'team_beta_default': {'id': 'team_beta_default', 'name': 'Team Beta', 'color': '#4b4bff', 'trait': 'Defensive'}
}

ACTION_DESCRIPTIONS = {
    'expand_add': "Add Line", 'expand_extend': "Extend Line", 'expand_grow': "Grow Vine", 'expand_fracture': "Fracture Line", 'expand_spawn': "Spawn Point",
    'expand_orbital': "Create Orbital",
    'fight_attack': "Attack Line", 'fight_convert': "Convert Point", 'fight_pincer_attack': "Pincer Attack", 'fight_territory_strike': "Territory Strike", 'fight_bastion_pulse': "Bastion Pulse", 'fight_sentry_zap': "Sentry Zap", 'fight_chain_lightning': "Chain Lightning", 'fight_refraction_beam': "Refraction Beam", 'fight_launch_payload': "Launch Payload", 'fight_purify_territory': "Purify Territory", 'fight_isolate_point': "Isolate Point",
    'fortify_claim': "Claim Territory", 'fortify_anchor': "Create Anchor", 'fortify_mirror': "Mirror Structure", 'fortify_form_bastion': "Form Bastion", 'fortify_form_monolith': "Form Monolith", 'fortify_form_purifier': "Form Purifier", 'fortify_cultivate_heartwood': "Cultivate Heartwood", 'fortify_form_rift_spire': "Form Rift Spire", 'terraform_create_fissure': "Create Fissure", 'fortify_build_wonder': "Build Wonder", 'fortify_reposition_point': "Reposition Point",
    'fortify_shield': "Shield Line / Overcharge", 'fortify_attune_nexus': "Attune Nexus", 'fortify_create_ley_line': "Create Ley Line",
    'sacrifice_nova': "Nova Burst", 'sacrifice_whirlpool': "Create Whirlpool", 'sacrifice_phase_shift': "Phase Shift", 'sacrifice_rift_trap': "Create Rift Trap", 'sacrifice_scorch_territory': "Scorch Territory",
    'rune_shoot_bisector': "Rune: V-Beam", 'rune_area_shield': "Rune: Area Shield", 'rune_shield_pulse': "Rune: Shield Pulse", 'rune_impale': "Rune: Impale", 'rune_hourglass_stasis': "Rune: Time Stasis", 'rune_starlight_cascade': "Rune: Starlight Cascade", 'rune_focus_beam': "Rune: Focus Beam", 'rune_cardinal_pulse': "Rune: Cardinal Pulse", 'rune_parallel_discharge': "Rune: Parallel Discharge", 'rune_t_hammer_slam': "Rune: T-Hammer Slam",
    'terraform_raise_barricade': "Raise Barricade"
}

ACTION_VERBOSE_DESCRIPTIONS = {
    'expand_add': "Connects two of the team's points with a new line. If no more lines can be drawn, it strengthens an existing line instead.",
    'expand_extend': "Extends a line between two points outwards to the grid border, creating a new point there. If no valid extensions are possible, it strengthens an existing line.",
    'expand_grow': "Grows a new, short line segment from an existing point at an angle. If it fails, it strengthens an existing line.",
    'expand_fracture': "Splits a long line into two smaller lines by creating a new point in the middle. If no lines are long enough, it strengthens one.",
    'expand_spawn': "Creates a new point in a random empty space near an existing friendly point. If no valid space is found, it strengthens a line.",
    'expand_orbital': "Creates a constellation of 3-5 new 'satellite' points in a circle around an existing point. If it fails, it reinforces all lines connected to the chosen center.",
    'fight_attack': "Extends a line outwards. If it intersects an enemy line, the enemy line is destroyed. If it misses, a new point is created on the border.",
    'fight_convert': "Sacrifices a friendly line to convert the nearest vulnerable enemy point to its team. If no target is in range, it creates a repulsive pulse that pushes enemies away.",
    'fight_pincer_attack': "Two friendly points flank and destroy a vulnerable enemy point between them. If no target is found, they form a temporary defensive barricade instead.",
    'fight_territory_strike': "Launches an attack from the center of a large claimed territory, destroying the nearest vulnerable enemy point. If no targets exist, it reinforces its own territory's borders.",
    'fight_bastion_pulse': "An active Bastion sacrifices one of its outer points to destroy all enemy lines crossing its perimeter. If the action fizzles, it creates a local shockwave.",
    'fight_sentry_zap': "An I-Rune (Sentry) fires a precise beam that destroys the first enemy point it hits. If it misses, it creates a new point on the border.",
    'fight_chain_lightning': "An I-Rune (Conduit) sacrifices an internal point to destroy the nearest enemy point. If it fizzles, the point explodes in a mini-nova, destroying nearby lines.",
    'fight_refraction_beam': "A Prism structure is used to 'bank' an attack shot. A beam is fired, reflects off the Prism's edge, and destroys the first enemy line it then hits. If it misses, it creates a point on the border.",
    'fight_launch_payload': "A Trebuchet structure launches a projectile to destroy a high-value enemy point (e.g., a fortified point). If none exist, it targets a regular point. If no targets exist, it creates a fissure.",
    'fight_purify_territory': "A Purifier structure neutralizes the nearest enemy territory, removing its fortified status. If no enemy territories exist, it pushes nearby enemy points away.",
    'fortify_create_ley_line': "Activates an I-Rune into a powerful Ley Line for several turns. When new friendly points are created near the Ley Line, they are automatically connected to it with a new line for free. If all I-Runes are already active, it pulses one Ley Line to strengthen all connected lines instead.",
    'fortify_attune_nexus': "Sacrifices a diagonal line from one of its Nexuses to supercharge it. For several turns, the Attuned Nexus energizes all nearby friendly lines, causing their attacks to also destroy the target line's endpoints.",
    'fortify_claim': "Forms a triangle of three points and their connecting lines into a claimed territory, making its points immune to conversion. If no new triangles can be formed, it reinforces an existing territory.",
    'fortify_anchor': "Sacrifices one point to turn another into a gravitational anchor, which pulls nearby enemy points towards it for several turns.",
    'fortify_mirror': "Creates a symmetrical structure by reflecting some of its points across an axis defined by two other points. If it fails, it reinforces the structure it was trying to mirror.",
    'fortify_reposition_point': "Moves a single 'free' (non-structural) point to a better tactical position nearby. A subtle but important move for setting up future formations. If it fails, a line is strengthened instead.",
    'fortify_form_bastion': "Converts a fortified point and its connections into a powerful defensive bastion, making its components immune to standard attacks. If not possible, it reinforces a key defensive point.",
    'fortify_form_monolith': "Forms a tall, thin rectangle of points into a Monolith. Every few turns, the Monolith emits a wave that strengthens nearby friendly lines.",
    'fortify_form_purifier': "Forms a regular pentagon of points into a Purifier, which unlocks the 'Purify Territory' action.",
    'fortify_cultivate_heartwood': "A unique action where a central point and at least 5 connected 'branch' points are sacrificed to create a Heartwood. The Heartwood passively generates new points and prevents enemy spawns nearby.",
    'fortify_form_rift_spire': "Sacrifices a point that is a vertex of 3 or more territories to create a Rift Spire. The Spire charges up to unlock the 'Create Fissure' action.",
    'fortify_build_wonder': "A rare action requiring a Star-Rune formation. Sacrifices the entire formation to build the Chronos Spire, an indestructible structure that provides a victory countdown.",
    'terraform_create_fissure': "A charged Rift Spire creates a temporary, impassable fissure across the map that blocks line-based actions.",
    'terraform_raise_barricade': "A Barricade-Rune is consumed to create a temporary, impassable wall that blocks line-based actions.",
    'sacrifice_nova': "Sacrifices a point to destroy all nearby enemy lines. If no lines are in range, it creates a shockwave that pushes all points away.",
    'sacrifice_whirlpool': "Sacrifices a point to create a vortex that pulls all nearby points towards its center for several turns. If no points are nearby on creation, it creates a small fissure instead.",
    'sacrifice_phase_shift': "Sacrifices a line to teleport one of its endpoints to a random new location. If it fails, the other endpoint becomes a temporary gravitational anchor.",
    'sacrifice_rift_trap': "Sacrifices a point to lay a temporary, invisible trap. If an enemy point enters its radius, the trap destroys it. If untriggered, it collapses into a new friendly point.",
    'sacrifice_scorch_territory': "Sacrifices an entire claimed territory, destroying its points and lines to render the triangular area impassable and unbuildable for several turns.",
    'fortify_shield': "Applies a temporary shield to a line, making it immune to one standard attack. If all lines are shielded, it overcharges an existing shield to extend its duration.",
    'rune_shoot_bisector': "A V-Rune fires a powerful beam along its bisector, destroying the first enemy line it hits. If it misses, it creates a fissure.",
    'rune_area_shield': "A Shield-Rune protects all friendly lines inside its triangular boundary with temporary shields. If no lines are found inside, it instead pushes friendly points out to de-clutter.",
    'rune_shield_pulse': "A Shield-Rune emits a shockwave, pushing all nearby enemy points away. If no enemies are in range, it gently pulls friendly points in.",
    'rune_impale': "A Trident-Rune fires a devastating beam that destroys ALL enemy lines in its path, piercing shields and monolith strength. If it misses, it creates a temporary barricade.",
    'rune_hourglass_stasis': "An Hourglass-Rune freezes a nearby enemy point in time for several turns, making it immune but unable to be used. If no target is found, it creates an anchor.",
    'rune_starlight_cascade': "A Star-Rune sacrifices one of its outer points to damage or destroy all nearby unshielded enemy lines.",
    'rune_focus_beam': "A Star-Rune fires a beam from its center to destroy a high-value enemy structure (like a Wonder or Bastion core). If none exist, it targets a regular point. If no targets exist, it creates a fissure.",
    'rune_cardinal_pulse': "A Plus-Rune is consumed to fire four beams from its center. Beams destroy the first enemy line hit and create a new point on the border if they miss.",
    'rune_parallel_discharge': "A Parallelogram-Rune destroys all enemy lines crossing its interior. If none, it creates a new central structure inside itself.",
    'rune_t_hammer_slam': "A T-Rune sacrifices its 'head' point to create a shockwave along its 'stem', pushing all nearby points away perpendicularly. If no points are hit, it reinforces its own stem lines."
}