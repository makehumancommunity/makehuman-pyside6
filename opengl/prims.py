from opengl.buffers import OpenGlBuffers, RenderedLines

from PySide6.QtGui import QVector3D

import numpy as np

class LineElements:
    def __init__(self, name, pos):
        self.name = name
        self.lines = None
        coord = np.asarray(pos, dtype=np.float32)
        self.gl_coord = coord.flatten()

        #self.icoord = np.arange(len(coord))
        self.icoord = np.arange(len(coord)*2)  # ?! TODO

        self.glbuffer = OpenGlBuffers()
        self.glbuffer.VertexBuffer(self.gl_coord)

    def create(self, context, shaders):
        self.lines = RenderedLines(context, self.icoord, self.name, self.glbuffer, shaders, pos=QVector3D(0, 0, 0))

    def draw(self, shaderprog, proj_view_matrix):
        if self.lines:
            self.lines.draw(shaderprog, proj_view_matrix)



