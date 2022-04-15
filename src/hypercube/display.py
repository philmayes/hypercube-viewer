#!/bin/env python
"""
There are four primitive actions:
    plot    calculate new positions of nodes etc.
    draw    project nodes onto a surface
    show    show the surface on a window
    write   write the surface to video

    display()   executes draw, show, write

"""

import copy
import math
import random
import re
import subprocess
import time

import cv2
import numpy as np
from PIL import Image
from PIL import ImageTk

import colors
import wireframe as wf

SIZE = 800
ROTATION = np.pi / 24
ROTATION_SCALE = 1.0#0.995  # amount to scale for each rotation step
SCALE = 1.25
TRANSLATE = 10
FRAME_RATE = 30
GHOST = 0.95            # 0 < GHOST < 1 leaves a ghost trail; 0 doesn't
##FRAME_RATE = 1
VIDEO_TMP = 'cv2.avi'
VIDEO_OUT = 'out.mp4'
##VIDEO = ''
COLOR_TEXT = (200, 200, 250)
HELP_TEXT = """\
Save to video: {self.save_to_video}
frame count:   {self.frame_count}
recording:     {self.recording}
"""
ESC = 27
PGUP = 0x210000
PGDN = 0x220000
END = 0x230000
HOME = 0x240000
LEFT = 0x250000
UP = 0x260000
RIGHT = 0x270000
DOWN = 0x280000
INS = 0x2d0000
DEL = 0x2e0000
F1 = 0x700000
F2 = 0x710000
F3 = 0x720000
F4 = 0x730000
F5 = 0x740000
F6 = 0x750000
F7 = 0x760000
F8 = 0x770000
F9 = 0x780000
F10 = 0x790000
F11 = 0x7a0000
F12 = 0x7b0000

key_to_function = {
    LEFT:       (lambda x: x.translate_all(0, -TRANSLATE)),
    RIGHT:      (lambda x: x.translate_all(0,  TRANSLATE)),
    DOWN:       (lambda x: x.translate_all(1,  TRANSLATE)),
    UP:         (lambda x: x.translate_all(1, -TRANSLATE)),
    ord('='):   (lambda x: x.scale_all(SCALE)),
    ord('-'):   (lambda x: x.scale_all(1 / SCALE)),
    # rotations are performed about the plane given by two dimensions where the
    # dimensions are X=0, Y=1, Z=2, etc.
    # There is no point in performing any rotations that do not include X or Y
    # as they will not be visible in the 2D projection
    ord('q'):   (lambda x: x.rotate_all(1, 2,  ROTATION)),
    ord('w'):   (lambda x: x.rotate_all(1, 2, -ROTATION)),
    ord('a'):   (lambda x: x.rotate_all(0, 2,  ROTATION)),
    ord('s'):   (lambda x: x.rotate_all(0, 2, -ROTATION)),
    ord('z'):   (lambda x: x.rotate_all(0, 1,  ROTATION)),
    ord('x'):   (lambda x: x.rotate_all(0, 1, -ROTATION)),

    ord('d'):   (lambda x: x.rotate_all(1, 3,  ROTATION)),
    ord('f'):   (lambda x: x.rotate_all(1, 3, -ROTATION)),
    ord('c'):   (lambda x: x.rotate_all(0, 3,  ROTATION)),
    ord('v'):   (lambda x: x.rotate_all(0, 3, -ROTATION)),

    ord('g'):   (lambda x: x.rotate_all(1, 4,  ROTATION)),
    ord('h'):   (lambda x: x.rotate_all(1, 4, -ROTATION)),
    ord('b'):   (lambda x: x.rotate_all(0, 4,  ROTATION)),
    ord('n'):   (lambda x: x.rotate_all(0, 4, -ROTATION)),

    ord('j'):   (lambda x: x.rotate_all(1, 5,  ROTATION)),
    ord('k'):   (lambda x: x.rotate_all(1, 5, -ROTATION)),
    ord('m'):   (lambda x: x.rotate_all(0, 5,  ROTATION)),
    ord(','):   (lambda x: x.rotate_all(0, 5, -ROTATION)),

    ord(' '):   (lambda x: x.repeat_frame(30)),

    ord('['):   (lambda x: x.record()),
    ord(']'):   (lambda x: x.play_back()),
    ord('\\'):  (lambda x: x.play_back(True)),

    F1:         (lambda x: x.xor_boolean('show_help')),
    F4:         (lambda x: x.init()),

    F5:         (lambda x: x.make_video1()),
    F6:         (lambda x: x.make_video2()),
    F7:         (lambda x: x.make_video3()),
    F8:         (lambda x: x.make_video4()),

    F9:         (lambda x: x.xor_boolean('plot_nodes')),
    F10:        (lambda x: x.xor_boolean('plot_edges')),
    F11:        (lambda x: x.xor_boolean('plot_center')),
    F12:        (lambda x: x.xor_boolean('save_to_video')),
    }

