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
        self.normals = normals
        self.helper = helper

        self.coordlines = []
        self.normlines = []
        self.uvlines = []
        self.obj = []

    def addCoords(self, coords):
        #
        # TODO offset

        mcoord = np.reshape(coords, (len(coords)//3,3))
        for co in mcoord:
            self.coordlines.append("v %.4f %.4f %.4f\n" % tuple(co * self.scale))

    def addUVCoords(self, coords):
        mcoord = np.reshape(coords, (len(coords)//2,2))
        for co in mcoord:
            self.uvlines.append("vt %.6f %.6f\n" % tuple(co))

    def ascSave(self, baseclass, filename):

        header = "# MakeHuman exported OBJ\n# www.makehumancommunity.org\n\n"


    def ascSave(self, baseclass, filename):

        header = "# MakeHuman exported OBJ\n# www.makehumancommunity.org\n\n"

        # TODO Materials

        # collect objects:
        #
        if baseclass.proxy is None:
            obj = baseclass.baseMesh
            self.obj.append(obj.getVisGeometry(self.hiddenverts))

        for elem in baseclass.attachedAssets:
            self.obj.append(elem.obj.getVisGeometry(self.hiddenverts))

        # vertices
        # order of self.obj = (coords, uvcoords, vpface, faces, overflows)
        #
        for obj in self.obj:
            self.addCoords(obj[0])

        if self.normals:
            # normals
            pass

        # UVs
        #
        for obj in self.obj:
            self.addUVCoords(obj[1])


        # faces
        if self.normals:
            # TRI-MESH
            pass
        else:
            # original mesh
            pass

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

                # TODO Rest

        except IOError as error:
            self.env.last_error = str(error)
            return False

        # save material extra

        return True
                               

