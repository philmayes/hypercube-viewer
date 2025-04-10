# -*- coding: utf-8 -*-

from functools import partial
import tkinter as tk
from tkinter import ttk

import colors
import dims
import hints

# Names for the states of buttons. Values are indices into lists.
DISABLED = 0
ENABLED = 1
ACTIVE = 2


class Button(tk.Button):
    """Class to implement a 3-state button."""

    tk_states = (tk.DISABLED, tk.NORMAL, tk.NORMAL)

    def __init__(self, parent, **kwargs):
        # User can supply a list of texts for the 3 states.
        # If this is supplied, there is no need to supply the standard text
        self.texts = kwargs.pop("texts", [])
        if self.texts:
            kwargs["text"] = self.texts[1]
        else:
            self.texts = None

        # user can supply a custom color for ENABLED and/or ACTIVE states
        colors = None
        color1 = kwargs.pop("color1", None)
        color2 = kwargs.pop("color2", None)
        if color1 or color2:
            colors = ["SystemButtonFace"] * 3
            if color1:
                colors[ENABLED] = color1
            if color2:
                colors[ACTIVE] = color2
        self.colors = colors

        super().__init__(parent, **kwargs)
        self._state = ENABLED

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        assert isinstance(state, int)
        if state != self._state:
            self._state = state
            kwargs = {"state": Button.tk_states[state]}
            if self.colors:
                kwargs["bg"] = self.colors[state]
            if self.texts:
                kwargs["text"] = self.texts[state]
            self.configure(**kwargs)


class Control:
    """Abstract base class for widgets."""

    """Base class for customized widgets."""

    def __init__(self, label):
        self.label = label
        self.callback = None
        self.dataname = ''
        # child classes will set .ctl to a tk control 
        self.ctl = None
        self.datatype = type
        self.int_var = tk.IntVar()
        self.float_var = tk.DoubleVar()
        self.str_var = tk.StringVar()

    def action(self, x=None):
        if self.callback is not None:
            # condition is always satisfied; test is to keep lint happy
            self.callback(self.dataname)

    def get(self):
        if self.datatype is int or self.datatype is bool:
            return self.int_var.get()
        elif self.datatype is float:
            return self.float_var.get()
        elif self.datatype is str:
            return self.str_var.get()
        else:
            raise TypeError

    def set(self, value):
        # ctl is a ttk.Checkbutton, ttk.Combobox or tk.Scale,
        # so ignore lint complaint
        self.ctl.set(value) # type: ignore

    def set_data(self, dataname: str, data):
        """Construct a tkinter variable that is compatible with our data."""
        self.dataname = dataname
        value = getattr(data, dataname)
        self.datatype = type(value)


class CheckControl(Control):
    """Class to manage a ttk.CheckButton widget."""

    def __init__(self, label, underline=-1):
        self.underline = underline
        super().__init__(label)

    def add_control(self, frame, row, col, **kwargs):
        self.ctl = ttk.Checkbutton(
            frame, text=self.label, variable=self.int_var, underline=self.underline, command=self.action
        )
        self.ctl.grid(row=row, column=col, sticky=tk.W, **kwargs)
        hints.set_hint_for_ctl(self.ctl, self.dataname)

    def set(self, value):
        if isinstance(value, str):
            value = 1 if value == "True" else 0
        else:
            value = int(value)
        self.int_var.set(value)

    def xor(self):
        self.int_var.set(self.int_var.get() ^ 1)


class ComboControl(Control):
    """Class to manage a ttk.Combobox widget."""

    def __init__(self, label, values):
        self.values = values
        super().__init__(label)

    def add_control(self, frame, row, col, **kwargs):
        ctl = tk.Label(frame, text=self.label)
        ctl.grid(row=row, column=0, sticky=tk.SW)
        self.ctl = ttk.Combobox(
            frame,
            state="readonly",
            width=4,
            values=self.values,
        )
        self.ctl.grid(row=row, column=col, sticky=tk.W, **kwargs)
        self.ctl.bind("<<ComboboxSelected>>", self.action)
        hints.set_hint_for_ctl(self.ctl, self.dataname)

    def get(self):
        return self.ctl.get()


