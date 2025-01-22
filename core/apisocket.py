import socket
import json
from PySide6.QtCore import QThread, Signal
from core.blender_communication import blendCom

class apiSocket(QThread):
    #update_progress = Signal(int)

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
            print ("send: " + txt)
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
                self.jsonparam = {"application": self.env.release_info["name"], "name": self.glob.baseClass.name }
                return True
            elif f == "getchar":
                # hiddenverts=False, onground=True, animation=False, scale =0.1
                self.blcom = blendCom(self.glob, None, False, True, False, 0.1)
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
            self.env.logLine(1, 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
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
                    self.env.logLine(1, 'Socket Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
                pass

    def stopListening(self):
        if not self.exiting:
            self.env.logLine(1, "Stopping socket connection")
            self.exiting = True
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except socket.error:
                print("Socket error 2")
                """If the socket was not connected, shutdown will complain. This isn't a problem, 
                so just ignore."""
                pass
            self.socket.close()
