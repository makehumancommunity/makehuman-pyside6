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

class LoopApproximation:
    def __init__(self, obj):
        self.pi2 = math.pi * 2
        self.beta = []
        self.obj = obj

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
        get the attached faces of a vertex for further calculation, then create neighbours of even vertices
        """

        attached = self.obj.calculateAttachedFaces(faceverts)

        # create edges from triangle, that is each triangle connected without vertex itself, make this unique
        #
        adjacent_even = {}
        maxn = 0
        for vert, faces in attached.items():
            adjacentverts = []
            for face in faces:
                for nvert in self.obj.gl_fvert[face]:
                    if nvert != vert and nvert not in adjacentverts:
                        adjacentverts.append(nvert)
            if len(adjacentverts) > maxn:
                maxn = len(adjacentverts)
            adjacent_even[vert] = adjacentverts

        #print (adjacent_even)
        return(maxn)

    def doCalculation(self):

        #TODO this should work with hidden verts etc.
        #
        maxn = self.calcNeighboursEven(self.obj.gl_fvert)

        # number of max. connected vertices will form betas
        #
        self.createBetas(maxn)
        print (self.beta)

