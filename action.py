from enum import Enum, auto

class Cmd(Enum):
    RESET = auto()
    PLAYBACK = auto()
    MOVE = auto()
    ROTATE = auto()
    ZOOM = auto()
    DIMS = auto()
    VISIBLE = auto()

class Action:
    """Class to hold an action request.

    The meanings of the parameters are:
    Action          cmd         p1          p2          p3          p4
    ---------------+-----------+-----------+-----------+-----------+-------------
    Reset           RESET       Reset flags
    Playback        PLAYBACK
    Move            MOVE        u,d,l,r
    Rotate          ROTATE      1st dim     2nd dim     [3rd dim]   direction
    Zoom            ZOOM        +/-
    Set dimensions  DIMS        n
    Visibility      VISIBLE     data name   data value
    """

    def __init__(self, cmd, p1=None, p2=None, p3=None, p4=None):
        self.cmd = cmd
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4

    @property
    def visible(self):
        return self.cmd == Cmd.VISIBLE

    def __str__(self):
        s = str(self.cmd)[4:]
        if self.p1 is not None:
            s += f": {self.p1}"
        if self.p2 is not None:
            s += f", {self.p2}"
        if self.p3 is not None:
            s += f", {self.p3}"
        if self.p4 is not None:
            s += f", {self.p4}"
        return s

class ActionQueue(list):
    """Class to hold a queue of Action items.
    
    The reason for this class is to merge successive SlideControl
    actions into a single change.
    """

    merging = True # merge successive slider values into a single action
    # A list of slider datanames that is constructed by App.make_controls()
    sliders = []

    def append(self, item):
        assert isinstance(item, Action)
        if ActionQueue.merging:
            if super().__len__():
                prev = super().__getitem__(-1)
                if prev.cmd == Cmd.VISIBLE and\
                item.cmd == Cmd.VISIBLE and\
                prev.p1 == item.p1 and\
                item.p1 in ActionQueue.sliders:
                    prev.p2 = item.p2
                    return
        super().append(item)
    
    def __str__(self):
        s = "Actions: "
        for n in range(super().__len__()):
            item = super().__getitem__(n)
            s += str(item)
            s += "; "
        return s
