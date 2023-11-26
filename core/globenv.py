
import sys
import os
import re
import locale
import platform
import json
import glob
from gui.application import QTVersion
from opengl.main import GLVersion

class globalObjects():
    def __init__(self, env):
        self.env = env
        self.graphwindow = None
        self.Targets = None
        self.targetCategories = None        # will contain the category object
        self.baseClass = None
        self.textures = []

    def freeTextures(self):
        self.textures = []

    def addTexture(self, path):
        self.textures.append(path)

class programInfo():
    """
    this class should contain 'global parameters'
    especially:
    * all pathnames
    * converter functions
    * JSON reader/writer + integrity test
    """
    def __init__(self, frozen: bool, path_sys: str, verbose: int, uselog: bool):
        """
        init: set all global parameters
        evaluates system path, platform in ostype and osindex.
        """
        self.release_info = {
            "name": "MakeHuman [test project]",
            "author": "black punkduck, elvaerwyn",
            "version": (2, 0, 1),
            "copyright": "Copyright ... and listed authors",
            "maintainer": "black punkduck",
            "status": "only development"
        }

        self.basename = None
        self.last_error = None

        self.verbose = verbose
        self.uselog  = uselog
        self.frozen  = frozen
        self.path_sys = path_sys
        
        p =sys.platform
        if p.startswith('win'):
            self.ostype = "Windows"
            self.osindex= 0
            self.platform_version = " ".join(platform.win32_ver())
        elif p.startswith('darwin'):
            self.ostype = "MacOS"
            self.osindex= 2
            self.platform_version = platform.mac_ver()[0]
        else:
            self.ostype = "Linux"
            self.osindex= 1
            try:
                self.platform_version = ' '.join(platform.linux_distribution())
            except AttributeError:
                try:
                    import distro
                    self.platform_version = ' '.join(distro.linux_distribution())
                    print (join(distro.linux_distribution()))
                except ImportError:
                    self.platform_version = "Unknown"

        self.sys_platform = p
        #
        # a lot of information for later use
        #
        self.default_encoding    = sys.getdefaultencoding()
        self.filesystem_encoding = sys.getfilesystemencoding()
        self.stdout_encoding     = sys.stdout.encoding
        self.preferred_encoding  = locale.getpreferredencoding()
        self.sys_path = os.path.pathsep.join( [self.pathToUnicode(p) for p in sys.path] )
        self.bin_path = self.pathToUnicode(os.environ['PATH'])
        self.sys_version = re.sub(r"[\r\n]"," ", sys.version)

        self.sys_executable = sys.executable
        self.platform_machine = platform.machine()
        self.platform_processor = platform.processor()
        self.platform_release = platform.uname()[2]

        from numpy import __version__ as numpvers
        self.numpy_version = [int(x) for x in numpvers.split('.')]
        if self.numpy_version[0] <= 1 and self.numpy_version[1] < 6:
            print ("MakeHuman requires at least numpy version 1.6")
            exit (20)

        self.QT_Info = QTVersion(self)
        self.GL_Info = GLVersion(False) # not yet initialized

    def __str__(self):
        """
        print debug information, should contain all information
        """
        return  json.dumps(self.__dict__, indent=4, sort_keys=True)

    def pathToUnicode(self, path: str) -> str:
        """
        Unicode representation of the filename.
        Bytes is decoded with the codeset used by the filesystem of the operating system.
        Unicode representations of paths are fit for use in GUI.
        """

        if isinstance(path, bytes):
            # Approach for bytes string type
            try:
                return str(path, 'utf-8')
            except UnicodeDecodeError:
                pass
            try:
                return str(path, self.filesystem_encoding)
            except UnicodeDecodeError:
                pass
            try:
                return str(path, self.default_encoding)
            except UnicodeDecodeError:
                pass
            try:
                return str(path, self.preferred_encoding)
            except UnicodeDecodeError:
                return path
        else:
            return path

    def formatPath(self, path: str) -> str:
        if path is None:
            return None
        return self.pathToUnicode(os.path.normpath(path).replace("\\", "/"))

    def readJSON(self, path: str) -> dict:
        """
        JSON reader, will return JSON object or None
        in case of error, self.last_error will be set
        """
        self.logLine(8, "Load '" + path + "'")

        try:
            f = open(path, 'r', encoding='utf-8')
        except:
            self.last_error =   "Cannot read JSON " + path
            return None
        with f:
            try:
                json_object = json.load(f)
            except json.JSONDecodeError as e:
                self.last_error = "JSON format error in " + path + " > " + str(e)
                return None
            if not json_object:
                self.last_error =  "Empty JSON file " + path
                return None
        return (json_object)
            
    def writeJSON(self, path: str, json_object: dict) -> bool:
        """
        JSON writer, will return False in case of error
        in case of error, self.last_error will be set
        """
        self.logLine(8, "Write '" + path + "'")

        try:
            f = open(path, 'w', encoding='utf-8')
        except:
           self.last_error =   "Cannot write JSON " + path
           return False
        with f:
            try:
                json.dump(json_object, f, indent=4)
            except:
                self.last_error = "Cannot write JSON " + path
                return False
        return True


    def environment(self) -> bool:
        """
        Read the configuration

        * environment in MH_HOME_LOCATION
        * a name of a folder in a configuration file
        * using the DOCUMENTS folder or home folder according to registry (Windows) or XDG-file (Linux)

        returns True (all okay) or False (system cannot start)
        """

        # default entries (will be used when not in user or system config)
        #
        defaultconf = {
            "basename": None,
            "graphicalgui_attached": False,
            "noSampleBuffers": False,
            "noShaders": False,
            "redirect_messages": True,
            "remember_session": False,
            "theme": "makehuman.qss",
            "units": "metric"
        }

        # get all system and user paths according to operating system
        #
        if self.osindex == 0:
            path = os.getenv('LOCALAPPDATA', '')
        elif self.osindex == 1:
            path = os.path.expanduser('~/.config')
        else:
            path = os.path.expanduser('~/Library/Application Support/MakeHuman')
        
        # system paths
        #
        self.path_sysdata = os.path.join(self.path_sys,  "data")
        self.path_sysicon = os.path.join(self.path_sysdata, "icons")
        self.path_sysconf = os.path.join(self.path_sysdata, "makehuman2_default.conf")

        # configuration files
        #
        # create of subfolder
        #
        folder = os.path.join(path, 'makehuman2')
        if not os.path.isdir(folder):
            try:
                os.mkdir(folder)
            except:
                self.last_error = "cannot create folder " + folder
                return (False)

        self.path_userconf = os.path.join(folder, 'makehuman2.conf')
        self.path_usersess = os.path.join(folder, 'makehuman2_session.conf') 

        # read json files with additional information, home-path can be changed
        #
        self.config = {}
        self.path_home = None
        self.writeconf = False          # in case of first time or in case of missing parameter, config file needs to rewritten

        if os.path.isfile(self.path_userconf):
            c = self.readJSON(self.path_userconf)
            if c is None:
                return False

            self.config = c
            self.path_home = c["path_home"] if "path_home" in c else None
        else:
            c = self.readJSON(self.path_sysconf)
            if c is None:
                return False
            self.writeconf = True
            self.config = c

        # integrity test (avoid missing keys)
        #
        if self.dictFillGaps(defaultconf, self.config):
            self.writeconf = True

        # calculate path_home
        # method: overwrite path_home by environment
        #
        path = os.environ.get("MH_HOME_LOCATION", '')
        if os.path.isdir(path):
            path = self.formatPath(path)

            if path is not None:
                self.path_home = path

        # in case of first time get home path from system if not already set
        #
        if self.path_home is None:

            # Windows (ask in registry)
            #
            if self.osindex == 0:
                import winreg
                keyname = r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
                #name = 'Personal'
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, keyname) as k:
                    try:
                        value, type_ = winreg.QueryValueEx(k, 'Personal')
                    except FileNotFoundError:
                        value, type_ = "%USERPROFILE%\Documents", winreg.REG_EXPAND_SZ
                    if type_ == winreg.REG_EXPAND_SZ:
                        self.path_home = self.formatPath(winreg.ExpandEnvironmentStrings(value))
                    elif type_ == winreg.REG_SZ:
                        self.path_home = self.formatPath(value)

            # Linux
            #
            elif self.osindex == 1:
                path = os.path.expanduser('~/.config/user-dirs.dirs')
                if os.path.isfile(path):
                    with open(path, 'r', encoding='utf-8') as file:
                        for line in file:
                            if line and line.startswith('XDG_DOCUMENTS_DIR'):
                                line = line.strip()
                                key, value = line.split('=')
                                key = key.split('_')[1]
                                value = os.path.expandvars(value.strip('"'))
                                if os.path.isdir(value):
                                    self.path_home = value

                if self.path_home is None:
                    self.path_home = self.pathToUnicode(os.path.expanduser('~'))

            # MacOS
            #
            else:
                self.path_home = os.path.expanduser('~')
            self.path_home = os.path.join(self.path_home, "makehuman2")
            self.config["path_home"] = self.path_home
            self.writeconf = True

        if self.path_home is None:
            self.last_error = "Cannot not determine user folder!"
            return False

        # set data paths
        #
        self.path_userdata = os.path.join(self.path_home, "data")

        # add own system path for windows
        #
        if self.frozen:
            # Make sure we load packaged DLLs instead of those present on the system
            os.environ["PATH"] = '.' + os.path.pathsep + self.path_sys + os.path.pathsep + os.environ["PATH"]

        # error files for redirection
        #
        if "path_error" not in self.config:
            self.config["path_error"] = self.path_error = os.path.join(self.path_home, "log")
        else:
            self.path_error = self.config["path_error"]

        # generate all (still missing) folders
        #
        if self.generateFolders() is False:
            return(False)

        self.reDirect(self.uselog)     # redirect error messages

        # in case of first start or missing parameter write configuration
        #
        if self.writeconf:
            if self.writeJSON(self.path_userconf, self.config) == False:
                return False

        # set further parameters from configuration
        #
        self.g_attach = self.config["graphicalgui_attached"]
        self.basename = self.config["basename"]

        # read last session on demand
        #
        self.loadSession()
        return True

    def generateFolders(self):
        """
        create folders, return false if problem, write results to logfile
        in case of error set last_error
        """
        for folder in [self.path_home, self.path_error]:
            if not os.path.isdir(folder):
                if os.path.isfile(folder):
                    self.last_error = "File exists instead of folder " + folder
                    return (False)
                else:
                    try:
                        os.mkdir(folder)
                    except:
                        self.last_error = "cannot create folder " + folder
                        return (False)
                    self.logLine(2, folder + " created")
        return (True)

    def reDirect(self, log=False):
        """
        redirection of stderr and stdout to files path_stdout and path_stderr
        """
        if self.config["redirect_messages"] or log is True:
            self.path_stdout = os.path.join(self.path_error, "makehuman-out.txt")
            sys.stdout = open(self.path_stdout, "w", encoding=self.preferred_encoding, errors="replace")
            self.path_stderr = os.path.join(self.path_error, "makehuman-err.txt")
            sys.stderr = open(self.path_stderr, "w", encoding=self.preferred_encoding, errors="replace")
        else:
            self.path_stdout= None
            self.path_stderr= None

    def getFileList(self, dirname, pattern):
        """
        get a file list with an extension
        """
        pattern = os.path.join(glob.escape(dirname), pattern)
        return(glob.glob(pattern))

    def getDataFileList(self, ext, *subdirs):
        """
        get filelist from system datapath or userdata + subdirectories
        """
        filebase = {}
        for path in [self.path_sysdata, self.path_userdata]:
            test = os.path.join(path, *[sdir for sdir in subdirs])
            if os.path.isdir(test):
                files = self.getFileList(test, "*." + ext)
                for filename in files:
                    directory, fname = os.path.split(filename)
                    filebase[fname] = filename
        return(filebase)

    def getDataDirList(self, search, *subdirs):
        """
        get filelist from system datapath or userdata + subdirectories
        """
        filebase = {}
        for path in [self.path_sysdata, self.path_userdata]:
            test = os.path.join(path, *[sdir for sdir in subdirs])
            files = self.getFileList(test, "*")
            for dirname in files:
                if os.path.isdir(dirname):
                    if search is not None:
                         filename = os.path.join(dirname, search)
                         if os.path.isfile(filename):
                            directory, fname = os.path.split(dirname)
                            filebase[fname] = filename
                    else:
                        directory, fname = os.path.split(dirname)
                        filebase[fname] = filename
        return(filebase)

    def existDataFile(self, *names):
        """
        check in both datapaths, if a file exists, first personal one is used
        in case it is not found last_error will mention the file name 
        """
        for path in [self.path_userdata, self.path_sysdata]:
            test = os.path.join(path, *[name for name in names])
            if os.path.isfile(test):
                return(test)
        self.last_error = "/".join([name for name in names]) + " not found"
        return None

    def dictFillGaps(self, standard, testdict):
        """
        recursively add elements from standard if dictionaries have missing data
        """
        changed = False
        for element in standard.keys():
            if element not in testdict:
                testdict[element] = standard[element]
                return True
            else:
                if isinstance(standard[element], dict):
                    changed = self.dictFillGaps(standard[element], testdict[element])
        return (changed)

    def logLine(self, level, line):
        """
        write to logfile
        """
        if self.verbose & level:
            print ("[" + str(level) + "] " + line)

    def loadSession(self):
        """
        load last saved session
        """
        default = { "mainwinsize": 
                { "w": 1200, "h": 800 }
        }
        self.session = None
        if self.config["remember_session"] is True:
            name = self.path_usersess
            self.logLine (2, "Read session from " + name)
            self.session = self.readJSON(name)
            if self.session == None:
                self.logLine (1, "JSON error " + self.last_error)

        if self.session is None:
            self.session = default
            self.logLine (2, "using standard session")
        else:
            # integrity test
            #
            self.dictFillGaps(default, self.session)

    def saveSession(self):
        """
        save last session (if desired)
        """
        if self.config["remember_session"] is True:
            name = self.path_usersess
            self.logLine(2, "Save session to " + name)
            if self.writeJSON(name, self.session) is False:
                self.logLine(1, self.last_error)
        else:
            self.logLine(2, "No need to save session")

    def cleanup(self):
        """
        all code for cleanup
        * close files
        """
        if self.path_stdout:
            sys.stdout.close()
        if self.path_stderr:
            sys.stderr.close()

