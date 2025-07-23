This iteration introduces a new strategic action inspired by concepts of Feng Shui (channeling energy) and warfare (strategic upgrades), and also performs a code cleanup to improve the robustness of how nexuses are handled.

### 1. New Feng Shui/Warfare Action: Attune Nexus

A new `Fortify` action has been added to provide teams with a powerful, temporary offensive buff, creating a new strategic objective around the `Nexus` structure.

*   **Action:** `Attune Nexus`
*   **Concept:** A team can channel energy into one of its Nexus structures, a place of geometric stability and power. This transforms it into an "Attuned Nexus" for a limited time.
*   **Cost & Effect:** The action sacrifices one of the Nexus's diagonal lines. In return, the Attuned Nexus projects an "energy field" in a radius around it. All friendly lines within this field become **Energized**.
*   **Strategic Impact:** An Energized line used in an `Attack Line` action is devastating. It not only destroys the enemy line but also obliterates both of its endpoints, making it a powerful tool for dismantling an opponent's entire structure. This creates a high-risk, high-reward choice: sacrifice a line for a temporary but significant power boost.
*   **Implementation:**
    *   A new `attune_nexus` method and its precondition check were added to `fortify_actions.py`.
    *   The game state in `game_logic.py` now tracks `attuned_nexuses`, which decay over time via the `turn_processor.py`.
    *   The `attack_line` logic in `fight_actions.py` was updated to check if the attacking line is energized and, if so, to destroy the target's points as well.
    *   The frontend in `main.js` now renders Attuned Nexuses with a distinct pulsing energy aura, and Energized Attacks are visualized with a more powerful beam effect.

### 2. Code Refactoring: Robust Nexus Handling

The introduction of this new action highlighted a need for more robust handling of Nexus structures.

*   The helper function `_find_attunable_nexuses` was created to ensure that only valid, non-attuned nexuses with the required diagonal line can be selected for the new action.
*   The `drawNexuses` function in `main.js` was refactored to handle rendering both regular and the new Attuned Nexuses from a single, unified data source, simplifying the rendering logic.