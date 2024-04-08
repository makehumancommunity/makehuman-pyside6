#!/usr/bin/python3

import os

def delFolder(folder):
    for root, dirs, files in os.walk(folder, topdown=False):
        for f in files:
            fabs = os.path.join(root, f)
            print ("rm " + fabs)
        for f in dirs:
            fabs = os.path.join(root, f)
            print ("rmdir " + fabs)

if __name__ == '__main__':
    standardmesh = "hm08"
    startpath = os.path.dirname(os.path.abspath(__file__))
    data = os.path.join(startpath, "data")
    for elem in ["clothes", "eyes", "tongue", "skins", "eyelashes", "eyebrows", "teeth", "proxy"]:
        check = os.path.join(data, elem, standardmesh)
        files = os.listdir(check)
        for subelem in files:
            ftest = os.path.join(check, subelem)
            if subelem != "icons" and os.path.isdir(ftest):
                delFolder(ftest)
                print ("rmdir " + ftest)

