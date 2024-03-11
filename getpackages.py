#!/usr/bin/python3

from io import BytesIO
from urllib.request import Request, urlopen
from urllib.error import URLError
from zipfile import ZipFile
from core.importfiles import AssetPack
import os
import shutil

if __name__ == '__main__':
    #
    # nearly all pathes just temporary, until solution found
    #
    assets = AssetPack("http", "files.makehumancommunity.org")
    tempdir =assets.tempDir()
    user = "/data/punkduck/Dokumente/makehuman2/data"
    sys = "/data/punkduck/build/new_makehuman/mh2/data"
    mesh = "hm08"
    (success, message) = assets.getAssetPack("asset_packs/makehuman_system_assets", "makehuman_system_assets_cc0.zip", tempdir)
    if not success:
        print (message)
        exit (20)
    assets.copyAssets(tempdir, user, mesh)
    assets.cleanupUnzip()
