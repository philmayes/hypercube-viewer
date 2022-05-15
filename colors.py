# opencv colors are BGR

import random

random.seed(a=1)

face_colors = {}


def random_color():
    """Return a 3-tuple of integers in the ranges 0-255."""
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


def face(pair: list):
    """Given a face identified by its two dimensions, return its color.

    Colors are generated randomly (because I cannot think of an aesthetically
    pleasing algorithm) and cached in a dictionary.
    The random number generator is seeded at load time so the same colors are
    generated on different invocations.
    """
    assert len(pair) == 2
    # convert the pair of dimensions into a hashable type
    key = tuple(pair)
    if key not in face_colors:
        face_colors[key] = random_color()
    return face_colors[key]


def hex_to_rgb(s):
    """Convert a string of 6 hex values into an RGB 3-tuple."""
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def hex_to_bgr(s):
    """Convert a string of 6 hex values into a BGR 3-tuple."""
    return int(s[4:6], 16), int(s[2:4], 16), int(s[0:2], 16)


# These colors are in the opencv format of BGR
node = (255, 255, 255)
center = (255, 255, 255)
vp = (244, 208, 140)  # vanishing point: a shade of aqua
text = (200, 200, 250)
bg = (0, 0, 0)  # must be zeros so we can fade to black in .draw()
names = (
    ("ff0000", "red"),
    ("00ffff", "aqua"),
    ("ffff00", "yellow"),
    ("00ff00", "green"),
    ("ff00ff", "fuschia"),
    ("ff8000", "orange"),
    ("00a8ec", "blue"),
    ("800080", "purple"),
    ("e62b86", "pink"),
    ("f1a629", "lt.orange"),
    ("fff99d", "lemon yellow"),
    ("8dcb41", "lt. green"),
    ("bfb2d3", "lilac"),
    ("826b89", "purple"),
    ("c0c0c0", "silver"),
    ("000000", "white"),
)
ascii = [name[0] for name in names]
name = [name[1] for name in names]
html = ["#" + s for s in ascii]
bgr = [hex_to_bgr(c) for c in ascii]
