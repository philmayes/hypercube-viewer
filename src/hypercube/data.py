import json
import os
import re
import sys

def get_location():
    """Get the location of the data file."""
    rel_dir = os.path.dirname(sys.argv[0])
    abs_dir = os.path.abspath(rel_dir)
    json_file = os.path.join(abs_dir, '../../settings/values.json')
    return os.path.normpath(json_file)

class Data:
    """A class to hold persistent data.

    If new values are needed, just add them as class attributes.
    """

    MISSING = 'attribute is missing'
    re_aspects = re.compile(r'\d\d?(:\d\d?)+$')

    def __init__(self):
        """Factory settings."""
        # settings for how the wireframe is constructed
        self.dims = 4
        self.aspects = '1:1'

        # settings for how the wireframe is displayed
        self.show_faces = False
        self.show_edges = True
        self.show_nodes = False
        self.show_coords = False
        self.show_center = False
        self.show_perspective = False

        # settings for how the wireframe is rotated
        self.ghost = 0.0
        self.angle = 15

    def validate_aspects(self, aspects):
        """Test whether supplied string is valid for self.aspects."""
        return bool(Data.re_aspects.match(aspects))

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
                    # perform additional validation(s) on the value
                    if key == 'aspects' and not self.validate_aspects(value):
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

