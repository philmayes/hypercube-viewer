hint_angle = """\
Set the amount by which
the movement controls
rotate the object."""
hint_aspect = """\
A cube has all sides of equal length,
but you can use different ratios,
e.g. 4:3:2 would set the x-dimension
to 4 units, the y-dimension to 3 units
and the z-dimention to 2 units.
Additional dimensions take the last-
specified value, e.g. the 4th dimension
would also be 2 units."""
hint_auto_scale = """\
Resize the object by this amount
during each step of movement.
1.00 means no resizing.

WARNING: Resizing is a slow operation.
To see it at the correct speed,
record the movements to video."""
hint_depth = """\
Change the amount of perspective that is shown.
A larger number is less perspective. Put differently,
the vanishing point is moved further away."""
hint_dims = "Choose how many dimensions for the hypercube"
hint_folder = "Open the folder where videos are saved"
hint_frame_rate = "Choose the frame rate of the video file."
hint_ghost = """\
Amount of ghost image left behnd
as the object is rotated.
0   = no ghosting;
10 = no fading out."""
hint_move = "Move the object up, down, left or right."
hint_play = "Play back what was previously\nrecorded to video"
hint_random = "Rotate the object randomly\naround 3 dimensions"
hint_record = "Record all movement to a video file"
hint_replay = "Play back all the movement\nthat you have done so far."
hint_replay_visible = """\
Oh, this is hard to explain.
Replay uses original\nvisibility settings."""
hint_restart = "Forget all movement\nthat you have done\nand start again"
hint_rotate = "Rotate the object around the given plane"
hint_show_center = "Show the center point of the object"
hint_show_coords = """\
Show the coordinates of each corner.
In most circumstances, these will overlap
until the object is rotated appropriately."""
hint_show_edges = "Show the edges of the object"
hint_show_faces = "Show the faces of the object"
hint_show_nodes = "Show the corners of the object"
hint_show_perspective = "Show the object in perspective view"
hint_show_steps = "Show intermediate steps during rotation"
hint_show_vp = "Show the vanishing point of the perspective view"
hint_stop = "Stop the Replay"
hint_viewsize = """\
The size in pixels of the hypercube display.
The width and height need not be the same."""
hint_zoom_m = "Shrink the size of the object"
hint_zoom_p = "Expand the size of the object"

lookup = {
    "angle": hint_angle,
    "aspect": hint_aspect,
    "auto_scale": hint_auto_scale,
    "depth": hint_depth,
    "dims": hint_dims,
    "folder": hint_folder,
    "frame_rate": hint_frame_rate,
    "ghost": hint_ghost,
    "move": hint_move,
    "play": hint_play,
    "random": hint_random,
    "record": hint_record,
    "replay": hint_replay,
    "replay_visible": hint_replay_visible,
    "restart": hint_restart,
    "rotate": hint_rotate,
    "show_center": hint_show_center,
    "show_coords": hint_show_coords,
    "show_edges": hint_show_edges,
    "show_faces": hint_show_faces,
    "show_nodes": hint_show_nodes,
    "show_perspective": hint_show_perspective,
    "show_steps": hint_show_steps,
    "show_vp": hint_show_vp,
    "stop": hint_stop,
    "viewsize": hint_viewsize,
    "zoom_m": hint_zoom_m,
    "zoom_p": hint_zoom_p,
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
