
import numpy as np

class cBone():
    def __init__(self, skel, name, val, roll=0, reference=None, weights=None):
        """
        headPos and tailPos should be in world space coordinates (relative to root).
        parent should be None for a root bone.
        """
        self.name = name
        self.skeleton = skel
        self.children = []
        self.reference = []
        self.weightref = None

        # sorted structure allows to add hierarchy to each bone, also add level
        #
        if val["parent"] is not None:
            self.parent = skel.bones[val["parent"]]
            self.parent.children.append(self)
            self.level = self.parent.level + 1
        else:
            self.parent = None
            self.level = 0

        self.head = val["head"]
        self.tail = val["tail"]
        self.roll = roll

        # coordinates for head and tail
        #
        self.headPos = np.zeros(3,dtype=np.float32)
        self.tailPos = np.zeros(3,dtype=np.float32)
        self.setInitialJointPos()

        # reference bones (used for mapped skeletons
        #
        if reference is not None:
            self.reference = reference

        if weights is not None:
            self.weightref = weights


    def __str__(self):
        return (self.name + " Level: " + str(self.level) + " Children " + str(len(self.children)))

    def setInitialJointPos(self):
        self.headPos[:] = self.skeleton.mesh.getMeanPosition(self.skeleton.jointVerts[self.head])
        self.tailPos[:] = self.skeleton.mesh.getMeanPosition(self.skeleton.jointVerts[self.tail])


class boneWeights():
    def __init__(self, glob, root):
        self.glob = glob
        self.env  = glob.env
        self.root = root
        self.bWeights = {}
        self.mesh = self.glob.baseClass.baseMesh

    def createWeightsPerBone(self, wdict):
        cnt = self.mesh.n_origverts


        # calculate sums to normalize weights
        #
        wtot = np.zeros(cnt, np.float32)
        for bone in wdict:
            g = wdict[bone]
            for item in g:
                vn,w = item
                wtot[vn] += w

        # calculate weights
        #
        for bone in wdict:
            g = wdict[bone]
            if len(g) == 0:
                continue
            verts = []
            weights = []
            for vn, w in g:
                verts.append(vn)
                weights.append(w / wtot[vn])
            verts = np.asarray(verts, dtype=np.uint32)
            weights = np.asarray(weights, np.float32)

            # Sort by vertex index
            #
            i_s = np.argsort(verts)
            verts = verts[i_s]
            weights = weights[i_s]

            # Filter out weights under the threshold
            #
            i_s = np.argwhere(weights > 1e-4)[:,0]
            verts = verts[i_s]
            weights = weights[i_s]
            self.bWeights[bone] = (verts, weights)

        # assign rest to root bone
        #
        if self.root not in wdict:
            vs = []
            ws = []
        else:
            vs,ws = self.bWeights[self.root]
            vs = list(vs)
            ws = list(ws)

        rw_i = np.argwhere(wtot == 0.0)[:,0]
        vs.extend(rw_i)
        ws.extend(np.ones(len(rw_i), dtype=np.float32))

        if len(rw_i) > 0:
            # get first 20 as an example if any
            text = ', '.join([str(s) for s in rw_i][:20])
            self.env.logLine(2, "Unweighted vertices assigned to:" + self.root + " " +  text)

        if len(vs) > 0:
            self.bWeights[self.root] = (np.asarray(vs, dtype=np.uint32), np.asarray(ws, dtype=np.float32))




    def loadJSON(self, path):
        json = self.env.readJSON(path)
        if json is None:
            return False

        for key in ["name", "version", "description"]:
            if key in json:
                print(json[key])
                setattr (self, key, json[key])

        if not "weights" in json:
            self.env.logLine(1, "JSON weights are missing in " + path)
            return False

        j = json["weights"]
        self.createWeightsPerBone (j)
        return True

