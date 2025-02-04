#
# this is still a testclass
#
from numpy import random

class TargetRandomizer():
    def __init__(self, glob):
        self.glob = glob
        self.groups = {}
        self.nonsymgroups = {}
        self.targetlist = []
        self.dedup = {}
        self.symmetric = False
        self.idealistic = False
        self.weirdofactor = 0.2
        self.gender = 0
        self.fromDefault = True

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
                x = random.rand() * modrange * self.weirdofactor + target.default
            else:
                x = random.rand() * 100 * self.weirdofactor
            return x

        x = (100 - random.rand() * 200) * self.weirdofactor
        return x

    def addTarget(self, key, target):
        #
        # special case, only males or females, or only ideal characters
        #
        if self.gender != 0 and target.name == "Gender":
            val = 0 if  self.gender == 1 else 100
            self.targetlist.append([key, target, val])
            return

        if self.idealistic and target.name == "Proportions":
            self.targetlist.append([key, target, 100])
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
            print (target.name)
            if target.barycentric is not None:
                bari = self.randomBaryCentric()
                # TODO does not yet work
                i = 0
                for elem in target.barycentric:
                    sname = elem["name"]
                    if sname not in self.dedup:
                        self.dedup[sname] =1
                        print (elem)
                        bartarget = self.glob.targetRepo[elem["name"]]
                        self.targetlist.append([elem["name"], bartarget, bari[i] * 100])
                        i += 1
            else:
                rnd = self.randomValue(target)
                self.targetlist.append([key, target, rnd])

    def do(self):
        if self.glob.baseClass is None:
            print ("No base")
            return
        if self.glob.targetRepo is None:
            print ("No Targets")
            return

        if self.fromDefault:
            self.glob.Targets.reset()

        self.targetlist = []
        self.dedup = {}

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
        self.do()

        for elem in self.targetlist:
            print (elem[0], elem[1], elem[2])
            elem[1].value = elem[2]

        self.glob.baseClass.parApplyTargets()



