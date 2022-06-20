#!/bin/env python

"""
The original code is from
  http://www.petercollingridge.co.uk/pygame-3d-graphics-tutorial/using-matrices
See rbaleksandar answer at
  https://math.stackexchange.com/questions/363652/understanding-rotation-matrices
Each column of a rotation matrix represents one of the axes of the space it is
applied in. In two dimensions, the standard rotation matrix has the form:
    | cos R  -sin R |
    | sin R   cos R |
In higher dimensions, we rotate around a plane, and apply this rotation to the
two axes of the plane.
"""

import copy
import numpy as np

import colors


def add_face_color(face, nodes):
    """Add a color to a face instance.

    A face is 4 nodes (points) in a plane. We color all faces in the same
    plane, e.g. the opposite faces of a cube, in the same color. To find what
    the two dimensions making up that plane are, we compare the node values
    of every dimension, looking for the two dimensions where the values vary.
    That pair is mapped to a unique color by colors.face()
    """
    node0 = nodes[face.node[0]]
    node1 = nodes[face.node[1]]
    node2 = nodes[face.node[2]]
    node3 = nodes[face.node[3]]
    other = [node1, node2, node3]
    # make a list of every dimension whose values are not all the same
    changes = []
    for dim, value in enumerate(node0):
        mismatch = [node[dim] for node in other if node[dim] != value]
        if mismatch:
            changes.append(dim)
        if len(changes) == 2:
            # no need to look any further; there are only two dimensions
            # that differ
            break
    face.color = colors.face(changes)


class Face:
    def __init__(self):
        self.node = [0] * 4
        self.out = True
        self.color = ""

