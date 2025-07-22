The main field is a 10x10 grid where users select multiple points, which may belong to two or more teams. These points and teams can expand, interact, or fight based on geometry-based rules.

**Goals:**

* Create a highly random, visually engaging auto-battle sandbox.
* Build a fun divination-style game: once all actions settle, the final grid pattern can be interpreted — for example, a user can input two sets of points: one tied to a birthdate and one to today’s date. After the simulation, the result can be read like a horoscope or star chart.

Users should be able to add points easily.

**Three phases:**

1. **Init phase:**
   Users set initial points (manually or randomly generated).

2. **Action phase:**
   Actions unfold based on geometric rules. Examples:

   * *Expand:* Extend the line between two same-team points. If the line hits the grid border, spawn a new team point at the edge.
   * *Expand:* Add a new line segment between two same-team points.
   * *Fight:* Extend a line segment. If it hits an enemy line, delete the enemy line.

   Each team can take multiple actions per turn. Actions are randomly selected and shown to the user. The action phase can run turn-by-turn or continue rapidly until finished. Users can set max turn count or other stopping conditions.

3. **Interpret phase:**
   The app helps users analyze the result. This may involve scoring (for sandbox play) or visual/structural interpretation (for divination). Examples: count triangles, measure total occupied area, number of lines, etc.

All actions must be geometric and visually striking. They can involve points, lines, shapes, hulls, or similar geometry elements.
