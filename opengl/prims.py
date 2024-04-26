from opengl.buffers import OpenGlBuffers, RenderedLines

from PySide6.QtGui import QVector3D

import numpy as np

class LineElements:
    def __init__(self, name, pos, cols):
        self.name = name
        self.lines = None
        coord = np.asarray(pos, dtype=np.float32)
        self.gl_coord = coord.flatten()
        cols = np.asarray(cols, dtype=np.float32)
        self.gl_cols = cols.flatten()
        self.icoord = np.arange(len(coord), dtype=np.uint32)

        self.glbuffer = OpenGlBuffers()
        self.glbuffer.VertexBuffer(self.gl_coord)
        self.glbuffer.NormalBuffer(self.gl_cols)   # used for color

    def create(self, context, shaders):
        self.lines = RenderedLines(context, self.icoord, self.name, self.glbuffer, shaders, pos=QVector3D(0, 0, 0))

    def draw(self, shaderprog, proj_view_matrix):
        if self.lines:
            self.lines.draw(shaderprog, proj_view_matrix)


class CoordinateSystem(LineElements):
    def __init__(self, size, context, shaders):
        super().__init__("coordinate-sys",
                [[ -size, 0.0, 0.0],  [ size, 0.0, 0.0],  [ 0.0, -size, 0.0], [ 0.0, size, 0.0], [ 0.0, 0.0, -size], [ 0.0, 0.0, size]],
                [[ 1.0, 0.0, 0.0],  [ 1.0, 0.0, 0.0],  [ 0.0, 1.0, 0.0], [ 0.0, 1.0, 0.0], [ 0.0, 0.0, 1.0], [ 0.0, 0.0, 1.0]])
        self.create(context, shaders)

class Grid(LineElements):
    def __init__(self, size, context, shaders):
        lines = []
        cols = []
        for i in range(1, 10):
            lines.extend ([[ -size, float(i), 0.0],  [ size, float(i), 0.0], [ -size, -float(i), 0.0],  [ size, -float(i), 0.0]])
            cols.extend ([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
            lines.extend ([[ float(i), -size, 0.0],  [ float(i), size, 0.0], [ -float(i), -size, 0.0],  [ -float(i), size, 0.0]])
            cols.extend ([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
        super().__init__("grid", lines, cols)
        self.create(context, shaders)
