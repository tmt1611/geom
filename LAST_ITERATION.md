### 1. New "Plus Rune" and Enhanced Action Fallbacks

This was a major update that addressed several core requests simultaneously, focusing on adding strategic depth and ensuring actions are never wasted.

-   **Files Modified**: `game_app/game_logic.py`, `static/js/main.js`, `rules.md`, `LAST_ITERATION.md`

-   **Key Changes**:
    -   **New Rune: The Plus-Rune (`+`)**:
        -   **Formation**: A new high-tier rune requiring 5 points and 4 lines in a perpendicular cross shape.
        -   **Bonus**: Unlocks the new `[RUNE] Cardinal Pulse` action.
    -   **New Action: `[RUNE] Cardinal Pulse`**:
        -   **Mechanic**: A powerful area-denial action that fires four beams from the rune's center. Each beam destroys the first enemy line it hits.
        -   **Fallback**: Any beam that misses creates a new friendly point on the border, making it a consistently powerful move.
    -   **Improved Action Fallbacks**: Several actions were enhanced to have "never useless" fallbacks, ensuring they have a meaningful impact even if their primary goal fails.
        -   **`Create Orbital`**: Now reinforces friendly lines if it cannot find a valid space to spawn.
        -   **`Rune: Starlight Cascade`**: Now creates a shockwave if it has no lines to damage.
        -   **`Rune: Focus Beam`**: Now creates a fissure if no targets of any kind are available.
    -   **Rulebook Cleanup**: The `rules.md` file was updated to include the new rune and its action. The `Sentry` and `Conduit` formations were also re-categorized under a unified **"I-Rune" (Line Rune)** concept for better clarity and thematic consistency.