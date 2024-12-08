import numpy as np
import core.math as mquat
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
        self.filename = None
        self.channelname = {"Xposition":0, "Yposition":1, "Zposition":2, "Xrotation":3, "Yrotation":4, "Zrotation":5}
        self.bvhJointOrder = []
        self.joints = {}
        self.frameCount = 1       # one frame at least (could be rest pose), will contain number of frames
        self.frameTime = 0.041667 # preset that to 1/24 sec
        self.currentFrame = 0  # is used for animplayer
        self.pi_mult = math.pi / 180.0

        self.dislocation = False        # allow dislocation of bones (usually only root can be moved), also face has no dislocation
        self.z_up = True                # read in different direction

    def keyParam(self, key, fp):
        param = fp.readline().split()
        if param[0] != key:
            self.env.last_error = key + " expected in line " + " ".join(param)
            return None
        return param[1:]

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
        param = self.keyParam('CHANNELS', fp)
        if param is None:
            return False

        nChannels = int(param[0])
        if nChannels != len(param)-1:
            self.env.last_error = "BVH-File: Channels indicated and number of channels differ"
            return False

        for cnt, channel in enumerate(param[1:]):
            if channel in self.channelname:
                joint.channelorder[self.channelname[channel]] = cnt
        joint.nChannels = nChannels

        # TODO atm only lxyz-rxyz  and rxyz are allowed, the channel order determines the order of rotation 
        #
        if joint.channelorder != [0, 1, 2, 3, 4, 5] and joint.channelorder != [-1, -1, -1, 0, 1, 2] :
            self.env.last_error = "BVH-File: channel order not yet supported"
            return False
        return True

    def getOffset(self, param):
        if self.z_up:
            return ([float(param[0]), float(param[2]), -float(param[1])])
        else:
            return ([float(param[0]), float(param[1]), float(param[2])])

    def readJointHierarchy(self, joint, fp):
        if self.keyParam('{', fp) is None:
            return False

        param = self.keyParam('OFFSET', fp)
        if param is None:
            return False

        # Calculate position from offset
        #
        joint.offset = self.getOffset(param)
        if self.getChannelOrder(joint, fp) is False:
            return False

        # Read child joints
        while True:
            line = fp.readline()
            words = line.split()

            if words[0] == 'JOINT':
                child = self.addJoint(words[1], joint)
                if self.readJointHierarchy(child, fp) is False:
                    return False

            elif words[0] == 'End': # Site
                child = self.addJoint(None, joint)
                if self.keyParam('{', fp) is None:
                    return False

                param = self.keyParam('OFFSET', fp)
                if param is None:
                    return False

                child.offset = self.getOffset(param)
                if self.keyParam('}', fp) is None:
                    return False

            elif words[0] == '}':
                break
            else:
                self.env.last_error = "BVH-File: unexpected end of file."
                return False

        return True

    def initFrames(self):
        for joint in self.bvhJointOrder:
            joint.animdata = np.zeros(shape=(self.frameCount, 6), dtype=np.float32)
            joint.matrixPoses = np.zeros((self.frameCount,3,4), dtype=np.float32)
            joint.matrixPoses[:,:3,:3] = np.identity(3, dtype=np.float32)


    def calcLocRotMat(self, frame, data):
        #
        # works only for YZX joint order (rotation)
        i = 0
        order = "yzx"       # original yzx 
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
                    y = -self.pi_mult * joint.animdata[frame, 4]
                else:
                    y = self.pi_mult * joint.animdata[frame, 4]
                z = self.pi_mult * joint.animdata[frame, 5]

                joint.matrixPoses[frame,:3,:3] = mquat.eulerMatrix(z, y, x, order)[:3,:3]
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

    def debugJoints(self, name):
        for joint in self.bvhJointOrder:
            if joint.name == name:
                print (joint.name)
                print (joint.offset)
                print (joint.position)
                print (joint.matRestLocal)
                print (joint.matRestGlobal)
                print (joint.animdata)
                print (joint.matrixPoses)


    def calcBVHRestMat(self):
        for joint in self.bvhJointOrder:
            joint.calculateRestMat()

    def load(self, filename):
        self.filename = filename
        self.env.logLine(8, "Load pose " + filename)

        with open(filename, "r", encoding='utf-8') as fp:
            # starts with HIERARCHIE 
            # ROOT
            if self.keyParam('HIERARCHY', fp) is None:
                return False

            param = self.keyParam('ROOT', fp)
            if param is None:
                return False

            root = self.addJoint(param[0], None)   # add root joint
            if self.readJointHierarchy(root, fp) is False:
                return False

            # calculate BVH rest matrix and offset
            #
            self.calcBVHRestMat()

            if self.keyParam('MOTION', fp) is None:
                return False

            param = self.keyParam('Frames:', fp)
            if param is None:
                return False
            self.frameCount = int(param[0])

            param = self.keyParam('Frame', fp) # Time:
            if param is None:
                return False
            self.frameTime = float(param[1])

            self.initFrames()

            for i in range(self.frameCount):
                words = fp.readline().split()
                data = [float(word) for word in words]
                self.calcLocRotMat(i, data)

        # self.debugJoints("lowerarm02.L")
        return True

class MHPose():
    def __init__(self, glob, faceunits, name):
        self.glob = glob
        self.env = glob.env
        self.name = name
        self.description =""
        self.license =""
        self.author =""
        self.filename = None
        self.units = faceunits.units
        self.blends = []
        self.tags = []
        self.poses = {}

    def load(self, filename):
        self.filename = filename
        pose = self.env.readJSON(filename)
        if pose is None:
            return (False, self.env.last_error)

        for elem in pose["unit_poses"]:
            weight = pose["unit_poses"][elem]
            print (elem, weight)
            self.poses[elem] = weight
            if elem in self.units:
                if "bones" in self.units[elem]:
                    m = self.units[elem]["bones"]
                    self.blends.append([m, weight * 100])

        for elem in ("name", "author", "description", "tags", "license"):
            if elem in pose:
                setattr (self, elem, pose[elem])
            else:
                setattr (self, elem, "")
        
        return (True, "Okay")

    def save(self, filename, json):
        json["name"] = self.name
        return(self.env.writeJSON(filename, json))

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
        self.filterparam = []
        for elem in self.groups:
            self.filterparam.append(elem)
        return (self.filterparam)

    def load(self):
        filename =self.env.existDataFile("base", self.env.basename, "face-poses.json")
        if filename is None:
            return (False)

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
        return (True, "Okay")

