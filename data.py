import json
import os
import re


class Data:
    """A class to hold persistent data.

    If new values are needed, just add them as class attributes.
    """

    MISSING = "attribute is missing"
    MIN_SIZE = 100
    MAX_SIZE = 4096
    re_aspects = re.compile(r"\d\d?(:\d\d?)+$")
    re_view = re.compile(r"\s*(\d+)\s*[xX:]\s*(\d+)\s*$")

    def __init__(self):
        """Factory settings."""
        # settings for how the wireframe is constructed
        self.dims = 4
        self.aspects = "1:1"
        self.viewer_size = "1000x1000"

        # settings for how the wireframe is displayed
        self.show_faces = False
        self.show_edges = True
        self.show_nodes = False
        self.show_steps = True
        self.show_center = False
        self.show_perspective = False
        self.show_vp = False
        self.depth = 2.0
        self.ghost = 0
        self.opacity = 1.0
        # these values are set in in preferences, not the main window.
        self.node_radius = 4
        self.center_radius = 1
        self.vp_radius = 2
        self.edge_width = 3
        self.font_size = 0.4
        self.show_coords = False
        self.show_node_ids = False
        self.show_4_narrow = False  # True: Line width is 1
        self.show_4_gray = False    # True: Line color is gray

        # settings for how the wireframe is rotated
        self.angle = 15
        self.auto_scale = 1.0

        # settings for recording
        self.frame_rate = 30

        # settings for playback
        self.replay_visible = True

        # window position
        self.win_x = 100
        self.win_y = 100

        # miscellaneous
        self.show_hints = True

    def get_viewer_size(self):
        """Test whether supplied string is valid for self.viewer_size."""
        match = Data.re_view.match(self.viewer_size)
        assert match is not None
        return int(match.group(1)), int(match.group(2))

    def validate_aspects(self, aspects):
        """Test whether supplied string is valid for self.aspects."""
        return bool(Data.re_aspects.match(aspects))

    def validate_viewer_size(self, viewer_size):
        """Test whether supplied string is valid for self.viewer_size."""
        match = Data.re_view.match(viewer_size)
        if match:
            x = int(match.group(1))
            y = int(match.group(2))
            if (
                Data.MIN_SIZE <= x <= Data.MAX_SIZE
            and Data.MIN_SIZE <= y <= Data.MAX_SIZE
            ):
                return x, y

    def xor(self, dataname):
        """Xor the value of a boolean attribute."""
        old = getattr(self, dataname)
        assert isinstance(old, bool)
        setattr(self, dataname, not old)

    def load(self, fname):
        """Load and validate settings from a json file."""
        try:
            with open(fname, "r") as read_file:
                data = json.load(read_file)
                for key, value in data.items():
                    # does this attribute already exist in this instance?
                    existing = getattr(self, key, Data.MISSING)
                    if existing is Data.MISSING:
                        # if it doesn't, it's an attribute we no longer use
                        # OR the json has been hacked, so ignore it
                        print("Bad json: data not recognized:", key, value)
                        continue
                    # if it does exist, check that the type is correct;
                    # if it doesn't, we've changed the type of the attribute
                    # OR the json has been hacked, so ignore it
                    if type(value) is not type(existing):
                        print("Bad json: type is wrong:", key, value)
                        continue
                    # perform additional validation on certain values
                    if key == "aspects" and not self.validate_aspects(value):
                        print("Bad json: format is wrong:", key, value)
                        continue
                    if key == "viewer_size" and not self.validate_viewer_size(value):
                        print("Bad json: format is wrong:", key, value)
                        continue
                    # everything looks good; use the json value
                    setattr(self, key, value)
        except:
            pass

    def save(self, fname):
        """Save settings to a json file."""
        data = self.__dict__
        with open(fname, "w") as write_file:
            json.dump(data, write_file)

    def coerce(self, value, data_name):
        """Coerce the value from a widget into the data type."""

        data_type = type(getattr(self, data_name))
        if isinstance(value, str):
            if value.isdigit():
                value = int(value)
            elif value == "True":
                value = True
            elif value == "False":
                value = False
            else:
                try:
                    value = float(value)
                except:
                    pass

        value = data_type(value)
        assert type(value) is data_type
        return value
