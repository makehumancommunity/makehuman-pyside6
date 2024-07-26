#
# new Blender exchange format similar to glTF, so binary buffers for verts and uvs and faces
# to read with from_pydata(), rest JSON, should create files but should also be used as an API 
#

import os
import json
import struct
import numpy as np

class blendCom:
    def __init__(self, glob, exportfolder, hiddenverts=False, onground=True, scale =0.1):

        # subfolder for textures
        #
        self.imagefolder = "textures"
        self.exportfolder = exportfolder
        self.env = glob.env
        self.hiddenverts = hiddenverts
        self.onground = onground
        self.scale = scale
        self.zmin = 0.0

        # all constants used
        #
        self.POS_BUFFER = 10        # targets
        self.VPF_BUFFER = 11        # vertex per face
        self.FACE_BUFFER = 12
        self.UV_BUFFER = 13
        self.OV_BUFFER = 14
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
        self.json["asset"] = {"generator": "makehuman2", "version": "1.0", "mode": 0, "nodes": []  } # mode=0 complete file

        self.json["nodes"] = [] # list of nodes

        self.json["meshes"] = []
        self.mesh_cnt = -1

        self.json["bufferViews"] = []   # list of bufferviews, mode of buffer, length, offset, buffer number
        self.bufferview_cnt = -1

        self.json["buffers"] = []       # at the moment we try one view = one buffer

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
        self.json["bufferViews"].append({"buffer": 0, "byteOffset": self.bufferoffset, "byteLength": length, "target": target })
        self.buffers.append(data)
        self.bufferoffset += length
        return(self.bufferview_cnt)

    def addPosBuffer(self, coord):
        if self.scale != 1.0:
            coord = coord * self.scale

        if self.zmin != 0.0:
            sub = np.array([0.0, self.zmin, 0.0], dtype=np.float32)
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


    def pbrMaterial(self, color, metal, rough):
        return ({ "baseColorFactor": [ color[0], color[1], color[2], 1.0 ], "metallicFactor": metal, "roughnessFactor": rough })

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

    def addDiffuseTexture(self, texture, metal, rough):
        self.texture_cnt += 1
        (okay, image) = self.addImage(texture)
        if not okay:
            return (None)
        self.json["textures"].append({"sampler": 0, "source": image})
        return ({ "baseColorTexture": { "index": self.texture_cnt }, "metallicFactor": metal, "roughnessFactor": rough })

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
        if material.sc_diffuse:
            print ("Diffuse " + material.diffuseTexture)
            pbr = self.addDiffuseTexture(material.diffuseTexture, material.metallicFactor, material.pbrMetallicRoughness)
        else:   
            pbr = self.pbrMaterial(material.diffuseColor, material.metallicFactor, material.pbrMetallicRoughness)

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

    def addMesh(self, obj, nodenumber):
        self.mesh_cnt += 1
        (coords, uvcoords, vpface, faces, overflows) = obj.getVisGeometry(self.hiddenverts)
        pos = self.addPosBuffer(coords)
        face = self.addFaceBuffer(faces)
        vpf = self.addVPFBuffer(vpface)
        texcoord = self.addTPosBuffer(uvcoords)
        if len(overflows) > 0:
            overflow = self.addOverflowBuffer(overflows)
            self.json["meshes"].append({"primitives": [ {"attributes": { "POSITION": pos, "VPF": vpf, "FACE": face, "TEXCOORD_0": texcoord, "OVERFLOW": overflow  }, "material": nodenumber }]})
        else:
            self.json["meshes"].append({"primitives": [ {"attributes": { "POSITION": pos, "VPF": vpf, "FACE": face, "TEXCOORD_0": texcoord }, "material": nodenumber }]})
        return (self.mesh_cnt)

    def addNodes(self, baseclass):
        #
        # add the basemesh itself, the other nodes will be children
        # here one node will always have one mesh
        #
        skin = baseclass.baseMesh.material

        # in case of a proxy use the proxy as first mesh
        #
        if baseclass.proxy:
            baseobject = baseclass.attachedAssets[0].obj
            start = 1
        else:
            baseobject = baseclass.baseMesh
            start = 0
        mat  = self.addMaterial(skin)
        if mat == -1:
            return (False)

        # in case of onground we need a translation
        #
        if self.onground:
            self.zmin = baseclass.getZMin() * self.scale

        mesh = self.addMesh(baseobject, mat)

        self.json["nodes"].append({"name": self.nodeName(baseobject.filename), "mesh": mesh,  "children": []  })
        self.json["asset"]["nodes"].append(0)
        children = self.json["nodes"][0]["children"]

        childnum = 1
        for elem in baseclass.attachedAssets[start:]:
            mat =  self.addMaterial(elem.obj.material)
            if mat == -1:
                return (False)
            mesh = self.addMesh(elem.obj, mat)
            self.json["nodes"].append({"name": self.nodeName(elem.filename), "mesh": mesh })
            children.append(childnum)
            childnum += 1

        self.json["buffers"].append({"byteLength": self.bufferoffset})
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
