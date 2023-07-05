import numpy as np 

class object3d:
    def __init__(self):
 
        self.name = None    # will contain object name derived from loaded file
        self.grpNames = []  # order list of groupnames

        self.prim    = 0    # will contain number of vertices per face (primitive), either 3 or 4
        self.maxAttachedFaces  = 0 # will contain "maxpole"
        self.n_origverts = 0 # number of vertices after loading
        self.n_verts = 0    # number of vertices
        self.n_faces = 0    # number of faces
        self.n_fuvs  = 0    # number of uv-faces
        self.n_groups= 0    # number of groups

        self.coord = []     # will contain positions of vertices, array of float32 for openGL
        self.uvs   = []     # will contain coordinates for uvs
        self.fvert = []     # will contain vertices per face, [verts, prim] array of uint32 to keep Quads
        self.fuvs  = None   # will contain UV buffer or will stay none (TODO: is that needed?)
        self.group = []     # will contain pointer to group per face

        self.overflow = None # will contain a table for double used vertices

        self.gl_coord = []    # will contain flattened gl-Buffer
        self.gl_uvcoord = []  # will contain flattened gluv-Buffer
        self.gl_norm  = []    # will contain flattended normal buffer
        self.gl_fvert  = []   # will contain vertices per face, [verts, 3] array of uint32 for openGL > 2
        self.n_glfaces = 0    # number of faces for open gl
        self.n_glverts = 0    # number of vertices for open gl
        self.n_glnorm  = 0    # number of normals for open gl

    def __str__(self):
        return (self.name + ": Object3d with " + str(self.n_groups) + " group(s)\n" + 
                str(self.n_origverts) + " vertices, " + str(self.n_faces) + " faces (" +
                str(self.prim) + " vertices per face), " + str(self.n_fuvs) + " uv-faces\nOpenGL triangles: " +
                str(self.n_glfaces) + "\nOpenGL DrawElements: " + str(self.n_verts) + "\nMaximum attached faces for one vertex: " + str(self.maxAttachedFaces))

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

    def triangulateFaces(self):
        if self.prim == 3:
            self.gl_fvert  = self.fvert
            self.n_glfaces = self.n_faces

        else:
            self.n_glfaces = self.n_faces * 2
            self.gl_fvert = np.empty((self.n_glfaces, 3), dtype=np.uint32)
            cnt = 0
            for elem in self.fvert:
                self.gl_fvert[cnt] = elem[:3]
                cnt += 1
                self.gl_fvert[cnt] = [elem[0], elem[2], elem[3]]
                cnt += 1


        # now put elements in a row

        self.n_glverts = self.n_glfaces * 3
        self.gl_icoord = np.zeros(self.n_glverts, dtype=np.uint32)
        cnt = 0
        for face in self.gl_fvert:
            for vert in face:
                self.gl_icoord[cnt] = vert
                cnt += 1
        self.gl_coord = self.coord.flatten()

        if self.n_fuvs > 0:
            self.gl_uvcoord = self.uvs.flatten()

        del self.uvs           # save memory
        del self.fvert


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
            norm = fa_norm[i] / fa_cnt[i]
            self.gi_norm[i] = norm / np.linalg.norm(norm)

        # simply copy for the doubles in the end using overflow
        #
        for (source, dest) in self.overflow:
            self.gi_norm[dest] =  self.gi_norm[source]
        #
        # flatten vector
        #
        self.gl_norm = self.gi_norm.flatten()

    def createGLFaces(self, nfaces, ufaces, prim, groups):
        self.prim = prim
        self.n_faces = nfaces
        self.n_fuvs =  ufaces

        self.fvert = np.empty((nfaces, self.prim), dtype=np.uint32)
        self.group = np.zeros(nfaces, dtype=np.uint16)
        if ufaces > 0:
            self.fuvs = np.empty((ufaces, self.prim), dtype=np.uint32)

        # fill faces and group buffer
        # ( array of numbers per face determining the group-nummber )
        n = x = 0
        for num, elem in enumerate (self.grpNames):
            n = x + len(groups[elem]["v"])
            self.fvert[x:n,] = groups[elem]["v"]
            self.group[x:n] = num
            x = n

        # if uv-buffer fill the uv-buffer
        #
        if self.fuvs is not None:
            n = x = 0
            for num, elem in enumerate (self.grpNames):
                n = x + len(groups[elem]["v"])
                self.fuvs[x:n,] = groups[elem]["v"]
                x = n

        self.calculateMaxAttachedFaces()
        self.triangulateFaces()
        self.calcNormals()


    def calculateMaxAttachedFaces(self):
        """
        this is the maxPole calculation (if needed)
        """
        attachedFaces = np.zeros(self.n_verts, dtype=np.uint8)
        for elem in self.fvert:
            for vert in elem:
                attachedFaces[vert] += 1

        self.maxAttachedFaces  = np.max(attachedFaces)
