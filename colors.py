# opencv colors are BGR

from dims import MAX

face_colors = {}


def face(pair: list):
    """Given a face identified by its two dimensions, return its color.

    Colors are generated by blending the colors of the two sides and cached
    in a dictionary.
    """
    dim1, dim2 = pair
    # Avoid [0, 1] and [1, 0] generating two cached entries
    if dim1 > dim2:
        dim1, dim2 = dim2, dim1
    # Convert the pair of dimensions into a hashable type
    key = dim1 * MAX + dim2
    if key not in face_colors:
        face_colors[key] = [sum(x) // 2 for x in zip(bgr[dim1], bgr[dim2])]
    return face_colors[key]


def bgr_to_html(b, g, r):
    return f"#{r:02x}{g:02x}{b:02x}"


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
html_bg = bgr_to_html(*bg)
dim4gray = (128,128,128)
html_dim4gray = bgr_to_html(*dim4gray)
names = (
    ("ff0000", "red"),
    ("ffffff", "white"),
    ("00a8ec", "blue"),
    ("00ff00", "green"),
    ("00ffff", "aqua"),
    ("ffff00", "yellow"),
    ("ff00ff", "fuschia"),
    ("ff8000", "orange"),
    ("800080", "purple"),
    ("e62b86", "pink"),
    ("f1a629", "lt.orange"),
    ("fff99d", "lemon yellow"),
    ("8dcb41", "lt. green"),
    ("bfb2d3", "lilac"),
    ("826b89", "purple"),
    ("c0c0c0", "silver"),
)
assert len(names) >= MAX    # Yes, there can be more colors than necessary
ascii = [name[0] for name in names]
name = [name[1] for name in names]
html = ["#" + s for s in ascii]
bgr = [hex_to_bgr(c) for c in ascii]
