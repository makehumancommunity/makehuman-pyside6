import numpy as np 
class object3d:
    def __init__(self):
 
        self.name = None    # will contain object name derived from loaded file
        self.grpNames = []  # order list of groupnames

        self.prim    = 0    # will contain number of vertices per face (primitive), either 3 or 4
        self.maxAttachedFaces  = 0 # will contain "maxpole"
        self.n_verts = 0    # number of vertices
        self.n_faces = 0    # number of uv-faces
        self.n_fuvs  = 0    # number of faces
        self.n_groups= 0    # number of groups

        self.coord = []     # will contain positions of vertices, array of float32 for openGL
        self.fvert = []     # will contain vertices per face, [verts, prim] array of uint32 fpr openGL (prim = 3 or 4)
        self.fuvs  = None   # will contain UV buffer or will stay none
        self.group = []     # will contain pointer to group per face

    def __str__(self):
        return (self.name + ": Object3d with " + str(self.n_groups) + " group(s)\n" + 
                str(self.n_verts) + " vertices, " + str(self.n_faces) + " faces (" + str(self.prim) + " vertices per face), " + str(self.n_fuvs) + " uv-faces\nMaximum: " +
                str(self.maxAttachedFaces) +  " attached faces for one vertex.")

    def setName(self, name):
        if name is None:
            self.name = "generic"
        else:
            self.name = name

    def setGroupNames(self, names):
        self.grpNames = names
        self.n_groups = len(self.grpNames)

    def createGLVertPos(self, pos):
        self.n_verts = len(pos)
        self.coord = np.asarray(pos, dtype=np.float32)        # positions converted to array of floats

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
                n = x + len(groups[elem]["uv"])
                self.fuvs[x:n,] = groups[elem]["uv"]
                x = n
        self.calculateMaxAttachedFaces()


    def calculateMaxAttachedFaces(self):
        """
        this is the maxPole calculation (if needed)
        """
        attachedFaces = np.zeros(self.n_verts, dtype=np.uint8)
        for elem in self.fvert:
            for vert in elem:
                attachedFaces[vert] += 1

        self.maxAttachedFaces  = np.max(attachedFaces)
