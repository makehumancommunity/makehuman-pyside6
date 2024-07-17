import bpy
import json
import struct
import bpy
from bpy_extras.io_utils import (ImportHelper, ExportHelper)
from bpy.props import StringProperty

class MH2B_OT_Loader:
    def __init__(self, context):
        self.context = context
        self.firstnode = 0
        self.firstname = "unknown"
        self.collection = None
        self.bufferoffset = 0

    def createCollection(self, jdata):
        #
        # get collection name from the referenced asset in nodes
        #
        self.firstnode = jdata["asset"]["nodes"][0]
        self.firstname = jdata["nodes"][self.firstnode]["name"]

        # create a new collection and add it to scene
        self.collection  = bpy.data.collections.new(self.firstname)
        self.context.scene.collection.children.link(self.collection )
        return (self.collection )

    def getBuffers(self, jdata, attrib, fp):
        pos  = attrib['POSITION']
        vpf  = attrib['VPF']
        face = attrib['FACE']
        uv   = attrib['TEXCOORD_0']
        buffers = [
                { "type": "P", "start": jdata["bufferViews"][pos]["byteOffset"], "len": jdata["bufferViews"][pos]["byteLength"] },
                { "type": "V", "start": jdata["bufferViews"][vpf]["byteOffset"], "len": jdata["bufferViews"][vpf]["byteLength"] },
                { "type": "F", "start": jdata["bufferViews"][face]["byteOffset"], "len": jdata["bufferViews"][face]["byteLength"] },
                { "type": "U", "start": jdata["bufferViews"][uv]["byteOffset"], "len": jdata["bufferViews"][uv]["byteLength"] }
                 ]

        # TODO: find less stupid method
        #
        for cnt in range(0,4):
            for elem in range(0,4):
                if buffers[elem]["start"] == self.bufferoffset:
                    print (buffers[elem]["type"])
                    length = buffers[elem]["len"]
                    print ("need to read " + str(length) + " bytes")
                    buffers[elem]["data"] = fp.read(length)
                    self.bufferoffset += length
                    break

        # now the conversions will done (replacement)
        fn = -1
        for cnt in range(0,4):
            t = buffers[cnt]["type"]
            if t == "P":
                print ("positions: must convert to floats, Positions")
            elif t == "U":
                print ("positions: must convert to floats, UV")
            elif t == "V":
                print ("VPF: must convert it to integers")
            else:
                print ("Keep Index from Face")
                fn = cnt

        print ("convert buffer " + str(fn) + " to faces tuples for from_pydata")

    def getMesh(self, jdata, num, fp):
        m = jdata["meshes"][num]["primitives"][0]   # only one primitive
        attributes = m["attributes"]
        self.getBuffers(jdata, attributes, fp)

    def createObjects(self, jdata, fp):
        #
        # just creates empties (will be change to a mesh soon), use an array
        # try to read buffers one after the other later
        #
        self.bufferoffset = 0
        nodes = []
        n = jdata["nodes"][self.firstnode]
        nodes.append([self.firstname, n["mesh"]])
        lastmesh = n["mesh"]
        children = n["children"]
        for elem in children:
            n = jdata["nodes"][elem]
            name = n["name"]
            mesh = n["mesh"]
            if mesh > lastmesh:
                nodes.append([name, mesh])
                lastmesh = mesh
            else:
                # TODO insert
                pass
        for elem in nodes:
            self.getMesh(jdata, elem[1], fp)
            empty = bpy.data.objects.new(elem[0], None)
            empty.empty_display_type = 'PLAIN_AXES'
            self.collection.objects.link(empty)

    def loadMH2B(self, props):
        with open(props.filepath, 'rb') as f:
            # it starts with a 12 byte header
            #
            magic = f.read(4)
            if magic != b'MH2B':
                f.close()
                return(False, "bad header")
            vers = f.read(4)
            vers = struct.unpack('<I', vers)
            if vers[0] != 1:
                f.close()
                return (False, "bad version number, must be 1")

            filelen = f.read(4)
            filelen = struct.unpack('<I', filelen)[0]

            # then json must be loaded, size + header = 8 byte
            #
            jsonlen = f.read(4)
            jsonlen = struct.unpack('<I', jsonlen)[0]

            jsonmark = f.read(4)
            if jsonmark != b'JSON':
                f.close()
                return (False, "JSON chunk expected")
            jsontext = f.read(jsonlen).decode("ascii")
            jdata = json.loads(jsontext)
            print(json.dumps(jdata, indent=3))

            lenbin = f.read(4)
            lenbin = struct.unpack('<I', lenbin)
            print ("Binlen = " + str(lenbin))

            magic = f.read(4)
            if magic != b'BIN\x00':
                f.close()
                return(False, "bad binary header")

            self.createCollection(jdata)
            self.createObjects(jdata, f)


        return (True, "okay")

class MH2B_OT_Load(bpy.types.Operator, ImportHelper):
    """Import MH2B file."""
    bl_idname = "mh2b.load"
    bl_label = "Load mh2b"
    bl_options = {'REGISTER'}
    filename_ext = ".mh2b"
    filter_glob: StringProperty(default="*.mh2b", options={'HIDDEN'})

    @classmethod
    def poll(self, context):
        return True

    def execute(self, context):
        mh2b = MH2B_OT_Loader(context)
        res, err = mh2b.loadMH2B(self.properties)
        if res is False:
            self.report({'ERROR'}, "File is not a valid mh2b file. " + err)
        else:
            self.report({'INFO'}, "File loaded.")
        return {'FINISHED'}

