"""
Go To dialog for adding jump events to macros.
"""
import tkinter as tk
from tkinter import Toplevel, Entry, Label, Button, ttk, messagebox
import re
from . import bind_enter_key


def open_goto_window(parent, coords_callback, checkpoints=None, treeview=None, initial_values=None):
    """Open the Go To settings window."""
    iv = initial_values or {}
    item_id = iv.get("item_id") or iv.get("item_number")
    
    goto_window = Toplevel(parent)
    goto_window.title("Go To" if not item_id else "Edit Go To")
    
    screen_width = goto_window.winfo_screenwidth()
    screen_height = goto_window.winfo_screenheight()
    window_width = int(screen_width * 0.4)
    window_height = int(screen_height * 0.3)
    goto_window.geometry(f"{window_width}x{window_height}")
    goto_window.attributes("-topmost", True)

    # Type selection
    Label(goto_window, text="Go To Type:").pack(pady=5)
    goto_type_var = tk.StringVar(value="Checkpoint")
    type_frame = tk.Frame(goto_window)
    type_frame.pack(pady=5)
    tk.Radiobutton(type_frame, text="Checkpoint", variable=goto_type_var, value="Checkpoint").pack(side=tk.LEFT, padx=10)
    tk.Radiobutton(type_frame, text="Line Number", variable=goto_type_var, value="Line").pack(side=tk.LEFT, padx=10)

    # Checkpoint selection
    checkpoint_frame = tk.Frame(goto_window)
    checkpoint_label = Label(checkpoint_frame, text="Checkpoint:")
    checkpoint_var = tk.StringVar()
    checkpoint_dropdown = ttk.Combobox(checkpoint_frame, textvariable=checkpoint_var, state="readonly")
    
    # Line number selection
    line_label = Label(goto_window, text="Line Number:")
    line_entry = Entry(goto_window, width=10)
    element_label = Label(goto_window, text="(Element will be saved)", fg="gray")

    # Warning label for line number changes
    warning_label = Label(goto_window, text="", fg="red")

    # OK button (used as anchor point)
    ok_button = Button(goto_window, text="OK", command=lambda: None)
    ok_button.pack(pady=10)

    def update_ui():
        """Update UI based on selected type."""
        goto_type = goto_type_var.get()
        
        # Unpack everything first
        checkpoint_frame.pack_forget()
        checkpoint_label.pack_forget()
        checkpoint_dropdown.pack_forget()
        line_label.pack_forget()
        line_entry.pack_forget()
        element_label.pack_forget()
        warning_label.pack_forget()
        
        if goto_type == "Checkpoint":
            checkpoint_label.pack(side=tk.LEFT, padx=5)
            checkpoint_dropdown.pack(side=tk.LEFT, padx=5)
            checkpoint_frame.pack(pady=5, before=ok_button)
        else:  # Line
            line_label.pack(pady=5, before=ok_button)
            line_entry.pack(pady=5, before=ok_button)
            element_label.pack(pady=5, before=ok_button)
            warning_label.pack(pady=5, before=ok_button)
            # Update element label if line is set
            try:
                line_num = int(line_entry.get())
                if treeview and 0 <= line_num < len(treeview.get_children()):
                    children = treeview.get_children()
                    element_text = treeview.item(children[line_num])["text"]
                    element_label.config(text=f"Element: {element_text[:50]}...", fg="black")
                    warning_label.config(text="")
                else:
                    element_label.config(text="(Invalid line number)", fg="red")
            except (ValueError, IndexError):
                element_label.config(text="(Enter valid line number)", fg="gray")

    goto_type_var.trace("w", lambda *args: update_ui())
    line_entry.bind("<KeyRelease>", lambda e: update_ui())

    # Populate checkpoints
    if checkpoints:
        checkpoint_dropdown['values'] = list(checkpoints.keys())
        if checkpoint_dropdown['values']:
            checkpoint_var.set(checkpoint_dropdown['values'][0])

    # Populate from initial_values if editing
    if iv:
        if "goto_type" in iv:
            goto_type_var.set(iv["goto_type"])
        if "checkpoint" in iv:
            checkpoint_var.set(iv["checkpoint"])
        if "line_number" in iv:
            line_entry.insert(0, str(iv["line_number"]))
        if "element_text" in iv:
            element_label.config(text=f"Saved Element: {iv['element_text'][:50]}...", fg="blue")
            # Check if element changed
            if treeview and "line_number" in iv:
                try:
                    line_num = int(iv["line_number"])
                    children = treeview.get_children()
                    if 0 <= line_num < len(children):
                        current_element = treeview.item(children[line_num])["text"]
                        if current_element != iv["element_text"]:
                            warning_label.config(
                                text=f"WARNING: Element at line {line_num} has changed!",
                                fg="red"
                            )
                except (ValueError, IndexError):
                    pass
        update_ui()

    def save_goto_event():
        """Save the Go To event."""
        goto_type = goto_type_var.get()
        
        if goto_type == "Checkpoint":
            checkpoint_name = checkpoint_var.get().strip()
            if not checkpoint_name:
                messagebox.showerror("Error", "Please select a checkpoint.", parent=goto_window)
                return
            event = f"Go To - Target: {checkpoint_name}"
            values = (goto_type, checkpoint_name, None, None)
        else:  # Line
            try:
                line_num = int(line_entry.get().strip())
                if line_num < 0:
                    messagebox.showerror("Error", "Line number must be non-negative.", parent=goto_window)
                    return
                if treeview:
                    children = treeview.get_children()
                    if line_num >= len(children):
                        messagebox.showerror("Error", f"Line number {line_num} is out of range. Maximum: {len(children)-1}", parent=goto_window)
                        return
                    element_text = treeview.item(children[line_num])["text"]
                else:
                    element_text = iv.get("element_text", "")
                event = f"Go To - Line: {line_num}, Element: {element_text}"
                values = (goto_type, None, line_num, element_text)
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid line number.", parent=goto_window)
                return

        if item_id is not None:
            coords_callback(event, item_id=item_id, values=values)
        else:
            coords_callback(event, values=values)
        
        goto_window.destroy()

    ok_button.config(command=save_goto_event)
    update_ui()
    
    # Bind Enter key and set focus
    def set_focus():
        widget = line_entry if goto_type_var.get() == "Line" else checkpoint_dropdown
        widget.focus_set()
    bind_enter_key(goto_window, save_goto_event, line_entry if goto_type_var.get() == "Line" else checkpoint_dropdown)
    # Update focus when type changes
    goto_type_var.trace("w", lambda *args: set_focus())

