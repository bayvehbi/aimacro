import tkinter as tk
from tkinter import ttk
import re
from aimacro.ui.dialogs.pattern_search_dialog import open_pattern_window
from aimacro.ui.dialogs.image_ai_dialog import open_image_ai_window
from aimacro.ui.dialogs.if_condition_dialog import open_if_window

class DraggableTreeview(ttk.Treeview):
    def __init__(self, master, accepted_sources=None, allow_drop=True, allow_self_drag=True, **kwargs):
        super().__init__(master, selectmode="extended", columns=("item"), show="tree", **kwargs)
        self.accepted_sources = accepted_sources if accepted_sources is not None else []  # List of accepted drag sources
        self.allow_drop = allow_drop  # Allow dropping items into this treeview
        self.allow_self_drag = allow_self_drag  # Allow dragging within this treeview
        self.clipboard_items = []
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.start_drag)
        self.bind("<ButtonRelease-1>", self.drop)
        self.bind("<Double-1>", self.open_edit_dialog)   
        self.bind("<Delete>", self.delete_selected)  # Bind Delete key to remove selected items
        self.bind_all("<Control-c>", self.copy_selected_items)
        self.bind_all("<Control-x>", self.cut_selected_items)
        self.bind_all("<Control-v>", self.paste_items)
        self.drag_data = {"items": [], "dragging": False, "selection_locked": False, "hover_item": None, "hover_treeview": None}

        # Configure visual styles
        self.tag_configure("selected", background="lightblue")
        self.tag_configure("hover", background="orange")
        self.tag_configure("target_hover", background="purple")
        self.tag_configure("active", background="green")  # Tag for active item
        self.column("#0", width=150)


    def copy_selected_items(self, event=None):
        selected = self.selection()
        if selected:
            self.clipboard_items = [self.item(i, "text") for i in selected]
            print(f"Copied {len(self.clipboard_items)} items")

    def cut_selected_items(self, event=None):
        selected = self.selection()
        if selected:
            self.clipboard_items = [self.item(i, "text") for i in selected]
            for i in selected:
                self.delete(i)
            self._rebuild_checkpoint_indices()
            print(f"Cut {len(self.clipboard_items)} items")

    def paste_items(self, event=None):
        if not self.clipboard_items:
            print("Clipboard empty")
            return

        selected = self.selection()
        if selected:
            insert_index = self.index(selected[-1]) + 1
        else:
            insert_index = len(self.get_children())

        for item_text in self.clipboard_items:
            self.insert("", insert_index, text=item_text)
            insert_index += 1

        # Rebuild checkpoint indices after paste
        self._rebuild_checkpoint_indices()
        print(f"Pasted {len(self.clipboard_items)} items")


    def open_edit_dialog(self, event):
        item_id = self.identify_row(event.y)
        item_idx = self.index(self.identify_row(event.y))
        if item_id:
            item_text = self.item(item_id, "text")
            pattern = r'(\w[\w\s]+):\s*((?:\{.*?\}|\(.*?\)|[^,])+)(?:,|$)'
            matches = re.findall(pattern, item_text)
            parsed_list = [(key.strip(), value.strip()) for key, value in matches]
            parsed_dict = dict(parsed_list)
            from aimacro.ui.dialogs.checkpoint_dialog import open_checkpoint_window
            from aimacro.ui.dialogs.wait_dialog import open_wait_window

            def map_pattern_keys(d):
                # Map to the exact keys expected by open_pattern_window
                return {
                    "pattern_image_base64": d.get("Image"),
                    "search_coords": d.get("Search Area"),
                    "succeed_checkpoint": d.get("Succeed Go To"),
                    "fail_checkpoint": d.get("Fail Go To"),
                    "click": d.get("Click"),
                    "wait_time": d.get("Wait", "5.0s").replace("s", ""),
                    "threshold": d.get("Threshold"),
                    "scene_change": d.get("Scene Change"),
                    "succeed_notification": d.get("Succeed Notification"),
                    "fail_notification": d.get("Fail Notification"),
                    "succeed_send": "Succeed Notification" in d and d.get("Succeed Notification") != "None",
                    "fail_send": "Fail Notification" in d and d.get("Fail Notification") != "None",
                    "item_id": item_idx
                }

            def map_image_ai_keys(d):
                return {
                    "coords": d.get("Area"),
                    "wait_time": d.get("Wait", "5.0s").replace("s", ""),
                    "variable_name": d.get("Variable"),
                    "variable_content": d.get("Variable Content"),
                    "ai_provider": d.get("Provider"),
                    "feature": d.get("Feature"),
                    "item_id": item_idx  # Use item_id if not present

                }

            def map_if_keys(d):
                return {
                    "variable": d.get("Variable"),
                    "condition": d.get("Condition"),
                    "value": d.get("Value"),
                    "succeed_checkpoint": d.get("Succeed Go To"),
                    "fail_checkpoint": d.get("Fail Go To"),
                    "succeed_send": d.get("Succeed Notification") not in (None, "", "None"),
                    "fail_send": d.get("Fail Notification") not in (None, "", "None"),
                    "succeed_notification": d.get("Succeed Notification"),
                    "fail_notification": d.get("Fail Notification"),
                    "item_id": item_idx  # Use item_id if not present
                }

            if item_text.startswith("Search Pattern"):
                iv = map_pattern_keys(parsed_dict)
                iv["item_id"] = item_id  # ensure we pass the stable Treeview IID
                open_pattern_window(
                    self.master.master,
                    self.master.master.add_event_to_treeview,  # real updater
                    initial_values=iv
            )
            elif item_text.startswith("Image AI") or item_text.startswith("Image AI"):
                print(f"Opening Image AI or Image AI for item: {item_text}")
                iv = map_image_ai_keys(parsed_dict)
                iv["item_id"] = item_id  # pass the stable Treeview IID
                open_image_ai_window(
                    self.master.master,
                    self.master.master.add_event_to_treeview,
                    initial_values=iv
                )
            elif item_text.startswith("If"):
                print(f"Opening If window for item: {item_text}")
                iv = map_if_keys(parsed_dict)
                iv["item_id"] = item_id  # pass the stable Treeview IID
                open_if_window(
                    self.master.master,
                    self.master.master.add_event_to_treeview,
                    variables={},
                    initial_values=iv
                )
            elif item_text.startswith("Checkpoint"):
                open_checkpoint_window(self.master, lambda *args, **kwargs: None)
            elif item_text.startswith("Wait"):
                from aimacro.core.event_patterns import WAIT_PATTERN
                wait_match = WAIT_PATTERN.match(item_text)
                if wait_match:
                    wait_time = wait_match.group(1)
                    iv = {
                        "wait_time": wait_time,
                        "item_id": item_id
                    }
                    open_wait_window(
                        self.master.master,
                        self.master.master.add_event_to_treeview,
                        initial_values=iv
                    )
            elif item_text.startswith("Go To"):
                from ..dialogs.goto_dialog import open_goto_window
                # Parse Go To event
                goto_match = re.match(r"Go To - (Target|Line): (.+?)(?:, Element: (.+))?$", item_text)
                if goto_match:
                    goto_type, target, element_text = goto_match.groups()
                    iv = {
                        "goto_type": goto_type,
                        "item_id": item_id
                    }
                    if goto_type == "Checkpoint":
                        iv["checkpoint"] = target.strip()
                    else:  # Line
                        iv["line_number"] = int(target.strip())
                        iv["element_text"] = element_text or ""
                    
                    open_goto_window(
                        self.master.master,
                        self.master.master.add_event_to_treeview,
                        checkpoints=self.master.master.checkpoints,
                        treeview=self.master.master.left_treeview,
                        initial_values=iv
                    )


        

    def on_click(self, event):
        """Handle mouse click to initiate selection or drag."""
        item = self.identify_row(event.y)
        if not item:
            return "break"

        current_selection = self.selection()
        if item in current_selection:
            self.drag_data["selection_locked"] = True
            self.drag_data["items"] = list(current_selection)
            return "break"

        self.drag_data["selection_locked"] = False
        return

    def start_drag(self, event):
        """Start dragging selected items."""
        if not self.drag_data["dragging"] and self.drag_data["items"]:
            self.drag_data["dragging"] = True
            print("Drag started")
            self.config(style="NoHighlight.Treeview")
        elif not self.drag_data["selection_locked"]:
            selected = self.selection()
            if selected:
                self.drag_data["items"] = selected
                self.drag_data["dragging"] = True
                print(f"Drag started, items: {[self.item(i, 'text') for i in selected]}")
                self.config(style="NoHighlight.Treeview")

        if self.drag_data["dragging"]:
            # Clear previous hover highlight
            if self.drag_data["hover_item"] and self.drag_data["hover_treeview"]:
                self.drag_data["hover_treeview"].item(self.drag_data["hover_item"], tags=[])
                self.drag_data["hover_item"] = None
                self.drag_data["hover_treeview"] = None

            drop_target = self.winfo_containing(event.x_root, event.y_root)
            if drop_target == self and self.allow_self_drag:
                hover_item = self.identify_row(event.y)
                if hover_item and hover_item not in self.drag_data["items"]:
                    self.item(hover_item, tags=["hover"])
                    self.drag_data["hover_item"] = hover_item
                    self.drag_data["hover_treeview"] = self
                    print(f"Self hover: {self.item(hover_item, 'text')}")
            elif (isinstance(drop_target, DraggableTreeview) and drop_target.allow_drop and 
                  self in drop_target.accepted_sources):
                drop_y = event.y_root - drop_target.winfo_rooty()
                hover_item = drop_target.identify_row(drop_y)
                if hover_item and hover_item not in self.drag_data["items"]:
                    drop_target.item(hover_item, tags=["target_hover"])
                    self.drag_data["hover_item"] = hover_item
                    self.drag_data["hover_treeview"] = drop_target
                    print(f"Target hover: {drop_target.item(hover_item, 'text')}")

        return "break"

    def get_item_treeview(self, item):
        """Check if an item belongs to this treeview."""
        try:
            self.item(item)
            return self
        except:
            return None

    def drop(self, event):
        """Handle dropping of dragged items."""
        if not self.drag_data["items"] or not self.drag_data["dragging"]:
            print("Drop cancelled: no items or not dragging")
            self.cleanup()
            return

        drop_target = self.winfo_containing(event.x_root, event.y_root)
        print(f"Drop target: {drop_target}, This treeview: {self}")

        if drop_target == self and self.allow_self_drag:
            # Reorder within the same treeview
            drop_item = self.identify_row(event.y)
            drop_index = self.index(drop_item) if drop_item else len(self.get_children())
            print(f"Self drop: {drop_item}, index: {drop_index}")
            items_to_move = self.drag_data["items"]
            for item in reversed(items_to_move):
                self.detach(item)
            for item in items_to_move:
                self.move(item, "", drop_index)
                drop_index += 1
            # Rebuild checkpoint indices after reordering
            self._rebuild_checkpoint_indices()

        elif isinstance(drop_target, DraggableTreeview) and drop_target.allow_drop and self in drop_target.accepted_sources:
            # Move to another treeview
            drop_y = event.y_root - drop_target.winfo_rooty()
            drop_item = drop_target.identify_row(drop_y)
            drop_index = drop_target.index(drop_item) if drop_item else len(drop_target.get_children())
            print(f"Target drop: {drop_item}, index: {drop_index}")
            items_to_move = self.drag_data["items"]
            for item in reversed(items_to_move):
                text = self.item(item, "text")
                print(f"Moved item: {text}")
                self.delete(item)
                new_item = drop_target.insert("", drop_index, text=text)
                drop_index += 1
            # Rebuild checkpoints in both treeviews after move
            self._rebuild_checkpoint_indices()
            if hasattr(drop_target.master.master, 'checkpoints'):
                drop_target._rebuild_checkpoint_indices()

        self.cleanup()

    def delete_selected(self, event):
        """Delete selected items using the Delete key."""
        selected_items = self.selection()
        if selected_items:
            for item in selected_items:
                self.delete(item)
                print(f"Deleted item: {item}")
            self._rebuild_checkpoint_indices()
        else:
            print("No items selected to delete")

    def _rebuild_checkpoint_indices(self):
        """Rebuild all checkpoint indices by scanning the treeview."""
        if not hasattr(self.master.master, 'checkpoints'):
            return
        
        # Clear and rebuild from scratch - simple and effective
        self.master.master.checkpoints.clear()
        for i, child in enumerate(self.get_children()):
            child_text = self.item(child, "text")
            # Extract action part (after timestamp if present)
            action = child_text.split(" - ", 1)[-1] if " - " in child_text else child_text
            # Only match actual checkpoint markers
            if action.strip().startswith("Checkpoint: "):
                checkpoint_name = action.split("Checkpoint: ", 1)[1].strip()
                self.master.master.checkpoints[checkpoint_name] = i
                print(f"Updated checkpoint '{checkpoint_name}' to index {i}")

    def cleanup(self):
        """Reset drag state and clear highlights."""
        if self.drag_data["hover_item"] and self.drag_data["hover_treeview"]:
            self.drag_data["hover_treeview"].item(self.drag_data["hover_item"], tags=[])
            self.drag_data["hover_item"] = None
            self.drag_data["hover_treeview"] = None

        for item in self.get_children():
            self.item(item, tags=[])

        drop_target = self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
        if isinstance(drop_target, DraggableTreeview) and drop_target != self:
            for item in drop_target.get_children():
                drop_target.item(item, tags=[])

        self.config(style="Treeview")
        self.drag_data["items"] = []
        self.drag_data["dragging"] = False
        self.drag_data["selection_locked"] = False
        print("All highlights cleared")

    def highlight_active_item(self, index, previous_index=None):
        """Highlight the item at the specified index, updating only previous and active items."""
        children = self.get_children()
        if not children:
            return

        # Clear highlight from previous item if valid
        if previous_index is not None and 0 <= previous_index < len(children):
            self.item(children[previous_index], tags=[])
            print(f"Removed highlight from previous item at index {previous_index}: {self.item(children[previous_index], 'text')}")

        # Highlight the active item if valid
        if 0 <= index < len(children):
            self.item(children[index], tags=["active"])
            print(f"Highlighted active item at index {index}: {self.item(children[index], 'text')}")
        elif index == -1:  # Clear all highlights
            for item in children:
                self.item(item, tags=[])
            print("Cleared all highlights")