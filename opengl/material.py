from PySide6.QtOpenGL import QOpenGLTexture
from PySide6.QtGui import QImage, QColor
from PySide6.QtCore import QSize

import os
import numpy
from core.debug import dumper


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
    def __init__(self, glob, objdir, eqtype):
        self.glob = glob
        self.env = glob.env
        self.objdir = objdir
        self.type = eqtype
        self.tags = []
        self._textures = []
        self.default()
        self.name = None
        self.filename = None

    def __str__(self):
        return(dumper(self))

    def default(self):
        self.diffuseColor = [1.0, 1.0, 1.0 ]
        self.specularColor = [0.5, 0.5, 0.5 ]
        self.has_imagetexture = False
        self.transparent = False
        self.backfaceCull = False
        self.shininess = 0.5

    def isExistent(self, filename):
        """
        concatenate / check same folder (objdir ends with the start of filename)
        """
        path = os.path.join(self.objdir, filename)
        if os.path.isfile(path):
            return (path)

        # try to get rid of first directory of filename
        #
        if "/" in filename:
            fname = "/".join (filename.split("/")[1:])
            path = os.path.join(self.objdir, fname)
            if os.path.isfile(path):
                return (path)

        # try an "absolute" method when it starts with the type name like "clothes"
        # then delete clothes 
        # in both cases try directly in asset folders
        # for base mesh default is skins
        #
        itype = "skins" if self.type == "base" else self.type

        if filename.startswith(itype):
            if "/" in filename:
                filename = "/".join (filename.split("/")[1:])

        path = os.path.join(self.env.stdSysPath(itype), filename)
        if os.path.isfile(path):
            return (path)

        path = os.path.join(self.env.stdUserPath(itype), filename)
        if os.path.isfile(path):
            return (path)
            
        return None

    def loadMatFile(self, path):
        """
        mhmat file loader, TODO, still a subset
        """
        self.filename = path
        self.objdir = os.path.dirname(path)

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
            elif key in ["ambientColor", "diffuseColor", "emissiveColor", "viewPortColor", "specularColor" ]:
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

        self.specularValue = sum(self.specularColor) / 3
        print(self)
        return (True)

    def getCurrentMatFilename(self):
        return self.filename

    def listAllMaterials(self, objdir = None):
        if objdir is None:
            objdir = self.objdir

        materialfiles=[]
        for (root, dirs, files) in  os.walk(objdir):
            for name in files:
                if name.endswith(".mhmat"):
                    materialfiles.append(os.path.join(root, name))
        return(materialfiles)

    def newTexture(self, path, image):
        texture = QOpenGLTexture(QOpenGLTexture.Target2D)
        texture.create()
        texture.setData(image)
        self.glob.addTexture(path, texture)
        texture.setMinMagFilters(QOpenGLTexture.Linear, QOpenGLTexture.Linear)
        texture.setWrapMode(QOpenGLTexture.ClampToEdge)
        self._textures.append(texture)
        return (texture)

    def emptyTexture(self, rgb = [0.5, 0.5, 0.5]):
        self.has_imagetexture = False
        image = QImage(QSize(1,1),QImage.Format_ARGB32)
        color = QColor.fromRgbF(rgb[0], rgb[1], rgb[2])
        image.fill(color)
        name = "Generated " + repr(self) + " [" +str(len(self._textures)+1) + "]"
        return(self.newTexture(name, image))

    def mixColors(self, colors, values):
        """
        generates a texture from a number of colors (e.g. ethic slider)
        """
        col = numpy.asarray(colors)
        newcolor = numpy.array([0.0, 0.0, 0.0])
        for n, elem in enumerate(col):
            newcolor += elem * values[n]
        self.freeTextures()
        return(self.emptyTexture([newcolor[0], newcolor[1], newcolor[2]]))

    def loadTexture(self, path):
        image = QImage(path)
        self.has_imagetexture = True
        return(self.newTexture(path, image))

    def freeTextures(self):
        for elem in self._textures:
            self.glob.freeTexture(elem)
        self._textures = []
