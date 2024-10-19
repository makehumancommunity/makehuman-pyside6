"""
realization of loop subdivision algorithm, invented by Charles Loop

loop algorithm only works with triangles

Naming:
* newly created vertices = odd vertices
* original but changed vertices = even vertices

Algorithm (one iteration)
1. Build adjacency data structure
    (a) Neighbours of each vertex via faces (even)
    (b) create edge neighbours (odd)

2. create cosines to get "Beta" according to loop from even values
3. Compute odd vertices
4. Compute even vertices
5. Rebuild mesh / Connect vertices to create new faces

"""

import math
import numpy as np

class LoopApproximation:
    def __init__(self, obj):
        self.pi2 = math.pi * 2
        self.beta = []
        self.obj = obj
        self.adjacent_even = {}
        self.adjacent_odd = {}
        self.facesAttached = {}

    def createBetas(self, maxn):
        """
        creates beta values only once to speed up calculation
        """
        self.beta = [0, 0, 0, 0.1875 ] # first ones are constant
        for k in range(4, maxn+1):
            m = 0.375 + (math.cos(self.pi2 / float(k)) / 4.0)
            m *= m
            self.beta.append(1.0 / float(k) * (0.625 - m))

    def calcNeighboursEven(self, faceverts):
        """
        create neighbours of even vertices
        for each face which is attached to a vertex check all other faces if that vertex is also
        contained, if so add these vertices, make them unique and do not add the same vertex again
        """

        maxn = 0
        for vert, faces in self.facesAttached.items():
            adjacentverts = []
            for face in faces:
                for nvert in faceverts[face]:
                    if nvert != vert and nvert not in adjacentverts:
                        adjacentverts.append(nvert)
            if len(adjacentverts) > maxn:
                maxn = len(adjacentverts)
            self.adjacent_even[vert] = adjacentverts
        return(maxn)

    def calcNeighboursOdd(self, faceverts):
        """
        for each face (triangle) check the edges and test to which other face both vertices of
        the edge also contained. If a common edge is found and it is not the same, figure out
        the missing vertex of the neighbour triangle, set -1 for missing vertex (boundary)
        """
        for fIndex, face in enumerate(faceverts):
            self.adjacent_odd[fIndex] = [-1, -1, -1]
            for i in range(0,3):
                j = (i+1) % 3               # to generate 0, 1, 2, 0
                v1, v2 = face[i], face[j]
                for l in self.facesAttached[v1]:
                    if l != fIndex and l in self.facesAttached[v2]:
                        for nv in faceverts[l]:
                            if nv != v1 and nv != v2:
                                self.adjacent_odd[fIndex][i] = nv
                                break

    def createSubTriangle(self, fIndex, verts, coords):
        """
        calculate the triangle sequence
        """
        # The odd vertices are the new ones
        #
        a_odd = self.adjacent_odd[fIndex]

        a, b, c = coords[verts[0]], coords[verts[1]], coords[verts[2]]
        if a_odd[0] != -1:
            # not a boundary, so calculate interior vertex
            #
            d = coords[a_odd[0]]
            v = 0.375 *( a + b)+  0.125 *(c + d)
        else:
            # calculate on boundary
            #
            v = 0.5 * (a + b)
        print (v)

        if a_odd[1] != -1:
            d = coords[a_odd[1]]
            v = 0.375 *(b + c)+  0.125 *(a + d)
        else:
            v = 0.5 * (b + c)
        print (v)

        if a_odd[2] != -1:
            d = coords[a_odd[2]]
            v = 0.375 *(c + a)+  0.125 *(b + d)
        else:
            v = 0.5 * (c + a)
        print (v)

        # the even ones should replace the orignal vertices
        # (TODO: could be merged with code above, to avoid boundary if/then/else)

        if a_odd[0] != -1:
            adj = self.adjacent_even[verts[0]]
            k = len(adj)
            beta = self.beta[k]
            sumk = coords[adj[0]]

            for elem in adj[1:]:
                sumk+=coords[elem]

            a_new = a *(1-k*beta) + sumk *beta
        else:
            a_new = 0.125 *(a + b) + 0.75 * a

        if a_odd[1] != -1:
            adj = self.adjacent_even[verts[1]]
            k = len(adj)
            beta = self.beta[k]
            sumk = coords[adj[0]]

            for elem in adj[1:]:
                sumk+=coords[elem]

            b_new = b *(1-k*beta) + sumk *beta
        else:
            b_new = 0.125 *(b + c) + 0.75 * b

        if a_odd[2] != -1:
            adj = self.adjacent_even[verts[2]]
            k = len(adj)
            beta = self.beta[k]
            sumk = coords[adj[0]]

            for elem in adj[1:]:
                sumk+=coords[elem]

            c_new = c *(1-k*beta) + sumk *beta
        else:
            c_new = 0.125 *(c + a) + 0.75 * c

        print (a_new, b_new, c_new)



    def doCalculation(self):

        #TODO this should work with hidden verts etc.
        #
        print ("Subdividing " + self.obj.filename)

        faceverts = self.obj.gl_fvert
        clen = len(self.obj.gl_coord) // 3
        coords = np.reshape(self.obj.gl_coord , (clen,3))

        # get a dictionary of vertices with all faces attached
        #
        self.facesAttached = self.obj.calculateAttachedFaces(faceverts)

        # calculate even and odd Neighbours
        #
        maxn = self.calcNeighboursEven(faceverts)
        self.calcNeighboursOdd(faceverts)

        # number of max. connected vertices will form betas
        #
        self.createBetas(maxn)

        # foreach triangle now 4 triangles are created, make sure that the odd neighbors are not
        # added twice, Test for one triangle (deduplication method NEEDED!)
        self.createSubTriangle(0, faceverts[0], coords)



