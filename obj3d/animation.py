import numpy as np
import math

class BVHJoint():
    def __init__(self, name):
        self.name = name
        self.end = name is None
        self.parent = None
        self.nChannels = 0
        self.children = []
        self.animdata = None

        # which channels are used, will contain index [-1, -1, -1, 0, 1, 2] = Xrotation, Yrotation, Zrotation
        #
        self.channelorder = [-1,-1,-1,-1,-1,-1]

        # offset
        #
        self.offset = np.zeros(3,dtype=np.float32)  # fixed relative offset
        self.position = np.zeros(3,dtype=np.float32)  # global position
        self.matRestLocal = None
        self.matRestGlobal = None

        self.matrixPoses = None         # location/rotation matrices for complete animation

    def calculateRestMat(self):

        # Calculate absolute joint position
        if self.parent:
            self.position = np.add(self.parent.position, self.offset)
        else:
            self.position = self.offset[:]

        # Create relative rest matrix for joint (only translation)
        self.matRestLocal = np.identity(4, dtype=np.float32)
        self.matRestLocal[:3,3] = self.offset

        # Create world rest matrix for joint (only translation)
        self.matRestGlobal = np.identity(4, dtype=np.float32)
        self.matRestGlobal[:3,3] = self.position


    def __repr__(self):
        output = self.name if self.name is not None else "end-site"

        return (output + " " + str(self.channelorder) + " " + str(self.animdata))

class BVH():
    def __init__(self, glob, name):
        self.glob = glob
        self.env = glob.env
        self.name = name
        self.channelname = {"Xposition":0, "Yposition":1, "Zposition":2, "Xrotation":3, "Yrotation":4, "Zrotation":5}
        self.bvhJointOrder = []
        self.joints = {}
        self.frameCount = 1     # one frame at least (could be rest pose), will contain number of frames
        self.currentFrame = 0  # is used for animplayer
        self.pi_mult = math.pi / 180.0

        self.dislocation = False        # allow dislocation of bones (usually only root can be moved), also face has no dislocation
        self.z_up = True                # read in different direction

    def keyParam(self, key, fp):
        param = fp.readline().split()
        if param[0] != key:
            return (None, key + " expected in line " + " ".join(param))
        return (param[1:], param[0])

    def addJoint(self, name, parent):
        joint = BVHJoint(name)
        if name is not None:
            self.joints[name] = joint
        self.bvhJointOrder.append(joint)
        joint.parent = parent
        if parent is not None:
            parent.children.append(joint)
        return (joint)

    def getChannelOrder(self, joint, fp):
        (param, msg ) = self.keyParam('CHANNELS', fp)
        if param is None:
            return (False, msg)
        nChannels = int(param[0])
        if nChannels != len(param)-1:
            return (False, "Channels indicated and number of channels differ")
        for cnt, channel in enumerate(param[1:]):
            if channel in self.channelname:
                joint.channelorder[self.channelname[channel]] = cnt
        joint.nChannels = nChannels
        return (True, "okay")

    def getOffset(self, param):
        if self.z_up:
            return ([float(param[0]), float(param[2]), -float(param[1])])
        else:
            return ([float(param[0]), float(param[1]), float(param[2])])

    def readJointHierarchy(self, joint, fp):
        (param, msg ) = self.keyParam('{', fp)
        if param is None:
            return (False, msg)

        (param, msg ) = self.keyParam('OFFSET', fp)
        if param is None:
            return (False, msg)

        # Calculate position from offset
        #
        joint.offset = self.getOffset(param)
        (err, msg ) = self.getChannelOrder(joint, fp)
        if err is False:
            return (False, msg)

        # Read child joints
        while True:
            line = fp.readline()
            words = line.split()

            if words[0] == 'JOINT':
                child = self.addJoint(words[1], joint)
                self.readJointHierarchy(child, fp)
            elif words[0] == 'End': # Site
                child = self.addJoint(None, joint)
                (param, msg ) = self.keyParam('{', fp)
                if param is None:
                    return (False, msg)
                (param, msg ) = self.keyParam('OFFSET', fp)
                if param is None:
                    return (False, msg)

                child.offset = self.getOffset(param)
                (param, msg ) = self.keyParam('}', fp)
                if param is None:
                    return (False, msg)
            elif words[0] == '}':
                break
            else:
                return (False, "File seems shortened")

        return (True, "okay")

    def initFrames(self):
        for joint in self.bvhJointOrder:
            joint.animdata = np.zeros(shape=(self.frameCount, 6), dtype=np.float32)
            joint.matrixPoses = np.zeros((self.frameCount,3,4), dtype=np.float32)
            joint.matrixPoses[:,:3,:3] = np.identity(3, dtype=np.float32)


    def eulerMatrixXYZ(self, ri, rj, rk):
        M = np.identity(4)
        si, sj, sk = math.sin(ri), math.sin(rj), math.sin(rk)
        ci, cj, ck = math.cos(ri), math.cos(rj), math.cos(rk)
        cc, cs = ci*ck, ci*sk
        sc, ss = si*ck, si*sk

        M[0, 0] = cj*ck
        M[0, 1] = sj*sc-cs
        M[0, 2] = sj*cc+ss
        M[1, 0] = cj*sk
        M[1, 1] = sj*ss+cc
        M[1, 2] = sj*cs-sc
        M[2, 0] = -sj
        M[2, 1] = cj*si
        M[2, 2] = cj*ci
        return(M)

    def eulerMatrix(self, x, y, z, s="xyz"):
        if s == "xyz":
            return self.eulerMatrixXYZ(x, y, z)
        elif s == "xzy":
            return self.eulerMatrixXYZ(x, z, y)
        elif s == "yxz":
            return self.eulerMatrixXYZ(y, x, z)
        elif s == "yzx":
            return self.eulerMatrixXYZ(y, z, x)
        elif s == "zxy":
            return self.eulerMatrixXYZ(z, x, y)
        return self.eulerMatrixXYZ(z, y, x)

    def calcLocRotMat(self, frame, data):
        #
        # works only for XYZ joint order (rotation)
        i = 0
        order = "xyz"
        for joint in self.bvhJointOrder:
            if joint.nChannels > 0:
                for j, m in enumerate(joint.channelorder):
                    if m>=0:
                        r = data[i+m]
                        if -0.0001 < r < 0.0001:
                            r = 0.0
                        joint.animdata[frame, j ] = r
                i += joint.nChannels
                x = self.pi_mult * joint.animdata[frame, 3]
                #
                if self.z_up:
                    y = self.pi_mult * joint.animdata[frame, 5]
                    z = -self.pi_mult * joint.animdata[frame, 4]
                else:
                    y = self.pi_mult * joint.animdata[frame, 4]
                    z = self.pi_mult * joint.animdata[frame, 5]

                joint.matrixPoses[frame,:3,:3] = self.eulerMatrix(x, y, z, order)[:3,:3]
                #
                if joint.parent is None or self.dislocation:
                    joint.matrixPoses[frame,:3,3] = [joint.animdata[frame, 0], joint.animdata[frame, 1], joint.animdata[frame, 2]]


    def debugChanged(self):
        np.set_printoptions(precision=3, suppress=True)
        restmatrix= np.zeros((3,4), dtype=np.float32)
        restmatrix[:3,:3] = np.identity(3, dtype=np.float32)
        print ("Frame: " + str(self.currentFrame))
        for joint in self.bvhJointOrder:
            m = np.round(joint.matrixPoses[self.currentFrame], decimals=3)
            if not np.array_equiv(m,restmatrix):
                if np.where(~m.any(axis=0))[0] == 3:
                    s = list(m[:3,:3].flatten())
                else:
                    s = list(m.flatten())
                print("\"" + joint.name + "\": " + str(s))

    def debugJoints(self):
        for joint in self.bvhJointOrder:
            #print (joint)
            print (joint.name)
            print (joint.matrixPoses)
            #print (joint.matRestLocal)
            #print (joint.matRestGlobal)



    def calcBVHRestMat(self):
        for joint in self.bvhJointOrder:
            joint.calculateRestMat()

    def load(self, filename):
        self.env.logLine(1, "Load pose " + filename)

        with open(filename, "r", encoding='utf-8') as fp:
            # starts with HIERARCHIE 
            # ROOT
            (param, msg ) = self.keyParam('HIERARCHY', fp)
            if param is None:
                return (False, msg)
            (param, msg ) = self.keyParam('ROOT', fp)
            if param is None:
                return (False, msg)

            root = self.addJoint(param[0], None)   # add root joint
            (err, msg ) = self.readJointHierarchy(root, fp)
            if err is False:
                return (False, msg)

            # calculate BVH rest matrix and offset
            #
            self.calcBVHRestMat()

            (param, msg ) = self.keyParam('MOTION', fp)
            if param is None:
                return (False, msg)
            (param, msg ) = self.keyParam('Frames:', fp)
            if param is None:
                return (False, msg)

            self.frameCount = int(param[0])

            (param, msg ) = self.keyParam('Frame', fp) # Time:
            if param is None:
                return (False, msg)
            self.frameTime = float(param[1])

            self.initFrames()

            for i in range(self.frameCount):
                words = fp.readline().split()
                data = [float(word) for word in words]
                self.calcLocRotMat(i, data)

        return (True, "Okay")

