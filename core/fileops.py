import os
from PySide6.QtCore import QUrl

from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DRender import Qt3DRender


class waveObj():
    def __init__(self, rootentity):
        self.name = None
        self.rootentity = rootentity

    def load(self, name):
        obj = QUrl.fromLocalFile(name)
        baseMesh = Qt3DRender.QMesh(self.rootentity)
        baseMesh.setSource(obj)
        return (baseMesh)

class baseClass():
    def __init__(self, env):
        self.env = env
        self.name = None

    def loadDefault(self, rootentity, baseclass):
        name = os.path.join(self.env.path_sysdata, "base", baseclass, "base.obj")
        obj = waveObj(rootentity)
        return(obj.load(name))

