#!/bin/env python
"""
There are four primitive actions:
    plot        calculate new positions of nodes etc.
    draw        project nodes onto an xy plane
    show        show the xy plane on a window
    video_write write the xy plane to video

    display()   executes draw, show, video_write

"""

import math
import os
import time

import cv2
import numpy as np
from PIL import Image
from PIL import ImageTk

from action import Action, ActionQueue, Cmd
import colors
from data import Data
from dims import MAX
from dims import X, Y, Z    # syntactic sugar for the first three dimensions
import pubsub
import utils
import wireframe as wf


class Viewer:
    """Display hypercube objects on a tkinter canvas."""

    # map the slider values to the amount of ghosting
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
    SCALE = 1.1  # fraction by which to zoom in/out
    TRANSLATE = 40  # amount in pixels to move up/down/left/right
    direction_to_values = {
        "l": (X, -TRANSLATE),
        "r": (X, TRANSLATE),
        "u": (Y, -TRANSLATE),
        "d": (Y, TRANSLATE),
    }
    # Construct the ratio of edge size to screen size such that the wireframe
    # will be nearly always fully displayed on the screen for all rotations.
    # These numbers were chosen pragmatically.
    r3 = 0.56
    r10 = 0.3
    ratio = math.pow(r10 / r3, 1 / 7)
    screen_fraction = [r3] * (MAX + 1)
    for dim in range(4, MAX + 1):
        screen_fraction[dim] = screen_fraction[dim - 1] * ratio

    def __init__(self, data: Data, canvas):
        self.data = data
        # make a directory to hold video output
        self.output_dir = utils.make_dir("output")
        # fraction of screen that the wireframe should occupy
        self.canvas = canvas
        self.actions = ActionQueue()
        self.recording = False
        self.video_reader = None
        self.video_writer = None
        self.id_rect = None
        self.id_text = None
        self.id_window = None

    def init(self, playback=False):
        """Initialize the viewer size and dimension count."""
        self.width, self.height = self.data.get_viewer_size()
        self.img = np.zeros((self.height, self.width, 3), np.uint8)
        # set the vanishing point in the middle of the screen
        # and somewhere along the z-axis
        self.vp = [
            int(round(self.width / 2)),
            int(round(self.height / 2)),
            int(round(self.width * self.data.depth)),
        ]
        # calculate the pixel sizes for all dimensions:
        # get the aspect ratios for all dimensions and the largest ratio
        ratios = [int(r) for r in self.data.aspects.split(":")]
        max_r = max(ratios)
        # calculate the size of the largest dimension in pixels
        screen_size = min(self.width, self.height) * Viewer.screen_fraction[self.data.dims]
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

        self.stop = False

        # initialize recording settings
        # When initializing the viewer for playing back, we:
        # * skip clearing the list of actions;
        # * continue to let video recording run;
        if not playback:
            self.actions.clear()
            self.recording = False
            self.video_writer = None
            self.video_reader = None

        # remove any previous drawing
        cv2.rectangle(self.img, (0, 0), (self.width, self.height), colors.bg, -1)

        # prime the canvas
        image = Image.fromarray(self.img)
        self.image = ImageTk.PhotoImage(image)
        self.id_image = self.canvas.create_image(0, 0, anchor="nw", image=self.image)
        self.clear_text()
        self.clear_window()

    def clear_text(self):
        self.canvas.delete(self.id_rect)
        self.canvas.delete(self.id_text)
        self.id_rect = None
        self.id_text = None

    def clear_window(self):
        self.canvas.delete(self.id_window)
        self.id_window = None

    def display(self):
        # Draw the wireframe onto the xy plane
        self.draw()
        # Show the xy plane on the tkinter canvas
        self.show()
        # Write to video if needed
        self.video_write()

    # @utils.time_function
    def draw(self):
        """Draw the wireframe onto the xy plane."""

        if self.data.ghost:
            # leave a shadow of the previous frame
            factor = Viewer.ghost_to_factor[self.data.ghost]
            np.multiply(self.img, factor, out=self.img, casting="unsafe")
        else:
            # clear the previous frame
            cv2.rectangle(self.img, (0, 0), (self.width, self.height), colors.bg, -1)

        wireframe = self.wireframe
        if self.data.show_vp:
            cv2.circle(
                self.img, (self.vp[X], self.vp[Y]), self.data.vp_radius, colors.vp, -1
            )

        if self.data.show_center:
            cv2.circle(
                self.img,
                (self.get_xy(wireframe.center)),
                self.data.center_radius,
                colors.center,
                -1,
            )

        if self.data.show_edges:
            w0 = self.data.edge_width
            w4 = self.data.show_4_narrow  # True: Line width is 1
            c4 = self.data.show_4_gray  # True: Line color is gray
            w4c4 = w4 or c4
            # If needed (because the wireframe has been rotated), the edges
            # are sorted in reverse z-order so that the edges at the front
            # overlay those at the back.
            if self.sort_edges:
                wireframe.sort_edges()
                self.sort_edges = False
            for n1, n2, color in wireframe.edges:
                node1 = wireframe.nodes[n1]
                node2 = wireframe.nodes[n2]
                width = w0
                if w4c4:
                    # Don't show width or color for higher dimensions
                    if n1 >= 8 or n2 >= 8:
                        if w4:
                            width = 1
                        if c4:
                            color = colors.dim4gray
                cv2.line(self.img, self.get_xy(node1), self.get_xy(node2), color, width)

        if self.data.show_faces:
            faces = wireframe.faces
            # see the sort explanation for edges
            if self.sort_faces:
                wireframe.sort_faces()
                self.sort_faces = False
            if self.data.opacity < 1.0:
                zmax = wireframe.get_face_z(faces[0])
                zmin = wireframe.get_face_z(faces[-1])
                zrange = zmax - zmin

            face_count = len(faces)
            start = 0
            if self.data.opacity == 1.0:
                start = face_count // 2
            for ndx in range(start, face_count):
                face = faces[ndx]
                # n0, n1, n2, n3, color = face
                # Get the x,y,z coordinates of each corner
                xyz0 = wireframe.nodes[face.node[0]][0:3]
                xyz1 = wireframe.nodes[face.node[1]][0:3]
                xyz2 = wireframe.nodes[face.node[2]][0:3]
                xyz3 = wireframe.nodes[face.node[3]][0:3]
                # Map those points onto the screen
                pts = [
                        self.get_xy(xyz0),
                        self.get_xy(xyz1),
                        self.get_xy(xyz2),
                        self.get_xy(xyz3),
                ]
                shape = np.array(pts)
                if self.data.opacity < 1.0:
                    # When the faces are translucent, draw every face
                    alpha = self.data.opacity
                    # scale the opacity from supplied value at front
                    # to fully opaque at back
                    z = wireframe.get_face_z(face)
                    alpha += (z - zmin) / zrange * (1.0 - alpha)
                    overlay = self.img.copy()
                    cv2.fillConvexPoly(overlay, shape, face.color)
                    self.img = cv2.addWeighted(overlay, alpha, self.img, 1-alpha, 0)
                else:
                    # When the faces are opaque
                    vec0 = xyz1 - xyz0
                    vec1 = xyz3 - xyz0
                    orth = np.cross(vec0, vec1)
                    if 1:#orth[Z] > 0:
                        # print(f"face={face.node} Z-vector = {orth[Z]:,.0f} = DRAW THIS FACE")
                        cv2.fillConvexPoly(self.img, shape, face.color)
                    else:
                        print(f"face={face.node} Z-vector = {orth[Z]:,.0f} = SKIP THIS FACE")
                        continue

        if self.data.show_nodes or self.data.show_node_ids or self.data.show_coords:
            radius = self.data.node_radius if self.data.show_nodes else 0
            # for node in wireframe.nodes:
            for index, node in enumerate(wireframe.nodes):
                xy = self.get_xy(node)
                if self.data.show_nodes:
                    cv2.circle(self.img, xy, radius, colors.node, -1)
                text = ""
                if self.data.show_node_ids:
                    text = str(index)
                if self.data.show_coords:
                    join = ":" if text else ""
                    values = [int(round(v)) for v in node[:-1]]
                    text = f"{text}{join}{values}"
                if text:
                    cv2.putText(
                        self.img, text, (xy[X] + radius, xy[Y] + 3),
                        cv2.FONT_HERSHEY_SIMPLEX, self.data.font_size,
                        colors.text
                    )

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

    # def repeat_frame(self, count):
    #     """Wait for <count> frames."""
    #     for _ in range(count):
    #         self.display()

    def rotate_all(self, dim1, dim2, theta, dim3=None):
        """Rotate all wireframes about their center, around one or two planes
        by a given angle."""
        wireframe = self.wireframe
        assert dim1 < wireframe.dims and dim2 < wireframe.dims
        if dim3 is not None:
            assert dim3 < wireframe.dims
        count = self.rotation_count if self.data.show_steps else 1
        delta = theta / count
        if dim3 is None:
            # we're rotating about a single plane so move in regular steps
            angles = [delta] * count
        else:
            # We're rotating about two planes, so increase the steps linearly.
            # The list is be used in the reverse order for the second plane.
            # (Repeating the call with the sign of theta reversed does not
            # quite return to the original position??!)
            angles = [0.0] * count
            if count > 1:
                step = delta * 2 / (count - 1)
                value = 0.0
                for n in range(count):
                    angles[n] = value
                    value += step
                assert math.isclose(sum(angles), theta)
            else:
                # gotta avoid a divide by zero!
                angles[0] = delta / 2
        if theta < 0.0:
            angles.reverse()
        scale = (self.data.auto_scale - 1.0) / count + 1.0
        for n in range(count):
            if self.stop:
                break
            # calculate the rotation needed
            angle = angles[-n - 1]
            matrix = wireframe.get_rotate_matrix(dim1, dim2, angle)
            if dim3 is not None:
                angle = angles[n]
                matrix = wireframe.get_rotate_matrix(dim1, dim3, angle, matrix)
            # move, rotate, move back
            wireframe.transform(self.norm_matrix)
            wireframe.transform(matrix)
            wireframe.transform(self.denorm_matrix)
            # having rotated the wireframe, the lists of edges and faces may
            # no longer be in reverse z-order, so mark them for sorting
            self.sort_edges = True
            self.sort_faces = True
            self.display()
            if scale != 1.0:
                self.scale_all(scale)

    def scale_all(self, scale):
        """Scale all wireframes by a given scale, centered on the center of the wireframe."""

        count = 10 if self.data.show_steps else 1
        scale = math.pow(scale, (1 / count))
        wireframe = self.wireframe
        for _ in range(count):
            if self.stop:
                break
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
        """Set rotation values from data.angle which is in degrees."""
        # convert to radians
        self.rotation = float(self.data.angle) * np.pi / 180
        # take 2 steps per degree
        self.rotation_count = self.data.angle * 2

    def show(self):
        """Display the xy plane on the tkinter canvas."""
        rgb_image = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        self.image = ImageTk.PhotoImage(Image.fromarray(rgb_image))
        self.canvas.itemconfig(self.id_image, image=self.image)
        self.canvas.update()

    def show_text(self, text):
        if not self.id_rect:
            # construct background and text widgets
            self.id_rect = self.canvas.create_rectangle((0,0,0,0), fill="white")
            self.id_text = self.canvas.create_text(22, 16, anchor="nw", font="Arial 12", fill="black")
        # put the text into the canvas widget
        self.canvas.itemconfig(self.id_text, text=text)
        # get the bounding box for that text
        bbox = self.canvas.bbox(self.id_text)
        # expand it slightly so it looks less crowded
        adjust = (-12, -6, 12, 6)
        bbox2 = tuple(bbox[n] + adjust[n] for n in range(4))
        # set the rect (the text background) to that size
        self.canvas.coords(self.id_rect, bbox2)

    def show_window(self, widget):
        if not self.id_window:
            self.id_window = self.canvas.create_window(10, 10, anchor="nw", window=widget)
        else:
            self.canvas.itemconfigure (self.id_window, window=widget)

    def take_action(self, action: Action, playback=False):
        """Perform and display the supplied action."""
        acted = True
        showed = False
        self.stop = False
        cmd = action.cmd
        if cmd == Cmd.ROTATE:
            # The 3rd dimension is optional
            rotation = self.rotation if action.p4 == "+" else -self.rotation
            self.rotate_all(action.p1, action.p2, rotation, action.p3)
            showed = True
        elif cmd == Cmd.VISIBLE:
            # This is a visibility action like showing faces, etc.
            # It does not make any changes to the wireframe model, but we need
            # the wireframe to be drawn with the changed visibility setting.
            pass
        elif cmd == Cmd.ZOOM:
            if action.p1 == "+":
                self.scale_all(Viewer.SCALE)
            else:
                self.scale_all(1 / Viewer.SCALE)
            showed = True
        elif cmd == Cmd.MOVE:
            dim, amount = Viewer.direction_to_values[action.p1]
            self.translate_all(dim, amount)
            showed = True
        elif cmd == Cmd.DIMS:
            assert isinstance(action.p1, int)
            self.data.dims = action.p1
            self.init()
        elif cmd == Cmd.RESET:
            pubsub.publish("reset", action.p1)
            acted = False
        else:
            acted = False

        if acted:
            if not showed:
                self.display()
            # Save the action for possible playback
            # We /don't/ keep history when the history is being played back
            if not playback:
                self.actions.append(action)

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
            if self.stop:
                break
            wireframe.transform(matrix)
            wireframe.center[dim] += delta
            self.make_normalize_translations()
            self.display()

    def video_play(self, video_file):
        try:
            self.video_reader = cv2.VideoCapture(video_file)
            print(self.video_reader, self.video_reader.isOpened())
            if self.video_reader.isOpened():
                while not self.stop:
                    t1 = time.perf_counter()
                    ret, frame = self.video_reader.read()
                    if not ret:
                        break
                    self.img = frame
                    self.show()
                    self.wait_for_frame(t1)
        except:
            pass
        self.video_reader = None
        pubsub.publish("vplay", False)

    def video_record(self, state):
        """Start recording video. See note in .video_write about file creation."""
        if state:
            assert not self.video_writer
            assert not self.recording
            self.recording = True
        else:
            self.video_writer = None
            self.recording = False

    def video_start(self):
        """Create a video file to write to."""
        assert not self.video_writer
        types = (("mp4", "mp4v"), ("avi", "XVID"))
        ext, codec = types[0]
        assert not self.video_writer
        fname = utils.make_filename("video", ext)
        output = os.path.join(self.output_dir, fname)
        self.video_writer = cv2.VideoWriter(
            output,
            cv2.VideoWriter_fourcc(*codec),
            self.data.frame_rate,
            (self.width, self.height),
        )

    def video_write(self):
        """Write the current xy plane to a video file.

        Takes about 80ms.
        """
        if self.recording:
            # By deferring file creation until an actual write is issued,
            # we avoid creating an empty video file when the user starts
            # and then stops video recording.
            if not self.video_writer:
                self.video_start()
            self.video_writer.write(self.img)

    def wait_for_frame(self, t1):
        """Wait out the remaining duration (if any) of a video frame."""
        t2 = time.perf_counter()
        # print('frame took %0.3f ms' % ((t2-t1)*1000.0))
        frame_time = 1 / self.data.frame_rate
        pause = frame_time - t2 + t1
        if pause > 0.0:
            time.sleep(pause)
