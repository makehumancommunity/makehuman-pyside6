"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck
"""
import os
import numpy
from core.debug import dumper
from opengl.texture import MH_Texture


"""
    try to put all Material Stuff here
"""


class Material:
    def __init__(self, glob, objdir, eqtype):
        self.glob = glob
        self.env = glob.env
        self.objdir = objdir
        self.type = eqtype
        self.tags = []
        self.default()
        self.name = None
        self.filename = None

    def __str__(self):
        return(dumper(self))

    def default(self):
        self.tex_diffuse = None
        self.tex_litsphere = None
        self.tex_aomap = None
        self.tex_nomap = None
        self.tex_mrmap = None
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
        self.alphaToCoverage = False
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
        self.shader = "phong3l"
        self.sp_AdditiveShading = 0.0

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
        
        self.env.logLine(8, "unknown texture " + filename)
            
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

            # shader is shadertype, old path is replaced by last term. default is phong3l
            #
            elif key == "shader":
                arg = words[1]
                if "/" in arg:
                    arg = arg.split("/")[-1]
                self.shader = arg

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

            # shaderparam will be prefixed by sp_, search for litsphere
            #
            elif key == "shaderParam":
                if words[1] == "litsphereTexture":
                    path = self.env.existDataFile("shaders", "litspheres", os.path.basename(words[2]))
                    if path is not None:
                        setattr (self, "sp_litsphereTexture", path)
                    else:
                        self.env.logLine(1, "missing litsphereTexture: " + words[2])
                elif words[1] == "AdditiveShading":
                    setattr (self, "sp_" + words[1], float(words[2]))
                else:
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

        # avoid empty litsphere textures (switch back to phong3l
        #
        if self.shader == "litsphere" and not hasattr(self, "sp_litsphereTexture"):
            self.shader = "phong3l"

        print(self)
        return (True)

    def textureRelName(self, path):
        """
        path name always in UNIX syntax, needed as a base
        """
        path = self.env.formatPath(path)
        if path.startswith(self.objdir):
            relpath = path[len(self.objdir)+1:]
            return(relpath)

        test = self.env.stdSysPath(self.type)
        rest = None
        if self.objdir.startswith(test):
            rest = self.objdir[len(test)+1:]
        
        test = self.env.stdUserPath(self.type)
        if self.objdir.startswith(test):
            rest = self.objdir[len(test)+1:]

        if rest:
            asset = rest.split("/")[0]
            relpath = os.path.join(self.type, asset, os.path.basename(path))
        else:
            relpath = os.path.basename(path)
        return(relpath)

    def saveMatFile(self, path):
        self.env.logLine(8, "Saving material " + path)

        if hasattr(self, "diffuseTexture"):
            diffuse = "diffuseTexture " + self.textureRelName(self.diffuseTexture) + "\n"
        else:
            diffuse = ""

        if hasattr(self, "normalmapTexture"):
            normal = "normalmapTexture " + self.textureRelName(self.normalmapTexture) + \
                "\nnormalmapIntensity " + str(self.normalmapIntensity) + "\n"
        else:
            normal = ""

        if hasattr(self, "aomapTexture"):
            occl = "aomapTexture " + self.textureRelName(self.aomapTexture) + \
                "\naomapIntensity " + str(self.aomapIntensity) + "\n"
        else:
            occl = ""

        if hasattr(self, "metallicRoughnessTexture"):
            metrough = "metallicRoughnessTexture " + self.textureRelName(self.metallicRoughnessTexture) + "\n"
        else:
            metrough = ""

        # for litsphere save only name to avoid trouble
        #
        if hasattr(self, "sp_litsphereTexture"):
            litsphere = "shaderParam litsphereTexture " + os.path.basename(self.sp_litsphereTexture)
        else:
            litsphere = ""

        shader = "shader " + self.shader + "\n"

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

        # second way is a parallel materials folder for common materials
        #
        if len( materialfiles) == 0:
            objdir = os.path.join(os.path.dirname(objdir), "materials")
            for (root, dirs, files) in  os.walk(objdir):
                for name in files:
                    if name.endswith(".mhmat"):
                        materialfiles.append(os.path.join(root, name))

        return(materialfiles)

    def mixColors(self, colors, values):
        """
        generates a texture from a number of colors (e.g. ethnic slider)
        """
        col = numpy.asarray(colors)
        newcolor = numpy.array([0.0, 0.0, 0.0])
        for n, elem in enumerate(col):
            newcolor += elem * values[n]
        self.freeTextures()
        self.tex_diffuse = MH_Texture(self.glob.textureRepo)
        return self.tex_diffuse.unicolor([newcolor[0], newcolor[1], newcolor[2]])

    def uniColor(self, rgb):
        self.tex_diffuse = MH_Texture(self.glob.textureRepo, self.type)
        return self.tex_diffuse.unicolor(rgb)

    def loadLitSphere(self):
        self.tex_litsphere = MH_Texture(self.glob.textureRepo)
        return self.tex_litsphere.load(self.sp_litsphereTexture)

    def loadAOMap(self, white):
        if hasattr(self, 'aomapTexture'):
            self.tex_aomap = MH_Texture(self.glob.textureRepo)
            return self.tex_aomap.load(self.aomapTexture)

        return white

    def loadNOMap(self, nocolor):
        if hasattr(self, 'normalmapTexture'):
            self.tex_nomap = MH_Texture(self.glob.textureRepo)
            return self.tex_nomap.load(self.normalmapTexture)

        return nocolor

    def loadMRMap(self, white):
        if hasattr(self, 'metallicRoughnessTexture'):
            self.tex_mrmap = MH_Texture(self.glob.textureRepo)
            return self.tex_mrmap.load(self.metallicRoughnessTexture)

        return white


    def loadDiffuse(self):
        self.tex_diffuse = MH_Texture(self.glob.textureRepo)
        if hasattr(self, 'diffuseTexture'):
            self.sc_diffuse = True
            return self.tex_diffuse.load(self.diffuseTexture)

        self.sc_diffuse = False
        if hasattr(self, 'diffuseColor'):
            return self.tex_diffuse.unicolor(self.diffuseColor)
        return self.tex_diffuse.unicolor()

    def freeTextures(self):
        # in case of system, cleanup is done in the end
        #
        if self.tex_diffuse:
            if self.type != "system":
                self.tex_diffuse.delete()
            else:
                self.tex_diffuse.destroy()

        for elem in [self.tex_litsphere, self.tex_aomap, self.tex_mrmap, self.tex_nomap]:
            if elem:
                elem.delete()

