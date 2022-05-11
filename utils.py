import datetime
import os
import sys
import tkinter as tk

def make_dir(rel_dir):
    """Get the location of the data file."""
    base_dir = os.path.dirname(sys.argv[0])
    location = os.path.join(base_dir, rel_dir)
    if not os.path.exists(location):
        os.mkdir(location)
    return location


def make_filename(prefix: str, ext: str):
    """Create a filename that includes date and time."""
    now = datetime.datetime.now()
    return f'{prefix}-{now:%y%m%d-%H%M%S}.{ext}'

