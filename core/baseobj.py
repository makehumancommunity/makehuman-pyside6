import os
from core.debug import dumper
from core.target import Targets
from core.attached_asset import attachedAsset
from obj3d.object3d import object3d
from core.debug import memInfo
from core.target import Modelling

class MakeHumanModel():
    def __init__(self):
        self.name = None
        self.version = None
        self.skinMaterial = None
        self.modifiers = []
        self.attached = []
        self.materials = []
        self.tags = []

    def __str__(self):
        return(dumper(self))

class mhcloElem():
    def __init__(self, name, uuid, path, folder, obj_file, thumbfile, author, tag):
        self.name = name
        self.uuid = uuid
        self.folder = folder
        self.path = path
        self.obj_file = os.path.join(os.path.dirname(path), obj_file)
        self.thumbfile = thumbfile
        self.author = author
        self.tag = tag
        self.used = False
        #
        # calculate expected npzfile
        #
        if obj_file.endswith(".obj"):
            obj_file = obj_file[:-3] + "npz"
        else:
            obj_file += ".npz"
        self.npz_file = os.path.join(os.path.dirname(path), "npzip", obj_file)

    def __str__(self):
        return(dumper(self))

class loadEquipment():
    """
    class to hold equipment while loading mhm to calculate absolute pathes and materials
    """
    def __init__(self, eqtype, name, uuid, path, materialpath, relmaterial):
        self.type =  eqtype
        self.name =  name
        self.uuid =  uuid
        self.path =  path
        self.material =  materialpath
        self.relmaterial =  relmaterial

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
        self.mhclo_namemap = []
        self.attachedAssets = []
        self.skinMaterial = None
        self.env.logLine(2, "New baseClass: " + name)
        memInfo()
        self.env.basename = name
        self.name = name                # will hold the character name
        self.tags = []                  # will hold the tags

    def noAssetsUsed(self):
        for elem in self.mhclo_namemap:
            elem.used = False

    def markAssetByFileName(self, path, value):
        for elem in self.mhclo_namemap:
            if elem.path == path:
                elem.used = value
                return

    def loadMHMFile(self, filename):
        """
        will usually load an mhm-file
        after load all filenames are absolute paths
        """
        self.env.logLine(8, "Load: " + filename)
        try:
            fp = open(filename, "r", encoding="utf-8", errors='ignore')
        except IOError as err:
            return (False, str(err))

        self.attachedAssets = []

        loaded = MakeHumanModel()
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
            elif key == "tags":
                loaded.tags = " ".join(words[1:]).split(";")
            elif key == "modifier":
                loaded.modifiers.append(" ".join(words[1:]))
            elif key == "material":
                loaded.materials.append([words[1],  words[2], words[3]])
            elif key in ["clothes", "eyebrows", "eyelashes", "eyes", "hair", "teeth", "tongue"]:

                # attached assets consists of name, type and uuid (material)
                #
                loaded.attached.append(loadEquipment(key, words[1], words[2], None, None, None))
            else:
                print (key + " is still unknown")

        fp.close()

        # get filename via mapping and connect relative material path to attached assets
        # set used assets in mapping
        #
        self.noAssetsUsed()
        for elem in loaded.attached:
            for mapping in self.mhclo_namemap:
                if elem.name == mapping.name and elem.uuid == mapping.uuid:
                    elem.path = mapping.path
                    mapping.used = True
            for mat in loaded.materials:
                if mat[0] == elem.name and mat[1] == elem.uuid:
                    elem.relmaterial = mat[2]
                    break

        del loaded.materials

        # set absolute path for material
        #
        for elem in loaded.attached:
            print (self.env.basename, elem.type, elem.name, elem.relmaterial)
            filename = self.env.existFileInBaseFolder(self.env.basename, elem.type, elem.name, elem.relmaterial)
            if filename is not None:
                elem.material = filename

        if loaded.name is not None:
            self.name = loaded.name
        self.tags = loaded.tags

        if loaded.skinMaterial is not None:
            self.skinMaterial = loaded.skinMaterial
            filename = self.env.existDataFile("skins", self.env.basename, os.path.basename(loaded.skinMaterial))
            if filename is not None:
                self.baseMesh.loadMaterial(filename, os.path.dirname(filename))

        print(loaded)

        # now load attached meshes
        #
        for elem in loaded.attached:
            if elem.path is not None:
                self.addAsset(elem.path, elem.type, elem.material, elem.relmaterial)

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

        # assets
        #
        for elem in self.attachedAssets:
            fp.write (elem.type + " " + elem.name + " " +  elem.uuid + "\n")

        # skinmaterial
        if self.skinMaterial:
            fp.write ("skinMaterial " + self.skinMaterial + "\n")

        # materials (elem.materialsource is None if material is unchanged, so no save)
        #
        for elem in self.attachedAssets:
            if  elem.materialsource is not None:
                fp.write ("material " + elem.name + " " +  elem.uuid + " " + elem.materialsource + "\n")
        
        fp.close()

    def loadMHCLO(self, filename, eqtype):
        """
        loads mhclo + object
        """
        attach = attachedAsset(self.glob, eqtype)
        (res, err) = attach.textLoad(filename)
        if res is True:
            print ("Object is:" + attach.obj_file)
            obj = object3d(self.glob, None)
            (res, err) = obj.load(attach.obj_file)
            if res is True:
                attach.obj = obj
                return (attach, None)

        self.env.logLine(1, err )
        return (None, err)

    def delAsset(self, filename):
        for elem in self.attachedAssets:
            if elem.filename == filename:
                self.glob.openGLWindow.deleteObject(elem.obj)
                self.attachedAssets.remove(elem)
                self.markAssetByFileName(filename, False)
                break

        # TODO check memory

    def addAsset(self, path, eqtype, materialpath=None, materialsource=None):
        print ("Attach: " + path)
        print ("Type: " + eqtype)
        (attach, err) = self.loadMHCLO(path, eqtype)
        if attach is None:
            return (None)
        if materialpath is not None:
            attach.material = materialpath
            attach.materialsource = materialsource
        if attach.material is not None:
            print ("Material: " + attach.material)
            attach.obj.loadMaterial(attach.material)
            self.attachedAssets.append(attach)
        return(attach)


    def addAndDisplayAsset(self, path, eqtype, multi):
        """
        attach an asset and propagate to OpenGL
        """

        # avoid same asset (should not happen)
        #
        for elem in  self.attachedAssets:
            if elem.filename == path:
                return

        if multi is False:
            for elem in self.attachedAssets:
                if elem.type == eqtype:
                    print ("Need to delete: " + elem.filename)
                    self.delAsset(elem.filename)

        asset = self.addAsset(path, eqtype)
        if asset is not None:
            self.markAssetByFileName(path, True)
            asset.obj.approxByTarget(asset, self.baseMesh)
            self.glob.openGLWindow.createObject(asset.obj)
            self.glob.openGLWindow.Tweak()

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

        self.mhclo_namemap = self.env.fileScanBaseFolder(".mhclo")
        for elem in self.mhclo_namemap:
            print (elem)

        name = os.path.join(self.dirname, "base.obj")

        self.baseMesh = object3d(self.glob, self.baseInfo)
        (res, err) = self.baseMesh.load(name)
        if res is False:
            del self.baseMesh
            self.baseMesh = None
            self.env.last_error = err
            self.env.logLine(1, err )
            return (False)

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
        self.attachedAssets = []

        # set here or/and in mhm
        #
        if "modifier-presets" in self.baseInfo:
            target.modifierPresets (self.baseInfo["modifier-presets"])

        if "mhm" in self.baseInfo:
            mhmfile = os.path.join(self.dirname, self.baseInfo["mhm"])
            self.loadMHMFile(mhmfile)
        else:
            self.baseMesh.loadMaterial(None)
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
                    self.baseMesh.setTarget(target.value / 100, target.decr, target.incr)
        self.updateAttachedAssets()

    def __del__(self):
        self.env.logLine (4, " -- __del__ baseClass " + self.name)