class SlideControl(Control):
    """Class to manage a tk.Scale widget."""

    def __init__(self, label, from_, to, res):
        self.fr = from_
        self.to = to
        self.res = res
        super().__init__(label)

    def add_control(self, frame, row, col, **kwargs):
        ctl = tk.Label(frame, text=self.label)
        ctl.grid(row=row, column=col - 1, sticky=tk.SW)
        self.ctl = tk.Scale(
            frame,
            from_=self.fr,
            to=self.to,
            resolution=self.res,
            orient=tk.HORIZONTAL,
            command=self.action,
        )
        self.ctl.grid(row=row, column=col, sticky=tk.W, **kwargs)
        hints.set_hint_for_ctl(self.ctl, self.dataname)

    def get(self):
        return self.ctl.get()

    def step(self, units):
        """Step the number of units specified."""
        self.ctl.set(self.ctl.get() + self.res * units)

class PlaneControl:
    """A class to manage tkinter controls for a single plane."""

    def __init__(self, frame, row, dim1, dim2, app):
        self.frame = frame
        self.row = row
        self.dim1 = dim1
        self.dim2 = dim2
        self.app = app
        self.active = False

    def add_controls(self):
        dim1str = dims.labels[self.dim1]
        dim2str = dims.labels[self.dim2]
        text = f"{dim1str}-{dim2str}"
        self.planes = tk.Label(self.frame, text=text)
        self.planes.grid(row=self.row, column=0, sticky=tk.EW, padx=2, pady=2)

        # create a subframe for the rotation controls
        self.rot_frame = tk.Frame(self.frame)
        self.rot_frame.grid(row=self.row, column=1)

        # insert rotation controls
        self.rotate1 = tk.Button(
            self.rot_frame, text=" < ", command=partial(self.app.on_rotate, "+", self)
        )
        self.rotate1.grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        hints.set_hint_for_ctl(self.rotate1, "rotate")
        self.rotate2 = tk.Button(
            self.rot_frame, text=" > ", command=partial(self.app.on_rotate, "-", self)
        )
        self.rotate2.grid(row=0, column=1, sticky=tk.W, padx=2, pady=2)
        hints.set_hint_for_ctl(self.rotate2, "rotate")

        # insert information about colors of dimensions
        self.swatch1 = tk.Label(self.frame, text=f"{dim1str}: ████", bg=colors.html_bg)
        self.swatch1.grid(row=self.row, column=2, sticky=tk.NSEW)
        self.swatch2 = tk.Label(self.frame, text=f"{dim2str}: ████", bg=colors.html_bg)
        self.swatch2.grid(row=self.row, column=3, sticky=tk.NSEW)
        self.swatch3 = tk.Label(self.frame, text=f"████", bg=colors.html_bg)
        self.swatch3.grid(row=self.row, column=4, sticky=tk.NSEW)
        self.active = True
        # self.show_colors()

    def delete_controls(self):
        self.rot_frame.destroy()
        self.planes.destroy()
        self.rotate1.destroy()
        self.rotate2.destroy()
        self.swatch1.destroy()
        self.swatch2.destroy()
        self.swatch3.destroy()
        self.active = False

    def show_colors(self, data):
        if self.active:
            no_color = colors.html_bg
            if data.show_edges:
                if data.show_4_gray and (self.dim1 > 2 or self.dim2 > 2):
                    color1 = color2 = colors.html_dim4gray
                else:
                    color1 = colors.html[self.dim1]
                    color2 = colors.html[self.dim2]
            else:
                color1 = color2 = no_color
            if data.show_faces:
                bgr = colors.face([self.dim1, self.dim2])
                color3 = colors.bgr_to_html(*bgr)
            else:
                color3 = no_color
            self.swatch1.configure(fg=color1)
            self.swatch2.configure(fg=color2)
            self.swatch3.configure(fg=color3)