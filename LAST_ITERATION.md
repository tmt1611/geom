This iteration focused on improving the user experience of the "Action Guide" tab by introducing clear visual sections for each action category. This makes the guide easier to navigate and digest, addressing the request to "improve the layout... avoid cluttering".

### Action Guide Layout Improvements

1.  **Visual Grouping**: The Action Guide now renders actions within distinct sections for each category (Expand, Fight, Fortify, etc.). Each section is preceded by a large, clear header, breaking up the "wall of cards" and making the information more structured.

2.  **Sticky Section Headers**: To enhance navigation within the guide, the section headers are now "sticky". As you scroll down the list of actions, the header for the current category remains visible at the top of the view, ensuring you always know which group of actions you are looking at.

3.  **Unified Scrolling**: The scrolling behavior has been refined. Instead of each action group having its own grid, the entire guide content now scrolls as a single unit, which is a more standard and user-friendly interaction.

4.  **Minor Aesthetic Tweak**: The vertical alignment within each action card's header has been adjusted from `baseline` to `center`, providing better visual balance between the action's name and its category tag.

These changes are primarily implemented in `static/css/style.css`, leveraging the existing JavaScript structure that already builds the guide in sections.