## Team Traits
When a team is created, it is assigned a trait which influences its behavior. The default "Random" option will assign one of the following traits upon game start.

*   **Aggressive:** Prefers to attack enemy lines and use high-risk actions.
*   **Expansive:** Focuses on creating new points and lines to cover more ground.
*   **Defensive:** Favors fortifying territory and protecting its existing lines.
*   **Balanced:** Has no strong preference for any particular type of action.

## Passive Formations & Runes
Runes are special geometric formations that grant a team passive bonuses or unlock powerful new actions. They are checked at the start of a team's turn.

*   **Passive Formation: Prism-Rune:** A Prism is created when two of a team's claimed territories (triangles) share a common edge line.
    *   **Unlocks:** **[FIGHT] Refraction Beam** action.
*   **Passive Formation: Nexus-Rune (Square):** A Nexus is a powerful economic structure that grants bonus actions.
    *   **Formation:** Four points that form a perfect square, with all four outer edge lines and at least one of the two inner diagonals connected.
    *   **Bonus:** For each Nexus a team controls at the start of a turn, that team gains **one bonus action**.
    *   **Unlocks:** **[SACRIFICE] Attune Nexus** action.

*   **I-Rune (Line Rune):** A line of 3 or more collinear points, connected sequentially. Also known as a Conduit or Sentry.
    *   **Passive Bonus:** Empowers the `Extend Line` action when it originates from one of the I-Rune's two endpoints. Empowered extensions automatically create a new line to the new point.
    *   **Unlocks:** **[FIGHT] Sentry Zap**, **[FORTIFY] Create Ley Line**, and **[SACRIFICE] Chain Lightning** actions.
*   **V-Rune:** Three points forming a 'V' shape, where two connected lines originating from the same point are of similar length.
    *   **Unlocks:** **[RUNE] Rune: V-Beam** action.
*   **Shield-Rune:** A triangle of three connected points with a fourth friendly point located inside.
    *   **Unlocks:** **[RUNE] Rune: Area Shield** and **[RUNE] Rune: Shield Pulse** actions.
*   **Cross-Rune:** Four points forming a rectangle, with both internal diagonals existing as lines.
    *   **Passive Bonus:** Grants the `Piercing Attacks` passive. The team's standard `Attack Line` action can now bypass one enemy shield.
*   **Plus-Rune (+):** A central point connected to four other points that form two perpendicular, straight lines.
    *   **Unlocks:** **[RUNE] Rune: Cardinal Pulse** action.
*   **T-Rune:** Four points in a 'T' shape. A central point is connected to two points forming a straight line (the stem) and a third point perpendicular to it (the head).
    *   **Unlocks:** **[RUNE] Rune: T-Hammer Slam** action.
*   **Trident-Rune:** An isosceles triangle and a fourth "handle" point extending from the apex along the line of symmetry. All required lines must exist.
    *   **Unlocks:** **[RUNE] Rune: Impale** action.
*   **Hourglass-Rune:** Five points forming two distinct triangles that share a single, common vertex point. All six lines must exist.
    *   **Unlocks:** **[RUNE] Rune: Time Stasis** action.
*   **Barricade-Rune:** Four points forming a rectangle, with all four sides existing as connected lines.
    *   **Unlocks:** **[RUNE] Rune: Raise Barricade** action.
*   **Parallelogram-Rune:** Four points forming a non-rectangular parallelogram, with all four sides existing as connected lines.
    *   **Unlocks:** **[RUNE] Rune: Parallel Discharge** action.
*   **Star-Rune:** A central point connected to a cycle of 5 or 6 other points, where the cycle points are also connected to each other sequentially.
    *   **Unlocks:** **[RUNE] Rune: Starlight Cascade**, **[RUNE] Rune: Gravity Well**, **[RUNE] Rune: Focus Beam**, and **[SACRIFICE] Build Wonder** actions.
*   **Trebuchet-Rune (Kite):** Four points in a kite shape, with all 5 lines forming the outer shape.
    *   **Unlocks:** **[FIGHT] Launch Payload** action.

## Sacrifice Mechanics
When a point is sacrificed as a cost for an action (e.g., Nova Burst, Create Whirlpool), it may not be gone forever. If the point was part of a simple line and not a critical structural weak point (an articulation point), its energy will coalesce. The point will be **removed from play for 3 turns, disabling any lines it was connected to**. After 3 turns, it will attempt to regenerate at its original location if the space is not blocked.

## Actions
On its turn, a team will perform an action from its pool of available actions. The choice is influenced by its Trait. Actions become available when a team meets specific geometric or structural conditions.

