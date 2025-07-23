This iteration focused on cleaning up the frontend code by removing a significant block of duplicated code and improving data consistency in the backend for a specific game structure.

**Key Changes:**

1.  **Refactored JavaScript:** A large block of code containing the `illustrationHelpers` and `illustrationDrawers` objects was duplicated in both `static/js/main.js` and `static/js/illustrations.js`. Since `illustrations.js` is loaded first, the definitions in `main.js` were overwriting the more complete ones from the dedicated file. This duplicated code has been removed from `main.js`, which now correctly uses the definitions from `illustrations.js`. This resolves a bug where many action illustrations in the guide would not display correctly and significantly cleans up the main JavaScript file.

2.  **Improved Data Consistency:** The `Heartwood` structure has a defensive aura that prevents enemy spawns. The radius of this aura was previously hardcoded in the geometry checking function. This value is now stored within the `Heartwood` object itself when it's created, making the structure's data self-contained and the single source of truth for its properties. The geometry function has been updated to read this value from the object.

These changes enhance code maintainability, fix a frontend bug, and improve the backend's data architecture.