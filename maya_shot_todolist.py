"""
Maya Native Pre-Publish Shot To-Do List (Auto-Height)
----------------------------------------------------
A lightweight, scene-persistent checklist tool for Maya artists.
Auto-resizes dynamically based on task count with no internal scrollbars.

Author: Rahul Gambhir
Version: 1.0.0
GitHub: https://github.com/thecodemaster21
"""

import json
import maya.cmds as cmds


class MayaShotChecklistUI(object):
    def __init__(self):
        self.window_name = "MayaShotChecklistWindow"
        self.node_name = "sg_todolist_data_node"
        
        # Default fallback tasks for new scenes
        self.default_tasks = [
            {"text": "Notes from Producer", "checked": False},
            {"text": "UV Check", "checked": False},
            {"text": "Check Light and Reflections", "checked": False}
        ]

    def build_ui(self):
        # Delete existing window instance if open
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name, window=True)

        # Create floating Maya window
        self.window = cmds.window(
            self.window_name,
            title="Shot Publish To-Do List",
            minimizeButton=True,
            maximizeButton=False,
            sizeable=True
        )

        # Main Layout
        main_layout = cmds.columnLayout(
            adjustableColumn=True,
            columnOffset=("both", 10),
            rowSpacing=6
        )

        # Title Header
        cmds.text(
            label="Shot Publish Checklist",
            height=25,
            font="boldLabelFont",
            align="left"
        )
        cmds.separator(height=4, style="single")

        # Input Row (Text Field + Add Button)
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnWidth2=(260, 80))
        self.task_input = cmds.textField(
            placeholderText="Add task before publishing...",
            enterCommand=lambda x: self.add_task_from_input()
        )
        cmds.button(label="+ Add", command=lambda x: self.add_task_from_input(), backgroundColor=[0.2, 0.5, 0.8])
        cmds.setParent("..")

        cmds.separator(height=4, style="none")

        # Direct container layout (No ScrollLayout = No inner scrollbars)
        self.task_container = cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
        cmds.setParent("..")

        cmds.separator(height=4, style="single")

        # Footer Stats & Control Button
        self.status_text = cmds.text(label="0 / 0 Completed", align="left", font="boldLabelFont")

        cmds.rowLayout(numberOfColumns=1, adjustableColumn=1)
        cmds.button(
            label="Restore Defaults",
            command=lambda x: self.restore_defaults(),
            backgroundColor=[0.3, 0.3, 0.3]
        )
        cmds.setParent("..")

        # Load existing scene tasks or defaults
        self.load_tasks()

        # Display window
        cmds.showWindow(self.window)
        self.adjust_window_size()

    def adjust_window_size(self):
        """Calculates dynamic window height based on task count to remove blank space."""
        checkbox_count = len(self.get_all_checkboxes())
        # Base UI height (~135px) + 22px per checkbox item
        calc_height = 135 + (checkbox_count * 22)
        
        cmds.window(self.window_name, edit=True, widthHeight=(360, calc_height))

    def add_task_from_input(self):
        """Reads text from input box and creates a new checkbox entry."""
        text = cmds.textField(self.task_input, query=True, text=True).strip()
        if text:
            self.create_task_checkbox(text, checked=False)
            cmds.textField(self.task_input, edit=True, text="")
            self.save_tasks()
            self.adjust_window_size()

    def create_task_checkbox(self, text, checked=False):
        """Builds a single native checkbox item inside the container layout."""
        cmds.setParent(self.task_container)
        cb = cmds.checkBox(
            label=text,
            value=checked,
            changeCommand=lambda x: self.save_tasks()
        )
        return cb

    def get_all_checkboxes(self):
        """Queries all checkbox child UI elements in the container."""
        children = cmds.columnLayout(self.task_container, query=True, childArray=True) or []
        return children

    def save_tasks(self):
        """Gathers task state and saves it to a hidden scriptNode inside the scene."""
        checkboxes = self.get_all_checkboxes()
        tasks = []
        completed_count = 0

        for cb in checkboxes:
            label = cmds.checkBox(cb, query=True, label=True)
            val = cmds.checkBox(cb, query=True, value=True)
            tasks.append({"text": label, "checked": val})
            if val:
                completed_count += 1

        total_count = len(tasks)

        # Update stats text
        if hasattr(self, "status_text"):
            cmds.text(
                self.status_text,
                edit=True,
                label=f"{completed_count} / {total_count} Completed"
            )

        # Save to Maya Scene Node
        raw_data = json.dumps(tasks)
        if not cmds.objExists(self.node_name):
            cmds.scriptNode(st=0, scriptType=0, beforeScript="", name=self.node_name)

        cmds.scriptNode(self.node_name, edit=True, beforeScript=raw_data)

    def load_tasks(self):
        """Loads tasks stored in scene node, or initializes defaults if empty."""
        # Clear existing container UI elements
        checkboxes = self.get_all_checkboxes()
        for cb in checkboxes:
            cmds.deleteUI(cb)

        if cmds.objExists(self.node_name):
            try:
                raw_data = cmds.scriptNode(self.node_name, query=True, beforeScript=True)
                tasks = json.loads(raw_data)
                if tasks:
                    for t in tasks:
                        self.create_task_checkbox(t["text"], t["checked"])
                    self.save_tasks()
                    self.adjust_window_size()
                    return
            except Exception:
                pass

        # Fallback to default task list
        self.load_defaults()

    def load_defaults(self):
        """Loads default task list into UI."""
        for t in self.default_tasks:
            self.create_task_checkbox(t["text"], t["checked"])
        self.save_tasks()
        self.adjust_window_size()

    def restore_defaults(self):
        """Deletes scene data node and reloads default task list."""
        if cmds.objExists(self.node_name):
            cmds.delete(self.node_name)
        self.load_tasks()


# Run in Maya
def show_ui():
    ui = MayaShotChecklistUI()
    ui.build_ui()


if __name__ == "__main__":
    show_ui()