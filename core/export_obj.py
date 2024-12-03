"""
wavefront exporter
"""



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

    def ascSave(self, baseclass, filename):

        header = "# MakeHuman exported OBJ\n# www.makehumancommunity.org\n\n"

        # TODO Materials

        # vertices
        if self.normals:
            # TRI-MESH
            pass
        else:
            # original mesh
            pass

        if self.normals:
            # normals
            pass

        # uv

        # faces
        # each mesh forms a group with own material

        try:
            with open(filename, 'w', encoding="utf-8") as f:
                f.write(header)
                # TODO Rest

        except IOError as error:
            self.env.last_error = str(error)
            return False

        # save material extra

        return True
                               

