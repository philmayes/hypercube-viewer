import datetime
import tkinter as tk

class ButtonPair:
    """Create a pair of buttons that act like radiobuttons."""

    states = (tk.NORMAL, tk.DISABLED)

    def __init__(self, frame, text: [], callback, row=0, col=0):
        self.buttons = []
        self.callback = callback
        self.active = 0
        for n in range(2):
            btn = tk.Button(frame, text=text[n], state=ButtonPair.states[n], command=self.passthrough)
            btn.grid(row=row, column=col, sticky=tk.E, padx=2, pady=2)
            col += 1
            self.buttons.append(btn)

    def passthrough(self):
        """Toggle which button is active and pass value to the user."""
        self.active ^= 1
        for n, btn in enumerate(self.buttons):
            btn["state"] = ButtonPair.states[n ^ self.active]
        self.callback(self.active)


def make_filename(prefix: str, ext: str):
    """Create a filename that includes date and time."""
    now = datetime.datetime.now()
    return f'{prefix}-{now:%y%m%d-%H%M%S}.{ext}'
