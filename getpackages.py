#!/usr/bin/python3
import os
from core.importfiles import AssetPack

if __name__ == '__main__':
    #
    # nearly all pathes just temporary, until solution found
    #
    server = "files.makehumancommunity.org"
    path   = "asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip"

    assets = AssetPack()
    tempdir =assets.tempDir()
    user = "/data/punkduck/Dokumente/makehuman2/data"
    sys = "/data/punkduck/build/new_makehuman/mh2/data"
    mesh = "hm08"
    (success, message) = assets.getAssetPack("http://" + server + "/" + path, tempdir)
    if not success:
        print (message)
        exit (20)
    filename = os.path.split(path)[1]
    assets.copyAssets(tempdir, user, mesh, filename)
    assets.cleanupUnzip()
