import numpy as np 
from obj3d.fops_binary import exportObj3dBinary, importObjFromFile
from opengl.material import Material
import os

class object3d:
    def __init__(self, glob, baseinfo, eqtype ):
 
        self.glob = glob
        self.env  = glob.env     # needed for globals
        self.type = eqtype      # equipmentype
        self.openGL   = None    # openGL pointer
        self.filename = None    # original file name
        self.name = None    # will contain object name derived from loaded file
        self.npGrpNames = []  # ordered list of groupnames numpy format

        self.prim    = 0    # will contain number primitives (tris)
        self.maxAttachedFaces  = 0 # will contain "maxpole"
        self.n_origverts = 0 # number of vertices after loading
        self.n_verts = 0    # number of vertices
        self.n_faces = 0    # number of faces
        self.n_fuvs  = 0    # number of uv-faces
        self.n_groups= 0    # number of groups
        self.z_depth = 0    # lowest value for z-depth, rendering of basemesh

        self.coord = []     # will contain positions of vertices, array of float32 for openGL
        self.uvs   = []     # will contain coordinates for uvs
        self.fuvs  = None   # will contain UV buffer or will stay none (TODO: is that needed?)
        self.loadedgroups = None # will contain the group after loading from file (also for hidden geometry)
        self.group = []     # will contain pointer to group per face

        self.overflow = None # will contain a table for double used vertices [source, dest]

        self.gl_coord = []    # will contain flattened gl-Buffer (these are coordinates to be changed)
        self.gl_coord_o = []  # will contain a copy of unchanged positions (TODO base mesh only ?)

        self.gl_coord_w = []  # will contain a copy of unchanged positions (working mode with targets) & for posing
        self.gl_coord_mn = []  # will contain buffer for work with macros containing all changes except the macros
        self.gl_coord_mm = []  # will contain buffer for work with macros containing all changes of the macros

        self.gl_uvcoord = []  # will contain flattened gluv-Buffer
        self.gl_norm  = []    # will contain flattended normal buffer
        self.gl_fvert  = []   # will contain vertices per face, [verts, 3] array of uint32 for openGL > 2
        self.n_glverts = 0    # number of vertices for open gl
        self.n_glnorm  = 0    # number of normals for open gl

        self.gl_icoord = []     # openGL-Drawarray Index
        self.gl_hicoord = None  # openGL-Drawarray used when parts are hidden

        self.material = None    # will contain a material

        if baseinfo is not None:
            self.visible = baseinfo["visible groups"]
            self.is_base = True
        else:
            self.visible = None
            self.is_base = False

    def __str__(self):
        return (self.name + ": Object3d with " + str(self.n_groups) + " group(s)\n" + 
                str(self.n_origverts) + " vertices, " + str(self.n_faces) + " faces (" +
                str(self.n_fuvs) + " uv-faces)\nOpenGL triangles: " +
                str(self.prim) + "\nOpenGL DrawElements: " + str(self.n_verts)) 
                #+ "\nMaximum attached faces for one vertex: " + str(self.maxAttachedFaces))

    def load(self, path, use_obj=False):
        """
        load a mesh either binary or per object
        """
        self.filename = path
        (success, text) = importObjFromFile(path, self, use_obj)
        if success:
            self.initMaterial(path)
        return (success, text)

    def setZDepth(self, z_depth):
        self.z_depth = z_depth

    def initMaterial(self, filename):
        self.material = Material(self.glob, os.path.dirname(filename), self.type)

    def listAllMaterials(self):
        if self.material:
            return self.material.listAllMaterials(os.path.dirname(self.filename))
        return []

    def getMaterialPath(self, filename):
        if filename is not None and self.material is not None:
            return(self.material.isExistent(filename))
        return None

    def loadMaterial(self, pathname):
        """
        use a relative path to object
        """
        if pathname is not None and self.material is not None:
            return(self.material.loadMatFile(pathname))
        else:
            return True

    def newMaterial(self, pathname):

        if self.material is not None:
             self.material.freeTextures()
        self.initMaterial(self.filename)
        return(self.material.loadMatFile(pathname))

    def getMaterialFilename(self):
        if self.material is not None:
            return(self.material.getCurrentMatFilename())
        return None

    def exportBinary(self):
        filename = self.filename[:-4] + ".mhbin" if self.filename.endswith(".obj") else self.filename + ".mhbin"
        return(exportObj3dBinary(filename, self))

    def setName(self, name):
        if name is None:
            self.name = "generic"
        else:
            self.name = name

    def setGroupNames(self, names):
        """
        group names in numpy format (usable for binary export)
        """
        nlen = 0
        for name in names:
            l = len(name)
            if l > nlen:
                nlen = l
        self.npGrpNames = np.array(names, dtype='|S'+str(nlen))
        self.n_groups = len(names)

    def getOpenGLIndex(self):
        #print (self.filename +  " deleted verts" if self.gl_hicoord is not None else self.filename + " normal")
        return (self.gl_hicoord if self.gl_hicoord is not None else self.gl_icoord)

    def notHidden(self):
         self.gl_hicoord = None

    def createGLVertPos(self, pos, uvs, overflow, orig):
        self.n_origverts = orig
        self.n_verts = len(pos)
        self.coord = np.asarray(pos, dtype=np.float32)      # positions converted to array of floats
        self.n_uvs = len(uvs)
        self.uvs = np.asarray(uvs, dtype=np.float32)        # positions converted to array of floats
        self.overflow = overflow

    def overflowCorrection(self, arr):
        """
        when the main part of the mesh is directly corrected, handle the overflow
        """
        # numpy: create fancy indices from columns, repeat it 3 times and add values 0, 1, 2
        # simulates this:
        # for (source, dest) in self.overflow:
        #    s = source * 3     # np.repeat
        #    d = dest * 3
        #    arr[d:d+3]   = arr[s:s+3]  (np.tile for d:d+3)

        index = np.tile(np.array([0,1,2]), len(self.overflow))
        src = np.repeat(self.overflow[:,0], 3)*3 + index
        dst = np.repeat(self.overflow[:,1], 3)*3 + index
        arr[dst]   = arr[src]

    def calcNormals(self):
        """
        calculates face-normals and then vertex normals
        """
        self.gi_norm = np.zeros((self.n_verts, 3), dtype=np.float32)

        # set the face normals for each vertex to zero, set the counter to zero
        #
        fa_norm = np.zeros((self.n_verts, 3), dtype=np.float32)
        fa_cnt  = np.zeros(self.n_verts, dtype=np.uint32)

        # calculate face normal and summarize them with other (for each 3 verts per triangle)
        #
        for elem in self.gl_fvert:
            v = self.coord[elem]
            norm = np.cross(v[0] - v[1], v[1] - v[2])

            # done on flattened array it works like this
            #x = elem * 3
            #a = [ self.gl_coord[x][0] - self.gl_coord[x][1], self.gl_coord[x+1][0] - self.gl_coord[x+1][1], self.gl_coord[x+2][0] - self.gl_coord[x+2][1] ]
            #b = [ self.gl_coord[x][1] - self.gl_coord[x][2], self.gl_coord[x+1][1] - self.gl_coord[x+1][2], self.gl_coord[x+2][1] - self.gl_coord[x+2][2] ]
            #norm = np.cross(a, b)

            for i in range(3):
                fa_norm[elem[i]] += norm
                fa_cnt[elem[i]] += 1

        # because part of the faces belong to the overflow buffer add them as well
        #
        for (source, dest) in self.overflow:
            fa_norm[source] += fa_norm[dest]
            fa_cnt[source]  += fa_cnt[dest]

        # now divide by the number of edges and normalize length with np.linalg.norm
        #
        for i in range(0, self.n_origverts):
            if fa_cnt[i] != 0:
                norm = fa_norm[i] / fa_cnt[i]
                l = np.linalg.norm(norm)
                if l != 0.0:
                    self.gi_norm[i] = norm / np.linalg.norm(norm)
                else:
                    self.gi_norm[i] = norm

        # simply copy for the doubles in the end using overflow
        #
        for (source, dest) in self.overflow:
            self.gi_norm[dest] =  self.gi_norm[source]

        # flatten vector
        #
        self.gl_norm = self.gi_norm.flatten()

    def createGLFaces(self, nfaces, ufaces, prim, groups):
        self.loadedgroups = groups
        self.prim = prim
        self.n_faces = nfaces
        self.n_fuvs =  ufaces
        self.group = np.zeros(nfaces, dtype=np.uint16)

        self.gl_fvert = np.zeros((self.prim, 3), dtype=np.uint32)
        # fill faces and group buffer
        # ( array of numbers per face determining the group-number )

        cnt = 0
        for num, npelem in enumerate (self.npGrpNames):
            elem = npelem.decode("utf-8")
            if self.visible is not None and elem not in self.visible:
                continue
            faces = groups[elem]["v"]
            for face in faces:
                l = len(face)
                self.gl_fvert[cnt] = face[:3]
                cnt += 1
                # rest for quad and n-gons 
                if l > 3:
                    i=2
                    while i < l-1:
                        self.gl_fvert[cnt] = [face[0], face[i], face[i+1]]
                        cnt += 1
                        i += 1

        # resize to visible groups only TODO not sure if it should stay like this
        #
        self.gl_fvert.resize((cnt, 3), refcheck=False)
        self.n_glverts = cnt * 3
        self.gl_icoord = np.zeros(self.n_glverts, dtype=np.uint32)
        cnt = 0
        for face in self.gl_fvert:
            for vert in face:
                self.gl_icoord[cnt] = vert
                cnt += 1
        self.gl_coord = self.coord.flatten()
        self.gl_coord_o = self.gl_coord.copy()  # create a copy for original values
        if self.is_base:
            self.gl_coord_w = self.gl_coord.copy()          # basemesh: create another one for working

        # for no UV map, use an empty array
        #
        if self.n_fuvs > 0:
            self.gl_uvcoord = self.uvs.flatten()
        else:
            self.gl_uvcoord = np.zeros(2 * self.n_glverts, dtype=np.float32)


        #del self.uvs           # save memory
        #del self.fvert

        #self.calculateMaxAttachedFaces()
        self.calcNormals()

    def getPosition(self, num):
        """
        get position of one vertex based on gl_coord
        """
        m = num*3
        return (self.gl_coord[m], self.gl_coord[m+1], self.gl_coord[m+2])

    def getMeanPosition(self, arr):
        """
        used for skeleton mainly, mean postion of an array, based on gl_coord
        """
        mean = [ 0.0, 0.0, 0.0]
        for i in arr:
            m = i*3
            mean[0] += self.gl_coord[m] 
            mean[1] += self.gl_coord[m+1] 
            mean[2] += self.gl_coord[m+2] 
        n = len(arr)
        return ([mean[0] / n, mean[1] / n, mean[2] / n] )

    def resetMesh(self):
        self.gl_coord[:] = self.gl_coord_o[:] # get back the copy

    def createWCopy(self):
        self.gl_coord_w[:] = self.gl_coord[:]

    def resetFromCopy(self):
        self.gl_coord[:] = self.gl_coord_w[:]

    def hideVertices(self, verts):
        numind = len(self.gl_icoord) -2
        w = np.resize(verts, self.n_verts)
        #
        # bool copy to end
        #
        for (source, dest) in self.overflow:
            w[dest] = w[source]
        #
        self.gl_hicoord = np.zeros(len(self.gl_icoord), dtype=np.uint32)
        scnt = 0
        dcnt = 0
        while scnt < numind:

            # if all 3 verts are false, triangle is created
            #
            if not (w[self.gl_icoord[scnt]] and w[self.gl_icoord[scnt+1]] and w[self.gl_icoord[scnt+2]]):
                self.gl_hicoord[dcnt:dcnt+3] = self.gl_icoord[scnt:scnt+3]
                dcnt += 3
            scnt += 3
        self.gl_hicoord.resize(dcnt, refcheck=False)

    def hideApproxVertices(self, asset, base, verts):
        self.gl_hicoord = np.zeros(len(self.gl_icoord), dtype=np.uint32)
        scnt = 0
        dcnt = 0

        w = np.resize(verts, base.n_verts)
        for (source, dest) in base.overflow:
            w[dest] = w[source]

        ref = np.resize(asset.ref_vIdxs,(self.n_verts,3))
        for (source, dest) in self.overflow:
            ref[dest] = ref[source]

        numind = len(self.gl_icoord) -2
        while scnt < numind:
            n1 = self.gl_icoord[scnt]
            n2 = self.gl_icoord[scnt+1]
            n3 = self.gl_icoord[scnt+2]
            if not (  w[ref[n1][0]] and w[ref[n1][1]] and  w[ref[n1][2]] and \
                    w[ref[n2][0]] and w[ref[n2][1]] and  w[ref[n2][2]] and \
                    w[ref[n3][0]] and w[ref[n3][1]] and  w[ref[n3][2]] ):
                self.gl_hicoord[dcnt:dcnt+3] = self.gl_icoord[scnt:scnt+3]
                dcnt += 3
            scnt += 3
        self.gl_hicoord.resize(dcnt, refcheck=False)

    def getInitialCopyForSlider(self, factor, targetlower, targetupper):
        """
        called when starting work with one slider, a copy without the value
        of this slider is created.
        """
        self.createWCopy()
        if factor == 0.0:
            return
        else:
            if factor < 0.0:
                if targetlower is None:
                    return
                verts = targetlower.verts
                data  = targetlower.data
                factor = -factor
            elif factor > 0.0:
                verts = targetupper.verts
                data  = targetupper.data
            for i in range(0, len(verts)):
                x = verts[i] * 3
                self.gl_coord_w[x]   = self.gl_coord[x]   - factor * data[i][0]
                self.gl_coord_w[x+1] = self.gl_coord[x+1] - factor * data[i][1]
                self.gl_coord_w[x+2] = self.gl_coord[x+2] - factor * data[i][2]

        self.overflowCorrection(self.gl_coord_w)
        # self.calcNormals()

    def updateByTarget(self, factor, targetlower, targetupper):
        """
        updates the mesh when slider is moved
        """
        if factor == 0.0:
            self.gl_coord[:] = self.gl_coord_w[:]
            return

        if factor < 0.0:
            if targetlower is None:
                return
            verts = targetlower.verts * 3
            data  = targetlower.data.ravel()
            factor = -factor
        elif factor > 0.0:
            verts = targetupper.verts * 3
            data  = targetupper.data.ravel()

        srcVerts = np.s_[...]
        self.gl_coord[verts] = self.gl_coord_w[verts] + data[srcVerts][::3] * factor
        self.gl_coord[verts+1] = self.gl_coord_w[verts+1] + data[srcVerts][1::3] * factor
        self.gl_coord[verts+2] = self.gl_coord_w[verts+2] + data[srcVerts][2::3] * factor

        # overflow vertices
        #
        self.overflowCorrection(self.gl_coord)

    def setTarget(self, factor, targetlower, targetupper):
        """
        updates from file (all done on basemesh directly)
        no overflow correction
        """
        if factor < 0.0:
            if targetlower is None:
                return
            verts = targetlower.verts * 3
            data  = targetlower.data.ravel()
            factor = -factor
        elif factor > 0.0:
            if targetupper is None:
                return
            verts = targetupper.verts * 3
            data  = targetupper.data.ravel()

        srcVerts = np.s_[...]
        self.gl_coord[verts] += data[srcVerts][::3] * factor
        self.gl_coord[verts+1] += data[srcVerts][1::3] * factor
        self.gl_coord[verts+2] += data[srcVerts][2::3] * factor

    def addAllNonMacroTargets(self):
        """
        copy original mesh + add all changes of non-macrotargets
        """
        print ("+++ Add all non Macro Targets to buffer")
        self.resetMesh()
        targets = self.glob.Targets.modelling_targets
        for target in targets:
            if target.value != 0.0 and target.macro is None:
                # print ("Set " + target.name)
                self.setTarget(target.value / 100, target.decr, target.incr)

        # overflow vertices
        #
        self.overflowCorrection(self.gl_coord)

    def prepareMacroBuffer(self):
        """
        copy original mesh + add all changes of non-macrotargets
        """
        print ("+++ Prepare Buffer")
        self.gl_coord_mn =  self.gl_coord.copy()
        self.gl_coord_mm = np.zeros_like(self.gl_coord)


    def addTargetToMacroBuffer(self, factor, target):
        """
        updates a special buffer for a macro target
        """
        m = target.data.ravel()
        verts = target.verts * 3

        srcVerts = np.s_[...]
        self.gl_coord_mm[verts] += m[srcVerts][::3] * factor
        self.gl_coord_mm[verts+1] += m[srcVerts][1::3] * factor
        self.gl_coord_mm[verts+2] += m[srcVerts][2::3] * factor


    def addMacroBuffer(self):
        """
        after changing a macro it will be added
        make sure to write in same buffer (out will avoid to get a new one)
        """
        print ("+++ Add macro to character")
        np.add(self.gl_coord_mm, self.gl_coord_mn, out=self.gl_coord)  
        self.overflowCorrection(self.gl_coord)
        self.gl_coord_mm = np.zeros_like(self.gl_coord)

    def approxByTarget(self, asset, base):
        """
        updates the mesh when slider is moved, approximation
        """

        b = base.gl_coord
        w = asset.weights
        o = asset.offsets

        verts = asset.ref_vIdxs * 3 # index (v0, v1, v2)

        """
        i = 0
        j = 0
        for v in verts:
            self.gl_coord[i]   = w[j,0]*b[v[0]]   + w[j,1]*b[v[1]]  +  w[j,2]*b[v[2]]   + o[j,0]
            self.gl_coord[i+1] = w[j,0]*b[v[0]+1] + w[j,1]*b[v[1]+1] + w[j,2]*b[v[2]+1] + o[j,1]
            self.gl_coord[i+2] = w[j,0]*b[v[0]+2] + w[j,1]*b[v[1]+2] + w[j,2]*b[v[2]+2] + o[j,2]
            i += 3
            j += 1

        """
        vlen = len(verts)
        self.gl_coord[:vlen*3:3]  = w[:,0]*b[verts[:,0]] + w[:,1]*b[verts[:,1]] +  w[:,2]*b[verts[:,2]] + o[:,0]
        self.gl_coord[1:vlen*3:3] = w[:,0]*b[verts[:,0]+1] + w[:,1]*b[verts[:,1]+1] +  w[:,2]*b[verts[:,2]+1] + o[:,1]
        self.gl_coord[2:vlen*3:3] = w[:,0]*b[verts[:,0]+2] + w[:,1]*b[verts[:,1]+2] +  w[:,2]*b[verts[:,2]+2] + o[:,2]

        # scaling: np.dot(asset.scaleMat, o.transpose()).transpose()
        # here it would be simply o0 * x, o1 *y, o2*z

        # do not forget the overflow vertices
        #
        self.overflowCorrection(self.gl_coord)

    def precalculateDimension(self):
        """
        calculate numbers of vertices, which are on the outside for later use
        do that only for visible groups
        """
        coord = np.zeros((self.n_origverts, 3), dtype=np.float32)
        for i in range (0, self.n_glverts):
            cnt = self.gl_icoord[i]
            if cnt < self.n_origverts:
                coord[cnt] = self.coord[cnt]
        self.max_index = np.argmax(coord, axis=0)
        self.min_index  = np.argmin(coord, axis=0)

    def getCenterWidth(self):
        return ((self.gl_coord[self.max_index[0]*3]+self.gl_coord[self.min_index[0]*3])/2.0)

    def getCenterHeight(self):
        return ((self.gl_coord[self.max_index[1]*3+1]+self.gl_coord[self.min_index[1]*3+1])/2.0)

    def getCenterDepth(self):
        return ((self.gl_coord[self.max_index[2]*3+2]+self.gl_coord[self.min_index[2]*3+2])/2.0)

    def getCenter(self):
        a =  self.gl_coord
        n = [ self.getCenterWidth(),  self.getCenterHeight(), self.getCenterDepth() ]
        return (n)

    def getZMin(self):
        return (self.gl_coord[self.min_index[1]*3+1])

    def getHeightInUnits(self):
        return (self.gl_coord[self.max_index[1]*3+1]-self.gl_coord[self.min_index[1]*3+1])

    """
    def calculateMaxAttachedFaces(self):
        attachedFaces = np.zeros(self.n_verts, dtype=np.uint8)
        for elem in faceverts:
            for vert in elem:
                attachedFaces[vert] += 1

        self.maxAttachedFaces  = np.max(attachedFaces)
    """
    def __del__(self):
        self.env.logLine (4, " -- delete object3d: " + str(self.name))