def parse_commands(commands):
    """Convert a string of commands into ordinals.
    fn or fnn is converted to the function key ordinal.
    """
    def func(f):
        return chr(int(f.group()[1:]))
    # first replace function key strings by ^A = F1 etc.
    subst = re.sub(r'f\d{1,2}', func, commands)
    def to_ordinal(c):
        number = ord(c)
        if number < 32:
            # convert control key to F-key equivalent
            number += 0x6F
            number <<= 16
        return number
    # convert control chars to Fn keys, others to their ordinal
    return [to_ordinal(c) for c in subst]
    
def time_function(func):
    """Decorator to time a function."""
    def wrapper(*args, **kwargs):
        t1 = time.process_time()
        res = func(*args, **kwargs)
        t2 = time.process_time()
        print('%s took %0.3f ms' % (func.__name__, (t2-t1)*1000.0))
        return res
    return wrapper

class Times(object):
    """class to record elapsed times and print out on request."""
    def __init__(self, desc=''):
        self.times = [time.process_time(),]

    def event(self, desc=''):
        """Record the time and description of an event."""
        self.times.append(desc)
        self.times.append(time.process_time())

    def print(self):
        """Print the duration and description of all events."""
        for n in range(1, len(self.times), 2):
            print('%.6f  %s'%(self.times[n+1]-self.times[n-1], self.times[n],))

class Viewer:
    """Display 3D objects on a screen."""

    def __init__(self, width, height, widget=None):
        self.width = width
        self.height = height
        self.widget = widget
        self.img = np.zeros((height, width, 3), np.uint8)

        # transform settings
        self.rotation = 0.0
        self.rotation_count = 1
        self.set_rotation(5)

        # visibility settings...
        self.plot_nodes = False
        self.plot_edges = True
        self.plot_center = False
        self.show_help = False
        self.save_to_video = False
        self.node_radius = 4
        self.center_radius = 1
        self.frame_time = 1 / FRAME_RATE
        self.frame_count = 0
        if VIDEO_TMP:
            self.video = cv2.VideoWriter(VIDEO_TMP,
                                         cv2.VideoWriter_fourcc(*'XVID'),
                                         FRAME_RATE,
                                         (width,height))
        else:
            self.video = None
        # self.init()

    def convert_video(self):
        """Convert the video format to .mp4.

        Because the opencv .avi file is not readable by PowerDirector.
        """

        if self.frame_count > 0:
            # usage: ffmpeg [options] [[infile options] -i infile]... {[outfile options] outfile}...
            # -i f    input files
            # -y        overwrite output files
            # -r 30     frame rate
            # -an       disable audio
            exe = r'E:\devtools\ffmpeg\bin\ffmpeg.exe'
            cmd = r'{0} -y -i {1} -y -r 30 -an {2}'.format(exe, VIDEO_TMP, VIDEO_OUT)
            retcode = subprocess.call(cmd)
            if retcode:
                print('ffmpeg failure:', retcode)

    def display(self):
        t1 = time.process_time()
        if self.recording:
            self.save_frame()
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

