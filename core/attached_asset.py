import os


class attachedAsset:
    def __init__(self, env, glob):
        self.env = env
        self.glob = glob
        self.tags = []
        self.version = 110
        self.z_depth = 50

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
        self.env.logLine(3, "Load: " + filename)
        try:
            fp = open(filename, "r", encoding="utf-8", errors='ignore')
        except IOError as err:
            return (False, str(err))

        for line in fp:
            words = line.split()

            # skip white space and comments
            #
            if len(words) == 0 or words[0].startswith('#'):
                continue

            key = words[0]
            key = key[:-1] if key.endswith(":") else key

            if key == "verts":
                continue
            if key == "weights":
                continue
            elif key == "delete_verts":
                continue

            if len(words) < 2:
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

        if self.obj_file is None:
            return(False, "Obj-File is missing")
        return (True, "Okay")
