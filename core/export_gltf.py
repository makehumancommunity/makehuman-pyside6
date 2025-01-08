import os
import json
import struct
import numpy as np
from obj3d.skeleton import skeleton as newSkeleton

"""
    GLTF module:
    Orientation
    + Y = up
    + z = to front
    + x = right
"""

class gltfExport:
    def __init__(self, glob, exportfolder, hiddenverts=False, onground=True, animation=False, scale =0.1):

        # subfolder for textures
        #
        self.imagefolder = "textures"
        self.exportfolder = exportfolder
        self.glob = glob
        self.env = glob.env
        self.hiddenverts = hiddenverts
        self.onground = onground
        self.animation = animation
        self.scale = scale
        self.lowestPos = 0.0

        # all constants used
        #
        self.TRIANGLES = 4
        self.UNSIGNED_BYTE = 5121
        self.UNSIGNED_SHORT = 5123
        self.UNSIGNED_INT = 5125
        self.FLOAT = 5126
        self.ARRAY_BUFFER = 34962          # usually positions
        self.ELEMENT_ARRAY_BUFFER = 34963  # usually indices
        self.GLTF_VERSION = 2
        self.MAGIC = b'glTF'
        self.JSON = b'JSON'
        self.BIN  = "BIN\x00"
        #
        # for image and sampler
        self.MAGFILTER = 9729   # Linear Magnification filter
        self.MINFILTER = 9987   # LINEAR_MIPMAP_LINEAR
        self.REPEAT = 10497
        self.IMAGEJPEG = 'image/jpeg'
        self.IMAGEPNG = "image/png"


        self.json = {}
        self.json["asset"] = {"generator": "makehuman2", "version": "2.0" }    # copyright maybe
        self.json["scenes"] = [ {"name": "makehuman2 export", "nodes": [] } ]  # one scene contains all nodes

        self.json["samplers"] = [ { "magFilter": self.MAGFILTER, "minFilter": self.MINFILTER, # fixed sampler (one for all)
            "wrapS": self.REPEAT, "wrapT" : self.REPEAT } ]

        self.json["scene"] = 0 # fixed number (we only have on scene)

        self.json["nodes"] = [] # list of nodes

        self.json["meshes"] = []
        self.mesh_cnt = -1

        self.json["accessors"] = []     # list of accessors (pointer to buffers, size, min, max
        self.accessor_cnt = -1

        self.json["bufferViews"] = []   # list of bufferviews, mode of buffer, length, offset, buffer number
        self.bufferview_cnt = -1

        self.json["buffers"] = []       # at the moment we try one view = one buffer

        # skeleton 
        #
        self.json["skins"] = []

        # texture and material
        #
        self.json["materials"] = []
        self.material_cnt = -1

        self.json["textures"] = []
        self.texture_cnt = -1

        self.json["images"] = []
        self.image_cnt = -1

        self.bufferoffset = 0
        self.buffers = []       # will hold the pointers

        self.bonelist = []      # helps to keep the order of the bones
        self.bonenames = {}

        self.meshindices = []   # holds meshindices for joints and weights

    def __str__(self):
        return (json.dumps(self.json, indent=3))

    def nodeName(self, filename):
        if filename is None:
            return("generic")

        fname = os.path.basename(filename)
        return(os.path.splitext(fname)[0])

    def addBufferView(self, target, data):
        #
        # buffer + we create one big binary buffer 

        length = len(data)
        # print (data)

        self.bufferview_cnt += 1
        if target is not None:
            self.json["bufferViews"].append({"buffer": 0, "byteOffset": self.bufferoffset, "byteLength": length, "target": target })
        else:
            self.json["bufferViews"].append({"buffer": 0, "byteOffset": self.bufferoffset, "byteLength": length })
        self.buffers.append(data)
        self.bufferoffset += length
        return(self.bufferview_cnt)

    def addPosAccessor(self, coord):
        self.accessor_cnt += 1

        cnt = len(coord) // 3

        ncoord = np.copy(coord)

        meshCoords = np.reshape(ncoord, (cnt,3))
        if self.lowestPos != 0.0:
            meshCoords -= [0.0, self.lowestPos, 0.0]

        if self.scale != 1.0:
            ncoord = ncoord * self.scale
        minimum = meshCoords.min(axis=0).tolist()
        maximum = meshCoords.max(axis=0).tolist()

        data = ncoord.tobytes()
        buf = self.addBufferView(self.ARRAY_BUFFER, data)

        self.json["accessors"].append({"bufferView": buf, "componentType": self.FLOAT, "count": cnt, "type": "VEC3", "min": minimum, "max": maximum})
        return(self.accessor_cnt)

    def addNormAccessor(self, norm):
        self.accessor_cnt += 1

        cnt = len(norm) // 3
        meshCoords = np.reshape(norm, (cnt,3))
        minimum = meshCoords.min(axis=0).tolist()
        maximum = meshCoords.max(axis=0).tolist()

        data = norm.tobytes()
        buf = self.addBufferView(self.ARRAY_BUFFER, data)
        self.json["accessors"].append({"bufferView": buf, "componentType": self.FLOAT, "count": cnt, "type": "VEC3", "min": minimum, "max": maximum})
        return(self.accessor_cnt)

    def addTPosAccessor(self, uvcoord):
        self.accessor_cnt += 1

        cnt = len(uvcoord) // 2
        meshCoords = np.reshape(uvcoord, (cnt,2))
        minimum = meshCoords.min(axis=0).tolist()
        maximum = meshCoords.max(axis=0).tolist()

        data = uvcoord.tobytes()
        buf = self.addBufferView(self.ARRAY_BUFFER, data)

        self.json["accessors"].append({"bufferView": buf, "componentType": self.FLOAT, "count": cnt, "type": "VEC2", "min": minimum, "max": maximum})
        return(self.accessor_cnt)

    def addIndAccessor(self, icoord):
        self.accessor_cnt += 1
        cnt = len(icoord)
        minimum = int(icoord.min())
        maximum = int(icoord.max())

        data = icoord.tobytes()
        buf = self.addBufferView(self.ELEMENT_ARRAY_BUFFER, data)

        self.json["accessors"].append({"bufferView": buf, "componentType": self.UNSIGNED_INT, "count": cnt, "type": "SCALAR", "min": [minimum], "max": [maximum]})
        return(self.accessor_cnt)

    def addBindMatAccessor(self, bonelist):
        self.accessor_cnt += 1
        cnt = len(bonelist)
        bindmat = np.zeros((cnt, 4,4), dtype=np.float32)
        n = 0
        for elem in self.bonenames:
            bone = self.bonenames[elem][1]
            bindmat[n], bindinv = bone.getBindMatrix(0, 'y')
            n += 1

        data = bindmat.tobytes()
        buf = self.addBufferView(None, data)

        self.json["accessors"].append({"bufferView": buf, "componentType": self.FLOAT, "count": cnt, "type": "MAT4"})
        return(self.accessor_cnt)

    def addJointAndWeightAccessor(self, numverts, bweights, overflow):
        self.accessor_cnt += 1

        if len(self.bonelist) > 255:
            joints = np.zeros((numverts, 4), dtype=np.uint16)
            jtype = self.UNSIGNED_SHORT
        else:
            joints = np.zeros((numverts, 4), dtype=np.uint8)
            jtype = self.UNSIGNED_BYTE

        weights = np.zeros((numverts, 4), dtype=np.float32)

        vertex = {}

        #print ("Verts:" + str(numverts))
        maxv = 0
        for elem in bweights:
            print (self.bonenames[elem][0])
            # get bone number from list
            #
            bonenumber = self.bonenames[elem][0]
            ind, w = bweights[elem]
            for n, i in enumerate (ind):
                if i > maxv:
                    maxv = i
                if i not in vertex:
                    vertex[i] = []
                vertex[i].append((bonenumber, w[n]))
        #print ("Maxv:" + str(maxv))

        for v in vertex:
            m = vertex[v]
            #
            # get largest 4 values
            #
            if len(m) > 4:
                m = sorted(m, key=lambda elem: elem[1], reverse=True)[:4]
            for i, (n,w) in enumerate(m):
                joints[v][i] = n
                weights[v][i] = w

        if overflow is not None:
           for (s,d) in overflow:
                for i in range(0,4):
                    joints[d][i] = joints[s][i]
                    weights[d][i] = weights[s][i]

        data = joints.tobytes()
        buf = self.addBufferView(self.ELEMENT_ARRAY_BUFFER, data)
        self.json["accessors"].append({"bufferView": buf, "componentType": jtype, "count": numverts, "type": "VEC4"})

        self.accessor_cnt += 1
        data = weights.tobytes()
        buf = self.addBufferView(self.ELEMENT_ARRAY_BUFFER, data)
        self.json["accessors"].append({"bufferView": buf, "componentType": self.FLOAT, "count": numverts, "type": "VEC4"})
        return(self.accessor_cnt)

    def addAnimInputAccessor(self, frames, framelen):
        self.accessor_cnt += 1
        timestamps = np.zeros(frames, dtype=np.float32)
        timepos = 0.0
        for i in range(frames):
            timestamps[i] = timepos
            timepos += framelen
        maximum = float(timestamps[-1])
        data = timestamps.tobytes()
        buf = self.addBufferView(None, data)
        self.json["accessors"].append({"bufferView": buf, "componentType": self.FLOAT, "count": frames, "min": [ 0.0 ], "max": [maximum],  "type": "SCALAR"})
        return(self.accessor_cnt)

    def addAnimOutputAccessor(self, frames, tlen):
        self.accessor_cnt += 1
        values = np.zeros((frames, tlen), dtype=np.float32)
        if tlen == 4:
            jtype = "VEC4"
            for i in range(frames):
                values[i][3] = 1.0 # Quaternions data fake
        else:
            jtype = "VEC3"
        data = values.tobytes()
        buf = self.addBufferView(None, data)
        self.json["accessors"].append({"bufferView": buf, "componentType": self.FLOAT, "count": frames, "type": jtype})
        return(self.accessor_cnt)

    def copyImage(self, source, dest):
        self.env.logLine (8, "Need to copy " + source + " to " + dest)

        if self.env.mkdir(dest) is False:
            return False

        dest = os.path.join(dest, os.path.basename(source))
        return (self.env.copyfile(source, dest))

    def addImage(self, image):
        self.image_cnt += 1
        destination = os.path.join(self.exportfolder, self.imagefolder)
        okay = self.copyImage(image, destination)
        if not okay:
            return (False, -1)

        uri = os.path.join(self.imagefolder, os.path.basename(image))
        self.json["images"].append({"uri": uri})
        return(True, self.image_cnt)

    def addMRTexture(self, roughtex):
        self.texture_cnt += 1
        (okay, image) = self.addImage(roughtex)
        if not okay:
            return (None)
        self.json["textures"].append({"sampler": 0, "source": image})
        return({ "index":  self.texture_cnt })

    def pbrMaterial(self, color, metal, rough, roughtex):
        pbr = { "baseColorFactor": [ color[0], color[1], color[2], 1.0 ], "metallicFactor": metal, "roughnessFactor": rough }
        if roughtex is not None:
            rtex = self.addMRTexture(roughtex)
            if rtex is not None:
                pbr["metallicRoughnessTexture"] = rtex
        return (pbr)

    def addDiffuseTexture(self, texture, metal, rough, roughtex):
        self.texture_cnt += 1
        (okay, image) = self.addImage(texture)
        if not okay:
            return (None)
        self.json["textures"].append({"sampler": 0, "source": image})

        pbr = { "baseColorTexture": { "index":  self.texture_cnt}, "metallicFactor": metal, "roughnessFactor": rough }

        if roughtex is not None:
            rtex = self.addMRTexture(roughtex)
            if rtex is not None:
                pbr["metallicRoughnessTexture"] = rtex

        return (pbr)

    def addNormalTexture(self, texture, scale):
        self.texture_cnt += 1
        (okay, image) = self.addImage(texture)
        if not okay:
            return (None)
        self.json["textures"].append({"sampler": 0, "source": image})
        return ({ "index": self.texture_cnt, "scale": scale })

    def addOcclusionTexture(self, texture, strength):
        self.texture_cnt += 1
        (okay, image) = self.addImage(texture)
        if not okay:
            return (None)
        self.json["textures"].append({"sampler": 0, "source": image})
        return ({ "index": self.texture_cnt, "strength": strength })

    def addMaterial(self, material):
        """
        :param material:  material from opengl.material
        TODO: alphaMode, alphaCutoff, doubleSided
        """
        self.material_cnt += 1
        name = material.name if  material.name is not None else "generic"

        roughtex = None
        if hasattr(material, "metallicRoughnessTexture"):
            roughtex = material.metallicRoughnessTexture

        if material.sc_diffuse:
            print ("Diffuse " + material.diffuseTexture)
            pbr = self.addDiffuseTexture(material.diffuseTexture, material.metallicFactor, material.pbrMetallicRoughness, roughtex)
        else:   
            pbr = self.pbrMaterial(material.diffuseColor, material.metallicFactor, material.pbrMetallicRoughness, roughtex)

        norm = None
        if material.sc_normal and hasattr(material, "normalmapTexture"):
            print ("Normals " + material.normalmapTexture)
            norm = self.addNormalTexture(material.normalmapTexture, material.normalmapIntensity)

        occl = None
        if material.sc_ambientOcclusion and hasattr(material, "aomapTexture"):
            print ("Ambient-Occlusion " + material.aomapTexture)
            occl = self.addOcclusionTexture(material.aomapTexture, material.aomapIntensity)


        if pbr is None:
            return(-1)

        mat = {"name": self.nodeName(name), "pbrMetallicRoughness": pbr}
        if material.sc_diffuse and material.transparent:
            mat["alphaMode"] = "BLEND"
            mat["doubleSided"] =  material.backfaceCull

        if norm is not None:
            mat["normalTexture"] = norm

        if occl is not None:
            mat["occlusionTexture"] = occl

        self.json["materials"].append(mat)
        return (self.material_cnt)

    def addMesh(self, obj, nodenumber, bweights):
        icoord = None
        if self.hiddenverts is False:
            icoord, coord, uvcoord, norm, nweights, overflow = obj.optimizeHiddenMesh(bweights)

        self.mesh_cnt += 1
        if icoord is not None:
            pos = self.addPosAccessor(coord)
            texcoord = self.addTPosAccessor(uvcoord)
            norm = self.addNormAccessor(norm)
            ind = self.addIndAccessor(icoord)
            self.meshindices.append((len(coord) // 3, nweights, overflow))
        else:
            pos = self.addPosAccessor(obj.gl_coord)
            texcoord = self.addTPosAccessor(obj.gl_uvcoord)
            norm = self.addNormAccessor(obj.gl_norm)
            ind = self.addIndAccessor(obj.gl_icoord)
            self.meshindices.append((len(obj.gl_coord) // 3, bweights, obj.overflow))

        self.json["meshes"].append({"primitives": [ {"attributes": { "POSITION": pos, "NORMAL": norm, "TEXCOORD_0": texcoord  }, "indices": ind, "material": nodenumber, "mode": self.TRIANGLES }]})
        return (self.mesh_cnt)

    def addWeights(self, num, elem, obj):
        print ("Adding weights to " +  str(self.json["nodes"][num]) )
        meshnum = self.json["nodes"][num]["mesh"]
        if elem is not None:
            ( numverts, weights, overflow) = self.meshindices[meshnum]
            weightbuf = self.addJointAndWeightAccessor(numverts, weights, overflow)
            jointbuf = weightbuf -1
            m = self.json["meshes"][meshnum]["primitives"][0]["attributes"]
            m["JOINTS_0"] = jointbuf
            m["WEIGHTS_0"] = weightbuf

    def addSkins(self, name):
        ptr = self.addBindMatAccessor(self.bonelist)
        self.json["skins"].append({ "inverseBindMatrices": ptr, "joints": self.bonelist, "name": name + "_skeleton" })

    def addBones(self, bone, num):
        #
        # bone-translations and rotations are fetched from local rest matrix, have to be relative in GLTF
        # Order of quaternions in GLTF: X Y Z W
        #
        trans = bone.getLocalTransitionVector().tolist()

        rot   = bone.getLocalRotationQVector()
        rot[[0, 1, 2, 3]] = rot[[1, 2, 3, 0]]       # change quaternion order (W is last element)
        rot = rot.tolist()

        node = {"name": bone.name, "translation": trans, "rotation": rot, "children": []  }
        self.json["nodes"].append(node)
        self.bonelist.append(num)
        self.bonenames[bone.name] = [ len(self.bonelist) -1, bone]   # because mesh was loaded before, just a hack :(
        num += 1
        nextnode = num
        for child in bone.children:
            nextnode = self.addBones(child, num)
            node["children"].append(num)
            num = nextnode
        return (num)

    def addAnimations(self, bvh):

        print ("Animations!!!!")
        # create channels and samplers
        #
        common_input = self.addAnimInputAccessor(bvh.frameCount, bvh.frameTime)
        print (common_input)

        channels = []
        samplers = []
        sampler = 0
        for elem in self.bonelist:
            channels.append({"sampler": sampler, "target": { "node": elem, "path": "translation" }})
            output = self.addAnimOutputAccessor(bvh.frameCount, 3)
            samplers.append({"input": common_input, "interpolation":"LINEAR", "output": output})
            sampler += 1
            channels.append({"sampler": sampler, "target": {"node": elem, "path": "rotation" }})
            output = self.addAnimOutputAccessor(bvh.frameCount, 4)
            samplers.append({"input": common_input, "interpolation":"LINEAR", "output": output})
            sampler += 1

        self.json["animations"] = []
        self.json["animations"].append({"name": bvh.name, "channels": channels, "samplers": samplers})

    def addNodes(self, baseclass):
        #
        # add the basemesh itself
        # then the skeleton and then the assets all these  nodes will be children
        # here one node will always have one mesh
        #
        skin = baseclass.baseMesh.material

        baseweights = None


        if baseclass.skeleton is not None:

            # recalculate weights for different skeleton
            #
            baseweights =  baseclass.default_skeleton.bWeights.transferWeights(baseclass.skeleton)


        # in case of a proxy use the proxy as first mesh, get weights for proxy
        #
        if baseclass.proxy:
            proxy = baseclass.attachedAssets[0]
            if baseweights is not None:
                proxy.calculateBoneWeights()
                baseweights = proxy.bWeights.transferWeights(baseclass.skeleton)
                baseobject = proxy.obj
            start = 1
        else:
            baseobject = baseclass.baseMesh
            start = 0
        charactername = self.nodeName(baseobject.filename)

        mat  = self.addMaterial(skin)
        if mat == -1:
            return (False)

        # in case of onground we need a translation which is then added to the mesh
        #
        if self.onground:
            self.lowestPos = baseclass.getLowestPos()


        mesh = self.addMesh(baseobject, mat, baseweights)

        self.json["nodes"].append({"name": charactername, "mesh": mesh,  "children": []  })
        self.json["scenes"][0]["nodes"].append(0)
        children = self.json["nodes"][0]["children"]

        childnum = 1

        # add skeleton, if baseweights are available
        #
        if baseweights is not None:
            self.json["nodes"][0]["skin"] = 0
            if self.scale != 1.0 or self.onground:
                print ("get a new skeleton")
                skeleton = newSkeleton(self.glob, "copy")
                skeleton.copyScaled(baseclass.skeleton, self.scale, self.lowestPos)
            else:
                skeleton = baseclass.skeleton

            bonename = list(skeleton.bones)[0]
            bone = skeleton.bones[bonename]

            children.append(childnum)
            childnum = self.addBones(bone, childnum)
            self.addSkins(charactername)

            # now add weights and joints
            #
            self.addWeights(0, skeleton, baseobject)

        # add all assets
        #
        for elem in baseclass.attachedAssets[start:]:
            mat =  self.addMaterial(elem.obj.material)
            if mat == -1:
                return (False)
            weights = elem.bWeights.transferWeights(baseclass.skeleton) if baseweights is not None else None
            mesh = self.addMesh(elem.obj, mat, weights)
            self.json["nodes"].append({"name": self.nodeName(elem.filename), "mesh": mesh })
            children.append(childnum)
            if baseweights is not None:
                self.json["nodes"][childnum]["skin"] = 0
                elem.calculateBoneWeights()
                self.addWeights(childnum, elem, elem.obj)
            childnum += 1

        # add animation, if any, allow only baseclass atm
        #
        if self.animation and baseweights is not None and baseclass.bvh:
            if baseclass.skeleton == baseclass.default_skeleton:
                self.addAnimations(baseclass.bvh)
            else:
                print ("No animation for different skeleton allowed atm")

        self.json["buffers"].append({"byteLength": self.bufferoffset})
        self.env.logLine(32, self)
        return (True)


    def binSave(self, baseclass, filename):
        #
        # binary glTF is:
        # 4 byte magic, 4 byte version + 4 byte length over all (which is the header)
        # JSON chunk:
        # chunklength 4 Byte, chunk type JSON, chunkData (4 Byte boundaries, padding)
        # BIN chunk:
        # chunklength 4 Byte, chunk type JSON, chunkData (4 Byte boundaries, padding)
        self.env.last_error ="okay"
        if self.addNodes(baseclass) is False:
            return False

        #TODO do we need an _ExtendedEncoder for JSON?

        version = struct.pack('<I', self.GLTF_VERSION)
        length = 12         # header length (always fix 12 bytes)

        jsondata = json.dumps(self.json, indent=None, allow_nan=False, skipkeys=True, separators=(',', ':')).encode("utf-8")

        # now pad json data to align with 4
        #
        pad = len(jsondata) % 4
        if pad != 0:
            jsondata += b' ' * (4-pad)
        
        lenjson = len(jsondata)
        length += (8 + lenjson) # add header + json-blob to length
        chunkjsonlen = struct.pack('<I', lenjson)

        # now the binary buffer. try to work with pointers here
        # the number of maximum used data is in bufferoffset
        # padding is not needed, we only use uint and float

        lenbin = self.bufferoffset

        length += (8 + lenbin) # add header + bin-blob to length
        chunkbinlen = struct.pack('<I', lenbin)

        completelength = struct.pack('<I', length)

        try:
            with open(filename, 'wb') as f:
                f.write(self.MAGIC)
                f.write(version)
                f.write(completelength)
                f.write(chunkjsonlen)
                f.write(self.JSON)
                f.write(jsondata)
                f.write(chunkbinlen)
                f.write(bytes(self.BIN, "utf-8"))
                for elem in self.buffers:
                    f.write(bytes(elem))

        except IOError as error: 
            self.env.last_error = str(error)
            return False
        return True
