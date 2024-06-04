import os
import json
import struct
import numpy as np

class gltfExport:
    def __init__(self):

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

        self.json = {}
        self.json["asset"] = {"generator": "makehuman2", "version": "2.0" }    # copyright maybe
        self.json["scenes"] = [ {"name": "makehuman2 export", "nodes": [] } ]  # one scene contains all nodes
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

        # texture and material (samplers are not needed)
        #
        self.json["materials"] = []
        self.material_cnt = -1

        self.json["textures"] = []
        self.json["images"] = []

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

    def addPosAccessor(self, obj):
        self.accessor_cnt += 1

        cnt = len(obj.gl_coord) // 3
        meshCoords = np.reshape(obj.gl_coord, (cnt,3))
        minimum = meshCoords.min(axis=0).tolist()
        maximum = meshCoords.max(axis=0).tolist()

        data = obj.gl_coord.tobytes()
        buf = self.addBufferView(self.ARRAY_BUFFER, data)

        self.json["accessors"].append({"bufferView": buf, "componentType": self.FLOAT, "count": cnt, "type": "VEC3", "min": minimum, "max": maximum})
        return(self.accessor_cnt)

    def addTPosAccessor(self, obj):
        self.accessor_cnt += 1

        cnt = len(obj.gl_uvcoord) // 2
        meshCoords = np.reshape(obj.gl_uvcoord, (cnt,2))
        minimum = meshCoords.min(axis=0).tolist()
        maximum = meshCoords.max(axis=0).tolist()

        data = obj.gl_uvcoord.tobytes()
        buf = self.addBufferView(self.ARRAY_BUFFER, data)

        self.json["accessors"].append({"bufferView": buf, "componentType": self.FLOAT, "count": cnt, "type": "VEC2", "min": minimum, "max": maximum})
        return(self.accessor_cnt)

    def addIndAccessor(self, obj):
        #
        # start with non hidden indices
        #
        self.accessor_cnt += 1
        cnt = len(obj.gl_icoord)
        minimum = int(obj.gl_icoord.min())
        maximum = int(obj.gl_icoord.max())

        data = obj.gl_icoord.tobytes()
        buf = self.addBufferView(self.ELEMENT_ARRAY_BUFFER, data)

        self.json["accessors"].append({"bufferView": buf, "componentType": self.UNSIGNED_INT, "count": cnt, "type": "SCALAR", "min": [minimum], "max": [maximum]})
        return(self.accessor_cnt)

    def pbrMaterial(self):
        return ({ "baseColorFactor": [ 0.5, 0.5, 0.5, 1.0 ], "metallicFactor": 0.5, "roughnessFactor": 0.5 })

    def addMaterial(self, name):
        self.material_cnt += 1
        material = self.pbrMaterial()       # dummy
        self.json["materials"].append({"name": self.nodeName(name), "pbrMetallicRoughness": material})
        return (self.material_cnt)

    def addMesh(self, obj, nodenumber):
        self.mesh_cnt += 1
        pos = self.addPosAccessor(obj)
        texcoord = self.addTPosAccessor(obj)
        ind = self.addIndAccessor(obj)
        self.json["meshes"].append({"primitives": [ {"attributes": { "POSITION": pos, "TEXCOORD_0": texcoord  }, "indices": ind, "material": nodenumber, "mode": self.TRIANGLES }]})
        return (self.mesh_cnt)

    def addNodes(self, baseclass):
        #
        # add the basemesh itself, the other nodes will be children
        # here one node will always have one mesh
        #
        mat  = self.addMaterial(baseclass.skinMaterialName)
        mesh = self.addMesh(baseclass.baseMesh, mat)
        self.json["nodes"].append({"name": self.nodeName(baseclass.baseMesh.filename), "mesh": mesh,  "children": []  })
        self.json["scenes"][0]["nodes"].append(0)
        children = self.json["nodes"][0]["children"]

        i = 1
        for elem in baseclass.attachedAssets:
            mat =  self.addMaterial(elem.material)
            mesh = self.addMesh(elem.obj, mat)
            self.json["nodes"].append({"name": self.nodeName(elem.filename), "mesh": mesh })
            children.append(i)
            i += 1

        
        self.json["buffers"].append({"byteLength": self.bufferoffset})
        print (self)


    def binSave(self, filename):
        #
        # binary glTF is:
        # 4 byte magic, 4 byte version + 4 byte length over all (which is the header)
        # JSON chunk:
        # chunklenght 4 Byte, chunk type JSON, chunkData (4 Byte boundaries, padding)
        # BIN chunk:
        # chunklenght 4 Byte, chunk type JSON, chunkData (4 Byte boundaries, padding)


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

