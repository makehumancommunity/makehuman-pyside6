import os
from PySide6.QtOpenGL import QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram, QOpenGLTexture
from PySide6.QtGui import QImage

"""
    try to put all Texture and Shader Stuff here
"""
class ShaderRepository(QOpenGLShaderProgram):

    def __init__(self, env):
        self.env = env
        super().__init__()
        self._vshaders = {}
        self._fshaders = {}
        self.uniforms = { "uMvpMatrix": -1, "uModelMatrix": -1, "uNormalMatrix": -1,
                "lightPos1": -1, "lightPos2": -1, "lightPos3": -1,
                "lightVol1": -1, "lightVol2": -1, "lightVol3": -1,
                "ambientLight": -1, "lightWeight": -1, "viewPos": -1, "blinn": -1  }

    def loadFragShader(self, filename):
        path = os.path.join (self.env.path_sysdata, "shaders", filename + ".frag")
        self.env.logLine(8, "Load: " + path)
        if self.addShaderFromSourceFile(QOpenGLShader.Fragment, path):
            self._fshaders[path] = { "id": self.shaders()[-1].shaderId() }

    def loadVertShader(self, filename):
        path = os.path.join (self.env.path_sysdata, "shaders", filename + ".vert")
        self.env.logLine(8, "Load: " + path)
        if self.addShaderFromSourceFile(QOpenGLShader.Vertex,path):
            self._vshaders[path] = { "id": self.shaders()[-1].shaderId() }

        print ( self._vshaders)
        print ( self._fshaders)

    def attribVertShader(self):
        self.bindAttributeLocation("aPosition", 0)
        self.bindAttributeLocation("aNormal", 1)
        self.bindAttributeLocation("aTexCoords", 2)
        self.link()
        self.bind()

    def getUniforms(self):
        for key in self.uniforms.keys():
            self.uniforms[key] = self.uniformLocation(key)

        print (self.uniforms)

    def setUniform(self, name, var):
        if name in self.uniforms:
            if self.uniforms[name] != -1:
                self.setUniformValue(self.uniforms[name], var)
            else:
                print (name + " not registered")
