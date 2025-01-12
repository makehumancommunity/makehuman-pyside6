
import numpy as np
import core.math as mquat

class cBone():
    def __init__(self, skel, name, parent, head, tail, localplane=0, reference=None, weights=None):
        """
        headPos and tailPos should be in world space coordinates (relative to root).
        parent should be None for a root bone.
        """
        self.glob = skel.glob
        self.parentname = parent
        self.name = name
        self.skeleton = skel
        self.children = []
        self.reference = []
        self.weightref = None

        # sorted structure allows to add hierarchy to each bone, also add level
        #
        if parent is not None:
            self.parent = skel.bones[parent]
            self.parent.children.append(self)
            self.level = self.parent.level + 1
        else:
            self.parent = None
            self.level = 0

        self.head = head
        self.tail = tail
        self.localplane = localplane

        # coordinates for head and tail
        #
        self.headPos = np.zeros(3,dtype=np.float32)
        self.tailPos = np.zeros(3,dtype=np.float32)
        self.setJointPos()

        # same for posing
        #
        self.poseheadPos = np.zeros(3,dtype=np.float32)
        self.posetailPos = np.zeros(3,dtype=np.float32)

        # reference bones (used for mapped skeletons)
        #
        if reference is not None:
            self.reference = reference

        if weights is not None:
            self.weightref = weights

        self.matRestGlobal = None       # rest Pose, global position 4x4 Matrix of bone object
        self.matRestLocal = None        # rest Pose, relative (local)  position 4x4 Matrix of bone object

        self.matPoseGlobal = None                       # global pose matrix
        self.matPoseLocal = np.identity(4, np.float32)  # relative pose matrix

        self.matPoseVerts = None                        # TODO not yet clear

        self.length = 0                 # length of bone

    def __str__(self):
        return (self.name + " Level: " + str(self.level) + " Children " + str(len(self.children)))

    def debugMats(self):
        print ("Debug for:" + self.name)
        print ("Rest-Global:")
        print (self.matRestGlobal)
        print ("Rest-Local:")
        print (self.matRestLocal)

    def getRestLocalRotQVector(self):
        return mquat.quaternionFromMatrix(self.matRestLocal)    # yields the rotation for bones

    def getPoseLocalRotQVector(self):
        return mquat.quaternionFromMatrix(self.matPoseLocal)    # yields the rotation for bones in Pose mode

    def getPoseGlobalRotQVector(self):
        return mquat.quaternionFromMatrix(self.matPoseGlobal)    # yields the rotation for bones in Pose mode

    def getRestLocalTransVector(self):         # return first 3 elements of last column 
        return self.matRestLocal[:3,3]

    def getRestGlobalTransVector(self):         # return first 3 elements of last column 
        return self.matRestGlobal[:3,3]

    def getPoseLocalTransVector(self):         # return first 3 elements of last column in Pose mode
        return self.matPoseLocal[:3,3]

    def getPoseGlobalTransVector(self):         # return first 3 elements of last column in Pose mode
        return self.matPoseGlobal[:3,3]

    def getBindMatrix(self, orientation=0, rotAxis='y', offset=[0,0,0]):
        """
        this is used for export mainly
        """
        restmat = self.getTransformedRestMatrix(orientation, rotAxis, offset)
        bindinv = np.transpose(restmat)
        bindmat = np.linalg.inv(bindinv)
        return bindmat,bindinv

    def getTransformedRestMatrix(self, orientation=0, rotAxis='y', offset=[0,0,0]):
        return mquat.changeOrientation(self.matRestGlobal, orientation, rotAxis, offset)


    def getNormal(self):
        """
        return normal from skeleton
        """
        # TODO: better inside skeleton?!

        normal = None
        if isinstance(self.localplane, list):
            print ("List:" + str(self.localplane))
        elif isinstance(self.localplane, str):
            normal = self.skeleton.getNormal(self.localplane)

        if normal is None or np.allclose(normal, np.zeros(3), atol=1e-05):
            normal = np.asarray([0.0, 1.0, 0.0], dtype=np.float32)

        return (normal)

    def assignJointPos(self, head, tail):
        self.headPos[:] = head
        self.tailPos[:] = tail

    def getJointPos(self):
        return (self.skeleton.mesh.getMeanPosition(self.skeleton.jointVerts[self.head]), \
                self.skeleton.mesh.getMeanPosition(self.skeleton.jointVerts[self.tail]))

    def setJointPos(self):
        self.headPos[:] = self.skeleton.mesh.getMeanPosition(self.skeleton.jointVerts[self.head])
        self.tailPos[:] = self.skeleton.mesh.getMeanPosition(self.skeleton.jointVerts[self.tail])

    def calcLocalRestMat(self, normal):

        mat = np.identity(4, dtype=np.float32)

        # create a normalized bone vector
        #
        diff = self.tailPos - self.headPos
        self.length = np.linalg.norm(diff)
        bone_direction = diff / self.length

        # orthonormal base, perpendicular vector to normal / bone_direction needed (cross-product)
        #
        cross = np.cross(normal, bone_direction)
        z_axis = cross / np.linalg.norm(cross)

        # one axis missing, so same with z_axis / bone_direction
        #
        cross = np.cross(bone_direction, z_axis)
        x_axis = cross / np.linalg.norm(cross)

        # Now we construct our orthonormal base
        mat[:3,0] = x_axis[:3]          # bone local X axis
        mat[:3,1] = bone_direction[:3]  # bone local Y axis
        mat[:3,2] = z_axis[:3]          # bone local Z axis
        mat[:3,3] = self.headPos[:3]            # head position as translation
        return mat


    def calcRestMatFromSkeleton(self):
        normal = self.getNormal()
        self.matRestGlobal = self.calcLocalRestMat(normal)
        if self.parent:
            self.matRestLocal = np.dot(np.linalg.inv(self.parent.matRestGlobal), self.matRestGlobal)
        else:
            self.matRestLocal = self.matRestGlobal


    def restPose(self):
        self.matPoseLocal = np.identity(4, dtype=np.float32)

    def calcLocalPoseMat(self, poseMat):
        self.matPoseLocal = np.identity(4, dtype=np.float32)

        # Calculate rotations
        self.matPoseLocal[:3,:3] = poseMat[:3,:3]
        invRest = np.linalg.inv(self.matRestGlobal)            # TODO precalculate this one time maybe
        self.matPoseLocal = np.dot(np.dot(invRest, self.matPoseLocal), self.matRestGlobal)

        # Add translations from original
        if poseMat.shape[1] == 4:
            # Note: we generally only have translations on the root bone
            trans = poseMat[:3,3]
            # print (self.name + " " + str(trans))
            trans = np.dot(invRest[:3,:3], trans.T)  # Describe translation in bone-local axis directions
            self.matPoseLocal[:3,3] = trans.T
        else:
            # No translation
            self.matPoseLocal[:3,3] = [0, 0, 0]

    def calcGlobalPoseMat(self):
        if self.parent:
            self.matPoseGlobal = np.dot(self.parent.matPoseGlobal, np.dot(self.matRestLocal, self.matPoseLocal))
        else:
            self.matPoseGlobal = np.dot(self.matRestLocal, self.matPoseLocal)

        try:
            self.matPoseVerts = np.dot(self.matPoseGlobal, np.linalg.inv(self.matRestGlobal))
        except:
            self.glob.env.logLine(1, "Cannot calculate pose verts matrix for bone " + self.name)
            self.glob.env.logLine(1, "Non-singular rest matrix " + str(self.matRestGlobal))
            return False
        return True

    def poseBone(self):
        m = np.ones(4)
        m[:3] = self.headPos
        vec = np.dot(self.matPoseVerts, m.transpose())
        self.poseheadPos = vec.transpose()[:3]
        m = np.ones(4)
        m[:3] = self.tailPos
        vec = np.dot(self.matPoseVerts, m.transpose())
        self.posetailPos = vec.transpose()[:3]



