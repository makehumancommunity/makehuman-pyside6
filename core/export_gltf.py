import os
import json

class gltfExport:
    def __init__(self):
        self.json = {}
        self.json["asset"] = {"generator": "makehuman2", "version": "2.0" }    # copyright maybe
        self.json["scenes"] = [ {"name": "makehuman2 export", "nodes": [] } ]  # one scene contains all nodes
        self.json["scene"] = 0 # fixed number (we only have on scene

        self.json["nodes"] = [] # list of nodes
        self.json["meshes"] = []

        self.json["accessors"] = []
        self.json["buffers"] = []
        self.json["bufferViews"] = []

        # skeleton 
        #
        self.json["skins"] = []
        #self.json["animations"] = []       # buffer?

        # texture and material (samplers are not needed)
        #
        self.json["materials"] = []
        self.json["textures"] = []
        self.json["images"] = []

    def __str__(self):
        return (json.dumps(self.json, indent=3))

    def nodeName(self, filename):
        fname = os.path.basename(filename)
        return(os.path.splitext(fname)[0])

    def addNodes(self, baseclass):
        #
        # add the basemesh itself, the other nodes will be children
        # here one node will always have one mesh
        #
        self.json["nodes"].append({"name": self.nodeName(baseclass.baseMesh.filename), "mesh": 0,  "children": []  })
        self.json["meshes"].append({"primitives": [ {"attributes": { "POSITION": 0 }, "material": 0, "mode": 4 }]})
        self.json["materials"].append({"name": self.nodeName(baseclass.skinMaterialName)})
        self.json["scenes"][0]["nodes"].append(0)
        children = self.json["nodes"][0]["children"]

        i = 1
        for elem in baseclass.attachedAssets:
            self.json["nodes"].append({"name": self.nodeName(elem.filename) })
            self.json["meshes"].append({"primitives": [ {"attributes": { "POSITION": i }, "material": i, "mode": 4 }]})
            self.json["materials"].append({"name": self.nodeName(elem.materialsource)})
            children.append(i)
            i += 1

        print (self)
