#
# class for randomizing a character
#
from numpy import random

class TargetRandomizer():
    def __init__(self, glob):
        self.glob = glob
        self.groups = {}            # all used groups
        self.nonsymgroups = {}      # precalculated non-symmetric groups
        self.symmetric = False      # symmetric: full symmetry
        self.ideaMin = 0.5          # minmum ideal value
        self.gender = 0             # 0 is both, 1 female, 2 male, 3 male or female
        self.gendName = None        # name for "gender" Macro/Slider
        self.idealName = None       # name for "ideal" Macro/Slider
        self.possibleGroups = {}    # possible groups from JSON file
        self.fromDefault = True     # use no standard values for all non-mentioned targets
        self.weirdofactor = 0.2     # value between 0 and 1 how much randomization should be used

        self.targetlist = []        # list of evaluated targets
        self.barycentrics = {}      # used of barycentric targets
        self.rules = {}

        bc = self.glob.baseClass
        bi = bc.baseInfo
        grps = []
        #
        # get infos from base.json 
        if "random" in bi:
            m= bi["random"]
            for name, key in m.items():
                if name == "nonsym":
                    self.setNonSymGroups(key)
                elif name == "gender":
                    self.gendName = key
                elif name == "ideal":
                    self.idealName = key
                elif name == "groups":
                    for sname, preselect in key.items():
                        self.possibleGroups[sname] = preselect
                        if preselect:
                            grps.append(sname)
                elif name == "rules":
                    for rname, rule in key.items():
                        self.rules[rname] = rule

        self.setGroups(grps)
        print (self.rules)

    def hasGender(self):
        return (self.gendName is not None)

    def hasIdeal(self):
        return (self.idealName is not None)

    def getGroups(self):
        return self.possibleGroups

    def setGroups(self, groups):
        self.groups = {}
        for elem in groups:
            if "|" in elem:
                key, group = elem.split("|", 2)
                if key in self.groups:
                    self.groups[key].append(group)
                else:
                    self.groups[key] = [group]
            else:
                self.groups[elem] = None

    def setWeirdoFactor(self, factor):
        self.weirdofactor = factor

    def setSym(self, ibool):
        self.symmetric = ibool

    def setIdealMinimum(self, value):
        self.idealMin = value

    def setFromDefault(self, ibool):
        self.fromDefault = ibool

    def setGender(self, gtype):
        self.gender = gtype

    def setNonSymGroups(self, groups):
        self.nonsymgroups = {}
        for elem in groups:
            self.nonsymgroups[elem] = 1

    def getTargetValue(self, name):

        # first check in new values
        #
        for t in self.targetlist:
            if t[1].name == name:
                return t[2]

        # then check standard values
        #
        for t in self.glob.targetRepo.values():
            if t.name == name:
                return t.value / 100

        return None

    def calculateRules(self, rule):
        for name, condition in rule.items():
            x = self.getTargetValue(name)
            if x is None:
                return False

            if eval(condition) is False:
                return False
        return True

    def applyRules(self):
        for elem, rule in self.rules.items():
            for t in self.targetlist:
                if t[1].name == elem:
                    if self.calculateRules(rule) is False:
                        print ("Reset:", t[1].name)
                        t[2] = 0.0

    def randomBaryCentric(self):
        x = random.rand()
        y = random.rand() * (1-x)
        z = 1 - x -y
        return [x, y, z]

    def randomValue(self, target):
        if target.decr is None or target.incr is None:
            if target.default != 0.0:
                modrange = 100-target.default if target.default > 50.0 else target.default
                x = (random.rand() * modrange * self.weirdofactor + target.default) / 100.0
            else:
                x = random.rand() * self.weirdofactor
            return x

        x = (1 - random.rand() * 2) * self.weirdofactor
        return x

    def randomGender(self, key, target):
        #
        # handle gender
        #
        if self.gender == 0:
            val  = random.rand() # weirdo factor to avoid in betweens?
        elif self.gender == 1:
            val = 0.0
        elif self.gender == 2:
            val = 1.0
        else:
            val = round(random.rand())
        print ("Gender:", val)
        self.targetlist.append([key, target, val])

    def randomProportions(self, key, target):
        factor = 1.0 - self.idealMin
        val = random.rand() * factor + self.idealMin
        self.targetlist.append([key, target, val])

    def addTarget(self, key, target):
        #
        # special cases first
        #
        if target.name == self.gendName:
            self.randomGender(key, target)
            return

        if target.name == self.idealName:
            self.randomProportions(key, target)
            return

        #
        # if symmetric, avoid non-symmetric targets
        #

        if self.symmetric:
            for s in self.nonsymgroups:
                if (target.decr is not None and target.decr.name.endswith(s)) or \
                    target.incr is not None and target.incr.name.endswith(s):
                    return

        #
        # in symmetric case set both values (here depending on symmetry)
        # ignore left side not to set them twice
        #
        if target.sym:
            if target.isRSide:
                oppositetarget = self.glob.targetRepo[target.sym]
                rnd = self.randomValue(target)
                self.targetlist.append([key, target, rnd])
                self.targetlist.append([target.sym, oppositetarget, rnd])
        else:
            if target.barycentric is not None:
                if target.name not in self.barycentrics:
                    bari = self.randomBaryCentric()
                    self.barycentrics[target.name] = target
                    i = 0
                    for elem in target.barycentric:
                        sname = elem["name"]
                        bartarget = self.glob.targetRepo[elem["name"]]
                        self.targetlist.append([elem["name"], bartarget, bari[i]])
                        i += 1
            else:
                rnd = self.randomValue(target)
                self.targetlist.append([key, target, rnd])

    def do(self):
        if self.glob.baseClass is None:
            print ("No base")
            return False
        if self.glob.targetRepo is None:
            print ("No Targets")
            return False

        if self.fromDefault:
            self.glob.Targets.reset()

        self.targetlist = []
        self.barycentrics = {}

        for key, target in self.glob.targetRepo.items():
            tg = target.group
            if not self.groups:                     # no group dictionary, so all elements
                self.addTarget(key, target)
            elif "|" in tg:
                group, sub = tg.split("|", 2)
                if group in self.groups:
                    if self.groups[group] is None:
                        self.addTarget(key, target)
                    else:
                        for subgroup in self.groups[group]:
                            if subgroup == sub:
                                self.addTarget(key, target)
        self.applyRules()
        return True

    def apply(self):
        for elem in self.targetlist:
            self.glob.Targets.setTargetByName(elem[0], elem[2])
        #
        # extra for skin-color
        for target in self.glob.targetRepo.values():
            if target.barycentric is not None:
                target.setBaryCentricDiffuse()
        self.glob.baseClass.parApplyTargets()

