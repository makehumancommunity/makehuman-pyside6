"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * LoopApproximation

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
        self.maxmesh = self.obj.n_origverts
        self.glob = glob
        self.org_uvs = None
        self.org_coords = None
        self.adjacent_even = {}
        self.adjacent_odd = {}
        self.facesAttached = {}
        self.edgesAttached = {}
        self.border = None
        self.evenVertsNew = None        # array filled with -1 at start, later contains position of newly created vertex
        self.ncoords = None             # new coordinates
        self.nuvs = None                # new uv coordinates
        self.indices = None             # new indices for drawarray
        self.overflow = {}
        self.seam = {}

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

        iplus = [1, 2, 0]
        for fIndex, face in enumerate(faceverts):
            self.adjacent_odd[fIndex] = [-1, -1, -1]
            for i in range(0,3):
                j = iplus[i]            # index + 1
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

    def createSubTriangles(self, faceverts, uvvertsarr):
        """
        calculate 4 sub triangles (atm only vertices)
        (coords array like in object3d.py)
        """

        uvs = self.org_uvs
        coords = self.org_coords
        maxmesh = self.maxmesh
        evenIndex = [0, 0, 0]
        oddIndex = [0, 0, 0]
        ncount = 0
        icount = 0
        ovcount = 0
        iplus = [1, 2, 0]
        jplus = [2, 0, 1]

        for fIndex in range(0, len(faceverts)):
            verts = faceverts[fIndex]
            uvverts = uvvertsarr[fIndex]

            # The odd vertices are the new ones
            #
            a_odd = self.adjacent_odd[fIndex]
            for i in range(0,3):
                j = iplus[i]    # index +1
                k = jplus[i]    # index +2
                v1, v2, = verts[i], verts[j]
                a, b = coords[v1], coords[v2]

                # UVS
                w1, w2 = uvverts[i], uvverts[j]
                un = 0.5 * (uvs[w1]+ uvs[w2]) # new value

                if v1 > v2:
                    v1, v2 = v2, v1

                if self.edgesAttached[v1][v2][2] is None:
                    if a_odd[i] != -1:
                        # not a boundary, so calculate interior vertex
                        #
                        c = coords[verts[k]]
                        d = coords[a_odd[i]]
                        v = 0.375 *( a + b)+  0.125 *(c + d)
                    else:
                        # calculate on boundary
                        #
                        v = 0.5 * (a + b)
                    self.edgesAttached[v1][v2][2] = ncount
                    oddIndex[i] = ncount

                    # coordinate + uv
                    #
                    self.ncoords[ncount] = v
                    self.nuvs[ncount] =  un
                    ncount += 1

                else:
                    oddIndex[i] = self.edgesAttached[v1][v2][2]

                # calculate UVs for seams
                #
                if v1 in self.seam and v2 in self.seam:
                    if w1 > w2:
                        w1, w2 = w2, w1

                    uvn = (w1,w2)
                    if uvn not in self.overflow:
                        ni = 0x80000000 + ovcount
                        ovcount += 1
                        self.overflow[uvn] = [ oddIndex[i], ni, un ]
                        oddIndex[i] = ni
                    else:
                        oddIndex[i] = self.overflow[uvn][1]

            # the even ones should replace the orignal vertices
            # edge-vertex: two edges are border
            #

            for i in range(0,3):
                vi = verts[i]
                v1 = coords[vi]
                uvn = uvverts[i]
                un = uvs[uvn]
                if self.evenVertsNew[vi] == -1:

                    if self.border[vi][1] != 0xffffffff:
                        # in case of border get the border neighbours
                        #
                        vn = 0.125 *(coords[self.border[vi][0]] + coords[self.border[vi][1]]) + 0.75 * v1
                    else:
                        adj = self.adjacent_even[vi]
                        k = len(adj)
                        beta = self.beta[k]
                        sumk = coords[adj[0]].copy()

                        for elem in adj[1:]:
                            sumk+=coords[elem]
                        vn = v1 *(1-k*beta) + sumk *beta
    
                    self.ncoords[ncount] = vn
                    self.evenVertsNew[verts[i]] = ncount
                    evenIndex[i] = ncount
                    # UVS
                    self.nuvs[ncount] =  un
                    ncount += 1
                else:
                    evenIndex[i] = self.evenVertsNew[vi]

                if uvn >= maxmesh:

                    # happens when a second UV value is needed because of a seam
                    #
                    if uvn not in self.overflow:
                        ni = 0x80000000 + ovcount
                        ovcount += 1
                        self.overflow[uvn] = [ evenIndex[i], ni, un ]
                        evenIndex[i] = ni
                    else:
                        evenIndex[i] = self.overflow[uvn][1]


            # now create opengl index for these 4 new triangles
            #
            self.indices[icount:icount+12] = [
                evenIndex[0], oddIndex[0], oddIndex[2],
                oddIndex[0], evenIndex[1], oddIndex[1],
                oddIndex[1], evenIndex[2], oddIndex[2],
                oddIndex[0], oddIndex[1], oddIndex[2]
            ]
            icount += 12

        return ncount, icount

    def deDupFaceVerts(self):
        # 
        # create a reduced mesh, when hidden
        # regenerate the overflow in a second mesh
        #
        mx = self.maxmesh
        ov = self.obj.overflow
        ov = ov[ov[:,1].argsort()]

        indices = self.obj.getOpenGLIndex()
        ilen= len(indices) // 3
        fverts = indices.copy().reshape((ilen, 3))
        uvverts = fverts.copy()

        for elem in fverts:
            for i,v in enumerate(elem):
                if v >= mx:
                    elem[i] = ov[v-mx][0]
        return fverts, uvverts

    def markSeam(self):
        for s,d in self.obj.overflow:
            self.seam[s] = True

    def doCalculation(self):

        # prepare algorithm, reshape coords to vectors and get a new index to mark the calculated indices
        # for hidden vertices, partly coords and uv-coords are not used

        print ("Subdividing " + self.obj.name)
        m = measureTime("subdivision")

        clen = len(self.obj.gl_coord) // 3
        self.org_coords = np.reshape(self.obj.gl_coord , (clen,3))  # coordinates are including overflow

        faceverts, uvverts = self.deDupFaceVerts()
        self.markSeam()

        ulen = len(self.obj.gl_uvcoord) // 2
        self.org_uvs = np.reshape(self.obj.gl_uvcoord , (ulen,2))

        # helper for even vertices, which contains positions in new array
        #
        self.evenVertsNew = np.full(clen, -1,  dtype=np.int32)

        # new coordinates (maximum is double size)
        # new index array (4 triangles instead of one, so 4 times obj.n_fverts
        #
        self.ncoords = np.zeros((clen*4, 3), dtype=np.float32)
        self.nuvs    = np.zeros((ulen*4, 2), dtype=np.float32)
        self.indices = np.zeros(self.obj.n_fverts * 4, dtype=np.uint32)

        # get attached faces, edges and border-neighbours for each vertex
        #
        self.facesAttached, self.edgesAttached, self.border = self.obj.calculateAttachedGeom(faceverts)
        m.passed("attached geometry calculated")

        # calculate even and odd neighbours
        #
        maxn = self.calcNeighboursEven(faceverts)
        self.calcNeighboursOdd(faceverts)
        m.passed("even and odd face vertices calculated")

        # number of max. connected vertices will form betas
        #
        self.createBetas(maxn)

        # foreach triangle now 4 triangles are created
        #
        ncount, icount = self.createSubTriangles(faceverts, uvverts)
        m.passed("sub triangles calculated")

        # reduce to size including UV buffer
        #
        numextra = len(self.overflow)

        self.ncoords = np.resize(self.ncoords, (ncount + numextra, 3))
        self.nuvs = np.resize(self.nuvs, (ncount + numextra, 2))
        self.indices = np.resize(self.indices, (icount))

        # create overflow-table, add missing UVs  and duplicate coordinates
        #
        overflowtable = np.empty((numextra, 2), dtype=np.uint32)
        nind = ncount 

        for oind, ind, uv in self.overflow.values():
            overflowtable[ind - 0x80000000] = [ oind , nind]
            self.nuvs[nind] = uv
            self.ncoords[nind] = self.ncoords[oind]
            nind += 1

        # correct indices marked by first bit
        #
        for i, n in enumerate(self.indices):
            if n >=  0x80000000:
                self.indices[i] = ncount + n - 0x80000000
        #
        # create the new object, TODO better "new" function needed

        subdiv = object3d(self.glob, None, self.obj.type)
        subdiv.visible = self.obj.visible
        subdiv.is_base = self.obj.is_base
        subdiv.material = self.obj.material
        subdiv.z_depth = self.obj.z_depth
        subdiv.name = self.obj.name
        subdiv.filename = "subdiv of " + self.obj.name

        subdiv.coord = self.ncoords
        subdiv.n_verts = len(self.ncoords)
        subdiv.n_origverts = subdiv.n_verts 
        subdiv.gl_coord = self.ncoords.flatten()
        subdiv.gl_icoord= self.indices
        subdiv.gl_uvcoord=self.nuvs.flatten()
        subdiv.fverts=np.reshape(self.indices, (icount//3,3))
        subdiv.n_fverts = icount//3
        subdiv.overflow = overflowtable
        subdiv.calcNormals()
        subdiv.min_index = None
        m.passed("normals calculated, done")
        return(subdiv)

