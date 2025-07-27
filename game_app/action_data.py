# game_app/action_data.py
from . import game_data
from .geometry import polygon_area

"""
A single source of truth for all action metadata in the game.
Each action is defined by a unique key and a dictionary containing:
- group: The action category (e.g., 'Expand', 'Fight').
- handler: The name of the handler attribute in the Game class.
- method: The method name within the handler class to call.
- display_name: The short, user-facing name for the action.
- description: A longer, verbose description for the action guide.
- precondition: A lambda function `(handler, teamId) -> (bool, str)` that checks if the action is valid.
- log_generators: A dictionary mapping result 'type' strings to functions
                  that generate the long and short log messages for that result.
"""

ACTIONS = {
    # --- EXPAND ACTIONS ---
    'expand_add': {
        'group': 'Expand', 'handler': 'expand_handler', 'method': 'add_line',
        'display_name': 'Add Line',
        'description': "Connects two of the team's points with a new line. If no more lines can be drawn, it strengthens an existing line instead.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_point_ids(tid)) >= 2
            else (False, "Requires at least 2 points.")
        ),
        'log_generators': {
            'add_line': lambda r: ("connected two points.", "[+LINE]"),
            'add_line_fizzle_strengthen': lambda r: ("could not add a new line, and instead reinforced an existing one.", "[ADD->REINFORCE]"),
        }
    },
    'expand_extend': {
        'group': 'Expand', 'handler': 'expand_handler', 'method': 'extend_line',
        'display_name': 'Extend Line',
        'description': "Extends a line between two points outwards to the grid border, creating a new point there. Can be empowered by an I-Rune to also create a line to the new point. If no valid extensions are possible, it strengthens an existing line.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_lines(tid)) > 0
            else (False, "No lines to extend or strengthen.")
        ),
        'log_generators': {
            'extend_line': lambda r: (
                f"extended a line to the border, creating a new point{' with an empowered Conduit extension!' if r.get('is_empowered') else '.'}",
                "[RAY!]" if r.get('is_empowered') else "[EXTEND]"
            ),
            'extend_fizzle_strengthen': lambda r: ("tried to extend a line but couldn't, so it reinforced an existing line instead.", "[EXTEND->REINFORCE]"),
        }
    },
    'expand_bisect_angle': {
        'group': 'Expand', 'handler': 'expand_handler', 'method': 'bisect_angle',
        'display_name': 'Bisect Angle',
        'description': "Finds a vertex point with two connected lines ('V' shape) and creates a new point along the angle's bisector. If it fails, it strengthens one of the angle's lines.",
        'precondition': lambda h, tid: (
            (False, "Requires at least 3 points to form an angle.") if len(h.game.query.get_team_point_ids(tid)) < 3
            else (True, "") if any(d >= 2 for d in h.game.query.get_team_degrees(tid).values()) or h.game.query.get_team_lines(tid)
            else (False, "No angles to bisect and no lines to strengthen.")
        ),
        'log_generators': {
            'bisect_angle': lambda r: ("bisected an angle, creating a new point.", "[BISECT]"),
            'bisect_fizzle_strengthen': lambda r: ("failed to bisect an angle and instead reinforced a line.", "[BISECT->REINFORCE]"),
        }
    },
    'expand_fracture': {
        'group': 'Expand', 'handler': 'expand_handler', 'method': 'fracture_line',
        'display_name': 'Fracture Line',
        'description': "Splits a long line into two smaller lines by creating a new point in the middle. If no lines are long enough, it strengthens one.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_lines(tid)) > 0
            else (False, "No lines to fracture or strengthen.")
        ),
        'log_generators': {
            'fracture_line': lambda r: ("fractured a line, creating a new point.", "[FRACTURE]"),
            'fracture_fizzle_strengthen': lambda r: ("could not find a line to fracture, and instead reinforced one.", "[FRACTURE->REINFORCE]"),
        }
    },
    'expand_spawn': {
        'group': 'Expand', 'handler': 'expand_handler', 'method': 'spawn_point',
        'display_name': 'Spawn Point',
        'description': "Creates a new point in a random empty space near an existing friendly point. If it fails, it strengthens a line, and if that also fails, it creates a new point on the border.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_point_ids(tid)) > 0
            else (False, "Requires at least one point to spawn from.")
        ),
        'log_generators': {
            'spawn_point': lambda r: ("spawned a new point from an existing one.", "[SPAWN]"),
            'spawn_fizzle_strengthen': lambda r: ("could not find a place to spawn a new point, and instead reinforced an existing line.", "[SPAWN->REINFORCE]"),
            'spawn_fizzle_border_spawn': lambda r: ("had no other option and projected its energy to the border, creating a new point.", "[SPAWN->BORDER]"),
        }
    },
    'expand_mirror_point': {
        'group': 'Expand', 'handler': 'expand_handler', 'method': 'mirror_point',
        'display_name': 'Mirror Point',
        'description': "Reflects a friendly point through another friendly point to create a new symmetrical point. If no valid reflection is found, it attempts to strengthen the line between a pair of points, or any random line as a final fallback.",
        'precondition': lambda h, tid: (
            (
                (True, "") if len(h.game.query.get_team_point_ids(tid)) >= 2 or len(h.game.query.get_team_lines(tid)) > 0
                else (False, "Requires at least 2 points to mirror or a line to strengthen.")
            )
        ),
        'log_generators': {
            'mirror_point': lambda r: (f"mirrored a point through another, creating a new point.", "[MIRROR PT]"),
            'mirror_point_fizzle_strengthen': lambda r: ("could not find a valid reflection and instead reinforced a line.", "[MIRROR PT->REINFORCE]"),
        }
    },
    'expand_orbital': {
        'group': 'Expand', 'handler': 'expand_handler', 'method': 'create_orbital',
        'display_name': 'Create Orbital',
        'description': "Creates a constellation of 3-5 new 'satellite' points in a circle around an existing point. If it fails, it reinforces all lines connected to the chosen center.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_point_ids(tid)) >= 1
            else (False, "Requires at least one point to be the center of an orbital.")
        ),
        'log_generators': {
            'create_orbital': lambda r: (f"created an orbital structure with {len(r['new_points'])} new points.", "[ORBITAL]"),
            'orbital_fizzle_strengthen': lambda r: (f"failed to form an orbital and instead reinforced {len(r['strengthened_lines'])} lines around a central point.", "[ORBITAL->REINFORCE]"),
        }
    },

    # --- FIGHT ACTIONS ---
    'fight_attack': {
        'group': 'Fight', 'handler': 'fight_handler', 'method': 'attack_line',
        'display_name': 'Attack Line',
        'description': "Extends a line outwards. If it intersects an enemy line, the enemy line is destroyed. If it misses, a new point is created on the border.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_lines(tid)) > 0
            else (False, "Requires at least 1 line to attack from.")
        ),
        'log_generators': {
            'attack_line': lambda r: (
                f"attacked and destroyed a line from {r['destroyed_team']}{', bypassing its shield with a Cross Rune!' if r.get('bypassed_shield') else '.'}",
                "[PIERCE!]" if r.get('bypassed_shield') else "[ATTACK]"
            ),
            'attack_line_energized': lambda r: (f"unleashed an energized attack, obliterating a line and its {len(r['destroyed_points'])} endpoints from {r['destroyed_team']}.", "[OBLITERATE!]"),
            'attack_miss_spawn': lambda r: ("launched an attack that missed, but the energy coalesced into a new point on the border.", "[ATTACK->SPAWN]"),
            'attack_line_strengthened': lambda r: ("attacked a strengthened line, weakening its defenses.", "[DAMAGE]"),
        }
    },
    'fight_pincer_attack': {
        'group': 'Fight', 'handler': 'fight_handler', 'method': 'pincer_attack',
        'display_name': 'Pincer Attack',
        'description': "Two friendly points flank and destroy a vulnerable enemy point between them. If no target is found, two random friendly points form a temporary defensive barricade instead.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_point_ids(tid)) >= 2
            else (False, "Requires at least 2 points.")
        ),
        'log_generators': {
            'pincer_attack': lambda r: (f"executed a pincer attack, destroying a point from {r['destroyed_team_name']}.", "[PINCER!]"),
            'pincer_fizzle_barricade': lambda r: ("failed to find a pincer target and instead formed a temporary defensive barricade.", "[PINCER->WALL]"),
        }
    },
    'fight_territory_bisector_strike': {
        'group': 'Fight', 'handler': 'fight_handler', 'method': 'territory_bisector_strike',
        'display_name': 'Territory Tri-Beam',
        'description': "A claimed territory fires three beams of energy along the bisectors of its angles. Each beam destroys the first enemy line it hits. If a beam misses, it creates a new point on the border.",
        'precondition': lambda h, tid: (
            (True, "") if any(t['teamId'] == tid for t in h.state.get('territories', []))
            else (False, "No claimed territories available.")
        ),
        'log_generators': {
            'territory_bisector_strike': lambda r: (f"unleashed a Tri-Beam from a territory, destroying {len(r['destroyed_lines'])} lines and creating {len(r['created_points'])} points.", "[TRI-BEAM!]"),
            'territory_bisector_strike_fizzle': lambda r: ("attempted a Tri-Beam strike but all paths were blocked, and instead reinforced its territory.", "[TRI-BEAM->REINFORCE]"),
        }
    },
    'fight_territory_strike': {
        'group': 'Fight', 'handler': 'fight_handler', 'method': 'territory_strike',
        'display_name': 'Territory Strike',
        'description': "Launches an attack from the center of a large claimed territory, destroying the nearest vulnerable enemy point. If no targets exist, it reinforces its own territory's borders.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_large_territories(tid)) > 0
            else (False, "No large territories available.")
        ),
        'log_generators': {
            'territory_strike': lambda r: (f"launched a strike from its territory, destroying a point from {r['destroyed_team_name']}.", "[TERRITORY!]"),
            'territory_fizzle_reinforce': lambda r: ("could not find a target for a territory strike, and instead reinforced its own boundaries.", "[TERRITORY->REINFORCE]"),
        }
    },
    'fight_sentry_zap': {
        'group': 'Fight', 'handler': 'fight_handler', 'method': 'sentry_zap',
        'display_name': 'Sentry Zap',
        'description': "An I-Rune (Sentry) fires a precise beam that destroys the first enemy point it hits. If it misses, it creates a new point on the border.",
        'precondition': lambda h, tid: (
            (True, "") if any(r.get('internal_points') for r in h.state.get('runes', {}).get(tid, {}).get('i_shape', []))
            else (False, "Requires an I-Rune with at least 3 points.")
        ),
        'log_generators': {
            'sentry_zap': lambda r: (f"fired a precision shot from a Sentry, obliterating a point from {r['destroyed_team_name']}.", "[ZAP!]"),
            'sentry_zap_miss_spawn': lambda r: ("a Sentry fired a beam that missed all targets, creating a new point on the border.", "[ZAP->SPAWN]"),
            'sentry_zap_fizzle_strengthen': lambda r: ("a Sentry's zap was blocked, and it reinforced its own structure instead.", "[ZAP->REINFORCE]"),
        }
    },
    'fight_refraction_beam': {
        'group': 'Fight', 'handler': 'fight_handler', 'method': 'refraction_beam',
        'display_name': 'Refraction Beam',
        'description': "A Prism structure is used to 'bank' an attack shot. A beam is fired, reflects off the Prism's edge, and destroys the first enemy line it then hits. If it misses, it creates a point on the border.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('prism', [])) and (len(h.state['lines']) - len(h.game.query.get_team_lines(tid)) > 0)
            else (False, "Requires a Prism Rune and enemy lines.")
        ),
        'log_generators': {
            'refraction_beam': lambda r: ("fired a refracted beam from a Prism, destroying an enemy line.", "[REFRACT!]"),
            'refraction_miss_spawn': lambda r: ("fired a refracted beam from a Prism that missed, creating a new point on the border.", "[REFRACT->SPAWN]"),
            'refraction_fizzle_strengthen': lambda r: ("failed to find a target for a refracted beam, and instead reinforced its Prism structure.", "[REFRACT->REINFORCE]"),
        }
    },
    'fight_launch_payload': {
        'group': 'Fight', 'handler': 'fight_handler', 'method': 'launch_payload',
        'display_name': 'Launch Payload',
        'description': "A Trebuchet structure launches a projectile to destroy a high-value enemy point (e.g., a fortified point). If none exist, it targets a regular point. If no targets exist, it creates a fissure.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('trebuchet', []))
            else (False, "Requires a Trebuchet Rune.")
        ),
        'log_generators': {
            'launch_payload': lambda r: (f"launched a payload from a Trebuchet, obliterating a fortified point from {r['destroyed_team_name']}.", "[TREBUCHET!]"),
            'launch_payload_fallback_hit': lambda r: (f"found no high-value targets and instead launched a payload from a Trebuchet at a standard point from {r['destroyed_team_name']}.", "[TREBUCHET]"),
            'launch_payload_fizzle_fissure': lambda r: ("found no enemy targets and instead launched a payload from a Trebuchet that impacted the battlefield, creating a temporary fissure.", "[TREBUCHET->FIZZLE]"),
        }
    },
    'fight_purify_territory': {
        'group': 'Fight', 'handler': 'fight_handler', 'method': 'purify_territory',
        'display_name': 'Purify Territory', 'no_cost': True,
        'description': "A Purifier structure neutralizes the nearest enemy territory, removing it from play and un-fortifying its points. If no enemy territories exist, it pushes nearby enemy points away. This action has no cost.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('purifiers', {}).get(tid, []))
            else (False, "Requires a Purifier.")
        ),
        'log_generators': {
            'purify_territory': lambda r: (f"unleashed its Purifier, cleansing a territory from {r['cleansed_team_name']}.", "[PURIFY!]"),
            'purify_fizzle_push': lambda r: (f"found no territories to cleanse, and instead emitted a pulse that pushed back {r['pushed_points_count']} enemies.", "[PURIFY->PUSH]"),
        }
    },
    'fight_isolate_point': {
        'group': 'Fight', 'handler': 'fight_handler', 'method': 'isolate_point',
        'display_name': 'Isolate Point', 'no_cost': True,
        'description': "Projects an isolation field onto a critical enemy connection point (an articulation point), making it vulnerable to collapse over time. This action has no cost. If no such point is found, it creates a defensive barricade (with 2+ points) or a weak repulsive pulse (with 1 point).",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_point_ids(tid)) >= 1
            else (False, "Requires at least one point to act.")
        ),
        'log_generators': {
            'isolate_point': lambda r: (f"isolated a critical point from {r['target_team_name']}", "[ISOLATE!]"),
            'isolate_fizzle_barricade': lambda r: ("failed to find a critical enemy point to isolate and instead formed a defensive barricade.", "[ISOLATE->WALL]"),
            'isolate_fizzle_push': lambda r: (f"failed to find a target to isolate and instead emitted a weak pulse, pushing back {r['pushed_points_count']} enemies.", "[ISOLATE->PUSH]"),
        }
    },
    'fight_parallel_strike': {
        'group': 'Fight', 'handler': 'fight_handler', 'method': 'parallel_strike',
        'display_name': 'Parallel Strike',
        'description': "From a friendly point, projects a beam parallel to a friendly line. Destroys the first enemy point it hits, or creates a new point on the border if it misses.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_lines(tid)) > 0 and len(h.game.query.get_team_point_ids(tid)) > 2
            else (False, "Requires at least one line and at least 3 points in total.")
        ),
        'log_generators': {
            'parallel_strike_hit': lambda r: (f"executed a parallel strike, destroying a point from {r['destroyed_team_name']}.", "[PARALLEL!]"),
            'parallel_strike_miss': lambda r: ("launched a parallel strike that missed, creating a new point on the border.", "[PARALLEL->SPAWN]"),
        }
    },
    'fight_hull_breach': {
        'group': 'Fight', 'handler': 'fight_handler', 'method': 'hull_breach',
        'display_name': 'Hull Breach',
        'description': "Projects the team's convex hull as an energy field, converting the most central enemy point found inside. If no enemy points are inside, it creates or reinforces the hull's boundary lines. If the hull is already fully reinforced, it emits a weak pulse that pushes nearby enemies away.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_point_ids(tid)) >= 3
            else (False, "Requires at least 3 points to form a hull.")
        ),
        'log_generators': {
            'hull_breach_convert': lambda r: (f"breached its hull, converting a point from {r['original_team_name']}.", "[BREACH!]"),
            'hull_breach_fizzle_reinforce': lambda r: (f"found no enemy points within its hull and instead fortified its boundary lines.", "[BREACH->FORTIFY]"),
            'hull_breach_fizzle_push': lambda r: (f"found no hull targets and instead emitted a pulse that pushed back {r['pushed_points_count']} enemies.", "[BREACH->PUSH]"),
        }
    },
    
    # --- FORTIFY ACTIONS ---
    'fortify_shield': {
        'group': 'Fortify', 'handler': 'fortify_handler', 'method': 'shield_line', 'no_cost': True,
        'display_name': 'Shield Line / Overcharge',
        'description': "Applies a temporary shield to a line, making it immune to one standard attack. If all lines are shielded, it overcharges an existing shield to extend its duration. This action has no cost.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_lines(tid)) > 0
            else (False, "Requires at least one line to shield or overcharge.")
        ),
        'log_generators': {
            'shield_line': lambda r: ("raised a defensive shield on one of its lines.", "[SHIELD]"),
            'shield_overcharge': lambda r: (f"could not shield a new line, and instead overcharged an existing shield to last for {r['new_duration']} turns.", "[OVERCHARGE]"),
        }
    },
    'fortify_claim': {
        'group': 'Fortify', 'handler': 'fortify_handler', 'method': 'claim_territory',
        'display_name': 'Claim Territory',
        'description': "Forms a triangle of three points and their connecting lines into a claimed territory, making its points immune to conversion. If no new triangles can be formed, it reinforces an existing territory.",
        'precondition': lambda h, tid: (
            (True, "") if (len(h.game.query.get_team_point_ids(tid)) >= 3 and len(h.game.query.get_team_lines(tid)) >= 3) or any(t['teamId'] == tid for t in h.state.get('territories', []))
            else (False, "Requires at least 3 points and 3 lines to claim, or an existing territory to reinforce.")
        ),
        'log_generators': {
            'claim_territory': lambda r: ("fortified its position, claiming new territory.", "[CLAIM]"),
            'claim_fizzle_reinforce': lambda r: ("could not find a new territory to claim, and instead reinforced an existing one.", "[CLAIM->REINFORCE]"),
        }
    },
    'fortify_anchor': {
        'group': 'Fortify', 'handler': 'fortify_handler', 'method': 'create_anchor',
        'display_name': 'Create Anchor', 'no_cost': True,
        'description': "Turns a non-critical point into a gravitational anchor, which pulls nearby enemy points towards it for several turns. This action has no cost.",
        'precondition': lambda h, tid: (lambda pids:
            ( (False, "Requires at least one point.") if not pids
            else (True, "") if any(
                pid not in h.game.query.get_critical_structure_point_ids(tid) and
                pid not in h.state.get('anchors', {})
                for pid in pids
            )
            else (False, "No available non-critical points to turn into an anchor.") )
        )(h.game.query.get_team_point_ids(tid)),
        'log_generators': {
            'create_anchor': lambda r: ("turned one of its points into a gravitational anchor.", "[ANCHOR]"),
        }
    },
    'fortify_mirror_structure': {
        'group': 'Fortify', 'handler': 'fortify_handler', 'method': 'mirror_structure',
        'display_name': 'Mirror Structure',
        'description': "Creates a symmetrical structure by reflecting some of its points across an axis defined by two other points. If it fails, it reinforces several existing lines around random points. If that also fails, it adds a new line as a last resort.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_point_ids(tid)) >= 2 or len(h.game.query.get_team_lines(tid)) > 0
            else (False, "Requires at least 2 points or 1 line.")
        ),
        'log_generators': {
            'mirror_structure': lambda r: (f"mirrored its structure, creating {len(r['new_points'])} new points.", "[MIRROR]"),
            'mirror_structure_fizzle_strengthen': lambda r: (f"attempted to mirror its structure, but instead reinforced {len(r['strengthened_lines'])} connected lines.", "[MIRROR->REINFORCE]"),
            'mirror_structure_fizzle_add_line': lambda r: ("failed to mirror or reinforce, and instead drew a new line as a last resort.", "[MIRROR->LINE]"),
        }
    },
    'fortify_form_bastion': {
        'group': 'Fortify', 'handler': 'fortify_handler', 'method': 'form_bastion',
        'display_name': 'Form Bastion',
        'description': "Converts a fortified point and its connections into a powerful defensive bastion, making its components immune to standard attacks. If not possible, it reinforces a key defensive point.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.find_possible_bastions(tid)) > 0 or bool(h.game.query.get_fortified_point_ids().intersection(h.game.query.get_team_point_ids(tid)))
            else (False, "No valid bastion formation and no fortified points to reinforce.")
        ),
        'log_generators': {
            'form_bastion': lambda r: ("consolidated its power, forming a new bastion.", "[BASTION!]"),
            'bastion_fizzle_reinforce': lambda r: (f"failed to form a Bastion and instead reinforced {len(r['strengthened_lines'])} lines around a key defensive point.", "[BASTION->REINFORCE]"),
        }
    },
    'fortify_form_monolith': {
        'group': 'Fortify', 'handler': 'fortify_handler', 'method': 'form_monolith',
        'display_name': 'Form Monolith',
        'description': "Forms a tall, thin rectangle of points into a Monolith. Every few turns, the Monolith emits a wave that strengthens nearby friendly lines.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_point_ids(tid)) >= 4
            else (False, "Requires at least 4 points to form a rectangle.")
        ),
        'log_generators': {
            'form_monolith': lambda r: ("erected a resonant Monolith from a pillar of light.", "[MONOLITH]"),
            'monolith_fizzle_reinforce': lambda r: (f"failed to form a Monolith and instead reinforced the {len(r['strengthened_lines'])} lines of a potential structure.", "[MONOLITH->REINFORCE]"),
        }
    },
    'fortify_form_purifier': {
        'group': 'Fortify', 'handler': 'fortify_handler', 'method': 'form_purifier',
        'display_name': 'Form Purifier',
        'description': "Forms a regular pentagon of points into a Purifier, which unlocks the 'Purify Territory' action. If no valid formation is found, it reinforces the lines between a cluster of five points instead.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_point_ids(tid)) >= 5
            else (False, "Requires at least 5 points to form a pentagon.")
        ),
        'log_generators': {
            'form_purifier': lambda r: ("aligned its points to form a territory Purifier.", "[PURIFIER]"),
            'purifier_fizzle_reinforce': lambda r: (f"failed to form a Purifier and instead reinforced {len(r['strengthened_lines'])} lines of a potential structure.", "[PURIFIER->REINFORCE]"),
        }
    },
    'fortify_reposition_point': {
        'group': 'Fortify', 'handler': 'fortify_handler', 'method': 'reposition_point',
        'display_name': 'Reposition Point', 'no_cost': True,
        'description': "Moves a single 'free' (non-structural) point to a better tactical position nearby. A subtle but important move for setting up future formations. This action has no cost and will fail if no point can be moved.",
        'precondition': lambda h, tid: (
            (True, "") if h.game.query.find_repositionable_point(tid)
            else (False, "No free points to reposition.")
        ),
        'log_generators': {
            'reposition_point': lambda r: ("subtly repositioned a point for a better tactical advantage.", "[REPOSITION]"),
            'reposition_fizzle': lambda r: ("attempted to reposition a point, but no valid move could be found.", "[REPOSITION->FIZZLE]"),
        }
    },
    'fortify_rotate_point': {
        'group': 'Fortify', 'handler': 'fortify_handler', 'method': 'rotate_point',
        'display_name': 'Rotate Point', 'no_cost': True,
        'description': "Rotates a single 'free' (non-structural) point around the grid center or another friendly point. This action has no cost and will fail if no valid rotation can be found.",
        'precondition': lambda h, tid: (
            (True, "") if h.game.query.find_repositionable_point(tid)
            else (False, "No free points to rotate.")
        ),
        'log_generators': {
            'rotate_point': lambda r: (f"rotated a point around {'the grid center.' if r.get('is_grid_center') else 'another point.'}", "[ROTATE]"),
            'rotate_fizzle': lambda r: ("attempted to rotate a point, but no valid move could be found.", "[ROTATE->FIZZLE]"),
        }
    },
    'fortify_create_ley_line': {
        'group': 'Fortify', 'handler': 'fortify_handler', 'method': 'create_ley_line', 'no_cost': True,
        'display_name': 'Create Ley Line',
        'description': "Activates an I-Rune into a powerful Ley Line for several turns. When new friendly points are created near the Ley Line, they are automatically connected to it with a new line for free. If all I-Runes are already active, it pulses one Ley Line to strengthen all connected lines instead. This action has no cost.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('i_shape', []))
            else (False, "Requires an I-Rune (a line of 3+ points).")
        ),
        'log_generators': {
            'create_ley_line': lambda r: ("activated an I-Rune, creating a powerful Ley Line.", "[LEY LINE!]"),
            'ley_line_pulse': lambda r: ("could not create a new Ley Line, and instead pulsed an existing one, strengthening nearby lines.", "[LEY LINE->PULSE]"),
        }
    },
    
    # --- SACRIFICE ACTIONS ---
    'sacrifice_nova': {
        'group': 'Sacrifice', 'handler': 'sacrifice_handler', 'method': 'nova_burst',
        'display_name': 'Nova Burst',
        'description': "Sacrifices a point to destroy all nearby enemy lines. If no lines are in range, it creates a shockwave that pushes all points away.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.find_possible_nova_bursts(tid)) > 0 or h.game.query.has_sacrificial_point(tid)
            else (False, "No suitable point to sacrifice for Nova Burst.")
        ),
        'log_generators': {
            'nova_burst': lambda r: (f"sacrificed a point in a nova burst, destroying {r['lines_destroyed']} lines.", "[NOVA]"),
            'nova_shockwave': lambda r: (f"sacrificed a point in a shockwave, pushing back {r['pushed_points_count']} nearby points.", "[SHOCKWAVE]"),
        }
    },
    'sacrifice_whirlpool': {
        'group': 'Sacrifice', 'handler': 'sacrifice_handler', 'method': 'create_whirlpool',
        'display_name': 'Create Whirlpool',
        'description': "Sacrifices a point to create a vortex that pulls all nearby points towards its center for several turns. If no points are nearby on creation, it creates a small fissure instead.",
        'precondition': lambda h, tid: (
            (True, "") if h.game.query.has_sacrificial_point(tid)
            else (False, "No non-critical point available to sacrifice.")
        ),
        'log_generators': {
            'create_whirlpool': lambda r: ("sacrificed a point to create a chaotic whirlpool.", "[WHIRLPOOL!]"),
            'whirlpool_fizzle_fissure': lambda r: ("sacrificed a point to open a whirlpool, but with no targets in range, it collapsed into a temporary fissure.", "[WHIRLPOOL->FIZZLE]"),
        }
    },
    'sacrifice_phase_shift': {
        'group': 'Sacrifice', 'handler': 'sacrifice_handler', 'method': 'phase_shift',
        'display_name': 'Phase Shift',
        'description': "Sacrifices a line to instantly 'teleport' one of the line's endpoints to a new random location. If it fails, the other endpoint becomes a temporary gravitational anchor.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_eligible_phase_shift_lines(tid)) > 0
            else (False, "Requires a non-critical/safe line to sacrifice.")
        ),
        'log_generators': {
            'phase_shift': lambda r: ("sacrificed a line to phase shift a point to a new location.", "[PHASE!]"),
            'phase_shift_fizzle_anchor': lambda r: (f"attempted to phase shift a point but failed, instead causing the residual energy to form a temporary gravitational anchor.", "[PHASE->ANCHOR]"),
        }
    },
    'sacrifice_rift_trap': {
        'group': 'Sacrifice', 'handler': 'sacrifice_handler', 'method': 'rift_trap',
        'display_name': 'Create Rift Trap',
        'description': "Sacrifices a point to lay a temporary, invisible trap. If an enemy point enters its radius, the trap destroys it. If untriggered, it collapses into a new friendly point.",
        'precondition': lambda h, tid: (
            (True, "") if h.game.query.has_sacrificial_point(tid)
            else (False, "No non-critical point available to sacrifice.")
        ),
        'log_generators': {
            'create_rift_trap': lambda r: ("sacrificed a point to lay a latent Rift Trap.", "[TRAP SET]"),
        }
    },
    'sacrifice_scorch_territory': {
        'group': 'Sacrifice', 'handler': 'sacrifice_handler', 'method': 'scorch_territory',
        'display_name': 'Scorch Territory',
        'description': "Sacrifices an entire claimed territory, destroying its points and lines to render the triangular area impassable and unbuildable for several turns.",
        'precondition': lambda h, tid: (
            (True, "") if any(t['teamId'] == tid for t in h.state.get('territories', []))
            else (False, "Requires at least one claimed territory to sacrifice.")
        ),
        'log_generators': {
            'scorch_territory': lambda r: (f"sacrificed a territory, scorching the earth and making it impassable.", "[SCORCHED!]"),
        }
    },
    'sacrifice_convert_point': {
        'group': 'Sacrifice', 'handler': 'sacrifice_handler', 'method': 'convert_point',
        'display_name': 'Convert Point',
        'description': "Sacrifices a friendly line to convert the nearest vulnerable enemy point to its team. If no target is in range, it creates a repulsive pulse that pushes enemies away.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_team_lines(tid)) > 0
            else (False, "Requires a line to sacrifice.")
        ),
        'log_generators': {
            'convert_point': lambda r: (f"sacrificed a line to convert a point from {r['original_team_name']}.", "[CONVERT]"),
            'convert_fizzle_push': lambda r: (f"attempted to convert a point but found no targets, instead unleashing a pulse that pushed back {r['pushed_points_count']} enemies.", "[CONVERT->PUSH]"),
        }
    },
    'sacrifice_line_retaliation': {
        'group': 'Sacrifice', 'handler': 'sacrifice_handler', 'method': 'line_retaliation',
        'display_name': 'Line Retaliation',
        'description': "Sacrifices a point on a line to unleash two projectiles from the line's former position. One continues along the line's path, the other fires perpendicularly. Each projectile destroys the first enemy line it hits, or creates a new point on the border if it misses.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.get_eligible_phase_shift_lines(tid)) > 0
            else (False, "Requires a non-critical line to sacrifice.")
        ),
        'log_generators': {
            'line_retaliation': lambda r: (f"sacrificed a point on a line, unleashing two projectiles that destroyed {len(r['destroyed_lines'])} lines and created {len(r['created_points'])} points.", "[RETALIATION!]"),
            'line_retaliation_fizzle': lambda r: ("attempted a line retaliation, but both projectiles were blocked.", "[RETALIATION->FIZZLE]"),
        }
    },
    'sacrifice_bastion_pulse': {
        'group': 'Sacrifice', 'handler': 'sacrifice_handler', 'method': 'bastion_pulse',
        'display_name': 'Bastion Pulse',
        'description': "An active Bastion sacrifices one of its outer points to destroy all enemy lines crossing its perimeter. If the action fizzles, it creates a local shockwave.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.find_possible_bastion_pulses(tid)) > 0
            else (False, "No bastion with enemy lines crossing its perimeter.")
        ),
        'log_generators': {
            'bastion_pulse': lambda r: (f"unleashed a defensive pulse from its bastion, destroying {len(r['lines_destroyed'])} lines.", "[PULSE!]"),
            'bastion_pulse_fizzle_shockwave': lambda r: (f"attempted a bastion pulse that fizzled, instead creating a shockwave that pushed {r['pushed_points_count']} points.", "[PULSE->FIZZLE]"),
        }
    },
    'sacrifice_chain_lightning': {
        'group': 'Sacrifice', 'handler': 'sacrifice_handler', 'method': 'chain_lightning',
        'display_name': 'Chain Lightning',
        'description': "An I-Rune (Conduit) sacrifices an internal point to destroy the nearest enemy point. If it fizzles, the point explodes in a mini-nova, destroying nearby lines.",
        'precondition': lambda h, tid: (
            (True, "") if any(
                pid in h.state['points'] 
                for r in h.state.get('runes', {}).get(tid, {}).get('i_shape', []) 
                for pid in r.get('internal_points', [])
            )
            else (False, "Requires an I-Rune (Conduit) with a sacrificial internal point.")
        ),
        'log_generators': {
            'chain_lightning': lambda r: (f"unleashed Chain Lightning from a Conduit, destroying a point from {r['destroyed_team_name']}.", "[LIGHTNING!]"),
            'chain_lightning_fizzle_nova': lambda r: (f"attempted to use Chain Lightning which fizzled, instead unleashing a mini-nova that destroyed {r['lines_destroyed_count']} lines.", "[LIGHTNING->NOVA]"),
        }
    },
    'sacrifice_cultivate_heartwood': {
        'group': 'Sacrifice', 'handler': 'sacrifice_handler', 'method': 'cultivate_heartwood',
        'display_name': 'Cultivate Heartwood',
        'description': "A unique action where a central point and at least 5 connected 'branch' points are sacrificed to create a Heartwood. The Heartwood passively generates new points and prevents enemy spawns nearby.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.find_heartwood_candidates(tid)) > 0
            else (False, "Requires a central point connected to at least 5 other points, and team cannot have an existing Heartwood.")
        ),
        'log_generators': {
            'cultivate_heartwood': lambda r: (f"sacrificed {len(r['sacrificed_points'])} points to cultivate a mighty Heartwood.", "[HEARTWOOD!]"),
        }
    },

    'sacrifice_build_wonder': {
        'group': 'Sacrifice', 'handler': 'sacrifice_handler', 'method': 'build_chronos_spire',
        'display_name': 'Build Wonder',
        'description': "A rare action requiring a Star-Rune formation. Sacrifices the entire formation to build the Chronos Spire, an indestructible structure that provides a victory countdown.",
        'precondition': lambda h, tid: (
            (False, "Team already has a Wonder.") if any(w['teamId'] == tid for w in h.state.get('wonders', {}).values())
            else (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('star', []))
            else (False, "Requires an active Star Rune to build a Wonder.")
        ),
        'log_generators': {
            'build_chronos_spire': lambda r: (f"sacrificed {r['sacrificed_points_count']} points to construct the Chronos Spire, a path to victory!", "[WONDER!]"),
        }
    },
    'sacrifice_attune_nexus': {
        'group': 'Sacrifice', 'handler': 'sacrifice_handler', 'method': 'attune_nexus',
        'display_name': 'Attune Nexus',
        'description': "Sacrifices a diagonal line from one of its Nexuses to supercharge it. For several turns, the Attuned Nexus energizes all nearby friendly lines, causing their attacks to also destroy the target line's endpoints.",
        'precondition': lambda h, tid: (
            lambda nexuses: (
                (False, "Requires an active Nexus Rune.") if not nexuses
                else (lambda attuned_pids:
                    (True, "") if any(frozenset(n.get('point_ids', [])) not in attuned_pids for n in nexuses)
                    else (False, "All active Nexuses are already attuned.")
                )({frozenset(an['point_ids']) for an in h.state.get('attuned_nexuses', {}).values()})
            )(h.state.get('runes', {}).get(tid, {}).get('nexus', []))
        ),
        'log_generators': {
            'attune_nexus': lambda r: ("attuned a Nexus, sacrificing a line to energize its surroundings.", "[ATTUNED!]"),
        }
    },

    
    # --- TERRAFORM ACTIONS ---
    'terraform_form_rift_spire': {
        'group': 'Terraform', 'handler': 'terraform_handler', 'method': 'form_rift_spire',
        'display_name': 'Form Rift Spire', 'no_cost': True,
        'description': "At a point that is a vertex of 3 or more territories, erects a Rift Spire. The Spire charges up to unlock the 'Create Fissure' action. This action costs no points.",
        'precondition': lambda h, tid: (
            (True, "") if len(h.game.query.find_rift_spire_candidates(tid)) > 0
            else (False, "Requires a point that is a vertex of at least 3 territories.")
        ),
        'log_generators': {
            'form_rift_spire': lambda r: ("erected a Rift Spire at a territorial nexus.", "[RIFT SPIRE!]"),
        }
    },
    'terraform_create_fissure': {
        'group': 'Terraform', 'handler': 'terraform_handler', 'method': 'create_fissure', 'no_cost': True,
        'display_name': 'Create Fissure',
        'description': "A charged Rift Spire creates a temporary, impassable fissure across the map that blocks line-based actions. This action has no cost.",
        'precondition': lambda h, tid: (
            (True, "") if any(
                s['teamId'] == tid and s.get('charge', 0) >= s.get('charge_needed', 3) 
                for s in h.state.get('rift_spires', {}).values()
            ) else (False, "Requires a charged Rift Spire.")
        ),
        'log_generators': {
            'create_fissure': lambda r: (f"unleashed the power of a Rift Spire, tearing a fissure across the battlefield.", "[FISSURE!]"),
        }
    },

    # --- RUNE ACTIONS ---
    'rune_shoot_bisector': {
        'group': 'Rune', 'handler': 'rune_handler', 'method': 'shoot_bisector',
        'display_name': 'Rune: V-Beam',
        'description': "A V-Rune fires a powerful beam along its bisector, destroying the first enemy line it hits. If it misses, it creates a fissure.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('v_shape', []))
            else (False, "Requires an active V-Rune.")
        ),
        'log_generators': {
            'rune_shoot_bisector': lambda r: ("unleashed a powerful beam from a V-Rune, destroying an enemy line.", "[V-BEAM!]"),
            'vbeam_miss_fissure': lambda r: ("unleashed a V-Rune beam that missed, scarring the earth with a temporary fissure.", "[V-BEAM->FISSURE]"),
            'vbeam_fizzle_strengthen': lambda r: ("a V-Rune's beam was blocked, so it reinforced its own structure instead.", "[V-BEAM->REINFORCE]"),
        }
    },
    'rune_area_shield': {
        'group': 'Rune', 'handler': 'rune_handler', 'method': 'area_shield',
        'display_name': 'Rune: Area Shield', 'no_cost': True,
        'description': "A Shield-Rune protects all friendly lines inside its triangular boundary with temporary shields. If no lines are found inside, it instead pushes friendly points out to de-clutter. This action has no cost.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('shield', []))
            else (False, "Requires an active Shield Rune.")
        ),
        'log_generators': {
            'rune_area_shield': lambda r: (f"activated a Shield Rune, protecting {r['shielded_lines_count']} lines within its boundary.", "[AEGIS!]"),
            'area_shield_fizzle_push': lambda r: (f"activated a Shield Rune with no lines to protect, instead pushing {r['pushed_points_count']} friendly points to de-clutter.", "[AEGIS->PUSH]"),
        }
    },
    'rune_shield_pulse': {
        'group': 'Rune', 'handler': 'rune_handler', 'method': 'shield_pulse',
        'display_name': 'Rune: Shield Pulse', 'no_cost': True,
        'description': "A Shield-Rune emits a shockwave, pushing all nearby enemy points away. If no enemies are in range, it gently pulls friendly points in. This action has no cost.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('shield', []))
            else (False, "Requires an active Shield Rune.")
        ),
        'log_generators': {
            'rune_shield_pulse': lambda r: (f"unleashed a shockwave from a Shield Rune, pushing back {r['pushed_points_count']} enemy points.", "[PULSE!]"),
            'shield_pulse_fizzle_pull': lambda r: (f"unleashed a shockwave from a Shield Rune with no enemies in range, instead pulling in {len(r['pulled_points'])} friendly points to consolidate.", "[PULSE->PULL]"),
        }
    },
    'rune_impale': {
        'group': 'Rune', 'handler': 'rune_handler', 'method': 'impale',
        'display_name': 'Rune: Impale',
        'description': "A Trident-Rune fires a devastating beam that destroys ALL enemy lines in its path, piercing shields and monolith strength. If it misses, it creates a temporary barricade.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('trident', []))
            else (False, "Requires an active Trident Rune.")
        ),
        'log_generators': {
            'rune_impale': lambda r: (f"fired a piercing blast from a Trident Rune, destroying {len(r['destroyed_lines'])} lines.", "[IMPALE!]"),
            'impale_fizzle_barricade': lambda r: ("fired a Trident blast that missed all targets, creating a temporary barricade in its wake.", "[IMPALE->WALL]"),
        }
    },
    'rune_hourglass_stasis': {
        'group': 'Rune', 'handler': 'rune_handler', 'method': 'hourglass_stasis', 'no_cost': True,
        'display_name': 'Rune: Time Stasis',
        'description': "An Hourglass-Rune freezes a nearby enemy point in time for several turns, making it immune but unable to be used. If no target is found, it creates an anchor. This action has no cost.",
        'precondition': lambda h, tid: (
            lambda runes: (
                (False, "Requires an active Hourglass Rune.") if not runes
                else (True, "") if h.game.query.get_vulnerable_enemy_points(tid)
                else (True, "") if any(
                    pid != r.get('vertex_id') and pid not in h.state.get('anchors', {})
                    for r in runes for pid in r.get('all_points', [])
                ) else (False, "Requires a valid target or a point to convert to an anchor.")
            )(h.state.get('runes', {}).get(tid, {}).get('hourglass', []))
        ),
        'log_generators': {
            'rune_hourglass_stasis': lambda r: (f"used an Hourglass Rune to freeze a point from {r['target_team_name']} in time.", "[STASIS!]"),
            'hourglass_fizzle_anchor': lambda r: ("failed to find a target for Time Stasis, and instead converted one of the rune's points into a temporary anchor.", "[STASIS->ANCHOR]"),
        }
    },
    'rune_focus_beam': {
        'group': 'Rune', 'handler': 'rune_handler', 'method': 'focus_beam',
        'display_name': 'Rune: Focus Beam',
        'description': "A Star-Rune fires a beam from its center to destroy a high-value enemy structure (like a Wonder or Bastion core). If none exist, it targets a regular point. If no targets exist at all, it creates a fissure.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('star', [])) and (len(h.state['points']) - len(h.game.query.get_team_point_ids(tid)) > 0)
            else (False, "Requires a Star Rune and an enemy point.")
        ),
        'log_generators': {
            'rune_focus_beam': lambda r: (f"fired a focused beam from a Star Rune, destroying a high-value point from {r['destroyed_team_name']}.", "[FOCUS BEAM!]"),
            'focus_beam_fallback_hit': lambda r: (f"found no high-value structures and instead used its Focus Beam to destroy a standard point from {r['destroyed_team_name']}.", "[FOCUS BEAM]"),
            'focus_beam_fizzle_fissure': lambda r: ("found no targets for its Focus Beam and instead scarred the enemy's heartland with a temporary fissure.", "[FOCUS->FIZZLE]"),
        }
    },
    'rune_starlight_cascade': {
        'group': 'Rune', 'handler': 'rune_handler', 'method': 'starlight_cascade',
        'display_name': 'Rune: Starlight Cascade',
        'description': "A Star-Rune unleashes a cascade of energy from its center, damaging or destroying all nearby unshielded enemy lines.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('star', []))
            else (False, "Requires an active Star Rune.")
        ),
        'log_generators': {
            'rune_starlight_cascade': lambda r: (f"unleashed a Starlight Cascade from a Star Rune, destroying {len(r['destroyed_lines'])} enemy lines and damaging {len(r['damaged_lines'])} others.", "[CASCADE!]"),
            'rune_starlight_cascade_fizzle': lambda r: ("unleashed a Starlight Cascade from a Star Rune, but found no targets in range.", "[CASCADE->FIZZLE]"),
        }
    },
    'rune_gravity_well': {
        'group': 'Rune', 'handler': 'rune_handler', 'method': 'gravity_well',
        'display_name': 'Rune: Gravity Well', 'no_cost': True,
        'description': "A Star-Rune creates a powerful gravitational field, pushing all non-friendly points away from its center. If no points are in range, it gently pulls friendly points towards its center to consolidate.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('star', []))
            else (False, "Requires an active Star Rune.")
        ),
        'log_generators': {
            'rune_gravity_well_push': lambda r: (f"unleashed a gravity well from a Star Rune, pushing back {r['pushed_points_count']} non-friendly points.", "[GRAV WELL!]"),
            'gravity_well_fizzle_pull': lambda r: (f"activated a Star Rune's gravity well with no targets, and instead pulled in {r['pulled_points_count']} friendly points.", "[GRAV WELL->PULL]"),
        }
    },
    'rune_parallel_discharge': {
        'group': 'Rune', 'handler': 'rune_handler', 'method': 'parallel_discharge',
        'display_name': 'Rune: Parallel Discharge',
        'description': "A Parallelogram-Rune destroys all enemy lines crossing its interior. If none, it creates a new central structure inside itself.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('parallel', []))
            else (False, "Requires an active Parallelogram Rune.")
        ),
        'log_generators': {
            'parallel_discharge': lambda r: (f"unleashed a Parallel Discharge, cleansing its interior of {len(r['lines_destroyed'])} enemy lines.", "[DISCHARGE!]"),
            'parallel_discharge_fizzle_spawn': lambda r: ("unleashed a Parallel Discharge that found no targets, and instead created a new structure at its center.", "[DISCHARGE->SPAWN]"),
        }
    },
    'rune_t_hammer_slam': {
        'group': 'Rune', 'handler': 'rune_handler', 'method': 't_hammer_slam',
        'display_name': 'Rune: T-Hammer Slam', 'no_cost': True,
        'description': "A T-Rune creates a shockwave along its 'stem', pushing all nearby points away perpendicularly from the stem line. If no points are hit, it reinforces its own stem lines. This action has no cost.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('t_shape', []))
            else (False, "Requires an active T-Rune.")
        ),
        'log_generators': {
            'rune_t_hammer_slam': lambda r: (f"used a T-Rune to unleash a shockwave, pushing back {r['pushed_points_count']} points.", "[HAMMER!]"),
            't_slam_fizzle_reinforce': lambda r: ("attempted a T-Hammer Slam that found no targets, and instead reinforced the rune's own structure.", "[HAMMER->REINFORCE]"),
        }
    },
    'rune_cardinal_pulse': {
        'group': 'Rune', 'handler': 'rune_handler', 'method': 'cardinal_pulse',
        'display_name': 'Rune: Cardinal Pulse',
        'description': "A Plus-Rune fires four beams from its center through its arms. Beams destroy the first enemy line they hit and create a new point on the border if they miss.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('plus_shape', []))
            else (False, "Requires an active Plus-Rune.")
        ),
        'log_generators': {
            'rune_cardinal_pulse': lambda r: (f"unleashed a Cardinal Pulse from a Plus-Rune, destroying {len(r['lines_destroyed'])} lines and creating {len(r['points_created'])} new points.", "[CARDINAL PULSE!]"),
        }
    },
    'rune_raise_barricade': {
        'group': 'Rune', 'handler': 'rune_handler', 'method': 'raise_barricade',
        'display_name': 'Rune: Raise Barricade', 'no_cost': True,
        'description': "A Barricade-Rune creates a temporary, impassable wall along one of its diagonals. This action has no cost.",
        'precondition': lambda h, tid: (
            (True, "") if bool(h.state.get('runes', {}).get(tid, {}).get('barricade', []))
            else (False, "Requires an active Barricade-Rune.")
        ),
        'log_generators': {
            'raise_barricade': lambda r: ("activated a Barricade Rune to raise a defensive wall.", "[BARRICADE!]"),
            'raise_barricade_fizzle': lambda r: ("activated a Barricade Rune, but its geometry was unstable, failing to form a wall.", "[BARRICADE->FIZZLE]"),
        }
    },
}