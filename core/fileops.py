import os
import json
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
        self.attached_objs = []
        env.logLine(2, "New baseClass: " + name)
        memInfo()
        self.env.basename = name
        self.name = name


    def prepareClass(self):
        print ("Prepare class called with: " + self.env.basename)

        basepath = os.path.join(self.env.path_sysdata, "base", self.env.basename)
        filename = os.path.join(basepath, "base.json")
        self.baseInfo = None
        #
        # TODO error handling
        #
        with open(filename, 'r') as f:
            self.baseInfo = json.load(f)
        
        name = os.path.join(basepath, "base.obj")

        self.baseMesh = object3d(self.env, self.baseInfo)
        self.env.logLine(3, "Load: " + name)
        (res, err) = importWaveFront(name, self.baseMesh)
        if res is False:
            del self.baseMesh
            self.baseMesh = None
            print (err)

        if self.glob.Targets is not None:
            self.glob.Targets.destroyTargets()

        if self.glob.baseClass is not None:
            print ("class before: " + str(self.glob.baseClass.baseMesh))
            del self.glob.baseClass
        self.glob.baseClass = self
        target = Targets(self.env, self.glob)
        target.loadTargets()
        #
        # TODO: still meshes, will be objects later (mhclo or mhpxy)
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
                    self.env.logLine(3, "Load: " + name)
                
                    obj = object3d(self.env, None)
                    (res, err) = importWaveFront(name, obj)
                    if res is False:
                        print (err)
                    else:
                        self.attached_objs.append(obj)
                else:
                    print(text)
        else:
            self.attached_objs = []
        memInfo()

    def __del__(self):
        self.env.logLine (4, " -- __del__ baseClass " + self.name)
