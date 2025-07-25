## Team Traits
When a team is created, it is assigned a trait which influences its behavior. The default "Random" option will assign one of the following traits upon game start.

*   **Aggressive:** Prefers to attack enemy lines and use high-risk actions.
*   **Expansive:** Focuses on creating new points and lines to cover more ground.
*   **Defensive:** Favors fortifying territory and protecting its existing lines.
*   **Balanced:** Has no strong preference for any particular type of action.

## Runes
Runes are special geometric formations that grant a team passive bonuses or unlock powerful new actions. They are checked at the start of a team's turn.

*   **I-Rune (Line Rune):**
    *   **Formation:** Three or more of a team's points are collinear and connected sequentially by lines.
    *   **Bonus 1 (Passive):** Empowers the `Extend Line` action when it originates from one of the I-Rune's two endpoints. Empowered extensions automatically create a new line to the new point.
    *   **Bonus 2 (Active):** Unlocks the `Sentry Zap` action.
    *   **Bonus 3 (Active):** Unlocks the `Chain Lightning` action.
*   **V-Rune:**
    *   **Formation:** Three points forming a 'V' shape, where two connected lines originating from the same point are of similar length.
    *   **Bonus:** Unlocks the **[RUNE] Shoot Bisector** action, a powerful, long-range attack fired from the 'V's vertex.
*   **Shield-Rune:**
    *   **Formation:** Three points connected by lines to form a triangle, with a fourth friendly point located inside the triangle.
    *   **Bonus 1:** Unlocks the **[RUNE] Area Shield** action.
    *   **Bonus 2:** Unlocks the **[RUNE] Shield Pulse** action.
*   **Cross-Rune:**
    *   **Formation:** Four points that form a rectangle, with both internal diagonals existing as lines for that team.
    *   **Bonus:** Grants the `Piercing Attacks` passive. The team's standard `Attack Line` action can now bypass one enemy shield.
*   **Plus-Rune (+):**
    *   **Formation:** Five points forming a '+' shape, where a central point is connected to four other points that form two perpendicular, straight lines.
    *   **Bonus:** Unlocks the **[RUNE] Cardinal Pulse** action. This is a powerful, one-use sacrificial action.
*   **T-Rune:**
    *   **Formation:** Four points in a 'T' shape. It requires a central point connected to three other points, where two of the connections form a straight line (the stem) and the third is perpendicular to it (the head). All three connecting lines must exist.
    *   **Bonus:** Unlocks the **[RUNE] T-Hammer Slam** action.
*   **Trident-Rune:**
    *   **Formation:** Four points forming a "trident" or "pitchfork" shape. This requires an isosceles triangle and a fourth "handle" point extending from the apex along the line of symmetry. All three connecting lines must exist.
    *   **Bonus:** Unlocks the **[RUNE] Impale** action.
*   **Hourglass-Rune:**
    *   **Formation:** Five points forming two distinct triangles that share a single, common vertex point. All six lines required to form the two triangles must exist.
    *   **Bonus:** Unlocks the **[RUNE] Time Stasis** action.
*   **Barricade-Rune:**
    *   **Formation:** Four points that form a rectangle, with all four of its sides existing as connected lines.
    *   **Bonus:** Unlocks the **[TERRAFORM] Raise Barricade** action.
*   **Parallelogram-Rune:**
    *   **Formation:** Four points that form a non-rectangular parallelogram, with all four of its sides existing as connected lines.
    *   **Bonus:** Unlocks the **[RUNE] Parallel Discharge** action.

## Actions
On its turn, a team will perform one of the following actions, with the choice being influenced by its trait.

