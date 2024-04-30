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
        self.matrixPoses = None

        # which channels are used, will contain index [-1, -1, -1, 0, 1, 2] = Xrotation, Yrotation, Zrotation
        #
        self.channelorder = [-1,-1,-1,-1,-1,-1]

        # offset
        #
        self.offset = np.zeros(3,dtype=np.float32)  # fixed relative offset

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
        self.frameCount = 1 # dummy frame

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


    def readJointHierarchy(self, joint, fp):
        (param, msg ) = self.keyParam('{', fp)
        if param is None:
            return (False, msg)

        (param, msg ) = self.keyParam('OFFSET', fp)
        if param is None:
            return (False, msg)

        # Calculate position from offset
        #
        joint.offset = [param[0], param[1], param[2]]

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
                child.offset = [param[0], param[1], param[2]]
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


    def eulerMatrix(self, ri, rj, rk):
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

    def fillFrames(self, frame, data):
        #
        i = 0
        for joint in self.bvhJointOrder:
            if joint.nChannels > 0:
                for j, m in enumerate(joint.channelorder):
                    if m>=0:
                        r = data[i+m]
                        if -0.0001 < r < 0.0001:
                            r = 0.0
                        joint.animdata[frame, j ] = r
                i += joint.nChannels
                joint.matrixPoses[frame,:3,:3] = self.eulerMatrix(joint.animdata[frame, 3], joint.animdata[frame, 4], joint.animdata[frame, 5])[:3,:3]


    def debugJoints(self):
        for joint in self.bvhJointOrder:
            print (joint)

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
                self.fillFrames(i, data)

        self.debugJoints()
        return (True, "Okay")

