#! python3.10
# -*- coding: utf-8 -*-

import argparse
from functools import partial
import tkinter as tk
from tkinter import ttk

import colors
import data
import display

MAX_DIM = 10
# construct all the planes where rotation is visible
planes = [(0, 1), (0, 2), (1, 2)]
for dim in range(3, MAX_DIM):
    planes.append((0, dim))
    planes.append((1, dim))
# construct labels for all dimensions
labels = ['X', 'Y', 'Z']
for dim in range(3, MAX_DIM):
    labels.append(str(dim + 1))

STR_UP = '↑'
STR_DN = '↓'
STR_LEFT = '←'
STR_RIGHT = '→'

class PlaneControl:
    """A class to manage tkinter controls for a single plane."""

    def __init__(self, frame, row, dim1, dim2, app):
        self.dim1 = dim1
        self.dim2 = dim2
        dim1str = labels[dim1]
        dim2str = labels[dim2]
        text = f'{dim1str}-{dim2str}'
        self.planes = tk.Label(frame, text=text)
        self.planes.grid(row=row, column=0, sticky=tk.EW, padx=2, pady=2)

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
        self.color1 = tk.Label(frame, text=f'{dim1str}: ████', bg='black', fg=color)
        self.color1.grid(row=row, column=2, sticky=tk.NSEW)
        color = colors.html[dim2]
        self.color2 = tk.Label(frame, text=f'{dim2str}: ████', bg='black', fg=color)
        self.color2.grid(row=row, column=3, sticky=tk.NSEW)
        tk.NS

    def enable(self, dim_size: int):
        applicable = self.dim1 < dim_size and self.dim2 < dim_size
        state = tk.ACTIVE if applicable else tk.DISABLED
        self.rotate1.configure(state=state)
        self.rotate2.configure(state=state)
        if applicable:
            self.planes.grid()
            self.rotate1.grid()
            self.rotate2.grid()
            self.color1.grid()
            self.color2.grid()
        else:
            self.planes.grid_remove()
            self.rotate1.grid_remove()
            self.rotate2.grid_remove()
            self.color1.grid_remove()
            self.color2.grid_remove()

