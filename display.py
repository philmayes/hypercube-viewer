#!/bin/env python
"""
There are four primitive actions:
    plot    calculate new positions of nodes etc.
    draw    project nodes onto an xy plane
    show    show the xy plane on a window
    write   write the xy plane to video

    display()   executes draw, show, write

"""

import math
import os
import re
import time

import cv2
import numpy as np
from PIL import Image
from PIL import ImageTk

import colors
import utils
import wireframe as wf

X, Y, Z = range(3)          # syntactic sugar for the first three dimensions
ROTATION_SCALE = 1.0#0.995  # amount to scale for each rotation step
SCALE = 1.1                 # fraction by which to zoom in/out
TRANSLATE = 40              # amount in pixels to move up/down/left/right
cmd_to_values = {
    'l': (X, -TRANSLATE),
    'r': (X, TRANSLATE),
    'u': (Y, -TRANSLATE),
    'd': (Y, TRANSLATE),
    }
FRAME_RATE = 30

class Viewer:
    """Display hypercube objects on a tkinter canvas."""

    ghost_to_factor = {
        0: 0.0,
        1: 0.6,
        2: 0.7,
        3: 0.75,
        4: 0.8,
        5: 0.85,
        6: 0.9,
        7: 0.95,
        8: 0.98,
        9: 0.99,
        10: 1.0,
    }

    def __init__(self, data, output_dir, canvas):
        self.data = data
        self.output_dir = output_dir
        # fraction of screen that the wireframe should occupy
        self.screen_fraction = 0.7
        self.canvas = canvas
        self.actions = []

        # visibility settings...
        self.node_radius = 4
        self.center_radius = 1
        self.vp_radius = 2
        self.frame_time = 1 / FRAME_RATE

    def init(self, playback=False):
        """Initialize the viewer size and dimension count."""
        self.width, self.height = self.data.get_viewer_size()
        self.img = np.zeros((self.height, self.width, 3), np.uint8)
        # set the vanishing point in the middle of the screen
        # and somewhere along the z-axis
        self.vp = [int(round(self.width/2)),
                   int(round(self.height/2)),
                   int(round(self.width * self.data.depth))]
        # calculate the pixel sizes for all dimensions:
        # get the aspect ratios for all dimensions and the largest ratio
        ratios = [int(r) for r in self.data.aspects.split(':')]
        max_r = max(ratios)
        # calculate the size of the largest dimension in pixels
        screen_size = min(self.width, self.height) * self.screen_fraction
        # scale all dimensions to that one
        sizes = [screen_size * r / max_r for r in ratios]
        self.set_rotation()

        # calculate top left position
        orgx = (self.width - sizes[X]) / 2
        orgy = (self.height - sizes[Y]) / 2

        # construct a wireframe object
        self.wireframe = wf.Wireframe(self.data.dims)
        self.wireframe.add_shape_sizes(orgx, orgy, sizes)
        self.make_normalize_translations()

        # We sort the edges and faces in z-order so they display correctly.
        # These flags are set when this is needed.
        self.sort_edges = True
        self.sort_faces = True

        # initialize recording settings
        # When initializing the viweer for playing back, we:
        # * skip clearing the list of actions;
        # * continue to let video recording run;
        if not playback:
            self.actions = []
            self.recording = False
            self.playing_back = False
            self.video = None

        # remove any previous drawing
        cv2.rectangle(self.img, (0, 0), (self.width, self.height), colors.bg, -1)

    def display(self):
        t1 = time.process_time()
        self.draw()
        self.show()
        self.write()
        t2 = time.process_time()
