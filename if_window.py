# if_window.py
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox

def open_if_window(parent, coords_callback, variables, initial_values=None):
    """Open the If condition window. Edit mode auto-detected from initial_values['item_id'/'item_number']."""
    iv = initial_values or {}
    item_id = iv.get("item_id") or iv.get("item_number")

    win = tk.Toplevel(parent)
    win.title("If Condition")
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{int(sw*0.4)}x{int(sh*0.5)}")
    win.attributes("-topmost", True)

    # ---- UI ----
    tk.Label(win, text="Define If Condition").pack(pady=5)

    # Variable dropdown
    tk.Label(win, text="Select Variable:").pack(pady=5)
    time_vars = ["time_hour","time_minute","time_second","time_weekday","time_day","time_month","time_year"]
    user_vars = list(variables.keys()) if isinstance(variables, dict) else list(variables or [])
    var_names = time_vars + user_vars
    variable_dropdown = ttk.Combobox(win, values=var_names or ["None"], state="readonly")
    variable_dropdown.set((var_names or ["None"])[0])
    variable_dropdown.pack(pady=5)

    # Condition
    tk.Label(win, text="Condition:").pack(pady=5)
    condition_dropdown = ttk.Combobox(win, values=["==", ">", "<", ">=", "<=", "!=", "Contains", "%"], state="readonly")
    condition_dropdown.set("==")
    condition_dropdown.pack(pady=5)

    # Value
    tk.Label(win, text="Value (string or number):").pack(pady=5)
    value_entry = tk.Entry(win)
    value_entry.pack(pady=5)

    # ---- Succeed row ----
    tk.Label(win, text="If Succeed, Go To:").pack(pady=5)
    succeed_frame = tk.Frame(win); succeed_frame.pack(pady=5)
    succeed_send_var = tk.BooleanVar(value=False)
    tk.Checkbutton(succeed_frame, text="Send Notification",
                   variable=succeed_send_var,
                   command=lambda: toggle_notification('succeed')).grid(row=0, column=0, padx=5)

    # derive checkpoints/notifications safely
    try:
        checkpoints = ["Next"] + list(getattr(parent, "checkpoints", {}) or {})
    except Exception:
        checkpoints = ["Next"]
    try:
        notifications = ["None"] + list(getattr(getattr(getattr(parent, "master", None), "master", None), "page2", None).__dict__.get("notifications", {}) or {})
    except Exception:
        notifications = ["None"]

    succeed_checkpoint_dropdown = ttk.Combobox(succeed_frame, values=checkpoints, state="readonly")
    succeed_checkpoint_dropdown.set("Next")
    succeed_checkpoint_dropdown.grid(row=0, column=1, padx=5)
    succeed_notification_dropdown = ttk.Combobox(succeed_frame, values=notifications, state="disabled")
    succeed_notification_dropdown.set("None")
    succeed_notification_dropdown.grid(row=0, column=2, padx=5)

    # ---- Fail row ----
    tk.Label(win, text="If Failed, Go To:").pack(pady=5)
    fail_frame = tk.Frame(win); fail_frame.pack(pady=5)
    fail_send_var = tk.BooleanVar(value=False)
    tk.Checkbutton(fail_frame, text="Send Notification",
                   variable=fail_send_var,
                   command=lambda: toggle_notification('fail')).grid(row=0, column=0, padx=5)

    fail_checkpoint_dropdown = ttk.Combobox(fail_frame, values=checkpoints, state="readonly")
    fail_checkpoint_dropdown.set("Next")
    fail_checkpoint_dropdown.grid(row=0, column=1, padx=5)
    fail_notification_dropdown = ttk.Combobox(fail_frame, values=notifications, state="disabled")
    fail_notification_dropdown.set("None")
    fail_notification_dropdown.grid(row=0, column=2, padx=5)

    # Wait time
    tk.Label(win, text="Wait Time if Failed (seconds):").pack(pady=5)
    wait_time_entry = tk.Entry(win); wait_time_entry.insert(0, "5"); wait_time_entry.pack(pady=5)

    def toggle_notification(mode):
        if mode == 'succeed':
            succeed_notification_dropdown.config(state="readonly" if succeed_send_var.get() else "disabled")
        elif mode == 'fail':
            fail_notification_dropdown.config(state="readonly" if fail_send_var.get() else "disabled")

    # ---- Populate from initial_values (if editing) ----
    if iv:
        # variable / condition / value (support multiple key casings)
        vname = iv.get("variable") or iv.get("Variable")
        cond  = iv.get("condition") or iv.get("Condition")
        val   = iv.get("value") or iv.get("Value")
        if vname and (vname in var_names or not var_names):
            variable_dropdown.set(vname)
        if cond:
            condition_dropdown.set(cond)
        if val is not None:
            value_entry.delete(0, tk.END); value_entry.insert(0, str(val))

        # succeed/fail goto + notifications
        sc = iv.get("succeed_checkpoint") or iv.get("Succeed Go To")
        fc = iv.get("fail_checkpoint")    or iv.get("Fail Go To")
        if sc: succeed_checkpoint_dropdown.set(sc)
        if fc: fail_checkpoint_dropdown.set(fc)

        # booleans (or infer from presence of notifications)
        ss = iv.get("succeed_send")
        fs = iv.get("fail_send")
        if ss is None: ss = (iv.get("succeed_notification") or iv.get("Succeed Notification")) not in (None, "", "None")
        if fs is None: fs = (iv.get("fail_notification") or iv.get("Fail Notification")) not in (None, "", "None")
        succeed_send_var.set(bool(ss))
        fail_send_var.set(bool(fs))

        sn = iv.get("succeed_notification") or iv.get("Succeed Notification")
        fn = iv.get("fail_notification") or iv.get("Fail Notification")
        if sn: succeed_notification_dropdown.set(sn)
        if fn: fail_notification_dropdown.set(fn)
        toggle_notification('succeed'); toggle_notification('fail')

        # wait time
        wt = iv.get("wait_time") or iv.get("Wait")
        if wt:
            wt_str = str(wt).rstrip("s")
            wait_time_entry.delete(0, tk.END); wait_time_entry.insert(0, wt_str)

    # ---- Save ----
    def save_if_event():
        try:
            variable_name = variable_dropdown.get()
            if variable_name == "None":
                messagebox.showerror("Missing Variable", "Please select a variable.")
                return

            condition = condition_dropdown.get()
            value = value_entry.get().strip()
            succeed_checkpoint = succeed_checkpoint_dropdown.get()
            fail_checkpoint = fail_checkpoint_dropdown.get()
            succeed_send = succeed_send_var.get()
            succeed_notification = succeed_notification_dropdown.get() or "None"
            fail_send = fail_send_var.get()
            fail_notification = fail_notification_dropdown.get() or "None"
            wait_time = float(wait_time_entry.get())

            event = (f"If {variable_name} {condition} {value}, "
                     f"Succeed Go To: {succeed_checkpoint}, "
                     f"Fail Go To: {fail_checkpoint}, "
                     f"Wait: {wait_time}s")
            if succeed_send and succeed_notification != "None":
                event += f", Succeed Notification: {succeed_notification}"
            if fail_send and fail_notification != "None":
                event += f", Fail Notification: {fail_notification}"

            values = (
                variable_name, condition, value,
                succeed_checkpoint, fail_checkpoint,
                str(succeed_send), succeed_notification,
                str(fail_send), fail_notification,
                str(wait_time)
            )

            if item_id is not None:
                coords_callback(event, item_id=item_id, values=values)
            else:
                coords_callback(event, values=values)

            print(f"{'Updated' if item_id is not None else 'Added'} If event: {event}")
            win.destroy()

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for wait time.")
        except Exception as e:
            print(f"Error saving if event: {type(e).__name__}: {e}")

    tk.Button(win, text="OK", command=save_if_event).pack(pady=10)
