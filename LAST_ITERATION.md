This iteration addresses two main issues: a critical backend crash during gameplay and a major refactoring of the `game_logic.py` file to improve code organization and maintainability.

### Issue 1: `KeyError` Crash during Action Logging

-   **Problem:** The server would crash with a `KeyError: 'destroyed_team_name'` when certain actions, like `pincer_attack`, were performed. The action's result dictionary, used to generate a log message, was missing the required key for the destroyed point's team name.
-   **Analysis:** A review of the `ACTION_LOG_GENERATORS` dictionary showed that several log messages relied on a `destroyed_team_name` or `target_team_name` key. However, the corresponding action methods in `game_logic.py` were not always adding this key to their return value.
-   **Solution:** I have systematically identified all action methods (`pincer_attack`, `sentry_zap`, `chain_lightning`, `launch_payload`, `hourglass_stasis`, and `focus_beam`) that could cause this error. Each method has been updated to include the necessary team name in its result dictionary upon successfully destroying or targeting an enemy point. This ensures that the log generation step will always have the data it needs, preventing the crash.

### Issue 2: Refactoring `game_logic.py`

-   **Problem:** The `game_logic.py` file was over 4,000 lines long, with a significant portion dedicated to large, static dictionaries containing game data (action descriptions, weights, log messages, etc.). This made the file difficult to navigate and maintain.
-   **Solution:**
    1.  A new file, `game_app/game_data.py`, has been created to act as a centralized repository for this static game data.
    2.  All large data dictionaries (`ACTION_GROUPS`, `ACTION_DESCRIPTIONS`, `ACTION_VERBOSE_DESCRIPTIONS`, `ACTION_MAP`, `ACTION_LOG_GENERATORS`, etc.) have been moved from the `Game` class into `game_app/game_data.py`.
    3.  The `Game` class in `game_logic.py` now imports this data from the new module. This separation of concerns drastically reduces the size of `game_logic.py` by nearly 300 lines, making the core game logic much cleaner and easier to read.
    4.  During the refactoring, an unused and incorrect method, `_get_action_weights`, was identified and removed, further cleaning up the codebase.

These changes resolve the critical bug and significantly improve the project's structure according to best practices, making future development more efficient.