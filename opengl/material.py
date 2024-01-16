from PySide6.QtOpenGL import QOpenGLTexture
from PySide6.QtGui import QImage

import os

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
         self.env.logLine(8, "Load: " + name)
         super().__init__(name)

    def __del__(self):
        self.env.logLine(4, "Release: " + self.name)
        

class Material:
    def __init__(self, glob, objdir):
        self.glob = glob
        self.env = glob.env
        self.objdir = objdir
        self.tags = []

    def __str__(self):
        text = ""
        for attr in dir(self):
            if not attr.startswith("__"):
                m = getattr(self, attr)
                if isinstance(m, int) or isinstance(m, str) or  isinstance(m, list):
                    text += (" %s = %r\n" % (attr, m))
        return(text)

    def isExistent(self, filename):
        path = os.path.join(self.objdir, filename)
        if os.path.isfile(path):
            return (path)
        else:
            return None

    def loadMatFile(self, filename):
        """
        mhmat file loader, TODO, still a subset
        """
        path = os.path.join(self.objdir, filename)
        self.env.logLine(8, "Loading material " + path)
        try:
            f = open(path, "r", encoding="utf-8", errors="ignore")
        except OSError as error:
            self.env.last_error = str(error)
            return (False)

        for line in f:
            words = line.split()
            if len(words) == 0:
                continue
            key = words[0]
            if key in ["#", "//"]:
                continue

            # if commands make no sense, they will be skipped ... 
            #
            if key in ["diffuseTexture", "normalmapTexture", "displacementmapTexture", "specularmapTexture", "transparencymapTexture",
                    "aomapTexture" ]:
                abspath = self.isExistent(words[1])
                if abspath is not None:
                    setattr (self, key, abspath)

            elif key in ["name", "description"]:
                setattr (self, key, " ".join(words[1:]))
            elif key == "tag":
                self.tags.append( " ".join(words[1:]).lower() )

            # simple bools:
            #
            elif key in [ "shadeless", "wireframe", "transparent", "alphaToCoverage", "backfaceCull", 
                    "depthless", "castShadows", "receiveShadows", "autoBlendSkin", "sssEnabled" ]:
                setattr (self, key, words[1].lower() in ["yes", "enabled", "true"])

            # colors
            #
            elif key in ["ambientColor", "diffuseColor", "emissiveColor", "viewPortColor" ]:
                setattr (self, key, [float(w) for w in words[1:4]])

            # intensities (all kind of floats)
            #
            elif key in ["shininess", "viewPortAlpha", "opacity", "translucency", "bumpmapIntensity",
                "normalmapIntensity", "displacementmapIntensity", "specularmapIntensity",
                "transparencymapIntensity", "aomapIntensity" ]:
                setattr (self, key, max(0.0, min(1.0, float(words[1]))))

            elif key in ["sssRScale", "sssGScale", "sssBScale"]:
                setattr (self, key, max(0.0, float(words[1])))

            # shaderparam will be prefixed by sp_
            #
            elif key == "shaderParam":
                setattr (self, "sp_" + words[1], words[2])

            # shaderconfig will be prefixed by sc_
            #
            elif key == "shaderConfig":
                if words[1] in ["diffuse", "bump", "normal", "displacement", "spec", "vertexColors", "transparency",
                        "ambientOcclusion"]:
                    setattr (self, "sc_" + words[1], words[2].lower() in ["yes", "enabled", "true"])


        print(self)

        return (True)

    def loadTexture(self, path):
        texture = QOpenGLTexture(QOpenGLTexture.Target2D)
        texture.create()
        texture.setData(QImage(path))
        self.glob.addTexture(path, texture)
        #texture.setData(MH_Image(path, self.env))
        texture.setMinMagFilters(QOpenGLTexture.Linear, QOpenGLTexture.Linear)
        texture.setWrapMode(QOpenGLTexture.ClampToEdge)
        #print (texture.target())
        return (texture)
