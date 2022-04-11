#! python3.9
# -*- coding: utf-8 -*-

import argparse
from functools import partial
import tkinter as tk

import cv2

import colors
import display
import wireframe as wf

class DimControl:
    """A class to manage tkinter controls for a single dimension."""

    labels = ('X', 'Y', 'Z', '4', '5', '6', '7', '8', '9', '10')

    def __init__(self, frame, dim, app):
##        self.frame = frame
        self.dim = dim
        # add 1 to the row because the headings occupy row 0
        row = dim + 1
        self.rot_axis = tk.IntVar(value=int(1 ^ dim & 1))
        # label the dimension
        ctl = tk.Label(frame, text=DimControl.labels[dim])
        ctl.grid(row=row, column=0, sticky=tk.EW, padx=2, pady=2)

        # insert rotation controls
        # create a subframe and place it as requested
        rot_frame = tk.Frame(frame)
        rot_frame.grid(row=row, column=1)
        rb = tk.Button(rot_frame, text='<', command=partial(app.on_rotate, -1, self))
        rb.grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        rb = tk.Button(rot_frame, text='>', command=partial(app.on_rotate, 1, self))
        rb.grid(row=0, column=1, sticky=tk.W, padx=2, pady=2)

        # insert rotation axis
        # see explanation in display.key_to_function
        axis_frame = tk.Frame(frame)
        axis_frame.grid(row=row, column=2, padx=4)
        rb1 = tk.Radiobutton(axis_frame, text='X', indicatoron=0, value=0, variable=self.rot_axis)
        rb1.grid(row=0, column=0, sticky=tk.W, padx=0, pady=2)
        rb2 = tk.Radiobutton(axis_frame, text='Y', indicatoron=0, value=1, variable=self.rot_axis)
        rb2.grid(row=0, column=1, sticky=tk.W, padx=0, pady=2)
        # special cases:
        if dim == 0:
            rb1.configure(state = tk.DISABLED)
        elif dim == 1:
            rb2.configure(state = tk.DISABLED)

        # insert information about color of dimension
        color = colors.html[dim]
        ctl = tk.Label(frame, text='color',
                              background='black',
                              foreground=color)
        ctl.grid(row=row, column=3, sticky=tk.EW, padx=2, pady=2)


class App(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.max_dim = 6
        self.dim_controls = [None] * self.max_dim
        self.grid(sticky=tk.NSEW)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.winfo_toplevel().title('Wireframe')

        # create a frame for controls
        self.left_frame = tk.Frame(self)
        self.left_frame.grid(row=0, column=0, rowspan=1, sticky=tk.NW)

        # create a frame for display
        self.right_frame = tk.Frame(self)
        self.right_frame.grid(row=0, column=1, rowspan=1, sticky=tk.NE)
        self.widget = tk.Label(self.right_frame)
        self.widget.grid(row=0, column=0, sticky=tk.N)

        # create tkinter controls:
        self.add_user_controls(self.left_frame, 0, 0)
        self.viewer = display.Viewer(1920, 1080, self.widget)
        self.viewer.display()

    def add_user_controls(self, parent_frame, row, col):
        """Add user control buttons to the window."""
        # create a subframe and place it as requested
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col)
        row = 0
        rb = tk.Button(frame, text='Load', command=self.on_load)
        rb.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1
        self.ghost = tk.Scale(frame, to=1.0,
                              resolution=0.05,
                              orient=tk.HORIZONTAL,
                              command=self.on_ghost)
        self.ghost.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1
        rb = tk.Button(frame, text='Dn', command=partial(self.move_user, 1))
        rb.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1
        self.add_dim_controls(frame, row, 0)
        row += 1
        font = ('calibri', 16, 'bold')
        rb = tk.Button(frame, text='Start', font=font, command=self.on_run)
        rb.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1

    def add_dim_controls(self, parent_frame, row, col):
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col)
        labels = (
            'Dimension',
            'Direction of\nrotation',
            'Rotate\naround',
            'Color of\nDimension',
            )
        row = 0
        for col, label in enumerate(labels):
            ctl = tk.Label(frame, text=label)
            ctl.grid(row=row, column=col, sticky=tk.W, padx=2, pady=2)
        row += 1

        for dim in range(self.max_dim):
            self.dim_controls[dim] = DimControl(frame, dim, self)

    def move_user(self, direction):
        """Move the selected user up or down one place in the list."""
        pass

    def on_ghost(self, value):
##        value = self.ghost.get()
        display.GHOST = value

    def on_load(self):
        self.viewer.run()

    def on_rotate(self, direction, dim_control):
        """Move the selected user up or down one place in the list."""
        print('on_rotate', direction)
        dim = dim_control.dim
        dim1 = 0 if dim else 0
        rot = '+' if dim_control.rot_axis.get() > 0 else '-'
        key = f'R{dim1}{dim}{rot}'
        print(f'{key = }')
        self.viewer.take_action(key)

    def on_run(self):
        """The Start/Pause/Continue button has been clicked."""
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multi-dimensional cube')
    parser.add_argument("-t", "--test", action="store_true", help="run in test mode")
    args = parser.parse_args()
##    if testing or args.test:
##        set_test()
##        print('testing')
    app = App()
    app.mainloop()


