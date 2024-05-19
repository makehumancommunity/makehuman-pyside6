import numpy as np
from obj3d.bone import cBone, boneWeights
import core.math as mquat

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
        self.bWeights = None
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

        self.bWeights = boneWeights(self.glob, self.root)
        self.bWeights.loadJSON(weightfile)

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
        self.calcRestMat()

    def getNormal(self, plane_name):
        """
        planes are used counter-clockwise
        returns normalized vector
        """
        if plane_name in self.planes:
            v = [None, None, None]
            for cnt, jointname in enumerate(self.planes[plane_name][:3]):
                v[cnt] = np.asarray(self.mesh.getMeanPosition(self.jointVerts[jointname]), dtype=np.float32)
            
            diff = v[1]-v[0]
            pvec = diff / np.linalg.norm(diff)
            diff = v[2]-v[1]
            yvec = diff / np.linalg.norm(diff)
            cross = np.cross(yvec, pvec)
            return (cross / np.linalg.norm(cross))
        else:
            return np.asarray([0,1,0], dtype=np.float32)

    def calcRestMat(self):
        for bone in self.bones:
            self.bones[bone].calcRestMatFromSkeleton()

    def newGeometry(self):
        """
        geometry changes, recalculate joint positions + rest matrix
        """
        for bone in  self.bones:
            self.bones[bone].setJointPos()
        self.calcRestMat()

    def calcLocalPoseMat(self, poses):
        for i, bone in  enumerate(self.bones):
            self.bones[bone].calcLocalPoseMat(poses[i])

    def calcGlobalPoseMat(self):
        for bone in  self.bones:
            self.bones[bone].calcGlobalPoseMat()


    def skinMesh(self):
        vmapping = self.bWeights.bWeights

        coords = np.zeros((self.mesh.n_origverts,3), float)        # own vector
        l = int(len(self.mesh.gl_coord) / 3)

        meshCoords = np.ones((l, 4), dtype=np.float32)
        meshCoords[:,:3] = np.reshape(self.mesh.gl_coord_w, (l,3))

        for bname in vmapping:
            bone = self.bones[bname]
            #
            # TODO: should not be None in the end
            #
            if bone.matPoseVerts is not None:
                verts, weights = vmapping[bname]
                vec = np.dot(bone.matPoseVerts, meshCoords[verts].transpose())
                vec *= weights
                coords[verts] += vec.transpose()[:,:3]

        m = coords.flatten()
        self.mesh.gl_coord[:self.mesh.n_origverts*3] = m[:]
        self.mesh.overflowCorrection(self.mesh.gl_coord)

    def restPose(self, bones_only=False):
        for bone in self.bones:
            self.bones[bone].restPose()
            self.bones[bone].calcGlobalPoseMat()
            self.bones[bone].poseBone()
        if not bones_only:
            self.skinMesh()
            self.glob.baseClass.updateAttachedAssets()

    def pose(self, joints, num=0, bones_only=False):
        for elem in self.bones:
            if elem in joints:
                self.bones[elem].calcLocalPoseMat(joints[elem].matrixPoses[num])

            self.bones[elem].calcGlobalPoseMat()
            self.bones[elem].poseBone()

        if not bones_only:
            self.skinMesh()
            self.glob.baseClass.updateAttachedAssets()

    def posebyBlends(self, blends, mask, bones_only=False):
        """
        function used for expressions, with mask set all unchanged bones will be set to rest position
        """
        if len(blends) == 0:
            return

        # check bonewise if blend is used, then use quaternionsSlerpFromMatrix with ratio to pose
        # in case the bone is posed by more than one posemat, multiply quaternion matrices
        #
        found = {}
        for bone in self.bones:
            modbone = False
            for blend in blends:
                posemat = blend[0]
                ratio = blend[1] / 100
                if bone in posemat:
                    found[bone] = True
                    if modbone is True:
                        q2 = mquat.quaternionSlerpFromMatrix(posemat[bone], ratio)
                        q1 = mquat.quaternionMult(q1, q2)
                    else:
                        q1 = mquat.quaternionSlerpFromMatrix(posemat[bone], ratio)
                    modbone = True

            if modbone is True:
                # print ("changed " + bone)
                mat = mquat.quaternionToRotMatrix(q1)
                self.bones[bone].calcLocalPoseMat(mat)

            self.bones[bone].calcGlobalPoseMat()
            self.bones[bone].poseBone()

        if mask is not None:
            for bone in mask:
                if bone not in found:
                    self.bones[bone].restPose()
                    self.bones[bone].calcGlobalPoseMat()
                    self.bones[bone].poseBone()

        if not bones_only:
            self.skinMesh()
            self.glob.baseClass.updateAttachedAssets()

