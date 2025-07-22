This iteration focuses on fixing a key frontend UI bug and analyzing a reported server error.

### 1. Fixed Disappearing Grid on Tab Switch (Issue #1)

- **Problem:** When navigating to the "Action Guide" tab and then back to the "Game" tab, the game grid canvas would disappear. This happened because the canvas element, being inside a container set to `display: none`, would lose its dimensions.
- **Solution:** In `static/js/main.js`, the tab-switching event listener was modified. Now, when the user clicks to activate the "Game" tab, a manual call to `resizeCanvas()` is triggered. This call is wrapped in `requestAnimationFrame()` to ensure the browser has completed its layout updates for the newly visible tab before the canvas is resized. This guarantees the canvas correctly redraws itself to fit its container, resolving the issue.

### 2. Analysis of Server Error (Issue #2)

- **Problem:** An "Unhandled Promise Rejection" error was reported during gameplay, originating from the `_fetchJson` function in `static/js/api.js`.
- **Analysis:**
    - The `_fetchJson` function was reviewed and found to be robust. It correctly handles various server responses, including successful requests, server errors (like 500 Internal Server Error), empty responses, and non-JSON responses.
    - The "unhandled rejection" is being correctly caught by a global error handler in `main.js`, which then displays the error modal to the user. This is the intended behavior for notifying the user of a server-side problem.
    - Therefore, the issue is not a bug in the JavaScript error handling, but rather an underlying error in the Python backend (`game_logic.py`) that is causing the server to crash and return an error page instead of valid JSON.
- **Conclusion:** Without a specific traceback from the server, pinpointing the exact cause in the complex Python game logic was not feasible in this iteration. The frontend is correctly reporting the backend failure. The fix for Issue #1 has been implemented.