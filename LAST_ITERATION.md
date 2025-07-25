This iteration focuses on streamlining the structure system as outlined in `design.md`. I've made the conceptual framework cleaner by consolidating all passive, auto-detected geometric formations under the "Rune" category in the documentation. This improves clarity for the user and aligns the rules more closely with the implementation.

1.  **Streamlined Structure/Rune Categories:**
    *   Identified that several structures (`Nexus`, `Prism`, `Trebuchet`) were passive formations detected automatically, just like the existing "Runes".
    *   To make the terminology consistent, these have been re-categorized as `Nexus-Rune`, `Prism-Rune`, and `Trebuchet-Rune` in `rules.md`.
    *   This clarifies the distinction between passive "Runes" and actively built "Structures" (like Bastions or Monoliths).

2.  **Updated `rules.md` for Clarity and Consistency:**
    *   Moved the descriptions for `Nexus`, `Prism`, and `Trebuchet` into the main `Runes` section, removing their old "Form X" entries from the `Actions` list.
    *   Moved `Star-Rune` out of the `Wonders` section and into the `Runes` section, as it is a prerequisite formation, not the wonder itself.
    *   Rewrote the `Wonders` section to focus solely on the `Chronos Spire` and its prerequisites, improving clarity.
    *   Updated the descriptions for actions like `Attune Nexus` and `Launch Payload` to refer to the new `Nexus-Rune` and `Trebuchet-Rune` names.

3.  **Corrected Action Description:**
    *   The description for `Isolate Point` in `rules.md` stated that it cost a line, which was inconsistent with the implementation and `design.md`'s principles for no-cost actions. I have corrected the description to reflect that it is a no-cost projection action.

These changes primarily affect the documentation (`rules.md`) to create a more coherent and streamlined conceptual model for players, without requiring major backend code changes.