*   **[EXPAND] Add Line:** Connect two of its own points with a new line. If not possible, it will reinforce an existing friendly line.
*   **[EXPAND] Extend Line:** Extend an existing line to the border of the grid, creating a new point. If no valid extensions can be found, it reinforces an existing friendly line.
*   **[EXPAND] Bisect Angle:** Finds a point with at least two connected lines (a 'V' shape) and creates a new point along the angle's bisector, also connecting it to the vertex. If it fails, it reinforces one of the lines forming the angle.
*   **[EXPAND] Fracture Line:** Splits an existing line into two, creating a new point along the line's original path. If no lines are long enough to fracture, it reinforces an existing friendly line.
*   **[EXPAND] Spawn Point:** Creates a new point near an existing one. If it cannot find a valid position, it reinforces an existing friendly line instead.
*   **[EXPAND] Mirror Point:** Reflects a friendly point through another friendly point to create a new symmetrical point. If no valid reflection is found, it strengthens the line between them (if it exists).
*   **[EXPAND] Create Orbital:** Creates a constellation of 3-5 new "satellite" points in a circle around one of its existing points. If no valid formation can be made, it instead reinforces all lines connected to the chosen center point.
*   **[FIGHT] Attack Line:** Extend an existing line. If it hits an enemy team's line, the enemy line is destroyed. If it misses, it creates a new friendly point on the border.
*   **[FIGHT] Pincer Attack:** If two of a team's points are flanking a single enemy point (creating a wide angle), they can perform a joint attack to destroy it. This does not work on fortified or bastion points. If no suitable target is found, the points instead form a small, temporary barricade between them.
*   **[FIGHT] Territory Strike:** _(Requires a large territory)_ Launches a bolt of energy from the center of a large claimed territory, destroying the nearest vulnerable enemy point. This makes controlling large areas of the map an offensive advantage. If no vulnerable enemies exist, the territory's boundary lines are reinforced instead.
*   **[FIGHT] Territory Tri-Beam:** _(Requires a claimed territory)_ A claimed territory fires three beams of energy along the bisectors of its angles. Each beam destroys the first enemy line it hits. If a beam misses, it creates a new point on the border.
*   **[FIGHT] Convert Point:** Sacrifice one of its own lines to convert the nearest enemy point to its team, if it's within range. If no target is found, it instead emits a repulsive pulse from the sacrifice location, pushing nearby enemies away.
*   **[SACRIFICE] Nova Burst:** Sacrifice one of its own points to destroy all nearby enemy lines in a radius. If no enemy lines are in range, it pushes all nearby points away instead.
*   **[SACRIFICE] Create Whirlpool:** Sacrifices a point to create a vortex that pulls nearby points toward its center. If no points are nearby when created, the action instead creates a small, temporary fissure on the map.
*   **[SACRIFICE] Create Rift Trap:** Sacrifices a point to create a temporary, invisible trap. If an enemy point moves into its small radius, the trap triggers, destroying the enemy point and itself. If the trap is not triggered after a few turns, it safely collapses and transforms into a new point for its owner.
*   **[SACRIFICE] Phase Shift:** Sacrifices a line to instantly "teleport" one of the line's endpoints to a new random location. If a valid new location cannot be found, the energy implodes into the *other* endpoint, turning it into a temporary **gravitational anchor** that pulls in nearby enemies.
*   **[FIGHT] Bastion Pulse:** _(Requires an active Bastion)_ Sacrifices one of the bastion's outer "prong" points to unleash a shockwave that destroys all enemy lines crossing the bastion's perimeter. If the pulse fizzles (e.g., the bastion dissolves upon sacrifice), the sacrificed point instead releases a **local shockwave**, pushing all nearby points away.
*   **[FIGHT] Sentry Zap:** _(Requires an active I-Rune)_ Fires a short, high-energy beam from an internal point of an I-Rune along its perpendicular axis. Destroys the first enemy **point** it hits within range. This is a powerful, precision attack capable of removing fortified points. If the beam misses, it creates a new point for the team where it hits the border.
*   **[FIGHT] Chain Lightning:** _(Requires an I-Rune with internal points)_ Sacrifices one of the I-Rune's internal points to fire a bolt of energy at the nearest enemy point, destroying it. If the attack fizzles (e.g., no target in range), the sacrificed point explodes in a **mini-nova**, destroying any nearby enemy lines.
*   **[FIGHT] Refraction Beam:** _(Requires an active Prism)_ Fires a beam from one of its lines that refracts off the Prism's shared edge, changing direction to hit an enemy line around obstacles. If the refracted beam misses, it creates a new friendly point where it hits the border.
*   **[FIGHT] Launch Payload:** _(Requires an active Trebuchet)_ Fires an arcing projectile. It prioritizes destroying a random enemy high-value point (e.g., a fortified point, bastion core, or monolith point). If none exist, it targets any vulnerable enemy point. If there are no targets at all, the payload impacts a random spot on the battlefield, creating a small, temporary fissure.
*   **[FIGHT] Purify Territory:** _(Requires an active Purifier)_ The Purifier unleashes a wave of energy at the nearest enemy territory, instantly neutralizing it. If there are no enemy territories to cleanse, it instead emits a defensive pulse that pushes all nearby enemy points away from it.
*   **[FIGHT] Isolate Point:** Sacrifices a line to isolate a critical enemy connection point (an articulation point), making it vulnerable to collapse over time. If no such point is found, it creates a defensive barricade instead.
*   **[FIGHT] Parallel Strike:** From a friendly point, projects a beam parallel to a friendly line. Destroys the first enemy point it hits, or creates a new point on the border if it misses.
*   **[RUNE] Cardinal Pulse:** _(Requires an active Plus-Rune)_ The rune is consumed. Four energy beams are fired from the central point through the four arm points. Beams destroy the first enemy line they hit (bypassing shields). Any beam that misses creates a new point on the border.
*   **[RUNE] Parallel Discharge:** _(Requires an active Parallelogram-Rune)_ Destroys all enemy lines crossing the interior of the parallelogram. If no lines are hit, it creates a new central structure of two points and a line inside the rune instead.
*   **[RUNE] T-Hammer Slam:** _(Requires an active T-Rune)_ The rune sacrifices its 'head' point to create a shockwave emanating from its 'stem' line, pushing all nearby points away perpendicularly. If no points are in range, it instead reinforces the two lines that form the stem.
*   **[RUNE] Shoot Bisector:** _(Requires an active V-Rune)_ Fires a powerful beam from a 'V' formation, destroying the first enemy line it hits. If it misses, it creates a temporary fissure along its path.
*   **[RUNE] Impale:** _(Requires an active Trident-Rune)_ Fires a devastating, long-range beam that pierces through all enemy lines in its path, ignoring shields. If the beam hits no targets, it instead creates a temporary defensive barricade along its path.
*   **[RUNE] Area Shield:** _(Requires an active Shield-Rune)_ Creates a temporary shield on all friendly lines contained within the rune's triangular boundary. If no lines are found inside, it instead emits a gentle pulse that pushes friendly points outwards to de-clutter the area.
*   **[RUNE] Shield Pulse:** _(Requires an active Shield-Rune)_ Emits a defensive shockwave from the rune's center, pushing all nearby enemy points outwards. If no enemies are in range, it instead gently pulls nearby friendly points inwards to consolidate the formation.
*   **[RUNE] Starlight Cascade:** _(Requires a Star-Rune)_ Sacrifices one of the outer cycle points to damage or destroy nearby unshielded/unfortified enemy lines in a small radius.
*   **[RUNE] Focus Beam:** _(Requires a Star-Rune)_ Fires a beam from the central point to destroy a high-value enemy structure (Wonder, Bastion core, etc). If no high-value targets exist, it targets a regular point. If no targets exist at all, it creates a small fissure in the heart of the enemy's territory.
*   **[RUNE] Time Stasis:** _(Requires an active Hourglass-Rune)_ The rune targets a nearby enemy point and freezes it in a **Stasis** field. If no valid targets are in range, it instead sacrifices one of its own points to turn another of its rune-points into a temporary gravitational **anchor**.
*   **[FORTIFY] Attune Nexus:** Sacrifices a diagonal line from one of its Nexuses to supercharge it. For several turns, the Attuned Nexus energizes all nearby friendly lines, causing their attacks to also destroy the target line's endpoints.
*   **[FORTIFY] Shield Line:** Applies a temporary shield to one of its lines. If all lines are already shielded, it will instead **overcharge** an existing shield, extending its duration.
*   **[DEFEND] Form Prism:** A passive formation. A Prism is created when two of a team's claimed territories (triangles) share a common edge line.
    *   **Bonus:** Unlocks the **[FIGHT] Refraction Beam** action, which allows for powerful bank-shot attacks.
