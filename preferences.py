import copy
import tkinter as tk

import controls
import pubsub

help4 = """\
Show dimensions
4 and up
differently:"""

class Preferences(tk.Toplevel):
    def __init__(self, data, win_x, win_y):
        super().__init__(None)
        self.transient(None)
        self.title("Preferences")
        self.grab_set()
        self.focus()
        self.geometry(f"+{win_x + 100}+{win_y + 100}")
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
        self.controls = {
            "node_radius": controls.SlideControl("Corner radius:", 1, 9, 1),
            "center_radius": controls.SlideControl("Center radius:", 1, 9, 1),
            "vp_radius": controls.SlideControl("Vanishing point radius:", 1, 9, 1),
            "edge_width": controls.SlideControl("Line width:", 1, 9, 1),
            "font_size": controls.SlideControl("Font size:", 0.2, 2.0, 0.2),
            'show_coords': controls.CheckControl('Show coordinates'),
            "show_node_ids": controls.CheckControl("Show corner numbers"),
            "show_4_narrow": controls.CheckControl("Line width is 1"),
            "show_4_gray": controls.CheckControl("Line color is gray"),
        }
        for dataname, control in self.controls.items():
            control.set_data(dataname, self.data)
            control.add_control(frame, row, 1)
            control.callback = self.on_data
            control.set(getattr(self.data, dataname))
            row += 1

        ctl = tk.Label(frame, text=help4, justify=tk.LEFT)
        ctl.grid(row=row-2, column=0, rowspan=2, sticky=tk.W)

        frame2 = tk.Frame(frame)
        frame2.grid(row=row, columnspan=2, sticky=tk.E)
        self.ok = tk.Button(frame2, width=10, text="OK", command=self.on_ok)
        self.ok.grid(row=0, column=0, padx=4, pady=4)
        ctl = tk.Button(frame2, width=10, text="Cancel", command=self.destroy)
        ctl.grid(row=0, column=1, padx=0, pady=4)

    def on_data(self, dataname):
        control = self.controls.get(dataname, None)
        if control:
            control_value = control.get()
            value = self.data.coerce(control_value, dataname)
            setattr(self.data, dataname, value)

    def on_ok(self):
        """The user is happy with the changes.
        
        We must use pubsub before destroying the dialog because the data
        will also be destroyed.
        """
        pubsub.publish("prefs", self.data)
        self.destroy()