### Actions (Expand)
These actions are the primary way a team grows its presence on the grid.

#### Condition: Team has at least 1 point
*   **[EXPAND] Spawn Point:** Creates a new point in a random empty space near an existing friendly point. If it fails, it strengthens a line, and if that also fails, it creates a new point on the border.
*   **[EXPAND] Create Orbital:** Creates a constellation of 3-5 new 'satellite' points in a circle around an existing point. If it fails, it reinforces all lines connected to the chosen center.

#### Condition: Team has at least 2 points
*   **[EXPAND] Add Line:** Connects two of the team's points with a new line. If no more lines can be drawn, it strengthens an existing line instead.
*   **[EXPAND] Mirror Point:** Reflects a friendly point through another friendly point to create a new symmetrical point. If no valid reflection is found, it attempts to strengthen the line between a pair of points, or any random line as a final fallback.

#### Condition: Team has at least 1 line
*   **[EXPAND] Extend Line:** Extends a line between two points outwards to the grid border, creating a new point there. Can be empowered by an I-Rune to also create a line to the new point. If no valid extensions are possible, it strengthens an existing line.
*   **[EXPAND] Fracture Line:** Splits a long line into two smaller lines by creating a new point in the middle. If no lines are long enough, it strengthens one.

#### Condition: Team has a V-shape (a point connected to two lines)
*   **[EXPAND] Bisect Angle:** Finds a vertex point with two connected lines ('V' shape) and creates a new point along the angle's bisector. If it fails, it strengthens one of the angle's lines.

### Actions (Fight)
These actions are used to disrupt, damage, or destroy enemy assets.

#### Condition: Team has at least 1 point
*   **[FIGHT] Isolate Point:** _(No Cost)_ Projects an isolation field onto a critical enemy connection point (an articulation point), making it vulnerable to collapse over time. If no such point is found, it creates a defensive barricade (with 2+ points) or a weak repulsive pulse (with 1 point).

#### Condition: Team has at least 1 line
*   **[FIGHT] Attack Line:** Extends a line outwards. If it intersects an enemy line, the enemy line is destroyed. If it misses, a new point is created on the border.

#### Condition: Team has at least 2 points
*   **[FIGHT] Pincer Attack:** Two friendly points flank and destroy a vulnerable enemy point between them. If no target is found, two random friendly points form a temporary defensive barricade instead.

#### Condition: Team has at least 3 points
*   **[FIGHT] Hull Breach:** Projects the team's convex hull as an energy field, converting the most central enemy point found inside. If no enemy points are inside, it creates or reinforces the hull's boundary lines. If the hull is already fully reinforced, it emits a weak pulse that pushes nearby enemies away.

#### Condition: Team has a point and a non-incident line
*   **[FIGHT] Parallel Strike:** From a friendly point, projects a beam parallel to a friendly line. Destroys the first enemy point it hits, or creates a new point on the border if it misses.

#### Condition: Team has a claimed Territory
*   **[FIGHT] Territory Tri-Beam:** A claimed territory fires three beams of energy along the bisectors of its angles. Each beam destroys the first enemy line it hits. If a beam misses, it creates a new point on the border.

#### Condition: Team has a large Territory
*   **[FIGHT] Territory Strike:** Launches an attack from the center of a large claimed territory, destroying the nearest vulnerable enemy point. If no targets exist, it reinforces its own territory's borders.

### Actions (Fortify)
These actions focus on strengthening a team's position, building defenses, and creating complex structures.

#### Condition: Team has a "free" (non-structural) point
*   **[FORTIFY] Reposition Point:** _(No Cost)_ Moves a single 'free' (non-structural) point to a better tactical position nearby.
*   **[FORTIFY] Rotate Point:** _(No Cost)_ Rotates a single 'free' (non-structural) point around the grid center or another friendly point.
*   **[FORTIFY] Create Anchor:** _(No Cost)_ Turns a non-critical point into a gravitational anchor, which pulls nearby enemy points towards it for several turns.

#### Condition: Team has at least 1 line
*   **[FORTIFY] Shield Line / Overcharge:** _(No Cost)_ Applies a temporary shield to a line, making it immune to one standard attack. If all lines are shielded, it overcharges an existing shield to extend its duration.

#### Condition: Team has points and lines to form a triangle
*   **[FORTIFY] Claim Territory:** Forms a triangle of three points and their connecting lines into a claimed territory, making its points immune to conversion. If no new triangles can be formed, it reinforces an existing territory.

