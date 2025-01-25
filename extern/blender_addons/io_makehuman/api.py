import socket
import json
import bpy
import os
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty

from .load import MH2B_OT_Loader


class API:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.json = None

    def connect(self, parent, info):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((self.host, self.port))
        except ConnectionRefusedError:
            error = "Connection refused"
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", info=info, error=error)
            parent.report({'ERROR'}, error)
            return False
        return True

    def getJSON(self):
        return self.json

    def getBinSize(self, parent):
        if "asset" in self.json and "buffersize"  in self.json["asset"]:
            return self.json["asset"]["buffersize"]
        error = "Binary buffer size is not defined"
        parent.report({'ERROR'}, error)
        bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", error=error)
        return 0

    def receive(self):
        data = ""
        while True:
            buf = self.client.recv(1024)
            if len(buf) > 0:
                data += buf.strip().decode('utf-8')
            else:
                break
        #print("received", data)
        return data

    def receive_bin(self):
        data = bytearray()
        while True:
            buf = self.client.recv(1024)
            if len(buf) > 0:
                data.extend(buf)
            else:
                break
        return data

    def send(self, function, params=None):
        print (function)
        js = { "function": function }
        if params:
            js["params"] = params
        txt = json.dumps(js)
        self.client.send (bytes(txt, 'utf-8'))

    def decodeAnswer(self, parent, function, data):
        try:
            self.json = json.loads(data)
        except json.JSONDecodeError as e:
            error = "JSON format error in string  > " + str(e)
            parent.report({'ERROR'}, error)
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", error=error)
            return False, None

        if not self.json:
            error = "Empty JSON string"
            parent.report({'ERROR'}, error)
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", error=error)
            return False, None

        if not "errcode" in self.json:
            error = "Missing error code in answer"
            parent.report({'ERROR'}, error)
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", error=error)
            return False, None

        if self.json["errcode"] != 0:
            error = self.json["errtext"] if "errtext" in self.json else "Errorcode " + str(self.json["errcode"])
            parent.report({'ERROR'}, error)
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", error=error)
            return False, None

        if function == "hello":
            info = "Application: " + self.json["application"] + "\n" + "Current model: " + self.json["name"]
            return True, info

        elif function == "getchar":
            info = "Get character"
            return True, info

        error = "Unknown command"
        parent.report({'ERROR'}, error)
        bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", error=error)
        return False, None


class MH2B_OT_Hello(bpy.types.Operator):
    """Test connection."""
    bl_idname = "mh2b.hello"
    bl_label = "Test communication"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(self, context):
        return True

    def execute(self, context):
        scn = context.scene
        info = "Test of connection to " + scn.MH2B_apihost + " Port " + str(scn.MH2B_apiport)
        res = True

        api = API(scn.MH2B_apihost, scn.MH2B_apiport)
        if not api.connect(self, info):
            return {'FINISHED'}

        api.send("hello")
        data = api.receive()

        res, text = api.decodeAnswer(self, "hello", data)
        if res is True:
            self.report({'INFO'}, text)
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", info=text)

        return {'FINISHED'}

class MH2B_OT_GetChar(bpy.types.Operator):
    """Get character."""
    bl_idname = "mh2b.getchar"
    bl_label = "Get character"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(self, context):
        return True

    def execute(self, context):
        scn = context.scene

        params = { "onground": scn.MH2B_feetonground, "hidden": scn.MH2B_gethiddenverts, \
                "anim": scn.MH2B_getanimation, "scale": float(scn.MH2B_getscale) }

        info = "Get character " + scn.MH2B_apihost + " Port " + str(scn.MH2B_apiport)
        res = True

        api = API(scn.MH2B_apihost, scn.MH2B_apiport)
        if not api.connect(self, info):
            return {'FINISHED'}

        api.send("getchar", params)
        data = api.receive()
        res, text = api.decodeAnswer(self, "getchar", data)
        if res is False:
            return {'FINISHED'}

        json = api.getJSON()
        print (json)

        buffersize = api.getBinSize(self)
        if buffersize == 0:
            return {'FINISHED'}

        api = API(scn.MH2B_apihost, scn.MH2B_apiport)
        if not api.connect(self, info):
            return {'FINISHED'}

        api.send("bin_getchar")
        bindata = api.receive_bin()
        l = len(bindata)
        if l != buffersize:
            error = "Expected amount of binary data " +str(buffersize) + " unequal to received amount " + str(l)
            self.report({'ERROR'}, error)
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", error=error)
            return {'FINISHED'}

        mh2b = MH2B_OT_Loader(context)
        mh2b.createCollection(json)
        if not mh2b.createObjects(json, bindata, None):
            error = "Bad structure"
            self.report({'ERROR'}, error)
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", error=error)
            return {'FINISHED'}

        text = "Got JSON description and " + str(l) + " bytes of binary data"
        self.report({'INFO'}, text)
        return {'FINISHED'}

class MH2B_OT_AssignProject(bpy.types.Operator, ExportHelper):
    '''Assign a folder for project'''
    bl_idname = "mh2b.assignprojdir"
    bl_label = 'Assign folder for project'
    bl_options = {'REGISTER'}
    filter_glob : StringProperty(default='*.blend', options={'HIDDEN'})
    filename_ext = ".blend"


    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        scn = context.scene
        layout = self.layout
        try:
            folder = scn.MH2B_projdir
        except:
            folder = "none"
        layout.label(text="Current project:")
        layout.label(text=folder)


    def invoke(self, context, event):
        return super().invoke(context, event)

    def execute(self, context):
        # try directly but allow only directories
        #
        scn = context.scene
        f = self.properties.filepath

        if os.path.isfile(f):
            scn.MH2B_projdir = os.path.dirname(f)
            fname = f
        else:
            scn.MH2B_projdir = f
            fname = os.path.join(f, "untitled.blend")
        bpy.ops.wm.save_as_mainfile(filepath=str(fname))
        scn.MH2B_projdir = f
        return {'FINISHED'}


