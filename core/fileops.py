import os
from core.target import Targets
from obj3d.fops_wavefront import importWaveFront


class baseClass():
    """
    get the environment for a base
    """
    def __init__(self, env, glob, name):
        self.env = env
        self.glob = glob
        print ("called for " + name)
        self.env.basename = name


    def prepareClass(self):
        name = os.path.join(self.env.path_sysdata, "base", self.env.basename, "base.obj")
        (res, err) = importWaveFront(name)
        if res is False:
            print (err)
        target = Targets(self.env, self.glob)
        target.loadTargets()
