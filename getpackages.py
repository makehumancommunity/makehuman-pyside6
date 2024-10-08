#!/usr/bin/python3
import os
import json
import argparse
from core.importfiles import AssetPack, UserEnvironment

if __name__ == '__main__':

    # get urls + name of standard mesh
    #
    release_info = os.path.join("data", "makehuman2_version.json")
    if os.path.isfile(release_info):
        with open(release_info, 'r') as f:
            release = json.load(f)

    (server, path, mesh)  = (release["url_fileserver"], release["url_systemassets"], release["standardmesh"])

    # get user data path (if available)
    #
    uenv = UserEnvironment()
    uenv.GetPlatform()
    conffile = uenv.GetUserConfigFilenames()[0]
    userspace = None
    if os.path.isfile(conffile):
        with open(conffile, 'r') as f:
            conf = json.load(f)
            userspace = os.path.join(conf["path_home"], "data")
    systemspace = os.path.join(os.path.dirname(os.path.abspath(__file__)),"data")

    parser = argparse.ArgumentParser(description="Load packages from asset server " + server)
    parser.add_argument("-s", action="store_true", help="store in system space")
    if userspace is not None:
        parser.add_argument("-u", action="store_true", help="store in user space instead of system space")

    args = parser.parse_args()

    space = None
    if args.u:
        if userspace is None:
            print ("No user space found")
            exit (2)
        space = userspace
    if args.s:
        space = systemspace

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

    source = "http://" + server + "/" + path
    print ("Download from: " + source)
    print ("for mesh     : " + mesh)
    print ("to folder    : " + space)
    okay = False
    while not okay:
        line = input('Enter a to abort, d to download: ')
        if line == "a":
            exit (0)
        if line == "d":
            okay = True

    assets = AssetPack()
    tempdir =assets.tempDir()
    filename = os.path.split(path)[1]
    (success, message) = assets.getAssetPack(source, tempdir, filename, unzip=True)
    if not success:
        print (message)
        exit (20)
    assets.copyAssets(tempdir, space, mesh)
    assets.cleanupUnzip()
