import os
from PySide6.QtOpenGL import QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram

"""
    try to put all Texture and Shader Stuff here
    TODO: will control multi-shaders later
"""

class ShaderPair(QOpenGLShaderProgram):
    def __init__(self, env, path):
        self.uniforms = { "uMvpMatrix": -1, "uModelMatrix": -1, "uNormalMatrix": -1,
                "ambientLight": -1, "lightWeight": -1, "viewPos": -1, "blinn": -1,
                "Texture": -1, "litsphereTexture": -1, "AdditiveShading": -1,
                "AOTexture": -1, "AOMult": -1, "MRTexture": -1, "MeMult": -1, "RoMult": -1, "skybox": -1}
        self.env = env
        self.frag_id = None
        self.vert_id = None
        self.path = path
        super().__init__()

    def __str__(self):
        return "Shader Pair: "+ self.path

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
        self._shaders = []          # list of shaders
        self._shadernames = {}      # shaders by name reference to _shaders

    def getShader(self, name):
        """
        return shader by name
        if not known, return default
        """
        shadernum = self._shadernames[name] if name in self._shadernames else 0
        return  self._shaders[shadernum]

    def loadShader(self, filename):
        path = os.path.join (self.env.path_sysdata, "shaders", filename)
        if path in self._shadernames:
            return self._shadernames[path]

        pair = ShaderPair(self.env, path)
        pair.loadFragShader()
        pair.loadVertShader()
        self._shaders.append(pair)
        shadernum = len(self._shaders)-1
        self._shadernames[filename] = shadernum
        return shadernum

    def loadShaders(self, filenames):
        """
        load a list of shaders
        """
        for shader in filenames:
            s = self.loadShader(shader)
            self.attribVertShader(s)
            self.getUniforms(s)

    def attribVertShader(self, num=0):
        shader = self._shaders[num]
        shader.bindAttributeLocation("aPosition", 0)
        shader.bindAttributeLocation("aNormal", 1)
        shader.bindAttributeLocation("aTexCoords", 2)
        shader.link()
        shader.bind()

    def bindShader(self, shader):
        shader.bind()

    def getUniforms(self, num=0):
        shader = self._shaders[num]
        for key in shader.uniforms.keys():
            shader.uniforms[key] = shader.uniformLocation(key)
        print ("shader: " + str(num))
        print (shader.uniforms)

    def setShaderUniform(self, shader, name, var):
        if name in shader.uniforms:
            if shader.uniforms[name] != -1:
                shader.setUniformValue(shader.uniforms[name], var)
            else:
                print (name + " not registered")

    def setShaderArrayStruct(self, shader, name, index, member, var):
        name = name + "[" + str(index) + "]." + member
        loc = shader.uniformLocation(name)
        if loc != -1:
            if isinstance(var, float):
                shader.setUniformValue1f(loc, var)
            else:
                shader.setUniformValue(loc, var)
        else:
            print (name + " not registered")

