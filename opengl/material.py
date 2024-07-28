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
        self.ambientColor = [0.5, 0.5, 0.5 ]
        self.diffuseColor = [1.0, 1.0, 1.0 ]
        self.specularColor = [0.5, 0.5, 0.5 ]
        self.emissiveColor = [0.0, 0.0, 0.0 ]
        self.opacity = 1.0
        self.translucency = 0.0
        self.metallicFactor = 0.0
        self.pbrMetallicRoughness = None
        self.transparent = False
        self.shininess = 0.5
        #
        self.shadeless = False
        self.depthless = False
        self.castShadows = True
        self.receiveShadows = True
        self.alphaToCoverage = True
        self.backfaceCull = False
        #
        self.sc_normal = False
        self.sc_ambientOcclusion = False
        self.sc_diffuse = False
        self.sc_bump = False
        self.sc_displacement = False
        self.sc_vertexColors = False
        self.sc_spec = False
        self.sc_transparency = False
        self.shader = None

        self.description = None
        self.aomapIntensity = 1.0
        self.normalmapIntensity = 1.0

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
                    "aomapTexture", "metallicRoughnessTexture" ]:
                abspath = self.isExistent(words[1])
                if abspath is not None:
                    setattr (self, key, abspath)

            elif key in ["name", "description"]:
                setattr (self, key, " ".join(words[1:]))
            elif key == "tag":
                self.tags.append( " ".join(words[1:]).lower() )
            elif key == "shader":
                self.shader = words[1]

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
                "transparencymapIntensity", "aomapIntensity", "pbrMetallicRoughness", "metallicFactor" ]:
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

        if self.pbrMetallicRoughness is None:
            self.pbrMetallicRoughness = 1.0 - sum(self.specularColor) / 3

        if self.name is None:
            self.name = os.path.basename(path)
        if self.description is None:
            self.description = self.name + " material"
        print(self)
        return (True)

    def saveMatFile(self, path):
        self.env.logLine(8, "Saving material " + path)

        if hasattr(self, "diffuseTexture"):
            diffuse = "diffuseTexture " + os.path.basename(self.diffuseTexture) + "\n"
        else:
            diffuse = ""

        if hasattr(self, "normalmapTexture"):
            normal = "normalmapTexture " + os.path.basename(self.normalmapTexture) + \
                "\nnormalmapIntensity " + str(self.normalmapIntensity) + "\n"
        else:
            normal = ""

        if hasattr(self, "aomapTexture"):
            occl = "aomapTexture " + os.path.basename(self.aomapTexture) + \
                "\naomapIntensity " + str(self.aomapIntensity) + "\n"
        else:
            occl = ""

        if hasattr(self, "metallicRoughnessTexture"):
            metrough = "metallicRoughnessTexture " + os.path.basename(self.metallicRoughnessTexture) + "\n"
        else:
            metrough = ""

        if hasattr(self, "sp_litsphereTexture"):
            litsphere = "shaderParam litsphereTexture " + self.sp_litsphereTexture
        else:
            litsphere = ""

        if self.shader is not None:
            shader = "shader " + self.shader + "\n"
        else:
            shader = ""

        try:
            fp = open(path, "w", encoding="utf-8", errors='ignore')
        except IOError as err:
            self.env.last_error = str(err)
            return (False)

        text = f"""# Material definition for {self.name}
name {self.name}
description {self.description}

ambientColor {self.ambientColor[0]} {self.ambientColor[1]} {self.ambientColor[2]}
diffuseColor {self.diffuseColor[0]} {self.diffuseColor[1]} {self.diffuseColor[2]}
specularColor {self.specularColor[0]} {self.specularColor[1]} {self.specularColor[2]}
shininess {self.shininess}
emissiveColor {self.emissiveColor[0]} {self.emissiveColor[1]} {self.emissiveColor[2]}
opacity {self.opacity}
translucency {self.translucency}
metallicFactor {self.metallicFactor}
pbrMetallicRoughness {self.pbrMetallicRoughness}

shadeless {self.shadeless}
wireframe {self.wireframe}
transparent {self.transparent}
alphaToCoverage {self.alphaToCoverage}
backfaceCull {self.backfaceCull}
depthless {self.depthless}

castShadows {self.castShadows}
receiveShadows {self.receiveShadows}

{diffuse}{normal}{occl}{metrough}

{shader}{litsphere}

shaderConfig ambientOcclusion {self.sc_ambientOcclusion}
shaderConfig normal {self.sc_normal}
shaderConfig bump {self.sc_bump}
shaderConfig displacement {self.sc_displacement}
shaderConfig vertexColors {self.sc_vertexColors}
shaderConfig spec {self.sc_spec}
shaderConfig transparency {self.sc_transparency}
shaderConfig diffuse {self.sc_diffuse}
"""
        
        fp.write(text)
        fp.close()
        return True

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
        self.sc_diffuse = False
        image = QImage(QSize(1,1),QImage.Format_ARGB32)
        color = QColor.fromRgbF(rgb[0], rgb[1], rgb[2])
        image.fill(color)
        name = "Generated " + repr(self) + " [" +str(len(self._textures)+1) + "]"
        return(self.newTexture(name, image))

    def mixColors(self, colors, values):
        """
        generates a texture from a number of colors (e.g. ethnic slider)
        """
        col = numpy.asarray(colors)
        newcolor = numpy.array([0.0, 0.0, 0.0])
        for n, elem in enumerate(col):
            newcolor += elem * values[n]
        self.freeTextures()
        return(self.emptyTexture([newcolor[0], newcolor[1], newcolor[2]]))

    def loadTexture(self, path):
        image = QImage(path)
        self.sc_diffuse = True
        return(self.newTexture(path, image))

    def freeTextures(self):
        for elem in self._textures:
            self.glob.freeTexture(elem)
        self._textures = []
