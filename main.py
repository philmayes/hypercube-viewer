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
import enum
from functools import partial
import os
import random
import tkinter as tk
from tkinter import ttk, messagebox

from action import Action, ActionQueue, Cmd
import controls
from controls import DISABLED, ENABLED, ACTIVE
from data import Data
import dims
from dims import X, Y, Z    # syntactic sugar for the first three dimensions
import display
from preferences import Preferences
from hints import Hints
from html_viewer import HtmlViewer, Name
import help
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


class Reset(enum.IntFlag):
    FACTORY = 1 # restore factory settings
    DATA = 2    # restore settings at beginning
    DIM = 4     # change the number of dimensions
    ASPECT = 8  # change the aspect ratios
    VIEW = 16   # change the viewer size


class App(tk.Frame):

    def __init__(self, root, args):
        tk.Frame.__init__(self, root)
        # set up hooks for program close
        self.root = root
        self.args = args
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind('<Key>', self.on_key)

        # create an instance for loading and saving data and get the filename
        # of the json file that holds data (.load_settings() and
        # .save_settings() will perform the actual transfers)
        # This is the canonical version of the persistent data. It is passed
        # into display.Viewer so that App and Viewer share the data.
        self.data = Data()
        self.data_file = utils.get_location("settings", "values.json")
        self.data.load(self.data_file)
        # set top-left position of window
        root.geometry(f'+{self.data.win_x}+{self.data.win_y}')
        self.actionQ = ActionQueue()    # queue of Action instances
        self.playback_index = -1        # if >= 0, we are replaying actionQ
        self.state = CLEAN
        self.construct_keymap()

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
        self.canvas.bind("<Button-1>", self.on_canvas)

        # construct the viewer and the wireframe
        self.viewer = display.Viewer(self.data, self.canvas)
        self.hints = Hints(self.viewer)
        self.html_viewer = HtmlViewer(self.viewer)

        # create a frame for controls and add them
        self.left_frame = tk.Frame(self)
        self.left_frame.grid(row=0, column=0, sticky=tk.NW)
        self.construct_controls()
        self.add_controls(self.left_frame, 0, 0)
        self.buttons = (self.replay_button, self.stop_button, self.record_button, self.play_button)

        self.add_menu()
        self.load_settings()
        self.reset(Reset.DIM | Reset.ASPECT | Reset.VIEW)

        pubsub.subscribe('reset', self.reset)
        pubsub.subscribe('prefs', self.set_prefs)
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
        self.aspect = tk.Entry(frame, width=12)
        self.aspect.grid(row=0, column=0, sticky=tk.W)
        self.aspect.bind('<FocusOut>', self.on_aspect)
        self.aspect.bind('<Return>', self.on_aspect)
        self.aspect.hint_id = "aspect"

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
        edit.add_command(label="Factory reset", command=self.on_factory_reset)
        edit.add_command(label="Preferences...", command=self.on_prefs)
        menubar.add_cascade(label="Edit", menu=edit)

        help = tk.Menu(menubar, tearoff=0)
        help.add_command(label="Help", command=self.on_help)
        help.add_command(label="Keyboard shortcuts", command=self.on_help_keys)
        help.add_command(label="About", command=partial(self.hints.show_static, "about"))
        menubar.add_cascade(label="Help", menu=help)
        self.root.config(menu=menubar)

    def add_movement_controls(self, parent_frame, row, col):
        """Add up/down/left/right controls to the window."""
        frame = tk.Frame(parent_frame)
        frame.grid(row=row, column=col, sticky=tk.W, padx=4)
        row = 0
        Zm = Action(Cmd.ZOOM, '-')
        Zp = Action(Cmd.ZOOM, '+')
        Ml = Action(Cmd.MOVE, 'l')
        Mr = Action(Cmd.MOVE, 'r')
        Mu = Action(Cmd.MOVE, 'u')
        Md = Action(Cmd.MOVE, 'd')
        PB = Action(Cmd.PLAYBACK)
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
        self.restart_button = controls.Button(frame, text="Begin Again", command=self.on_restart)
        self.restart_button.grid(row=row, column=0, columnspan=3, sticky=tk.NSEW, padx=2, pady=2)
        self.restart_button.hint_id = "restart"
        # add a "Restart" control
        ctl = controls.Button(frame, text="Show Actions", command=self.on_list)
        ctl.grid(row=row, column=4, sticky=tk.NSEW, padx=2, pady=2)
        ctl.hint_id = "list"
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
            'Color of\nface',
            )
        for col, label in enumerate(labels):
            ctl = tk.Label(frame, text=label)
            ctl.grid(row=row, column=col, sticky=tk.W, padx=2, pady=2)
        row += 1

        for plane in dims.planes:
            control = controls.PlaneControl(frame, row, plane[0], plane[1], self)
            self.dim_controls.append(control)
            control.show_colors(self.data)
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
                          values=[str(n) for n in range(dims.MIN, dims.MAX+1)],
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
        self.viewer_size = tk.Entry(frame, width=12)
        self.viewer_size.grid(row=0, column=0, sticky=tk.W)
        self.viewer_size.bind('<FocusOut>', self.on_viewer_size)
        self.viewer_size.bind('<Return>', self.on_viewer_size)
        self.viewer_size.hint_id = "viewsize"

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
            'show_steps',
            'show_center',
            'show_perspective',
            'show_vp',
            'depth',
            'ghost',
            'angle',
            'auto_scale',
            'opacity',
            ):
            control = self.controls[dataname]
            control.add_control(frame, row, 1)
            row += 1
        # show_hints is treated separately as it lives in a different column
        control = self.controls['show_hints']
        control.add_control(frame, row, 0)
        row += 1

    def construct_controls(self):
        """Construct controls in a dictionary."""
        self.controls = {
            'show_faces': controls.CheckControl('Show faces', underline=5),
            'show_edges': controls.CheckControl('Show edges', underline=5),
            'show_nodes': controls.CheckControl('Show corners', underline=5),
            'show_steps': controls.CheckControl('Show intermediate steps', underline=5),
            'show_center': controls.CheckControl('Show center', underline=8),
            'show_perspective': controls.CheckControl('Perspective view', underline=0),
            'show_vp': controls.CheckControl('Show vanishing point', underline=5),
            'depth': controls.SlideControl('Depth of perspective:', 2.0, 10.0, 0.5),
            'ghost': controls.SlideControl('Amount of ghosting:', 0, 10, 1),
            'angle': controls.SlideControl('Rotation per click in degrees:', 1, 20, 1),
            'auto_scale': controls.SlideControl('Resizing during rotation:', 0.90, 1.10, 0.02),
            'opacity': controls.SlideControl('Opacity:', 0.1, 1.0, 0.1),
            'replay_visible': controls.CheckControl('Replay with original\nvisibility settings'),
            'frame_rate': controls.ComboControl('Frame rate of video:', ['24', '25', '30', '60', '120']),
            'show_hints': controls.CheckControl('Show hints'),
            # The following datanames are changed in preferences and have no
            # widget in this window. They exist here for the benefit of
            # keyboard shortcuts, see key_visible().
            'show_coords': None,
            "show_node_ids": None,
            "show_4_narrow": None,
            "show_4_gray": None,
        }

        # set up a sleazy but convenient way of associating the control
        # and the callback
        callback = self.visibility_action
        for dataname, control in self.controls.items():
            if control:
                control.set_data(dataname, self.data)
                control.callback = callback
                # show_hints uses a different callback
                if dataname == "show_hints":
                    control.callback = self.on_hints
                # If this control is a slider, tell the action queue so it is able
                # to merge successive values together
                if isinstance(control, controls.SlideControl) or isinstance(control, controls.ComboControl):
                    ActionQueue.sliders.append(dataname)

    def construct_keymap(self):
        """Construct the mapping from tkinter key events to actions."""
        self.key_map = {
            "f": (self.key_visible, "show_faces"),
            "e": (self.key_visible, "show_edges"),
            "c": (self.key_visible, "show_nodes"),
            "i": (self.key_visible, "show_steps"),
            "t": (self.key_visible, "show_center"),
            "p": (self.key_visible, "show_perspective"),
            "v": (self.key_visible, "show_vp"),

            "d": (self.key_slider, "depth"),
            "g": (self.key_slider, "ghost"),
            "r": (self.key_slider, "angle"),
            "z": (self.key_slider, "auto_scale"),
            "0": (self.key_rotate, None),

            "minus": (self.key_action, Action(Cmd.ZOOM, '-')),
            "plus": (self.key_action, Action(Cmd.ZOOM, '+')),
            "left": (self.key_action, Action(Cmd.MOVE, 'l')),
            "right": (self.key_action, Action(Cmd.MOVE, 'r')),
            "up": (self.key_action, Action(Cmd.MOVE, 'u')),
            "down": (self.key_action, Action(Cmd.MOVE, 'd')),
            "h": (self.key_visible, "show_hints"),

            "s": (self.key_visible, "replay_visible"),
            "space": (self.key_action, Action(Cmd.PLAYBACK)),
            "escape": (self.key_passthrough, self.on_escape),
            "a": (self.key_passthrough, self.on_list),

            "f1": (self.key_passthrough, self.on_help),

            # keys for values that are set in preferences
            "o": (self.key_visible, "show_coords"),
            "n": (self.key_visible, "show_node_ids"),
            "w": (self.key_visible, "show_4_narrow"),
            "q": (self.key_visible, "show_4_gray"),
        }

    def copy_data(self, from_data: Data, skip=False):
        """Update the data settings from another instance of Data().

        This function is used for several purposes: for a full factory reset,
        and to reset values as they were when starting. For the latter, there
        are certain settings that the user will expect to remain the same, and
        so skip is supplied to leave those untouched.

        This function is used for several purposes:
        * For a full factory reset
        * To reset values as they were when starting. There are certain
          settings that the user will expect to remain the same, and so
          skip is supplied to leave those untouched.
        * To update preferences. For this, we need to know what has changed
          so we can push events on the actionQ.
        """
        changed = []
        for attr in from_data.__dict__:
            old_value = getattr(self.data, attr)
            new_value = getattr(from_data, attr)
            if new_value != old_value:
                if skip and attr in ("replay_visible", "frame_rate"):
                    # Keep the current replay_visible value because if it started
                    # out one way but the user changed it, we don't want to use
                    # the original setting. Same applies to frame_rate.
                    continue
                setattr(self.data, attr, new_value)
                if attr in self.controls:
                    control = self.controls[attr]
                    if control:
                        control.set(new_value)
                changed.append(attr)
        return changed

    def get_previous_action(self):
        if self.actionQ:
            return self.actionQ[-1]
        if self.viewer.actions:
            return self.viewer.actions[-1]

    def hint_manager(self):
        try:
            hint_id = None
            # get the widget under the cursor
            x, y = self.winfo_pointerxy()
            widget = self.winfo_containing(x, y)
            if widget:
                # get possible hint id for this control...
                if hasattr(widget, "hint_id"):
                    hint_id = widget.hint_id
            self.hints.show(hint_id)
        except:
            # specifically, we are catching a popdown exception in
            # winfo_containing, but why not catch everything?
            pass

    #
    # key_xxxx() functions are callbacks from on_key()
    #

    def key_action(self, keysym, state, action):
        if not state & 0x20004: # ignore Ctl and Alt modifiers
            self.queue_action(action)

    def key_passthrough(self, keysym, state, function):
        function()

    def key_rotate(self, keysym, state, value):
        keysym = int(keysym)
        direction = '+' if state & 4 else '-'
        if keysym == 0:
            self.on_random(direction)
        else:
            dim = keysym - 1
            if dim < self.data.dims:
                plane = self.dim_controls[dim]
                self.on_rotate(direction, plane)

    def key_slider(self, keysym, state, dataname):
        control = self.controls[dataname]
        step = -1 if keysym.islower() else 1
        control.step(step)
        self.visibility_action(dataname)

    def key_visible(self, keysym, state, dataname):
        if not state & 0x20004: # ignore Ctl and Alt modifiers
            control = self.controls[dataname]
            if control:
                # Change the value and visible appearance of the control.
                # In visibility_action, the value will be extracted and put
                # into an Action object. The value is not set into the data
                # instance until run() processes the queue.
                control.xor()
            else:
                # If there is no control, it is because the keystroke is a
                # shortcut for a value managed by preferences, so flip it
                # here and visibility_action will extract it from self.data.
                self.data.xor(dataname)
            self.visibility_action(dataname)

    def load_settings(self):
        """Load initial settings."""
        self.aspect.delete(0,999)
        self.aspect.insert(0, self.data.aspects)
        self.viewer_size.delete(0,999)
        self.viewer_size.insert(0, self.data.viewer_size)
        for dataname, control in self.controls.items():
            value = getattr(self.data, dataname)
            if control:
                control.set(value)

    def on_aspect(self, _):
        """The aspect ratios have been changed.
        
        If they're valid, save them and rebuild the viewer,
        else highlight the edit control in yellow
        """
        aspects = self.aspect.get()
        if self.data.validate_aspects(aspects):
            self.aspect.configure(bg='white')
            if aspects != self.data.aspects:
                self.data.aspects = aspects
                self.stop()
                self.queue_action(Action(Cmd.RESET, Reset.ASPECT))
        else:
            self.aspect.configure(bg='yellow')

    def on_canvas(self, x):
        """Left-click on canvas."""
        self.hints.stop_static()

    def on_close(self):
        # close the app
        data = self.data
        data.win_x = self.root.winfo_x()
        data.win_y = self.root.winfo_y()
        data.dims = int(self.dim_choice.get())
        data.save(self.data_file)
        self.root.destroy()

    def on_dim(self, param):
        """User has selected the number of dimensions via the combo box."""
        dims = int(param.widget.get())
        if dims != self.data.dims:
            self.data.dims = dims
            self.stop()
            self.queue_action(Action(Cmd.RESET, Reset.DIM))

    def on_escape(self):
        """User has hit ESC key."""
        self.html_viewer.clear()
        self.stop()

    def on_factory_reset(self):
        self.stop()
        self.queue_action(Action(Cmd.RESET, Reset.FACTORY | Reset.DIM | Reset.VIEW))

    def on_help(self):
        if not self.html_viewer.clear_if_showing(Name.HELP):
            self.html_viewer.show(help.help, Name.HELP)

    def on_help_keys(self):
        if not self.html_viewer.clear_if_showing(Name.KEYS):
            self.html_viewer.show(help.keys, Name.KEYS)

    def on_hints(self, dataname):
        """User has toggled whether hints are to be shown."""
        control = self.controls[dataname]
        value = bool(control.get())
        if not value:
            # Special case: when turning off hints, the hint for this control
            # wouldn't get hidden by hint_manager because Hints.active==False,
            # so force it to be hidden here.
            self.hints.show(None)
        self.data.show_hints = value
        self.hints.visible(value)

    def on_key(self, event):
        # print(event, 'state=', hex(event.state))
        focus = self.focus_get()
        # Ignore keystroke when editing a field
        if focus == self.aspect or focus == self.viewer_size:
            return
        # Convert to lower to simplify the keymap for, say, A nd a
        lower = event.keysym.lower()
        # Simplify the keymap further by forcing all digits to zero
        if lower.isdigit():
            lower = '0'
        # Look for an action and a possible parameter
        callback, value = self.key_map.get(lower, (None, None))
        # if there is a handler for this keystroke, execute it
        if callback:
            callback(event.keysym, event.state, value)

    def on_list(self):
        if not self.html_viewer.clear_if_showing(Name.ACTIONS):
            htm = ""
            if self.viewer.actions:
                for action in self.viewer.actions:
                    htm += str(action)
                    htm += "<br>"
            else:
                htm = "There are no actions to list."
            self.html_viewer.show(htm, Name.ACTIONS)

    def on_play_end(self, state):
        assert state is False
        self.set_button_state(IDLE)

    def on_play_video(self):
        """Show the last video recorded."""
        play_file = None
        playing = self.viewer.video_reader is not None
        self.viewer.stop = playing
        if not playing:
            play_file = utils.find_latest_file(self.viewer.output_dir)
        if play_file:
            self.set_button_state(PLAYING)
            self.viewer.video_play(play_file)
        else:
            self.set_button_state(IDLE)

    def on_prefs(self):
        win_x = self.root.winfo_x()
        win_y = self.root.winfo_y()
        Preferences(self.data, win_x, win_y)

    def on_random(self, direction):
        """Rotate the wireframe randomly in 3 dimensions."""

        # Make a list of every dimension. A random dimension is chosen from
        # this list and then removed to ensure that a later pick has a
        # different value.
        dims = list(range(self.data.dims))

        # The first dimension is always X or Y so we can see it on screen
        dim1 = random.randint(X, Y)
        dims.remove(dim1)

        # If the previous action was also a random rotation, reuse its second
        # dimension to reduce the jerkiness unless that is dim1
        # otherwise just pick a random one
        prev = self.get_previous_action()
        if prev and prev.cmd == Cmd.ROTATE and prev.p3 is not None:
            dim2 = prev.p2
            if dim2 == dim1:
                dim2 = random.choice(dims)
        else:
            dim2 = random.choice(dims)
        dims.remove(dim2)

        # pick the 3rd dimension from the remaining ones
        dim3 = random.choice(dims)

        # Create and queue the action
        action = Action(Cmd.ROTATE, dim1, dim2, dim3, direction)
        self.queue_action(action)

    def on_restart(self):
        self.stop()
        self.queue_action(Action(Cmd.RESET, Reset.DATA))

    def on_rotate(self, direction, dim_control):
        """Rotate the wireframe."""
        action = Action(Cmd.ROTATE, dim_control.dim1, dim_control.dim2, None, direction)
        self.queue_action(action)

    def on_stop(self):
        """User has asked for the current and pending actions to be stopped."""
        self.stop()

    def on_view_files(self):
        """Show the folder where video output is saved."""
        os.startfile(self.viewer.output_dir)

    def on_viewer_size(self, _):
        """The viewer_size ratios have been changed.
        
        If they're valid,
            if they've changed, save them and rebuild the viewer,
        else highlight the edit control in yellow
        """
        viewer_size = self.viewer_size.get()
        if self.data.validate_viewer_size(viewer_size):
            self.viewer_size.configure(bg='white')
            if viewer_size != self.data.viewer_size:
                self.data.viewer_size = viewer_size
                self.stop()
                self.queue_action(Action(Cmd.RESET, Reset.VIEW))
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

    def reset(self, flags: Reset):
        """Reset the program in various ways.

        It is called:
            at initial start
            at restart
            when the dimensions, aspect or view size has changed
        The flags parameter indicates what actions to take.

        NOTE: this must not be called directly except at initial start
        because there may be an action in progress that is relying on old
        values and will crash. This is weird: flushing actionQ and forcing
        stop does not solve the problem. The fix is that reset calls must
        be made via the actionQ. In this way, the prior action will have
        completed.
        """
        if flags & Reset.FACTORY:
            self.copy_data(Data())
            self.load_settings()

        if flags & Reset.DATA:
            self.copy_data(self.data_copy, skip=True)
            self.load_settings()

        if flags & Reset.DIM:
            dim_count = self.data.dims
            self.dim_choice.set(str(dim_count))
            # create or destroy the dimension controls as appropriate
            for dim, control in enumerate(self.dim_controls):
                if control.dim2 < dim_count:
                    if not control.active:
                        self.dim_controls[dim].add_controls()
                        control.show_colors(self.data)
                else:
                    if control.active:
                        self.dim_controls[dim].delete_controls()

        if flags & Reset.VIEW:
            x, y = self.data.get_viewer_size()
            self.canvas.config(width=x, height=y)

        if flags & Reset.ASPECT:
            aspects = self.aspect.get()
            self.data.aspects = aspects

        # make a copy of the data for when we replay with visibility
        self.data_copy = copy.copy(self.data)
        self.viewer.init()
        self.viewer.display()

        self.hints.visible(self.data.show_hints)
        self.set_record_state(False)
        self.set_button_state(CLEAN, force=True)
        self.restart_button.state = DISABLED

        # For reasons I do not understand, the controls "ghost" and "angle"
        # trigger callbacks when their value is set. Flush the spurious actions.
        self.actionQ.clear()

    def run(self):
        """Run the actions on the action queue.

        https://stackoverflow.com/questions/18499082/tkinter-only-calls-after-idle-once
        """
        if self.playback_index >= 0:
            # remove any HTML window
            self.html_viewer.clear()
            # we're playing back the actions previously taken
            if self.playback_index < len(self.viewer.actions):
                # there are more actions to take
                action = self.viewer.actions[self.playback_index]
                self.playback_index += 1
                act = True
                if action.visible:
                    # only replay visibility actions when asked
                    if act := self.data.replay_visible:
                        # change the value in .data
                        # and the visible state of the control
                        self.set_data_value(action)
                        self.set_visible_state(action)
                if act:
                    self.viewer.take_action(action, playback=True)
            else:
                # we've played back all the actions, so cancel playback
                self.playback_index = -1
                self.set_button_state(IDLE)

        elif self.actionQ:
            # the user has initiated an action like rotate, zoom, etc.
            # and it has been placed on a queue. Take it off the queue.
            action = self.actionQ[0]
            del self.actionQ[0]
            # remove any HTML window
            self.html_viewer.clear()
            if action.cmd == Cmd.PLAYBACK:
                # the action is to play back all the actions up until now,
                self.playback_index = 0
                self.set_button_state(REPLAYING)
                if self.data.replay_visible:
                    # restore most data settings in place at the beginning
                    self.copy_data(self.data_copy, skip=True)
                self.viewer.init(playback=True)
                self.viewer.display()
            else:
                # It's a regular action. Enable the replay button
                # (it would have been disabled if the queue were formerly empty)
                self.set_button_state(RUNNING)
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
                        self.show_colors()
                    elif vis == 'depth':
                        self.viewer.set_depth()
                    elif vis == 'angle':
                        self.viewer.set_rotation()
                    elif vis == 'auto_scale':
                        need_action = False
                    elif vis == 'replay_visible':
                        need_action = False
                    elif vis in ('show_4_gray', 'show_edges'):
                        self.show_colors()

                if need_action:
                    # execute the action
                    self.viewer.take_action(action)
                if real_ghost:
                    # We turned off ghosting. Turn it back on.
                    self.data.ghost = real_ghost

                if not self.actionQ:
                    # if there are no more actions queued, it makes no sense
                    # to offer a "Stop" action, so disable the button
                    state = IDLE if self.viewer.actions else CLEAN
                    self.set_button_state(state)
        else:
            self.hint_manager()

        # wait 10ms, which allows tk UI actions, then check again
        self.root.after(10, self.run)

    def set_button_state(self, new_state: int, force: bool=False):
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

    def set_data_value(self, action: Action):
        assert action.visible
        data_name = action.p1
        value = action.p2

        # change the data value
        old_data = getattr(self.data, data_name)
        assert type(value) is type(old_data)
        setattr(self.data, data_name, value)

    def set_prefs(self, new_data):
        for dataname in self.copy_data(new_data, skip=True):
            self.visibility_action(dataname)

    def set_record_state(self, active=None):
        """Set or Xor the record button.

        active == None:     xor the recording state
        active == boolean:  recording [not] wanted
        """
        if active is None:
            active = not self.viewer.recording
        self.viewer.video_record(active)
        self.set_button_state(self.state, force=True)

    def set_replay_button(self, state):
        """Set the Replay button as disabled, ready or replaying."""
        self.replay_button.state = state

    def set_visible_state(self, action: Action):
        """Set the visible state of the control associated with the action."""
        assert action.visible
        dataname = action.p1
        value = action.p2

        # Get the control associated with the data_name (if any; might be
        # adjusted in prefs) and change its state to match the data value.
        control = self.controls.get(dataname, None)
        if control:
            control.set(value)

    def stop(self):
        """Stop the current and pending actions."""
        # ask the viewer to stop ASAP
        self.viewer.stop = True
        # discard all actions in the pending queue
        self.actionQ.clear()
        # stop any playback
        self.playback_index = -1
        # adjust button states
        self.set_button_state(IDLE)

    def visibility_action(self, dataname):
        """Execute a visibility action."""
        # get the control associated with the data_name and the present value
        control = self.controls.get(dataname, None)
        if control:
            control_value = control.get()
            value = self.data.coerce(control_value, dataname)
        else:
            # Some visibility settings are adjusted in preferences, so they
            # don't have a control in this window; the new value has already
            # been put into self.data by copy_data().
            # Alternatively, the shortcut key for a setting in preferences has
            # been typed and the new value has been set in key_visible().
            value = getattr(self.data, dataname)
        action = Action(Cmd.VISIBLE, dataname, value)
        self.queue_action(action)

    def show_colors(self):
        for control in self.dim_controls:
            control.show_colors(self.data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Hypercube')
    parser.add_argument("-t", "--test", action="store_true", help="run in test mode")
    args = parser.parse_args()
    root = tk.Tk()
    app = App(root, args)
    try:
        # if compiled with pyinstaller, close any flash screen
        import pyi_splash
        pyi_splash.close()
    except:
        pass
    root.mainloop()
