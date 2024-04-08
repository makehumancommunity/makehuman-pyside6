from io import BytesIO
from urllib.request import Request, urlopen
from urllib.error import URLError
from zipfile import ZipFile
import os
import sys
import shutil
import platform
import tempfile

class UserEnvironment():
    def __init__(self):
        self.osindex= -1

    def GetPlatform(self):
        p =sys.platform
        if p.startswith('win'):
            ostype = "Windows"
            osindex= 0
            platform_version = " ".join(platform.win32_ver())
        elif p.startswith('darwin'):
            ostype = "MacOS"
            osindex= 2
            platform_version = platform.mac_ver()[0]
        else:
            ostype = "Linux"
            osindex= 1
            try:
                platform_version = ' '.join(platform.linux_distribution())
            except AttributeError:
                try:
                    import distro
                    platform_version = ' '.join(distro.linux_distribution())
                except ImportError:
                    platform_version = "Unknown"
        self.osindex = osindex
        return (p, osindex, ostype, platform_version)

    def GetHardware(self):
        return(platform.machine(), platform.processor(), platform.uname()[2])

    def GetUserConfigFilenames(self, osindex=None, create=False):
        if osindex is None:
            osindex = self.osindex
        if osindex == 0:
            path = os.getenv('LOCALAPPDATA', '')
        elif osindex == 1:
            path = os.path.expanduser('~/.config')
        else:
            path = os.path.expanduser('~/Library/Application Support/MakeHuman')

        #
        # create of subfolder
        folder = os.path.join(path, 'makehuman2')
        if create is True:
            if not os.path.isdir(folder):
                try:
                    os.mkdir(folder)
                except:
                    return (None, folder)

        return (os.path.join(folder, 'makehuman2.conf'), os.path.join(folder, 'makehuman2_session.conf'))
        

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
                if category in ["clothes", "eyes", "eyelashes", "eyebrows", "hair", "skins", "teeth", "tongue", "proxymeshes"]:
                    # proxy is renamed
                    #
                    if category == "proxymeshes":
                        category = "proxy"
                    folder = os.path.join(dest, category, mesh)
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

