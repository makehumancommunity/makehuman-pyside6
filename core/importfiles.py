from io import BytesIO
from urllib.request import Request, urlopen
from urllib.error import URLError
from zipfile import ZipFile
import os
import shutil
import tempfile

class AssetPack():
    def __init__(self):
        self.unzipdir = None

    def getAssetPack(self, url, save_path, filename, unzip=False):
        """
        get URL and extract zipfile
        """
        try:
            req = Request(url)
        except Exception as err:
            return (False, str(err))

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
            if not unzip:
                outpath = os.path.join(save_path, filename)
                with open(outpath, mode="wb") as file:
                    file.write(response.read())
            else:
                with ZipFile(BytesIO(response.read())) as zfile:
                    zfile.extractall(self.unzipdir)

        return (True, None)

    def tempDir(self):
        self.unzipdir = tempfile.mkdtemp(prefix="mh_")
        return (self.unzipdir)

    def unZip(self, zipfile):
        self.tempDir()
        with ZipFile(zipfile,"r") as zip_ref:
            zip_ref.extractall(self.unzipdir)
        return(self.unzipdir)

    def cleanupUnzip(self):
        if self.unzipdir is not None:
            if os.path.split(self.unzipdir)[1].startswith("mh_"):
                print ("Cleanup " + self.unzipdir)
                shutil.rmtree(self.unzipdir)


    def copyAssets(self, source, dest, mesh):
        l = len(source)
        for root, dirs, files in os.walk(source, topdown=True):
            for name in files:
                if root.startswith(source):
                    root = root[l+1:]

                dirs = root.split(os.sep)
                category = dirs[0]
                if category in ["clothes", "eyes", "eyelashes", "eyebrows", "hair", "skins", "teeth", "tongue"]:
                    folder = os.path.join(dest, category, mesh)
                    restdirs = os.sep.join(dirs[1:])
                    destfolder = os.path.join(folder, restdirs)
                    sourcefolder = os.path.join(source, root)
                    print(destfolder)
                    print (sourcefolder)
                    #os.makedirs(destfolder, exist_ok = True)
                    sourcename = os.path.join(sourcefolder, name)
                    destname = os.path.join(destfolder, name)
                    print (sourcename)
                    print (destname)
                    #shutil.copyfile(sourcename, destname)

