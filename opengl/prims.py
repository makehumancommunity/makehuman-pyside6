from opengl.buffers import OpenGlBuffers, RenderedLines

from PySide6.QtGui import QVector3D

import numpy as np

class LineElements:
    """
    create geometry for gdrawelements
    array of positions, array of colors or one color to be repeated
    """
    def __init__(self, name, pos, cols):
        self.name = name
        self.lines = None
        self.glfunc = None
        self.width = 1.0
        self.visible = False
        self.gl_coord = np.asarray(pos, dtype=np.float32).flatten()
        if len(cols) > 0 and isinstance(cols[0], list):
            self.gl_cols = np.asarray(cols, dtype=np.float32).flatten()
        else:
            self.gl_cols = np.tile(np.asarray(cols, dtype=np.float32), len(pos))

        self.icoord = np.arange(len(pos), dtype=np.uint32)

        self.glbuffer = OpenGlBuffers()
        self.glbuffer.VertexBuffer(self.gl_coord)
        self.glbuffer.NormalBuffer(self.gl_cols)   # used for color

    def setVisible(self, status):
        self.visible = status

    def create(self, context, shaders, width=1.0):
        self.glfunc = context.functions()
        self.width = width
        self.lines = RenderedLines(context, self.icoord, self.name, self.glbuffer, shaders, pos=QVector3D(0, 0, 0))

    def newGeometry(self, pos):
        self.gl_coord[:] = np.asarray(pos, dtype=np.float32).flatten()
        self.glbuffer.Tweak()

    def draw(self, shaderprog, proj_view_matrix):
        if self.lines and self.visible:
            self.glfunc.glLineWidth(self.width)
            self.lines.draw(shaderprog, proj_view_matrix)

    def delete(self):
        if self.lines:
            self.lines.delete()

class CoordinateSystem(LineElements):
    def __init__(self, name, size, context, shaders, width=2.0):
        super().__init__(name,
                [[ -size, 0.0, 0.0],  [ size, 0.0, 0.0],  [ 0.0, -size, 0.0], [ 0.0, size, 0.0], [ 0.0, 0.0, -size], [ 0.0, 0.0, size]],
                [[ 1.0, 0.0, 0.0],  [ 1.0, 0.0, 0.0],  [ 0.0, 1.0, 0.0], [ 0.0, 1.0, 0.0], [ 0.0, 0.0, 1.0], [ 0.0, 0.0, 1.0]])
        self.create(context, shaders, width)

class Grid(LineElements):
    def __init__(self, name, size, context, shaders):
        lines = []
        for i in range(1, 10):
            lines.extend ([[ -size, float(i), 0.0],  [ size, float(i), 0.0], [ -size, -float(i), 0.0],  [ size, -float(i), 0.0]])
            lines.extend ([[ float(i), -size, 0.0],  [ float(i), size, 0.0], [ -float(i), -size, 0.0],  [ -float(i), size, 0.0]])
        super().__init__(name, lines, [0.0, 0.0, 0.0])
        self.create(context, shaders)

class BoneList(LineElements):
    def __init__(self, name, skeleton, context, shaders):
        self.skeleton = skeleton
        lines = []
        for bone in skeleton.bones:
            lines.extend ([skeleton.bones[bone].headPos, skeleton.bones[bone].tailPos])
        super().__init__(name, lines, [1.0, 1.0, 1.0])
        self.create(context, shaders, width=3.0)

    def newGeometry(self):
        skeleton = self.skeleton
        lines = []
        for bone in skeleton.bones:
            lines.extend ([skeleton.bones[bone].headPos, skeleton.bones[bone].tailPos])
        super().newGeometry(lines)
