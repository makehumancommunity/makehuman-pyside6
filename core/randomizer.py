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
        self.symmetric = False
        self.weirdofactor = 0.2

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

    def setNonSymGroups(self, groups):
        self.nonsymgroups = {}
        for elem in groups:
            self.nonsymgroups[elem] = 1

    def setRules(self, target, rule):
        # would be for things like pregnant / or create two passes (first age and gender, then rest)
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
            print ("single sided")
            return x

        x = (100 - random.rand() * 200) * self.weirdofactor
        return x

    def addTarget(self, key, target):
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
                bari = self.randomBaryCentric()
                # TODO does not yet work
                """
                i = 0
                for elem in target.barycentric:
                    elem["value"] = bari[i]
                    i += 1
                    #self.targetlist.append([elem["text"], elem["name"], bari[i]])
                """
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

        self.targetlist = []

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

        for elem in self.targetlist:
            print (elem[0], elem[1], elem[2])

    def test(self):
        # groups: 
        #self.setGroups(["shapes|female shapes", "shapes|female hormonal", "gender|breast", "face|right ear", "face|left ear", "torso"])
        self.setGroups(["main", "arms", "torso", "face", "legs"])
        self.setSym(True)
        self.setWeirdoFactor(0.5)
        self.setNonSymGroups(["trans-in", "trans-out"])
        self.do()

        self.glob.Targets.reset()
        for elem in self.targetlist:
            elem[1].value = elem[2]

        self.glob.baseClass.parApplyTargets()