##        print('display took %0.3f ms' % ((t2-t1)*1000.0))
        # wait for the time a video frame would take to play back
        # (although writing a frame often takes longer than this),
        # thus emulating what a video would look like
        pause = self.frame_time - t2 + t1
        if pause > 0.0:
            time.sleep(pause)

    def draw(self):
        """Draw the wireframe onto the xy plane."""

        if self.data.ghost:
            # leave a shadow of the previous frame
            factor = Viewer.ghost_to_factor[self.data.ghost]
            np.multiply(self.img, factor, out=self.img, casting='unsafe')
        else:
            # clear the previous frame
            cv2.rectangle(self.img, (0, 0), (self.width, self.height), colors.bg, -1)

        wireframe = self.wireframe
        if self.data.show_vp and self.data.show_perspective:
            cv2.circle(self.img,
                       (self.vp[X], self.vp[Y]),
                       self.vp_radius,
                       colors.vp,
                       -1)

        if self.data.show_center:
            cv2.circle(self.img,
                       (self.get_xy(wireframe.center)),
                       self.center_radius,
                       colors.center,
                       -1)

        if self.data.show_edges:
            # Use reversed so that edges are drawn from the back and appear to
            # overlap correctly. Especially important for perspective view.
            # This doesn't help when the user rotates the wireframe 180 degrees
            # around the x- or y-axis. For that, I think sorting the edges is
            # needed; I haven't investigated the performance cost.
            # for n1, n2, color in reversed(wireframe.edges):
            if self.sort_edges:
                wireframe.sort_edges()
                self.sort_edges = False
            for n1, n2, color in wireframe.edges:
                node1 = wireframe.nodes[n1]
                node2 = wireframe.nodes[n2]
                cv2.line(self.img,
                        self.get_xy(node1),
                        self.get_xy(node2),
                        color,
                        3)

        if self.data.show_faces:
            if self.sort_faces:
                wireframe.sort_faces()
                self.sort_faces = False
            for n1, n2, n3, n4, color in wireframe.faces:
                pts = [self.get_xy(wireframe.nodes[n1]),
                       self.get_xy(wireframe.nodes[n2]),
                       self.get_xy(wireframe.nodes[n3]),
                       self.get_xy(wireframe.nodes[n4])]
                shape = np.array(pts)
                cv2.fillConvexPoly(self.img, shape, color)

        if self.data.show_nodes or self.data.show_coords:
            for node in wireframe.nodes:
                xy = self.get_xy(node)
                if self.data.show_nodes:
                    cv2.circle(self.img,
                            xy,
                            self.node_radius,
                            colors.node,
                            -1)
                if self.data.show_coords:
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    values = [int(round(v)) for v in node[:-1]]
                    text = str(values)
                    cv2.putText(self.img, text, (xy[X] + 5, xy[Y] + 3), font, 0.5, colors.text)

    def get_xy(self, node):
        """Given a node, return orthogonal or perspective x,y

                    orthogonal projection on screen
                    |      perspective projection on screen
                    |      |
        window------O------P--------V---------------------> x- or y-axis
        |           |\     |        |
        |           | \    |        |
        |           |  \   |        |
        |           |   \  |        |
        |           |    \ |        |
        |           |     \|        |
        |     node: N      '        |
        |                   \       |
        |                    \      |
        |                     \     |
        |                      \    |
        |                       \   |
        |                        \  |
        V                         \ |
        z-axis                     \|
                                    .vanishing point
        """
        x = node[X]
        y = node[Y]
        if self.data.show_perspective:
            vp = self.vp
            f = node[Z] / vp[Z]
            x += (vp[X] - node[X]) * f
            y += (vp[Y] - node[Y]) * f
        return (int(round(x)), int(round(y)))

    def make_normalize_translations(self):
        """Make 2 matrices for moving to (0,0,0,...) and back."""
        wireframe = self.wireframe        
        normalize = [-x for x in wireframe.center]
        self.norm_matrix = wireframe.get_translation_matrix(normalize)
        self.denorm_matrix = wireframe.get_translation_matrix(wireframe.center)

    def record(self, state):
        if state:
            assert not self.video
            assert not self.recording
            self.recording = True
        else:
            self.video = None
            self.recording = False

    def repeat_frame(self, count):
        """Wait for <count> frames."""
        for _ in range(count):
            self.display()

    def rotate_all(self, dim1, dim2, theta, dim3=-1):
        """Rotate all wireframes about their center, around one or two planes
            by a given angle."""
        count = self.rotation_count if self.data.show_steps else 1
        delta = theta / count
        if dim3 < 0:
            # we're rotating about a single plane so move in regular steps
            angles = [delta] * count
        else:
            # We're rotating about two planes, so increase the steps linearly.
            # The list is be used in the reverse order for the second plane.
            # (Repeating the call with the sign of theta reversed does not
            # quite return to the original position??!)
            angles = [0.0] * count
            step = delta * 2 / (count - 1)
            value = 0.0
            for n in range(count):
                angles[n] = value
                value += step
        if theta < 0.0:
            angles.reverse()
        assert math.isclose(sum(angles), theta)
        wireframe = self.wireframe
        for n in range(count):
            if dim1 < wireframe.dims and dim2 < wireframe.dims:
                # calculate the rotation needed
                angle = angles[-n - 1]
                angle2 = angle
                matrix = wireframe.get_rotate_matrix(dim1, dim2, angle)
                if dim3 >= 0:
                    angle = angles[n]
                    matrix = wireframe.get_rotate_matrix(dim1, dim3, angle, matrix)
                # move, rotate, move back
                wireframe.transform(self.norm_matrix)
                wireframe.transform(matrix)
                wireframe.transform(self.denorm_matrix)
            else:
                print('too big', dim1, dim2, wireframe.dims)
            self.display()
            if ROTATION_SCALE != 1.0:
                self.scale_all(ROTATION_SCALE, 1)
        self.sort_edges = True
        self.sort_faces = True

    def scale_all(self, scale, count=10):
        """Scale all wireframes by a given scale, centered on the center of the wireframe."""

        scale = math.pow(scale, (1 / count))
        wireframe = self.wireframe
        for _ in range(count):
            matrix = wireframe.get_scale_matrix(scale)
            # move, scale, move back
            wireframe.transform(self.norm_matrix)
            wireframe.transform(matrix)
            wireframe.transform(self.denorm_matrix)
            self.display()

    def set_depth(self):
        """The perspective depth has changed."""
        self.vp[2] = int(round(self.width * self.data.depth))

    def set_rotation(self):
        self.rotation = float(self.data.angle) * np.pi / 180
        self.rotation_count = self.data.angle * 2

    def show(self):
        """Display the xy plane on the tkinter canvas."""
        image = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        self.image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor='nw', image=self.image)
        self.canvas.update()

    re_dim = re.compile(r'D([3-9])')
    re_move = re.compile(r'M([udlr])')
    re_rotate = re.compile(r'R(\d)(\d)(\+|-)')
    re_zoom = re.compile(r'Z(\+|-)')
    def take_action(self, action: str, playback=False):
        """Perform and display the supplied action."""
        acted = True
        if match := Viewer.re_rotate.match(action):
            rotation = self.rotation if match.group(3) == '+' else -self.rotation
            self.rotate_all(int(match.group(1)), int(match.group(2)), rotation)
        elif match := Viewer.re_zoom.match(action):
            if match.group(1) == '+':
                self.scale_all(SCALE)
            else:
                self.scale_all(1 / SCALE)
        elif match := Viewer.re_move.match(action):
            dim, amount = cmd_to_values[match.group(1)]
            self.translate_all(dim, amount)
        elif match := Viewer.re_dim.match(action):
            self.data.dims = match.group(1)
            self.init()
        elif match := Viewer.re_video.match(action):
            self.video(match.group(1))
            acted = False
        else:
            acted = False

        if acted:
            # Draw the wireframe onto the xy plane
            self.draw()
            # Show the xy plane on the tkinter canvas
            self.show()
            # Write to video if needed
            self.write()
            # Save the action for possible playback
            # We /don't/ keep history when the history is being played back
            if not playback:
                self.actions.append(action)

    def start_video(self):
        if not self.video:
            types = (('mp4', 'mp4v'), ('avi', 'XVID'))
            ext, codec = types[0]
            assert not self.video
            fname = utils.make_filename('video', ext)
            output = os.path.join(self.output_dir, fname)
            self.video = cv2.VideoWriter(output,
                                         cv2.VideoWriter_fourcc(*codec),
                                         FRAME_RATE,
                                         (self.width, self.height))
        else:
            # I /think/ start_video is only called when there isn't one
            assert 0

    def translate_all(self, dim, amount):
        """Translate (move) the wireframe along a given axis by a certain amount.

        In practise, dim is always 0 or 1.
        """
        count = 10 if self.data.show_steps else 1
        delta = amount / count
        wireframe = self.wireframe
        vector = [0] * wireframe.dims
        vector[dim] = delta
        matrix = wireframe.get_translation_matrix(vector)
        for n in range(count):
            wireframe.transform(matrix)
            wireframe.center[dim] += delta
            self.make_normalize_translations()
            self.display()

    def write(self):
        """Write the current xy plane to a video file.

        Takes about 80ms.
        """
        if self.recording:
            # By deferring file creation until an actual write is issued,
            # we avoid creating an empty video file when the user starts
            # and then stops video recording.
            if not self.video:
                self.start_video()
            self.video.write(self.img)
