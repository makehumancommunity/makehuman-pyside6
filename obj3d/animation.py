
class BVHJoint():
    def __init__(self, name):
        self.name = name
        self.end = name is None
        self.channels = []

    def __repr__(self):
        return (self.name if self.name is not None else "end-site")

class BVH():
    def __init__(self, glob, name):
        self.glob = glob
        self.name = name
        self.bvhJointOrder = []
        self.joints = {}

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
        return (joint)

    def readJointHierarchy(self, joint, fp):
        (param, msg ) = self.keyParam('{', fp)
        if param is None:
            return (False, msg)

        (param, msg ) = self.keyParam('OFFSET', fp)
        if param is None:
            return (False, msg)

        # Calculate position from offset
        #
        offset = [float(x) for x in param]

        (param, msg ) = self.keyParam('CHANNELS', fp)
        if param is None:
            return (False, msg)
        nChannels = int(param[0])
        joint.channels = param[1:]
        if nChannels != len(joint.channels):
            return (False, "Channels indicated and number of channels differ")

        # Read child joints
        while True:
            line = fp.readline()
            words = line.split()

            if words[0] == 'JOINT':
                child = self.addJoint(words[1], joint.name)
                self.readJointHierarchy(child, fp)
            elif words[0] == 'End': # Site
                child = self.addJoint(None, joint.name)
                (param, msg ) = self.keyParam('{', fp)
                if param is None:
                    return (False, msg)
                (param, msg ) = self.keyParam('OFFSET', fp)
                if param is None:
                    return (False, msg)
                offset = [float(x) for x in param]
                (param, msg ) = self.keyParam('}', fp)
                if param is None:
                    return (False, msg)
            elif words[0] == '}':
                break
            else:
                return (False, "File seems shortened")

        return (True, "okay")

    def load(self, filename):
        print ("Load " + filename)

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

            for i in range(self.frameCount):
                words = fp.readline().split()
                data = [float(word) for word in words]
                print (len(data))

        print (self.bvhJointOrder)
        return (True, "Okay")

