This iteration focused on implementing several new rune-based sacrifice actions, bringing the game's mechanics closer to the vision in `design.md`.

1.  **Implemented New Rune-Sacrifice Actions:** Added four complex actions that are unlocked by specific runes and involve sacrificing part or all of the rune structure, as per `design.md` and `rules.md`.
    -   `sacrifice_attune_nexus`: A Nexus sacrifices one of its diagonal lines to become "attuned," energizing nearby friendly lines for several turns, causing their attacks to become more destructive.
    -   `sacrifice_starlight_cascade`: A Star-Rune sacrifices an outer point to create a small blast that destroys nearby unshielded enemy lines.
    -   `sacrifice_t_hammer_slam`: A T-Rune sacrifices its "head" point to create a perpendicular shockwave, pushing points away from its "stem." It reinforces itself if it misses.
    -   `sacrifice_cardinal_pulse`: A Plus-Rune is consumed entirely to fire four powerful beams in cardinal directions, destroying enemy lines or creating new friendly points.

2.  **State Management for New Effects:**
    -   Added the `attuned_nexuses` state to `game_logic.py`.
    -   Implemented the `_process_attuned_nexuses` logic in `turn_processor.py` to handle the effect's duration.
    -   Updated `structure_data.py` to include `attuned_nexuses` in the turn processing order.

3.  **Code Cleanup:**
    -   Added necessary imports for new geometry functions in `sacrifice_actions.py`.
    -   Ensured the new actions and their preconditions are correctly registered and checked by the game logic.