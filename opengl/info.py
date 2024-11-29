import OpenGL
from OpenGL import GL as gl

def openGLReset():
    a = gl.glGetError() # this is a joke, usually makeCurrent should work but it does not (it returns 1280)

class GLDebug:
    def __init__(self, initialized=True):
        self.initialized = initialized
        self.min_version = tuple([3, 3])

    def getOpenGL_LibVers(self):
        return OpenGL.__version__

    def minVersion(self):
        return str(self.min_version)

    def getVersion(self):
        if self.initialized:
            return(gl.glGetIntegerv(gl.GL_MAJOR_VERSION, '*'), gl.glGetIntegerv(gl.GL_MINOR_VERSION, '*'))
        else:
            return(0,0)

    def checkVersion(self):
        major, minor = self.getVersion()
        return( (major, minor) >=  self.min_version)

    def getExtensions(self):
        extensions = []
        if self.initialized:
            n=  gl.glGetIntegerv(gl.GL_NUM_EXTENSIONS, "*")
            for i in range(0, n):
                extensions.append (gl.glGetStringi(gl.GL_EXTENSIONS, i).decode("utf-8"))
        return (extensions)

    def getShadingLanguages(self):
        languages = []
        if self.initialized:
            n = int.from_bytes(gl.glGetIntegerv(gl.GL_NUM_SHADING_LANGUAGE_VERSIONS, "*"), "big")
            for i in range(0, n):
                languages.append(gl.glGetStringi(gl.GL_SHADING_LANGUAGE_VERSION, i).decode("utf-8"))
        return (languages)

    def getCard(self):
        return gl.glGetString(gl.GL_VERSION).decode("utf-8") if self.initialized else "not initialized"

    def getRenderer(self):
        return gl.glGetString(gl.GL_RENDERER).decode("utf-8") if self.initialized else "not initialized"

    def getInfo(self):
        info = {}
        info["min_version"] = self.minVersion()
        info["version"] = self.getVersion()
        info["card"] = self.getCard()
        info["renderer"] = self.getRenderer()
        info["languages"] = self.getShadingLanguages()
        info["extensions"] = self.getExtensions()
        return(info)

    def getTextInfo(self):
        openGLReset()  
        text = "Minimum version demanded: " + str(self.min_version) + \
            "<br>Highest version available: " + str(self.getVersion()) + \
            "<br>Card Driver: " + self.getCard() + \
            "<br>Renderer: " + self.getRenderer() + \
            "<p>Shading languages:"

        lang = self.getShadingLanguages()
        for l in lang:
            text += "<br>" + l

        text += "<p>Extensions:"
        ext = self.getExtensions()
        for l in ext:
            text += "<br>" + l

        return (text)



