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
        self.idealistic = False     # true: proportions set to 100 %
        self.gender = 0             # 0 is both, 1 female, 2 male
        self.fromDefault = True     # use no standard values for all non-mentioned targets
        self.weirdofactor = 0.2     # value between 0 and 1 how much randomization should be used

        self.targetlist = []        # list of evaluated targets
        self.barycentrics = {}      # used of barycentric targets

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

    def setIdeal(self, ibool):
        self.idealistic = ibool

    def setFromDefault(self, ibool):
        self.fromDefault = ibool

    def setGender(self, text):
        if text.startswith("f"):
            self.gender = 1
        elif text.startswith("m"):
            self.gender = 2
        else:
            self.gender = 0

    def setNonSymGroups(self, groups):
        self.nonsymgroups = {}
        for elem in groups:
            self.nonsymgroups[elem] = 1

    def setRules(self, target, rule):
        # would be for things like pregnant / or create two passes (first age and gender, then rest)
        # also sth like when male, no gender breast
        pass

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

    def addTarget(self, key, target):
        #
        # special case, only males or females, or only ideal characters
        #
        if self.gender != 0 and target.name == "Gender":
            val = 0.0 if  self.gender == 1 else 1.0
            self.targetlist.append([key, target, val])
            return

        if self.idealistic and target.name == "Proportions":
            self.targetlist.append([key, target, 1.0])
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
                self.targetlist.append(["opposite", oppositetarget, rnd])
        else:
            if target.barycentric is not None:
                if target.name not in self.barycentrics:
                    bari = self.randomBaryCentric()
                    self.barycentrics[target.name] = target
                    print ("Targetname:", target.name)
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
        return True

    def apply(self):
        for elem in self.targetlist:
            self.glob.Targets.setTargetByName(elem[0], elem[2])
        for elem, target in self.barycentrics.items():
            target.setBaryCentricDiffuse()
        self.glob.baseClass.parApplyTargets()

    def test(self):
        # groups: 
        #self.setGroups(["shapes|female shapes", "shapes|female hormonal", "gender|breast", "face|right ear", "face|left ear", "torso"])
        #self.setGroups(["main", "arms", "torso", "face", "legs", "gender|breast"])
        self.setGroups(["main", "arms", "torso", "face", "legs"])
        self.setSym(True)
        self.setIdeal(True)
        self.setFromDefault(False) # no reset, reuse what is set manually
        self.setGender("female")
        self.setWeirdoFactor(0.2)
        self.setNonSymGroups(["trans-in", "trans-out"])
        if self.do():
            self.apply()


