#
# this is still a testclass
#
class TargetRandomizer():
    def __init__(self, glob):
        self.glob = glob
        self.groups = {}
        self.nonsymgroups = {}
        self.targetlist = []
        self.symmetric = False

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

    def setSym(self, ibool):
        self.symmetric = ibool

    def setNonSymGroups(self, groups):
        self.nonsymgroups = {}
        for elem in groups:
            self.nonsymgroups[elem] = 1

    def setRules(self, target, rule):
        # would be for things like pregnant / or create two passes (first age and gender, then rest)
        pass

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
                self.targetlist.append([key, target])
                self.targetlist.append(["opposite", target.sym])
        else:
            self.targetlist.append([key, target])

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
            print (elem[0], elem[1])

    def test(self):
        self.setGroups(["shapes|female shapes", "shapes|female hormonal", "gender|breast", "face|right ear", "face|left ear", "torso"])
        self.setSym(True)
        self.setNonSymGroups(["trans-in", "trans-out"])
        self.do()

