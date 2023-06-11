import os
import json

class Modelling:
    def __init__(self, name, icon, tip):
        self.name = name
        self.icon = icon
        self.tip  = tip
        self.selected = False
        self.value = 0.0



class Targets:
    def __init__(self, env, glob):
        self.env = env
        self.modelling_targets = []
        glob.Targets = self

    def loadTargets(self):
        targetpath = os.path.join(self.env.path_sysdata, "target", self.env.basename)
        iconpath = os.path.join(targetpath, "icons")
        filename = os.path.join(targetpath, "modelling.json")

        with open(filename, 'r') as f:
            targetjson = json.load(f)
        for name in targetjson:
            t = targetjson[name]
            tip = t["tip"] if "tip" in t else "Select to modify"
            self.modelling_targets.append(Modelling(name, os.path.join(iconpath, t["icon"]), tip))


