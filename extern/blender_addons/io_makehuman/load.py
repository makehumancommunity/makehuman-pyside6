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

    def createObjects(self, jdata):
        #
        # just creates empties (will be change to a mesh soon)
        #
        empty = bpy.data.objects.new(self.firstname, None)  # Create new empty object
        empty.empty_display_type = 'PLAIN_AXES'
        self.collection.objects.link(empty)
        children = jdata["nodes"][self.firstnode]["children"]
        for elem in children:
            name = jdata["nodes"][elem]["name"]
            empty = bpy.data.objects.new(name, None)
            self.collection.objects.link(empty)

    def loadMH2B(self, props):
        with open(props.filepath, 'rb') as f:
            # it starts with a 12 byte header
            #
            magic = f.read(4)
            if magic != b'MH2B':
                close(f)
                return(False, "bad header")
            vers = f.read(4)
            vers = struct.unpack('<I', vers)
            if vers[0] != 1:
                close(f)
                return (False, "bad version number, must be 1")

            filelen = f.read(4)
            filelen = struct.unpack('<I', filelen)[0]

            # then json must be loaded, size + header = 8 byte
            #
            jsonlen = f.read(4)
            jsonlen = struct.unpack('<I', jsonlen)[0]

            jsonmark = f.read(4)
            if jsonmark != b'JSON':
                close(f)
                return (False, "JSON chunk expected")
            jsontext = f.read(jsonlen).decode("ascii")
            jdata = json.loads(jsontext)
            print(json.dumps(jdata, indent=3))
            self.createCollection(jdata)
            self.createObjects(jdata)


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

