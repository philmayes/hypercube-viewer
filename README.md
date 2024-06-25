# Hypercube Viewer

Hypercube Viewer is a program that draws a hypercube of 3 to 10 dimensions.

## What is a hypercube?

Start with a point. It has no dimensions. Now move that point along a dimension. In doing so, you create a second point and also create a line (a one-dimensional object.) Now move that line along a dimension at right-angles (aka orthogonal) to the first dimension. You double the number of points and lines, and also create two new lines from the movement of the points. Voila! A square. Now repeat the process by moving the square along a new dimension orthogonal to the existing two dimensions, and you have created a cube. Note that it has 6 faces; one by moving the square in the new (third) dimension, and 4 from moving the 4 lines of the square along the new dimension.

Now move that cube along an orthogonal fourth dimension. You now have 8 cubes; the original; one from the original being moved; and 6 from the 6 faces of the original cube being extended. This object is called a tesseract.

We can continue this process without end. A 5-cube has 32 points, etc. Each value in this table comes from doubling the value above and adding the value above and in the previous column.

| # Dims | Points | Edges | Faces | Cubes |
| :----: | -----: | ----: | ----: | ----: |
|      0 |      1 |       |       |       |
|      1 |      2 |     1 |       |       |
|      2 |      4 |     4 |     1 |       |
|      3 |      8 |    12 |     6 |     1 |
|      4 |     16 |    32 |    24 |     8 |
|      5 |     32 |    80 |    80 |    50 |

## Drawing the hypercube

The points, edges and/or faces are projected onto a plane surface (the x-y plane) in either a perspective or orthographic view. The origin is at the top left with the x-axis horizontal, the y-axis pointing down, and the Z-axis projecting into the screen.

**NOTE:** Some of the drawing calculations take a long time. Factors that exacerbate this are:
* A large number of dimensions
* Drawing the faces
* Showing intermediate steps
* Showing ghosting
* Resizing during rotation
* Showing partially transparent faces

These delays do NOT occur in the video recording.

## How is the hypercube rotated?

In the real world, we think of rotation as about an axis. A square on your screen being rotated clockwise is though of as rotating around the z-axis that projects perpendicularly from the screen, but what is actually changing are the x- and y-coordinates of the 4 corners. Similarly, rotation around the x-axis is done by rotating the y-z plane. 

The concept of rotating about an axis works in 3 dimensions because, for any axis, there is only one plane that that is perpendicular to that axis. For higher dimension, each dimension is perpendicular to more than one plane, so naming the dimension would be ambiguous and XXXX. For a higher dimension D, the only rotations visible on the screen (the x-y surface) are rotations in the x-D plane and the y-D plane. Hypercube-viewer allows the user to rotate in both directions around these higher planes.

For random rotations, Hypercube Viewer rotates about two randomly-chosen planes at once.

## Available controls

### SETUP

* **Number of dimensions:** Choose from 3 to 10.
* **Aspect ratios:** It need not be a cube. Here, you can set the ratios of the edges for each dimension, for instance: 16:9:4 specifies a cuboid with width of 16, height of 9 and depth of 4. Additional dimensions take the value of the rightmost one specified.
* **Viewing size:** The size in pixels of the plane surface on which the Hypercube is projected.

### VISIBILITY

* **Show faces, edges, corners:** Control what is drawn.
* **Show intermediate steps:** Draw the intermediate steps of moves and rotations. Note that this may slow the operation, especially when the hypercube has a large number of dimensions.
* **Show center:** Show the centerpoint of the hypercube.
* **Perspective view:** Choose whether the hypercube is projected as a perspective or orthographic view.
* **Show vanishing point:** When perspective view is selected, show the vanishing point.
* **Depth of perspective:** Controls the amount of perspective. The vanishing point is placed at this value times the screen width.
* **Amount of ghosting:** As the hypercube is moved, the program can leave a ghost image that fades out. 0 indicates no ghosting, and with 10, no fading takes place.
* **Rotation per click:** The rotation in degrees per click.
* **Resizing during rotation:** The program can resize the object during rotation. This gives the amount by which the object is scaled. The rotation is slower because of this. <ins>Note</ins> that when intermediate steps are shown, a fraction of the scaling takes place for every step, making it much slower. When there are a large number of dimensions, the speed is even worse. This speed slowdown does not show in recorded videos.
* **Opacity:** The opacity of the faces. <ins>Note</ins> that when the faces are translucent, drawing times are much slower.

In Preferences, accessed through the menu, you can also change:

* **Corner radius**
* **Center radius**
* **Vanishing point radius**
* **Line width**
* **Font Size:** The font size for coordinates and corner numbers.
* **Show coordinates:** Show the coordinates of every point. The points may overlap for, say, a cube in orthogonal view. Avoid this by using perspective view and/or rotating the object so that every point is at a different place on screen.
* **Show corner numbers:** Show the internal index number of all corners.
* **Set line width to 1:** For dimensions of 4 or more, set the line width to 1.
* **Set line color to gray:** For dimensions of 4 or more, set the line color to gray.

### MOVEMENT

The object can be rotated around various planes, moved, zoomed and shrunk.

* **Replay:** This button will replay all the movement and visibility actions from the beginning.
* **Stop:** This button will stop replay and also long movement operations.
* **Show Actions:** This button shows a list of all the actions performed so far.
* **Begin Again:** This button will forget all movement that you have done and start again.
* **Replay with original visibility settings:** This checkbox chooses whether replay includes all changes to visibility settings that were made. When it is unchecked, replay takes place using the current visibility settings.

### REQUIREMENTS

It requires the following packages:

* numpy
* opencv-python
* pillow
* tkhtmlview

### RECORDING TO VIDEO

Hypercube Viewer can record the movements to a video. Recording will capture
replay events as well as the original actions. Each start and stop creates a separate
video file.

* **Frame rate of videos** Choose the frame rate which which videos are created.
* **Record** Start recording to a video file whose name is time-stamped.
* **Play** Play back the last recorded video file.
* **View Folder** Open the folder where the video files are saved.

### EXAMPLE

[Youtube demonstration](https://www.youtube.com/embed/KZZ3qxXrC58)
