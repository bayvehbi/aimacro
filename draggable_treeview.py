import tkinter as tk
from tkinter import ttk

class DraggableTreeview(ttk.Treeview):
    def __init__(self, master, accepted_sources=None, allow_drop=True, allow_self_drag=True, **kwargs):
        super().__init__(master, selectmode="extended", columns=("item"), show="tree", **kwargs)
        self.accepted_sources = accepted_sources if accepted_sources is not None else []  # List of accepted drag sources
        self.allow_drop = allow_drop  # Allow dropping items into this treeview
        self.allow_self_drag = allow_self_drag  # Allow dragging within this treeview
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.start_drag)
        self.bind("<ButtonRelease-1>", self.drop)
        self.bind("<Delete>", self.delete_selected)  # Bind Delete key to remove selected items
        self.drag_data = {"items": [], "dragging": False, "selection_locked": False, "hover_item": None, "hover_treeview": None}

        # Configure visual styles
        self.tag_configure("selected", background="lightblue")
        self.tag_configure("hover", background="orange")
        self.tag_configure("target_hover", background="purple")
        self.tag_configure("active", background="green")  # Tag for active item
        self.column("#0", width=150)

    def on_click(self, event):
        """Handle mouse click to initiate selection or drag."""
        item = self.identify_row(event.y)
        if not item:
            return "break"

        current_selection = self.selection()
        if item in current_selection:
            self.drag_data["selection_locked"] = True
            self.drag_data["items"] = list(current_selection)
            print(f"Selected items: {[self.item(i, 'text') for i in current_selection]}")
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
            # Update checkpoint indices in Page1
            if hasattr(self.master.master, 'checkpoints'):
                for checkpoint_name in self.master.master.checkpoints:
                    for i, child in enumerate(self.get_children()):
                        if f"Checkpoint: {checkpoint_name}" in self.item(child, "text"):
                            self.master.master.checkpoints[checkpoint_name] = i
                            print(f"Updated checkpoint '{checkpoint_name}' to index {i}")
                            break

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

        self.cleanup()

    def delete_selected(self, event):
        """Delete selected items using the Delete key."""
        selected_items = self.selection()
        if selected_items:
            for item in selected_items:
                self.delete(item)
                print(f"Deleted item: {item}")
        else:
            print("No items selected to delete")

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