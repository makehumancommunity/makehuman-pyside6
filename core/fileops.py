import os
import json
from core.target import Targets
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
        self.object3d = None
        self.baseInfo = None
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

        self.object3d = object3d(self.env, self.baseInfo)
        self.env.logLine(3, "Load: " + name)
        (res, err) = importWaveFront(name, self.object3d)
        if res is False:
            del self.object3d
            self.object3d = None
            print (err)

        if self.glob.Targets is not None:
            self.glob.Targets.destroyTargets()

        if self.glob.baseClass is not None:
            print ("class before: " + str(self.glob.baseClass))
            del self.glob.baseClass
        self.glob.baseClass = self.object3d
        print(self.object3d)
        target = Targets(self.env, self.glob)
        target.loadTargets()
        memInfo()

    def __del__(self):
        self.env.logLine (4, " -- __del__ baseClass " + self.name)
