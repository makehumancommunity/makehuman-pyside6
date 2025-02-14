"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck
"""
from numpy import random

class TargetRandomizer():
    """
    class for randomizing a character,
    old values can be stored and restored

    * parameters for this randomizer and gui are used from base/<mesh>/base.json
      which are:
      - selectable groups (as a complete group or a sub-group using group|subgroup)
      - non-symmetric suffixes
      - name of "gender" and "ideal"
      - rules

    * if a parameter is missing, slider will not be added by GUI, all values are multiplied by 100
    * enum gender   can be used to create only one gender, both genders or all in-between
        - gender is always used when it is set to 1-3, even when macro with 'Gender' is not selected
    * idealMin      (roportions) is a value of minimum "beauty"
        - idealMin  is always used when it is > 0.0, even when macro with 'Ideal' is not selected
    * symfactor     is a value between full symmetry (1.0) and no symmetry (0.0)
    * weirdofactor  is a value between no change at all (0.0) and fully random change (1.0)
    * fromDefault   means the character is reset to default before. Without that, non-selected groups are not changed at all

    this class is API callable
    """
    def __init__(self, glob):
        self.glob = glob
        self.groups = {}            # all used groups
        self.nonsymgroups = {}      # precalculated non-symmetric groups
        self.idealMin = 0.5         # minmum ideal value
        self.gender = 0             # 0 is both, 1 female, 2 male, 3 male or female
        self.gendset = False        # gender already found
        self.idealset = False       # ideal value already found
        self.gendName = None        # name for "gender" Macro/Slider
        self.idealName = None       # name for "ideal" Macro/Slider
        self.possibleGroups = {}    # possible groups from JSON file
        self.fromDefault = True     # use no standard values for all non-mentioned targets
        self.weirdofactor = 0.2     # value between 0 and 1 how much randomization should be used
        self.symfactor    = 1.0     # symmetry factor

        self.before = []            # keep the old values
        self.targetlist = []        # list of evaluated targets
        self.barycentrics = {}      # used of barycentric targets
        self.rules = {}

        bc = self.glob.baseClass
        bi = bc.baseInfo
        grps = []
        #
        # get infos from base.json, section "random"
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

    def storeAllValues(self):
        """
        store recent values (can be restored)
        """
        self.before = []
        bar = set()
        for key, target in self.glob.targetRepo.items():
            if target.barycentric is not None:
                if target.name not in bar:
                    for elem in target.barycentric:
                        sname = elem["name"]
                        bartarget = self.glob.targetRepo[elem["name"]]
                        self.before.append([elem["name"], bartarget,  elem["value"]])
                    bar.add(target.name)
            else:
                val = target.value / 100
                self.before.append([key, target, val])

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

    def setSym(self, factor):
        self.symfactor = factor

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

    def addNamedTarget(self, name):
        for key, t in self.glob.targetRepo.items():
            if (name == t.name):
                self.addTarget(key, t)
                return

    def getTargetValue(self, name):
        """
        gets target value of the new changed character, if there is none
        the non-changed value from the character itself
        """
        for t in self.targetlist:
            if t[1].name == name:
                return t[2]

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
        """
        tests if a target should be changed or set to 0. Example: pregnant males are not possible
        """
        for elem, rule in self.rules.items():
            for t in self.targetlist:
                if t[1].name == elem:
                    if self.calculateRules(rule) is False:
                        # print ("Reset:", t[1].name)
                        t[2] = 0.0

    def randomBaryCentric(self):
        x = random.rand()
        y = random.rand() * (1-x)
        z = 1 - x -y
        return [x, y, z]

    def randomValue(self, target):
        """
        get a random value for single or double-sided targets, returns 0 for single side targets, 1 for double sided
        """
        if target.decr is None or target.incr is None:
            if target.default != 0.0:
                modrange = 100-target.default if target.default > 50.0 else target.default
                x = (random.rand() * modrange * self.weirdofactor + target.default) / 100.0
            else:
                x = random.rand() * self.weirdofactor
            return x, 0

        x = (1 - random.rand() * 2) * self.weirdofactor
        return x, 1

    def randomGender(self, key, target):
        """
        handle gender
        HINT: one could also use weirdo factor to "reduce in betweens"
        """
        if self.gender == 0:
            val  = random.rand()
        elif self.gender == 1:
            val = 0.0
        elif self.gender == 2:
            val = 1.0
        else:
            val = round(random.rand())  # yields either 0 or 1
        self.targetlist.append([key, target, val])

    def randomProportions(self, key, target):
        """
        handle proportions
        """
        factor = 1.0 - self.idealMin
        val = random.rand() * factor + self.idealMin
        self.targetlist.append([key, target, val])

    def addTarget(self, key, target):
        #
        # special cases first, set gender if not already done
        #
        if target.name == self.gendName:
            if self.gendset is False:
                self.randomGender(key, target)
                self.gendset = True
            return

        if target.name == self.idealName:
            if self.idealset is False:
                self.randomProportions(key, target)
                self.idealset = True
            return

        #
        # non-symmetric groups are used not at all, when symfactor is > 0.99
        # or the randomvalue is multiplied by 1.0 - self.symfactor which yields
        # small values for non-symmetry, when symmetry is nearly 1.0
        #
        for s in self.nonsymgroups:
            if (target.decr is not None and target.decr.name.endswith(s)) or \
                target.incr is not None and target.incr.name.endswith(s):

                if self.symfactor > 0.99:
                    return
                else:
                    rnd, s = self.randomValue(target)
                    rnd = (1.0 - self.symfactor) * rnd
                    self.targetlist.append([key, target, rnd])
                    return

        #
        # if target has a symmetric 'partner' set both values (here depending on symmetry)
        # ignore left side not to set them twice
        #
        if target.sym:
            if target.isRSide:
                oppositetarget = self.glob.targetRepo[target.sym]
                rnd, s = self.randomValue(target)
                self.targetlist.append([key, target, rnd])
                if self.symfactor > 0.99:
                    # total symmetry
                    self.targetlist.append([target.sym, oppositetarget, rnd])
                else:
                    # symmetry, get a second random value between minimum and max
                    # s == 0 is single sided slider
                    #
                    if s == 0:
                        d = (random.rand() - 0.5) * (1.0 - self.symfactor) # -0.5 to create -0.5 to 0.5
                        lower = 0.0
                    else:
                        d = (1 - random.rand() * 2) * (1.0 - self.symfactor)
                        lower = 1.0
                    #
                    # use values either between min and rnd or rnd and max
                    # and calculate rnd2 by multiplying the distance between min/rnd or rnd/max
                    #
                    if d < 0.0:
                        rnd2 = (lower + rnd) * d + rnd
                    else:
                        rnd2 = (1.0 - rnd) * d + rnd
                    # 
                    # should not happen :P
                    if rnd2 < -lower or rnd2 > 1.0:
                        rnd2 = rnd
                    self.targetlist.append([target.sym, oppositetarget, rnd2])
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
                rnd, dummy = self.randomValue(target)
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

        self.gendset = False
        self.idealset = False
        self.targetlist = []
        self.barycentrics = {}

        # make sure gender and proportions are used, in case macro is not used
        #
        if self.gender != 0:
            self.addNamedTarget(self.gendName)

        if self.idealMin > 0.0:
            self.addNamedTarget(self.idealName)

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

    def _applyList(self, tlist, api=False):
        for elem in tlist:
            self.glob.Targets.setTargetByName(elem[0], elem[2])

        # API is not allowed to run in thread or set diffuse colors
        if api:
            self.glob.baseClass.nonParApplyTargets()
        else:
            self.glob.baseClass.parApplyTargets()
            self.glob.Targets.setSkinDiffuseColor()

    def apply(self, api=False):
        self._applyList(self.targetlist, api)

    def restore(self):
        self._applyList(self.before)

