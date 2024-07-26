import os
import json
import struct
import numpy as np

class gltfExport:
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
        self.TRIANGLES = 4
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
        #self.json["animations"] = []       # buffer?

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
        # print (data)

        self.bufferview_cnt += 1
        self.json["bufferViews"].append({"buffer": 0, "byteOffset": self.bufferoffset, "byteLength": length, "target": target })
        self.buffers.append(data)
        self.bufferoffset += length
        return(self.bufferview_cnt)

    def addPosAccessor(self, coord):
        self.accessor_cnt += 1

        cnt = len(coord) // 3

        if self.scale != 1.0:
            coord = coord * self.scale

        meshCoords = np.reshape(coord, (cnt,3))
        if self.zmin != 0.0:
            meshCoords -= [0.0, self.zmin, 0.0]
        minimum = meshCoords.min(axis=0).tolist()
        maximum = meshCoords.max(axis=0).tolist()

        data = coord.tobytes()
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
        icoord = None
        if self.hiddenverts is False:
            icoord, coord, uvcoord, norm = obj.optimizeHiddenMesh()
            if icoord is None:
                print ("Not hidden")

        self.mesh_cnt += 1
        if icoord is not None:
            pos = self.addPosAccessor(coord)
            texcoord = self.addTPosAccessor(uvcoord)
            norm = self.addNormAccessor(norm)
            ind = self.addIndAccessor(icoord)
        else:
            pos = self.addPosAccessor(obj.gl_coord)
            texcoord = self.addTPosAccessor(obj.gl_uvcoord)
            norm = self.addNormAccessor(obj.gl_norm)
            ind = self.addIndAccessor(obj.gl_icoord)
        self.json["meshes"].append({"primitives": [ {"attributes": { "POSITION": pos, "NORMAL": norm, "TEXCOORD_0": texcoord  }, "indices": ind, "material": nodenumber, "mode": self.TRIANGLES }]})
        return (self.mesh_cnt)

    def addBones(self, bone, num, pos):
        #
        # bone-translations have to be relative in GLTF
        #
        trans = ((bone.headPos - pos) * self.scale).tolist()
        node = {"name": bone.name, "translation": trans, "children": []  }
        self.json["nodes"].append(node)
        num += 1
        nextnode = num
        for child in bone.children:
            nextnode = self.addBones(child, num, bone.headPos)
            node["children"].append(num)
            num = nextnode
        return (num)

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

        # in case of onground we need a translation which is then added to the mesh
        #
        if self.onground:
            self.zmin = baseclass.getZMin() * self.scale

        mesh = self.addMesh(baseobject, mat)

        self.json["nodes"].append({"name": self.nodeName(baseobject.filename), "mesh": mesh,  "children": []  })
        self.json["scenes"][0]["nodes"].append(0)
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

        if baseclass.skeleton is not None:
            skeleton = baseclass.skeleton
            bonename = list(skeleton.bones)[0]
            bone = skeleton.bones[bonename]
            start = np.zeros(3,dtype=np.float32)
            if self.zmin != 0.0:
                start[1] = baseclass.getZMin()  # unscaled needed

            self.addBones(bone, childnum, start)
            children.append(childnum)
        
        self.json["buffers"].append({"byteLength": self.bufferoffset})
        print (self)
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
