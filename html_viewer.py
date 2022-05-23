from enum import Enum, auto

import tkinter as tk
from tkhtmlview import HTMLScrolledText

class Name(Enum):
    NONE = 0
    HELP = auto()
    ACTIONS = auto()

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
        ctl = tk.Button(frame, text="Close", command=self.clear)
        ctl.grid(row=1, column=0, sticky=tk.E, padx=10, pady=4)
        self.viewer.show_window(frame)

