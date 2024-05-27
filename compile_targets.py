#!/usr/bin/python3
import os
import json
import argparse
from core.importfiles import UserEnvironment, TargetASCII

if __name__ == '__main__':
    # get urls + name of standard mesh
    #
    release_info = os.path.join("data", "makehuman2_version.json")
    if os.path.isfile(release_info):
        with open(release_info, 'r') as f:
            release = json.load(f)

    mesh  = release["standardmesh"]

    uenv = UserEnvironment()
    uenv.GetPlatform()
    conffile = uenv.GetUserConfigFilenames()[0]
    userspace = None
    if os.path.isfile(conffile):
        with open(conffile, 'r') as f:
            conf = json.load(f)
            userspace = os.path.join(conf["path_home"], "data", "target", mesh)
    systemspace = os.path.join(os.path.dirname(os.path.abspath(__file__)),"data", "target", mesh)

    parser = argparse.ArgumentParser(description="Compile targets to binary form (usually works interactive)")
    parser.add_argument("-s", action="store_true", help="compile system space targets")
    if userspace is not None:
        parser.add_argument("-u", action="store_true", help="compile user space instead of system space")

    parser.add_argument("-n", action="store_true", help="compile non interactive")

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

    dest = os.path.join(space, "compressedtargets.npz")
    print ("Compile targets in: " + space)
    print ("Destination file is: " + dest)
    if args.n is False:
        okay = False
        while not okay:
            line = input('Enter a to abort, c to compress: ')
            if line == "a":
                exit (0)
            if line == "c":
                okay = True

    at = TargetASCII()
    at.compressAllTargets(space, dest, 1)

