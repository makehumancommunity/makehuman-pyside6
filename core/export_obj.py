"""
wavefront exporter
"""

import numpy as np

class objExport:
    def __init__(self, glob, exportfolder, hiddenverts=False, onground=True, helper=False, normals=False, scale =0.1):
        self.exportfolder = exportfolder
        self.glob = glob
        self.env = glob.env
        self.hiddenverts = hiddenverts
        self.onground = onground
        self.scale = scale
        self.lowestPos = 0.0
        self.normals = normals
        self.helper = helper

        self.coordlines = []
        self.normlines = []
        self.uvlines = []
        self.facelines = []

        self.startvert = 1
        self.startuv = 1

        self.obj = []

    def addCoords(self, num, coords):
        mcoord = np.reshape(coords, (len(coords)//3,3))
        for co in mcoord:
            self.coordlines.append("v %.4f %.4f %.4f\n" % (co[0]*self.scale, co[1]*self.scale -self.lowestPos, co[2]*self.scale))
        self.obj[num]["lenV"] = len(mcoord)

    def addUVCoords(self, num, coords):
        mcoord = np.reshape(coords, (len(coords)//2,2))
        for co in mcoord:
            self.uvlines.append("vt %.6f %.6f\n" % (co[0], 1.0 -co[1]))
        self.obj[num]["lenUV"] = len(mcoord)

    def addFaces(self, num, name, vpf, faces, ov):
        self.facelines.append("g %s\n" % name)
        overflow = {}
        for l in ov:
            overflow[l[1]] = l[0]
        x = 0
        for n in vpf:
            out = "f "
            for i in range(n):
                uvface = faces[x]
                face = overflow[uvface] if uvface in overflow else uvface

                out += "%d/%d " % (face+self.startvert, uvface+self.startuv)
                x += 1
            self.facelines.append(out + "\n")

        self.startvert += self.obj[num]["lenV"]
        self.startuv   += self.obj[num]["lenUV"]

    def ascSave(self, baseclass, filename):

        header = "# MakeHuman exported OBJ\n# www.makehumancommunity.org\n\n"

        # TODO Materials

        # collect objects:
        #
        if self.onground:
            self.lowestPos = baseclass.getLowestPos() * self.scale

        if baseclass.proxy is None:
            obj = baseclass.baseMesh
            (coords, uvcoords, vpface, faces, overflow) = obj.getVisGeometry(self.hiddenverts)
            self.obj.append ({"name": "base", "c": coords, "uv": uvcoords, "vpf": vpface, "f": faces, "o": overflow })

        for elem in baseclass.attachedAssets:
            (coords, uvcoords, vpface, faces, overflow) = elem.obj.getVisGeometry(self.hiddenverts)
            self.obj.append ({"name": elem.obj.name, "c": coords, "uv": uvcoords, "vpf": vpface, "f": faces, "o": overflow })

        # vertices
        #
        for i, obj in enumerate(self.obj):
            self.addCoords(i, obj["c"])

        if self.normals:
            # normals
            pass

        # UVs
        #
        for i, obj in enumerate(self.obj):
            self.addUVCoords(i, obj["uv"])


        # faces
        if self.normals:
            # TRI-MESH
            pass
        else:
            for i, obj in enumerate(self.obj):
                self.addFaces(i, obj["name"], obj["vpf"], obj["f"], obj["o"])

        # each mesh forms a group with own material

        try:
            with open(filename, 'w', encoding="utf-8") as f:
                f.write(header)
                for line in self.coordlines:
                    f.write(line)
                for line in self.normlines:
                    f.write(line)
                for line in self.uvlines:
                    f.write(line)
                for line in self.facelines:
                    f.write(line)

                # TODO Rest

        except IOError as error:
            self.env.last_error = str(error)
            return False

        # save material extra

        return True
                               

