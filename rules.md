## Team Traits
When a team is created, it is assigned a random trait which influences its behavior.

*   **Aggressive:** Prefers to attack enemy lines and use high-risk actions.
*   **Expansive:** Focuses on creating new points and lines to cover more ground.
*   **Defensive:** Favors fortifying territory and protecting its existing lines.
*   **Balanced:** Has no strong preference for any particular type of action.

## Runes
Runes are special geometric formations that grant a team passive bonuses or unlock powerful new actions. They are checked at the start of a team's turn.

*   **V-Rune:**
    *   **Formation:** Three points forming a 'V' shape, where two connected lines originating from the same point are of similar length.
    *   **Bonus:** Unlocks the **[RUNE] Shoot Bisector** action, a powerful, long-range attack fired from the 'V's vertex.

*   **Cross-Rune:**
    *   **Formation:** Four points that form a rectangle, with both internal diagonals existing as lines for that team.
    *   **Bonus:** Grants the `Piercing Attacks` passive. The team's standard `Attack Line` action can now bypass one enemy shield.

## Actions
On its turn, a team will perform one of the following actions, with the choice being influenced by its trait.

*   **[EXPAND] Add Line:** Connect two of its own points with a new line.
*   **[EXPAND] Extend Line:** Extend an existing line to the border of the grid, creating a new point.
*   **[EXPAND] Grow Line (Vine):** Grow a new, short line segment from an existing point, creating organic, branching structures.
*   **[EXPAND] Fracture Line:** Splits an existing line into two, creating a new point along the line's original path. This helps create denser networks.
*   **[EXPAND] Spawn Point:** Creates a new point near an existing one. This is a last-resort action to ensure a team can recover even from a single point.
*   **[EXPAND] Create Orbital:** A rare action where a team with enough points creates a constellation of 3-5 new "satellite" points in a circle around one of its existing points.
*   **[FIGHT] Attack Line:** Extend an existing line. If it hits an enemy team's line, the enemy line is destroyed.
*   **[FIGHT] Convert Point:** Sacrifice one of its own lines to convert the nearest enemy point to its team, if it's within range.
*   **[FIGHT] Nova Burst:** Sacrifice one of its own points to destroy all nearby enemy lines in a radius.
*   **[FIGHT] Bastion Pulse:** _(Requires an active Bastion)_ Sacrifices one of the bastion's outer "prong" points to unleash a shockwave. The shockwave destroys all enemy lines that cross the bastion's perimeter.
*   **[RUNE] Shoot Bisector:** _(Requires an active V-Rune)_ Fires a powerful beam from a 'V' formation, destroying the first enemy line it hits.
*   **[DEFEND] Shield Line:** Apply a temporary shield to one of its lines, making it immune to attacks for a few turns.
*   **[DEFEND] Fortify Territory:** If three points and their connecting lines form a triangle, the team can claim that triangle as its territory, shading the area in its color.
    *   **Bonus:** The three points of a claimed territory become **Fortified**, making them immune to conversion. The three boundary lines become **Reinforced** and cannot be fractured by their owner, preserving the structure.
*   **[FORTIFY] Form Bastion:** Converts a fortified point (a vertex of a claimed territory) and at least three of its connected lines into a powerful defensive structure.
    *   **Bonus:** The bastion's core point, prong points, and connecting lines become immune to standard attacks and conversion.
*   **[FORTIFY] Create Anchor:** Sacrifice one of its own points to turn another into a gravitational anchor. For a few turns, the anchor will slowly pull nearby enemy points towards it.
*   **[FORTIFY] Mirror Structure:** Selects two of its points to form an axis, then reflects some of its other points across this axis to create new points, forming symmetrical patterns.