#! python3
# -*- coding: utf-8 -*-
"""
All activity takes place via Action objects. They are pushed onto a queue
(actionQ) which is emptied by run(), which pauses after each event to allow
tkinter to update the user interface and keep the program responsive.
(In addition, long-running drawing actions in display.py that would otherwise
make user requests wait can be terminated by setting a flag.)

Activities are of two sorts: visibility changes and movement changes.
Movement actions control the orientation of the hypercube; visibility actions
control how it is displayed, e.g. whether faces, edges or corners are shown;
the perspective; the amount of rotation; etc.

A history of actions is kept, and it is possible to replay these. The program
updates the user interface to correspond with the original actions. This
requires the program to know what control corresponds to which action, and to
update it; this needs a 3-way relationship between the control, the action and
the state. This is done by having Control classes encapsulate widgets (this
also hides the differences in the way widgets operate), holding them as values
in a dictionary whose keys are the action types, and placing callback info in
the class instances.

When the actions are originally carried out, triggered by the user clicking
controls, the run loop updates the state and changes the wireframe and display.
When the actions are replayed, the run loop leaves the state untouched and
updates the control, wireframe and display.
"""
import argparse
import copy
from functools import partial
import os
import random
import tkinter as tk
from tkinter import ttk

from action import Action
import controls
import data
import dims
import display
import utils

STR_UP = '↑'
STR_DN = '↓'
STR_LEFT = '←'
STR_RIGHT = '→'

# Names for the states of buttons. Values are indices into lists.
DISABLED = 0
ENABLED = 1
REPLAYING = 2

