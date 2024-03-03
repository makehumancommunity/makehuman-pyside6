import os

class TargetCategories:
    """
    class to support the files for categories, creates also JSON files
    for categories in User space
    """

    def __init__(self, glob):
        self.glob = glob
        self.env = glob.env
        self.basename = self.env.basename
        self.mod_cat = 0
        self.mod_modelling = 0
        self.mod_latest = 0
        self.user_targets = []
        self.icon_repos = []

    def addUserTarget(self, folder, subfolder, filename ):
        if subfolder is None:
            fname = os.path.join(folder, filename)
        else:
            fname = os.path.join(folder, subfolder, filename)
            filename = os.path.join(subfolder, filename)
        mod = int(os.stat(fname).st_mtime)
        if mod > self.mod_latest:
            self.env.logLine(8, "Newer modification time detected: " + filename + " " + str(mod))
            self.mod_latest = mod
        self.user_targets.append(filename[:-7])


    def formatModellingEntry(self, user_mod, cats, folder, filename):
        """
        :param: filename is target without suffix
        """
        name = filename.replace('-', ' ') # display name
        if folder is not None:
            fname = os.path.join(folder, filename)
            elem = folder.capitalize() + " " + name.capitalize()
            group = "user|" + folder
            iconname = folder + "-" + filename
        else:
            fname = filename
            elem = "User " + name.capitalize()
            group = "user|unsorted"
            iconname = filename

        dualtarget = False
        if filename.endswith("incr"):
            if folder is not None:
                opposite = os.path.join(folder, filename.replace("incr", "decr"))
            else:
                opposite = filename.replace("incr", "decr")
            if opposite in cats:
                print ("Dual target: " + filename + " / "  + opposite)
                name = name[:-5]
                elem = elem[:-5]
                user_mod[elem] = ({"user": 1, "name": name, "group": group,  "incr": fname, "decr": opposite })

                iconname = iconname[:-5] + ".png"
                if iconname in self.icon_repos:
                    user_mod[elem]["icon"] = iconname
                dualtarget = True

        elif filename.endswith("decr"):
            if folder is not None:
                opposite = os.path.join(folder, filename.replace("decr", "incr"))
            else:
                opposite = filename.replace("decr", "incr")

            if opposite in cats:
                dualtarget = True

        if dualtarget is False:
            print ("Simple target: " + filename)
            user_mod[elem] = ({"user": 1, "name": name, "group": group,  "incr": fname })
            iconname = iconname + ".png"
            if iconname in self.icon_repos:
                user_mod[elem]["icon"] = iconname

    def getIcons(self, folder):
        dirs = os.listdir(folder)
        for ifile in dirs:
            if ifile.endswith(".png"):
                fname = os.path.join(folder, ifile)
                mod = int(os.stat(fname).st_mtime)
                if mod > self.mod_latest:
                    self.env.logLine(8, "Newer modification time detected: " + ifile + " " + str(mod))
                    self.mod_latest = mod
                self.icon_repos.append(ifile)

    def getAListOfTargets(self, folder):
        """
        allow two layers as a maximum
        """
        dirs = os.listdir(folder)
        for ifile in dirs:

            fname = os.path.join(folder, ifile)

            # read names of the icons
            #
            if ifile == "icons":
                self.getIcons(fname)
                continue

            # we don't do it recursive to avoid more than two layers
            #
            if os.path.isdir(fname):
                dir2s = os.listdir(fname)
                for ifile2 in dir2s:
                    if ifile2.endswith(".target"):
                        self.addUserTarget(folder, ifile, ifile2)

            elif ifile.endswith(".target"):
                self.addUserTarget(folder, None, ifile)


    def createJStruct(self, categories):
        user_mod = {}
        cat_list = []
        user_cat = {"User": {"group": "user", "items": [] }}
        items = user_cat["User"]["items"]
        for elem in categories:
            if "/" in elem:
                (d, f) = elem.split("/")
                if d not in cat_list:
                    cat_list.append(d)
                    items.append( {"title": d.capitalize(), "cat": d } )
                self.formatModellingEntry(user_mod, categories, d, f)
            elif "\\" in elem:
                (d, f) = elem.split("\\")
                if d not in cat_list:
                    cat_list.append(d)
                    items.append( {"title": d.capitalize(), "cat": d } )
                self.formatModellingEntry(user_mod, categories, d, f)
            else:
                if "unsorted" not in cat_list:
                    cat_list.append("unsorted")
                    items.append( {"title": "Unsorted", "cat": "unsorted" } )
                self.formatModellingEntry(user_mod, categories, None, elem)

        return (user_cat, user_mod)

    def readFiles(self):
        """
        create internal structure of target categories
        this method re-creates a target category for user space 
        the user category is appended to system category
        """

        # read the system target category first
        #
        filename = os.path.join(self.env.stdSysPath("target"), "target_cat.json")
        categoryjson = self.env.readJSON(filename)

        # now user
        #
        targetpath = self.env.stdUserPath("target")

        # if folder does not exists do nothing
        #
        if not os.path.isdir(targetpath):
            self.env.logLine(8, "No target folder for " + self.basename + " in user space")
            return (categoryjson)

        #    check for "target_cat.json" (with date)
        #
        catfilename = os.path.join(targetpath, "target_cat.json")
        if os.path.isfile(catfilename):
            self.mod_cat = int(os.stat(catfilename).st_mtime)
            self.env.logLine(8, "User target category file exists and last modified: " + str(self.mod_cat))
        else:
            self.env.logLine(8, "User target category file does not exists")
            self.mod_cat = 0

        #    check for "modelling.json" (with date)
        #
        modfilename = os.path.join(targetpath, "modelling.json")
        if os.path.isfile(modfilename):
            self.mod_modelling = int(os.stat(modfilename).st_mtime)
            self.env.logLine(8, "User target modelling file exists and last modified: " + str(self.mod_modelling))
        else:
            self.env.logLine(8, "User target modelling file does not exists")

        # now scan targets
        #
        self.getAListOfTargets(targetpath)
        if self.mod_latest > self.mod_cat or self.mod_latest > self.mod_modelling:
            (json_cat_object, json_mod_object) = self.createJStruct(self.user_targets)
            self.env.writeJSON(catfilename, json_cat_object)
            self.env.logLine(8, "New user target category file written")
            self.env.writeJSON(modfilename, json_mod_object)
            self.env.logLine(8, "New user target modelling file written")
        else:
            self.env.logLine(8, "User target category and modelling file is not changed")

        userjson = self.env.readJSON(catfilename)
        if userjson is not None:
            if categoryjson is not None:
                categoryjson["User"] = userjson["User"]
            else:
                categoryjson = userjson         # only user targets

        # make it globally available
        #
        self.glob.targetCategories = categoryjson

