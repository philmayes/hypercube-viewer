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
from tkinter import ttk, messagebox

from action import Action, ActionQueue
import controls
from controls import DISABLED, ENABLED, ACTIVE
import data
import dims
import display
from hints import Hints
import pubsub
import utils

STR_UP = "↑"
STR_DN = "↓"
STR_LEFT = "←"
STR_RIGHT = "→"

# The application can be in any of these 5 states. These states maintain
# buttons in the appropriate state. (Buttons have 3 states: disabled, enabled,
# and active. This allows for text and color changes.)
# CLEAN is the state when no actions have been issued, so the Play and Stop
# buttons should be disabled.
# IDLE is when nothing is happening.
# RUNNING is when user-issued actions are being executed.
# DO NOT CONFUSE REPLAYING and PLAYING. REPLAYING is playing back all the
# commands like move and rotate that have been issued, while PLAYING is the
# playback of a previously-recorded video.
CLEAN, IDLE, RUNNING, REPLAYING, PLAYING = range(5)

# An additional state that exists alongside the above five is whether we are
# recording to video or not. This state is held in Viewer.recording.
# This table gives the button that is pressed to enter the state
# and the action that is triggered.
#      state       button          action
#   -----------|----------------|-----------------
#   CLEAN       .restart_button  .restart
#   IDLE        .stop_button     .on_stop
#   RUNNING     movement buttons .queue_action(Action)
#   PLAYING     .play_button     .on_play_video
#   REPLAYING   .replay_button   .queue_action(PB)
#   RECORDING   .record_button   .set_record_state

# These lists give the states of the above 5 buttons for each of the 5
# application states for each of the 2 record states.
button_states_normal = (
#    replay_button  stop_button  record_button  play_button    state
    (DISABLED,      DISABLED,    ENABLED,       ENABLED),    # CLEAN
    (ENABLED,       DISABLED,    ENABLED,       ENABLED),    # IDLE
    (ENABLED,       ACTIVE,      ENABLED,       ENABLED),    # RUNNING
    (ACTIVE,        ACTIVE,      ENABLED,       DISABLED),   # REPLAYING
    (DISABLED,      DISABLED,    DISABLED,      ACTIVE),     # PLAYING
)
button_states_recording = (
#    replay_button  stop_button  record_button  play_button    state
    (DISABLED,      DISABLED,    ACTIVE,        ENABLED),    # CLEAN
    (ENABLED,       DISABLED,    ACTIVE,        DISABLED),   # IDLE
    (ENABLED,       ACTIVE,      ACTIVE,        ENABLED),    # RUNNING
    (ACTIVE,        ACTIVE,      ACTIVE,        DISABLED),   # REPLAYING
    (DISABLED,      DISABLED,    DISABLED,      DISABLED),   # PLAYING
)


def about():
    messagebox.showinfo('Hypercube', 'Version 0.0.1')

def preferences():
    messagebox.showinfo('Hypercube', 'Not yet implemented')

