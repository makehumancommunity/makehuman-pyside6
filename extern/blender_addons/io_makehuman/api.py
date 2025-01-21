import socket
import json
import bpy

class API:
    def __init__(self, host, port):
        self.host = host
        self.port = port

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
            js = json.loads(data)
        except json.JSONDecodeError as e:
            error = "JSON format error in string  > " + str(e)
            parent.report({'ERROR'}, error)
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", error=error)
            return False, None

        if not js:
            error = "Empty JSON string"
            parent.report({'ERROR'}, error)
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", error=error)
            return False, None

        if not "errcode" in js:
            error = "Missing error code in answer"
            parent.report({'ERROR'}, error)
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", error=error)
            return False, None

        if js["errcode"] != 0:
            error = js["errtext"] if "errtext" in js else "Errorcode " + str(js["errcode"])
            parent.report({'ERROR'}, error)
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", error=error)
            return False, None

        if function == "hello":
            info = "Application: " + js["application"] + "\n" + "Current model: " + js["name"]
            return True, info

        elif function == "getchar":
            info = "Get character"
            print (js)
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
        info = "Get character " + scn.MH2B_apihost + " Port " + str(scn.MH2B_apiport)
        res = True

        api = API(scn.MH2B_apihost, scn.MH2B_apiport)
        if not api.connect(self, info):
            return {'FINISHED'}

        api.send("getchar")
        data = api.receive()
        res, text = api.decodeAnswer(self, "getchar", data)
        if res is False:
            return {'FINISHED'}

        api = API(scn.MH2B_apihost, scn.MH2B_apiport)
        if not api.connect(self, info):
            return {'FINISHED'}

        api.send("bin_getchar")
        data = api.receive_bin()
        print ("received: ", len(data))

        if res is True:
            self.report({'INFO'}, text)
        return {'FINISHED'}

