import bpy
import json
import os
import struct
from bpy_extras.io_utils import (ImportHelper, ExportHelper)
from mathutils import Vector
from bpy.props import StringProperty
from .materials import MH2B_OT_Material

class MH2B_OT_Loader:
    def __init__(self, context, subsurf):
        self.context = context
        self.firstnode = 0
        self.firstname = "unknown"
        self.collection = None
        self.bufferoffset = 0
        self.subsurf = subsurf

    def activateObject(self, ob):
        scn = self.context.scene
        for ob1 in scn.collection.objects:
            ob1.select_set(False)
        ob.select_set(True)
        self.context.view_layer.objects.active = ob

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

        if "OVERFLOW" in attrib:
            ov   = attrib['OVERFLOW']
            buffers.append ({ "type": "O", "start": jdata["bufferViews"][ov]["byteOffset"], "len": jdata["bufferViews"][ov]["byteLength"] })

        bufs = len(buffers)
        # TODO: find less stupid method
        #
        for cnt in range(0,bufs):
            for elem in range(0,bufs):
                if buffers[elem]["start"] == self.bufferoffset:
                    length = buffers[elem]["len"]
                    print (buffers[elem]["type"] + " need to read " + str(length) + " bytes")
                    buffers[elem]["data"] = fp.read(length)
                    self.bufferoffset += length
                    break

        overflow = {}
        # now the conversions will be done (replacement)
        for cnt in range(0,bufs):
            t = buffers[cnt]["type"]
            b = []
            if t == "P":
                m = struct.iter_unpack('<fff',  buffers[cnt]["data"])
                for l in m:
                    b.append((l[0], -l[2], l[1]))
                buffers[cnt]["data"] = b
            elif t == "U":
                m = struct.iter_unpack('<ff',  buffers[cnt]["data"])
                for l in m:
                    b.append(l)
                buffers[cnt]["data"] = b
            elif t == "V":
                m = struct.iter_unpack('<i',  buffers[cnt]["data"])
                for l in m:
                    b.append(l)
                buffers[cnt]["data"] = b
            elif  t == "F":
                m = struct.iter_unpack('<i',  buffers[cnt]["data"])
                for l in m:
                    b.append(l)
                buffers[cnt]["data"] = b
            else:
                m = struct.iter_unpack('<ii',  buffers[cnt]["data"])
                for l in m:
                    overflow[l[1]] = l[0]

        print ("calculate faces and uvs")
        b = []
        uv = []
        maxp =  len(buffers[0]["data"])
        vpb = buffers[1]["data"]
        face = buffers[2]["data"]

        n = 0
        for nfaces in vpb:
            l = nfaces[0]
            c = []
            u = []
            faceok = True
            for i in range(0,l):
                v = face[n][0]
                n += 1
                u.append(v)
                if v in overflow:
                    v = overflow[v]
                if v >= maxp:
                    faceok = False
                c.append(v)
            if faceok:
                b.append(tuple(c))
                uv.append(tuple(u))

        bufarr = [buffers[0]["data"], b, buffers[3]["data"], uv]
        return (bufarr)
                

    def getMesh(self, jdata, name, num, fp, dirname):
        m = jdata["meshes"][num]["primitives"][0]   # only one primitive
        attributes = m["attributes"]
        (coords, faces, uvdata, uvfaces)  = self.getBuffers(jdata, attributes, fp)

        mesh = bpy.data.meshes.new(name)
        nobject = bpy.data.objects.new(name, mesh)
        mesh.from_pydata( coords, [], faces, shade_flat=False)

        mesh.uv_layers.new()
        uvlayer =  mesh.uv_layers[0]
        n=0
        for face in uvfaces:
            for vert in face:
                uvlayer.data[n].uv = (uvdata[vert][0], 1.0 - uvdata[vert][1])
                n += 1

        if "material" in m:
            material =  m["material"]
            mclass = MH2B_OT_Material(dirname)
            blendmat = mclass.addMaterial(jdata, material)
            nobject.data.materials.append(blendmat)

        if self.subsurf is True:
            modifier = nobject.modifiers.new(name="Subdivision", type='SUBSURF')

        return(nobject)

    def getSkeleton(self, jdata, fp):
        """
        read restmatrix in case of skeleton not break importer
        """
        skel =  jdata["skeleton"]
        restmatnum = skel["RESTMAT"]
        length = jdata["bufferViews"][restmatnum]["byteLength"] 
        print ("restmat need to read " + str(length) + " bytes")
        restmat = fp.read(length)
        self.bufferoffset += length

        amt = bpy.data.armatures.new(skel["name"])
        rig = bpy.data.objects.new(skel["name"], amt)
        setattr(amt, "display_type", 'STICK')
        setattr(rig, "show_in_front" , True)
        self.collection.objects.link(rig)
        self.activateObject(rig)

        bpy.ops.object.mode_set(mode='EDIT')
        for bone in skel["bones"]:
            eb = amt.edit_bones.new(bone["name"])
            h = bone["head"]
            t = bone["tail"]
            eb.head = Vector((h[0], -h[2], h[1]))
            eb.tail = Vector((t[0], -t[2], t[1]))
            if "parent" in bone:
                eb.parent = amt.edit_bones[bone["parent"]]
            print (bone)

        bpy.ops.object.mode_set(mode='OBJECT')




    def createObjects(self, jdata, fp, dirname):
        #
        # just creates meshes and skeleton, use an array
        # optimized to read the buffer only once
        #
        self.bufferoffset = 0
        nodes = []
        n = jdata["nodes"][self.firstnode]
        nodes.append([self.firstname, n["mesh"]])
        lastmesh = n["mesh"]
        children = n["children"]
        if "skeleton" in jdata:
            nodes.append(["skeleton", None])
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
            if elem[1] is None:
                skeleton = self.getSkeleton(jdata, fp)
            else:
                mesh = self.getMesh(jdata, elem[0], elem[1], fp, dirname)
                self.collection.objects.link(mesh)

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
            # print(json.dumps(jdata, indent=3))

            lenbin = f.read(4)
            lenbin = struct.unpack('<I', lenbin)
            print ("Binlen = " + str(lenbin))

            magic = f.read(4)
            if magic != b'BIN\x00':
                f.close()
                return(False, "bad binary header")

            self.createCollection(jdata)
            self.createObjects(jdata, f, os.path.dirname(props.filepath))


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
        scn = context.scene
        mh2b = MH2B_OT_Loader(context, scn.MH2B_subdiv)
        res, err = mh2b.loadMH2B(self.properties)
        if res is False:
            self.report({'ERROR'}, "File is not a valid mh2b file. " + err)
        else:
            self.report({'INFO'}, "File loaded.")
        return {'FINISHED'}