class Wireframe:
    def __init__(self, dims):
        self.dims = dims
        # create a NumPy array with 0 rows, 1 col per dim, 1 for scale
        self.nodes = np.zeros((0, dims + 1))
        # List of edges; each edge is [node_index1, node_index2, color]
        self.edges = []
        # List of Face() instances
        self.faces = []

    def add_nodes(self, node_array):
        ones_column = np.ones((len(node_array), 1))
        ones_added = np.hstack((node_array, ones_column))
        self.nodes = np.vstack((self.nodes, ones_added))

    def add_edges(self, edgeList):
        self.edges += edgeList

    def add_shape_sizes(self, orgx=50, orgy=50, sizes=[200]):
        """Create a shape and set up its nodes and edges."""

        orgs = [0] * self.dims
        orgs[0] = orgx
        orgs[1] = orgy
        # make sure there is a size for each dimension
        while len(sizes) < self.dims:
            sizes.append(sizes[-1])
        center = [0] * self.dims
        # calculate the center along each dimension
        for d in range(self.dims):
            center[d] = int(round(orgs[d] + sizes[d] / 2))

        nodes = []
        edges = []
        faces = []
        # start with a point
        nodes.append([])
        # extend everything along the axes
        for dim in range(self.dims):
            edge_color = colors.bgr[dim]
            begin = orgs[dim]
            end = begin + sizes[dim]
            node_count = len(nodes)
            # When we extend this shape into the next dimension:
            # * node count will be double
            # * edge count will be double + number of nodes in previous dimension
            # * face count will be double + number of edges in previous dimension
            # * (and so on for cubes, tesseracts, etc., but we ignore those)
            # and their locations will be different,
            # so copy the existing faces, edges and nodes:

            # Make a copy of every existing face
            new_faces = copy.deepcopy(faces)
            # Each new face will be defined by new nodes (that have not been
            # created yet, but that doesn't matter) whose indices follow on
            # from the existing ones.
            for new_face in new_faces:
                new_face.node[0] += node_count
                new_face.node[1] += node_count
                new_face.node[2] += node_count
                new_face.node[3] += node_count
                new_face.out ^= True

            # Make a copy of every existing edge
            new_edges = copy.deepcopy(edges)
            # Adjust their node indices (again, these nodes don't exist yet)
            # and create a face for every edge that has been moved.
            for new_edge in new_edges:
                # A face is 4 nodes; the first two are the ends of the edge before moving it;
                # face = [new_edge[0], new_edge[1], 0, 0]
                face = Face()
                face.node[0] = new_edge[0]
                face.node[1] = new_edge[1]
                # adjust the location of the new edge
                new_edge[0] += node_count
                new_edge[1] += node_count
                # the second 2 nodes of the face are the ends of the edge after moving it
                face.node[2] = new_edge[1]
                face.node[3] = new_edge[0]
                faces.append(face)

            # Make a copy of every existing node
            new_nodes = [None] * node_count
            nodes.extend(new_nodes)
            for ndx in range(node_count):
                old_node = nodes[ndx]
                # create a new node
                new_node = old_node.copy()
                # add the location in this dimension to the existing node
                old_node.append(begin)
                # add the location in this dimension to the new node
                new_node.append(end)
                # put the new node on the list
                nodes[ndx + node_count] = new_node
                # extending this node into the next dimension creates another
                # edge, identified by the two node indices
                edges.append([ndx, ndx + node_count, edge_color])

            # add these extended objects to the existing ones
            faces.extend(new_faces)
            edges.extend(new_edges)

        # color the faces
        for face in faces:
            add_face_color(face, nodes)

        self.add_nodes(nodes)
        self.add_edges(edges)
        self.faces = faces
        self.center = center

    def get_edge_z(self, edge):
        """Get 2x the z-value of the midpoint of the edge."""
        return self.nodes[edge[0]][2] + self.nodes[edge[1]][2]

    def get_face_z(self, face):
        """Get 4x the z-value of the midpoint of the face."""
        return (
            self.nodes[face.node[0]][2] +
            self.nodes[face.node[1]][2] +
            self.nodes[face.node[2]][2] +
            self.nodes[face.node[3]][2]
        )

    def get_rotate_matrix(self, dim1, dim2, radians, a=None):
        """Return matrix for rotating about the x-axis by 'radians' radians"""

        if a is None:
            a = np.eye(self.dims + 1)
        c = np.cos(radians)
        s = np.sin(radians)
        a[dim1][dim1] = c
        a[dim1][dim2] = -s
        a[dim2][dim1] = s
        a[dim2][dim2] = c
        return a

    def get_scale_matrix(self, scale):
        """Return matrix for scaling equally along all axes.

        return np.array([[s, 0, 0, 0],
                         [0, s, 0, 0],
                         [0, 0, s, 0],
                         [0, 0, 0, 1]])
        """
        dims = self.dims
        a = np.eye(dims + 1)
        for n in range(dims):
            a[n][n] = scale
        return a

    def get_translation_matrix(self, vector):
        """Return matrix for translation along vector (dx, dy, dz).

        return np.array([[1, 0, 0, 0],
                         [0, 1, 0, 0],
                         [0, 0, 1, 0],
                         [v, v, v, 1]])
        """

        dims = self.dims
        a = np.eye(dims + 1)
        a[dims][:dims] = vector
        return a

    def output_nodes(self):
        print("\n --- Nodes --- ")
        for i, node in enumerate(self.nodes):
            print(f"{i:3}: ", end="")
            for j in node[:-1]:
                print(f"{j:>-7}, ", end="")
            print()

    def output_edges(self):
        print("\n --- Edges --- ")
        for i, (node1, node2, color) in enumerate(self.edges):
            print("%2d: %2d -> %2d " % (i, node1, node2), color)

    def findCentre(self):
        """Unused for now."""
        num_nodes = len(self.nodes)
        meanX = sum([node.x for node in self.nodes]) / num_nodes
        meanY = sum([node.y for node in self.nodes]) / num_nodes
        meanZ = sum([node.z for node in self.nodes]) / num_nodes

        return (meanX, meanY, meanZ)

    def sort_edges(self):
        """Sort the edges so that the furthest away is first in the list,
        and hence gets drawn first and is then overlaid by nearer ones.
        "Furthest away" means furthest on the z-axis, and we use the
        midpoint of the edge for this (except there's no need to divide
        by 2 for each edge)
        """

        self.edges.sort(key=self.get_edge_z, reverse=True)

    def sort_faces(self):
        """See explanation for sort_edges()."""

        self.faces.sort(key=self.get_face_z, reverse=True)

    def transform(self, matrix):
        """Apply a transformation defined by a given matrix."""

        self.nodes = np.dot(self.nodes, matrix)
