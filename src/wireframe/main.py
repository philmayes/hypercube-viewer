#! python3.10
# -*- coding: utf-8 -*-

import argparse
from functools import partial
import tkinter as tk
from tkinter import ttk
from xmlrpc.client import Boolean

import cv2

import colors
import display
import wireframe as wf

MAX_DIM = 10
planes = [
    (0, 1),
    (0, 2),
    (1, 2),
]
for dim in range(3, MAX_DIM):
    planes.append((0, dim))
    planes.append((1, dim))
labels = ('X', 'Y', 'Z', '4', '5', '6', '7', '8', '9', '10')
# dim_choices = ['3','4','5','6','7','8','9','10']

class DimControl:
    """A class to manage tkinter controls for a single plane."""

    def __init__(self, frame, row, dim1, dim2, app):
        self.dim1 = dim1
        self.dim2 = dim2
        text = f'{labels[dim1]}-{labels[dim2]}'
        ctl = tk.Label(frame, text=text)
        ctl.grid(row=row, column=0, sticky=tk.EW, padx=2, pady=2)

        # insert rotation controls
        # create a subframe and place it as requested
        rot_frame = tk.Frame(frame)
        rot_frame.grid(row=row, column=1)
        self.rotate1 = tk.Button(rot_frame, text=' < ', command=partial(app.on_rotate, '-', self))
        self.rotate1.grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        self.rotate2 = tk.Button(rot_frame, text=' > ', command=partial(app.on_rotate, '+', self))
        self.rotate2.grid(row=0, column=1, sticky=tk.W, padx=2, pady=2)

        # insert information about colors of dimensions
        color = colors.html[dim1]
        self.color1 = tk.Label(frame, text='color', bg='black', fg=color)
        self.color1.grid(row=row, column=2, sticky=tk.EW)
        color = colors.html[dim2]
        self.color2 = tk.Label(frame, text='color', bg='black', fg=color)
        self.color2.grid(row=row, column=3, sticky=tk.EW)

    def enable(self, dim_size: int):
        applicable = self.dim1 < dim_size and self.dim2 < dim_size
        state = tk.ACTIVE if applicable else tk.DISABLED
        self.rotate1.configure(state=state)
        self.rotate2.configure(state=state)
        if applicable:
            self.color1.grid()
            self.color2.grid()
        else:
            self.color1.grid_remove()
            self.color2.grid_remove()

class App(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.max_dim = 6
        self.dim_controls = []
        self.grid(sticky=tk.NSEW)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.winfo_toplevel().title('Wireframe')
        self.big_font = ('calibri', 16, 'bold')

        # create a frame for controls and add them
        self.left_frame = tk.Frame(self)
        self.left_frame.grid(row=0, column=0, rowspan=1, sticky=tk.NW)
        self.add_user_controls(self.left_frame, 0, 0)

        # create a frame for display
        self.right_frame = tk.Frame(self)
        self.right_frame.grid(row=0, column=1, rowspan=1, sticky=tk.NE)
        self.widget = tk.Label(self.right_frame)
        self.widget.grid(row=0, column=0, sticky=tk.N)

        self.viewer = display.Viewer(1920, 1080, self.widget)
        self.set_dim(6)

    def add_dim_controls(self, parent_frame, row, col):
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col)
        row = 0
        # add heading
        ctl = tk.Label(frame, text='CONTROLS', font=self.big_font)
        ctl.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1
        labels = (
            'Plane of\nRotation',
            'Direction of\nRotation',
            'Color of 1st\nDimension',
            'Color of 2nd\nDimension',
            )
        for col, label in enumerate(labels):
            ctl = tk.Label(frame, text=label)
            ctl.grid(row=row, column=col, sticky=tk.W, padx=2, pady=2)
        row += 1

        for plane in planes:
            self.dim_controls.append(DimControl(frame, row, plane[0], plane[1], self))
            row += 1

    def add_user_controls(self, parent_frame, row, col):
        """Add user control buttons to the window."""
        # create a subframe and place it as requested
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, padx=2)
        row = 0
        # add heading
        ctl = tk.Label(frame, text='SET UP', font=self.big_font)
        ctl.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1

        # add choice of number of dimensions
        self.dim_choice = ttk.Combobox(frame,
                          state='readonly',
                          values=[str(n+1) for n in range(2, MAX_DIM)],
                          )
        self.dim_choice.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        self.dim_choice.bind('<<ComboboxSelected>>', self.on_dim)
        row += 1

        rb = tk.Button(frame, text='Load', command=self.on_load)
        rb.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1
        self.ghost = tk.Scale(frame, to=1.0,
                              resolution=0.05,
                              orient=tk.HORIZONTAL,
                              command=self.on_ghost)
        self.ghost.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1
        rb = ttk.Button(frame, text='Dn', command=partial(self.move_user, 1))
        rb.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1

        # add rotation controls
        self.add_dim_controls(frame, row, 0)
        row += 1

        rb = tk.Button(frame, text='Start', font=self.big_font, command=self.on_run)
        rb.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1

    def move_user(self, direction):
        """Move the selected user up or down one place in the list."""
        pass

    def on_dim(self, param):
        """User has selected the number of dimensions via the combo box."""
        dim = int(param.widget.get())
        self.set_dim(dim)

    def on_ghost(self, value):
##        value = self.ghost.get()
        display.GHOST = value

    def on_load(self):
        self.viewer.run()

    def on_rotate(self, direction, dim_control):
        """Rotate the wireframe."""
        # print('on_rotate', direction)
        # dim1 = dim_control.rot_axis.get()
        # dim2 = dim_control.dim
        action = f'R{dim_control.dim1}{dim_control.dim2}{direction}'
        print(f'{action = }')
        self.viewer.take_action(action)

    def on_run(self):
        """The Start/Pause/Continue button has been clicked."""
        pass

    def set_dim(self, dim):
        """Set the number of dimensions to use."""
        self.dim_choice.set(str(dim))
        for control in self.dim_controls:
            control.enable(dim)
        self.viewer.init(dim)
        self.viewer.display()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multi-dimensional cube')
    parser.add_argument("-t", "--test", action="store_true", help="run in test mode")
    args = parser.parse_args()
    app = App()
    app.mainloop()

