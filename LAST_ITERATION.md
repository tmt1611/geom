This iteration implemented a missing high-level feature from the design documents.

1.  **Implemented Wonder Construction**: The `build_chronos_spire` action, defined in `action_data.py` but missing an implementation, has been added to `sacrifice_actions.py`.
2.  **New Action Logic**: This new sacrifice action allows a team with a Star-Rune to sacrifice the entire rune formation to create a "Chronos Spire" wonder. This introduces an alternative victory condition as specified in `rules.md`.
3.  **Added Precondition**: A corresponding `can_perform_build_chronos_spire` check was added to ensure the action is only available to teams that have a Star-Rune and do not already control a wonder.