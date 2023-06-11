
import numpy as np
from OpenGL import GL as gl
from PySide6.QtGui import QVector3D, QMatrix4x4

from PySide6.QtOpenGL import (QOpenGLBuffer, QOpenGLShader,
                              QOpenGLShaderProgram, QOpenGLTexture)

class OpenGlBuffers():
    def __init__(self):
        self.vert_pos_buffer = None
        self.normal_buffer = None
        self.tex_coord_buffer = None
        self.amount_of_vertices = 0

    def VertexBuffer(self, pos, amount):
        binpos = np.array(pos, dtype=np.float32)
        vbuffer = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        vbuffer.create()
        vbuffer.bind()
        vbuffer.setUsagePattern(QOpenGLBuffer.DynamicDraw)
        vbuffer.allocate(binpos, len(pos) * 4)
        self.vert_pos_buffer = vbuffer
        self.amount_of_vertices = amount

    def NormalBuffer(self, pos):
        binpos = np.array(pos, dtype=np.float32)
        vbuffer = QOpenGLBuffer()
        vbuffer.create()
        vbuffer.bind()
        vbuffer.allocate(binpos, len(pos) * 4)
        self.normal_buffer = vbuffer

    def TexCoordBuffer(self, pos):
        binpos = np.array(pos, dtype=np.float32)
        vbuffer = QOpenGLBuffer()
        vbuffer.create()
        vbuffer.bind()
        vbuffer.allocate(binpos, len(pos) * 4)
        self.tex_coord_buffer = vbuffer

class Object3D:
    def __init__(self, vert_buffers, locations, texture, pos):
        self.position = QVector3D(0, 0, 0)
        self.rotation = QVector3D(0, 0, 0)
        self.scale = QVector3D(1, 1, 1)
        self.mvp_matrix = QMatrix4x4()
        self.model_matrix = QMatrix4x4()
        self.normal_matrix = QMatrix4x4()

        self.vert_pos_buffer = vert_buffers.vert_pos_buffer
        self.normal_buffer = vert_buffers.normal_buffer
        self.tex_coord_buffer = vert_buffers.tex_coord_buffer
        self.amount_of_vertices = vert_buffers.amount_of_vertices

        self.mvp_matrix_location = locations.mvp_matrix_location
        self.model_matrix_location = locations.model_matrix_location
        self.normal_matrix_location = locations.normal_matrix_location

        self.texture = texture

        self.position = pos

    def draw(self, program, proj_view_matrix):
        program.bind()

        self.vert_pos_buffer.bind()
        program.setAttributeBuffer(0, gl.GL_FLOAT, 0, 3)
        program.enableAttributeArray(0)

        self.normal_buffer.bind()
        program.setAttributeBuffer(1, gl.GL_FLOAT, 0, 3)
        program.enableAttributeArray(1)

        self.tex_coord_buffer.bind()
        program.setAttributeBuffer(2, gl.GL_FLOAT, 0, 2)
        program.enableAttributeArray(2)


        self.model_matrix.setToIdentity()
        self.model_matrix.translate(self.position)
        self.model_matrix.scale(self.scale)
        self.mvp_matrix = proj_view_matrix * self.model_matrix

        self.normal_matrix = self.model_matrix.inverted()
        self.normal_matrix = self.normal_matrix[0].transposed()

        program.bind()
        program.setUniformValue(self.mvp_matrix_location, self.mvp_matrix)
        program.setUniformValue(self.model_matrix_location, self.model_matrix)
        program.setUniformValue(self.normal_matrix_location, self.normal_matrix)

        self.texture.bind()

        gl.glDrawArrays(gl.GL_TRIANGLES, 0, self.amount_of_vertices)


