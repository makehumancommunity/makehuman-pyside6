import os
import json
import struct
import numpy as np

class gltfExport:
    def __init__(self, glob, exportfolder):

        # subfolder for textures
        #
        self.imagefolder = "textures"
        self.exportfolder = exportfolder
        self.env = glob.env

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

    def addNormAccessor(self, obj):
        self.accessor_cnt += 1

        cnt = len(obj.gl_norm) // 3
        meshCoords = np.reshape(obj.gl_norm, (cnt,3))
        minimum = meshCoords.min(axis=0).tolist()
        maximum = meshCoords.max(axis=0).tolist()

        data = obj.gl_norm.tobytes()
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

    def pbrMaterial(self, color):
        return ({ "baseColorFactor": [ color[0], color[1], color[2], 1.0 ], "metallicFactor": 0.5, "roughnessFactor": 0.5 })

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

    def addTexture(self, texture):
        self.texture_cnt += 1
        (okay, image) = self.addImage(texture)
        if not okay:
            return (None)
        self.json["textures"].append({"sampler": 0, "source": image})
        return ({ "baseColorTexture": { "index": self.texture_cnt }, "metallicFactor": 0.5, "roughnessFactor": 0.5 })

    def addMaterial(self, material):
        """
        :param material:  material from opengl.material
        TODO: alphaMode, alphaCutoff, doubleSided
        """
        self.material_cnt += 1
        name = material.name if  material.name is not None else "generic"
        if material.has_imagetexture:
            print ("we need a texture")
            print (material.diffuseTexture)
            pbr = self.addTexture(material.diffuseTexture)
        else:   
            pbr = self.pbrMaterial(material.diffuseColor)

        if pbr is None:
            return(-1)
        if material.has_imagetexture:
            self.json["materials"].append({"name": self.nodeName(name), "alphaMode":"BLEND", "doubleSided":True, "pbrMetallicRoughness": pbr})
        else:   
            self.json["materials"].append({"name": self.nodeName(name), "pbrMetallicRoughness": pbr})
        return (self.material_cnt)

    def addMesh(self, obj, nodenumber):
        self.mesh_cnt += 1
        pos = self.addPosAccessor(obj)
        texcoord = self.addTPosAccessor(obj)
        norm = self.addNormAccessor(obj)
        ind = self.addIndAccessor(obj)
        self.json["meshes"].append({"primitives": [ {"attributes": { "POSITION": pos, "NORMAL": norm, "TEXCOORD_0": texcoord  }, "indices": ind, "material": nodenumber, "mode": self.TRIANGLES }]})
        return (self.mesh_cnt)

    def addNodes(self, baseclass):
        #
        # add the basemesh itself, the other nodes will be children
        # here one node will always have one mesh
        #
        baseobject = baseclass.baseMesh
        mat  = self.addMaterial(baseobject.material)
        if mat == -1:
            return (False)

        mesh = self.addMesh(baseobject, mat)
        self.json["nodes"].append({"name": self.nodeName(baseobject.filename), "mesh": mesh,  "children": []  })
        self.json["scenes"][0]["nodes"].append(0)
        children = self.json["nodes"][0]["children"]

        i = 1
        for elem in baseclass.attachedAssets:
            mat =  self.addMaterial(elem.obj.material)
            if mat == -1:
                return (False)
            mesh = self.addMesh(elem.obj, mat)
            self.json["nodes"].append({"name": self.nodeName(elem.filename), "mesh": mesh })
            children.append(i)
            i += 1

        
        self.json["buffers"].append({"byteLength": self.bufferoffset})
        print (self)
        return (True)


    def binSave(self, baseclass, filename):
        #
        # binary glTF is:
        # 4 byte magic, 4 byte version + 4 byte length over all (which is the header)
        # JSON chunk:
        # chunklenght 4 Byte, chunk type JSON, chunkData (4 Byte boundaries, padding)
        # BIN chunk:
        # chunklenght 4 Byte, chunk type JSON, chunkData (4 Byte boundaries, padding)
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
