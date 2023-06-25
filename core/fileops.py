import os
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
        print ("called for " + name)
        memInfo()
        self.env.basename = name


    def prepareClass(self):
        name = os.path.join(self.env.path_sysdata, "base", self.env.basename, "base.obj")
        self.object3d = object3d()
        (res, err) = importWaveFront(name, self.object3d)
        if res is False:
            del self.object3d
            self.object3d = None
            print (err)
        self.glob.baseClass = self.object3d
        print(self.object3d)
        target = Targets(self.env, self.glob)
        target.loadTargets()
        memInfo()


