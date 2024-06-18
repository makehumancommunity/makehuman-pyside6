import time
import numpy as np
from PySide6.QtGui import QVector3D, QMatrix4x4, QImage

from PySide6.QtOpenGL import (QOpenGLBuffer, QOpenGLShader,
                              QOpenGLShaderProgram, QOpenGLTexture)

# Constants from OpenGL GL_TRIANGLES, GL_FLOAT
# 

from OpenGL import GL as gl

class OpenGlBuffers():
    def __init__(self):
        self.vert_pos_buffer = None
        self.normal_buffer = None
        self.tex_coord_buffer = None
        self.memory_pos = None
        self.len_memory = 0

    def VertexBuffer(self, pos):
        vbuffer = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        vbuffer.create()
        vbuffer.bind()
        vbuffer.setUsagePattern(QOpenGLBuffer.DynamicDraw)
        self.len_memory = len(pos) * 4
        self.memory_pos = pos
        vbuffer.allocate(pos, self.len_memory)
        self.vert_pos_buffer = vbuffer

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

    def GetBuffers(self, pos, norm, tpos):
        self.VertexBuffer(pos)
        self.NormalBuffer(norm)
        self.TexCoordBuffer(tpos)

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

class RenderedObject:
    def __init__(self, context, getindex, name, z_depth, glbuffers, shaders, texture, pos):
        self.context = context
        self.z_depth = z_depth
        self.name = name
        self.getindex = getindex
        self.position = QVector3D(0, 0, 0)
        self.rotation = QVector3D(0, 0, 0)
        self.scale = QVector3D(1, 1, 1)
        self.mvp_matrix = QMatrix4x4()
        self.model_matrix = QMatrix4x4()
        self.normal_matrix = QMatrix4x4()
        self.glbuffers = glbuffers

        self.vert_pos_buffer = glbuffers.vert_pos_buffer
        self.normal_buffer = glbuffers.normal_buffer
        self.tex_coord_buffer = glbuffers.tex_coord_buffer

        self.mvp_matrix_location = shaders.uniforms["uMvpMatrix" ]
        self.model_matrix_location = shaders.uniforms["uModelMatrix"]
        self.normal_matrix_location = shaders.uniforms["uNormalMatrix"]

        self.texture = texture

        self.position = pos

    def __str__(self):
        return("GL Object " + str(self.name))

    def delete(self):
        self.glbuffers.Delete()

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
        indices = self.getindex()
        functions.glDrawElements(gl.GL_TRIANGLES, len(indices), gl.GL_UNSIGNED_INT, indices)

class RenderedLines:
    def __init__(self, context, indices, name, glbuffers, shaders, pos):
        self.context = context
        self.name = name
        self.position = QVector3D(0, 0, 0)
        self.rotation = QVector3D(0, 0, 0)
        self.scale = QVector3D(1, 1, 1)
        self.mvp_matrix = QMatrix4x4()
        self.model_matrix = QMatrix4x4()
        self.normal_matrix = QMatrix4x4()
        self.glbuffers = glbuffers
        self.indices = indices

        self.vert_pos_buffer = glbuffers.vert_pos_buffer
        self.color_buffer = glbuffers.normal_buffer
        self.mvp_matrix_location = shaders.uniforms["uMvpMatrix" ]
        self.model_matrix_location = shaders.uniforms["uModelMatrix"]

        self.position = pos

    def __str__(self):
        return("GL Lines " + str(self.name))

    def delete(self):
        self.glbuffers.Delete()

    def draw(self, shaderprog, proj_view_matrix):
        """
        :param shaderprog: QOpenGLShaderProgram
        """
        shaderprog.bind()
        functions = self.context.functions()

        # VAO, bind the position-buffer, color-buffer and texture-coordinates to attribute 0, 1
        # these are the values changed per vertex
        #
        self.vert_pos_buffer.bind()
        shaderprog.setAttributeBuffer(0, gl.GL_FLOAT, 0, 3)     # OpenGL glVertexAttribPointer
        shaderprog.enableAttributeArray(0)                      # OpenGL glEnableVertexAttribArray

        self.color_buffer.bind()
        shaderprog.setAttributeBuffer(1, gl.GL_FLOAT, 0, 3)
        shaderprog.enableAttributeArray(1)

        self.model_matrix.setToIdentity()
        self.model_matrix.translate(self.position)
        self.model_matrix.scale(self.scale)
        self.mvp_matrix = proj_view_matrix * self.model_matrix

        # now set uMvpMatrix, uModelMatrix

        shaderprog.bind()
        shaderprog.setUniformValue(self.mvp_matrix_location, self.mvp_matrix)
        shaderprog.setUniformValue(self.model_matrix_location, self.model_matrix)

        indices = self.indices
        functions.glDrawElements(gl.GL_LINES, len(indices), gl.GL_UNSIGNED_INT, indices)


