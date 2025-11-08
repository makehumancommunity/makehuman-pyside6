"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * apiSocket
"""
import socket
import json
from PySide6.QtCore import QThread, Signal
from core.blender_communication import blendCom

class apiSocket(QThread):
    """
    class for communication socket
    """
    viewRedisplay = Signal(int)         # signal when redisplay should be done

    def __init__(self, glob, *args):
        super().__init__()
        self.exiting = False
        self.env = glob.env
        self.glob = glob
        self.error = "No error"
        self.errcode = 0
        self.jsonparam = None
        self.binarybuffers = None
        self.blcom = None
        self.socket = None
        self.host = self.env.config["apihost"] if "apihost" in self.env.config else '127.0.0.1'
        self.port = self.env.config["apiport"] if "apiport" in self.env.config else 12345

    def replyError(self, conn):
        self.env.logLine(1, "API reply:" + self.error)
        js = { "errcode": self.errcode, "errtext": self.error }
        txt = json.dumps(js)
        conn.send (bytes(txt, 'utf-8'))
        conn.close()

    def replyAnswer(self, conn):
        if self.jsonparam is not None:
            self.jsonparam["errcode"]= 0 
            txt = json.dumps(self.jsonparam)
            # print ("send answer: " + txt)
            conn.send (bytes(txt, 'utf-8'))
        else:
            for sbuffer in self.binarybuffers:
                print ("send binary data")
                l = len(sbuffer)
                total = 0
                while total < l:
                    s = conn.send (sbuffer)
                    if s == 0:
                        return False
                    total += s
        conn.close()
        return True

    def decodeRequest(self, data):
        self.jsonparam = None
        self.binarybuffers = None
        baseclass = self.glob.baseClass

        try:
            js = json.loads(data)
        except json.JSONDecodeError as e:
            self.error = "JSON format error in string  > " + str(e)
            self.errcode = 1
            return False
        if not js:
            self.error =  "Empty JSON string"
            self.errcode = 2
            return False

        if "function" in js:
            f = js["function"]
            if f == "hello":
                self.jsonparam = {"application": self.env.release_info["name"], "name": baseclass.name }
                return True
            elif f == "getchar":
                # hiddenverts=False, onground=True, animation=False, scale =0.1
                scale = 0.1
                onground = True
                hidden = False
                anim = False
                if "params" in js:
                    p = js["params"]
                    scale    = p["scale"] if "scale" in p else scale
                    onground = p["onground"] if "onground" in p else onground
                    hidden = p["hidden"] if "hidden" in p else hidden
                    anim = p["anim"] if "anim" in p else anim

                self.blcom = blendCom(self.glob, None, None, hidden, onground, anim, scale)
                if baseclass.in_posemode:
                    print ("I am in pose mode")
                    baseclass.baseMesh.resetFromCopy()
                    baseclass.updateAttachedAssets()
                self.jsonparam = self.blcom.apiGetChar()
                return True
            elif f == "bin_getchar":
                if self.blcom is None:
                    self.error =  "Bad json/binary order"
                    self.errcode = 4
                    return False
                self.binarybuffers = self.blcom.apiGetBuffers()
                self.blcom = None
                return True
            elif f == "randomize":
                mode = 0
                if "params" in js:
                    p = js["params"]
                    mode = p["mode"] if "mode" in p else mode
                tr = self.glob.guiPresets["Randomizer"].tr
                tr.storeAllValues()
                if tr.do(mode):
                    tr.apply(True)
                self.jsonparam = {}
                self.viewRedisplay.emit(1)
                return True

        self.error =  "Unknown command"
        self.errcode = 3
        return False

    def run(self):
        self.env.logLine(1, "Opening server socket... ")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
        except socket.error as msg:
            self.env.logLine(1, 'Bind failed. Error Code : %s' %  msg)
            return

        self.env.logLine(1, "Using host: " + self.host + ", Port: " + str(self.port))
        self.socket.listen(10)

        while not self.exiting:
            self.env.logLine(8, "Waiting for connection.")

            try:
                conn, addr = self.socket.accept()

                if conn and not self.exiting:
                    self.env.logLine(2, "Connected with " + str(addr[0]) + ":" + str(addr[1]))
                    data = str(conn.recv(8192), encoding='utf-8')
                    self.env.logLine(2, "Got: '" + data + "'")
                    if self.decodeRequest(data):
                        self.replyAnswer(conn)
                    else:
                        self.replyError(conn)

            except socket.error as msg:
                # usually it sends an error when terminated, all other will be displayed
                #
                if not self.exiting:
                    self.env.logLine(1, 'Socket Error Code : %s' %  msg)
                pass

    def stopListening(self):
        if not self.exiting:
            self.env.logLine(1, "Stopping socket connection")
            self.exiting = True
            if self.socket is None:
                return
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except socket.error:
                print("Socket error 2")
                """If the socket was not connected, shutdown will complain. This isn't a problem, 
                so just ignore."""
                pass
            self.socket.close()
