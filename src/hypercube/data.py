import json

class Data:
    """A class to hold persistent data.
    If new values are needed, just add them as class attributes.
    """
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
                setattr(self, key, value)
        except:
            pass

    def save(self, fname):
        data = self.__dict__
        print(data)
        with open(fname, "w") as write_file:
            json.dump(data, write_file)

