
import numpy as np
from PySide6.QtGui import QVector3D, QMatrix4x4

from PySide6.QtOpenGL import (QOpenGLBuffer, QOpenGLShader,
                              QOpenGLShaderProgram, QOpenGLTexture)

# Constants from OpenGL GL_TRIANGLES, GL_FLOAT
# 

from OpenGL import GL as gl
class OpenGlBuffers():
    def __init__(self):
        self.vert_pos_buffer = None
        self.indices = None
        self.normal_buffer = None
        self.tex_coord_buffer = None
        self.amount_of_vertices = 0
        self.memory_pos = None
        self.len_memory = 0

    def VertexBuffer(self, pos, icoord, amount):
        vbuffer = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        vbuffer.create()
        vbuffer.bind()
        vbuffer.setUsagePattern(QOpenGLBuffer.DynamicDraw)
        self.len_memory = len(pos) * 4
        self.memory_pos = pos
        vbuffer.allocate(pos, self.len_memory)
        self.vert_pos_buffer = vbuffer

        self.indices = icoord
        self.amount_of_vertices = amount

    def NormalBuffer(self, pos):
        vbuffer = QOpenGLBuffer()
        vbuffer.create()
        vbuffer.bind()
        vbuffer.allocate(pos, len(pos) * 4)
        self.normal_buffer = vbuffer

    def TexCoordBuffer(self, pos):
        vbuffer = QOpenGLBuffer()
        vbuffer.create()
        vbuffer.bind()
        vbuffer.allocate(pos, len(pos) * 4)
        self.tex_coord_buffer = vbuffer

    def Tweak(self):
        self.vert_pos_buffer.bind()
        self.vert_pos_buffer.write(0,self.memory_pos, self.len_memory )

    def Delete(self):
        if self.vert_pos_buffer is not None:
            self.vert_pos_buffer.destroy()
        if self.normal_buffer is not None:
            self.normal_buffer.destroy()
        if self.tex_coord_buffer is not None:
            self.tex_coord_buffer.destroy()
        self.amount_of_vertices = 0

class RenderedObject:
    def __init__(self, context, z_depth, vert_buffers, shaders, texture, pos):
        self.context = context
        self.z_depth = z_depth
        self.position = QVector3D(0, 0, 0)
        self.rotation = QVector3D(0, 0, 0)
        self.scale = QVector3D(1, 1, 1)
        self.mvp_matrix = QMatrix4x4()
        self.model_matrix = QMatrix4x4()
        self.normal_matrix = QMatrix4x4()
        self.vert_buffers = vert_buffers

        self.vert_pos_buffer = vert_buffers.vert_pos_buffer
        self.indices = vert_buffers.indices
        self.normal_buffer = vert_buffers.normal_buffer
        self.tex_coord_buffer = vert_buffers.tex_coord_buffer
        self.amount_of_vertices = vert_buffers.amount_of_vertices

        self.mvp_matrix_location = shaders.uniforms["uMvpMatrix" ]
        self.model_matrix_location = shaders.uniforms["uModelMatrix"]
        self.normal_matrix_location = shaders.uniforms["uNormalMatrix"]

        self.texture = texture

        self.position = pos

    def delete(self):
        self.vert_buffers.Delete()

    def setTexture(self, texture):
        functions = self.context.functions()
        functions.glActiveTexture(gl.GL_TEXTURE0)
        self.texture = texture
        self.texture.bind()

    def draw(self, shaderprog, proj_view_matrix):
        """
        :param shaderprog: QOpenGLShaderProgram
        """
        shaderprog.bind()
        functions = self.context.functions()

        # VAO, bind the position-buffer, normal-buffer and texture-coordinates to attribute 0, 1, 2
        # these are the values changed per vertex
        #
        self.vert_pos_buffer.bind()
        shaderprog.setAttributeBuffer(0, gl.GL_FLOAT, 0, 3)     # OpenGL glVertexAttribPointer
        shaderprog.enableAttributeArray(0)                      # OpenGL glEnableVertexAttribArray

        self.normal_buffer.bind()
        shaderprog.setAttributeBuffer(1, gl.GL_FLOAT, 0, 3)
        shaderprog.enableAttributeArray(1)

        self.tex_coord_buffer.bind()
        shaderprog.setAttributeBuffer(2, gl.GL_FLOAT, 0, 2)
        shaderprog.enableAttributeArray(2)

        self.model_matrix.setToIdentity()
        self.model_matrix.translate(self.position)
        self.model_matrix.scale(self.scale)
        self.mvp_matrix = proj_view_matrix * self.model_matrix

        self.normal_matrix = self.model_matrix.inverted()
        self.normal_matrix = self.normal_matrix[0].transposed()

        # now set uMvpMatrix, uModelMatrix, uNormalMatrix

        shaderprog.bind()
        shaderprog.setUniformValue(self.mvp_matrix_location, self.mvp_matrix)
        shaderprog.setUniformValue(self.model_matrix_location, self.model_matrix)
        shaderprog.setUniformValue(self.normal_matrix_location, self.normal_matrix)
        
        functions.glActiveTexture(gl.GL_TEXTURE0)
        self.texture.bind()

        functions.glDrawElements(gl.GL_TRIANGLES, self.amount_of_vertices, gl.GL_UNSIGNED_INT, self.indices)


