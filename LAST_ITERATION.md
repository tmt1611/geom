This iteration focuses on fixing two key frontend issues: one related to UI layout and another to robust error handling.

### 1. Fixed Disappearing Grid on Tab Switch (Issue #1)

- **Problem:** When navigating to the "Action Guide" tab and then back to the "Game" tab, the game grid canvas would disappear.
- **Cause:** This was a layout issue. When the game tab's container was set to `display: none`, the canvas's container lost its dimensions. The `ResizeObserver` was not reliably re-triggering to resize the canvas when the tab became visible again.
- **Solution:** In `static/js/main.js`, a manual call to `resizeCanvas()` has been added within the tab-switching logic. This call is wrapped in `requestAnimationFrame()` to ensure the browser has completed its layout calculations for the newly visible tab before the canvas is resized, guaranteeing it correctly fits its container.

### 2. Implemented Robust API Error Handling (Issue #2)

- **Problem:** The application would crash with a `JSON.parse` error when the server returned a non-JSON response, such as an HTML error page for a 500 Internal Server Error.
- **Cause:** The `fetch` calls in `static/js/api.js` did not check if the server response was successful (`response.ok`) before attempting to parse the body as JSON.
- **Solution:**
    - A new helper function, `_fetchJson`, was created in `api.js`.
    - This function wraps the `fetch` call and first checks if `response.ok` is true.
    - If the response is not OK, it reads the response body as text (to capture any error messages from the server) and throws a descriptive `Error`.
    - It also handles cases where a successful response might have an empty body, preventing parsing errors in that scenario.
    - All API calls in `api.js` were refactored to use this new, safer helper function. This prevents the JSON parsing crash and allows the global error handler in `main.js` to display a more informative error message to the user.

These changes enhance the stability and user experience of the application, making it more resilient to layout quirks and server-side errors.