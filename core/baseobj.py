import os
from core.target import Targets
from core.attached_asset import attachedAsset
from obj3d.fops_wavefront import importWaveFront
from obj3d.object3d import object3d
from core.debug import memInfo
from core.target import Modelling

class loadedMHM():
    def __init__(self):
        self.name = None
        self.modifiers = []

class baseClass():
    """
    get the environment for a base
    """
    def __init__(self, glob, name):
        self.env = glob.env
        self.glob = glob
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
            if key in ["version"]:
                setattr (loadedMHM, key, words[1])
            elif key == "name":
                loaded.name = " ".join(words[1:])
            elif key == "modifier":
                loaded.modifiers.append(" ".join(words[1:]))


        fp.close()

        if loaded.name is not None:
            self.name = loaded.name
        # reset all targets and mesh
        #
        self.glob.Targets.reset()

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

        basepath = os.path.join(self.env.path_sysdata, "base", self.env.basename)
        filename = os.path.join(basepath, "base.json")

        self.glob.generateBaseSubDirs(self.env.basename)

        self.baseInfo = self.env.readJSON(filename)
        if self.baseInfo is None:
            self.env.logLine(1, self.env.last_error )

        name = os.path.join(basepath, "base.obj")

        self.baseMesh = object3d(self.env, self.baseInfo)
        self.env.logLine(8, "Load: " + name)
        (res, err) = importWaveFront(name, self.baseMesh)
        if res is False:
            del self.baseMesh
            self.baseMesh = None
            self.env.logLine(1, err )

        if self.glob.Targets is not None:
            self.glob.Targets.destroyTargets()

        if self.glob.baseClass is not None:
            self.env.logLine(2, "class before: " + str(self.glob.baseClass.baseMesh))
            self.glob.reset()
            del self.glob.baseClass
        self.glob.baseClass = self
        target = Targets(self.glob)
        target.loadTargets()
        if "modifier-presets" in self.baseInfo:
            target.modifierPresets (self.baseInfo["modifier-presets"])
        #
        # attach the assets to the basemesh
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
                    self.env.logLine(8, "Load: " + name)
                
                    obj = object3d(self.env, None)
                    (res, err) = importWaveFront(name, obj)
                    if res is False:
                        self.env.logLine(1, err )
                    else:
                        attach.obj = obj
                        self.attachedAssets.append(attach)
                else:
                    print(text )
        else:
            self.attachedAssets = []
        memInfo()

    def getInitialCopyForSlider(self, factor, decr, incr):
        """
        get initial atm is only need for base, because the rest is done identically
        """
        self.baseMesh.getInitialCopyForSlider(factor, decr, incr)

    def updateByTarget(self, factor, decr, incr):
        """
        update all meshes by target
        """
        self.baseMesh.updateByTarget(factor, decr, incr)
        for asset in self.attachedAssets:
            #
            # TODO: could be that the method will be moved to attached_asset
            #
            asset.obj.approxByTarget(asset, self.baseMesh)

    def setTarget(self, factor, decr, incr):
        """
        set all meshe by target
        """
        self.baseMesh.setTarget(factor, decr, incr)
        for asset in self.attachedAssets:
            asset.obj.approxByTarget(asset, self.baseMesh)

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
                print ("Set " + target.name)
                if target.macro is None:
                    self.setTarget(target.value / 100, target.decr, target.incr)

    def __del__(self):
        self.env.logLine (4, " -- __del__ baseClass " + self.name)
