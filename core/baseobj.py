import os
from core.target import Targets
from core.attached_asset import attachedAsset
from obj3d.object3d import object3d
from obj3d.skeleton import skeleton
from obj3d.animation import BVH
from core.debug import memInfo, dumper
from core.target import Modelling
from gui.common import WorkerThread

class MakeHumanModel():
    def __init__(self):
        self.name = None
        self.uuid = None
        self.version = None
        self.skinMaterial = None
        self.modifiers = []
        self.attached = []
        self.materials = []
        self.tags = []

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
        self.cachedInfo = []
        self.attachedAssets = []
        self.env.logLine(2, "New baseClass: " + name)
        self.env.basename = name
        self.name = name                # will hold the character name
        self.reset()
        memInfo()

    def __str__(self):
        return(dumper(self))

    def reset(self):
        self.skinMaterialName = None
        self.skinMaterial = None
        self.proxy = None
        self.tags = [] 
        self.photo = None
        self.uuid = None

    def noAssetsUsed(self):
        for elem in self.cachedInfo:
            elem.used = False

    def markAssetByFileName(self, path, value):
        for elem in self.cachedInfo:
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
            if key in ["version", "uuid", "skinMaterial"]:
                setattr (loaded, key, words[1])
            elif key == "name":
                loaded.name = " ".join(words[1:])
            elif key == "tags":
                loaded.tags = " ".join(words[1:]).split(";")
            elif key == "modifier":
                loaded.modifiers.append(" ".join(words[1:]))
            elif key == "material":
                loaded.materials.append([words[1],  words[2], words[3]])
            elif key in ["clothes", "eyebrows", "eyelashes", "eyes", "hair", "teeth", "tongue", "proxy"]:

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
            for mapping in self.cachedInfo:
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
            if elem.relmaterial is not None:
                matfilename = self.env.existFileInBaseFolder(self.env.basename, elem.type, elem.name, elem.relmaterial)
                if matfilename is not None:
                    elem.material = matfilename

        if loaded.name is not None:
            self.name = loaded.name
        self.tags = loaded.tags
        self.uuid = loaded.uuid

        if loaded.skinMaterial is not None:
            self.skinMaterialName = loaded.skinMaterial
            matfilename = self.env.existDataFile("skins", self.env.basename, os.path.basename(loaded.skinMaterial))
            if matfilename is not None:
                self.baseMesh.loadMaterial(matfilename)
                self.skinMaterial = matfilename

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

        # finally mark MHM as used
        #
        self.markAssetByFileName(filename, True)
        return (True, "okay")

    def saveMHMFile(self, filename):
        self.env.logLine(8, "Save: " + filename)
        try:
            fp = open(filename, "w", encoding="utf-8", errors='ignore')
        except IOError as err:
            return (False, str(err))

        # create version as string, name from self.name or filename
        #
        vers = ".".join(map(str,self.env.release_info["version"]))
        name = self.name if  self.name != "" else os.path.split(filename[:-4])[-1]

        fp.write("# MakeHuman2 Model File\nversion v" + vers + "\nname " + name + "\n")

        # tags and uuid if available
        #
        if self.uuid is not None and self.uuid != "":
            fp.write ("uuid " + self.uuid + "\n")
        if len(self.tags) > 0:
            fp.write ("tags " + ";".join(self.tags) + "\n")

        # write targets
        #
        if self.glob.Targets is not None:
            for target in self.glob.Targets.modelling_targets:
                if target.value != target.default and target.pattern != "None":
                    fp.write ("modifier " + target.pattern + " " + str(round(target.value / 100, 6)) + "\n")

        # assets
        #
        for elem in self.attachedAssets:
            fp.write (elem.type + " " + elem.name + " " +  elem.uuid + "\n")

        # skinmaterial
        if self.skinMaterialName:
            fp.write ("skinMaterial " + self.skinMaterialName + "\n")

        # materials (elem.materialsource is None if material is unchanged, so no save)
        #
        for elem in self.attachedAssets:
            if  elem.materialsource is not None:
                fp.write ("material " + elem.name + " " +  elem.uuid + " " + elem.materialsource + "\n")
        
        fp.close()

    def calculateDeletedVerts(self):
        verts = None
        for elem in reversed(self.attachedAssets):
            if elem.deleteVerts is not None:
                if verts is None:
                    print ("First: " + elem.name)
                    verts = elem.deleteVerts.copy()
                    elem.obj.notHidden()
                else:
                    print ("Join: " + elem.name)
                    elem.obj.hideApproxVertices(elem, self.baseMesh, verts)
                    verts |= elem.deleteVerts
            else:
                if verts is not None:
                    print ("Join: " + elem.name)
                    elem.obj.hideApproxVertices(elem, self.baseMesh, verts)
                else:
                    elem.obj.notHidden()

        # start with base mesh only
        #
        if verts is None:
            self.baseMesh.notHidden()
        else:
            self.baseMesh.hideVertices(verts)

    def delAsset(self, filename):
        for elem in self.attachedAssets:
            if elem.filename == filename:
                self.glob.openGLWindow.deleteObject(elem.obj)
                self.attachedAssets.remove(elem)
                self.markAssetByFileName(filename, False)
                if elem.deleteVerts is not None:
                    print ("Need to recalculate base and other meshes because vertices are visible again")
                    self.calculateDeletedVerts()
                if elem.type == "proxy":
                    self.proxy  = None
                break

    def delProxy(self):
        for elem in self.attachedAssets:
            if elem.type == "proxy":
                self.glob.openGLWindow.deleteObject(elem.obj)
                self.attachedAssets.remove(elem)
                self.markAssetByFileName(elem.filename, False)
                self.proxy  = None
                break


    def addAsset(self, path, eqtype, materialpath=None, materialsource=None):
        print ("Attach: " + path + " of " + eqtype)
        attach = attachedAsset(self.glob, eqtype)
        attach.load(path)
        if attach is None:
            return (None)
        if eqtype == "proxy":
            attach.material = self.skinMaterial
            attach.materialsource = materialsource
            self.proxy = True
        elif materialpath is not None:
            attach.material = materialpath
            attach.materialsource = materialsource
        if attach.material is not None:
            attach.obj.loadMaterial(attach.material)

        # insert according to z-depth
        cnt = 0
        for elem in self.attachedAssets:
            if attach.z_depth < elem.z_depth:
                break
            cnt += 1
        self.attachedAssets.insert(cnt, attach)

        # do that always?
        #if attach.deleteVerts is not None:
        self.calculateDeletedVerts()

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

    def scanAssets(self, asset_type=None):
        if asset_type != "models":
            self.env.fileScanFoldersAttachObjects(asset_type)
        if asset_type is None or  asset_type  == "models":
            self.env.fileScanFolderMHM()
        self.cachedInfo = self.env.getCacheData()
        return(self.cachedInfo)

    def addSkeleton(self, name, path):
        self.skeleton = skeleton(self.glob, name)
        self.skeleton.loadJSON(path)

    def addPose(self, name, path):
        self.bvh = BVH(self.glob, name)
        loaded, msg  = self.bvh.load(path)
        if not loaded:
            self.env.logLine(1, "BVH: " + path + " " + msg)

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
        self.env.initFileCache()


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
        self.scanAssets()
        #for elem in self.cachedInfo:
        #    print (elem)

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

    def applyAllTargets(self, bckproc=None, args=None):
        """
        applies all targets and corrects attached assets
        """
        #self.baseMesh.resetMesh()
        targets = self.glob.Targets.modelling_targets
        self.baseMesh.addAllNonMacroTargets()

        if self.glob.targetMacros is not None:
            #
            # TODO: this dummy class method is not that good 
            #
            mo = Modelling(self.glob, "dummy", None)
            mo.macroCalculationLoad()
        self.updateAttachedAssets()


    def finishApply(self):
        self.glob.openGLWindow.Tweak()
        self.glob.parallel = None

    def parApplyTargets(self):
        """
        background process for applyAllTargets
        """
        if self.glob.parallel is None:
            self.glob.parallel = WorkerThread(self.applyAllTargets, None)
            self.glob.parallel.start()
            self.glob.parallel.finished.connect(self.finishApply)

    def __del__(self):
        self.env.logLine (4, " -- __del__ baseClass " + self.name)
