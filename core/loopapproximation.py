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
    def __init__(self, glob, obj):
        self.pi2 = math.pi * 2
        self.beta = []
        self.obj = obj
        self.glob = glob
        self.adjacent_even = {}
        self.adjacent_odd = {}
        self.facesAttached = {}
        self.edgesAttached = {}
        self.evenVertsNew = None        # array filled with -1 at start, later contains position of newly created vertex
        self.ncoords = None             # new coordinates
        self.nuvs = None                # new uv coordinates
        self.indices = None             # new indices for drawarray
        self.ncount  = 0                # counter for new coordinates   TODO make local
        self.ucount  = 0                # counter for new uvs   TODO make local
        self.icount  = 0                # counter for new indices   TODO make local

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
                if face[i] > face[j]:
                    v1, v2 = face[j], face[i]
                else:
                    v1, v2 = face[i], face[j]

                nface = self.edgesAttached[v1][v2][0]
                if nface == fIndex:
                    if self.edgesAttached[v1][v2][1] < 0:
                        continue
                    nface = self.edgesAttached[v1][v2][1]

                for nv in faceverts[nface]:
                    if nv != v1 and nv != v2:
                        self.adjacent_odd[fIndex][i] = nv
                    break

    def createSubTriangle(self, fIndex, verts, coords, uvs):
        """
        calculate 4 sub triangles (atm only vertices)
        (coords array like in object3d.py)
        """
        # The odd vertices are the new ones
        #
        a_odd = self.adjacent_odd[fIndex]
        oddIndex = [0, 0, 0]
        for i in range(0,3):
            j = (i+1) % 3               # to generate 0, 1, 2, 0
            k = (i+2) % 3
            v1, v2, v3 = verts[i], verts[j], verts[k]
            a, b, c = coords[v1], coords[v2], coords[v3]
            u1, u2, d = uvs[v1], uvs[v2], uvs[v3]

            if v1 > v2:
                v1, v2 = v2, v1

            if self.edgesAttached[v1][v2][2] is None:
                if a_odd[i] != -1:
                    # not a boundary, so calculate interior vertex
                    #
                    d = coords[a_odd[i]]
                    v = 0.375 *( a + b)+  0.125 *(c + d)
                else:
                    # calculate on boundary
                    #
                    v = 0.5 * (a + b)
                self.edgesAttached[v1][v2][2] = self.ncount
                oddIndex[i] = self.ncount
                self.ncoords[self.ncount] = v
                self.nuvs[self.ucount] =  0.5 * (u1 + u2)
                self.ncount += 1
                self.ucount += 1
            else:
                #n = self.edgesAttached[v1][v2][2]
                #print (str(i) + " is already calculated as vertex number " + str(n))
                oddIndex[i] = self.edgesAttached[v1][v2][2]


        # the even ones should replace the orignal vertices
        #
        evenIndex = [0, 0, 0]

        for i in range(0,3):
            j = (i+1) % 3               # to generate 0, 1, 2, 0

            v1 = coords[verts[i]]
            if self.evenVertsNew[verts[i]] == -1:
                if a_odd[i] != -1:
                    adj = self.adjacent_even[verts[i]]
                    k = len(adj)
                    beta = self.beta[k]
                    sumk = coords[adj[0]].copy()

                    for elem in adj[1:]:
                        sumk+=coords[elem]
                    vn = v1 *(1-k*beta) + sumk *beta
                else:
                    v2 = coords[verts[j]]
                    vn = 0.125 *(v1 + v2) + 0.75 * v1

                self.ncoords[self.ncount] = vn
                self.evenVertsNew[verts[i]] = self.ncount
                evenIndex[i] = self.ncount
                self.nuvs[self.ucount] =  uvs[verts[i]]
                self.ncount += 1
                self.ucount += 1
            else:
                evenIndex[i] = self.evenVertsNew[verts[i]]
                #print (str(i) + " already calculate as number " + str(self.evenVertsNew[verts[i]]))

        # now create opengl index for these 4 new triangles
        #
        c = self.icount
        self.indices[c:c+12] = [
            evenIndex[0], oddIndex[0], oddIndex[2],
            evenIndex[1], oddIndex[1], oddIndex[0],
            evenIndex[2], oddIndex[2], oddIndex[1],
            oddIndex[0], oddIndex[1], oddIndex[2]
        ]
        self.icount += 12


    def doCalculation(self):

        #TODO this should work with hidden verts etc.
        # could be solved via reshaped indices (?)
        #
        # prepare algorithm, reshape coords to vectors and get a new index to mark the calculated indices

        print ("Subdividing " + self.obj.name)
        #if self.obj.name != "generic":
        return

        faceverts = self.obj.fverts
        #faceverts = self.obj.gl_icoord.copy().reshape(len(self.obj.gl_icoord) // 3, 3)
        clen = len(self.obj.gl_coord) // 3
        coords = np.reshape(self.obj.gl_coord , (clen,3))
        ulen = len(self.obj.gl_uvcoord) // 2
        uvs = np.reshape(self.obj.gl_uvcoord , (ulen,2))

        # helper for even vertices, which contains positions in new array
        #
        self.evenVertsNew = np.full(clen, -1,  dtype=np.int32)

        # new coordinates (maximum is double size)
        # new index array (4 triangles instead of one, so 4 times obj.n_fverts
        #
        self.ncoords = np.zeros((clen*4, 3), dtype=np.float32)
        self.nuvs    = np.zeros((ulen*4, 2), dtype=np.float32)
        self.indices = np.zeros(self.obj.n_fverts * 4, dtype=np.uint32)


        # get a dictionary of faces and edges
        #
        self.facesAttached, self.edgesAttached = self.obj.calculateAttachedGeom(faceverts)

        # calculate even and odd Neighbours
        #
        maxn = self.calcNeighboursEven(faceverts)
        self.calcNeighboursOdd(faceverts)

        # number of max. connected vertices will form betas
        #
        self.createBetas(maxn)

        # foreach triangle now 4 triangles are created, make sure that the odd neighbors are not
        # atm the deduplication is implemented completely, coords and indices are calculated
        # TODO: overflow uvs?
        #
        #for i in range(0, 20):
        for i in range(0, len(faceverts)):
            self.createSubTriangle(i, faceverts[i], coords, uvs)

        # reduce to size .. at least this is needed for testing
        #
        self.ncoords = np.resize(self.ncoords, (self.ncount, 3))
        print (self.ncoords)
        print (self.ncount)
        self.indices = np.resize(self.indices, (self.icount))
        print (self.indices)
        self.nuvs = np.resize(self.nuvs, (self.ucount, 2))
        print (self.nuvs)
        # testing by replacing original mesh
        self.glob.midColumn.view.deleteObject(self.obj)
        self.obj.coord = self.ncoords
        self.obj.n_verts = len(self.ncoords)
        self.obj.n_origverts = self.obj.n_verts 
        self.obj.gl_coord = self.ncoords.flatten()
        self.obj.gl_icoord= self.indices
        self.obj.gl_uvcoord=self.nuvs.flatten()
        self.obj.fverts=np.reshape(self.indices, (self.icount//3,3))
        self.obj.n_fverts = self.icount//3
        self.obj.overflow = []
        self.obj.calcNormals()
        self.obj.min_index = None
        self.glob.midColumn.view.createObject(self.obj)
        self.glob.midColumn.view.Tweak()

