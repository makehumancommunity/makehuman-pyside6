import socket
import json
import bpy

class API:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def connect(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((self.host, self.port))
        except ConnectionRefusedError:
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
        return data

    def send(self, function, params=None):
        js = { "function": function }
        if params:
            js["params"] = params
        txt = json.dumps(js)
        self.client.send (bytes(txt, 'utf-8'))

    def decodeRequest(self, function, data):
        try:
            js = json.loads(data)
        except json.JSONDecodeError as e:
            return False, "JSON format error in string  > " + str(e)
        if not js:
            return False, "Empty JSON string"

        if function == "hello":
            info = "Application: " + js["application"] + "\n" + "Current model: " + js["name"]
            return True, info

        return False, "Unknown command"


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
        if not api.connect():
            error = "Connection refused"
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", info=info, error=error)
            self.report({'ERROR'}, error)
            return {'FINISHED'}

        api.send("hello")
        data = api.receive()
        # print (data)
        res, text = api.decodeRequest("hello", data)

        if res is False:
            self.report({'ERROR'},  text)
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", error=text)
        else:
            self.report({'INFO'}, text)
            bpy.ops.mh2b.infobox('INVOKE_DEFAULT', title="Connection", info=text)
        return {'FINISHED'}