*   **[DEFEND] Form Nexus:** A passive formation. A Nexus is a powerful economic structure that grants bonus actions.
    *   **Formation:** Four points that form a perfect square, with all four outer edge lines and at least one of the two inner diagonals connected.
    *   **Bonus:** For each Nexus a team controls at the start of a turn, that team gains **one bonus action** to perform during that turn.
*   **[FORTIFY] Claim Territory:** If three points and their connecting lines form a triangle, the team can claim that triangle as its territory. If no new triangles can be formed, it will instead reinforce the boundary lines of an existing friendly territory.
    *   **Bonus:** The three points of a claimed territory become **Fortified**, making them immune to conversion. The three boundary lines become **Reinforced** and cannot be fractured by their owner, preserving the structure.
*   **[FORTIFY] Form Bastion:** Converts a fortified point (a vertex of a claimed territory) and at least three of its connected, non-fortified points into a powerful defensive structure. If no valid formation can be found, it instead reinforces all lines connected to the team's most-connected fortified point.
    *   **Bonus:** The bastion's core point, prong points, and connecting lines become immune to standard attacks and conversion.
*   **[FORTIFY] Form Monolith:** Forms a special defensive structure from four points that create a tall, thin rectangle with its perimeter lines connected. If no valid formation is found, it will instead reinforce the boundary lines of any existing rectangular structure.
    *   **Bonus (Resonance Wave):** Every few turns, the Monolith emits a wave that **Empowers** all friendly lines in a radius around it. Empowered lines can absorb one or more hits before being destroyed.
