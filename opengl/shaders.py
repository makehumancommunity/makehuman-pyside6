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

    def loadFragShader(self, filename):
        path = os.path.join (self.env.path_sysdata, "shaders", filename + ".frag")
        self.env.logLine(3, "Load: " + path)
        self.addShaderFromSourceFile(QOpenGLShader.Fragment, path)

    def loadVertShader(self, filename):
        path = os.path.join (self.env.path_sysdata, "shaders", filename + ".vert")
        self.env.logLine(3, "Load: " + path)
        self.addShaderFromSourceFile(QOpenGLShader.Vertex,path)

    def attribVertShader(self):
        self.bindAttributeLocation("aPosition", 0)
        self.bindAttributeLocation("aNormal", 1)
        self.bindAttributeLocation("aTexCoord", 2)
        self.link()
        self.bind()

    def getVertLocations(self):
        self.mvp_matrix_location = self.uniformLocation("uMvpMatrix")
        self.model_matrix_location = self.uniformLocation("uModelMatrix")
        self.normal_matrix_location =  self.uniformLocation("uNormalMatrix")

