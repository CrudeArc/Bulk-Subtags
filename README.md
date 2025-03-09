# Bulk Create Subtags

This Anki add-on allows you to efficiently create multiple subtags at the same time for a selected tag. Instead of adding subtags one by one, you can simply type or paste a list of subtag lines, and the add-on automatically creates a hierarchical structure by enumerating each line based on its indentation.

## Features

- **Bulk Subtag Creation:** Quickly create multiple subtags for a tag with one action. Just input your subtags using indentation (4 spaces or 1 tab per level) to denote hierarchy.
- **Hierarchical Tag Structure:** Each subtag is automatically enumerated (e.g., `01_Main_Tag`, `01_Main_Tag::01_Subtag`), making it easier to organize and manage nested tags.
- **Unique Interface:** A modern, dark-themed UI styled with the Orbitron font for a distinctive look.
- **Tag Selection:** Easily select an existing parent tag using a searchable tree widget and auto-completion.
- **Persistent Settings:** User preferences such as tag tree expansions and explanation visibility are saved between sessions.

## Installation

1. Download the latest release from the [Releases](https://github.com/CrudeArc/Bulk-Subtags) page.
2. Extract the file
3. Paste it in the Anki2/addons21/ directory (should be something like /home/user/.local/share/Anki2/addons21/ if you're on linux) alongside the other addons
4. If it went well, in anki Tools > addons you should see the addon appear

## Usage

1. **Select Cards:**  
   Open the Anki Browser and select one or more cards.  
   **Note:** If no cards are selected, you'll receive the message: "No cards selected. Please select cards in the browser."

2. **Launch Bulk Subtags:**  
   In the Browser window, go to the **Edit** menu and click on **Bulk Subtags**, or simply press the shortcut **Alt+B**.

3. **Configure Your Subtags:**  
   - **Parent Tag:** Optionally, click on the tag input field to type or select an existing tag. This will serve as the parent for the new subtags.
   - **Subtags Input:** Type or paste your list of subtags in the provided text area. Use indentation (4 spaces or 1 tab per level) to indicate the hierarchy. The add-on will automatically enumerate each line based on its indentation to create a structured set of subtags.

4. **Apply the Subtags:**  
   Click **OK** to add the newly created subtags to all the selected cards.

## Author

- **Cell ☘**
