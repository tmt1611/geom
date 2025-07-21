# Iteration Analysis and Changelog

## 1. Analysis Summary
This iteration introduces a new strategic element, the **Conduit**, to deepen gameplay and encourage new geometric formations. A Conduit is a passive structure formed by three or more collinear points, rewarding players for creating linear alignments. This addition provides both a passive buff to expansion and a powerful new offensive action, diversifying the available strategies beyond triangular and clustered formations.

The implementation involved adding backend logic to detect these new structures, creating a new "Chain Lightning" action, and enhancing an existing action (`Extend Line`) to benefit from the Conduit. On the frontend, new visualizations were created to clearly represent Conduits on the grid and to provide a dynamic, visually appealing effect for the new Chain Lightning attack.

## 2. Key Changes

### 2.1. New Structure: The Conduit
- **Files**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`
- **Concept:** A new passive structure formed by 3 or more collinear points of the same team. Unlike Sentries, they do not require connecting lines.
- **Backend (`game_logic.py`):**
    - Added `conduits` to the game state.
    - Implemented `_update_conduits_for_team` to efficiently detect all collinear point sets for each team at the start of their turn.
    - **Empowered Extension**: The `expand_action_extend_line` was refactored. When an extension originates from a Conduit's endpoint, it is "empowered" and automatically creates a new line to the new point, forming a ray.
    - **New Action `[FIGHT] Chain Lightning`:** Implemented a new high-risk, high-reward action. A team can sacrifice an internal point of a Conduit to unleash a lightning strike that destroys a nearby enemy point.
    - Integrated the new action into the AI's decision-making process (`_choose_action_for_team`), weighted towards `Aggressive` teams.
- **Frontend (`static/js/main.js`):**
    - Added `drawConduits` to render a faint, translucent line connecting the endpoints of a Conduit, making the structure clearly visible.
    - Updated `drawPoints` to give points that are part of a Conduit a distinct visual glow.
    - Implemented a new "chain lightning" visual effect: a jagged, electrical line arcs along the Conduit's path, then jumps to the enemy target, culminating in a point explosion.
- **Documentation (`rules.md`):**
    - Updated the rules to explain the Conduit formation, the passive Empowered Extension bonus, and the new Chain Lightning action.

### 2.2. Small Refinements
- **File**: `game_logic.py`
    - Refactored `expand_action_extend_line` to be aware of the origin point of the extension, which was necessary for the Conduit's empower mechanic.
- **File**: `rules.md`
    - Removed a duplicated rule entry for `Shield Line`.