import os
from core.target import Targets
from core.attached_asset import attachedAsset
from obj3d.fops_wavefront import importWaveFront
from obj3d.object3d import object3d
from core.debug import memInfo

class baseClass():
    """
    get the environment for a base
    """
    def __init__(self, env, glob, name):
        self.env = env
        self.glob = glob
        self.baseMesh = None
        self.baseInfo = None
        self.attachedAssets = []
        env.logLine(2, "New baseClass: " + name)
        memInfo()
        self.env.basename = name
        self.name = name


    def prepareClass(self):
        self.env.logLine(2, "Prepare class called with: " + self.env.basename)

        basepath = os.path.join(self.env.path_sysdata, "base", self.env.basename)
        filename = os.path.join(basepath, "base.json")

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
            self.glob.freeTextures()
            del self.glob.baseClass
        self.glob.baseClass = self
        target = Targets(self.env, self.glob)
        target.loadTargets()
        #
        # attach the assets to the basemesh
        #
        if "meshes" in self.baseInfo:
            attach = attachedAsset(self.env, self.glob)

            m = self.baseInfo["meshes"]
            for elem in m:
                attach = attachedAsset(self.env, self.glob)
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
            # TODO: could be that the method will be to attached_asset
            #
            asset.obj.approxByTarget(asset, self.baseMesh)

    def __del__(self):
        self.env.logLine (4, " -- __del__ baseClass " + self.name)
