#
# new Blender exchange format similar to glTF, so binary buffers for
# verts, vertex per faces, faces, uvs => to read with from_pydata() in Blender
#
# definition of structure is in JSON
#
# it is planned to use this module for files but should also be used as an API 
#
# so order of buffers is significant to be able to read the file chunk by chunk
#
# start must be skeleton (if available) to get the restmatrix buffer first,
# then all othter future components not directly associated with a mesh

import os
import json
import struct
import numpy as np
from obj3d.skeleton import skeleton as newSkeleton

class blendCom:
    def __init__(self, glob, exportfolder, hiddenverts=False, onground=True, scale =0.1):

        # subfolder for textures
        #
        self.imagefolder = "textures"
        self.exportfolder = exportfolder
        self.glob = glob
        self.env = glob.env
        self.hiddenverts = hiddenverts
        self.onground = onground
        self.scale = scale
        self.lowestPos = 0.0

        # all constants used
        #
        self.RMAT_BUFFER   = 1  # rest matrix (skeleton)
        self.POS_BUFFER    = 10 # target: position
        self.VPF_BUFFER    = 11 # vertex per face
        self.FACE_BUFFER   = 12
        self.UV_BUFFER     = 13
        self.OV_BUFFER     = 14
        self.WPV_BUFFER    = 16 # weight per vertex
        self.JOINT_BUFFER  = 17
        self.WEIGHT_BUFFER = 18
        self.MH2B_VERSION = 1
        self.MAGIC = b'MH2B'
        self.JSON = b'JSON'
        self.BIN  = "BIN\x00"
        #
        # for image and sampler
        self.IMAGEJPEG = 'image/jpeg'
        self.IMAGEPNG = "image/png"

        self.json = {}
        # change asset version to add a name for collection
        self.json["asset"] = {"generator": "makehuman2", "version": "1.0", "mode": 0, "buffersize": 0, "nodes": []  } # mode=0 complete file

        self.json["nodes"] = [] # list of nodes

        self.json["meshes"] = []
        self.mesh_cnt = -1

        self.json["bufferViews"] = []   # list of bufferviews, mode of buffer, length, offset, buffer number
        self.bufferview_cnt = -1

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

        self.bonenames = {}

        # additional block: skeleton

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

        self.bufferview_cnt += 1
        self.json["bufferViews"].append({"byteOffset": self.bufferoffset, "byteLength": length, "target": target })
        self.buffers.append(data)
        self.bufferoffset += length
        return(self.bufferview_cnt)

    def addPosBuffer(self, coord):
        if self.scale != 1.0:
            coord = coord * self.scale

        if self.lowestPos != 0.0:
            sub = np.array([0.0, self.lowestPos, 0.0], dtype=np.float32)
            change = np.tile(sub, len(coord)//3)
            coord = coord - change

        data = coord.tobytes()
        return(self.addBufferView(self.POS_BUFFER, data))


    def addTPosBuffer(self, uvcoord):
        data = uvcoord.tobytes()
        return(self.addBufferView(self.UV_BUFFER, data))

    def addOverflowBuffer(self, overflow):
        data = overflow.flatten().tobytes()
        return(self.addBufferView(self.OV_BUFFER, data))

    def addFaceBuffer(self, faces):
        data = faces.tobytes()
        return(self.addBufferView(self.FACE_BUFFER, data))

    def addVPFBuffer(self, vpf):
        data = vpf.tobytes()
        return(self.addBufferView(self.VPF_BUFFER, data))

    def copyImage(self, source, dest):
        print ("Need to copy " + source + " to " + dest)

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

    def addWeightBuffers(self, coords, bweights):
        print ("We have weights")
        wpvlen = len(coords) // 3   # length of vertex per face derived from flattened coords

        lsize = 0

        vertex = {}

        # TODO: how to deal with empty weights

        for bone, t in bweights.items():
            lsize += len(t[0])
            bonenumber = self.bonenames[bone]
            ind, w = bweights[bone]
            for n, i in enumerate (ind):
                if i < wpvlen:
                    if i not in vertex:
                        vertex[i] = []
                    vertex[i].append((bonenumber, w[n]))


        print ("Verts:" + str(wpvlen))
        print ("Weight array:" + str(lsize))
        weightpervertex = np.zeros(wpvlen, dtype=np.dtype('i1'))
        joints =  np.zeros(lsize, dtype=np.dtype('i4'))
        weights = np.zeros(lsize, dtype=np.float32)

        i = 0
        for j in range(0, wpvlen):
            cnt = 0
            if j in vertex:
                for n,w in vertex[j]:
                    joints[i] = n
                    weights[i] = w
                    i += 1
                    cnt += 1
            weightpervertex[j] = cnt

        bufwpv    = self.addBufferView(self.WPV_BUFFER, weightpervertex.tobytes())
        bufjoint  = self.addBufferView(self.JOINT_BUFFER, joints.tobytes())
        bufweight = self.addBufferView(self.WEIGHT_BUFFER, weights.tobytes())

        return bufwpv, bufjoint, bufweight

    def addMesh(self, obj, nodenumber, bweights):
        self.mesh_cnt += 1
        (coords, uvcoords, vpface, faces, overflows) = obj.getVisGeometry(self.hiddenverts)
        pos = self.addPosBuffer(coords)
        face = self.addFaceBuffer(faces)
        vpf = self.addVPFBuffer(vpface)
        texcoord = self.addTPosBuffer(uvcoords)

        jmesh = {"primitives": [ {"attributes": { "POSITION": pos, "VPF": vpf, "FACE": face, "TEXCOORD_0": texcoord }, "material": nodenumber }]}

        # add the overflow
        #
        if len(overflows) > 0:
            overflow = self.addOverflowBuffer(overflows)
            jmesh["primitives"][0]["attributes"]["OVERFLOW"] = overflow

        # add weights in case of skeleton
        #
        if bweights is not None:
            bufwpv, bufjoint, bufweight = self.addWeightBuffers(coords, bweights)
            jmesh["primitives"][0]["attributes"]["WPF"] = bufwpv
            jmesh["primitives"][0]["attributes"]["JOINTS"] = bufjoint
            jmesh["primitives"][0]["attributes"]["WEIGHTS"] = bufweight

        self.json["meshes"].append(jmesh)
        return (self.mesh_cnt)

    def addBone(self, bone, restmat, num):
        entry = {"id": num, "name": bone.name, "head": list(bone.headPos.astype(float)), "tail": list(bone.tailPos.astype(float))}
        restmat[num] = bone.matRestGlobal
        if bone.parentname:
            entry["parent"] = bone.parentname
        self.bonenames[bone.name] = num       # keep position in dictionary
        return entry

    def addSkeleton(self, skeleton):
        """
        skeleton definition uses an array of bones + pointer to binary restmatrices
        """
        bones = []

        cnt = len(skeleton.bones)
        restmat = np.zeros((cnt, 4,4), dtype=np.float32)
        n = 0
        for bone in skeleton.bones:
            bones.append(self.addBone(skeleton.bones[bone], restmat, n))
            n += 1
        data = restmat.tobytes()
        buf = self.addBufferView( self.RMAT_BUFFER, data)
        self.json["skeleton"] = {"name": self.nodeName(skeleton.name), "bones": bones, "RESTMAT": buf}


    def addNodes(self, baseclass):
        #
        # start with all non-meshes using extra buffers (so skeleton with restmatrix etc.)
        #
        # add the basemesh itself, the other nodes will be children
        # here one node will always have one mesh
        #

        # in case of onground we need a translation
        #
        if self.onground:
            self.lowestPos = baseclass.getLowestPos() * self.scale

        # use baseweights as a hint for having a skeleton
        #
        baseweights = baseclass.skeleton.bWeights.bWeights if baseclass.skeleton is not None else None

        # add skeleton, if available
        #
        if baseweights is not None:
            if self.scale != 1.0 or self.onground:
                print ("get a new skeleton")
                skeleton = newSkeleton(self.glob, "copy")
                skeleton.copyScaled(baseclass.skeleton, self.scale, self.lowestPos)
            else:
                skeleton = baseclass.skeleton

            self.addSkeleton(skeleton)


        skin = baseclass.baseMesh.material

        # add the base object,  in case of a proxy use the proxy as first mesh, get weights for proxy
        #
        if baseclass.proxy:
            proxy = baseclass.attachedAssets[0]
            if baseweights is not None:
                proxy.calculateBoneWeights()
                baseweights = proxy.bWeights.bWeights
                baseobject = proxy.obj
            start = 1
        else:
            baseobject = baseclass.baseMesh
            start = 0
        mat  = self.addMaterial(skin)
        if mat == -1:
            return (False)

        mesh = self.addMesh(baseobject, mat, baseweights)

        self.json["nodes"].append({"name": self.nodeName(baseobject.filename), "mesh": mesh,  "children": []  })
        self.json["asset"]["nodes"].append(0)
        children = self.json["nodes"][0]["children"]

        childnum = 1

        for elem in baseclass.attachedAssets[start:]:
            mat =  self.addMaterial(elem.obj.material)
            if mat == -1:
                return (False)
            if baseweights is not None:
                elem.calculateBoneWeights()
                weights = elem.bWeights.bWeights
            else:
                weights = None
            mesh = self.addMesh(elem.obj, mat, weights)
            self.json["nodes"].append({"name": self.nodeName(elem.filename), "mesh": mesh })
            children.append(childnum)
            childnum += 1

        # now insert correct lenght of available buffers
        #
        self.json["asset"]["buffersize"] =  self.bufferoffset
        print (self)
        return (True)


    def binSave(self, baseclass, filename):
        #
        # binary mh2b is:
        # 4 byte magic, 4 byte version + 4 byte length over all (which is the header)
        # JSON chunk:
        # chunklength 4 Byte, chunk type JSON, chunkData (4 Byte boundaries, padding)
        # BIN chunk:
        # chunklength 4 Byte, chunk type JSON, chunkData (4 Byte boundaries, padding)
        self.env.last_error ="okay"
        if self.addNodes(baseclass) is False:
            return False

        version = struct.pack('<I', self.MH2B_VERSION)
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
        #print (jsondata)

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
