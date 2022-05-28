from enum import Enum, auto
import re

import tkinter as tk
from tkhtmlview import HTMLScrolledText

re_strip = re.compile(r"<.*?>")

class Name(Enum):
    NONE = 0
    ACTIONS = auto()
    HELP = auto()
    KEYS = auto()

class HtmlViewer():
    def __init__(self, viewer):
        self.viewer = viewer
        self.name = Name.NONE

    def clear(self):
        if self.name is not Name.NONE:
            self.name = Name.NONE
            self.viewer.clear_window()
            return True

    def clear_if_showing(self, name: Name):
        if name == self.name:
            self.clear()
            return True
        return False

    def copy(self):
        text = re_strip.sub("", self.html, 9999)
        w = self.window
        w.clipboard_clear()
        w.clipboard_append(text)
        w.update() # keep it on the clipboard after the window is closed


    def show(self, htm, name: Name):
        self.name = name
        frame = tk.Frame()
        window = HTMLScrolledText(frame, html=htm, padx=10)
        window.grid(row=0, column=0, padx=4, pady=4, sticky=tk.NW)
        vx, vy = self.viewer.data.get_viewer_size()
        # From measurement, the width and height settings for HTMLScrolledtext
        # (which is derived from tk.Text) are 16 and 8 pixels, so here we turn
        # the viewer size into character counts, allowing for the scroolbar
        # and button row.
        vx -= 64
        vy -= 80
        vx //= 8
        vy //= 16
        # Make it at least 30 high and nor more than 100 wide
        vx = min(100, vx)
        vy = max(30, vy)
        window.config(width=vx, height=vy)

        # add buttons at the bottom of the window
        frame2 = tk.Frame(frame)
        frame2.grid(row=1, sticky=tk.E, padx=2)
        ctl = tk.Button(frame2, width=10, text="Copy", command=self.copy)
        ctl.grid(row=0, column=0, sticky=tk.E, padx=0, pady=4)
        ctl = tk.Button(frame2, width=10, text="Close", command=self.clear)
        ctl.grid(row=0, column=1, sticky=tk.E, padx=10, pady=4)
        self.viewer.show_window(frame)

        # save values for possible copy operation
        self.html = htm
        self.window = window