#### Condition: Team has at least 3 points
*   **[FORTIFY] Mirror Structure:** Creates a symmetrical structure by reflecting some of its points across an axis defined by two other points. If it fails, it reinforces lines connected to the team's two closest points. If that also fails, it adds a new line as a last resort.

#### Condition: Team has a fortified point
*   **[FORTIFY] Form Bastion:** Converts a fortified point and its connections into a powerful defensive bastion, making its components immune to standard attacks. If not possible, it reinforces a key defensive point.

#### Condition: Team has a rectangular formation
*   **[FORTIFY] Form Monolith:** Forms a tall, thin rectangle of points into a Monolith. Every few turns, the Monolith emits a wave that strengthens nearby friendly lines.

#### Condition: Team has a pentagonal formation
*   **[FORTIFY] Form Purifier:** Forms a regular pentagon of points into a Purifier, which unlocks the 'Purify Territory' action. If no valid formation is found, it reinforces the lines of a potential structure instead.

### Actions (Sacrifice)
Sacrifice actions require a team to destroy one of its own assets to produce a powerful effect.

#### Condition: Team has a non-critical point to sacrifice
*   **[SACRIFICE] Nova Burst:** Sacrifices a point to destroy all nearby enemy lines. If no lines are in range, it creates a shockwave that pushes all points away.
*   **[SACRIFICE] Create Whirlpool:** Sacrifices a point to create a vortex that pulls all nearby points towards its center for several turns. If no points are nearby on creation, it creates a small fissure instead.
*   **[SACRIFICE] Create Rift Trap:** Sacrifices a point to lay a temporary, invisible trap. If an enemy point enters its radius, the trap destroys it. If untriggered, it collapses into a new friendly point.

#### Condition: Team has at least 1 line to sacrifice
*   **[SACRIFICE] Convert Point:** Sacrifices a friendly line (preferring non-critical ones) to convert the nearest vulnerable enemy point to its team. If no target is in range, it creates a repulsive pulse that pushes enemies away.

#### Condition: Team has a non-critical line to sacrifice
*   **[SACRIFICE] Phase Shift:** Sacrifices a line to instantly 'teleport' one of the line's endpoints to a new random location. If it fails, the other endpoint becomes a temporary gravitational anchor.
*   **[SACRIFICE] Line Retaliation:** Sacrifices a point on a line to unleash two projectiles from the line's former position. One continues along the line's path, the other fires perpendicularly.

#### Condition: Team has a claimed Territory to sacrifice
*   **[SACRIFICE] Scorch Territory:** Sacrifices an entire claimed territory, destroying its points and lines to render the triangular area impassable and unbuildable for several turns.

#### Condition: Team has a special "Heartwood" formation
*   **[SACRIFICE] Cultivate Heartwood:** A unique action where a central point and at least 5 connected 'branch' points are sacrificed to create a Heartwood. The Heartwood passively generates new points and prevents enemy spawns nearby.

### Actions (Rune & Structure)
These are powerful actions unlocked by specific, complex geometric formations.

#### Condition: Team has an I-Rune (Sentry/Conduit)
*   **[FIGHT] Sentry Zap:** An I-Rune (Sentry) fires a precise beam that destroys the first enemy point it hits. If it misses, it creates a new point on the border.
*   **[FORTIFY] Create Ley Line:** _(No Cost)_ Activates an I-Rune into a powerful Ley Line for several turns, granting bonuses to nearby point creation. If all are active, it pulses one instead.
*   **[SACRIFICE] Chain Lightning:** An I-Rune (Conduit) sacrifices an internal point to destroy the nearest enemy point. If it fizzles, the point explodes in a mini-nova, destroying nearby lines.

#### Condition: Team has a V-Rune
*   **[RUNE] Rune: V-Beam:** A V-Rune fires a powerful beam along its bisector, destroying the first enemy line it hits. If it misses, it creates a fissure.

#### Condition: Team has a Shield-Rune
*   **[RUNE] Rune: Area Shield:** _(No Cost)_ A Shield-Rune protects all friendly lines inside its triangular boundary with temporary shields. If no lines are found inside, it instead pushes friendly points out to de-clutter.
*   **[RUNE] Rune: Shield Pulse:** _(No Cost)_ A Shield-Rune emits a shockwave, pushing all nearby enemy points away. If no enemies are in range, it gently pulls friendly points in.

#### Condition: Team has a Trident-Rune
*   **[RUNE] Rune: Impale:** A Trident-Rune fires a devastating beam that destroys ALL enemy lines in its path, piercing shields and monolith strength. If it misses, it creates a temporary barricade.