*   **[FORTIFY] Form Purifier:** A high-level strategic structure for countering area-control strategies.
    *   **Formation:** Requires five points to form a perfect, regular pentagon, with all 5 outer lines connected. This is a difficult and resource-intensive shape to create.
    *   **Bonus:** Unlocks the **[FIGHT] Purify Territory** action.
*   **[FORTIFY] Form Trebuchet:** Forms a powerful siege engine from a kite-shaped formation of four points.
    *   **Formation:** Requires a tight, isosceles triangle (the "base") connected to a "counterweight" point along its axis of symmetry. All 5 lines that form the outer kite shape must exist.
    *   **Bonus:** Unlocks the **[FIGHT] Launch Payload** action.
*   **[FORTIFY] Create Anchor:** Sacrifice one of its own points to turn another into a gravitational anchor. For a few turns, the anchor will slowly pull nearby enemy points towards it.
*   **[FORTIFY] Mirror Structure:** Selects two of its points to form an axis, then reflects some of its other points across this axis to create new points, forming symmetrical patterns. If no valid reflections can be found, it instead reinforces the lines of the structure it was attempting to mirror.
*   **[FORTIFY] Reposition Point:** Moves a single 'free' (non-structural) point to a better tactical position nearby. A subtle but important move for setting up future formations. If it fails, a line is strengthened instead.
*   **[FORTIFY] Cultivate Heartwood:** A unique, powerful structure. Requires a central point connected to at least 5 other "branch" points.
    *   **Cost:** The central point and all branch points are sacrificed. This action can only be performed once per team.
    *   **Bonus 1 (Passive Growth):** Every few turns, the Heartwood automatically creates a new point for its team nearby.
    *   **Bonus 2 (Defensive Aura):** Prevents enemy points from being created in a large radius around it.
*   **[FORTIFY] Form Rift Spire:** Sacrifices a point that serves as a vertex for at least three different claimed territories.
    *   **Bonus:** Creates a **Rift Spire**. This structure takes several turns to charge. Once charged, it unlocks the **[TERRAFORM] Create Fissure** action.
*   **[TERRAFORM] Raise Barricade:** _(Requires an active Barricade-Rune)_ Consumes the rune to create a temporary, impassable wall along the rune's central axis. The wall blocks line-based actions for several turns, offering a flexible way to control the battlefield.
*   **[TERRAFORM] Create Fissure:** _(Requires a charged Rift Spire)_ The spire opens a temporary, impassable fissure across the battlefield.
    *   **Effect:** The fissure is a line on the grid that blocks most actions. No points can be created near it, and line-based actions (like `Attack Line` or `Extend Line`) cannot cross it. It decays after a number of turns.

## Wonders
Wonders are unique, game-changing structures that require immense investment and provide a path to an alternative victory. Only one Wonder can be controlled by each team.

*   **Star-Rune:**
    *   **Formation:** A central point connected to a cycle of 5 or 6 other points, where the cycle points are also connected to each other sequentially. All required lines must exist.
    *   **Bonus 1:** Unlocks the **[RUNE] Starlight Cascade** action.
    *   **Bonus 2:** Unlocks the **[RUNE] Focus Beam** action.
    *   **Bonus 3:** This formation is a prerequisite for building the **Chronos Spire** wonder.
    *   **Cost:** The central point and all points in the cycle are sacrificed to create the Spire.
    *   **Bonus 1 (Temporal Distortion):** The Spire grants its owner **one bonus action** every turn. This stacks with other sources of bonus actions like Nexuses.
    *   **Bonus 2 (Victory Countdown):** The Spire is indestructible. If it remains on the field for **10 turns** after its creation, its owner immediately wins the game.