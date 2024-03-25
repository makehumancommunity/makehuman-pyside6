import os
import numpy as np
from core.debug import dumper
from obj3d.fops_binary import exportObj3dBinary, importObjValues
from obj3d.object3d  import object3d


class referenceVerts:
    def __init__(self):
        pass

    def __str__(self):
        return("N:"+ str(self._verts) + " W:" + str(self._weights) + " O:" + str(self._offset))

    def identicalValue(self, words, vnum, vertWeights):
        v0 = int(words[0])
        self._verts = (v0,0,1)
        self._weights = (1.0,0.0,0.0)
        self._offset = np.zeros(3, float)
        if v0 in vertWeights:
            vertWeights[v0].append((vnum, 1))
        else:
            vertWeights[v0] = [(vnum,1)]
        return self

    def fromTriple(self, words, vnum, vertWeights):
        v0 = int(words[0])
        v1 = int(words[1])
        v2 = int(words[2])
        w0 = float(words[3])
        w1 = float(words[4])
        w2 = float(words[5])
        if len(words) > 6:
            d0 = float(words[6])
            d1 = float(words[7])
            d2 = float(words[8])
        else:
            (d0,d1,d2) = (0,0,0)

        self._verts = (v0,v1,v2)
        self._weights = (w0,w1,w2)
        self._offset = np.array((d0,d1,d2), float)

        if v0 in vertWeights:
            vertWeights[v0].append((vnum, w0))
        else:
            vertWeights[v0] = [(vnum,w0)]

        if v1 in vertWeights:
            vertWeights[v1].append((vnum, w1))
        else:
            vertWeights[v1] = [(vnum,w1)]

        if v2 in vertWeights:
            vertWeights[v2].append((vnum, w2))
        else:
            vertWeights[v2] = [(vnum,w2)]

        return self


