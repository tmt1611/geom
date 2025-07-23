The main field is a 10x10 grid where users place multiple points, potentially linked to different teams. These points and teams can grow, interact, or clash through geometry-based rules.

**Objectives:**

* Build a highly random, visually engaging auto-battle sandbox.
* Create a divination-style game where, after actions resolve, the resulting grid pattern can be interpreted. Example: users input two point sets — one based on a birthdate, another on today's date — and the simulation outcome is read similarly to a horoscope or star chart.

Users must be able to place points easily.

**Game has three phases:**

1. **Init phase:**
   Users input initial points manually or via random generation.

2. **Action phase:**
   Geometric rules drive actions. Examples:

   * *Expand:* Draw a line between two same-team points. If the line touches the grid border, a new team point appears at the edge.
   * *Expand:* Create a new line segment connecting two same-team points.
   * *Fight:* Extend a line. If it hits an enemy line, that enemy line is removed.

   Each team performs multiple actions per turn. Actions are picked randomly from the available pool and displayed to the user. The phase can proceed turn-by-turn or run rapidly until stopping criteria (e.g., turn limit) are met.

3. **Interpret phase:**
   The system helps users examine the outcome. This can include scores (for sandbox use) or structural/visual analysis (for divination). Metrics might include triangle count, occupied area, line count, etc.

All actions must be geometric and visually impactful. They may use points, lines, shapes, hulls, and similar geometry constructs.

**Complex structure design:**

* The game favors more complex structures by granting stronger actions, better defense, and strategic benefits.
* Complexity hierarchy: point < line < rune < territory < wonder.
* When a rune or territory is destroyed, all its points are lost. However, runes and territories must be tougher than the sum of their parts.

**Special status system:**

* Statuses (e.g., reinforced, fortified, enhanced, protected) are allowed but must be non-redundant and minimal in overlap.

**Action system details:**

* Structures (points, lines, runes, territories) and their positions define the action pool under geometric constraints.
* Action selection works in two steps: group probabilities are distributed evenly and then modified by team traits; within a group, actions are evenly split.
* Some actions are stronger, especially those from advanced structures.
* Sacrifice actions must be grouped separately. Example: sacrificing a point to trigger an attack is not a fight action but a sacrifice action.
* Sacrifice actions must never result in negative net gain. At worst, they offer zero net gain — which already has a cost due to time or structure loss.
  Example: sacrificing a point for a infinitely-lasting attack that hits three times, then restores the point. At all times, the team holds one point or an equivalent attack.
* Sacrifice must yield at least 2×, 3×, 4×, 5× the cost when using points, lines, runes, and territories, respectively.
* Structures must provide more non-sacrifice than sacrifice actions.