class MHPose():
    def __init__(self, glob, faceunits, name):
        self.glob = glob
        self.env = glob.env
        self.name = name
        self.units = faceunits.units

    def load(self, filename):
        self.env.logLine(1, "Load pose " + filename)
        pose = self.env.readJSON(filename)
        if pose is None:
            return (False, self.env.last_error)

        for elem in pose["unit_poses"]:
            weight = pose["unit_poses"][elem]
            print (elem, weight)
            if elem in self.units:
                m = self.units[elem]
                for bone in m:
                    print ("    " + str(bone))
        return (True, "Okay")

class FaceUnits():
    def __init__(self, glob):
        self.glob = glob
        self.env = glob.env
        self.units = None
        self.filterparam = None
        self.groups   = []
        self.bonemask = []

    def __str__(self):
        return(str(self.units.keys()))

    def createFilterDict(self):
        self.filterparam = { "Face": {"group": "main", "items": [] }}

        for elem in self.groups:
            self.filterparam["Face"]["items"].append({"title": elem.capitalize(), "cat": elem})
        return (self.filterparam)

    def load(self):
        filename =self.env.existDataFile("base", self.env.basename, "face-poses.json")
        if filename is None:
            return (False)

        self.env.logLine(1, "Load face units " + filename)
        faceunits = self.env.readJSON(filename)
        if faceunits is None:
            return (False, self.env.last_error)

        # create a bone mask and collect groups, convert to posematrix

        for elem in faceunits:
            if "group" in faceunits[elem]:
                g = faceunits[elem]["group"]
                if g not in self.groups:
                    self.groups.append(g)

            if "bones" in faceunits[elem]:
                g =  faceunits[elem]["bones"]
                for bone in g:
                    g[bone] = np.asarray(g[bone], dtype=np.float32).reshape(3,3)
                    if bone not in self.bonemask:
                        self.bonemask.append(bone)
        self.units = faceunits
        print (faceunits)
        return (True, "Okay")

