import numpy as np

class object3d:
    def __init__(self):
 
        self.name = None    # will contain object name derived from loaded file
        self.prim = 0       # will contain number of vertices per face (primitive), either 3 or 4
        self.coord = []     # will contain positions of vertices, array of float32 for openGL
        self.fvert = []     # will contain vertices per face, [verts, prim] array of uint32 fpr openGL (prim = 3 or 4)


    def __str__(self):
        return (self.name + ": Object3d with " + str(self.prim) + " vertices per face")

    def setName(self, name):
        if name is None:
            self.name = "generic"
        else:
            self.name = name

    def createGLVertPos(self, pos):
        self.coord = np.asarray(pos, dtype=np.float32)        # positions converted to array of floats

    def createGLFaces(self, pos, prim):
        self.prim = prim
        nfaces = len(pos)
        self.fvert = np.empty((nfaces, self.prim), dtype=np.uint32)