class boneWeights():
    def __init__(self, glob, default_skeleton, mesh):
        self.glob = glob
        self.env  = glob.env
        self.default_skeleton = default_skeleton
        self.root = default_skeleton.root
        self.bWeights = {}
        self.mesh = mesh

    def createWeightsPerBone(self, wdict):
        cnt = self.mesh.n_origverts

        # calculate sums to normalize weights
        #
        wtot = np.zeros(cnt, np.float32)

        for bone, g in wdict.items():
            for item in g:
                vn,w = item
                wtot[vn] += w

        # calculate weights
        #
        for bone, g in wdict.items():
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
        if self.root not in self.bWeights:
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

    def sortWeights(self, weights):
        """
        when using a custom skeleton, one bone may contain more than one bone of the
        default skeleton, call sortWeights, since deduplication is only working on sorted arrays
        """
        for bone in weights:
            v, w = weights[bone]
            i_s = np.argsort(v)
            v = v[i_s]
            w = w[i_s]
            weights[bone] = (v,w)
        return weights

    def deDuplicateWeights(self, weights):
        """
        weight arrays must be sorted
        for assets weights are calculated using 3 values from the base mesh, this means that values are used multiple times
        the skinning algorithm expects them once. This procedure is doing that by using np.unique to get occurences
        """

        for bone in weights:
            v, w = weights[bone]
            m, ind = np.unique(v, return_index=True)
            m, cnt = np.unique(v, return_counts=True)

            # in m values, in ind positions to get initial weights from, in cnt count how many others to add
            # we now can organize the new weights array and then set or add the values
            #
            sumweights = np.zeros(len(m), dtype=np.float32)
            i = 0
            for x in m:
                pos = ind[i]
                sumw = w[pos]
                for l in range(1,cnt[i]):
                    sumw +=  w[pos+l]
                sumweights[i] = sumw
                i+=1
            weights[bone] = (m, sumweights)

        return weights


    def approxWeights(self, asset, base):
        #
        # create bone weights from base

        print ("Calculate bone weights " + asset.name)

        # recalculate the input in case of mesh loaded in binary form for easier calculation (tested)
        # form is:
        # vertex_num: baseskeleton: [(vertexnum_asset, weight), (...) ]

        self.vertWeights = {}
        for idx in range(asset.ref_vIdxs.shape[0]):
            for l in range(0,3):
                base_vert, w = asset.ref_vIdxs[idx, l], asset.weights[idx, l]
                if base_vert in self.vertWeights:
                    self.vertWeights[base_vert].append((idx, w))
                else:
                    self.vertWeights[base_vert] = [(idx, w)]

        # now generate the weights to be calculated by createWeightsPerBone
        #
        weights = {}
        for bname, (indxs, wghts) in list(base.bWeights.items()):
            vgroup = []
            for (base_vert,wt) in zip(indxs, wghts):
                if base_vert in self.vertWeights:
                    vlist = self.vertWeights[base_vert]
                    for (pv, w) in vlist:
                        pw = w*wt
                        if (pw > 1e-4):
                            vgroup.append((pv, pw))

            if len(vgroup) > 0:
                weights[bname] = vgroup
        self.createWeightsPerBone (weights)

        # since the algorithm above also creates multiple values for one index it must be changed to unique
        #
        self.bWeights = self.deDuplicateWeights(self.bWeights)

    def transferWeights(self, customskeleton):

        # in case skeleton is default skeleton, do nothing
        #
        if customskeleton is self.default_skeleton:
            print ("no transfer, default skeleton")
            return self.bWeights

        weights = {}    # new weights
        bonesref = {}   # contains all bones referenced by custom skeleton

        print ("is a different skeleton")
        print (self.default_skeleton.name)
        print (customskeleton.name)
        for bone, b in customskeleton.bones.items():

            # first collect which bones of standard-skeleton  are referenced by this bone
            #
            if b.weightref is not None and len(b.weightref) > 0:
                 for  elem in b.weightref:
                     bonesref[elem] = bone
            else:
                bonesref[bone] = bone
            for elem in b.reference:
                bonesref[elem] = bone

            # if bone is found in default, test "weights_reference"
            # if available sum these up to one bone
            # otherwise simply "copy" the weights
            # it is possible to define the same name for another bone
            # but in this case reference must have 0 elements
            #

            if bone in self.bWeights and len(b.reference) == 0:
                if b.weightref is not None and len(b.weightref) > 0:
                    bonegroup = []
                    for  elem in b.weightref:
                        if elem in  self.bWeights:
                            bonegroup.append(elem)
                    if len(bonegroup) > 0:
                        vn =  np.concatenate((tuple(self.bWeights[elem][0] for elem in bonegroup)), axis=0)
                        w  =  np.concatenate((tuple(self.bWeights[elem][1] for elem in bonegroup)), axis=0)
                        weights[bone] = (vn, w)
                else:
                    weights[bone] = self.bWeights[bone]

            else:
                # print (b.name, b.reference) # array
                bonegroup = []
                for  elem in b.reference:
                    if elem in  self.bWeights:
                        bonegroup.append(elem)

                if b.weightref is not None and len(b.weightref) > 0:
                    for  elem in b.weightref:
                        if elem in  self.bWeights and elem not in bonegroup:
                            bonegroup.append(elem)
                if len(bonegroup) > 0:
                    vn =  np.concatenate((tuple(self.bWeights[elem][0] for elem in bonegroup)), axis=0)
                    w  =  np.concatenate((tuple(self.bWeights[elem][1] for elem in bonegroup)), axis=0)
                    weights[bone] = (vn, w)

        # distribute missing vertices
        #
        for bone in self.bWeights:
            if bone not in bonesref:
                nbone = self.default_skeleton.bones[bone]
                while nbone.parent is not None:
                    nbone = nbone.parent
                    if nbone.name in bonesref:
                        dest = bonesref[nbone.name]
                        if dest in weights:
                            self.env.logLine(2, bone + ": parent chain reference: " + nbone.name + " should be appended to " + dest)
                            vn =  np.concatenate((self.bWeights[bone][0], weights[dest][0] ), axis=0)
                            w  =  np.concatenate((self.bWeights[bone][1], weights[dest][1] ), axis=0)
                        else:
                            self.env.logLine(2, bone + ": parent chain reference: " + nbone.name + " should be created as " + dest)
                            vn =  self.bWeights[bone][0]
                            w  =  self.bWeights[bone][1]

                        weights[dest] = (vn, w)
                        break
            else:
                self.env.logLine(2, bone + ": " + bonesref[bone])

        weights = self.sortWeights(weights)
        weights = self.deDuplicateWeights(weights)

        return weights

    def loadJSON(self, path):
        json = self.env.readJSON(path)
        if json is None:
            return False

        for key in ["name", "version", "description"]:
            if key in json:
                setattr (self, key, json[key])

        if not "weights" in json:
            self.env.logLine(1, "JSON weights are missing in " + path)
            return False

        self.createWeightsPerBone (json["weights"])
        return True

