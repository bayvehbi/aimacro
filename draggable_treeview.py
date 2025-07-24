import tkinter as tk
from tkinter import ttk
import re

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

        print(f"Pasted {len(self.clipboard_items)} items")


    def open_edit_dialog(self, event):
        import re
        import ast

        def is_mouse_action_with_coordinates(text):
            patterns = [
                r"Mouse Button\.left (pressed|released) at: \(\d+, \d+\)",
                r"Mouse Button\.right (pressed|released) at: \(\d+, \d+\)",
                r"Mouse scrolled (up|down) at: \(\d+, \d+\)"
            ]
            return any(re.match(p, text) for p in patterns)

        item_id = self.identify_row(event.y)
        if not item_id:
            return

        full_text = self.item(item_id, "text").strip()

        if full_text.startswith("OCR Search - Area:"):
            try:
                values = self.item(item_id, "values")
                coords, wait, variable, content = values
                initial_values = {
                    "coords": coords,
                    "wait_time": float(wait),
                    "variable_name": variable,
                    "variable_content": content,
                    "item_id": item_id
                }
                from ai_stuff import open_ocr_window
                open_ocr_window(
                    self.master.master,
                    self.master.master.add_event_to_treeview,
                    self.master.master.variables,
                    edit_mode=True,
                    initial_values=initial_values
                )
                return
            except Exception as e:
                print(f"Error parsing OCR values: {e}")

        if full_text.startswith("Search Pattern - Image:"):
            try:
                values = self.item(item_id, "values")
                print("[DEBUG] Pattern Search values:", values)
                (
                    pattern_image_base64,
                    search_coords,
                    succeed_goto,
                    fail_goto,
                    click,
                    wait_time,
                    threshold,
                    scene_change,
                    succeed_notify,
                    succeed_notify_value,
                    fail_notify,
                    fail_notify_value
                ) = values

                context = {
                    "item_id": item_id,
                    "pattern_image_base64": pattern_image_base64,
                    "search_coords": search_coords,
                    "pattern_coords": None,  # You can enhance this later
                    "search_image_base64": None,
                    "succeed_goto": succeed_goto,
                    "fail_goto": fail_goto,
                    "click": click == "True",
                    "wait_time": float(wait_time),
                    "threshold": float(threshold),
                    "scene_change": scene_change == "True",
                    "succeed_notify": succeed_notify == "True",
                    "succeed_notify_value": succeed_notify_value,
                    "fail_notify": fail_notify == "True",
                    "fail_notify_value": fail_notify_value,
                }

                self.master.master.editing_pattern_context = context
                from ai_stuff import open_pattern_window
                open_pattern_window(self.master.master, self.master.master.add_event_to_treeview)
                return
            except Exception as e:
                print(f"Error parsing Pattern Search values: {e}")

        action_only = full_text.split(" - ", 1)[-1].strip()
        if is_mouse_action_with_coordinates(action_only):
            edit_win = tk.Toplevel(self)
            edit_win.title("Edit Mouse Action")
            edit_win.grab_set()
            edit_win.resizable(False, False)

            raw_var = tk.StringVar(value=full_text)
            use_current_position = tk.BooleanVar(value=False)

            tk.Label(edit_win, text="Mouse Action Text:").pack(padx=10, pady=(10, 4))
            tk.Entry(edit_win, textvariable=raw_var, width=70).pack(padx=10, pady=4)

            tk.Checkbutton(
                edit_win,
                text="Use current position (remove coordinates)",
                variable=use_current_position
            ).pack(padx=10, pady=4)

            def save_mouse_action():
                text = raw_var.get().strip()
                if use_current_position.get():
                    text = re.sub(r" at: \(\d+, \d+\)", "", text)
                self.item(item_id, text=text)
                print(f"Updated mouse action to: {text}")
                edit_win.destroy()

            tk.Button(edit_win, text="Save", command=save_mouse_action).pack(side=tk.LEFT, padx=10, pady=10)
            tk.Button(edit_win, text="Cancel", command=edit_win.destroy).pack(side=tk.RIGHT, padx=10, pady=10)
            return

        if " - " in full_text and not ":" in full_text:
            time_part, content = full_text.split(" - ", 1)
            simple_win = tk.Toplevel(self)
            simple_win.title("Edit Item")
            simple_win.grab_set()

            time_var = tk.StringVar(value=time_part)
            content_var = tk.StringVar(value=content)

            tk.Label(simple_win, text="Time:").grid(row=0, column=0, sticky="e")
            tk.Entry(simple_win, textvariable=time_var, width=10).grid(row=0, column=1)

            tk.Label(simple_win, text="Text:").grid(row=1, column=0, sticky="e")
            tk.Entry(simple_win, textvariable=content_var, width=50).grid(row=1, column=1)

            def save_simple():
                try:
                    new_time = float(time_var.get())
                    new_text = f"{new_time:.3f} - {content_var.get().strip()}"
                    self.item(item_id, text=new_text)
                    simple_win.destroy()
                except:
                    tk.messagebox.showerror("Invalid time", "Time must be a float.")

            tk.Button(simple_win, text="Save", command=save_simple).grid(row=2, column=0, pady=6)
            tk.Button(simple_win, text="Cancel", command=simple_win.destroy).grid(row=2, column=1, pady=6, sticky="e")
            return

        def safe_split(s):
            parts = []
            current = ""
            depth = 0
            for char in s:
                if char == ',' and depth == 0:
                    parts.append(current.strip())
                    current = ""
                else:
                    current += char
                    if char in "([{":
                        depth += 1
                    elif char in ")]}":
                        depth -= 1
            if current:
                parts.append(current.strip())
            return parts

        pairs = safe_split(full_text)
        key_value_pairs = []
        for pair in pairs:
            if ":" in pair:
                key, val = pair.split(":", 1)
                key_value_pairs.append((key.strip(), val.strip()))
            else:
                key_value_pairs.append((pair.strip(), ""))

        edit_win = tk.Toplevel(self)
        edit_win.title("Edit Structured Item")
        edit_win.grab_set()
        edit_win.resizable(False, False)

        entries = []
        for i, (key, val) in enumerate(key_value_pairs):
            tk.Label(edit_win, text=key + ":").grid(row=i, column=0, sticky="e", padx=5, pady=3)
            var = tk.StringVar(value=val)
            entry = tk.Entry(edit_win, textvariable=var, width=60)
            entry.grid(row=i, column=1, padx=5, pady=3)
            entries.append((key, var))

        def save_advanced():
            new_parts = [f"{key}: {var.get().strip()}" for key, var in entries]
            new_text = ", ".join(new_parts)
            self.item(item_id, text=new_text)
            print(f"Updated structured item to:\n{new_text}")
            edit_win.destroy()

        tk.Button(edit_win, text="Save", command=save_advanced).grid(row=len(entries), column=0, pady=10)
        tk.Button(edit_win, text="Cancel", command=edit_win.destroy).grid(row=len(entries), column=1, pady=10, sticky="e")


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