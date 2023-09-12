import os
import sys
import json
import numpy as np

class Modelling:
    def __init__(self, name, obj, refreshwindow, icon, tip):
        self.name = name
        self.icon = icon
        self.tip  = tip
        self.obj  = obj
        self.refresh = refreshwindow
        self.selected = False
        self.value = 0.0
        self.up   = None    # target "up"
        self.down = None    # target "down"
        self.displayname = name
        self.group = None

    def __str__(self):
        return (self.name + ": " + str(self.up) + "/" + str(self.down))

    def up_target(self, fname):
        self.up = fname

    def down_target(self, fname):
        self.down = fname

    def set_refresh(self,refreshwindow):
        self.refresh = refreshwindow

    def set_displayname(self, name):
        self.displayname = name

    def set_group(self, name):
        self.group = name

    def callback(self):
        factor = self.value / 100
        print("change " + self.name)
        if self.up is not None and self.down is not None:
            self.obj.updateByTarget(factor, self.down, self.up)
            self.refresh.Tweak()

    #def __del__(self):
    #    print (" -- __del__ Modelling: " + self.name)


class Morphtarget:
    """
    handle a single target
    """
    def __init__(self, env, name):
        self.dtype = [('index','u4'),('vector','(3,)f4')]
        self.name = name
        self.raw  = None
        self.verts= None
        self.data = []
        self.env  = env

    def __str__(self):
        return (self.name)

    def loadTextFile(self, path):
        filename = os.path.join(path, self.name)
        try:
            fd = open(filename, 'r', encoding='utf-8')
        except:
            self.env.logLine(1, "Cannot load:" + filename)
        else:
            self.env.logLine(3, "Load: " + filename)
            for line in fd:
                line = line.strip()
                if line.startswith('#'):
                    continue
                translationData = line.split()
                if len(translationData) != 4:
                    continue
                vertIndex = int(translationData[0])
                translationVector = (float(translationData[1]), float(translationData[2]), float(translationData[3]))
                self.data.append((vertIndex, translationVector))
            self.raw = np.asarray(self.data, dtype=self.dtype)
            self.verts = self.raw['index']
            self.data = self.raw['vector']

    def releaseNumpy(self):
        if self.raw is not None:
            self.verts = None
            self.raw = None
            self.data = []

    def __del__(self):
        self.env.logLine(4, " -- __del__ Morphtarget: " + self.name)


class Targets:
    def __init__(self, env, glob):
        self.env = env
        self.modelling_targets = []
        glob.Targets = self
        self.collection = None
        self.object3d = glob.baseClass
        self.graphwindow = glob.graphwindow

    def __str__(self):
        return ("Target-Collection: " + str(self.collection))

    def loadTargets(self):
        targetpath = os.path.join(self.env.path_sysdata, "target", self.env.basename)
        iconpath = os.path.join(targetpath, "icons")
        filename = os.path.join(targetpath, "modelling.json")
        self.collection = self.env.basename

        targetjson = self.env.readJSON(filename)
        if targetjson is None:
            self.env.logLine(1, self.env.last_error )
            return

        for name in targetjson:
            t = targetjson[name]
            tip = t["tip"] if "tip" in t else "Select to modify"
            m = Modelling(name, self.object3d, self.graphwindow, os.path.join(iconpath, t["icon"]), tip)
            if "down" in t:
                mt = Morphtarget(self.env, t["down"])
                mt.loadTextFile(targetpath)
                m.down_target(mt)
            if "up" in t:
                mt = Morphtarget(self.env, t["up"])
                mt.loadTextFile(targetpath)
                m.up_target(mt)
            if "name" in t:
                m.set_displayname(t["name"])
            if "group" in t:
                m.set_group(t["group"])
            self.modelling_targets.append(m)

    def refreshTargets(self, window):
        """
        refreshes Callbacks
        """
        for target in self.modelling_targets:
            target.set_refresh(window)

    def destroyTargets(self):
        self.env.logLine (2, "destroy Targets:" + str(self.collection))

        for m in self.modelling_targets:
            if m.up:
                m.up.releaseNumpy()
            if m.down:
                m.down.releaseNumpy()

        self.modelling_targets = []

    def __del__(self):
        self.env.logLine (4, " -- __del__ Targets: " + self.collection)
