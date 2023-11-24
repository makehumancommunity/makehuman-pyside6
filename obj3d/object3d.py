import numpy as np 
# from timeit import default_timer as timer

class object3d:
    def __init__(self, env, baseinfo ):
 
        self.env  = env     # needed for globals
        self.name = None    # will contain object name derived from loaded file
        self.grpNames = []  # order list of groupnames

        self.prim    = 0    # will contain number primitives (tris)
        self.maxAttachedFaces  = 0 # will contain "maxpole"
        self.n_origverts = 0 # number of vertices after loading
        self.n_verts = 0    # number of vertices
        self.n_faces = 0    # number of faces
        self.n_fuvs  = 0    # number of uv-faces
        self.n_groups= 0    # number of groups

        self.coord = []     # will contain positions of vertices, array of float32 for openGL
        self.uvs   = []     # will contain coordinates for uvs
        self.fuvs  = None   # will contain UV buffer or will stay none (TODO: is that needed?)
        self.group = []     # will contain pointer to group per face

        self.overflow = None # will contain a table for double used vertices [source, dest]

        self.gl_coord = []    # will contain flattened gl-Buffer (these are coordinates to be changed)
        self.gl_coord_o = []  # will contain a copy of unchanged positions
        self.gl_coord_w = []  # will contain a copy of unchanged positions (working mode with targets)
        self.gl_uvcoord = []  # will contain flattened gluv-Buffer
        self.gl_norm  = []    # will contain flattended normal buffer
        self.gl_fvert  = []   # will contain vertices per face, [verts, 3] array of uint32 for openGL > 2
        self.n_glverts = 0    # number of vertices for open gl
        self.n_glnorm  = 0    # number of normals for open gl
        if baseinfo is not None:
            self.visible = baseinfo["visible groups"]
        else:
            self.visible = None

    def __str__(self):
        return (self.name + ": Object3d with " + str(self.n_groups) + " group(s)\n" + 
                str(self.n_origverts) + " vertices, " + str(self.n_faces) + " faces (" +
                str(self.n_fuvs) + " uv-faces)\nOpenGL triangles: " +
                str(self.prim) + "\nOpenGL DrawElements: " + str(self.n_verts)) 
                #+ "\nMaximum attached faces for one vertex: " + str(self.maxAttachedFaces))

    def setName(self, name):
        if name is None:
            self.name = "generic"
        else:
            self.name = name

    def setGroupNames(self, names):
        self.grpNames = names
        self.n_groups = len(self.grpNames)

    def createGLVertPos(self, pos, uvs, overflow, orig):
        self.n_origverts = orig
        self.n_verts = len(pos)
        self.coord = np.asarray(pos, dtype=np.float32)      # positions converted to array of floats
        self.n_uvs = len(uvs)
        self.uvs = np.asarray(uvs, dtype=np.float32)        # positions converted to array of floats
        self.overflow = overflow


    def overflowCorrection(self, arr):
        """
        when the main part of the mesh is directly corrected, handle the overflow
        """
        for (source, dest) in self.overflow:
            s = source * 3
            d = dest * 3
            arr[d:d+3]   = arr[s:s+3]

    def calcNormals(self):
        """
        calculates face-normals and then vertex normals
        """
        self.gi_norm = np.zeros((self.n_verts, 3), dtype=np.float32)

        # set the face normals for each vertex to zero, set the counter to zero
        #
        fa_norm = np.zeros((self.n_verts, 3), dtype=np.float32)
        fa_cnt  = np.zeros(self.n_verts, dtype=np.uint32)

        # calculate face normal and summarize them with other (for each 3 verts per triangle)
        #
        for elem in self.gl_fvert:
            v = self.coord[elem]
            norm = np.cross(v[0] - v[1], v[1] - v[2])

            # done on flattened array it works like this
            #x = elem * 3
            #a = [ self.gl_coord[x][0] - self.gl_coord[x][1], self.gl_coord[x+1][0] - self.gl_coord[x+1][1], self.gl_coord[x+2][0] - self.gl_coord[x+2][1] ]
            #b = [ self.gl_coord[x][1] - self.gl_coord[x][2], self.gl_coord[x+1][1] - self.gl_coord[x+1][2], self.gl_coord[x+2][1] - self.gl_coord[x+2][2] ]
            #norm = np.cross(a, b)

            for i in range(2):
                fa_norm[elem[i]] += norm
                fa_cnt[elem[i]] += 1

        # because part of the faces belong to the overflow buffer add them as well
        #
        for (source, dest) in self.overflow:
            fa_norm[source] += fa_norm[dest]
            fa_cnt[source]  += fa_cnt[dest]

        # now divide by the number of edges and normalize length with np.linalg.norm
        #
        for i in range(0, self.n_origverts):
            if fa_cnt[i] != 0:
                norm = fa_norm[i] / fa_cnt[i]
                l = np.linalg.norm(norm)
                if l != 0.0:
                    self.gi_norm[i] = norm / np.linalg.norm(norm)
                else:
                    self.gi_norm[i] = norm

        # simply copy for the doubles in the end using overflow
        #
        for (source, dest) in self.overflow:
            self.gi_norm[dest] =  self.gi_norm[source]

        # flatten vector
        #
        self.gl_norm = self.gi_norm.flatten()

    def createGLFaces(self, nfaces, ufaces, prim, groups):
        self.prim = prim
        self.n_faces = nfaces
        self.n_fuvs =  ufaces
        self.group = np.zeros(nfaces, dtype=np.uint16)

        self.gl_fvert = np.zeros((self.prim, 3), dtype=np.uint32)
        # fill faces and group buffer
        # ( array of numbers per face determining the group-number )

        cnt = 0
        for num, elem in enumerate (self.grpNames):
            if self.visible is not None and elem not in self.visible:
                continue
            faces = groups[elem]["v"]
            for face in faces:
                l = len(face)
                self.gl_fvert[cnt] = face[:3]
                cnt += 1
                # rest for quad and n-gons 
                if l > 3:
                    i=2
                    while i < l-1:
                        self.gl_fvert[cnt] = [face[0], face[i], face[i+1]]
                        cnt += 1
                        i += 1

        # resize to visible groups only TODO not sure if it should stay like this
        #
        self.gl_fvert.resize((cnt, 3), refcheck=False)
        self.n_glverts = cnt * 3
        self.gl_icoord = np.zeros(self.n_glverts, dtype=np.uint32)
        cnt = 0
        for face in self.gl_fvert:
            for vert in face:
                self.gl_icoord[cnt] = vert
                cnt += 1
        self.gl_coord = self.coord.flatten()
        self.gl_coord_o = self.gl_coord.copy()  # create a copy for original values
        self.gl_coord_w = self.gl_coord.copy()  # create another one for working

        if self.n_fuvs > 0:
            self.gl_uvcoord = self.uvs.flatten()

        #del self.uvs           # save memory
        #del self.fvert

        #self.calculateMaxAttachedFaces()
        self.calcNormals()

    def getInitialCopyForSlider(self, factor, targetlower, targetupper):
        """
        called when starting work with one slider, a copy without the value
        of this slider is created.
        """
        if factor == 0.0:
            self.gl_coord_w[:] = self.gl_coord[:]
        else:
            if factor < 0.0:
                if targetlower is None:
                    self.gl_coord_w[:] = self.gl_coord[:]
                    return
                verts = targetlower.verts
                data  = targetlower.data
                factor = -factor
            elif factor > 0.0:
                verts = targetupper.verts
                data  = targetupper.data
            for i in range(0, len(verts)):
                x = verts[i] * 3
                self.gl_coord_w[x]   = self.gl_coord[x]   - factor * data[i][0]
                self.gl_coord_w[x+1] = self.gl_coord[x+1] - factor * data[i][1]
                self.gl_coord_w[x+2] = self.gl_coord[x+2] - factor * data[i][2]

        self.overflowCorrection(self.gl_coord_w)
        # self.calcNormals()

    def updateByTarget(self, factor, targetlower, targetupper):
        """
        updates the mesh when slider is moved
        """
        if factor == 0.0:
            self.gl_coord[:] = self.gl_coord_w[:]
            return

        if factor < 0.0:
            if targetlower is None:
                return
            verts = targetlower.verts
            data  = targetlower.data
            factor = -factor
        elif factor > 0.0:
            verts = targetupper.verts
            data  = targetupper.data

        for i in range(0, len(verts)):
            x = verts[i] * 3
            self.gl_coord[x]   = self.gl_coord_w[x]   + factor * data[i][0]
            self.gl_coord[x+1] = self.gl_coord_w[x+1] + factor * data[i][1]
            self.gl_coord[x+2] = self.gl_coord_w[x+2] + factor * data[i][2]

        # do not forget the overflow vertices
        #
        self.overflowCorrection(self.gl_coord)


    def approxByTarget(self, asset, base):
        """
        updates the mesh when slider is moved, approximation
        """

        # TODO: only handles simple case
        i = 0
        for vnum in asset.ref_vIdxs:
            x =  vnum[0] * 3
            self.gl_coord[i] = base.gl_coord[x]
            self.gl_coord[i+1] = base.gl_coord[x+1]
            self.gl_coord[i+2] = base.gl_coord[x+2]
            i += 3

        # do not forget the overflow vertices
        #
        self.overflowCorrection(self.gl_coord)

    def recalculateDimension(self):

        a = self.gl_coord.reshape((int(len(self.gl_coord)/3),3))
        self.minimum_axis = np.min(a, axis=0)
        self.maximum_axis = np.max(a, axis=0)

        print ("Dimension left/right: " + str(self.minimum_axis[0]) + " / " + str(self.maximum_axis[0]))
        print ("Dimension back/front: " + str(self.minimum_axis[2]) + " / " + str(self.maximum_axis[2]))
        print ("Dimension bottom/top: " + str(self.minimum_axis[1]) + " / " + str(self.maximum_axis[1]))

    def getCenter(self):
        return ((self.maximum_axis+self.minimum_axis) / 2)

    """
    def calculateMaxAttachedFaces(self):
        attachedFaces = np.zeros(self.n_verts, dtype=np.uint8)
        for elem in faceverts:
            for vert in elem:
                attachedFaces[vert] += 1

        self.maxAttachedFaces  = np.max(attachedFaces)
    """
    def __del__(self):
        self.env.logLine (4, " -- delete object3d: " + str(self.name))
