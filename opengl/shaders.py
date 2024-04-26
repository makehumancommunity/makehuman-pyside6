import os
from PySide6.QtOpenGL import QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram

"""
    try to put all Texture and Shader Stuff here
    TODO: will control multi-shaders later
"""

class ShaderPair(QOpenGLShaderProgram):
    def __init__(self, env, path):
        self.uniforms = { "uMvpMatrix": -1, "uModelMatrix": -1, "uNormalMatrix": -1,
                "lightPos1": -1, "lightPos2": -1, "lightPos3": -1,
                "lightVol1": -1, "lightVol2": -1, "lightVol3": -1,
                "ambientLight": -1, "lightWeight": -1, "viewPos": -1, "blinn": -1}
        self.env = env
        self.frag_id = None
        self.vert_id = None
        self.path = path
        super().__init__()

    def loadFragShader(self):
        path = self.path + ".frag"
        self.env.logLine(8, "Load: " + path)
        if self.addShaderFromSourceFile(QOpenGLShader.Fragment, path):
            self.frag_id  = self.shaders()[-1].shaderId()

    def loadVertShader(self):
        path = self.path + ".vert"
        self.env.logLine(8, "Load: " + path)
        if self.addShaderFromSourceFile(QOpenGLShader.Vertex,path):
            self.vert_id = self.shaders()[-1].shaderId()



class ShaderRepository():

    def __init__(self, glob):
        self.glob = glob
        self.env = glob.env
        self._shaders = []

    def loadShaders(self, filename):
        path = os.path.join (self.env.path_sysdata, "shaders", filename)
        for elem in self._shaders:
            if elem.path == path:
                return(elem.vert_id)

        pair = ShaderPair(self.env, path)
        pair.loadFragShader()
        pair.loadVertShader()
        self._shaders.append(pair)
        return(pair.vert_id)

    def attribVertShader(self, num=0):
        shader = self._shaders[num]
        shader.bindAttributeLocation("aPosition", 0)
        shader.bindAttributeLocation("aNormal", 1)
        shader.bindAttributeLocation("aTexCoords", 2)
        shader.link()
        shader.bind()

    def bind(self, num=0):
        shader = self._shaders[num]
        shader.bind()

    def getUniforms(self, num=0):
        shader = self._shaders[num]
        for key in shader.uniforms.keys():
            shader.uniforms[key] = shader.uniformLocation(key)
        print ("shader: " + str(num))
        print (shader.uniforms)

    def setUniform(self, name, var, num=0):
        shader = self._shaders[num]
        if name in shader.uniforms:
            if shader.uniforms[name] != -1:
                shader.setUniformValue(shader.uniforms[name], var)
            else:
                print (name + " not registered")
