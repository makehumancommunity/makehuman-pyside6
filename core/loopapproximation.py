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
from core.debug import measureTime
from obj3d.object3d import object3d

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
        self.overflow = {}
        self.ovcount = 0

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

    def createSubTriangle(self, fIndex, verts, uvverts, coords, uvs, maxmesh):
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

            # UVS
            w1, w2, w3 = uvverts[i], uvverts[j], uvverts[k]
            u1, u2, d = uvs[w1], uvs[w2], uvs[w3]

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
                self.ncount += 1
                # UVS
                self.nuvs[self.ucount] =  0.5 * (u1 + u2)
                self.ucount += 1
                # mark it as done? like this self.edgesAttached[v1][v2][3] = True

            else:
                #n = self.edgesAttached[v1][v2][2]
                #print (str(i) + " is already calculated as vertex number " + str(n))
                oddIndex[i] = self.edgesAttached[v1][v2][2]

            if w1 >= maxmesh and w2 >= maxmesh:
                if w1 > w2:
                    w1, w2 = w2, w1

                uvn = (w1,w2)
                oi = oddIndex[i]
                if uvn not in self.overflow:
                    ni = 0x80000000 + self.ovcount
                    self.ovcount += 1
                    self.overflow[uvn] = { "oldindex": oi, "newindex": ni,  "uv": 0.5 * (u1 + u2) }
                    oddIndex[i] = ni
                else:
                    oddIndex[i] = self.overflow[uvn]["newindex"]


        # the even ones should replace the orignal vertices
        # edges-vertex: two edges are border
        #
        evenIndex = [0, 0, 0]

        for i in range(0,3):
            j = (i+1) % 3               # to generate 0, 1, 2, 0

            v1 = coords[verts[i]]
            uvn = uvverts[i]
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
                    vn = 0.125 *(v1 + v2) + 0.75 * v1       # TODO:  I am not sure. the border method is a bit strange

                self.ncoords[self.ncount] = vn
                self.evenVertsNew[verts[i]] = self.ncount
                evenIndex[i] = self.ncount
                self.ncount += 1

                # UVS
                self.nuvs[self.ucount] =  uvs[uvn]
                self.ucount += 1
            else:
                evenIndex[i] = self.evenVertsNew[verts[i]]
                #print (str(i) + " already calculate as number " + str(self.evenVertsNew[verts[i]]))

            if uvn >= maxmesh:
                oi = evenIndex[i]
                if uvn not in self.overflow:
                    ni = 0x80000000 + self.ovcount
                    self.ovcount += 1
                    self.overflow[uvn] = { "oldindex": oi, "newindex": ni,  "uv": uvs[uvn] }
                    evenIndex[i] = ni
                else:
                    evenIndex[i] = self.overflow[uvn]["newindex"]


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

    def deDupFaceVerts(self):
        # sort overflow
        #
        mx = self.obj.n_origverts
        ov = self.obj.overflow
        ov = ov[ov[:,1].argsort()]
        fv = self.obj.fverts.copy()
        for elem in fv:
            for i,v in enumerate(elem):
                if v >= mx:
                    elem[i] = ov[v-mx][0]
        return(fv)

    def doCalculation(self):

        #TODO this should work with hidden verts etc.
        # could be solved via reshaped indices (?)
        #
        # prepare algorithm, reshape coords to vectors and get a new index to mark the calculated indices

        print ("Subdividing " + self.obj.name)
        #if self.obj.name != "generic":
        m = measureTime("subdivision")
        clen = len(self.obj.gl_coord) // 3
        coords = np.reshape(self.obj.gl_coord , (clen,3))  # coordinates are including overflow

        #faceverts = self.obj.fverts
        faceverts = self.deDupFaceVerts()
        m.passed("deduplication of faces")

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
        m.passed("attached geometry calculated")

        # calculate even and odd Neighbours
        #
        maxn = self.calcNeighboursEven(faceverts)
        m.passed("even faces vertices calculated")
        self.calcNeighboursOdd(faceverts)
        m.passed("odd faces vertices calculated")

        # number of max. connected vertices will form betas
        #
        self.createBetas(maxn)

        # foreach triangle now 4 triangles are created, make sure that the odd neighbors are not
        # atm the deduplication is implemented completely, coords and indices are calculated
        # TODO: not yet working 100 % percent correct no hidden verts
        #
        for i in range(0, len(faceverts)):
            self.createSubTriangle(i, faceverts[i], self.obj.fverts[i], coords, uvs, self.obj.n_origverts)
        m.passed("sub triangles calculated")


        # we need duplicate vertices into the overflow buffer
        #
        numextra = len(self.overflow)
        # then copy change size and copy coords to end

        # reduce to size .. at least this is needed for testing
        #
        self.ncoords = np.resize(self.ncoords, (self.ncount + numextra, 3))
        self.nuvs = np.resize(self.nuvs, (self.ucount + numextra, 2))
        #print (self.ncount)
        #print (self.ucount)
        self.indices = np.resize(self.indices, (self.icount))


        overflowtable = np.empty((numextra, 2), dtype=np.uint32)
        ncount = self.ncount 
        for elem in self.overflow.values():
            # print(elem)
            oind =  elem["oldindex"]
            ind = elem["newindex"] - 0x80000000
            overflowtable[ind] = [ oind , ncount]
            self.nuvs[ncount] = elem["uv"]
            self.ncoords[ncount] = self.ncoords[oind]
            ncount += 1

        for i, n in enumerate(self.indices):
            if n >=  0x80000000:
                self.indices[i] = self.ncount + n - 0x80000000
        #
        # better "new" function needed

        subdiv = object3d(self.glob, None, self.obj.type)
        subdiv.visible = self.obj.visible
        subdiv.is_base = self.obj.is_base
        subdiv.material = self.obj.material
        subdiv.z_depth = self.obj.z_depth

        subdiv.coord = self.ncoords
        subdiv.n_verts = len(self.ncoords)
        subdiv.n_origverts = subdiv.n_verts 
        subdiv.gl_coord = self.ncoords.flatten()
        subdiv.gl_icoord= self.indices
        subdiv.gl_uvcoord=self.nuvs.flatten()
        subdiv.fverts=np.reshape(self.indices, (self.icount//3,3))
        subdiv.n_fverts = self.icount//3
        subdiv.overflow = overflowtable
        subdiv.calcNormals()
        m.passed("normals calculated")
        subdiv.min_index = None
        self.glob.midColumn.view.createObject(subdiv)
        self.glob.midColumn.view.Tweak()
        m.passed("all assignments done")

