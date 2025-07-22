## Team Traits
When a team is created, it is assigned a trait which influences its behavior. The default "Random" option will assign one of the following traits upon game start.

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
*   **[FIGHT] Pincer Attack:** If two of a team's points are flanking a single enemy point (creating a wide angle), they can perform a joint attack to destroy it. This does not work on fortified or bastion points.
*   **[FIGHT] Convert Point:** Sacrifice one of its own lines to convert the nearest enemy point to its team, if it's within range.
*   **[SACRIFICE] Nova Burst:** Sacrifice one of its own points to destroy all nearby enemy lines in a radius.
*   **[SACRIFICE] Create Whirlpool:** Sacrifices one of its own points to create a chaotic vortex on the battlefield for a few turns. The whirlpool slowly pulls all nearby points (friendly and enemy) towards its center, disrupting formations.
*   **[SACRIFICE] Phase Shift:** Sacrifices one of its lines to instantly "teleport" one of the line's endpoints to a new random location on the grid. This is a chaotic and powerful repositioning tool that leaves stretched lines in its wake.
*   **[FIGHT] Bastion Pulse:** _(Requires an active Bastion)_ Sacrifices one of the bastion's outer "prong" points to unleash a shockwave. The shockwave destroys all enemy lines that cross the bastion's perimeter.
*   **[FIGHT] Sentry Zap:** _(Requires an active Sentry)_ Fires a short, high-energy beam from the Sentry's "eye" along its perpendicular axis. Destroys the first enemy **point** it hits within range. This is a powerful, precision attack capable of removing fortified points.
*   **[FIGHT] Chain Lightning:** _(Requires a Conduit with internal points)_ Sacrifice one of the Conduit's internal points. A bolt of energy travels along the Conduit and then jumps to the nearest enemy point, destroying it.
*   **[FIGHT] Refraction Beam:** _(Requires an active Prism)_ Fires a beam from one of its lines that refracts off the Prism's shared edge, changing direction to hit an enemy line around obstacles.
*   **[FIGHT] Launch Payload:** _(Requires an active Trebuchet)_ Fires an arcing projectile at a random enemy high-value point (e.g., a fortified point, bastion core, or monolith point), destroying it. This is a powerful siege attack for breaking down entrenched defenses.
*   **[RUNE] Shoot Bisector:** _(Requires an active V-Rune)_ Fires a powerful beam from a 'V' formation, destroying the first enemy line it hits.
*   **[DEFEND] Shield Line:** Apply a temporary shield to one of its lines, making it immune to attacks for a few turns.
*   **[DEFEND] Form Sentry:** A passive formation. When three of a team's points are collinear and connected by lines (forming Post-Eye-Post), they become a Sentry.
    *   **Bonus:** Unlocks the **[FIGHT] Sentry Zap** action.
*   **[DEFEND] Form Conduit:** A passive formation. When three or more of a team's points are collinear, they form a Conduit.
    *   **Bonus 1 (Passive):** `Extend Line` actions originating from one of the Conduit's two endpoints become **Empowered**, creating a new line to the new point automatically.
    *   **Bonus 2 (Active):** Unlocks the **[FIGHT] Chain Lightning** action.
*   **[DEFEND] Form Prism:** A passive formation. A Prism is created when two of a team's claimed territories (triangles) share a common edge line.
    *   **Bonus:** Unlocks the **[FIGHT] Refraction Beam** action, which allows for powerful bank-shot attacks.
*   **[DEFEND] Form Nexus:** A passive formation. A Nexus is a powerful economic structure that grants bonus actions.
    *   **Formation:** Four points that form a perfect square, with all four outer edge lines and at least one of the two inner diagonals connected.
    *   **Bonus:** For each Nexus a team controls at the start of a turn, that team gains **one bonus action** to perform during that turn.
*   **[FORTIFY] Fortify Territory:** If three points and their connecting lines form a triangle, the team can claim that triangle as its territory, shading the area in its color.
    *   **Bonus:** The three points of a claimed territory become **Fortified**, making them immune to conversion. The three boundary lines become **Reinforced** and cannot be fractured by their owner, preserving the structure.
*   **[FORTIFY] Form Bastion:** Converts a fortified point (a vertex of a claimed territory) and at least three of its connected, non-fortified points into a powerful defensive structure.
    *   **Bonus:** The bastion's core point, prong points, and connecting lines become immune to standard attacks and conversion.
*   **[FORTIFY] Form Monolith:** Forms a special defensive structure from four points that create a tall, thin rectangle with its perimeter lines connected.
    *   **Bonus (Resonance Wave):** Every few turns, the Monolith emits a wave that **Empowers** all friendly lines in a radius around it. Empowered lines can absorb one or more hits before being destroyed.
*   **[FORTIFY] Form Trebuchet:** Forms a powerful siege engine from a kite-shaped formation of four points.
    *   **Formation:** Requires a tight, isosceles triangle (the "base") connected to a "counterweight" point along its axis of symmetry. All 5 lines that form the outer kite shape must exist.
    *   **Bonus:** Unlocks the **[FIGHT] Launch Payload** action.
*   **[FORTIFY] Create Anchor:** Sacrifice one of its own points to turn another into a gravitational anchor. For a few turns, the anchor will slowly pull nearby enemy points towards it.
*   **[FORTIFY] Mirror Structure:** Selects two of its points to form an axis, then reflects some of its other points across this axis to create new points, forming symmetrical patterns.
*   **[FORTIFY] Cultivate Heartwood:** A unique, powerful structure. Requires a central point connected to at least 5 other "branch" points.
    *   **Cost:** The central point and all branch points are sacrificed. This action can only be performed once per team.
    *   **Bonus 1 (Passive Growth):** Every few turns, the Heartwood automatically creates a new point for its team nearby.
    *   **Bonus 2 (Defensive Aura):** Prevents enemy points from being created in a large radius around it.

## Wonders
Wonders are unique, game-changing structures that require immense investment and provide a path to an alternative victory. Only one Wonder can be controlled by each team.

*   **[WONDER] The Chronos Spire**
    *   **Formation:** Requires a "star" formation: a central point connected to a cycle of 5 or 6 other points, where the cycle points are also connected to each other sequentially. All involved points and lines must belong to the same team.
    *   **Cost:** The central point and all points in the cycle are sacrificed to create the Spire.
    *   **Bonus 1 (Temporal Distortion):** The Spire grants its owner **one bonus action** every turn. This stacks with other sources of bonus actions like Nexuses.
    *   **Bonus 2 (Victory Countdown):** The Spire is indestructible. If it remains on the field for **10 turns** after its creation, its owner immediately wins the game.