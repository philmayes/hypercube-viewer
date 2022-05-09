
class Action:
    """Class to hold an action request.

    The meanings of the parameters are:
    Action          cmd         p1          p2          p3          p4
    ---------------+-----------+-----------+-----------+-----------+-------------
    Playback        P
    Move            M           u,d,l,r
    Rotate          R           1st dim     2nd dim     [3rd dim]   direction
    Zoom            Z           +/-
    Set dimensions  D           n
    Visibility      V           data name   data value
    """

    def __init__(self, cmd, p1=None, p2=None, p3=None, p4=None):
        self.cmd = cmd
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4

    @property
    def visible(self):
        return self.cmd == 'V'

    def __str__(self):
        return f'{self.cmd}, {self.p1}'
