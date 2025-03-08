"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * OpenGlBuffers
    * RenderedObject
    * RenderedLines
    * RenderedSimple
    * PixelBuffer
"""
import time
import numpy as np
from PySide6.QtGui import QVector3D, QMatrix4x4, QImage
from PySide6.QtCore import QByteArray

from PySide6.QtOpenGL import (QOpenGLBuffer, QOpenGLShader,
                              QOpenGLShaderProgram, QOpenGLTexture)

from opengl.info import openGLReset

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

    def BindBuffersToShader(self, shader):
        """
        VAO, bind the position-buffer, normal-buffer and texture-coordinates to attribute 0, 1, 2
        must be done on each render cycle
        """
        self.vert_pos_buffer.bind()
        shader.setAttributeBuffer(0, gl.GL_FLOAT, 0, 3)     # OpenGL = glVertexAttribPointer
        shader.enableAttributeArray(0)                      # OpenGL = glEnableVertexAttribArray

        self.normal_buffer.bind()
        shader.setAttributeBuffer(1, gl.GL_FLOAT, 0, 3)
        shader.enableAttributeArray(1)
        
        # allow none textured objects (e.g. lines, they use normal buffer as color buffer and no texture)
        #
        if  self.tex_coord_buffer is not None:
            self.tex_coord_buffer.bind()
            shader.setAttributeBuffer(2, gl.GL_FLOAT, 0, 2)
            shader.enableAttributeArray(2)

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
    def __init__(self, parent, obj, boundingbox, glbuffers, pos):
        self.parent = parent
        self.glob = parent.glob
        self.context = parent.context()
        self.shaders = parent.mh_shaders

        self.env = self.glob.env
        self.texture = None
        self.litsphere = None
        self.aomap = None
        self.nomap = None
        self.mrmap = None
        self.emmap = None
        self.mefac = 0.0
        self.z_depth = obj.z_depth
        self.name = obj.filename
        self.boundingbox = boundingbox
        self.getindex = obj.getOpenGLIndex
        self.position = QVector3D(0, 0, 0)
        self.scale = QVector3D(1, 1, 1)
        self.y_rotation = 0.0
        self.mvp_matrix = QMatrix4x4()
        self.model_matrix = QMatrix4x4()
        self.normal_matrix = QMatrix4x4()
        self.glbuffers = glbuffers

        self.setMaterial(obj.material)

        self.position = pos

    def __str__(self):
        return("GL Object " + str(self.name))

    def delete(self):
        self.glbuffers.Delete()

    def setMaterial(self, material):
        """
        set shader and creates textures from material according to shader
        all shaders use a diffuse texture
        """
        self.material = material
        self.texture = self.material.loadDiffuse()

        if material.shader == "litsphere":
            self.shader = self.shaders.getShader("litsphere")
            self.litsphere = self.material.loadLitSphere()
        elif material.shader == "pbr":
            self.shader = self.shaders.getShader("pbr")
            self.aomap = self.material.loadAOMap(self.parent.white)
            self.mrmap = self.material.loadMRMap(self.parent.white)
            self.emmap = self.material.loadEMMap(self.parent.black)
            self.mefac = material.metallicFactor if hasattr(self, 'metallicRoughnessTexture') else 1.0 - material.metallicFactor

        elif material.shader == "normal":
            self.shader = self.shaders.getShader("normal")
            self.aomap = self.material.loadAOMap(self.parent.white)
            self.nomap = self.material.loadNOMap(self.parent.white)
            self.mrmap = self.material.loadMRMap(self.parent.white)
        elif material.shader == "toon":
            self.shader = self.shaders.getShader("toon")
        else:
            self.shader = self.shaders.getShader("phong3l")

    def setTexture(self, texture):
        # only used for colors
        self.texture = texture
    
    def setPosition(self, pos):
        self.position = pos

    def setYRotation(self, rot):
        self.y_rotation = rot

    def geomToShader(self, shader, proj_view_matrix, campos):
        """
        create geometry
        """
        self.mvp_matrix_location = shader.uniforms["uMvpMatrix" ]
        self.model_matrix_location = shader.uniforms["uModelMatrix"]
        self.normal_matrix_location = shader.uniforms["uNormalMatrix"]
        self.viewpos_location = shader.uniforms["viewPos"]

        shader.bind()

        self.glbuffers.BindBuffersToShader(shader)  # VAO etc.

        self.model_matrix.setToIdentity()
        self.model_matrix.translate(self.position)
        if self.y_rotation != 0.0:
            self.model_matrix.rotate(self.y_rotation, 0.0, 1.0, 0.0)
        self.model_matrix.scale(self.scale)
        self.mvp_matrix = proj_view_matrix * self.model_matrix

        self.normal_matrix = self.model_matrix.inverted()
        self.normal_matrix = self.normal_matrix[0].transposed()

        # now set uMvpMatrix, uModelMatrix, uNormalMatrix

        shader.setUniformValue(self.mvp_matrix_location, self.mvp_matrix)
        if self.model_matrix_location != -1:
            shader.setUniformValue(self.model_matrix_location, self.model_matrix)
        if self.normal_matrix_location != -1:
            shader.setUniformValue(self.normal_matrix_location, self.normal_matrix)
        if self.viewpos_location != -1:
            shader.setUniformValue(self.viewpos_location, campos)


    def draw(self, proj_view_matrix, campos, light, xrayed = False):
        """
        :param proj_view_matrix: matrix
        """
        shader = self.shaders.getShader("xray") if xrayed else self.shader
        self.geomToShader(shader, proj_view_matrix, campos)
        functions = self.context.functions()


        functions.glEnable(gl.GL_DEPTH_TEST)
        if self.material.pbrMetallicRoughness is not None:
            lightWeight = QVector3D(1.0 - self.material.pbrMetallicRoughness, light.lightWeight.y(), 0)
        else:
            lightWeight = QVector3D(0.5, light.lightWeight.y(), 0)
        shader.setUniformValue("lightWeight", lightWeight)

        # alphaCoverage demands samples buffers, so if these are not given
        # do not use alphaToCoverage, use BLEND instead

        alphaCover = self.material.alphaToCoverage and not self.env.noalphacover

        if self.material.transparent or xrayed:
            if alphaCover and not xrayed:
                functions.glEnable(gl.GL_MULTISAMPLE)
                functions.glEnable(gl.GL_SAMPLE_ALPHA_TO_COVERAGE)
                functions.glDisable(gl.GL_BLEND)
            else:
                functions.glEnable(gl.GL_BLEND)

            functions.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        else:
            functions.glBlendFunc(gl.GL_ONE, gl.GL_ZERO)

        if self.material.backfaceCull or xrayed:
            functions.glEnable(gl.GL_CULL_FACE)
        else:
            functions.glDisable(gl.GL_CULL_FACE)

        if not xrayed:
            functions.glUniform1i(shader.uniforms['Texture'], 0)
            functions.glActiveTexture(gl.GL_TEXTURE0)
            self.texture.bind()

            if self.material.shader == "litsphere":
                functions.glUniform1f(shader.uniforms['AdditiveShading'], self.material.sp_AdditiveShading)

                functions.glUniform1i(shader.uniforms['litsphereTexture'], 1)
                functions.glActiveTexture(gl.GL_TEXTURE1)
                self.litsphere.bind()

            elif self.material.shader == "pbr":
                functions.glUniform1f(shader.uniforms['AOMult'], self.material.aomapIntensity)

                functions.glUniform1i(shader.uniforms['AOTexture'], 1)
                functions.glActiveTexture(gl.GL_TEXTURE1)
                self.aomap.bind()

                functions.glUniform1f(shader.uniforms['MeMult'], self.mefac)
                functions.glUniform1f(shader.uniforms['RoMult'], self.material.pbrMetallicRoughness)

                functions.glUniform1i(shader.uniforms['MRTexture'], 2)
                functions.glActiveTexture(gl.GL_TEXTURE2)
                self.mrmap.bind()

                functions.glUniform1f(shader.uniforms['EmMult'], self.material.emissiveFactor)

                functions.glUniform1i(shader.uniforms['EMTexture'], 3)
                functions.glActiveTexture(gl.GL_TEXTURE3)
                self.emmap.bind()

            elif self.material.shader == "normal":
                functions.glUniform1f(shader.uniforms['AOMult'], self.material.aomapIntensity)

                functions.glUniform1i(shader.uniforms['AOTexture'], 1)
                functions.glActiveTexture(gl.GL_TEXTURE1)
                self.aomap.bind()

                functions.glUniform1i(shader.uniforms['NOTexture'], 2)
                functions.glActiveTexture(gl.GL_TEXTURE2)
                self.nomap.bind()

                functions.glUniform1i(shader.uniforms['MRTexture'], 3)
                functions.glActiveTexture(gl.GL_TEXTURE3)
                self.mrmap.bind()

        indices = self.getindex()
        functions.glDrawElements(gl.GL_TRIANGLES, len(indices), gl.GL_UNSIGNED_INT, indices)
        #
        # TODO: this is done always to reset, also setting of gl.GL_TEXTURE0
        #
        functions.glDisable(gl.GL_CULL_FACE)
        functions.glDisable(gl.GL_SAMPLE_ALPHA_TO_COVERAGE)
        functions.glDisable(gl.GL_BLEND)
        functions.glDisable(gl.GL_MULTISAMPLE)
        functions.glDisable(gl.GL_TEXTURE1)
        functions.glDisable(gl.GL_DEPTH_TEST)
        functions.glActiveTexture(gl.GL_TEXTURE0)

    def drawWireframe(self, proj_view_matrix, campos, black, white):
        """
        creates a wireframe model
        """
        shader = self.shaders.getShader("phong3l")
        self.geomToShader(shader, proj_view_matrix, campos)
        functions = self.context.functions()

        oldtexture = self.texture
        self.setTexture(black)
        t1 = shader.uniforms['Texture']
        functions.glUniform1i(t1, 0)
        functions.glActiveTexture(gl.GL_TEXTURE0)
        self.texture.bind()

        indices = self.getindex()

        openGLReset() # call sth stupid, becaue PolygonMode is not in the context
        
        functions.glEnable(gl.GL_DEPTH_TEST)
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        functions.glDrawElements(gl.GL_TRIANGLES, len(indices), gl.GL_UNSIGNED_INT, indices)

        functions.glEnable(gl.GL_CULL_FACE)
        functions.glEnable(gl.GL_POLYGON_OFFSET_FILL)
        functions.glPolygonOffset(1.0, 1.0)

        self.setTexture(white)
        functions.glActiveTexture(gl.GL_TEXTURE0)
        self.texture.bind()
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        functions.glDrawElements(gl.GL_TRIANGLES, len(indices), gl.GL_UNSIGNED_INT, indices)

        functions.glDisable(gl.GL_POLYGON_OFFSET_FILL)
        functions.glDisable(gl.GL_CULL_FACE)

        self.setTexture(oldtexture)
        functions.glDisable(gl.GL_DEPTH_TEST)
        functions.glActiveTexture(gl.GL_TEXTURE0)


class RenderedLines:
    def __init__(self, functions, shader, indices, name, glbuffers, pos, infront=False):
        self.functions = functions
        self.shader = shader
        self.name = name
        self.infront = infront
        self.position = QVector3D(0, 0, 0)
        self.scale = QVector3D(1, 1, 1)
        self.y_rotation = 0.0
        self.mvp_matrix = QMatrix4x4()
        self.model_matrix = QMatrix4x4()
        self.normal_matrix = QMatrix4x4()
        self.glbuffers = glbuffers
        self.indices = indices

        self.mvp_matrix_location = shader.uniforms["uMvpMatrix" ]
        self.model_matrix_location = shader.uniforms["uModelMatrix"]

        self.position = pos

    def __str__(self):
        return("GL Lines " + str(self.name))

    def delete(self):
        self.glbuffers.Delete()

    def setYRotation(self, rot):
        self.y_rotation = rot

    def draw(self, proj_view_matrix):
        """
        :param shaderprog: QOpenGLShaderProgram
        """
        self.shader.bind()

        self.glbuffers.BindBuffersToShader(self.shader)  # VAO etc.

        self.model_matrix.setToIdentity()
        self.model_matrix.translate(self.position)
        self.model_matrix.scale(self.scale)
        if self.y_rotation != 0.0:
            self.model_matrix.rotate(self.y_rotation, 0.0, 1.0, 0.0)
        self.mvp_matrix = proj_view_matrix * self.model_matrix

        # now set uMvpMatrix, uModelMatrix

        self.functions.glEnable(gl.GL_BLEND)
        if self.infront:
            self.functions.glDisable(gl.GL_DEPTH_TEST)
        else:
            self.functions.glEnable(gl.GL_DEPTH_TEST)
        self.shader.setUniformValue(self.mvp_matrix_location, self.mvp_matrix)
        self.shader.setUniformValue(self.model_matrix_location, self.model_matrix)

        indices = self.indices
        self.functions.glDrawElements(gl.GL_LINES, len(indices), gl.GL_UNSIGNED_INT, indices)
        self.functions.glDisable(gl.GL_BLEND)
        self.functions.glDisable(gl.GL_DEPTH_TEST)

class RenderedSimple:
    def __init__(self, functions, shaders, indices, name, glbuffers):
        self.functions = functions
        self.name = name
        self.scale = QVector3D(1, 1, 1)
        self.mvp_matrix = QMatrix4x4()
        self.model_matrix = QMatrix4x4()
        self.normal_matrix = QMatrix4x4()
        self.rotation = QMatrix4x4()
        self.glbuffers = glbuffers
        self.indices = indices

        self.shader = shaders.getShader("phong3l")
        self.mvp_matrix_location = self.shader.uniforms["uMvpMatrix" ]
        self.model_matrix_location = self.shader.uniforms["uModelMatrix"]
        self.normal_matrix_location = self.shader.uniforms["uNormalMatrix"]

    def __str__(self):
        return("GL Simple " + str(self.name))

    def setScale(self, s):
        self.scale = QVector3D(s, s, s)

    def setRotation(self, rot):
        self.rotation = QMatrix4x4(rot.flatten().tolist())

    def delete(self):
        self.glbuffers.Delete()

    def draw(self, proj_view_matrix, white):
        shader = self.shader
        shader.bind()

        self.glbuffers.BindBuffersToShader(self.shader)  # VAO etc.

        self.model_matrix.setToIdentity()
        self.model_matrix = self.model_matrix * self.rotation
        self.model_matrix.scale(self.scale)
        self.mvp_matrix = proj_view_matrix * self.model_matrix

        self.normal_matrix = self.model_matrix.inverted()
        self.normal_matrix = self.normal_matrix[0].transposed()

        # now set uMvpMatrix, uModelMatrix, uNormalMatrix

        shader.setUniformValue(self.mvp_matrix_location, self.mvp_matrix)
        shader.setUniformValue(self.model_matrix_location, self.model_matrix)
        shader.setUniformValue(self.normal_matrix_location, self.normal_matrix)
        self.texture = white
        t1 = shader.uniforms['Texture']
        self.functions.glActiveTexture(gl.GL_TEXTURE0)
        self.functions.glUniform1i(t1, 0)
        self.texture.bind()
        self.functions.glEnable(gl.GL_DEPTH_TEST)
        self.functions.glEnable(gl.GL_BLEND)
        self.functions.glBlendFunc(gl.GL_ONE, gl.GL_ZERO)
        self.functions.glDrawElements(gl.GL_TRIANGLES, len(self.indices), gl.GL_UNSIGNED_INT, self.indices)
        self.functions.glDisable(gl.GL_BLEND)
        self.functions.glDisable(gl.GL_DEPTH_TEST)



class PixelBuffer:
    """
    looks like the pixelbuffer functionality can only be reached by using classical gl-Functions
    still not okay. 

    TODO: multisample?
    """
    def __init__(self, glob, view, transparent=False):
        self.glob = glob
        self.view = view
        self.framebuffer = None
        self.colorbuffer = None
        self.depthbuffer = None
        self.width = 0
        self.height = 0
        self.oldheight = 0
        self.oldwidth = 0
        self.transparent = transparent

    # https://stackoverflow.com/questions/60800538/python-opengl-how-to-render-off-screen-correctly
    # https://learnopengl.com/Advanced-OpenGL/Framebuffers
    def getBuffer(self, width, height):
        self.width = width
        self.height = height
        self.oldheight = self.view.window_height
        self.oldwidth = self.view.window_width
        functions = self.view.context().functions()

        openGLReset() # call sth stupid, because glGenFramebuffers is not in the context

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

        c = self.view.light.glclearcolor
        transp = 0 if self.transparent else c.w()
        gl.glClearColor(c.x(), c.y(), c.z(), transp)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        proj_view_matrix = self.view.camera.getProjViewMatrix()
        baseClass = self.glob.baseClass
        start = 1 if baseClass.proxy is True else 0

        for obj in self.view.objects[start:]:
            obj.draw(proj_view_matrix, self.view.light)


    def bufferToImage(self):

        openGLReset() # call sth stupid, because glGenFramebuffers is not in the context
        gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT0)
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT, 1)

        pixmode = gl.GL_RGBA if self.transparent else gl.GL_RGB
        imgmode = QImage.Format_RGBA8888 if self.transparent else QImage.Format_RGB888

        data = gl.glReadPixels (0, 0, self.width, self.height, pixmode,  gl.GL_UNSIGNED_BYTE)

        image = QImage(self.width, self.height, imgmode)
        image.fromData(data)

        if self.transparent:
            # slow but I cannot find a better method yet
            for y in range (0, self.height):
                for x in range(0, self.width):
                    rgba = image.pixel(x,y)
                    if rgba & 0xff000000:
                        image.setPixel(x,y, rgba | 0xff000000)

        image.mirrored_inplace(False, True)
        return (image)

    def releaseBuffer(self):
        functions = self.view.context().functions()
        if self.framebuffer is not None:
            gl.glDeleteFramebuffers(1, np.array([self.framebuffer]))
        if self.colorbuffer is not None:
            gl.glDeleteRenderbuffers(1, np.array([self.colorbuffer]))
        if self.depthbuffer is not None:
            gl.glDeleteRenderbuffers(1, np.array([self.depthbuffer]))

        # use functions because then "0" is translated to default buffer
        #
        functions.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0)
        functions.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        gl.glPopAttrib()
        #
        # still not clear ... without glDisable I get a black screen
        #
        functions.glDisable(gl.GL_DEPTH_TEST)
        self.view.resizeGL(self.oldwidth, self.oldheight)
