import identity

help = f"""
<h3>{identity.PRODUCT}</h3>

{identity.PRODUCT} is a program that draws a hypercube of 3 to 10 dimensions.

<h3>What is a hypercube?</h3>

<p>Start with a point. It has no dimensions. Now move that point along a dimension. 
In doing so, you create a second point and also create a line (a one-dimensional 
object.) Now move that line along a dimension at right-angles (aka orthogonal) 
to the first dimension. You double the number of points and lines, and also 
create two new lines from the movement of the points. Voila! A square. Now 
repeat the process by moving the square along a new dimension orthogonal to 
the existing two dimensions, and you have created a cube. Note that it has 
6 faces; one by moving the square in the new (third) dimension, and 4 from 
moving the 4 lines of the square along the new dimension.
</p>
<p>Now move that cube along an orthogonal fourth dimension. You now have 8 cubes; 
the original; one from the original being moved; and 6 from the 6 faces of the 
original cube being extended. This object is called a tesseract.
</p>
<p>We can continue this process without end. A 5-cube has 32 points, etc. 
Each value in this table comes from doubling the value above and adding 
the value above and in the previous column.</p>

<code>| # Dims | Points | Edges | Faces | Cubes |
|--------|--------|-------|-------|-------|
|      0 |      1 |       |       |       |
|      1 |      2 |     1 |       |       |
|      2 |      4 |     4 |     1 |       |
|      3 |      8 |    12 |     6 |     1 |
|      4 |     16 |    32 |    24 |     8 |
|      5 |     32 |    80 |    80 |    50 |
</code>

<h3>Drawing the hypercube</h3>

<p>The points, edges and/or faces are projected onto a plane surface 
(the x-y plane) in either a perspective or orthographic view.
 The origin is at the top left with the x-axis horizontal, the y-axis
 pointing down, and the Z-axis projecting into the screen.
 <br>
<b>NOTE:</b> Some of the drawing calculations take a long time. Factors that exacerbate this are:
<ul>
<li>A large number of dimensions</li>
<li>Drawing the faces</li>
<li>Showing intermediate steps</li>
<li>Showing ghosting</li>
<li>Resizing during rotation</li>
<li>Showing partially transparent faces</li>
</ul>
These delays do NOT occur in the video recording.
</p>

<h3>How is the hypercube rotated?</h3>

<p>In the real world, we think of rotation as about an axis. A square on your
screen being rotated clockwise is though of as rotating around the z-axis that
projects perpendicularly from the screen, but what is actually changing are
the x- and y-coordinates of the 4 corners. Similarly, rotation around the
x-axis is done by rotating the y-z plane. 
</p>
<p>The concept of rotating about an axis works in 3 dimensions because, for
any axis, there is only one plane that that is perpendicular to that axis.
For higher dimension, each dimension is perpendicular to more than one plane,
so naming the dimension would be ambiguous and XXXX. For a higher dimension D, 
the only rotations visible on the screen (the x-y surface) are rotations in
the x-D plane and the y-D plane. Hypercube-viewer allows the user to rotate
in both directions around these higher planes.
</p>
<p>For random rotations, Hypercube Viewer rotates about two randomly-chosen planes at once.
</p>

<h3>Available controls</h3>

<h5>SETUP</h5>
<ul>
<li><b>Number of dimensions:</b> Choose from 3 to 10.
</li>
<li><b>Aspect ratios:</b> It need not be a cube. Here, you can set the ratios 
of the edges for each dimension, for instance: 16:9:4 specifies a cuboid with 
width of 16, height of 9 and depth of 4. Additional dimensions take the value 
of the rightmost one specified.
</li>
<li><b>Viewing size:</b> The size in pixels of the plane surface on which the 
Hypercube is projected.
</li>
</ul>

<h5>VISIBILITY</h5>
<ul>
<li><b>Show faces, edges, corners:</b> Control what is drawn.
</li>
<li><b>Show intermediate steps:</b> Draw the intermediate steps of moves and 
rotations. Note that this may slow the operation, especially when the hypercube has 
a large number of dimensions.
</li>
<li><b>Show center:</b> Show the centerpoint of the hypercube.
</li>
<li><b>Perspective view:</b> Choose whether the hypercube is projected as a 
perspective or orthographic view.
</li>
<li><b>Show vanishing point:</b> When perspective view is selected, show the 
vanishing point.
</li>
<li><b>Depth of perspective:</b> Controls the amount of perspective. The 
vanishing point is placed at this value times the screen width.
</li>
<li><b>Amount of ghosting:</b> As the hypercube moves, the program can 
leave a ghost image that fades out. 0 indicates no ghosting, and with 10, 
no fading takes place.
</li>
<li><b>Rotation per click:</b> The rotation in degrees per click.
</li>
<li><b>Resizing during rotation:</b> The program can resize the object during rotation. 
This gives the amount by which the object is scaled. The rotation is slower because of 
this. Note that when intermediate steps are shown, a fraction of the scaling takes place 
for every step, making it <i>much slower</i>. When there are a large number of dimensions, 
the speed is even worse. This speed slowdown does not show in recorded videos.
</li>
<li><b>Opacity:</b> The opacity of the faces. Note that when the faces are
translucent, drawing times are <i>much slower</i>.
</li>

</ul>

<p>In preferences, you can also control:</p>
<ul>
<li><b>Corner radius</b></li>
<li><b>Center radius</b></li>
<li><b>Vanishing point radius</b></li>
<li><b>Line width</b></li>
<li><b>Font size:</b> The font size for coordinates and corner numbers</li>
<li><b>Show coordinates:</b> Show the coordinates of every point. The points 
may overlap for, say, a cube in orthogonal view. Avoid this by using perspective 
view and/or rotating the object so that every point is at a different place on screen.
</li>
<li><b>Show corner numbers:</b> The internal index number of all corners.</li>
<li><b>Set line width to 1:</b> For dimensions of 4 or more, set the line width to 1.</li>
<li><b>Set line color to gray:</b> For dimensions of 4 or more, set the line color to gray.</li>

<h5>MOVEMENT</h5>
<ul>
<li>The object can be rotated around various planes, moved, zoomed and shrunk.
</li>
<li><b>Replay:</b> This button will replay all the movement and visibility actions 
from the beginning.
</li>
<li><b>Stop:</b> This button will stop replay and also long movement operations.
</li>
<li><b>Begin Again:</b> This button will forget all movement that you have done 
and start again.
</li>
<li><b>Replay with original visibility settings:</b> This checkbox chooses whether 
replay includes all changes to visibility settings that were made. When it is 
unchecked, replay takes place using the current visibility settings.
</li>
</ul>

<h5>RECORDING TO VIDEO</h5>
<p>{identity.PRODUCT} can record the movements to a video. Recording will capture
replay events as well as the original actions. Each start and stop creates a separate
video file.
</p>
<ul>
<li><b>Frame rate of videos:</b> Choose the frame rate which which videos are created.
</li>
<li><b>Record:</b> Start recording to a video file whose name is time-stamped.
</li>
<li><b>Play:</b> Play back the last recorded video file.
</li>
<li><b>View Folder:</b> Open the folder where the video files are saved.
</li>
</ul>
"""

keys = """
<h5>VISIBILITY</h5>
f = Show faces<br>
e = Show edges<br>
c = Show corners<br>
i = Show intermediate steps<br>
t = Show center<br>
p = Perspective view<br>
v = Show vanishing point<br>
----<br>
d = Depth of perspective<br>
g = Amount of ghosting<br>
r = Rotation per click in degrees<br>
z = Resizing during rotation<br>
----<br>
o = Show coordinates<br>
n = Show corner numbers<br>
For dimensions of 4 or more:<br>
w = Set edge width to 1<br>
o = Set edge color to gray<br>
----<br>
h = Show hints<br>

<h5>MOVEMENT</h5>
1-9 = Rotation in that plane (1-3 = X,Y,Z)<br>
0 = Random rotation<br>
Ctrl+1 etc. Rotates in the opposite direction<br>
+,- = Zoom in, out<br>
Arrows = Movement<br>

<h5>REPLAYING</h5>
s = Replay with original visibility settings<br>
Space = Replay<br>
Esc = Stop<br>
a = Show Actions<br>
<br>
"""