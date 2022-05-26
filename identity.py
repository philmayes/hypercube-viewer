""" identity.py

https://semver.org/
"""
PRODUCT = "Hypercube Viewer"
MAJOR = 0
MINOR = 0
PATCH = 3

VERSION = "%d.%d" % (MAJOR, MINOR)
if PATCH:
    VERSION = "%s.%d" % (VERSION,PATCH)

IDENTITY = "%s %s" % (PRODUCT, VERSION)