class App(tk.Frame):

    def __init__(self, root, args):
        tk.Frame.__init__(self, root)
        # set up hooks for program close
        self.root = root
        self.args = args
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind('<Escape>', lambda e: self.on_close())

        # create an instance for loading and saving data and get the filename
        # of the json file that holds data (.load_settings() and
        # .save_settings() will perform the actual transfers)
        # This is the canonical version of the persistent data. It is passed
        # into display.Viewer so that App and Viewer share the data.
        self.data = data.Data()
        self.data_file = data.get_location('settings')
        self.data.load(self.data_file)
        # set top-left position of window
        root.geometry(f'+{self.data.win_x}+{self.data.win_y}')
        self.actionQ = []               # queue of Action instances
        self.playback_index = -1        # if >= 0, we are replaying actionQ

        self.dim_controls = []
        self.grid(sticky=tk.NSEW)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.winfo_toplevel().title('Hypercube')
        self.big_font = ('calibri', 14, 'bold')

        # create a frame for display and add a canvas to it
        self.right_frame = tk.Frame(self)
        self.right_frame.grid(row=0, column=1, sticky=tk.NE)
        self.canvas = tk.Canvas(self.right_frame, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)

        # construct the viewer and the wireframe
        self.viewer = display.Viewer(self.data, self.canvas)

        # create a frame for controls and add them
        self.left_frame = tk.Frame(self)
        self.left_frame.grid(row=0, column=0, sticky=tk.NW)
        self.make_controls()
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

        # add test controls
        if self.args.test:
            ctl = tk.Label(frame, text='TEST', font=self.big_font)
            ctl.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
            row += 1
            self.add_test_controls(frame, row, 0)
            row += 1

    def add_test_controls(self, parent_frame, row, col):
        """Add test controls to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W, padx=2)
        row = 0
        ctl = tk.Button(frame, text="Test 1", command=self.on_test1)
        ctl.grid(row=row, column=0, sticky=tk.E, padx=4)
        ctl = tk.Button(frame, text="Test 2", command=self.on_test2)
        ctl.grid(row=row, column=1, sticky=tk.E, padx=4)
        ctl = tk.Button(frame, text="Test 3", command=self.on_test3)
        ctl.grid(row=row, column=2, sticky=tk.E, padx=4)
        row += 1
        ctl = tk.Button(frame, text="Test 4", command=self.on_test4)
        ctl.grid(row=row, column=0, sticky=tk.E, padx=4)
        ctl = tk.Button(frame, text="Test 5", command=self.on_test5)
        ctl.grid(row=row, column=1, sticky=tk.E, padx=4)
        ctl = tk.Button(frame, text="Test 6", command=self.on_test6)
        ctl.grid(row=row, column=2, sticky=tk.E, padx=4)
        row += 1

    def on_test1(self):
        print('Actions: ', end='')
        for a in self.viewer.actions:
            print(a, end='; ')
        print()

    def on_test2(self):
        pass

    def on_test3(self):
        control = self.controls['ghost']
        value = self.data.ghost + 1
        print('set ghost to', value)
        control.set(value)

    def on_test4(self):
        control = self.controls['angle']
        value = self.data.angle + 1
        print('set angle to', value)
        control.set(value)

    def on_test5(self):
        control = self.controls['auto_scale']
        value = self.data.auto_scale + 0.02
        print('set auto_scale to', value)
        control.set(value)

    def on_test6(self):
        control = self.controls['show_faces']
        value = self.data.show_faces ^ True
        print('set show_faces to', value)
        control.set(value)

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
        Zm = Action('Z', '-')
        Zp = Action('Z', '+')
        Ml = Action('M', 'l')
        Mr = Action('M', 'r')
        Mu = Action('M', 'u')
        Md = Action('M', 'd')
        PB = Action('P')
        ctl = tk.Button(frame, text='-', font=self.big_font, command=partial(self.queue_action, Zm))
        ctl.grid(row=row, column=0, sticky=tk.E, padx=2, pady=2)
        ctl = tk.Button(frame, text=STR_UP, font=self.big_font, command=partial(self.queue_action, Mu))
        ctl.grid(row=row, column=1, sticky=tk.W, padx=2, pady=2)
        ctl = tk.Button(frame, text='+', font=self.big_font, command=partial(self.queue_action, Zp))
        ctl.grid(row=row, column=2, sticky=tk.W, padx=2, pady=2)
        # add a "Replay" control
        spacer1 = tk.Label(frame, text="")
        spacer1.grid(row=row, column=3, padx=20)
        self.replay_button = tk.Button(frame, text="Play Recording", font=self.big_font, width=12, command=partial(self.queue_action, PB))
        self.replay_button.grid(row=row, column=4, columnspan=2, sticky=tk.NSEW, padx=2, pady=2)
        row += 1
        ctl = tk.Button(frame, text=STR_LEFT, font=self.big_font, command=partial(self.queue_action, Ml))
        ctl.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        ctl = tk.Button(frame, text=STR_DN, font=self.big_font, command=partial(self.queue_action, Md))
        ctl.grid(row=row, column=1, sticky=tk.W, padx=2, pady=2)
        ctl = tk.Button(frame, text=STR_RIGHT, font=self.big_font, command=partial(self.queue_action, Mr))
        ctl.grid(row=row, column=2, sticky=tk.W, padx=2, pady=2)
        # add a "Stop" control
        self.stop_button = tk.Button(frame, text="Stop", font=self.big_font, width=12, command=self.on_stop)
        self.stop_button.grid(row=row, column=4, sticky=tk.NSEW, padx=2, pady=2)
        row += 1

    def add_recording_controls(self, parent_frame, row, col):
        """Add recording controls to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W, padx=4)
        row = 0

        # add choice of frame rate
        ctrl = self.controls['frame_rate']
        ctrl.add_control(frame, row, 1)
        row += 1

        self.recording = False
        w = 16
        self.rec_start = tk.Button(frame, text="Start recording", width=w, command=partial(self.set_record_state, True))
        self.rec_start.grid(row=row, column=0, padx=2, pady=2)
        self.rec_stop = tk.Button(frame, text="Stop recording", width=w, command=partial(self.set_record_state, False))
        self.rec_stop.grid(row=row, column=1, padx=2, pady=2)
        self.set_record_state(False)
        row += 1
        self.rec_view = tk.Button(frame, text='View Recording', width=w, command=self.on_view_video)
        self.rec_view.grid(row=row, column=0, pady=2)
        # self.set_widget_state(self.rec_view, DISABLED)
        ctl = tk.Button(frame, text='View Folder', width=w, command=self.on_view_files)
        ctl.grid(row=row, column=1, pady=2)
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

        for plane in dims.planes:
            self.dim_controls.append(controls.PlaneControl(frame, row, plane[0], plane[1], self))
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

        # add a checkbox for whether replay tracks the visible settings
        ctl = self.controls['replay_visible']
        ctl.add_control(frame, row, 2, **{"padx":(12,0), "columnspan":2})
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
                          values=[str(n+1) for n in range(2, dims.MAX)],
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

        # add a "Restart" control
        self.clear_button = tk.Button(frame, text="Restart", command=self.reset)
        self.clear_button.grid(row=row, column=1, sticky=tk.NSEW, padx=2, pady=8)
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
        ctl = tk.Label(frame, text='These controls\naffect how the\nmovement actions\nare displayed.')
        ctl.grid(row=row, column=0, rowspan=8, sticky=tk.W, pady=2)

        # add controls to this frame
        for dataname in (
            'show_faces',
            'show_edges',
            'show_nodes',
            'show_coords',
            'show_steps',
            'show_center',
            'show_perspective',
            'show_vp',
            'depth',
            'ghost',
            'angle',
            'auto_scale',
            ):
            control = self.controls[dataname]
            control.add_control(frame, row, 1)
            row += 1

    def load_settings(self):
        """Load initial settings."""
        self.aspect.insert(0, self.data.aspects)
        self.viewer_size.insert(0, self.data.viewer_size)
        for dataname, control in self.controls.items():
            value = getattr(self.data, dataname)
            control.set(value)
        self.set_dim(0)

    def make_controls(self):
        """Construct controls in a dictionary."""
        self.controls = {
            'show_faces': controls.CheckControl('Show faces'),
            'show_edges': controls.CheckControl('Show edges'),
            'show_nodes': controls.CheckControl('Show corners'),
            'show_coords': controls.CheckControl('Show coordinates'),
            'show_steps': controls.CheckControl('Show intermediate steps'),
            'show_center': controls.CheckControl('Show center'),
            'show_perspective': controls.CheckControl('Perspective view'),
            'show_vp': controls.CheckControl('Show vanishing point'),
            'depth': controls.SlideControl('Depth of perspective:', 2.0, 10.0, 0.5),
            'ghost': controls.SlideControl('Amount of ghosting:', 0, 10, 1),
            'angle': controls.SlideControl('Rotation per click in degrees:', 1, 20, 1),
            'auto_scale': controls.SlideControl('Resizing during rotation:', 0.90, 1.10, 0.02),
            'replay_visible': controls.CheckControl('Replay uses\nvisibility settings'),
            'frame_rate': controls.ComboControl('Frame rate of video:', ['24', '25', '30', '60', '120']),
        }

        # set up a sleazy but convenient way of associating the control
        # and the callback
        callback = self.visibility_action
        for dataname, control in self.controls.items():
            control.set_data(dataname, self.data)
            control.callback = callback

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

    def on_close(self):
        """App is closing."""
        data = self.data
        data.win_x = self.root.winfo_x()
        data.win_y = self.root.winfo_y()
        data.dims = int(self.dim_choice.get())
        data.save(self.data_file)
        self.root.destroy()

    def on_dim(self, param):
        """User has selected the number of dimensions via the combo box."""
        old = self.data.dims
        self.data.dims = int(param.widget.get())
        self.set_dim(old)

    def on_frame_rate(self, param):
        self.data.frame_rate = int(param.widget.get())

    def on_random(self, direction):
        """Rotate the wireframe randomly in 3 dimensions."""
        dims = list(range(self.data.dims))
        dim1 = random.randint(0, 1)
        dims.remove(dim1)
        dim2 = random.choice(dims)
        dims.remove(dim2)
        dim3 = random.choice(dims)
        action = Action('R', dim1, dim2, dim3, direction)
        self.queue_action(action)

    def on_rotate(self, direction, dim_control):
        """Rotate the wireframe."""
        action = Action('R', dim_control.dim1, dim_control.dim2, None, direction)
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

    def on_view_video(self):
        """Show the last video recorded."""
        play_file = None
        if self.viewer.video_reader:
            self.viewer.stop = True
            text = "Play Recording"
            color = "SystemButtonFace"
        else:
            play_file = utils.find_latest_file(self.viewer.output_dir)
            text = "Stop Playing"
            color = "red"
        self.rec_view.configure(text=text, bg=color)
        if play_file:
            self.viewer.video_play(play_file)

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

    def queue_action(self, action: Action):
        """Add this action to the queue awaiting execution."""
        # Sometimes (why the inconsistency?) setting the value for a widget
        # generates a callback. This doubles up the action during playback,
        # so ignore all queue requests during playback.
        if self.playback_index < 0:
            self.actionQ.append(action)
            self.set_widget_state(self.clear_button, ENABLED)
            self.set_stop_button(ENABLED)

    def reset(self):
        """The dimensions, aspect or view size has changed.

        This is called at initial start and restart, too.
        (Re)set all buttons to initial state.
        (Re)initialize the viewer with the current values set up in .data.
        """
        self.recording = False
        self.set_record_state(False)
        self.viewer.record(False)
        self.set_replay_button(DISABLED)
        self.set_stop_button(DISABLED)
        self.set_widget_state(self.clear_button, DISABLED)

        # make a copy of the data for when we replay with visibility
        self.data_copy = copy.copy(self.data)
        self.viewer.init()
        self.viewer.display()

    def restore_data(self):
        """Restore the data settings in place at the beginning."""
        for attr in self.data_copy.__dict__:
            value = getattr(self.data_copy, attr)
            if attr == "replay_visible":
                # Keep the current replay_visible value because if it started
                # out one way but the user flipped it, we don't want to use
                # the original setting.
                continue
            if attr == "frame_rate":
                # Similar reasoning applies to frame_rate
                continue
            setattr(self.data, attr, value)
            if attr in self.controls:
                control = self.controls[attr]
                control.set(value)

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
                if action.visible:
                    if self.data.replay_visible:
                        # change the value in .data
                        # and the visible state of the control
                        self.set_data_value(action)
                        self.set_visible_state(action)
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
            if action.cmd == 'P':
                # the action is to play back all the actions up until now,
                self.set_replay_button(REPLAYING)
                self.playback_index = 0
                if self.data.replay_visible:
                    # restore the data settings in place at the beginning
                    self.restore_data()
                self.viewer.init(playback=True)
                self.viewer.display()
            else:
                # It's a regular action. Enable the replay button
                # (it would have been disabled if the queue were formerly empty)
                self.set_replay_button(ENABLED)

                need_action = True
                real_ghost = 0
                if action.visible:
                    # change the value in .data
                    self.set_data_value(action)
                    # certain actions need special treatment
                    vis = action.p1
                    if vis == 'show_faces':
                        # If ghosting is on when we hide faces, they don't
                        # seem to be hidden because their ghost is still
                        # visible, so turn ghosting off and then back on.
                        if not self.data.show_faces:
                            real_ghost = self.data.ghost
                            self.data.ghost = 0
                        pass
                    elif vis == 'depth':
                        self.viewer.set_depth()
                    elif vis == 'angle':
                        self.viewer.set_rotation()
                    elif vis == 'auto_scale':
                        need_action = False
                    elif vis == 'replay_visible':
                        need_action = False

                if need_action:
                    # execute the action
                    self.viewer.take_action(action)
                if real_ghost:
                    # We turned off ghosting. Turn it back on.
                    self.data.ghost = real_ghost

                if not self.actionQ:
                    # if there are no more actions queued, it makes no sense
                    # to offer a "Stop" action, so disable the button
                    self.set_stop_button(DISABLED)

        # wait 10ms, which allows tk UI actions, then check again
        self.root.after(10, self.run)

    def set_data_value(self, action: Action):
        assert action.visible
        data_name = action.p1
        value = action.p2

        # change the data value
        old_data = getattr(self.data, data_name)
        assert type(value) is type(old_data)
        setattr(self.data, data_name, value)

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

    def set_record_state(self, state: bool):
        self.recording = state
        self.set_widget_state(self.rec_start, not state)
        self.set_widget_state(self.rec_stop, state, "red")
        self.viewer.record(state)

    def set_replay_button(self, state):
        """Set the Replay button as disabled, ready or replaying."""
        states = (tk.DISABLED, tk.NORMAL, tk.NORMAL)
        text = ["Replay", "Replay", "Replaying"]
        self.replay_button.configure(state = states[state],
                                     text= text[state])

    def set_stop_button(self, state):
        """Set the Stop button as active or disabled."""
        self.set_widget_state(self.stop_button, state, "red")

    def set_visible_state(self, action: Action):
        assert action.visible
        data_name = action.p1
        value = action.p2

        # get the control associated with the data_name
        # and change its state to match the data value
        control = self.controls[data_name]
        control.set(value)

    def set_widget_state(self, control, state, color=None):
        """Set the control as active or disabled."""
        state = int(state)
        states = (tk.DISABLED, tk.NORMAL)
        control.configure(state = states[state])
        if color:
            colors = ["SystemButtonFace", color]
            control.configure(bg=colors[state], fg=colors[state ^ 1])

    def set_view_size(self):
        """Set the viewing size from the values in data."""
        x, y = self.data.get_viewer_size()
        self.canvas.config(width=x, height=y)
        self.reset()

    def visibility_action(self, data_name):
        """Execute a visibility action."""
        # get the control associated with the data_name and the present value
        control = self.controls[data_name]
        control_value = control.get()
        action = Action('V', data_name, self.data.coerce(control_value, data_name))
        self.queue_action(action)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Hypercube')
    parser.add_argument("-t", "--test", action="store_true", help="run in test mode")
    args = parser.parse_args()
    root = tk.Tk()
    app = App(root, args)
    root.mainloop()
