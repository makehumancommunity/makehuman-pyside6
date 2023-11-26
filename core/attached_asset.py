import os
import numpy as np

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


class attachedAsset:
    def __init__(self, glob):
        self.glob = glob
        self.env = glob.env
        self.tags = []
        self.version = 110
        self.z_depth = 50
        self.obj = None             # will contain the object3d class
        self.vertWeights = {}       # will contain the parent weight

                                    # numpy arrays
        self.ref_vIdxs = None       # (Vidx1,Vidx2,Vidx3) list with references to human vertex indices, indexed by reference vert
        self.weights = None         # (w1,w2,w3) list, with weights per human vertex (mapped by ref_vIdxs), indexed by reference vert
        self.offsets = None         # (x,y,z) list of vertex offsets, indexed by reference vert


    def __str__(self):
        text = ""
        for attr in dir(self):
            if not attr.startswith("__"):
                m = getattr(self, attr)
                if isinstance(m, int) or isinstance(m, str) or  isinstance(m, list):
                    text += (" %s = %r\n" % (attr, m))
        return(text)

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

        #
        # status = 0, read normal
        #          1, read vertices
        #
        status = 0
        refVerts = [] # local reference for vertices
        vnum   = 0    # will contain the vertex number (counting from 0 to x)

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
                continue
            elif key == "delete_verts":
                continue

            if status == 1:
                refVert = referenceVerts()
                refVerts.append(refVert)
                if len(words) == 1:
                    value = refVert.identicalValue(words, vnum, self.vertWeights)
                #else:
                    #refVert.fromTriple(words, vnum, proxy.vertWeights)
                vnum += 1

            if len(words) < 2 or status > 0:
                continue

            if key in ["name", "uuid", "description", "author", "license", "homepage"]:
                setattr (self, key, " ".join(words[1:]))
            elif key == "tag":
                self.tags.append( " ".join(words[1:]).lower() )
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

        # finally create the numpy arrays here
        #
        self.weights = np.asarray([v._weights for v in refVerts], dtype=np.float32)
        self.ref_vIdxs = np.asarray([v._verts for v in refVerts], dtype=np.uint32)
        self.offsets = np.asarray([v._offset for v in refVerts], dtype=np.float32)

        return (True, "Okay")