class App(tk.Frame):
    def __init__(self, root=None):
        tk.Frame.__init__(self, root)
        # set up hooks for program close
        self.root = root
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind('<Escape>', lambda e: self.on_close())

        # create an instance for loading and saving data and get the filename
        # of the json file that holds data (.load_settings() and
        # .save_settings() will perform the actual transfers)
        # This is the canonical version of the persistent data. It is passed
        # into display.Viewer so that App and Viewer share the data.
        self.data = data.Data()
        self.data_file = data.get_location()

        self.max_dim = 6
        self.dim_controls = []
        self.grid(sticky=tk.NSEW)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.winfo_toplevel().title('Hypercube')
        self.big_font = ('calibri', 16, 'bold')
        # self.bind_all('<Key>', self.on_key)

        # create a frame for controls and add them
        self.left_frame = tk.Frame(self)
        self.left_frame.grid(row=0, column=0, sticky=tk.NW)
        self.add_controls(self.left_frame, 0, 0)

        # create a frame for display
        self.right_frame = tk.Frame(self)
        self.right_frame.grid(row=0, column=1, sticky=tk.NE)
        self.canvas = tk.Canvas(self.right_frame, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)

        self.viewer = display.Viewer(self.data, self.canvas)

        self.load_settings()
        self.set_view_size()

    def add_controls(self, parent_frame, row, col):
        """Add user control buttons to the window."""
        # create a subframe and place it as requested
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, padx=2)
        row = 0

        # add setup controls
        self.add_setup_controls(frame, row, 0)
        row += 1

        # add setup controls
        self.add_visibility_controls(frame, row, 0)
        row += 1

        # add rotation controls
        self.add_rotation_controls(frame, row, 0)
        row += 1
        self.add_movement_controls(frame, row, 0)
        row += 1

    def add_aspect_control(self, parent_frame, row, col):
        """Add view size control to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W, padx=2)
        self.aspect = tk.Text(frame, height=1, width=15)
        self.aspect.grid(row=0, column=0, sticky=tk.W)
        ctl = tk.Button(frame, text="Apply", command=self.on_aspect)
        ctl.grid(row=0, column=1, sticky=tk.E, padx=4)

    def add_movement_controls(self, parent_frame, row, col):
        """Add up/down/left/right controls to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W)
        row = 0
        ctl = tk.Button(frame, text='-', font=self.big_font, command=partial(self.action, 'Z-'))
        ctl.grid(row=row, column=0, sticky=tk.E, padx=2, pady=2)
        ctl = tk.Button(frame, text=STR_UP, font=self.big_font, command=partial(self.action, 'Mu'))
        ctl.grid(row=row, column=1, sticky=tk.W, padx=2, pady=2)
        ctl = tk.Button(frame, text='+', font=self.big_font, command=partial(self.action, 'Z+'))
        ctl.grid(row=row, column=2, sticky=tk.W, padx=2, pady=2)
        row += 1
        ctl = tk.Button(frame, text=STR_LEFT, font=self.big_font, command=partial(self.action, 'Ml'))
        ctl.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        ctl = tk.Button(frame, text=STR_DN, font=self.big_font, command=partial(self.action, 'Md'))
        ctl.grid(row=row, column=1, sticky=tk.W, padx=2, pady=2)
        ctl = tk.Button(frame, text=STR_RIGHT, font=self.big_font, command=partial(self.action, 'Mr'))
        ctl.grid(row=row, column=2, sticky=tk.W, padx=2, pady=2)

    def add_rotation_controls(self, parent_frame, row, col):
        """Add rotation controls to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col)
        row = 0
        # add heading
        ctl = tk.Label(frame, text='CONTROLS', font=self.big_font)
        ctl.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1
        # add column headings
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
            self.dim_controls.append(PlaneControl(frame, row, plane[0], plane[1], self))
            row += 1

    def add_setup_controls(self, parent_frame, row, col):
        """Add setup controls to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W, padx=2)
        row = 0
        # add heading
        ctl = tk.Label(frame, text='SET UP', font=self.big_font)
        ctl.grid(row=row, column=0, sticky=tk.W, pady=2)
        row += 1

        # add choice of number of dimensions
        ctl = tk.Label(frame, text='Number of dimensions:')
        ctl.grid(row=row, column=0, sticky=tk.W, pady=2)
        self.dim_choice = ttk.Combobox(frame,
                          state='readonly',
                          width=3,
                          values=[str(n+1) for n in range(2, MAX_DIM)],
                          )
        self.dim_choice.grid(row=row, column=1, sticky=tk.W, pady=0)
        self.dim_choice.bind('<<ComboboxSelected>>', self.on_dim)
        row += 1

        # add control of aspect ratios
        ctl = tk.Label(frame, text='Aspect ratios:')
        ctl.grid(row=row, column=0, sticky=tk.SW)
        self.add_aspect_control(frame, row, 1)
        row += 1

        # add control of viewer size
        ctl = tk.Label(frame, text='Viewing size:')
        ctl.grid(row=row, column=0, sticky=tk.SW)
        self.add_viewer_size_control(frame, row, 1)
        row += 1

    def add_viewer_size_control(self, parent_frame, row, col):
        """Add view size control to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W, padx=2)
        self.viewer_size = tk.Text(frame, height=1, width=15)
        self.viewer_size.grid(row=0, column=0, sticky=tk.W)
        ctl = tk.Button(frame, text="Apply", command=self.on_viewer_size)
        ctl.grid(row=0, column=1, sticky=tk.E, padx=4)

    def add_visibility_controls(self, parent_frame, row, col):
        """Add setup controls to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W, padx=2)
        row = 0
        # add heading
        ctl = tk.Label(frame, text='VISIBILITY', font=self.big_font)
        ctl.grid(row=row, column=0, sticky=tk.W, pady=2)
        row += 1

        # add choices of what to display
        # ctl = tk.Label(frame, text='Visibility:')
        # ctl.grid(row=row, column=0, sticky=tk.W, rowspan=3, pady=2)
        self.show_faces = tk.IntVar(value=1)
        ctl = ttk.Checkbutton(frame, text='Show faces', variable=self.show_faces, command=self.on_faces)
        ctl.grid(row=row, column=1, sticky=tk.W, pady=0)
        row += 1
        self.show_edges = tk.IntVar(value=1)
        ctl = ttk.Checkbutton(frame, text='Show edges', variable=self.show_edges, command=self.on_edges)
        ctl.grid(row=row, column=1, sticky=tk.W, pady=0)
        row += 1
        self.show_nodes = tk.IntVar()
        ctl = ttk.Checkbutton(frame, text='Show corners', variable=self.show_nodes, command=self.on_nodes)
        ctl.grid(row=row, column=1, sticky=tk.W, pady=0)
        row += 1
        self.show_coords = tk.IntVar()
        ctl = ttk.Checkbutton(frame, text='Show coords', variable=self.show_coords, command=self.on_coords)
        ctl.grid(row=row, column=1, sticky=tk.W, pady=0)
        row += 1
        self.show_center = tk.IntVar(value=1)
        ctl = ttk.Checkbutton(frame, text='Show center', variable=self.show_center, command=self.on_center)
        ctl.grid(row=row, column=1, sticky=tk.W, pady=0)
        row += 1
        self.show_perspective = tk.IntVar(value=1)
        ctl = ttk.Checkbutton(frame, text='Perspective view', variable=self.show_perspective, command=self.on_perspective)
        ctl.grid(row=row, column=1, sticky=tk.W, pady=0)
        row += 1

        # add a slider to control amount of ghosting
        ctl = tk.Label(frame, text='Amount of ghosting:')
        ctl.grid(row=row, column=0, sticky=tk.SW)
        self.ghost = tk.Scale(frame, to=1.0,
                              resolution=0.05,
                              orient=tk.HORIZONTAL,
                              command=self.on_ghost)
        self.ghost.grid(row=row, column=1, sticky=tk.W, pady=0)
        row += 1

        # add a slider to control amount of rotation
        ctl = tk.Label(frame, text='Rotation per click in degrees:')
        ctl.grid(row=row, column=0, sticky=tk.SW)
        self.angle = tk.Scale(frame, from_=1, to=20,
                              resolution=1,
                              orient=tk.HORIZONTAL,
                              command=self.on_angle)
        self.angle.grid(row=row, column=1, sticky=tk.W, pady=0)
        row += 1

    def action(self, value):
        """Pass the action through to the viewer.
        
        This exists because tkinter controls are created before the viewer.
        """
        self.viewer.take_action(value)

    def load_settings(self):
        """Load initial settings."""
        self.data.load(self.data_file)
        self.aspect.insert('1.0', self.data.aspects)
        self.viewer_size.insert('1.0', self.data.viewer_size)
        self.ghost.set(self.data.ghost)
        self.angle.set(self.data.angle)
        self.show_faces.set(self.data.show_faces)
        self.show_edges.set(self.data.show_edges)
        self.show_nodes.set(self.data.show_nodes)
        self.show_coords.set(self.data.show_coords)
        self.show_center.set(self.data.show_center)
        self.show_perspective.set(self.data.show_perspective)
        self.set_dim()

    def on_angle(self, value):
        """The angle of rotation slider has been changed."""
        self.data.angle = int(value)
        self.viewer.set_rotation()

    def on_aspect(self):
        """The aspect ratios have been changed.
        
        If they're valid, save them and rebuild the viewer,
        else highlight the edit control in yellow
        """
        aspects = self.aspect.get('1.0', '1.99')
        if self.data.validate_aspects(aspects):
            self.data.aspects = aspects
            self.aspect.configure(bg='white')
            self.viewer.init()
            self.viewer.display()
        else:
            self.aspect.configure(bg='yellow')

    def on_center(self):
        """The "show center" checkbox has been clicked."""
        self.data.show_center = bool(self.show_center.get())
        self.viewer.display()

    def on_close(self):
        """App is closing."""
        data = self.data
        data.dims = int(self.dim_choice.get())
        data.angle = self.angle.get()
        data.save(self.data_file)
        self.root.destroy()

    def on_coords(self):
        """The "show coords" checkbox has been clicked."""
        self.data.show_coords = bool(self.show_coords.get())
        self.viewer.display()

    def on_dim(self, param):
        """User has selected the number of dimensions via the combo box."""
        self.data.dims = int(param.widget.get())
        self.set_dim()

    def on_edges(self):
        """The "show edges" checkbox has been clicked."""
        self.data.show_edges = bool(self.show_edges.get())
        self.viewer.display()

    def on_faces(self):
        """The "show faces" checkbox has been clicked."""
        self.data.show_faces = bool(self.show_faces.get())
        self.viewer.display()

    def on_ghost(self, value):
        self.data.ghost = float(value)

    def on_key(self, event):
        print('on key', event)

    def on_load(self):
        self.viewer.run()

    def on_nodes(self):
        """The "show nodes" checkbox has been clicked."""
        self.data.show_nodes = bool(self.show_nodes.get())
        self.viewer.display()

    def on_perspective(self):
        """The "show center" checkbox has been clicked."""
        self.data.show_perspective = bool(self.show_perspective.get())
        self.viewer.display()

    def on_rotate(self, direction, dim_control):
        """Rotate the wireframe."""
        action = f'R{dim_control.dim1}{dim_control.dim2}{direction}'
        self.viewer.take_action(action)

    def on_viewer_size(self):
        """The viewer_size ratios have been changed.
        
        If they're valid, save them and rebuild the viewer,
        else highlight the edit control in yellow
        """
        viewer_size = self.viewer_size.get('1.0', '1.99')
        if self.data.validate_viewer_size(viewer_size):
            self.data.viewer_size = viewer_size
            self.viewer_size.configure(bg='white')
            self.set_view_size()
        else:
            self.viewer_size.configure(bg='yellow')

    def set_dim(self):
        """Set the number of dimensions to use."""
        dim = self.data.dims
        self.dim_choice.set(str(dim))
        # hide/show the dimension controls as appropriate
        for control in self.dim_controls:
            control.enable(dim)
        self.viewer.init()
        self.viewer.display()

    def set_view_size(self):
        """Set the viewing size from the values in data."""
        x, y = self.data.get_viewer_size()
        self.canvas.config(width=x, height=y)
        self.viewer.init()
        self.viewer.display()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Hypercube')
    parser.add_argument("-t", "--test", action="store_true", help="run in test mode")
    args = parser.parse_args()
    root = tk.Tk()
    app = App(root)
    root.mainloop()