class attachedAsset:
    def __init__(self, glob, eqtype):
        self.glob = glob
        self.env = glob.env
        self.type = eqtype          # asset type
        self.tags = []
        self.version = 110
        self.z_depth = 50
        self.obj = None             # will contain the object3d class
        self.vertWeights = {}       # will contain the parent weight
        self.description = ""
        self.license = ""
        self.author = ""
        self.uuid = ""
        self.meshtype = self.env.basename  # for binary saving

                                    # numpy arrays
        self.ref_vIdxs = None       # (Vidx1,Vidx2,Vidx3) list with references to human vertex indices, indexed by reference vert
        self.weights = None         # (w1,w2,w3) list, with weights per human vertex (mapped by ref_vIdxs), indexed by reference vert
        self.offsets = None         # (x,y,z) list of vertex offsets, indexed by reference vert
        self.deleteVerts = None     # will contain vertices to delete
        self.material = None        # path material, fully qualified
        self.vertexboneweights_file = None # path to vbone file
        self.materialsource = None    # path material, relative
        self.base_verts = self.glob.baseClass.baseMesh.n_origverts

    def __str__(self):
        return(dumper(self))

    def textLoad(self, filename):
        """
        will usually load an mhclo-file
        structure is a key/value system + rows of verts in the end
        """
        self.env.logLine(8, "Load: " + filename)

        try:
            fp = open(filename, "r", encoding="utf-8", errors='ignore')
        except IOError as err:
            return (False, str(err))

        self.filename = filename
        #
        # status = 0, read normal
        #          1, read vertices
        #          2, read weights
        #          3, read delete_verts
        #
        status = 0
        refVerts = [] # local reference for vertices
        vnum   = 0    # will contain the vertex number (counting from 0 to x)
        self.deleteVerts = np.zeros(self.base_verts, bool)

        for line in fp:
            words = line.split()

            # skip white space and comments
            #
            if len(words) == 0 or words[0].startswith('#'):
                continue

            key = words[0]
            key = key[:-1] if key.endswith(":") else key

            if key == "verts":
                status = 1
                continue
            if key == "weights":
                status = 2
                continue
            elif key == "delete_verts":
                status = 3
                continue

            if status == 1:
                if key.isnumeric():
                    refVert = referenceVerts()
                    refVerts.append(refVert)
                    if len(words) == 1:
                        value = refVert.identicalValue(words, vnum, self.vertWeights)
                    else:
                        refVert.fromTriple(words, vnum, self.vertWeights)
                    vnum += 1
                    continue

            elif status == 2:
                #
                # to do representation of weights
                #
                continue

            elif status == 3:

                # delete vertices
                #
                sequence = False
                for v in words:
                    if v == "-":
                        sequence = True
                    else:
                        v1 = int(v)
                        if sequence:
                            for vn in range(v0,v1+1):
                                self.deleteVerts[vn] = True
                            sequence = False
                        else:
                            self.deleteVerts[v1] = True
                        v0 = v1

                continue

            if len(words) < 2:
                continue

            if key in ["name", "uuid", "description", "author", "license", "homepage"]:
                setattr (self, key, " ".join(words[1:]))
            elif key == "tag":
                self.tags.append(" ".join(words[1:]).encode('ascii', 'ignore').lower().decode("utf-8"))
            elif key in ["obj_file", "material", "vertexboneweights_file"]:
                setattr (self, key, words[1])
            elif key in ["version", "z_depth"]:
                setattr (self, key, int(words[1]))

            elif key == 'x_scale':
                #self.tmatrix.getScaleData(words, 0)
                pass
            elif key == 'y_scale':
                #self.tmatrix.getScaleData(words, 1)
                pass
            elif key == 'z_scale':
                #self.tmatrix.getScaleData(words, 2)
                pass

        fp.close()
        print (self)
        #for elem in refVerts:
        #    print (elem)

        if self.obj_file is None:
            return(False, "Obj-File is missing")

        self.obj_file = os.path.join(os.path.dirname(filename), self.obj_file)
        if self.material is not None:
            self.material_orgpath = self.material
            self.material = os.path.normpath(os.path.join(os.path.dirname(filename), self.material))
        else:
            self.material_orgpath = ""
        print(self.obj_file)
        print("Material: " + str(self.material))
        # finally create the numpy arrays here
        #
        self.weights = np.asarray([v._weights for v in refVerts], dtype=np.float32)
        self.ref_vIdxs = np.asarray([v._verts for v in refVerts], dtype=np.uint32)
        self.offsets = np.asarray([v._offset for v in refVerts], dtype=np.float32)

        return (True, "Okay")

    def importBinary(self, path):
        print ("read binary " + path)
        npzfile = np.load(path)
        for elem in ['asset', 'files', 'ref_vIdxs', 'weights']:
            if elem not in npzfile:
                error =  "Malformed file, missing component " + elem
                return (False, error)

        # now get data from binary, asset
        #
        asset = list(npzfile['asset'][0])
        self.name        = asset[0].decode("utf-8")
        self.uuid        = asset[1].decode("utf-8")
        self.author      = asset[2].decode("utf-8")
        self.description = asset[3].decode("utf-8")
        self.meshtype    = asset[4].decode("utf-8")
        nrefverts        = asset[5]
        self.version     = asset[6]
        self.z_depth     = asset[7]
        self.license     = asset[8].decode("utf-8")
        self.tags        = asset[9].decode("utf-8").split("|")

        if nrefverts == 3 and 'offsets' not in npzfile:
            error =  "Malformed file, missing component offsets"
            return (False, error)

        files = list(npzfile['files'][0])
        self.material = files[0].decode("utf-8")
        vwfile        = files[1].decode("utf-8")
        if len(vwfile) == 0:
            self.vertexboneweights_file = None
        else:
            self.vertexboneweights_file = vwfile

        if nrefverts == 3:
            self.ref_vIdxs = npzfile["ref_vIdxs"]
            self.offsets   = npzfile["offsets"]
            self.weights   = npzfile["weights"]
        else:
            num_refs = npzfile['ref_vIdxs'].shape[0]
            self.ref_vIdxs = np.zeros((num_refs,3), dtype=np.uint32)
            self.ref_vIdxs[:,0] = npzfile['ref_vIdxs']
            self.offsets = np.zeros((num_refs,3), dtype=np.float32)
            self.weights = np.zeros((num_refs,3), dtype=np.float32)
            self.weights[:,0] = npzfile['weights']

        if "deleteVerts" in npzfile:
            self.deleteVerts = npzfile["deleteVerts"]

        self.obj_file = path
        if self.material is not None:
            self.material_orgpath = self.material
            self.material = os.path.normpath(os.path.join(os.path.dirname(path), self.material))
        else:
            self.material_orgpath = ""

        importObjValues(npzfile, self.obj)


    def load(self, filename, use_mhclo=False):

        if use_mhclo is False and filename.endswith(".mhclo"):
            binfile = filename[:-5] + "mhbin"
            if os.path.isfile(binfile):
                print ("we have a binary file")
                self.filename = filename
                self.obj = object3d(self.glob, None)
                self.importBinary(binfile)
                self.obj.filename = filename
                self.obj.initMaterial(filename)
                return (self, None)

        (res, err) = self.textLoad(filename)
        if res is True:
            print ("Object is:" + self.obj_file)
            obj = object3d(self.glob, None)
            (res, err) = obj.load(self.obj_file)
            if res is True:
                self.obj = obj
                return (self, None)

        self.env.logLine(1, err )
        return (None, err)

    def exportBinary(self, filename=None):

        filename = self.filename if filename is None  else filename
        filename = filename[:-6] + ".mhbin" if filename.endswith(".mhclo") else filename + ".mhbin"
        content = {}

        # binary structure
        # first header
        mtags = "|".join(self.tags)
        ltags = "|S" + str(len(mtags))

        lname = "|S" + str(len(self.name))
        llics = "|S" + str(len(self.license))
        luuid = "|S" + str(len(self.uuid))
        lauth = "|S" + str(len(self.author))
        ldesc = "|S" + str(len(self.description))
        lmesh = "|S" + str(len(self.meshtype))

        nrefverts = 3 if self.weights[:,1:].any() else 1

        asset_type = np.dtype({'names':('name', 'uuid', 'author', 'description', 'meshtype', 'refverts', 'version', 'zdepth', 'license', 'tags'),
            'formats':(lname, luuid, lauth, ldesc, lmesh, 'i4', 'i4', 'i4', llics, ltags)})
        content["asset"] = np.array([(self.name, self.uuid, self.author, self.description, self.meshtype, nrefverts, self.version,
            self.z_depth, self.license, mtags)], dtype=asset_type)

        lmat = "|S" + str(len(self.material))
        if self.vertexboneweights_file is None:
            vwfile = ""
        else:
            vwfile = self.vertexboneweights_file
        lweight = "|S" + str(len(vwfile))

        files_type = np.dtype({'names':('material', 'weight'), 'formats': (lmat, lweight)})
        content["files"] =  np.array([(self.material_orgpath, vwfile)], dtype=files_type)

        if nrefverts == 3:
            content["ref_vIdxs"] = self.ref_vIdxs
            content["offsets"] = self.offsets
            content["weights"] = self.weights
        else:
            content["ref_vIdxs"] = self.ref_vIdxs[:,0]
            content["weights"] = self.weights[:,0]

        if np.any(self.deleteVerts):
            content["deleteVerts"] = self.deleteVerts

        return(exportObj3dBinary(filename, self.obj, content))

