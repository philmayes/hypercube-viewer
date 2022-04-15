# opencv colors are BGR

def hex_to_rgb(s):
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)

def hex_to_bgr(s):
    return int(s[4:6], 16), int(s[2:4], 16), int(s[0:2], 16)

node = (255,255,255)
center = (255,255,255)
bg = (0, 0, 0)      # must be zeros so we can fade to black in .draw()
ascii = (
    'ff0000',       # red
    '00ffff',       # aqua
    '00ff00',       # green
    'ffff00',       # yellow
    'ff8000',       # orange
    '00a8ec',       # blue
    'ff00ff',       # fuschia
    '800080',       # purple
    'e62b86',       # pink
    'f1a629',       # lt.orange
    'fff99d',       # lemon yellow
    '8dcb41',       # lt. green
    'bfb2d3',       # lilac
    '826b89',       # purple
    'c0c0c0',       # silver
    '000000',       # white
    )
html = ['#' + s for s in ascii]
bgr = [hex_to_bgr(c) for c in ascii]
