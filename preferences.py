import copy
from functools import partial
import tkinter as tk

import pubsub

class Preferences(tk.Toplevel):
    def __init__(self, data, win_x, win_y):
        super().__init__(None)
        self.transient(None)
        self.title("Preferences")
        self.grab_set()
        self.focus()
        self.geometry(f'+{win_x + 100}+{win_y + 100}')
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        frame = tk.Frame(self)
        frame.grid(row=0, column=0, padx=4, pady=4)

        # Make a copy of the data so we don't trample on existing values.
        # The copy is returned via pubsub if the user accepts the changes.
        self.data = copy.copy(data)

        # make the controls
        big_font = ("calibri", 14, "bold")
        row = 0
        ctl = tk.Label(frame, text="VISIBILITY", font=big_font, fg="red3")
        ctl.grid(row=row, column=0, sticky=tk.W, pady=2)
        row += 1
        for values in (
            ("node_radius", "Corner radius (1-9):", 1, 9),
            ("center_radius", "Center radius (1-9):", 1, 9),
            ("vp_radius", "Vanishing point radius (1-9):", 1, 9),
            ("edge_width", "Line width (1-9):", 1, 9),
        ):
            self.add_control(frame, row, *values)
            row += 1
        frame2 = tk.Frame(frame)
        frame2.grid(row=row, columnspan=2, sticky=tk.E)
        self.ok = tk.Button(frame2, width=10, text="OK", command=self.on_ok)
        self.ok.grid(row=0, column=0, padx=4, pady=4)
        ctl = tk.Button(frame2, width=10, text="Cancel", command=self.destroy)
        ctl.grid(row=0, column=1, padx=0, pady=4)

    def add_control(self, frame, row, dataname, label, vmin, vmax):
            text = str(getattr(self.data, dataname))
            ctl = tk.Label(frame, text=label)
            ctl.grid(row=row, column=0, sticky=tk.W, padx=4, pady=4)
            ctl = tk.Entry(frame, width=5)
            ctl.grid(row=row, column=1, sticky=tk.W, padx=4, pady=4)
            ctl.insert(0, text)
            vcmd = (self.register(partial(self.validate, ctl)), '%P')
            ctl.config(validate="key", validatecommand=vcmd)
            # stash various values in the control for later use
            ctl.dataname = dataname
            ctl.vmin = vmin
            ctl.vmax = vmax

    def on_ok(self):
        """The user is happy with the changes.
        
        We must use pubsub before destroying the dialog because the data
        will also be destroyed.
        """
        pubsub.publish("prefs", self.data)
        self.destroy()

    def validate(self, ctl, value):
        """Validate the control.

        If it is valid:
            set value in copy of data
        else:
            indicate invalid
            disable OK
            tell tkinter it's valid
            (otherwise the invalid value is not shown in the control)
        """
        if value.isdigit():
            value = int(value)
            if ctl.vmin <= value <= ctl.vmax:
                ctl.configure(bg='white')
                self.ok["state"] = tk.NORMAL
                setattr(self.data, ctl.dataname, value)
                return True
        ctl.configure(bg='yellow')
        self.ok["state"] = tk.DISABLED
        return True
