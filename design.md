
## **Overview**

A 10×10 grid-based auto-battle sandbox where users place multiple points belonging to different teams. Points and teams interact or clash through geometry-based rules. The simulation can be interpreted in two ways:

* As a battle game.
* As a divination-style pattern analysis.

## **Objectives**

* Build a highly random, visually engaging auto-battle sandbox.
* Enable divination-style interpretation of results.
  Example: Users input two sets of points (e.g., birthdate and today’s date); simulation resolves; grid is interpreted similar to a horoscope or star chart.

## **Phases**

### 1. **Init Phase**

* Users input initial points manually or via random generation.
* Must allow easy point placement.

### 2. **Action Phase**

* Driven by geometric rules.
* Each team performs one action per turn, unless get bonus action by special structures. Some actions are no-cost, they grant a bonus action. Team may use only one no-cost action per turn.
* Actions are picked randomly from a pool and shown to the user.
* Can run turn-by-turn or rapidly until a stopping condition (e.g., turn limit).
* If an action might fail, fallback logic must reduce its cost.

**Action Examples:**

* **Expand:**

  * Draw a line between two same-team points. If it touches the border, create a new point at the edge.
  * Connect two same-team points with a new line segment.
* **Fight:**

  * Extend a line to deal 1 damage to each enemy line it touches.
  * Add fallback if miss: generate points, lines, traps that may revert into points, or bounce at the border.

**Geometric constraints:**

* All actions must be geometry-based and visually clear and impressive.
* Use constructs: points, lines, shapes, hulls, rotations, mirrors.
* Avoid generic effects. Prefer specific designs, e.g.:

  * Instead of make a point from a point, try : From a point, draw line parallel to a friendly line. If it hits enemy point, destroy. If it hits border, generate a point.
  * Instead of make a point from a point, try : Mirror a friendly point through another.
  * Instead of move a point, try : Rotate a point around grid center or another point.
  * Instead of convert a point, try : convert a point that is contained in the hull of the team (with proper visual display of the hull for user to see)

### 3. **Interpret Phase**

* System helps analyze outcomes.
* Use scores (sandbox) or structural/visual metrics (divination).
* Metrics may include: triangle count, occupied area, line count, etc.

## **Structures and Complexity**

**Complexity hierarchy:**
`Point < Line < Rune < Territory < Wonder`

* Stronger structures provide better actions, defense, and strategic benefits.
* To destroy rune/territory/wonder: enemy must destroy all constituent points.
* Friendly structures can be restored by recreating missing points.

**Example:**

* Line-based fight: extend line to attack or create up to 2 points.
* Triangle territory fight: extend 3 bisectors, potentially affecting more targets.

## **Status System**

* Statuses (e.g., reinforced, fortified, enhanced, protected) allowed.
* Must be minimal, non-redundant, and consistent across actions.
* Example:

  * Fortified: adds 1 hitpoint to a point or line.

    * Via fortify action or placing a point on an occupied location.

## **Action System**

**Action Pool:**

* Defined by structure types and positions under geometric constraints.
* Selection in two steps:

  1. Group-level probability (equal, then team-modified)
  2. Even split within group

**Action Design Rules:**

* Stronger structures yield stronger actions.
* Any actions containing sacrifice must be counted as sacrifice action.
* Action that does not generate points or deal damage (like rotations, push, pull, etc) must not cost points.
* Action pool should NEVER be empty, there should always be available actions even in extreme cases (only one point left, only 2 points far away, only a line left, etc)

**Sacrifice Action Rules:**

* Never cause negative net gain.
* Must return at least:
  * 2× cost for points
  * 3× for lines
  * 4× for runes
  * 5× for territories
* Rune, territory, and wonder points cannot be sacrificed.
* Structures must offer more non-sacrifice actions than sacrifice actions.

**Sacrifice Variants:**

* **On lonely point:**

  * Sacrifice to trigger action.
* **On point part of a line:**

  1. If line remains, regenerate point after 3 turns.
  2. Line also sacrificed: fires a perpendicular and an extended line.

     * Deals 1 damage on first enemy hit or creates point if border is hit.
  3. The other point on the line can trigger same effect without being sacrificed.

## **Rules Management**

* All changes to structures, statuses, actions, etc. must be updated in `rules.md`.
