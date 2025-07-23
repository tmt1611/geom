This iteration introduces a significant code cleanup, a bug fix, and a new illustration for the Action Guide.

### 1. Refactored Turn Processing Logic

To improve code organization and make the core `game_logic.py` file more manageable, all start-of-turn effect processing logic has been extracted into a new, dedicated `TurnProcessor` class in `game_app/turn_processor.py`. This includes methods for handling the decay of shields and traps, the effects of anchors and whirlpools, and the passive abilities of structures like Heartwoods and Monoliths. This refactoring cleans up the main `Game` class, making its responsibilities clearer and the overall codebase easier to maintain.

### 2. Fixed ID Generation Bug

A latent bug was discovered in `fight_actions.py` where two actions (`attack_line` and the fallback for `pincer_attack`) were calling a non-existent `_generate_id` method. This would have caused a crash if those specific code paths were executed. I have replaced these calls with the correct `uuid`-based ID generation, ensuring consistency and preventing future errors.

### 3. New Illustration for "Build Wonder"

To continue expanding the visual documentation of game mechanics, a new illustration has been created for the powerful `fortify_build_wonder` action. The illustration depicts a team sacrificing a complex Star-Rune formation, which then transforms into the Chronos Spire wonder, visually explaining the high cost and significant outcome of this game-changing action.