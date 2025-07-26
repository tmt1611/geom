*   **Implemented Sacrifice Actions:** Added the logic and preconditions for two missing sacrifice actions: `chain_lightning` and `cultivate_heartwood`, as defined in `action_data.py`.
*   **New Structure: Heartwood:** Implemented the "Heartwood" structure, a unique team structure created by the `cultivate_heartwood` action.
*   **Heartwood Turn Logic:** Added turn-based processing for Heartwoods, allowing them to passively generate new points for their team.
*   **Heartwood Gameplay Logic:** Integrated the Heartwood's defensive aura into the game's point placement validation, preventing enemies from spawning nearby.
*   **Code Refinement:** Added a helper method `_find_heartwood_candidates` to the `SacrificeActionsHandler` to centralize the logic for finding valid formations.
*   **Sacrifice Mechanic:** Updated the sacrifice logic for `chain_lightning` to use the `allow_regeneration` flag, allowing the sacrificed point to potentially respawn later.