import datetime
import os
import sys
import time
import tkinter as tk


def find_latest_file(path):
    latest = None
    tm = 0.0
    for fname in os.listdir(path):
        full = os.path.join(path, fname)
        stat_info = os.stat(full)
        if tm < stat_info.st_mtime:
            tm = stat_info.st_mtime
            latest = full
    return latest


def get_location(rel_dir, fname):
    """Get the location of the data file."""
    location = make_dir(rel_dir)
    return os.path.join(location, fname)


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
    return f"{prefix}-{now:%y%m%d-%H%M%S}.{ext}"

def time_function(func):
    """Decorator to time a function."""
    def wrapper(*args, **kwargs):
        t1 = time.perf_counter()
        res = func(*args, **kwargs)
        t2 = time.perf_counter()
        print('%s took %0.3f ms' % (func.__name__, (t2-t1)*1000.0))
        return res
    return wrapper

