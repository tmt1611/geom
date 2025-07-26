This iteration focused on cleaning up documentation and ensuring consistency between the `rules.md` file, the `action_data.py` definitions, and the actual implementation in `game_logic.py` and its handlers. This improves clarity for players and maintainability for developers.

1.  **Corrected `rules.md` for `no_cost` Actions**: Updated several actions in `rules.md` (`Create Anchor`, `Reposition Point`) to reflect their `no_cost` status and remove inaccurate descriptions of sacrifice or fallback behavior.

2.  **Documented New/Missing Actions**: Added descriptions for `Rotate Point` and `Gravity Well` to `rules.md`, as they were implemented but not yet documented for players.

3.  **Standardized `no_cost` Tag**: Ensured all `no_cost` actions (`Purify Territory`, `Area Shield`, `Shield Pulse`, etc.) explicitly state "This action has no cost." in `rules.md` for consistency.

4.  **Action Group Correction**: Moved `Convert Point` from the `[FIGHT]` group to the `[SACRIFICE]` group in `rules.md`, to correctly categorize it as a sacrifice action per `design.md`.

5.  **Updated Star-Rune Rules**: Corrected the `Starlight Cascade` description to remove the mention of sacrifice and added the new `Gravity Well` action to the list of Star-Rune bonuses.

6.  **Clarified Action Description**: Refined the description for `fight_purify_territory` in `action_data.py` to more accurately state that it removes the entire territory, not just the "fortified" status.