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
import random

import numpy as np

import colors

class Wireframe:

    def __init__(self, dims):
        self.dims = dims
        # create a NumPy array with 0 rows, 1 col per dim, 1 for scale
        self.nodes = np.zeros((0, dims + 1))
        self.edges = []

    def add_nodes(self, node_array):
        ones_column = np.ones((len(node_array), 1))
        ones_added = np.hstack((node_array, ones_column))
        self.nodes = np.vstack((self.nodes, ones_added))

    def add_edges(self, edgeList):
        self.edges += edgeList

    def add_center(self, center):
        self.center = center

    def add_shape(self, orgx=50, orgy=50, minsize=200, maxsize = 0):
        """ Create a shape and set up its nodes and edges."""

        sizes = [0] * self.dims
        for d in range(self.dims):
            if maxsize:
                sz = random.randrange(minsize, maxsize)
            else:
                sz = minsize
            sizes[d] = sz
        self.add_shape_sizes(orgx, orgy, sizes)

    def add_shape_sizes(self, orgx=50, orgy=50, sizes=[200]):
        """ Create a shape and set up its nodes and edges."""

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
        # start with a point
        nodes.append([])
        # extend everything along the axes
        for dim in range(self.dims):
            edge_color = colors.bgr[dim]
            begin = orgs[dim]
            end = begin + sizes[dim]
            node_count = len(nodes)
            edge_count = len(edges)
            new_edges = copy.deepcopy(edges)
    ##        print('new edges b4', new_edges)
            for new_edge in new_edges:
                new_edge[0] += node_count
                new_edge[1] += node_count
    ##        print('new edges af', new_edges)
            new_nodes = []
            for ndx, node in enumerate(nodes):
                new_node = node.copy()
                node.append(begin)
                new_node.append(end)
                new_nodes.append(new_node)
                edges.append([ndx, ndx + node_count, edge_color])
            nodes.extend(new_nodes)
            edges.extend(new_edges)

    ##    print('nodes', nodes)
    ##    print('edges', edges)
        self.add_nodes(nodes)
        self.add_edges(edges)
        self.add_center(center)

    def get_rotate_matrix(self, dim1, dim2, radians, a=None):
        """ Return matrix for rotating about the x-axis by 'radians' radians """

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
        """ Return matrix for scaling equally along all axes.

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
        """ Return matrix for translation along vector (dx, dy, dz).

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
        for i, (x, y, z, _) in enumerate(self.nodes):
            print("%2d: (%3d, %3d, %3d)" % (i, x, y, z))

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

    def transform(self, matrix):
        """ Apply a transformation defined by a given matrix. """
    
        self.nodes = np.dot(self.nodes, matrix)

if __name__ == "__main__":
    cube = Wireframe(3)
    cube.add_shape()
    # print the nodes and edges
    cube.output_nodes()
    cube.output_edges()
