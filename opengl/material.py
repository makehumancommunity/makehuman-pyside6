from PySide6.QtOpenGL import QOpenGLTexture
from PySide6.QtGui import QImage

"""
    try to put all Texture and Material Stuff here
"""

class MH_Image(QImage):
    """
    this may be used later when working on big textures
    """
    def __init__(self,name,env):
         self.env = env
         self.name = name
         self.env.logLine(3, "Load: " + name)
         super().__init__(name)

    def __del__(self):
        self.env.logLine(3, "Release: " + self.name)
        

class Material:
    def __init__(self, env, glob):
        self.env = env
        self.glob = glob

    def loadTexture(self, path):
        texture = QOpenGLTexture(QOpenGLTexture.Target2D)
        texture.create()
        texture.setData(QImage(path))
        self.glob.addTexture(path)
        #texture.setData(MH_Image(path, self.env))
        texture.setMinMagFilters(QOpenGLTexture.Linear, QOpenGLTexture.Linear)
        texture.setWrapMode(QOpenGLTexture.ClampToEdge)
        print (texture.target())
        return (texture)
