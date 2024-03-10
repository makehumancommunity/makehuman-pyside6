#!/usr/bin/python3

from io import BytesIO
from urllib.request import Request, urlopen
from urllib.error import URLError
from zipfile import ZipFile
import os
import shutil

class AssetPack():
    def __init__(self, protocol, server):
        self.protocol = protocol
        self.server = server

    def getAssetPack(self, path, filename, save_path):
        """
        get URL and extract zipfile
        """
        url = self.protocol  + "://" + self.server + "/" + path + "/" + filename

        req = Request(url)
        try:
            response = urlopen(req)
        except URLError as e:
            if hasattr(e, 'reason'):
                err = 'URL: ' + url + ' ' +str(e.reason)
                return (False, err)
            elif hasattr(e, 'code'):
                err = 'URL: ' + url + ' Error code: ' + str( e.code)
                return (False, err)
        else:
            with ZipFile(BytesIO(response.read())) as zfile:
                zfile.extractall(save_path)
        return (True, None)

    def copyAssets(self, source, dest, mesh):
        l = len(source)
        for root, dirs, files in os.walk(source, topdown=True):
            for name in files:
                if root.startswith(source):
                    root = root[l+1:]

                dirs = root.split(os.sep)
                category = dirs[0]
                if category in ["clothes", "eyes", "eyelashes", "eyebrows", "hair", "skins", "teeth", "tongue"]:
                    folder = os.path.join(dest, "data", category, mesh)
                    restdirs = os.sep.join(dirs[1:])
                    destfolder = os.path.join(folder, restdirs)
                    sourcefolder = os.path.join(source, root)
                    print(destfolder)
                    print (sourcefolder)
                    os.makedirs(destfolder, exist_ok = True)
                    sourcename = os.path.join(sourcefolder, name)
                    destname = os.path.join(destfolder, name)
                    print (sourcename)
                    print (destname)
                    shutil.copyfile(sourcename, destname)

if __name__ == '__main__':
    #
    # nearly all pathes just temporary, until solution found
    #
    tempdir = "/tmp/mystuff4"
    assets = AssetPack("http", "files.makehumancommunity.org")
    user = "/data/punkduck/Dokumente/makehuman2/"
    sys = "/data/punkduck/build/new_makehuman/mh2"
    mesh = "hm08"
    #(success, message) = assets.getAssetPack("asset_packs/makehuman_system_assets", "makehuman_system_assets_cc0.zip", tempdir)
    #if not success:
    #    print (message)
    #    exit (20)
    assets.copyAssets(tempdir, user, mesh)
