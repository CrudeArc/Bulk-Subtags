import os
import json
from aqt import mw
from aqt.qt import (
    QAction, QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLineEdit, QLabel, QTreeWidget, QTreeWidgetItem, QMenu, QCompleter
)
from aqt.utils import showInfo
from aqt.browser import Browser
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QHeaderView
)

##############################################################################
#                              SETTINGS                                      #
##############################################################################
ADDON_NAME = "Bulk Create Subtags"
ADDON_DIR = os.path.join(mw.pm.addonFolder(), ADDON_NAME)
SETTINGS_FILE = os.path.join(ADDON_DIR, "bulk_subtags_settings.json")

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error loading settings:", e)
        return {}

def save_settings(data):
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Error saving settings:", e)
        pass

settings = load_settings()
if "expansions" not in settings:
    settings["expansions"] = {}
if "explanationVisible" not in settings:
    settings["explanationVisible"] = True

##############################################################################
#                          ORBITRON FONT LOADING                             #
##############################################################################
orbitron_font = None
orbitron_family = None
try:
    font_path = os.path.join(ADDON_DIR, "Orbitron-Regular.ttf")
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            orbitron_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            orbitron_font = QFont(orbitron_family, 8)
            # Set letter spacing to 150% for the main UI
            orbitron_font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 150)
except Exception as e:
    print("Error loading Orbitron font:", e)
    pass

##############################################################################
#                     APPLY CUSTOM ORBITRON STYLE                            #
##############################################################################
def apply_orbitron_style(widget):
    """
    Applies a custom darker style to the widget.
    This uses Orbitron plus a unique dark look with deeper backgrounds,
    darker borders, and refined hover/pressed effects.
    """
    base_style = f"""
    /* General Dialog styling */
    QDialog {{
      background-color: #1F1F1F;
      border: 1px solid #333;
      border-radius: 8px;
    }}
    /* Orbitron font for core widgets */
    QDialog, QWidget, QLineEdit, QPushButton, QTreeWidget, QLabel, QTextEdit {{
      font-family: 'Orbitron', sans-serif;
      font-size: 8pt;
      letter-spacing: 1.8px;
    }}
    /* QLineEdit styling */
    QLineEdit {{
      background-color: #2D2F33;
      border: 1px solid #444;
      border-radius: 4px;
      padding: 4px;
      color: #DADADA;
    }}
    /* QPushButton styling */
    QPushButton {{
      background-color: #2D2F33;
      border: 1px solid #444;
      border-radius: 4px;
      padding: 6px 12px;
      color: #DADADA;
    }}
    QPushButton:hover {{
      background-color: #3A3E42;
    }}
    QPushButton:pressed {{
      background-color: #24282B;
    }}
    /* QTreeWidget styling */
    QTreeWidget {{
      background-color: #2D2F33;
      border: none;
      color: #DADADA;
    }}
    QTreeWidget::item {{
      padding-top: 4px;
      padding-bottom: 4px;
    }}
    QTreeWidget::item:selected {{
      background-color: #444;
      color: #FFFFFF;
    }}
    /* QCompleter popup (QListView) styling */
    QListView {{
      background-color: #2D2F33;
      color: #DADADA;
      border: 1px solid #444;
    }}
    """
    widget.setStyleSheet(base_style)
    if orbitron_font:
        widget.setFont(orbitron_font)

##############################################################################
#                      HELPER FUNCTIONS FOR TAGS                             #
##############################################################################
def get_all_tags():
    try:
        tags = mw.col.tags.all()
        tags.sort()
        return tags
    except Exception as e:
        print("Error retrieving tags:", e)
        return []

def replace_spaces_with_underscores(s: str) -> str:
    return s.replace(" ", "_")

def parse_indentation_level(line: str):
    leading_spaces = 0
    for ch in line:
        if ch == ' ':
            leading_spaces += 1
        elif ch == '\t':
            leading_spaces += 4
        else:
            break
    indent_level = leading_spaces // 4
    to_remove = leading_spaces
    actual_removed = 0
    new_content = []
    for ch in line:
        if ch == ' ' and actual_removed < to_remove:
            actual_removed += 1
        elif ch == '\t' and actual_removed + 4 <= to_remove:
            actual_removed += 4
        else:
            new_content.append(ch)
    content = "".join(new_content).strip()
    return indent_level, content

