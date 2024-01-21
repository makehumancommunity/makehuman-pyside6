import os
from core.target import Targets
from core.attached_asset import attachedAsset
from obj3d.object3d import object3d
from core.debug import memInfo
from core.target import Modelling

class loadedMHM():
    def __init__(self):
        self.name = None
        self.skinMaterial = None
        self.modifiers = []

class baseClass():
    """
    get the environment for a base
    """
    def __init__(self, glob, name, dirname):
        self.env = glob.env
        self.glob = glob
        self.dirname = dirname        # contains dirname of the obj (to determine user or system space)
        self.baseMesh = None
        self.baseInfo = None
        self.attachedAssets = []
        self.env.logLine(2, "New baseClass: " + name)
        memInfo()
        self.env.basename = name
        self.name = name                # will hold the character name


    def loadMHMFile(self, filename):
        """
        will usually load an mhm-file
        """
        self.env.logLine(8, "Load: " + filename)
        try:
            fp = open(filename, "r", encoding="utf-8", errors='ignore')
        except IOError as err:
            return (False, str(err))

        loaded = loadedMHM()
        for line in fp:
            words = line.split()

            # skip white space and comments
            #
            if len(words) == 0 or words[0].startswith('#'):
                continue

            key = words[0]
            if key in ["version", "skinMaterial"]:
                setattr (loaded, key, words[1])
            elif key == "name":
                loaded.name = " ".join(words[1:])
            elif key == "modifier":
                loaded.modifiers.append(" ".join(words[1:]))


        fp.close()

        if loaded.name is not None:
            self.name = loaded.name

        if loaded.skinMaterial is not None:
            filename = self.env.existDataFile("skins", self.env.basename, os.path.basename(loaded.skinMaterial))
            if filename is not None:
                self.baseMesh.loadMaterial(filename, os.path.dirname(filename))

        # reset all targets and mesh, reset missing targets
        #
        self.glob.Targets.reset()
        self.glob.missingTargets = []
        for elem in loaded.modifiers:
            name, value = elem.split()
            self.glob.Targets.setTargetByName(name, value)

        self.applyAllTargets()
        return (True, "okay")

    def saveMHMFile(self, filename):
        self.env.logLine(8, "Save: " + filename)
        try:
            fp = open(filename, "w", encoding="utf-8", errors='ignore')
        except IOError as err:
            return (False, str(err))

        # create version as string, name from filename
        #
        vers = ".".join(map(str,self.env.release_info["version"]))
        (p, name) = os.path.split(filename[:-4])

        fp.write("# MakeHuman2 Model File\nversion v" + vers + "\nname " + name + "\n")

        # write targets
        #
        if self.glob.Targets is not None:
            for target in self.glob.Targets.modelling_targets:
                if target.value != 0.0 and target.pattern != "None":
                    fp.write ("modifier " + target.pattern + " " + str(target.value / 100) + "\n")

        fp.close()

    def prepareClass(self):
        self.env.logLine(2, "Prepare class called with: " + self.env.basename)

        filename = os.path.join(self.dirname, "base.json")

        okay = self.glob.generateBaseSubDirs(self.env.basename)
        if not okay:
            return (False)

        self.baseInfo = self.env.readJSON(filename)
        if self.baseInfo is None:
            self.env.logLine(1, self.env.last_error )
            return (False)

        name = os.path.join(self.dirname, "base.obj")

        self.baseMesh = object3d(self.glob, self.baseInfo)
        (res, err) = self.baseMesh.load(name)
        if res is False:
            del self.baseMesh
            self.baseMesh = None
            self.env.last_error = err
            self.env.logLine(1, err )
            return (False)

        self.baseMesh.loadMaterial(None)

        if self.glob.Targets is not None:
            self.glob.Targets.destroyTargets()

        if self.glob.baseClass is not None:
            self.env.logLine(2, "class before: " + str(self.glob.baseClass.baseMesh))
            self.glob.reset()
            del self.glob.baseClass
        self.glob.baseClass = self

        self.baseMesh.precalculateDimension()
        target = Targets(self.glob)
        target.loadTargets()
        if "modifier-presets" in self.baseInfo:
            target.modifierPresets (self.baseInfo["modifier-presets"])
        #
        # attach the assets to the basemesh. TODO works only with system space!!!
        #
        if "meshes" in self.baseInfo:
            attach = attachedAsset(self.glob)

            m = self.baseInfo["meshes"]
            for elem in m:
                attach = attachedAsset(self.glob)
                name = os.path.join(self.env.path_sysdata, elem["cat"], self.env.basename, elem["name"])
                (res, text) = attach.textLoad(name)
                if res is True:
                    name = os.path.join(self.env.path_sysdata, elem["cat"], self.env.basename, attach.obj_file)
                    obj = object3d(self.glob, None)
                    (res, err) = obj.load(name)
                    if res is False:
                        self.env.logLine(1, err )
                        # TODO: error handling? Generate a list of errors?
                    else:
                        if attach.material is not None:
                            # TODO: error handling
                            obj.loadMaterial(attach.material)
                        attach.obj = obj
                        self.attachedAssets.append(attach)
                else:
                    print(text )
        else:
            self.attachedAssets = []
        memInfo()
        return (True)

    def getInitialCopyForSlider(self, factor, decr, incr):
        """
        get initial atm is only need for base, because the rest is done identically
        """
        self.baseMesh.getInitialCopyForSlider(factor, decr, incr)

    def updateAttachedAssets(self):
        for asset in self.attachedAssets:
            #
            # TODO: could be that the method will be moved to attached_asset
            #
            asset.obj.approxByTarget(asset, self.baseMesh)

    def updateByTarget(self, factor, decr, incr):
        """
        update all meshes by target
        """
        self.baseMesh.updateByTarget(factor, decr, incr)
        self.updateAttachedAssets()

    def setTarget(self, factor, decr, incr):
        """
        set all meshes by target
        """
        self.baseMesh.setTarget(factor, decr, incr)
        self.updateAttachedAssets()

    def applyAllTargets(self):
        #
        #
        self.baseMesh.resetMesh()
        targets = self.glob.Targets.modelling_targets
        if self.glob.targetMacros is not None:
            #
            # TODO: this dummy class method is not that good 
            #
            m = self.glob.targetMacros['macrodef']
            mo = Modelling(self.glob, "dummy", None, None)
            mo.macroCalculation(list(range(0,len(m))))
            
        for target in targets:
            if target.value != 0.0:
                if target.macro is None:
                    print ("Set " + target.name)
                    self.setTarget(target.value / 100, target.decr, target.incr)

    def __del__(self):
        self.env.logLine (4, " -- __del__ baseClass " + self.name)
