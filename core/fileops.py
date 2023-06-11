import os
from core.target import Targets

class waveObj():
    def __init__(self):
        self.name = None

    def load(self, name):
        print ("Would load base mesh")
        return (baseMesh)

class baseClass():
    """
    get the environment for a base
    """
    def __init__(self, env, glob, name):
        self.env = env
        self.glob = glob
        print ("called for " + name)
        self.env.basename = name


    def loadBaseMesh(self):
        name = os.path.join(self.env.path_sysdata, "base", self.env.basename, "base.obj")
        obj = waveObj()
        return(obj.load(name))

    def prepareClass(self):
        target = Targets(self.env, self.glob)
        target.loadTargets()