class App(tk.Frame):

    def __init__(self, root, args):
        tk.Frame.__init__(self, root)
        # set up hooks for program close
        self.root = root
        self.args = args
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind('<Escape>', lambda e: self.on_close())
        self.add_menu()

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
        self.actionQ = ActionQueue()    # queue of Action instances
        self.playback_index = -1        # if >= 0, we are replaying actionQ
        self.state = CLEAN

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
        self.hints = Hints(self.viewer)

        # create a frame for controls and add them
        self.left_frame = tk.Frame(self)
        self.left_frame.grid(row=0, column=0, sticky=tk.NW)
        self.make_controls()
        self.add_controls(self.left_frame, 0, 0)
        self.buttons = (self.replay_button, self.stop_button, self.record_button, self.play_button)

        self.load_settings()
        self.set_view_size()
        # For reasons I do not understand, the controls "ghost" and "angle"
        # trigger callbacks when their value is set. Flush the spurious
        # actions and disable the "Begin Again" button which got enabled. 
        self.actionQ.clear()
        self.restart_button.state = DISABLED
        self.set_state(CLEAN, force=True)

        pubsub.subscribe('vplay', self.on_play_end)
        self.run()

    def add_controls(self, parent_frame, row, col):
        """Add user controls to the window."""
        # create a subframe and place it as requested
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, padx=2)
        row = 0
        color = "red3"

        # add setup controls
        ctl = tk.Label(frame, text='SETUP', font=self.big_font, fg=color)
        ctl.grid(row=row, column=0, sticky=tk.W, pady=2)
        row += 1
        self.add_setup_controls(frame, row, 0)
        row += 1
        w = ttk.Separator(frame, orient=tk.HORIZONTAL)
        w.grid(row=row, column=0, sticky=tk.EW, pady=(8,0))
        row += 1

        # add visibility controls
        ctl = tk.Label(frame, text='VISIBILITY', font=self.big_font, fg=color)
        ctl.grid(row=row, column=0, sticky=tk.W, pady=2)
        row += 1
        self.add_visibility_controls(frame, row, 0)
        row += 1
        w = ttk.Separator(frame, orient=tk.HORIZONTAL)
        w.grid(row=row, column=0, sticky=tk.EW, pady=(6,0))
        row += 1

        # add movement controls
        ctl = tk.Label(frame, text='MOVEMENT', font=self.big_font, fg=color)
        ctl.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1
        self.add_rotation_controls(frame, row, 0)
        row += 1
        self.add_movement_controls(frame, row, 0)
        row += 1
        w = ttk.Separator(frame, orient=tk.HORIZONTAL)
        w.grid(row=row, column=0, sticky=tk.EW, pady=(10,0))
        row += 1

        # add recording controls
        ctl = tk.Label(frame, text='RECORDING TO VIDEO', font=self.big_font, fg=color)
        ctl.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        row += 1
        self.add_recording_controls(frame, row, 0)
        row += 1
        w = ttk.Separator(frame, orient=tk.HORIZONTAL)
        w.grid(row=row, column=0, sticky=tk.EW, pady=(10,0))
        row += 1

        # add test controls
        if self.args.test:
            ctl = tk.Label(frame, text='TEST', font=self.big_font, fg=color)
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
        print(self.viewer.actions)

    ttt = ""
    def on_test2(self):
        App.ttt += "A rose by any other name\nwould still be\na rose.\n"
        self.viewer.show_text(App.ttt)

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
        self.aspect.hint_id = "aspect"
        ctl = tk.Button(frame, text="Apply", command=self.on_aspect)
        ctl.grid(row=0, column=1, sticky=tk.E, padx=4)

    def add_menu(self):
        menubar = tk.Menu(self.root, background='#ff8000', foreground='black', activebackground='white', activeforeground='black')
        file = tk.Menu(menubar, tearoff=0)
        # file.add_command(label="New")
        # file.add_command(label="Open")
        # file.add_command(label="Save")
        # file.add_command(label="Save as")
        # file.add_separator()
        file.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file)

        edit = tk.Menu(menubar, tearoff=0)
        edit.add_command(label="Preferences...", command=preferences)
        menubar.add_cascade(label="Edit", menu=edit)

        help = tk.Menu(menubar, tearoff=0)
        help.add_command(label="About", command=about)
        menubar.add_cascade(label="Help", menu=help)
        self.root.config(menu=menubar)

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
        ctl.hint_id = "zoom_m"
        ctl = tk.Button(frame, text=STR_UP, font=self.big_font, command=partial(self.queue_action, Mu))
        ctl.grid(row=row, column=1, sticky=tk.W, padx=2, pady=2)
        ctl.hint_id = "move"
        ctl = tk.Button(frame, text='+', font=self.big_font, command=partial(self.queue_action, Zp))
        ctl.grid(row=row, column=2, sticky=tk.W, padx=2, pady=2)
        ctl.hint_id = "zoom_p"
        # add a "Replay" control
        spacer1 = tk.Label(frame, text="")
        spacer1.grid(row=row, column=3, padx=20)
        self.replay_button = controls.Button(frame,
                                             texts = ["Replay", "Replay", "Replaying"],
                                             font=self.big_font,
                                             width=12,
                                             command=partial(self.queue_action, PB))
        self.replay_button.hint_id = "replay"
        self.replay_button.grid(row=row, column=4, columnspan=2, sticky=tk.NSEW, padx=2, pady=2)
        row += 1
        ctl = tk.Button(frame, text=STR_LEFT, font=self.big_font, command=partial(self.queue_action, Ml))
        ctl.grid(row=row, column=0, sticky=tk.W, padx=2, pady=2)
        ctl.hint_id = "move"
        ctl = tk.Button(frame, text=STR_DN, font=self.big_font, command=partial(self.queue_action, Md))
        ctl.grid(row=row, column=1, sticky=tk.W, padx=2, pady=2)
        ctl.hint_id = "move"
        ctl = tk.Button(frame, text=STR_RIGHT, font=self.big_font, command=partial(self.queue_action, Mr))
        ctl.grid(row=row, column=2, sticky=tk.W, padx=2, pady=2)
        ctl.hint_id = "move"
        # add a "Stop" control
        self.stop_button = controls.Button(frame, text="Stop", color2="red", font=self.big_font, width=12, command=self.on_stop)
        self.stop_button.grid(row=row, column=4, sticky=tk.NSEW, padx=2, pady=2)
        self.stop_button.hint_id = "stop"
        row += 1
        # add a "Restart" control
        self.restart_button = controls.Button(frame, text="Begin Again", command=self.restart)
        self.restart_button.grid(row=row, column=4, sticky=tk.NSEW, padx=2, pady=2)
        self.restart_button.hint_id = "restart"
        row += 1


    def add_recording_controls(self, parent_frame, row, col):
        """Add recording controls to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W, padx=4)
        row = 0

        # add choice of frame rate
        control = self.controls['frame_rate']
        control.add_control(frame, row, 1, **{"columnspan": 3})
        row += 1

        w = 10
        self.record_button = controls.Button(frame, texts=["Record", "Record", "Stop"], color2="red", width=w, command=self.set_record_state)
        self.record_button.grid(row=row, column=0, sticky=tk.E, pady=2)
        self.record_button.hint_id = "record"
        self.play_button = controls.Button(frame, texts=["Play", "Play", "Stop"], color2="red", width=w, command=self.on_play_video)
        self.play_button.grid(row=row, column=1, pady=2)
        self.play_button.hint_id = "play"
        ctl = tk.Button(frame, text='View Folder', width=w, command=self.on_view_files)
        ctl.grid(row=row, column=2, pady=2)
        ctl.hint_id = "folder"
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
        btn.hint_id = "random"
        btn = tk.Button(rot_frame, text=' > ', command=partial(self.on_random, '+'))
        btn.grid(row=0, column=1, sticky=tk.W, padx=2, pady=2)
        btn.hint_id = "random"

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
        self.dim_choice.hint_id = "dims"
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
        self.viewer_size.hint_id = "viewsize"
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
        control = self.controls['show_hints']
        control.add_control(frame, row, 0)
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
            'replay_visible': controls.CheckControl('Replay uses original\nvisibility settings'),
            'frame_rate': controls.ComboControl('Frame rate of video:', ['24', '25', '30', '60', '120']),
            'show_hints': controls.CheckControl('Show hints'),
        }

        # set up a sleazy but convenient way of associating the control
        # and the callback
        callback = self.visibility_action
        for dataname, control in self.controls.items():
            control.set_data(dataname, self.data)
            control.callback = callback
            if dataname == "show_hints":
                control.callback = self.on_hints
            # If this control is a slider, tell the action queue so it is able
            # to merge successive values together
            if isinstance(control, controls.SlideControl | controls.ComboControl):
                ActionQueue.sliders.append(dataname)

    def on_aspect(self):
        """The aspect ratios have been changed.
        
        If they're valid, save them and rebuild the viewer,
        else highlight the edit control in yellow
        """
        aspects = self.aspect.get()
        if self.data.validate_aspects(aspects):
            self.data.aspects = aspects
            self.aspect.configure(bg='white')
            self.restart()
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

    def on_hints(self, dataname):
        """User has toggled whether hints are to be shown."""
        control = self.controls[dataname]
        value = control.get()
        self.hints.visible(value)

    def on_play_end(self, state):
        assert state is False
        self.set_state(IDLE)

    def on_play_video(self):
        """Show the last video recorded."""
        play_file = None
        playing = self.viewer.video_reader is not None
        self.viewer.stop = playing
        if not playing:
            play_file = utils.find_latest_file(self.viewer.output_dir)
        if play_file:
            self.set_state(PLAYING)
            self.viewer.video_play(play_file)
        else:
            self.set_state(IDLE)

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

    def on_stop(self):
        """User has asked for the current and pending actions to be stopped."""
        # ask the viewer to stop ASAP
        self.viewer.stop = True
        # discard all actions in the pending queue
        self.actionQ.clear()
        # stop any playback
        self.playback_index = -1
        # adjust button states
        self.set_state(IDLE)

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

    def queue_action(self, action: Action):
        """Add this action to the queue awaiting execution."""
        # Sometimes (why the inconsistency?) setting the value for a widget
        # generates a callback. This doubles up the action during playback,
        # so ignore all queue requests during playback.
        if self.playback_index < 0:
            self.actionQ.append(action)
            self.restart_button.state = ENABLED

    def restart(self):
        """The dimensions, aspect or view size has changed.

        This is called at initial start and restart, too.
        (Re)set all buttons to initial state.
        (Re)initialize the viewer with the current values set up in .data.
        """
        self.set_record_state(False)
        self.set_state(CLEAN)
        self.restart_button.state = DISABLED

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
                self.set_state(IDLE)

        elif self.actionQ:
            # the user has initiated an action like rotate, zoom, etc.
            # and it has been placed on a queue. Take it off the queue.
            action = self.actionQ[0]
            del self.actionQ[0]
            if action.cmd == 'P':
                # the action is to play back all the actions up until now,
                # self.set_replay_button(ACTIVE)
                self.playback_index = 0
                self.set_state(REPLAYING)
                if self.data.replay_visible:
                    # restore the data settings in place at the beginning
                    self.restore_data()
                self.viewer.init(playback=True)
                self.viewer.display()
            else:
                # It's a regular action. Enable the replay button
                # (it would have been disabled if the queue were formerly empty)
                self.set_state(RUNNING)

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
                    self.set_state(IDLE)
        else:
            self.hint_manager()

        # wait 10ms, which allows tk UI actions, then check again
        self.root.after(10, self.run)

    def hint_manager(self):
        try:
            # get the widget under the cursor
            x, y = self.winfo_pointerxy()
            widget = self.winfo_containing(x, y)
            if widget:
                # get possible hint id for this control...
                if hasattr(widget, "hint_id"):
                    hint_id = widget.hint_id
                else:
                    hint_id = None
                self.hints.show(hint_id)
        except:
            # specificly, we are catching a popdown exception in
            # winfo_containing, but why not catch everything?
            pass

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
        # If old_count==0, we are being called from .__init__ and .set_view_size
        # will subsequently call .restart, so there is no need to do it here.
        if old_count != 0:
            self.restart()

    def set_record_state(self, active=None):
        """Set or Xor the record button.

        active == None:     xor the recording state
        active == boolean:  recording [not] wanted
        """
        if active is None:
            active = not self.viewer.recording
        self.viewer.video_record(active)
        self.set_state(self.state, force=True)

    def set_replay_button(self, state):
        """Set the Replay button as disabled, ready or replaying."""
        self.replay_button.state = state

    def set_state(self, new_state: int, force: bool=False):
        """Set the new app state and adjust button states to match."""
        combined = self.state * 10 + new_state # useful for debug breakpoints
        if not force and new_state == self.state:
            # print(f'state change {self.state} unchanged')
            return
        button_states = button_states_recording if self.viewer.recording\
                   else button_states_normal
        values = button_states[new_state]
        for index, btn_state in enumerate(values):
            self.buttons[index].state = btn_state
        # print(f'state change {self.state} -> {new_state}; buttons={values}; forced={force}')
        self.state = new_state

    def set_visible_state(self, action: Action):
        """Set the visible state of the control associated with the action."""
        assert action.visible
        data_name = action.p1
        value = action.p2

        # get the control associated with the data_name
        # and change its state to match the data value
        control = self.controls[data_name]
        control.set(value)

    def set_view_size(self):
        """Set the viewing size from the values in data."""
        x, y = self.data.get_viewer_size()
        self.canvas.config(width=x, height=y)
        self.restart()

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