#### Condition: Team has a Plus-Rune
*   **[RUNE] Rune: Cardinal Pulse:** A Plus-Rune fires four beams from its center through its arms. Beams destroy the first enemy line they hit and create a new point on the border if they miss.

#### Condition: Team has a T-Rune
*   **[RUNE] Rune: T-Hammer Slam:** _(No Cost)_ A T-Rune creates a shockwave along its 'stem', pushing all nearby points away perpendicularly from the stem line. If no points are hit, it reinforces its own stem lines.

#### Condition: Team has a Parallelogram-Rune
*   **[RUNE] Rune: Parallel Discharge:** A Parallelogram-Rune destroys all enemy lines crossing its interior. If none, it creates a new central structure inside itself.

#### Condition: Team has a Barricade-Rune
*   **[RUNE] Rune: Raise Barricade:** _(No Cost)_ A Barricade-Rune creates a temporary, impassable wall along one of its diagonals.

#### Condition: Team has an Hourglass-Rune
*   **[RUNE] Rune: Time Stasis:** _(No Cost)_ An Hourglass-Rune freezes a nearby enemy point in time for several turns, making it immune but unable to be used. If no target is found, it creates an anchor.

#### Condition: Team has a Star-Rune
*   **[RUNE] Rune: Focus Beam:** A Star-Rune fires a beam from its center to destroy a high-value enemy structure (like a Wonder or Bastion core). If none exist, it targets a regular point.
*   **[RUNE] Rune: Starlight Cascade:** A Star-Rune unleashes a cascade of energy from its center, damaging or destroying all nearby unshielded enemy lines.
*   **[RUNE] Rune: Gravity Well:** _(No Cost)_ A Star-Rune creates a powerful gravitational field, pushing all non-friendly points away from its center.
*   **[SACRIFICE] Build Wonder:** A rare action requiring a Star-Rune formation. Sacrifices the entire formation to build the Chronos Spire, an indestructible structure that provides a victory countdown.

#### Condition: Team has a Nexus-Rune
*   **[SACRIFICE] Attune Nexus:** Sacrifices a diagonal line from one of its Nexuses to supercharge it. For several turns, the Attuned Nexus energizes all nearby friendly lines.

#### Condition: Team has a Bastion
*   **[SACRIFICE] Bastion Pulse:** An active Bastion sacrifices one of its outer points to destroy all enemy lines crossing its perimeter. If the action fizzles, it creates a local shockwave.

#### Condition: Team has a Prism-Rune
*   **[FIGHT] Refraction Beam:** A Prism structure is used to 'bank' an attack shot. A beam is fired, reflects off the Prism's edge, and destroys the first enemy line it then hits. If it misses, it creates a point on the border.

#### Condition: Team has a Trebuchet-Rune
*   **[FIGHT] Launch Payload:** A Trebuchet structure launches a projectile to destroy a high-value enemy point (e.g., a fortified point). If none exist, it targets a regular point. If no targets exist, it creates a fissure.

#### Condition: Team has a Purifier structure
*   **[FIGHT] Purify Territory:** _(No Cost)_ A Purifier structure neutralizes the nearest enemy territory, removing it from play and un-fortifying its points. If no enemy territories exist, it pushes nearby enemy points away.

### Actions (Terraform)
These actions alter the battlefield itself.

#### Condition: Team has a territorial nexus (point in 3+ territories)
*   **[TERRAFORM] Form Rift Spire:** _(No Cost)_ At a point that is a vertex of 3 or more territories, erects a Rift Spire. The Spire charges up to unlock the 'Create Fissure' action.

#### Condition: Team has a charged Rift Spire
*   **[TERRAFORM] Create Fissure:** _(No Cost)_ A charged Rift Spire creates a temporary, impassable fissure across the map that blocks line-based actions.

## Wonders
Wonders are unique, game-changing structures that require immense investment and provide a path to an alternative victory. Only one Wonder can be controlled by each team.

*   **Chronos Spire:**
    *   **Prerequisite:** A team must have an active **Star-Rune**.
    *   **Action:** The **[SACRIFICE] Build Wonder** action becomes available.
    *   **Cost:** The entire Star-Rune formation is sacrificed.
    *   **Bonus 1 (Temporal Distortion):** The Spire grants its owner **one bonus action** every turn. This stacks with other sources of bonus actions.
    *   **Bonus 2 (Victory Countdown):** The Spire is indestructible. If it remains on the field for **10 turns** after its creation, its owner immediately wins the game.