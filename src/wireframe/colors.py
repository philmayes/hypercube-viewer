def hex_to_rgb(s):
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)

def hex_to_bgr(s):
    return int(s[4:6], 16), int(s[2:4], 16), int(s[0:2], 16)

node_color = (255,255,255)
center_color = (255,255,255)
ascii = (
    'ff0000',     # red
    'ff8000',     # orange
    'ffff00',     # yellow
    '00ff00',     # green
    '00a8ec',     # blue
    'ff00ff',     # fuschia
    '800080',     # purple
    'e62b86',     # pink
    'f1a629',     # lt.orange
    'fff99d',     # lemon yellow
    '8dcb41',     # lt. green
    '00ffff',     # aqua
    'bfb2d3',     # lilac
    '826b89',     # purple
    'c0c0c0',     # silver
    '000000',     # white
    )
html = ['#' + s for s in ascii]
bgr = [hex_to_bgr(c) for c in ascii]