##    @time_function
    def draw(self):
        """Draw the wireframe onto the video surface."""

        if GHOST:
            # leave a shadow of the previous frame
            np.multiply(self.img, GHOST, out=self.img, casting='unsafe')
        else:
            # clear the previous frame
            cv2.rectangle(self.img, (0, 0), (self.width, self.height), colors.bg, -1)
        if self.show_help:
            self.draw_text(HELP_TEXT.format(self=self))

        wireframe = self.wireframe
        if self.plot_center:
            cv2.circle(self.img,
                       (wireframe.center[0], wireframe.center[1]),
                       self.center_radius,
                       colors.center,
                       -1)

        if self.plot_edges:
            for n1, n2, color in wireframe.edges:
                node1 = wireframe.nodes[n1]
                node2 = wireframe.nodes[n2]
                cv2.line(self.img,
                        (int(round(node1[0])), int(round(node1[1]))),
                        (int(round(node2[0])), int(round(node2[1]))),
                        color,
                        3)

        if self.plot_nodes:
            for node in wireframe.nodes:
                cv2.circle(self.img,
                           (int(round(node[0])), int(round(node[1]))),
                           self.node_radius,
                        colors.node,
                           -1)

    def draw_text(self, text, y=30):
        font = cv2.FONT_HERSHEY_SIMPLEX
        x = self.ndims
        lines = text.split('\n')
        for line in lines:
            cv2.putText(self.img, line, (x, y), font, 1, COLOR_TEXT, 2, cv2.LINE_AA)
            y += 30

    def help(self):
        self.show_help ^= False

    def init(self, ndims: int):
        self.ndims = ndims
        # calculate size and location
        sizey = SIZE
        sizex = SIZE * 16 // 9
        orgx = (self.width - sizex) // 2
        orgy = (self.height - sizey) // 2
        # construct a wireframe object
        self.wireframe = wf.Wireframe(ndims)
        self.wireframe.add_shape_sizes(orgx, orgy, [sizex, sizey])
        self.make_normalize_translations()
        # initialize recording settings
        self.frames = []
        self.recording = False
        self.playing_back = False
        # remove any previous drawing
        cv2.rectangle(self.img, (0, 0), (self.width, self.height), colors.bg, -1)
        # request redraw (for when called via keystroke)
        return True

    def make_normalize_translations(self):
        """Make 2 matrices for moving to (0,0,0,...) and back."""
        wireframe = self.wireframe        
        normalize = [-x for x in wireframe.center]
        self.norm_matrix = wireframe.get_translation_matrix(normalize)
        self.denorm_matrix = wireframe.get_translation_matrix(wireframe.center)

    def make_video1(self):
        dims = self.wireframe.dims
        step = np.pi/400
    ##        steps = [step] * 15
        steps = [step * n for n in range(1,5)]
        steps = [step * 4] * 5
        steps.extend(reversed(steps))
        self.display()
        for dim1, dim2, count in (
            (0, 1, 10),
            (0, 2, 10),
            (1, 2, 10),
            (1, 3, 10),
            (0, 3, 10),
            (1, 4, 10),
            (0, 4, 10),
            (1, 5, 10),
            (0, 5, 10),
            ):
            for rotation in steps[:count]:
                self.rotate_all(dim1, dim2, rotation)
                self.display()

    def make_video2(self):
        dims = self.wireframe.dims
        step = np.pi/400
##        steps = [step] * 15
        steps = [step * n for n in range(1,5)]
        steps = [step * 4] * 5
        steps.extend(reversed(steps))
        self.display()

        for maxdim in range(3, dims):
            for n in range(10):
                # choose two dimensions at random
                dim1 = random.randrange(2)
                dim2 = random.randrange(2, maxdim)

                # ignore it when both dimensions are the same
                if dim1 != dim2:
                    # normalize the dimensions
                    if dim1 > dim2:
                        dim1, dim2 = dim2, dim1
                    #
                    print(dim1, dim2)
                    for rotation in steps:
                        self.rotate_all(dim1, dim2, step)
                        self.display()
                        if dim1 != 0 and dim2 != 2:    # ie DRY
                            self.rotate_all(0, 2, step * 4)
                            self.display()

    def make_video3(self):
        dims = self.wireframe.dims
        step = np.pi/40
