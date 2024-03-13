#!/usr/bin/python3
import os
import json
from core.importfiles import AssetPack, UserEnvironment

if __name__ == '__main__':
    #
    # nearly all pathes just temporary, until solution found
    #
    server = "files.makehumancommunity.org"
    path   = "asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip"
    mesh = "hm08"

    uenv = UserEnvironment()
    uenv.GetPlatform()
    conffile = uenv.GetUserConfigFilenames()[0]
    userspace = None
    if os.path.isfile(conffile):
        with open(conffile, 'r') as f:
            conf = json.load(f)
            userspace = os.path.join(conf["path_home"], "data")
    systemspace = os.path.join(os.path.dirname(os.path.abspath(__file__)),"data")

    if userspace:
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
    else:
        space = systemspace
    
    print ("Selection: " + space)
    okay = False
    while not okay:
        line = input('Enter a to abort, d to download: ')
        if line == "a":
            exit (0)
        if line == "d":
            okay = True

    assets = AssetPack()
    tempdir =assets.tempDir()
    (success, message) = assets.getAssetPack("http://" + server + "/" + path, tempdir)
    if not success:
        print (message)
        exit (20)
    filename = os.path.split(path)[1]
    assets.copyAssets(tempdir, space, mesh, filename)
    assets.cleanupUnzip()
