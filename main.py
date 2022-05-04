#! python3.10
# -*- coding: utf-8 -*-

from functools import partial
import os
import random
import sys
import tkinter as tk
from tkinter import ttk

import colors
import data
import display
import utils

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

# Names for the states of buttons. Values are indices into lists.
DISABLED = 0
ENABLED = 1
REPLAYING = 2

class PlaneControl:
    """A class to manage tkinter controls for a single plane."""

    def __init__(self, frame, row, dim1, dim2, app):
        self.frame = frame
        self.row = row
        self.dim1 = dim1
        self.dim2 = dim2
        self.app = app

    def add_controls(self):
        dim1str = labels[self.dim1]
        dim2str = labels[self.dim2]
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


class App(tk.Frame):

    PLAYBACK_ACTION = 'PB'

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
        self.actionQ = []
        self.playback_index = -1

        self.max_dim = 6
        self.dim_controls = []
        self.grid(sticky=tk.NSEW)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.winfo_toplevel().title('Hypercube')
        self.big_font = ('calibri', 14, 'bold')
        # self.bind_all('<Key>', self.on_key)

        # create a frame for display
        self.right_frame = tk.Frame(self)
        self.right_frame.grid(row=0, column=1, sticky=tk.NE)
        self.canvas = tk.Canvas(self.right_frame, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)

        # calculate the directory for output data
        working = os.path.dirname(sys.argv[0])
        output = os.path.join(working, r'output')
        self.viewer = display.Viewer(self.data, output, self.canvas)

        # create a frame for controls and add them
        self.left_frame = tk.Frame(self)
        self.left_frame.grid(row=0, column=0, sticky=tk.NW)
        self.add_controls(self.left_frame, 0, 0)

        self.load_settings()
        self.set_view_size()
        self.run()

    def add_controls(self, parent_frame, row, col):
        """Add user controls to the window."""
        # create a subframe and place it as requested
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, padx=2)
        row = 0

        # add setup controls
        ctl = tk.Label(frame, text='SETUP', font=self.big_font)
        ctl.grid(row=row, column=0, sticky=tk.W, pady=2)
        row += 1
        self.add_setup_controls(frame, row, 0)
        row += 1

        # add visibility controls
        ctl = tk.Label(frame, text='VISIBILITY', font=self.big_font)
        ctl.grid(row=row, column=0, sticky=tk.W, pady=2)
        row += 1
        self.add_visibility_controls(frame, row, 0)
        row += 1

        # add movement controls
        ctl = tk.Label(frame, text='MOVEMENT', font=self.big_font)
        ctl.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1
        self.add_rotation_controls(frame, row, 0)
        row += 1
        self.add_movement_controls(frame, row, 0)
        row += 1

        # add recording controls
        ctl = tk.Label(frame, text='RECORDING', font=self.big_font)
        ctl.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1
        self.add_recording_controls(frame, row, 0)
        row += 1

    def add_aspect_control(self, parent_frame, row, col):
        """Add view size control to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W, padx=2)
        self.aspect = tk.Entry(frame, width=15)
        self.aspect.grid(row=0, column=0, sticky=tk.W)
        ctl = tk.Button(frame, text="Apply", command=self.on_aspect)
        ctl.grid(row=0, column=1, sticky=tk.E, padx=4)

    def add_movement_controls(self, parent_frame, row, col):
        """Add up/down/left/right controls to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W, padx=4)
        row = 0
        ctl = tk.Button(frame, text='-', font=self.big_font, command=partial(self.queue_action, 'Z-'))
        ctl.grid(row=row, column=0, sticky=tk.E, padx=2, pady=2)
        ctl = tk.Button(frame, text=STR_UP, font=self.big_font, command=partial(self.queue_action, 'Mu'))
        ctl.grid(row=row, column=1, sticky=tk.W, padx=2, pady=2)
        ctl = tk.Button(frame, text='+', font=self.big_font, command=partial(self.queue_action, 'Z+'))
        ctl.grid(row=row, column=2, sticky=tk.W, padx=2, pady=2)
        # add a "Replay" control
        spacer1 = tk.Label(frame, text="")
        spacer1.grid(row=row, column=3, padx=20)
        self.replay_button = tk.Button(frame, text="Replay", font=self.big_font, width=12, command=partial(self.queue_action, App.PLAYBACK_ACTION))
        self.replay_button.grid(row=row, column=4, columnspan=2, sticky=tk.NSEW, padx=2, pady=2)
        row += 1
        ctl = tk.Button(frame, text=STR_LEFT, font=self.big_font, command=partial(self.queue_action, 'Ml'))
        ctl.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        ctl = tk.Button(frame, text=STR_DN, font=self.big_font, command=partial(self.queue_action, 'Md'))
        ctl.grid(row=row, column=1, sticky=tk.W, padx=2, pady=2)
        ctl = tk.Button(frame, text=STR_RIGHT, font=self.big_font, command=partial(self.queue_action, 'Mr'))
        ctl.grid(row=row, column=2, sticky=tk.W, padx=2, pady=2)
        # add a "Stop" control
        self.stop_button = tk.Button(frame, text="Stop", font=self.big_font, width=12, command=self.on_stop)
        self.stop_button.grid(row=row, column=4, sticky=tk.NSEW, padx=2, pady=2)
        row += 1
        # add a "Restart" control
        self.clear_button = tk.Button(frame, text="Restart", command=self.reset)
        self.clear_button.grid(row=row, column=4, sticky=tk.NSEW, padx=2, pady=2)
        row += 1

    def add_recording_controls(self, parent_frame, row, col):
        """Add recording controls to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W, padx=4)
        row = 0
        self.rec_buttons = utils.ButtonPair(frame, ['Start recording', 'Stop recording'], self.viewer.record, row=row)
        ctl = tk.Button(frame, text='View File Location', command=self.on_view_files)
        ctl.grid(row=row, column=2, sticky=tk.W, padx=6, pady=2)
        row += 1

    def add_rotation_controls(self, parent_frame, row, col):
        """Add rotation controls to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col)
        row = 0
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

        # add a random rotation
        ctl = tk.Label(frame, text='Random')
        ctl.grid(row=row, column=0, sticky=tk.EW, padx=2, pady=2)
        # insert controls for random rotation in a subframe
        rot_frame = tk.Frame(frame)
        rot_frame.grid(row=row, column=1)
        btn = tk.Button(rot_frame, text=' < ', command=partial(self.on_random, '-'))
        btn.grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        btn = tk.Button(rot_frame, text=' > ', command=partial(self.on_random, '+'))
        btn.grid(row=0, column=1, sticky=tk.W, padx=2, pady=2)
        row += 1

    def add_setup_controls(self, parent_frame, row, col):
        """Add setup controls to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W, padx=2)
        row = 0
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
        self.viewer_size = tk.Entry(frame, width=15)
        self.viewer_size.grid(row=0, column=0, sticky=tk.W)
        ctl = tk.Button(frame, text="Apply", command=self.on_viewer_size)
        ctl.grid(row=0, column=1, sticky=tk.E, padx=4)

    def add_visibility_controls(self, parent_frame, row, col):
        """Add controls for what to display to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W, padx=2)
        row = 0
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
        ctl = ttk.Checkbutton(frame, text='Show coordinates', variable=self.show_coords, command=self.on_coords)
        ctl.grid(row=row, column=1, sticky=tk.W, pady=0)
        row += 1
        self.show_steps = tk.IntVar(value=1)
        ctl = ttk.Checkbutton(frame, text='Show intermediate steps', variable=self.show_steps, command=self.on_steps)
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
        self.show_vp = tk.IntVar(value=1)
        ctl = ttk.Checkbutton(frame, text='Show vanishing point', variable=self.show_vp, command=self.on_vp)
        ctl.grid(row=row, column=1, sticky=tk.W, pady=0)
        row += 1

        # add a slider to control perspective depth
        ctl = tk.Label(frame, text='Depth of perspective:')
        ctl.grid(row=row, column=0, sticky=tk.SW)
        self.depth = tk.Scale(frame, from_=2.0, to=10.0,
                              resolution=0.5,
                              orient=tk.HORIZONTAL,
                              command=self.on_depth)
        self.depth.grid(row=row, column=1, sticky=tk.W, pady=0)
        row += 1

        # add a slider to control amount of ghosting
        ctl = tk.Label(frame, text='Amount of ghosting:')
        ctl.grid(row=row, column=0, sticky=tk.SW)
        self.ghost = tk.Scale(frame, to=10,
                              resolution=1,
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

    def load_settings(self):
        """Load initial settings."""
        self.data.load(self.data_file)
        self.aspect.insert(0, self.data.aspects)
        self.viewer_size.insert(0, self.data.viewer_size)
        self.depth.set(self.data.depth)
        self.ghost.set(self.data.ghost)
        self.angle.set(self.data.angle)
        self.show_faces.set(self.data.show_faces)
        self.show_edges.set(self.data.show_edges)
        self.show_nodes.set(self.data.show_nodes)
        self.show_coords.set(self.data.show_coords)
        self.show_center.set(self.data.show_center)
        self.show_perspective.set(self.data.show_perspective)
        self.show_vp.set(self.data.show_vp)
        self.show_steps.set(self.data.show_steps)
        self.set_dim(0)

    def on_angle(self, value):
        """The angle of rotation slider has been changed."""
        self.data.angle = int(value)
        self.viewer.set_rotation()

    def on_aspect(self):
        """The aspect ratios have been changed.
        
        If they're valid, save them and rebuild the viewer,
        else highlight the edit control in yellow
        """
        aspects = self.aspect.get()
        if self.data.validate_aspects(aspects):
            self.data.aspects = aspects
            self.aspect.configure(bg='white')
            self.reset()
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

    def on_depth(self, value):
        self.data.depth = float(value)
        self.viewer.set_depth()
        self.viewer.display()

    def on_dim(self, param):
        """User has selected the number of dimensions via the combo box."""
        old = self.data.dims
        self.data.dims = int(param.widget.get())
        self.set_dim(old)

    def on_edges(self):
        """The "show edges" checkbox has been clicked."""
        self.data.show_edges = bool(self.show_edges.get())
        self.viewer.display()

    def on_faces(self):
        """The "show faces" checkbox has been clicked."""
        self.data.show_faces = bool(self.show_faces.get())
        self.viewer.display()

    def on_ghost(self, value):
        """The amount of ghosting has been changed."""
        self.data.ghost = int(value)

    def on_key(self, event):
        print('on key', event)

    def on_nodes(self):
        """The "show nodes" checkbox has been clicked."""
        self.data.show_nodes = bool(self.show_nodes.get())
        self.viewer.display()

    def on_perspective(self):
        """The "show center" checkbox has been clicked."""
        self.data.show_perspective = bool(self.show_perspective.get())
        self.viewer.display()

    def on_random(self, direction):
        """Rotate the wireframe randomly in 3 dimensions."""
        dims = list(range(self.data.dims))
        dim1 = random.randint(0, 1)
        dims.remove(dim1)
        dim2 = random.choice(dims)
        dims.remove(dim2)
        dim3 = random.choice(dims)
        action = f'R{dim1}{dim2}{dim3}{direction}'
        self.queue_action(action)

    def on_rotate(self, direction, dim_control):
        """Rotate the wireframe."""
        action = f'R{dim_control.dim1}{dim_control.dim2}{direction}'
        self.queue_action(action)

    def on_steps(self):
        """The "show intermediate steps" checkbox has been clicked."""
        self.data.show_steps = bool(self.show_steps.get())
        self.viewer.display()

    def on_stop(self):
        """User has asked for the current and pending actions to be stopped."""
        # ask the viewer to stop ASAP
        self.viewer.stop = True
        # discard all actions in the pending queue
        self.actionQ = []
        # stop any playback
        self.playback_index = -1
        # adjust button states
        self.set_replay_button(ENABLED)
        self.set_stop_button(DISABLED)

    def on_view_files(self):
        """Show the folder where video output is saved."""
        os.startfile(self.viewer.output_dir)

    def on_viewer_size(self):
        """The viewer_size ratios have been changed.
        
        If they're valid, save them and rebuild the viewer,
        else highlight the edit control in yellow
        """
        viewer_size = self.viewer_size.get()
        if self.data.validate_viewer_size(viewer_size):
            self.data.viewer_size = viewer_size
            self.viewer_size.configure(bg='white')
            self.set_view_size()
        else:
            self.viewer_size.configure(bg='yellow')

    def on_vp(self):
        """The "show vanishing point" checkbox has been clicked."""
        self.data.show_vp = bool(self.show_vp.get())
        self.viewer.display()

    def queue_action(self, action):
        """Add this action to the queue awaiting execution."""
        self.actionQ.append(action)
        self.set_widget_state(self.clear_button, ENABLED)
        self.set_stop_button(ENABLED)

    def reset(self):
        """The dimensions,aspect or view size has changed.

        This is called at initial start and restart, too.
        (Re)set all buttons to initial state.
        (Re)initialize the viewer with the current values set up in .data.
        """
        self.rec_buttons.stop()
        self.set_replay_button(DISABLED)
        self.set_stop_button(DISABLED)
        self.set_widget_state(self.clear_button, DISABLED)

        self.viewer.init()
        self.viewer.display()

    def run(self):
        """Run the actions on the action queue.

        https://stackoverflow.com/questions/18499082/tkinter-only-calls-after-idle-once
        """
        if self.playback_index >= 0:
            # we're playing back the actions previously taken
            if self.playback_index < len(self.viewer.actions):
                # there are more actions to take
                action = self.viewer.actions[self.playback_index]
                self.playback_index += 1
                # stop playing back if the user has canceled
                self.viewer.take_action(action, playback=True)
            else:
                # we've played back all the actions, so cancel playback
                self.playback_index = -1
                self.set_replay_button(ENABLED)
                self.set_stop_button(DISABLED)

        elif self.actionQ:
            # the user has initiated an action like rotate, zoom, etc.
            # and it has been placed on a queue. Take it off the queue.
            action = self.actionQ[0]
            del self.actionQ[0]
            if action == app.PLAYBACK_ACTION:
                # the action is to play back all the actions up until now,
                self.set_replay_button(REPLAYING)
                self.playback_index = 0
                self.viewer.init(playback=True)
                self.viewer.display()
            else:
                # It's a regular action. Enable the replay button
                # (it would have been disabled if the queue were formerly empty)
                self.set_replay_button(ENABLED)
                # execute the action
                self.viewer.take_action(action)
                if not self.actionQ:
                    # if there are no more actions queued, it makes no sense
                    # to offer a "Stop" action, so disable the button
                    self.set_stop_button(DISABLED)

        # wait 10ms, which allows tk UI actions, then check again
        self.root.after(10, self.run)

    def set_dim(self, old_count):
        """Set the number of dimensions to use and adjust the controls."""
        dim_count = self.data.dims
        self.dim_choice.set(str(dim_count))
        # create or destroy the dimension controls as appropriate
        if old_count < dim_count:
            for dim in range(old_count, dim_count):
                self.dim_controls[dim].add_controls()
        else:
            for dim in range(dim_count, old_count):
                self.dim_controls[dim].delete_controls()
        self.reset()

    def set_replay_button(self, state):
        """Set the Replay button as disabled, ready or replaying."""
        states = (tk.DISABLED, tk.NORMAL, tk.NORMAL)
        text = ["Replay", "Replay", "Replaying"]
        self.replay_button.configure(state = states[state],
                                     text= text[state])

    def set_stop_button(self, state):
        """Set the Stop button as active or disabled."""
        states = (tk.DISABLED, tk.NORMAL)
        color = ['SystemButtonFace', 'red']
        self.stop_button.configure(state = states[state],
                                   bg=color[state])

    def set_widget_state(self, control, state):
        """Set the control as active or disabled."""
        states = (tk.DISABLED, tk.NORMAL)
        control.configure(state = states[state])

    def set_view_size(self):
        """Set the viewing size from the values in data."""
        x, y = self.data.get_viewer_size()
        self.canvas.config(width=x, height=y)
        self.reset()


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
