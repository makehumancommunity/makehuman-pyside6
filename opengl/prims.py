from opengl.buffers import OpenGlBuffers, RenderedLines, RenderedObject

from PySide6.QtGui import QVector3D
import numpy as np
import os

from obj3d.object3d import object3d

class LineElements:
    """
    create geometry for gdrawelements
    array of positions, array of colors or one color to be repeated
    """
    def __init__(self, context, shader, name, pos, cols):
        self.name = name
        self.lines = None
        self.glfunc =  context.functions()
        self.shader = shader
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

    def isVisible(self):
        return self.visible

    def setVisible(self, status):
        self.visible = status

    def create(self, width=1.0):
        self.width = width
        self.lines = RenderedLines(self.glfunc, self.shader, self.icoord, self.name, self.glbuffer, pos=QVector3D(0, 0, 0))

    def newGeometry(self, pos):
        self.gl_coord[:] = np.asarray(pos, dtype=np.float32).flatten()
        self.glbuffer.Tweak()

    def draw(self, proj_view_matrix):
        if self.lines and self.visible:
            self.glfunc.glLineWidth(self.width)
            self.lines.draw(proj_view_matrix)

    def delete(self):
        if self.lines:
            self.lines.delete()

class CoordinateSystem(LineElements):
    def __init__(self, context, shader, name, size, width=2.0):
        super().__init__(context, shader, name,
                [[ -size, 0.0, 0.0],  [ size, 0.0, 0.0],  [ 0.0, -size, 0.0], [ 0.0, size, 0.0], [ 0.0, 0.0, -size], [ 0.0, 0.0, size]],
                [[ 1.0, 0.0, 0.0],  [ 1.0, 0.0, 0.0],  [ 0.0, 1.0, 0.0], [ 0.0, 1.0, 0.0], [ 0.0, 0.0, 1.0], [ 0.0, 0.0, 1.0]])
        self.create(width)

class Grid(LineElements):
    def __init__(self, context, shader, name, size, ground, direction):
        lines = []
        cols = []
        self.border = int(size)
        lines = self.setGrid(ground, direction)
        # add colors one time
        #
        if direction == "xy":
            for i in range(-self.border, self.border+1):
                # xy-plane
                cols.extend ([[0.0, 0.0, 0.4], [0.0, 0.0, 0.4], [0.0, 0.0, 0.4], [0.0, 0.0, 0.4]])
        elif direction == "yz":
            for i in range(-self.border, self.border+1):
                # yz-plane
                cols.extend ([[0.4, 0.0, 0.0], [0.4, 0.0, 0.0], [0.4, 0.0, 0.0], [0.4, 0.0, 0.0]])
        else:
            for i in range(-self.border, self.border+1):
                # xz-plane
                cols.extend ([[0.0, 0.4, 0.0], [0.0, 0.4, 0.0], [0.0, 0.4, 0.0], [0.0, 0.4, 0.0]])

        super().__init__(context, shader, name, lines, cols)
        self.create()

    def setGrid(self, ground, direction):
        size = float(self.border)
        lines = []
        if direction == "xy":
            for i in range(-self.border, self.border+1):
                # xy-plane
                lines.extend ([[ -size, float(i), 0.0],  [ size, float(i), 0.0], [ float(i), -size, 0.0],  [ float(i), size, 0.0]])
        elif direction == "yz":
            for i in range(-self.border, self.border+1):
                # yz-plane
                lines.extend ([[ 0.0, float(i), -size],  [ 0.0, float(i), size], [0.0, -size, float(i)],  [ 0.0, size, float(i)]])

        else:
            for i in range(-self.border, self.border+1):
                # xz-plane
                lines.extend ([[ float(i), ground, -size ],  [ float(i), ground, size], [-size, ground, float(i)],  [size, ground, float(i)]])
        return (lines)

    def newGeometry(self,ground, direction):
        self.setGrid(ground, direction)
        super().newGeometry(self.setGrid(ground, direction))

class BoneList(LineElements):
    def __init__(self, context, shader, name, skeleton, col):
        self.skeleton = skeleton
        lines = []
        for bone in skeleton.bones:
            lines.extend ([skeleton.bones[bone].headPos, skeleton.bones[bone].tailPos])
        super().__init__(context, shader, name, lines, col)
        self.create(width=3.0)

    def newGeometry(self,posed=True):
        skeleton = self.skeleton
        lines = []
        if posed:
            for bone in skeleton.bones:
                lines.extend ([skeleton.bones[bone].poseheadPos, skeleton.bones[bone].posetailPos])
        else:
            for bone in skeleton.bones:
                lines.extend ([skeleton.bones[bone].headPos, skeleton.bones[bone].tailPos])
        super().newGeometry(lines)


class VisLights():
    """
    should create symbolic lamps
    """
    def __init__(self, parent, light):
        self.parent = parent
        self.glob =  parent.glob
        self.light = light
        self.lampobj =  object3d(self.glob, None, "system")
        self.obj = []

    def setup(self):
        lampfile = os.path.join(self.glob.env.path_sysdata, "shaders", "meshes", "lampsymbol.obj")
        (success, text) =self.lampobj.load(lampfile)

        if not success:
            self.glob.env.logLine(1, text)
            return False

        glbuffer = OpenGlBuffers()
        glbuffer.GetBuffers(self.lampobj.gl_coord, self.lampobj.gl_norm, self.lampobj.gl_uvcoord)
        boundingbox = self.lampobj.boundingBox()

        for light in self.light.lights:
            l = RenderedObject(self.parent, self.lampobj, boundingbox, glbuffer, pos=light["pos"])
            self.obj.append(l)
        return True

    def draw(self, proj_view_matrix):
        for i, light in enumerate(self.light.lights):
            self.obj[i].setPosition(light["pos"])
            self.obj[i].setTexture(self.parent.white)
            self.obj[i].draw(proj_view_matrix, self.light, False)


