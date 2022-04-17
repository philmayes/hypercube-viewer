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
    re_aspects = re.compile(r'\d\d?(:\d\d?)*$')

    def __init__(self):
        self.dims = 4
        self.aspects = '1:1'
        self.ghost = 0.0
        self.angle = 15
        self.plot_nodes = False
        self.plot_edges = True
        self.plot_center = False

    def load(self, fname):
        try:
            with open(fname, "r") as read_file:
                data = json.load(read_file)
                for key, value in data.items():
                    # does this attribute already exist in this instance?
                    existing = getattr(self, key, Data.MISSING)
                    if existing is Data.MISSING:
                        # if it doesn't, it's an attribute we no longer use
                        # OR the json has been hacked, so ignore it
                        print('Bad json 1:', key, value)
                        continue
                    # if it does exist, check that the type is correct;
                    # if it doesn't, we've changed the type of the attribute
                    # OR the json has been hacked, so ignore it
                    if type(value) is not type(existing):
                        print('Bad json 2:', key, value)
                        continue
                    # perform additional validation(s) on the value
                    if key == 'aspects' and Data.re_aspects.match(value) is None:
                        print('Bad json 3:', key, value)
                        continue
                    # everything looks good; use the json value
                    setattr(self, key, value)
        except:
            pass

    def save(self, fname):
        data = self.__dict__
        with open(fname, "w") as write_file:
            json.dump(data, write_file)