##        steps = [step] * 15
        steps = [step * n for n in range(1,5)]
        steps = [step * 4] * 5
        steps.extend(reversed(steps))
        self.display()

        # run 3D for a bit, then 4D,...
        for maxdim in range(3, dims + 1):
            for n in range(10):
                # choose two dimensions at random
                # The 1st dimension is always 0/1, aka X or Y, as rotations in
                # the other dimensions have no effect on the 2D projection
                dim1 = random.randrange(2)
                dim2 = random.randrange(2, maxdim)
                # skip when both dimensions are the same
                if dim1 != dim2:
                    # normalize the dimensions
                    if dim1 > dim2:
                        dim1, dim2 = dim2, dim1
                    print(dim1, dim2)
                    # rotate XZ and YZ regularly
                    rotate_dim1 = 1 if n & 8 else 0
##                    rotate_dim1 = 1
                    self.rotate_all(rotate_dim1, 2, step)
                    self.display()
                    if dim1 != 0 and dim2 != 2:    # ie DRY
                        self.rotate_all(dim1, dim2, step)
                        self.display()

    def make_video4(self):
        for key in parse_commands('[ xxxwwwssssjjbb[f12\\'):
            self.take_action(key)

    def play_back(self, reversed=False):
        if not self.playing_back:
            self.playing_back = True
            self.recording = False
            if reversed:
                start = len(self.frames) - 1
                stop = -1
                step = -1
            else:
                start = 0
                stop = len(self.frames)
                step = 1
            for index in range(start, stop, step):
                self.wireframe = self.frames[index]
                self.display()
            self.playing_back = False

    def record(self):
        assert not self.playing_back
        if self.recording:
            self.recording = False
        else:
            self.frames = []
            self.save_frame()
            self.recording = True

    def repeat_frame(self, count):
        """Wait for <count> frames."""
        for _ in range(count):
            self.display()

    def rotate_all(self, dim1, dim2, theta, dim3=-1):
        """Rotate all wireframes about their center, around one or two planes
            by a given angle."""
##        theta *= 5
##        print('rotate_all', dim1, dim2, theta, count)

        count = self.rotation_count
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

    def run(self):
        """Process commands until finished."""
        self.display()
        while 1:
            key = cv2.waitKeyEx(0)
            print('Key:', chr(key) if 32 < key < 128 else hex(key))
            if key == ESC or key < 0:
                break
            self.take_action(key)
        self.convert_video()
        cv2.destroyAllWindows()

    def save_frame(self):
        """Save wireframe without drawing or showing it."""
        self.frames.append(copy.copy(self.wireframe))

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

    def set_rotation(self, angle):
        self.rotation = float(angle) * np.pi / 180
        self.rotation_count = angle * 2

    def show(self):
        """Display image on screen."""
        if self.widget:
            image = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            image = ImageTk.PhotoImage(image)
            self.widget.configure(image=image)
            self.widget.image = image
            self.widget.update()
        else:
            cv2.imshow("Wireframe Display", self.img)

    def take_action(self, key):
        if isinstance(key, str) and len(key) == 4:
            cmd = key[0]
            if cmd == 'R':
                dim1 = int(key[1])
                dim2 = int(key[2])
                rotation = self.rotation if key[3] == '+' else -self.rotation
                self.rotate_all(dim1, dim2, rotation)
                self.draw()
                self.show()
                return True
            else:
                return
        if key in key_to_function:
            key_to_function[key](self)
            self.draw()
            self.show()
            return True

    def translate_all(self, dim, amount):
        """Translate all wireframes along a given axis by d units."""

        wireframe = self.wireframe
        vector = [0] * wireframe.dims
        vector[dim] = amount
        matrix = wireframe.get_translation_matrix(vector)
        wireframe.transform(matrix)
        wireframe.center[dim] += amount
        self.make_normalize_translations()
        self.display()

    def write(self):
        """Takes about 80ms."""
        if self.save_to_video:
            if self.video:
                self.video.write(self.img)
                self.frame_count += 1

    def xor_boolean(self, attrib, changes_screen=True):
        """Toggle the value of a boolean."""

        b = getattr(self, attrib) ^ True
        setattr(self, attrib, b)
        print('Changed', attrib, 'to', b)
        return changes_screen


if __name__ == '__main__':
##    print(parse_commands(' xxsjbf1f11g'))
    pv = Viewer(1920, 1080)
    pv.run()
