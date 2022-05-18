hint_show_faces = "Show the faces of the object"
hint_show_edges = "Show the edges of the object"
hint_show_nodes = "Show the corners of the object"
hint_show_coords = """\
Show the coordinates of each corner.
In most circumstances, these will overlap
until the object is rotated appropriately."""
hint_show_steps = "Show intermediate steps during rotation"
hint_show_center = "Show the center point of the object"
hint_show_perspective = "Show the object in perspective view"
hint_show_vp = "Show the vanishing point of the perspective view"
hint_depth = """\
Change the amount of perspective that is shown.
A larger number is less perspective. Put differently,
the vanishing point is moved further away."""
hint_ghost = """\
Leave a ghost image as the object is rotated.
0   = is no ghosting;
10 = no fading out."""
hint_angle = """\
Sets the amount the movement controls
rotate the object."""
hint_auto_scale = """\
SlideControl 'Resizing during rotation:' 0 90 1 10 0 02)
BIG WARNING HERE"""
hint_replay_visible = """\
Oh, this is hard to explain.
Replay uses original\nvisibility settings."""
hint_frame_rate = "Choose the frame rate of the video file."
hint_playback = "this is the help for hint_playback"
hint_move = "This control moves the object up, down, left or right."
hint_rotate = "This button rotates the object in a certain plane."
hint_zoom = "this is the help for hint_zoom"
hint_dimensions = "this is the help for hint_dimensions"

lookup = {
    "show_faces": hint_show_faces,
    "show_edges": hint_show_edges,
    "show_nodes": hint_show_nodes,
    "show_coords": hint_show_coords,
    "show_steps": hint_show_steps,
    "show_center": hint_show_center,
    "show_perspective": hint_show_perspective,
    "show_vp": hint_show_vp,
    "depth": hint_depth,
    "ghost": hint_ghost,
    "angle": hint_angle,
    "auto_scale": hint_auto_scale,
    "replay_visible": hint_replay_visible,
    "frame_rate": hint_frame_rate,
    "P": hint_playback,
    "M": hint_move,
    "R": hint_rotate,
    "Z": hint_zoom,
    "D": hint_dimensions,
    "Restart": "the restart button",
    "Replay": "the replay button",
    "Stop": "the stop button",
    "Dims": "the # dims",
}
# cache the amount of time the hint is shown.
# Longer descriptions are given more time.
durations = {}
MS_PER_WORD = 250  # reading rate


class Hints:
    def __init__(self, viewer):
        self.viewer = viewer
        self.active = True
        self.showing = None

    def visible(self, active: int):
        """Set whether hints are to show or not."""
        self.active = active

    def show(self, hint_id):
        """Show a hint.
                                            hint
        old state   new state   old==new    exists  action
            none        none        y         -       -
            none        hint        n         y     show
            none        hint        n         n       -
            hint        none        n         -     clear
            hint        hint        y         -       -
            hint        hint        n         y     show
            hint        hint        n         n     clear
        """
        if self.active:
            if hint_id is None:
                if self.showing is not None:
                    self.viewer.clear_text()
                    self.showing = hint_id
            elif hint_id != self.showing:
                if hint_id in lookup:
                    text = lookup[hint_id]
                    self.viewer.show_text(text)
                    self.showing = hint_id
                else:
                    self.viewer.clear_text()
                    self.showing = None