def parse_indented_subtags_enumerate_all(lines):
    counters = [0] * 50
    levels = [None] * 50
    results = []
    for line in lines:
        indent_level, raw_content = parse_indentation_level(line)
        if not raw_content.strip():
            continue
        for i in range(indent_level + 1, len(counters)):
            counters[i] = 0
            levels[i] = None
        counters[indent_level] += 1
        content = replace_spaces_with_underscores(raw_content)
        enumerated_name = f"{counters[indent_level]:02d}_{content}"
        levels[indent_level] = enumerated_name
        path_segments = [levels[i] for i in range(indent_level + 1) if levels[i]]
        final_path = "::".join(path_segments)
        results.append(final_path)
    seen = set()
    final = []
    for r in results:
        if r not in seen:
            seen.add(r)
            final.append(r)
    return final

##############################################################################
#              HIERARCHICAL TAG TREE WIDGET & SELECTION DIALOG               #
##############################################################################
class TagTreeWidget(QTreeWidget):
    def __init__(self, multi_select=False, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.setAccessibleName("Tag Tree")
        self.setToolTip("Select one or more tags from the hierarchical tree.")
        self.setStyleSheet("""
        QTreeWidget::item {
            /* Base item styling */
            padding: 4px 8px;
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        QTreeWidget::item:selected {
            /* Selected item styling */
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(100, 150, 255, 0.05),
                stop:1 rgba(100, 150, 255, 0.05)
            );
            color: #4477cc;
            border: 1px solid rgba(100, 150, 255, 0.3);
            border-radius: 8px;
            font-weight: bold;
        }
        QTreeWidget::item:selected:focus {
            /* Remove or restyle the black focus rectangle */
            outline: none;  /* Removes default dotted focus outline */
            border: 1px solid rgba(100, 150, 255, 0.5);
            border-radius: 8px;
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(100, 150, 255, 0.05),
                stop:1 rgba(100, 150, 255, 0.05)
            );
            color: #4477cc;
            font-weight: bold;
        }
        QTreeWidget:focus {
            /* Prevent the QTreeWidget from showing an additional focus outline */
            outline: none;
        }
        """)
        self.setHeaderHidden(True)
        self.setColumnCount(1)
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        self.populateTree()
        self.collapseAll()
        self.applySavedExpansions()
        if multi_select:
            self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        else:
            self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.itemExpanded.connect(lambda i: self.onItemExpandedOrCollapsed(i, True))
        self.itemCollapsed.connect(lambda i: self.onItemExpandedOrCollapsed(i, False))

    def populateTree(self):
        self.clear()
        treeDict = {}
        for tag in get_all_tags():
            parts = tag.split("::")
            current = treeDict
            for part in parts:
                current = current.setdefault(part, {})
            current["_full"] = tag

        def addItems(parent, subtree):
            for key, value in subtree.items():
                if key == "_full":
                    continue
                item = QTreeWidgetItem([key])
                full_tag = value.get("_full", key)
                item.setData(0, Qt.ItemDataRole.UserRole, full_tag)
                if parent is None:
                    self.addTopLevelItem(item)
                else:
                    parent.addChild(item)
                addItems(item, value)

        addItems(None, treeDict)

    def applySavedExpansions(self):
        def walk(item):
            full_tag = item.data(0, Qt.ItemDataRole.UserRole)
            if full_tag:
                is_expanded = settings["expansions"].get(full_tag, False)
                item.setExpanded(is_expanded)
            for i in range(item.childCount()):
                walk(item.child(i))
        for i in range(self.topLevelItemCount()):
            walk(self.topLevelItem(i))

    def onItemExpandedOrCollapsed(self, item, expanded):
        full_tag = item.data(0, Qt.ItemDataRole.UserRole)
        if full_tag:
            settings["expansions"][full_tag] = expanded
            save_settings(settings)

    def getSelectedTags(self):
        selected = self.selectedItems()
        return [itm.data(0, Qt.ItemDataRole.UserRole) for itm in selected if itm]

    def filterTree(self, query: str):
        tokens = [t.strip().lower() for t in query.split() if t.strip()]

        def matches(item) -> bool:
            text = item.text(0).lower()
            full_tag = (item.data(0, Qt.ItemDataRole.UserRole) or "").lower()
            if not tokens:
                return True
            for tok in tokens:
                if tok in text or tok in full_tag:
                    return True
            return False

        def filterItem(item):
            me = matches(item)
            child_match = False
            for i in range(item.childCount()):
                if filterItem(item.child(i)):
                    child_match = True
            show_me = me or child_match
            item.setHidden(not show_me)
            return show_me

        for i in range(self.topLevelItemCount()):
            filterItem(self.topLevelItem(i))

class TagSelectionDialog(QDialog):
    def __init__(self, multi_select=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Tag")
        self.resize(500, 600)
        main_layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Search tags...")
        self.search_edit.setAccessibleName("Search Tags")
        self.search_edit.setToolTip("Type here to filter the list of tags.")
        search_layout.addWidget(self.search_edit)
        main_layout.addLayout(search_layout)

        self.tree = TagTreeWidget(multi_select=multi_select, parent=self)
        main_layout.addWidget(self.tree)

        btnLayout = QHBoxLayout()
        okBtn = QPushButton("OK", self)
        okBtn.setAccessibleName("Confirm Tag Selection")
        okBtn.setToolTip("Press to confirm the tag selection (Ctrl+Enter).")
        okBtn.setShortcut("Ctrl+Return")
        cancelBtn = QPushButton("Cancel", self)
        cancelBtn.setAccessibleName("Cancel Tag Selection")
        cancelBtn.setToolTip("Press to cancel this selection.")
        btnLayout.addWidget(okBtn)
        btnLayout.addWidget(cancelBtn)
        main_layout.addLayout(btnLayout)

        okBtn.clicked.connect(self.accept)
        cancelBtn.clicked.connect(self.reject)
        apply_orbitron_style(self)
        self.setLayout(main_layout)
        self.search_edit.textChanged.connect(self.onSearchChanged)

    def onSearchChanged(self, text):
        self.tree.filterTree(text)

    def getSelectedTags(self):
        return self.tree.getSelectedTags()

##############################################################################
#                          BULK SUBTAG DIALOG                                #
##############################################################################
class BulkSubtagDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bulk Create Subtags")
        self.resize(600, 400)
        layout = QVBoxLayout(self)

        # Parent tag input layout
        parent_layout = QHBoxLayout()
        self.parentTagEdit = QLineEdit(self)
        self.parentTagEdit.setPlaceholderText("Enter or select parent tag (optional)")
        self.parentTagEdit.setAccessibleName("Parent Tag Input")
        self.parentTagEdit.setToolTip("You may type a parent tag manually or click the button to select one.")
        all_tags = get_all_tags()
        self.completer = QCompleter(all_tags)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.parentTagEdit.setCompleter(self.completer)
        if orbitron_family:
            orbitron_completer_font = QFont(orbitron_family, 8)
            orbitron_completer_font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 130)
            self.completer.popup().setFont(orbitron_completer_font)
            self.completer.popup().setStyleSheet("""
            QListView {
                font-family: 'Orbitron', sans-serif;
                font-size: 8pt;
                letter-spacing: 1.3px;
            }
            """)
        select_button = QPushButton("Select Tag", self)
        select_button.setAccessibleName("Select Parent Tag")
        select_button.setToolTip("Click here to open a tag selector dialog.")
        select_button.clicked.connect(self.open_tag_selection)
        parent_layout.addWidget(QLabel("<b>Parent Tag:</b>", self))
        parent_layout.addWidget(self.parentTagEdit)
        parent_layout.addWidget(select_button)
        layout.addLayout(parent_layout)

        # Toggle explanation section
        self.toggleButton = QPushButton(self)
        explanation_visible = settings.get("explanationVisible", True)
        self.toggleButton.setText("Hide Explanation" if explanation_visible else "Show Explanation")
        self.toggleButton.setAccessibleName("Toggle Explanation Visibility")
        self.toggleButton.setToolTip("Click to show or hide the explanation for subtag formatting.")
        self.toggleButton.clicked.connect(self.toggleExplanation)
        layout.addWidget(self.toggleButton)

        label_text = (
            "<b>Subtags:</b><br>"
            "Each line is enumerated at its indentation level (01_, 02_, etc.).<br>"
            "Indentation = multiples of 4 spaces or 1 tab => deeper level.<br><br>"
            "<b>Example:</b><br>"
            "01_Main_Tag<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;01_Subtag<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;01_Child Tag<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;02_Child Tag<br>"
            "01_Main_Tag<br>"
        )
        self.explanationLabel = QLabel(label_text, self)
        self.explanationLabel.setWordWrap(True)
        self.explanationLabel.setTextFormat(Qt.TextFormat.RichText)
        self.explanationLabel.setVisible(explanation_visible)
        self.explanationLabel.setAccessibleName("Subtag Explanation")
        self.explanationLabel.setToolTip("This section explains how to format your subtags with indentation and numbering.")
        layout.addWidget(self.explanationLabel)

        # Subtags text edit area
        self.subtagsEdit = QTextEdit(self)
        self.subtagsEdit.setPlaceholderText("Paste or type your lines here...")
        self.subtagsEdit.setAccessibleName("Subtags Input Area")
        self.subtagsEdit.setToolTip("Type or paste your subtag lines here. Each line with proper indentation will be enumerated.")
        layout.addWidget(self.subtagsEdit)

        # OK / Cancel buttons layout
        btnLayout = QHBoxLayout()
        self.okButton = QPushButton("OK", self)
        self.okButton.setAccessibleName("Confirm Bulk Subtags")
        self.okButton.setToolTip("Press to add the subtags to selected cards (Ctrl+Enter).")
        self.okButton.setShortcut("Ctrl+Return")
        self.cancelButton = QPushButton("Cancel", self)
        self.cancelButton.setAccessibleName("Cancel Bulk Subtags")
        self.cancelButton.setToolTip("Press to cancel this operation, closing the dialog.")
        btnLayout.addWidget(self.okButton)
        btnLayout.addWidget(self.cancelButton)
        layout.addLayout(btnLayout)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self.setLayout(layout)
        apply_orbitron_style(self)

    def toggleExplanation(self):
        isVisible = self.explanationLabel.isVisible()
        newVisible = not isVisible
        self.explanationLabel.setVisible(newVisible)
        self.toggleButton.setText("Hide Explanation" if newVisible else "Show Explanation")
        settings["explanationVisible"] = newVisible
        save_settings(settings)

    def open_tag_selection(self):
        dlg = TagSelectionDialog(multi_select=False, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            selected = dlg.getSelectedTags()
            if selected:
                self.parentTagEdit.setText(selected[0])

    def getData(self):
        parentTag = replace_spaces_with_underscores(self.parentTagEdit.text().strip())
        lines = self.subtagsEdit.toPlainText().splitlines()
        enumerated_paths = parse_indented_subtags_enumerate_all(lines)
        final_tags = []
        for path in enumerated_paths:
            if parentTag:
                final_tags.append(f"{parentTag}::{path}")
            else:
                final_tags.append(path)
        return final_tags

##############################################################################
#            APPLY SUBTAGS TO SELECTED CARDS FROM THE BROWSER              #
##############################################################################
def add_subtags_to_cards(browser):
    card_ids = browser.selectedCards()
    if not card_ids:
        showInfo("No cards selected. Please select cards in the browser.")
        return
    dlg = BulkSubtagDialog(browser)
    if dlg.exec() == QDialog.DialogCode.Accepted:
        full_tags = dlg.getData()
        if not full_tags:
            showInfo("No subtags provided.")
            return
        for cid in card_ids:
            card = browser.mw.col.getCard(cid)
            note = card.note()
            # Handle tags stored as either list or string format
            if isinstance(note.tags, list):
                current_tags = note.tags
            else:
                current_tags = note.tags.split()
            for new_tag in full_tags:
                if new_tag not in current_tags:
                    current_tags.append(new_tag)
            if isinstance(note.tags, list):
                note.tags = current_tags
            else:
                note.tags = " ".join(current_tags)
            note.flush()
        browser.mw.col.save()
        showInfo("Subtags added to selected cards.")

##############################################################################
#                    INTEGRATE ADD-ON INTO THE BROWSER MENU                  #
##############################################################################
old_setupMenus = Browser.setupMenus

def new_setupMenus(self):
    old_setupMenus(self)
    
    # Add new action for bulk subtags
    action = QAction("Bulk Subtags", self)
    action.triggered.connect(lambda: add_subtags_to_cards(self))
    action.setShortcut("Alt+B")  # Shortcut to open the add-on
    action.setToolTip("Open Bulk Subtags dialog (Alt+B)")
    
    # Instead of using the Tools menu, look for the Edit menu
    edit_menu = None
    if hasattr(self.form, "menuEdit"):
        edit_menu = self.form.menuEdit
    else:
        edit_menu = self.menuBar().findChild(QMenu, "menuEdit")
    if edit_menu:
        edit_menu.addAction(action)
    else:
        self.menuBar().addAction(action)

Browser.setupMenus = new_setupMenus
print("Bulk Create Subtags add-on loaded.")