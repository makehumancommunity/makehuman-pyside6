import numpy as np
from obj3d.bone import cBone, boneWeights

class skeleton:
    def __init__(self, glob, name):
        self.glob = glob
        self.env  = glob.env
        self.name = name
        self.newSkeleton()

    def newSkeleton(self):
        self.jointVerts = {} # vertices for position (median calculation)
        self.planes = {}
        self.bones = {}      # list of cBones
        self.root = None     # our skeleton accepts one root bone, not more
        self.mesh = self.glob.baseClass.baseMesh

    def loadJSON(self, path):
        json = self.env.readJSON(path)
        if json is None:
            return False

        # check for main elements in json file:
        #
        for elem in ["joints", "bones"]:
            if elem not in json:
                self.env.logLine(1, "JSON " + elem + " is missing in " + path)
                return False

        # read joints into a list (avoid wrong types)
        #
        j = json["joints"]
        for name in j:
            val = j[name]
            if isinstance(val, list) and len(val) > 0:
                self.jointVerts[name] = val


        # read planes into a list
        #
        if "planes" in json:
            self.planes = json["planes"]

        # integrity test, all bones have a valid parent bone, one bone is root, rotation plane is valid,
        # head, tail are available
        #
        j = json["bones"]
        for bone in j:
            val = j[bone]
            if "head" not in val:
                self.env.logLine(1, "head is missing for " + bone + " in " + path)
                return False
            if "tail" not in val:
                self.env.logLine(1, "tail is missing for " + bone + " in " + path)
                return False

            if "rotation_plane" in val:
                plane = val["rotation_plane"]
                if plane in self.planes:
                    if self.planes[plane] == [None, None, None]:
                        self.env.logLine(1, "Invalid rotation plane " + plane + " in " + path)
                        return False
                else:
                    self.env.logLine(1, "Rotation plane " + plane + " is missing in " + path)
                    return False

            if "parent" in val and val["parent"] is not None:
                p = val["parent"]
                if p not in j:
                    self.env.logLine(1, "Parent bone of " + bone + ": " + p + " is missing in " + path)
                    return False

            else:
                if self.root is not None:
                    self.env.logLine(1, "Only one root accepted. Found: " + self.root + ", " + bone + " in " + path)
                    return False
                if "parent" not in val:
                    json["bones"][bone]["parent"] = None        # in case it is missing
                self.root = bone

        if self.root is None:
            self.env.logLine(1, "Missing root bone (bone without parent) in " + path)
            return False

        # read weights (either default or own)
        #
        weightname = json["weights_file"] if "weights_file" in json else "default_weights.mhw"
        weightfile = self.env.existDataFile("rigs", self.env.basename, weightname)
        if weightfile is None:
            self.env.logLine(1, "Missing weight file " + weightname)
            return False

        bWeights = boneWeights(self.glob, self.root)
        bWeights.loadJSON(weightfile)

        # array with ordered bones
        #
        orderedbones = [self.root]
        pindex = 0

        while pindex < len(j):
            if pindex < len(orderedbones):
                for bone in j:
                    if bone not in orderedbones:
                        val = j[bone]
                        if "parent" in val and val["parent"] == orderedbones[pindex]:
                            orderedbones.append(bone)
            pindex += 1

        for bone in orderedbones:
            val = j[bone]
            rotplane = val["rotation_plane"] if "rotation_plane" in val else 0
            reference = val["reference"] if "reference" in val else None
            weights = val["weights_reference"] if "weights_reference" in val else None
            cbone = cBone(self, bone, val, rotplane, reference, weights)
            self.bones[bone] = cbone

        """
        for bone in  self.bones:
            print (self.bones[bone])
        """

    def newJointPos(self):
        for bone in  self.bones:
            self.bones[bone].setJointPos()

