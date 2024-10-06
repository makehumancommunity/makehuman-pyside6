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
        self.filename = None

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

        self.bWeights = boneWeights(self.glob, self.root, self.mesh)
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
            cbone = cBone(self, bone, val["parent"], val["head"], val["tail"], rotplane, reference, weights)
            self.bones[bone] = cbone

        """
        for bone in  self.bones:
            print (self.bones[bone])
        """
        self.calcRestMat()
        self.filename = path

    def copyScaled(self, source, scale, offset):
        """
        generate a resized skeleton
        """

        self.jointVerts = source.jointVerts
        self.bWeights = source.bWeights

        for bone in source.bones:
            b = source.bones[bone]

            cbone = cBone(self, b.name, b.parentname, b.head, b.tail, b.localplane, b.reference, b.weightref)
            head, tail = b.getJointPos()
            head = np.asarray(head, dtype=np.float32)
            tail = np.asarray(tail, dtype=np.float32)
            head[1] -= offset
            tail[1] -= offset
            cbone.assignJointPos(head * scale , tail * scale)
            self.bones[bone] = cbone

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
            if self.bones[bone].calcGlobalPoseMat() is False:
                return False
        return True

    def skinBasemesh(self):
        self.skinMesh(self.mesh, self.bWeights)

    def skinMesh(self, mesh, bWeights):
        vmapping = bWeights.bWeights

        coords = np.zeros((mesh.n_origverts,3), float)        # own vector
        l = len(mesh.gl_coord) // 3

        meshCoords = np.ones((l, 4), dtype=np.float32)
        meshCoords[:,:3] = np.reshape(mesh.gl_coord_w, (l,3))

        for bname in vmapping:
            bone = self.bones[bname]

            verts, weights = vmapping[bname]
            vec = np.dot(bone.matPoseVerts, meshCoords[verts].transpose())
            vec *= weights
            coords[verts] += vec.transpose()[:,:3]

        m = coords.flatten()
        mesh.gl_coord[:mesh.n_origverts*3] = m[:]
        mesh.overflowCorrection(mesh.gl_coord)


    def restPose(self, bones_only=False):
        for bone in self.bones:
            self.bones[bone].restPose()
            if self.bones[bone].calcGlobalPoseMat() is False:
                return False
            self.bones[bone].poseBone()

        # in case of restpose, pose with update function and not with pose function
        #
        if not bones_only:
            self.skinBasemesh()
            self.glob.baseClass.updateAttachedAssets()

    def pose(self, joints, num=0, bones_only=False):
        for elem in self.bones:
            if elem in joints:
                self.bones[elem].calcLocalPoseMat(joints[elem].matrixPoses[num])

            if self.bones[elem].calcGlobalPoseMat() is False:
                return False
            self.bones[elem].poseBone()

        if not bones_only:
            self.skinBasemesh()
            self.glob.baseClass.poseAttachedAssets()

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

            if self.bones[bone].calcGlobalPoseMat() is False:
                return False
            self.bones[bone].poseBone()

        if mask is not None:
            for bone in mask:
                if bone not in found:
                    self.bones[bone].restPose()
                    if self.bones[bone].calcGlobalPoseMat() is False:
                        return False
                    self.bones[bone].poseBone()

        if not bones_only:
            self.skinBasemesh()
            self.glob.baseClass.poseAttachedAssets()

