import json
import os
import re
import sys

def get_location():
    """Get the location of the data file."""
    rel_dir = os.path.dirname(sys.argv[0])
    return os.path.join(rel_dir, r'settings\values.json')

class Data:
    """A class to hold persistent data.

    If new values are needed, just add them as class attributes.
    """

    MISSING = 'attribute is missing'
    MIN_SIZE = 100
    MAX_SIZE = 4096
    re_aspects = re.compile(r'\d\d?(:\d\d?)+$')
    re_view = re.compile(r'\s*(\d+)\s*[xX:]\s*(\d+)\s*$')

    def __init__(self):
        """Factory settings."""
        # settings for how the wireframe is constructed
        self.dims = 4
        self.aspects = '1:1'
        self.viewer_size = '800x600'

        # settings for how the wireframe is displayed
        self.show_faces = False
        self.show_edges = True
        self.show_nodes = False
        self.show_coords = False
        self.show_steps = True
        self.show_center = False
        self.show_perspective = False
        self.show_vp = False
        self.depth = 2.0
        self.ghost = 0

        # settings for how the wireframe is rotated
        self.angle = 15
        self.auto_scale = 1.0

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
            if  Data.MIN_SIZE <= x <= Data.MAX_SIZE\
            and Data.MIN_SIZE <= y <= Data.MAX_SIZE:
                return x, y

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
                        print('Bad json: data not recognized:', key, value)
                        continue
                    # if it does exist, check that the type is correct;
                    # if it doesn't, we've changed the type of the attribute
                    # OR the json has been hacked, so ignore it
                    if type(value) is not type(existing):
                        print('Bad json: type is wrong:', key, value)
                        continue
                    # perform additional validation on certain values
                    if key == 'aspects' and not self.validate_aspects(value):
                        print('Bad json: format is wrong:', key, value)
                        continue
                    if key == 'viewer_size' and not self.validate_viewer_size(value):
                        print('Bad json: format is wrong:', key, value)
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

