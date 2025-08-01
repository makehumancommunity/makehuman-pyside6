"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * TargetCategories
"""

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
        self.user_targets = []
        self.icon_repos = []

    def addUserTarget(self, folder, subfolder, filename, latest ):
        if subfolder is None:
            fname = os.path.join(folder, filename)
        else:
            fname = os.path.join(folder, subfolder, filename)
            filename = os.path.join(subfolder, filename)
        mod = int(os.stat(fname).st_mtime)
        self.user_targets.append(filename[:-7])
        
        if mod > latest:
            self.env.logTime(mod, "Newer modification time detected for: " + filename)
            return (True)
        return(False)

    def formatModellingEntry(self, user_mod, cats, folder, filename):
        """
        :param: filename is target without suffix
        """
        name = filename.replace('-', ' ') # display name
        if folder is not None:
            fname = folder + "/" + filename         # URI style
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
                oppentry = folder + "/" + filename.replace("incr", "decr")          # entries are in URI style
            else:
                opposite = filename.replace("incr", "decr")
            if opposite in cats:
                self.env.logLine(2, "Dual target: " + filename + " / "  + opposite)
                name = name[:-5]
                elem = elem[:-5]
                user_mod[elem] = ({"user": 1, "name": name, "group": group,  "incr": fname, "decr": oppentry })

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
            self.env.logLine(2, "Simple target: " + filename)
            user_mod[elem] = ({"user": 1, "name": name, "group": group,  "incr": fname })
            iconname = iconname + ".png"
            if iconname in self.icon_repos:
                user_mod[elem]["icon"] = iconname

    def getIcons(self, folder, latest):
        dirs = os.listdir(folder)
        rescan = False
        for ifile in dirs:
            if ifile.endswith(".png"):
                fname = os.path.join(folder, ifile)
                mod = int(os.stat(fname).st_mtime)
                self.icon_repos.append(ifile)
                if mod > latest:
                    self.env.logTime(mod, "Newer modification time detected for: " + ifile)
                    rescan = True
        return (rescan)

    def getAListOfTargets(self, folder, latest):
        """
        scan targets, two layers as a maximum
        """
        # check own folder
        #
        mod = int(os.stat(folder).st_mtime)
        rescan = ( mod > latest)

        dirs = os.listdir(folder)
        for ifile in dirs:

            fname = os.path.join(folder, ifile)

            # read names of the icons
            #
            if ifile == "icons":
                rescan |= self.getIcons(fname, latest)
                continue

            # we don't do it recursive to avoid more than two layers
            #
            if os.path.isdir(fname):
                # check sub folder
                #
                mod = int(os.stat(fname).st_mtime)
                rescan |= ( mod > latest)

                dir2s = os.listdir(fname)
                for ifile2 in dir2s:
                    if ifile2.endswith(".target"):
                        rescan |= self.addUserTarget(folder, ifile, ifile2, latest)

            elif ifile.endswith(".target"):
                rescan |= self.addUserTarget(folder, None, ifile, latest)

        return (rescan)


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

    def recreateUserCategories(self):
        """
        recreates target category for user space 
        """
        mod_cat = 0
        mod_modelling = 0
        targetpath = self.env.stdUserPath("target")

        # if folder does not exists do nothing
        #
        if not os.path.isdir(targetpath):
            self.env.logLine(8, "No target folder for " + self.basename + " in user space")
            return None

        #    check for "target_cat.json" (with date)
        #
        catfilename = os.path.join(targetpath, "target_cat.json")
        if os.path.isfile(catfilename):
            mod_cat = int(os.stat(catfilename).st_mtime)
            self.env.logTime(mod_cat, "last change of User target category file")
        else:
            self.env.logLine(8, "User target category file does not exists")

        #    check for "modelling.json" (with date)
        #
        modfilename = os.path.join(targetpath, "modelling.json")
        if os.path.isfile(modfilename):
            mod_modelling = int(os.stat(modfilename).st_mtime)
            self.env.logTime(mod_modelling, "last change of User target modelling.json")
        else:
            self.env.logLine(8, "User target modelling file does not exists")

        lastcreated = mod_cat if mod_cat < mod_modelling else mod_modelling

        # now scan targets
        #
        rescan = self.getAListOfTargets(targetpath, lastcreated)
        if rescan:
            (json_cat_object, json_mod_object) = self.createJStruct(self.user_targets)
            self.env.writeJSON(catfilename, json_cat_object)
            self.env.logLine(8, "New user target category file written")
            self.env.writeJSON(modfilename, json_mod_object)
            self.env.logLine(8, "New user target modelling file written")
        else:
            self.env.logLine(8, "User target category and modelling file is not changed")

        userjson = self.env.readJSON(catfilename)
        return userjson

    def connectCategories(self, json):
        if self.glob.targetCategories is not None:
            self.glob.targetCategories["User"] = json["User"]
        else:
            self.glob.targetCategories = json         # only user targets

    def readFiles(self):
        """
        create internal structure of target categories
        the user category is appended to system category
        """

        # read the system target category first
        #
        filename = os.path.join(self.env.stdSysPath("target"), "target_cat.json")

        # make it globally available and add user categories
        #
        self.glob.targetCategories = self.env.readJSON(filename)
        self.newUserCategories()

    def newUserCategories(self):
        userjson = self.recreateUserCategories()
        self.connectCategories(userjson)

    def findUserAsset(self, search):
        s1 = search[:-7]
        s2 = "/" + s1
        targetpath = self.env.stdUserPath("target")
        modfilename = os.path.join(targetpath, "modelling.json")
        json = self.env.readJSON(modfilename)
        found = None
        for name, t in json.items():
            if t["incr"].endswith(s2) or t["incr"] == s1:
                found = name
                return name, t
            if "decr" in t and (t["decr"].endswith(s2) or t["decr"] == s1):
                found = name
                return name, t

        return None, None
