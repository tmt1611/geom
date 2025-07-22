This iteration focuses on fixing a UI rendering bug and improving server-side error reporting to help diagnose a backend crash.

**1. Fixed Disappearing Grid on Tab Switch (Issue #1)**
- **Problem:** When switching from the "Action Guide" tab back to the "Game" tab during the setup phase, the canvas grid would disappear. This is a common issue when a canvas's parent container has `display: none`, as the canvas element's dimensions collapse to zero.
- **Analysis:** The existing fix using `requestAnimationFrame` was insufficient for the complex CSS grid/flexbox layout, which can take longer than a single frame to reflow. The `resizeCanvas` function was being called before the canvas's container had its final, non-zero dimensions.
- **Solution:** In `static/js/main.js`, the tab-switching event listener was modified to use `setTimeout(resizeCanvas, 0)` instead of `requestAnimationFrame`. Using a timeout of 0ms pushes the `resizeCanvas` call to the end of the browser's event queue. This ensures that all layout and rendering calculations triggered by the tab switch are complete before the canvas is resized, reliably solving the rendering issue.

**2. Improved Server Error Diagnostics (Issue #2)**
- **Problem:** A generic "Unhandled Promise Rejection" was reported from the frontend, indicating a server-side crash during gameplay, but with no details about the backend error.
- **Analysis:** The frontend's `_fetchJson` function was correctly identifying the server error (e.g., HTTP 500) and rejecting the promise. However, the error information passed to the frontend's global error handler was generic and did not include the rich traceback information sent by the Flask debug server in the response body.
- **Solution:**
    1.  In `static/js/api.js`, the `_fetchJson` function was updated. When a server error occurs, it now attaches the full text of the server's response (which contains the HTML traceback) to the `Error` object it throws.
    2.  In `static/js/main.js`, the global `unhandledrejection` event listener was enhanced. It now checks if the error object has the attached server response. If so, it extracts the traceback from the HTML and displays it in the error modal. This provides immediate, detailed diagnostic information to the user/developer, making it much easier to identify and fix the underlying Python bug.