class PixelBuffer:
    """
    looks like the pixelbuffer functionality can only be reached by using classical gl-Functions
    still not okay. 
    """
    def __init__(self, glob, view):
        self.glob = glob
        self.view = view
        self.framebuffer = None
        self.colorbuffer = None
        self.depthbuffer = None
        self.width = 0
        self.height = 0
        self.oldheight = 0
        self.oldwidth = 0

    # https://stackoverflow.com/questions/60800538/python-opengl-how-to-render-off-screen-correctly
    # https://learnopengl.com/Advanced-OpenGL/Framebuffers
    def getBuffer(self, width, height):
        self.width = width
        self.height = height
        self.oldheight = self.view.window_height
        self.oldwidth = self.view.window_width
        functions = self.view.context().functions()

        # frame
        self.framebuffer = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.framebuffer)

        # color
        self.colorbuffer = gl.glGenRenderbuffers(1)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.colorbuffer)
        functions.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_RGBA, width, height)
        functions.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_RENDERBUFFER, self.colorbuffer)

        # depth
        self.depthbuffer = gl.glGenRenderbuffers(1)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.depthbuffer)
        functions.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT, width, height)
        functions.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_RENDERBUFFER, self.depthbuffer)
        print ("Frame / Color /Depth = ", self.framebuffer, self.colorbuffer, self.depthbuffer)

        status = functions.glCheckFramebufferStatus (gl.GL_FRAMEBUFFER)
        if status != gl.GL_FRAMEBUFFER_COMPLETE:
            print ("Status is " + str(status))

        self.view.resizeGL(width, height)

        gl.glPushAttrib(gl.GL_VIEWPORT_BIT)

        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        c = self.view.light.glclearcolor
        gl.glClearColor(c.x(), c.y(), c.z(), c.w())
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        proj_view_matrix = self.view.camera.getProjViewMatrix()
        baseClass = self.glob.baseClass
        start = 1 if baseClass.proxy is True else 0
        for obj in self.view.objects[start:]:
            obj.draw(self.view.mh_shaders._shaders[0], proj_view_matrix)


    def saveBuffer(self, path):
        gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT0)
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT, 1)
        data = gl.glReadPixels (0, 0, self.width, self.height, gl.GL_RGB,  gl.GL_UNSIGNED_BYTE)
        image = QImage(self.width, self.height, QImage.Format_RGB888)
        image.fromData(data)
        image.mirrored_inplace(False, True)
        image.save(path, "PNG", -1)

    def releaseBuffer(self):
        functions = self.view.context().functions()
        if self.framebuffer is not None:
            gl.glDeleteFramebuffers(1, np.array([self.framebuffer]))
        if self.colorbuffer is not None:
            gl.glDeleteRenderbuffers(1, np.array([self.colorbuffer]))
        if self.depthbuffer is not None:
            gl.glDeleteRenderbuffers(1, np.array([self.depthbuffer]))

        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glPopAttrib()
        #
        # still not clear ... without glDisable I get a black screen
        #
        functions.glDisable(gl.GL_DEPTH_TEST)
        self.view.resizeGL(self.oldwidth, self.oldheight)
