# -*- coding: utf-8 -*-

from functools import partial
import tkinter as tk
from tkinter import ttk

import colors
import dims

class Control:
    """Abstract base class for widgets."""

    # these get filled in early; it's a lazy way of supplying the same values
    # to all instances
    # callback = None

    """Base class for customized widgets."""
    def __init__(self, label):
        self.label = label
        self.callback = None

    def action(self):
        print('Control.action', self.dataname)
        self.callback(self.dataname)

    def get(self):
        return self.var.get()

    def set(self, value):
        self.ctl.set(value)

    def set_data(self, dataname, data):
        """Construct a tkinter variable that is compatible with our data."""
        self.dataname = dataname
        value = getattr(data, dataname)
        datatype = type(value)
        if datatype is int or datatype is bool:
            self.var = tk.IntVar()
        elif datatype is float:
            self.var = tk.DoubleVar()
        elif datatype is str:
            self.var = tk.StringVar()
        else:
            raise TypeError


class CheckControl(Control):
    """Class to manage a ttk.CheckButton widget."""
    def __init__(self, label):
        super().__init__(label)

    def add_control(self, frame, row, col):
        self.ctl = ttk.Checkbutton(frame, text=self.label, variable=self.var, command=self.action)
        self.ctl.grid(row=row, column=col, sticky=tk.W, pady=0)

    def set(self, value):
        if isinstance(value, str):
            value = 1 if value == 'True' else 0
        else:
            value = int(value)
        self.var.set(value)


class ComboControl(Control):
    """Class to manage a ttk.Combobox widget."""
    def __init__(self, label, values):
        self.values = values
        super().__init__(label)

    def add_control(self, frame, row, col):
        ctl = tk.Label(frame, text=self.label)
        ctl.grid(row=row, column=0, sticky=tk.SW)
        self.ctl = ttk.Combobox(frame,
                           state='readonly',
                           width=4,
                           values=self.values,
                          )
        self.ctl.grid(row=row, column=1, sticky=tk.W, pady=0)
        self.ctl.bind('<<ComboboxSelected>>', self.action)


class SlideControl(Control):
    """Class to manage a tk.Scale widget."""
    def __init__(self, label, from_, to, res):
        self.fr = from_
        self.to = to
        self.res = res
        super().__init__(label)

    def add_control(self, frame, row, col):
        ctl = tk.Label(frame, text=self.label)
        ctl.grid(row=row, column=0, sticky=tk.SW)
        self.ctl = tk.Scale(frame,
                       from_=self.fr,
                       to=self.to,
                       resolution=self.res,
                       orient=tk.HORIZONTAL,
                       command=self.action)
        self.ctl.grid(row=row, column=col, sticky=tk.W, pady=0)

    def action(self, x):
        print('SlideControl.action', self.dataname, x)
        self.callback(self.dataname)

    def get(self):
        return self.ctl.get()

class ButtonPair:
    """Create a pair of buttons that act like radiobuttons."""

    states = (tk.NORMAL, tk.DISABLED)

    def __init__(self, frame, text: list[str], callback, row=0, col=0):
        self.buttons = []
        self.callback = callback
        self.active = 0
        for n in range(2):
            btn = tk.Button(frame, text=text[n], state=ButtonPair.states[n], command=self.passthrough)
            btn.grid(row=row, column=col, sticky=tk.E, padx=2, pady=2)
            col += 1
            self.buttons.append(btn)

    def passthrough(self):
        """Toggle which button is active and pass value to the user."""
        self.active ^= 1
        for n, btn in enumerate(self.buttons):
            btn["state"] = ButtonPair.states[n ^ self.active]
        self.callback(self.active)

    def stop(self):
        """If the control is active, cancel it."""
        if self.active:
            self.passthrough()


class PlaneControl:
    """A class to manage tkinter controls for a single plane."""

    def __init__(self, frame, row, dim1, dim2, app):
        self.frame = frame
        self.row = row
        self.dim1 = dim1
        self.dim2 = dim2
        self.app = app

    def add_controls(self):
        dim1str = dims.labels[self.dim1]
        dim2str = dims.labels[self.dim2]
        color1 = colors.html[self.dim1]
        color2 = colors.html[self.dim2]
        text = f'{dim1str}-{dim2str}'
        self.planes = tk.Label(self.frame, text=text)
        self.planes.grid(row=self.row, column=0, sticky=tk.EW, padx=2, pady=2)

        # create a subframe for the rotation controls
        self.rot_frame = tk.Frame(self.frame)
        self.rot_frame.grid(row=self.row, column=1)

        # insert rotation controls
        self.rotate1 = tk.Button(self.rot_frame, text=' < ', command=partial(self.app.on_rotate, '+', self))
        self.rotate1.grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        self.rotate2 = tk.Button(self.rot_frame, text=' > ', command=partial(self.app.on_rotate, '-', self))
        self.rotate2.grid(row=0, column=1, sticky=tk.W, padx=2, pady=2)

        # insert information about colors of dimensions
        self.swatch1 = tk.Label(self.frame, text=f'{dim1str}: ████', bg='black', fg=color1)
        self.swatch1.grid(row=self.row, column=2, sticky=tk.NSEW)
        self.swatch2 = tk.Label(self.frame, text=f'{dim2str}: ████', bg='black', fg=color2)
        self.swatch2.grid(row=self.row, column=3, sticky=tk.NSEW)

    def delete_controls(self):
        self.rot_frame.destroy()
        self.planes.destroy()
        self.rotate1.destroy()
        self.rotate2.destroy()
        self.swatch1.destroy()
        self.swatch2.destroy()

