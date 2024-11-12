from PySide6.QtOpenGL import QOpenGLTexture, QOpenGLBuffer
from PySide6.QtGui import QImage, QVector4D
import numpy as np
from OpenGL import GL as gl
import os

class OpenGLSkyBox:
    def __init__(self, env, glprog, glfunc):
        self.env  = env
        self.prog = glprog
        self.func = glfunc
        self.texture = None
        self.vbuffer = None

    def create(self):
        # textures
        self.image = [ None, None, None, None, None, None ]
        self.texture = QOpenGLTexture(QOpenGLTexture.TargetCubeMap)
        self.texture.setSize(2048, 2048)
        self.texture.create()
        # self.texture.bind()
        self.texture.setFormat(QOpenGLTexture.RGBAFormat)

        shaderpath = os.path.join(self.env.path_sysdata, "shaders", "img")
        for i, elem in enumerate (["posx.jpg", "negx.jpg", "posy.jpg", "negy.jpg", "posz.jpg", "negz.jpg"]):
            filename = os.path.join(shaderpath, elem)
            self.image[i] = QImage(filename)

        self.texture.allocateStorage()

        self.texture.setData(0, 0, QOpenGLTexture.CubeMapPositiveX, QOpenGLTexture.RGBA, QOpenGLTexture.UInt8, self.image[0].bits())
        self.texture.setData(0, 0, QOpenGLTexture.CubeMapNegativeX, QOpenGLTexture.RGBA, QOpenGLTexture.UInt8, self.image[1].bits())
        self.texture.setData(0, 0, QOpenGLTexture.CubeMapPositiveY, QOpenGLTexture.RGBA, QOpenGLTexture.UInt8, self.image[2].bits())
        self.texture.setData(0, 0, QOpenGLTexture.CubeMapNegativeY, QOpenGLTexture.RGBA, QOpenGLTexture.UInt8, self.image[3].bits())
        self.texture.setData(0, 0, QOpenGLTexture.CubeMapPositiveZ, QOpenGLTexture.RGBA, QOpenGLTexture.UInt8, self.image[4].bits())
        self.texture.setData(0, 0, QOpenGLTexture.CubeMapNegativeZ, QOpenGLTexture.RGBA, QOpenGLTexture.UInt8, self.image[5].bits())


        self.texture.setMinMagFilters(QOpenGLTexture.Linear, QOpenGLTexture.Linear)
        self.texture.setWrapMode(QOpenGLTexture.ClampToEdge)

        # vertices
        skyboxVerts = [ -1.0,  1.0, -1.0, -1.0, -1.0, -1.0, 1.0, -1.0, -1.0, 1.0, -1.0, -1.0, 1.0,  1.0, -1.0, -1.0,  1.0, -1.0, 
                -1.0, -1.0,  1.0, -1.0, -1.0, -1.0, -1.0,  1.0, -1.0, -1.0,  1.0, -1.0, -1.0,  1.0,  1.0, -1.0, -1.0,  1.0, 
                1.0, -1.0, -1.0, 1.0, -1.0,  1.0, 1.0,  1.0,  1.0, 1.0,  1.0,  1.0, 1.0,  1.0, -1.0, 1.0, -1.0, -1.0, 
                -1.0, -1.0,  1.0, -1.0,  1.0,  1.0, 1.0,  1.0,  1.0, 1.0,  1.0,  1.0, 1.0, -1.0,  1.0, -1.0, -1.0,  1.0, 
                -1.0,  1.0, -1.0, 1.0,  1.0, -1.0, 1.0,  1.0,  1.0, 1.0,  1.0,  1.0, -1.0,  1.0,  1.0, -1.0,  1.0, -1.0, 
                -1.0, -1.0, -1.0, -1.0, -1.0,  1.0, 1.0, -1.0, -1.0, 1.0, -1.0, -1.0, -1.0, -1.0,  1.0, 1.0, -1.0,  1.0 ]

        skyboxVerts = np.array(skyboxVerts, dtype=np.float32) 

        self.vbuffer = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        self.vbuffer.create()
        self.vbuffer.bind()
        self.vbuffer.allocate(skyboxVerts, len(skyboxVerts)*4)

        self.prog.enableAttributeArray(0)
        self.prog.setAttributeBuffer(0, gl.GL_FLOAT, 0, 3, 3 * 4)

    def delete(self):
        if self.vbuffer is not None:
            self.vbuffer.destroy()
        if self.texture is not None:
            self.texture.destroy()


    def draw(self, projection):
        self.prog.bind()
        self.func.glDepthFunc(gl.GL_LEQUAL);
        key = self.prog.uniformLocation("uModelMatrix")
        self.prog.setUniformValue(key, projection)

        self.vbuffer.bind()
        self.prog.enableAttributeArray(0)
        self.prog.setAttributeBuffer(0, gl.GL_FLOAT, 0, 3, 3 * 4)
        t1 = self.prog.uniforms['skybox']
        self.func.glUniform1i(t1, 0)
        self.func.glActiveTexture(gl.GL_TEXTURE0)
        self.texture.bind()
        self.func.glDrawArrays(gl.GL_TRIANGLES, 0, 36)
        self.func.glDepthFunc(gl.GL_LESS)
        self.texture.release()

