import datetime
import tkinter as tk

def make_filename(prefix: str, ext: str):
    """Create a filename that includes date and time."""
    now = datetime.datetime.now()
    return f'{prefix}-{now:%y%m%d-%H%M%S}.{ext}'

def nothing():
    pass

