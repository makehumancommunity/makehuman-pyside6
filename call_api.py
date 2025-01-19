#!/usr/bin/python3
import socket
import os
import json
import argparse
from core.importfiles import UserEnvironment

class API:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def connect(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((self.host, self.port))
        except ConnectionRefusedError:
            print ("Connection refused")
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
        print ("recv: ", data)

    def send(self, function, params=None):
        js = { "function": function }
        if params:
            js["params"] = params
        txt = json.dumps(js)
        print ("send: " + txt)
        self.client.send (bytes(txt, 'utf-8'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Test program for API using socket port communication")
    parser.add_argument("-s", type=int, help="Socket port number", default=12345)
    parser.add_argument("-n", type=str, help="Hostname", default="127.0.0.1")
    args = parser.parse_args()

    port = args.s
    host = args.n
    uenv = UserEnvironment()
    uenv.GetPlatform()
    conffile = uenv.GetUserConfigFilenames()[0]
    if os.path.isfile(conffile):
        with open(conffile, 'r') as f:
            conf = json.load(f)
            host = conf["apihost"] if "apihost" in conf and args.n is None else host
            port = conf["apiport"] if "apiport" in conf and args.s is None else port

    api = API(host, port)
    if not api.connect():
        exit(20)
    #
    # this is the ping command of the application
    #
    api.send("hello")
    api.receive()

