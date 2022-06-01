import identity

hint_about = f"""\
{identity.PRODUCT}

Version {identity.VERSION}"""
hint_angle = """\
Set the amount by which
the movement controls
rotate the object."""
hint_aspect = """\
A cube has all sides of equal length,
but you can use different ratios,
e.g. 4:3:2 would set:
    the x-dimension to 4 units
    the y-dimension to 3 units
    the z-dimension to 2 units
Extra dimensions take the last-specified value,
e.g. the 4th dimension would also be 2 units."""
hint_auto_scale = """\
Resize the object by this amount during
each step of movement.
1.00 means no resizing.

WARNING:
The rotation is slower because of this.
Note that when intermediate steps are
shown, a fraction of the scaling takes
place for every step, making it much slower.
When there are a large number of dimensions,
the speed is even worse.
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
As the hypercube is moved, the program can leave
a ghost image that fades out. The amount of ghost
image left behind as the object is rotated is:
0   = no ghosting;
10 = no fading out."""
hint_list = "Show a list of all the actions so far"
hint_move = "Move the object up, down, left or right."
hint_opacity = """\
Change the opacity of the faces.
1.0 is completely opaque.

WARNING:
This is a very slow operation.
To see it at the correct speed,
record the movements to video."""
hint_play = "Play back the last recorded video file"
hint_random = "Rotate the object randomly\naround 3 dimensions"
hint_record = "Record all movement to a video file"
hint_replay = "Play back all the movement\nthat you have done so far."
hint_replay_visible = """\
Choose whether replay includes all changes
to visibility settings that were made.
When it is unchecked, replay takes place
using the current visibility settings.."""
hint_restart = "Forget all movement\nthat you have done\nand start again"
hint_rotate = "Rotate the object around the given plane"
hint_show_center = "Show the center point of the object"
hint_show_edges = "Show the edges of the object"
hint_show_faces = "Show the faces of the object"
hint_show_hints = """\
Show a hint like this
when moving the mouse
over a control"""
hint_show_nodes = "Show the corners of the object"
hint_show_perspective = "Show the object in perspective view"
hint_show_steps = """\
Draw the intermediate steps of moves and rotations.
Note that this may slow the operation, especially
when the hypercube has a large number of dimensions."""
hint_show_vp = "Show the vanishing point of the perspective view"
hint_stop = "Stop the Replay"
hint_viewsize = """\
The size in pixels of the hypercube display.
The width and height need not be the same."""
hint_zoom_m = "Shrink the size of the object"
hint_zoom_p = "Expand the size of the object"

lookup = {
    "about": hint_about,
    "angle": hint_angle,
    "aspect": hint_aspect,
    "auto_scale": hint_auto_scale,
    "depth": hint_depth,
    "dims": hint_dims,
    "folder": hint_folder,
    "frame_rate": hint_frame_rate,
    "ghost": hint_ghost,
    "list": hint_list,
    "move": hint_move,
    "opacity": hint_opacity,
    "play": hint_play,
    "random": hint_random,
    "record": hint_record,
    "replay": hint_replay,
    "replay_visible": hint_replay_visible,
    "restart": hint_restart,
    "rotate": hint_rotate,
    "show_center": hint_show_center,
    "show_edges": hint_show_edges,
    "show_faces": hint_show_faces,
    "show_hints": hint_show_hints,
    "show_nodes": hint_show_nodes,
    "show_perspective": hint_show_perspective,
    "show_steps": hint_show_steps,
    "show_vp": hint_show_vp,
    "stop": hint_stop,
    "viewsize": hint_viewsize,
    "zoom_m": hint_zoom_m,
    "zoom_p": hint_zoom_p,
}


class Hints:
    def __init__(self, viewer):
        self.viewer = viewer
        self.active = True
        self.showing = None
        self.static = False

    def visible(self, active: bool):
        """Set whether hints are to show or not."""
        self.active = active

    def show(self, hint_id):
        """Show a hint.

        State table:                        hint
        old state   new state   old==new    exists  action
            none        none        y         -       -
            none        hint        n         y     show
            none        hint        n         n       -
            hint        none        n         -     clear
            static      none        n         -       -
            hint        hint        y         -       -
            hint        hint        n         y     show
            hint        hint        n         n     clear
        Notes:
            * The hint should always exist. The "hint exists"
              column is just a precaution.
            * The table does not cover static hints, though the code does.
              See the docstring for show_static for details.
        """
        if self.active:
            if hint_id is None:
                if self.showing is not None and not self.static:
                    self.viewer.clear_text()
                    self.showing = None
            elif hint_id != self.showing:
                if hint_id in lookup:
                    text = lookup[hint_id]
                    self.viewer.show_text(text)
                    self.showing = hint_id
                    self.static = False
                else:
                    self.viewer.clear_text()
                    self.showing = None

    def show_static(self, hint_id):
        """Show a static hint.

        For example, about. This hint:
            * is shown regardless of the active state
            * is not canceled by show(None), aka ordinary mouse movement
            * is removed by a left-click on the canvas
        """
        old_active = self.active
        # Temporarily force active so that the hint will be shown.
        self.active = True
        self.show(hint_id)
        # Set the static flag AFTER calling show() because that call clears it
        self.static = True
        self.active = old_active

    def stop_static(self):
        """Cancel a static hint."""
        self.static = False
        self.viewer.clear_text()
        self.showing = None
