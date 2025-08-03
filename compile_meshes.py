#!/usr/bin/python3
import os
import json
import argparse
from core.importfiles import UserEnvironment
from core.attached_asset import attachedAsset
from obj3d.object3d import object3d

#
# we need a dummy class for global containing the environment 
# and a logLine function provided in inside environment
#

class globalObjects():
    def __init__(self, env):
        self.env = env

def logLine(level, line):
    if level & 8:
        print (line)

def compressFile(glob, eqtype, path, source):
    filename = os.path.join(path, source)
    asset =  attachedAsset(glob, eqtype, glob.env.numverts)
    asset.mhcloToMHBin(filename)

if __name__ == '__main__':
    # get predefined environment parameters (standardmesh)
    #
    release_info = os.path.join("data", "makehuman2_version.json")
    if os.path.isfile(release_info):
        with open(release_info, 'r') as f:
            release = json.load(f)


    uenv = UserEnvironment()
    uenv.GetPlatform()
    #
    # now add a few additional environment variables
    #
    uenv.logLine = logLine                          # the function we supply directly
    uenv.verbose = 0                                # do not print comments from makehuman2
    uenv.basename = release["standardmesh"]         # the meshname
    uenv.numverts = release["standardnumverts"]     # use to determine delete bool array

    conffile = uenv.GetUserConfigFilenames()[0]
    userspace = None
    if os.path.isfile(conffile):
        with open(conffile, 'r') as f:
            conf = json.load(f)
            userspace = os.path.join(conf["path_home"], "data")
    systemspace = os.path.join(os.path.dirname(os.path.abspath(__file__)),"data")

    parser = argparse.ArgumentParser(description="Compile objects (mhclo + obj) to binary form (mhbin) (usually works interactive). Currently it only works with standard mesh.")
    parser.add_argument("-s", action="store_true", help="compile system space objects")
    if userspace is not None:
        parser.add_argument("-u", action="store_true", help="compile user space instead of system space")

    parser.add_argument("-n", action="store_true", help="compile non interactive")
    parser.add_argument("filename", nargs="?", type=str, help="compile only assets which are similar to this filename")

    args = parser.parse_args()

    space = None
    if args.u:
        if userspace is None:
            print ("No user space found")
            exit (2)
        space = userspace
    if args.s:
        space = systemspace

    # no decision, ask user
    #
    if space is None:
        print("[1] User   space: " + userspace)
        print("[2] System space: " + systemspace)

        okay = False
        while not okay:
            line = input('Enter 1, 2 or a to abort: ')
            if line == "a":
                exit (0)
            if line == "1":
                space = userspace
                okay = True
            if line == "2":
                space = systemspace
                okay = True

    print ("Compile objects in: " + space + "\n")
    if args.n is False:
        okay = False
        while not okay:
            line = input('Enter a to abort, c to compress: ')
            if line == "a":
                exit (0)
            if line == "c":
                okay = True

    glob = globalObjects(uenv)

    # first compile base if added to user space or system space
    #
    num = 0
    base =  os.path.join(space, "base", uenv.basename, "base.obj")
    if os.path.isfile (base):
        if args.filename is None or "base" in args.filename:
            print ("Found: " + base)
            basemesh = object3d(glob, None, "base")
            (res, err) = basemesh.load(base, True)
            if res == 0:
                print (err)
                exit(10)
            basemesh.exportBinary()
            num += 1

    for folder in ["clothes", "eyebrows", "eyelashes", "eyes", "hair", "proxy", "teeth", "tongue"]:
        absfolder = os.path.join(space, folder, uenv.basename)
        if os.path.isdir(absfolder):
            for root, dirs, files in os.walk(absfolder, topdown=True):
                for name in files:
                    if name.endswith(".mhclo") or name.endswith(".proxy"):
                        if args.filename:
                            if args.filename in name:
                                compressFile (glob, folder, root, name)
                                num += 1
                        else:
                            compressFile (glob, folder, root, name)
                            num += 1

    print (str(num) + " mesh(es) compiled.")
    exit(0)
