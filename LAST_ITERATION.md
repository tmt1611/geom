This iteration resolves a frontend rendering bug and a critical backend crash.

**1. Fixed Disappearing Grid on Tab Switch (Issue #1)**
- **Problem:** The canvas grid and points would disappear when switching to another tab and back during the setup phase.
- **Analysis:** This was caused by the canvas's parent container being set to `display: none`, which collapses the canvas's client dimensions to zero. When the tab became visible again, the `resizeCanvas` function was sometimes called before the layout was fully recalculated, causing the canvas's drawing surface to be incorrectly sized to 0x0. The `ResizeObserver` was the correct tool, but it could also be triggered when the canvas was hidden, setting its size to 0.
- **Solution:** Two changes were made in `static/js/main.js`:
    1.  A guard condition was added to `resizeCanvas()` to prevent it from executing if the canvas's `clientWidth` is 0. This stops the drawing buffer from being destroyed when the tab is hidden.
    2.  The manual `setTimeout(resizeCanvas, 0)` call in the tab-switching logic was removed. This simplifies the code and makes the `ResizeObserver` the single source of truth for handling resizes, which is more robust and prevents potential race conditions.

**2. Fixed `AttributeError` Crash during Sacrifice Actions (Issue #2)**
- **Problem:** The game server would crash with an `AttributeError: 'Game' object has no attribute '_find_non_critical_sacrificial_point'` when certain sacrifice actions (like `sacrifice_whirlpool`) were attempted.
- **Analysis:** The error was straightforward: the `_find_non_critical_sacrificial_point` method was called by several actions but was never defined in the `Game` class in `game_app/game_logic.py`.
- **Solution:**
    1.  A new private method, `_find_non_critical_sacrificial_point`, was implemented and added to the `Game` class.
    2.  This method provides crucial game logic to prevent teams from crippling themselves. It identifies a "safe" point to sacrifice by first excluding points that are part of important structures (Runes, Bastions, Monoliths, etc.).
    3.  It then performs a graph analysis to ensure the chosen point is not an "articulation point" (i.e., its removal won't split the team's formation into separate, disconnected pieces).
    4.  This fix not only resolves the crash but also significantly improves the game's AI by making sacrifice actions smarter and less self-destructive.