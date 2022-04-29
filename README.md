# Hypercube-viewer

Hypercube-viewer is a program that visualizes a hypercube of 3 to 10 dimensions.

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

The points, edges and/or faces are projected onto a plane surface (the x-y plane) in either a perspective or orthographic view.

## How is the hypercube rotated?

In the real world, we think of rotation as about an axis. A square on your screen being rotated clockwise is though of as rotating around the z-axis that projects perpendicularly from the screen, but what is actually changing are the x- and y-coordinates of the 4 corners. Similarly, rotation around the x-axis is donw by rotating the y-z plane. For a higher dimension D, the only rotations visible on the screen (the x-y surface) are rotations in the x-D plane and the y-D plane. Hypercube-viewer allows the user to rotate in both directions around these higher planes.

## Available controls

### Setup

* **Number of dimensions:** Choose from 3 to 10.
* **Aspect ratios:** It need not be a cube. Here, you can set the ratios of the edges for each dimension, for instance: 16:9:4 specifies a cuboid with width of 16, height of 9 and depth of 4. Additional dimensions take the value of the rightmost one specified.
* **Viewing size:** The size in pixels of the plane surface on which the Hypercube is projected.

### Visibility

* **Show faces, edges, corners:** Control what is drawn.
* **Show coordinates:** Show the coordinates of every point. Points may overlap for, say, a cube in orthogonal view. Avoid this by using perspective view and/or rotating the object so that every point is at a different place on screen.
* **Show intermediate steps:** 
* **Show center:** Show the centerpoint of the hypercube.
* **Perspective view:** Choose whether the hypercube is projected as a perspective or orthographic view.
* **Show vanishing point:** When perspective view is selected, show the vanishing point.
* **Depth of perspective:** Controls the amount of perspective. The vanishing point is placed at this value times the screen width.
* **Amount of ghosting:** As the hypercube moves, the program can leave a ghost image that fades out. 0 indicates no ghosting, and with 10, no fading takes place.


