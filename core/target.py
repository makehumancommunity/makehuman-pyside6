import os
import sys
import json
import numpy as np

class MacroTree:
    def __init__(self):
        self.names = [ None, None, None ]
        self.values = [ 0.0, 0.0, 0.0 ]

    def insert(self, name, value):
        for i in range(0, 3):
            if self.names[i] is None:
                self.names[i] = name
                self.values[i] = value
                return

    def __str__(self):
        return (str(self.names) + " " + str(self.values))


class Modelling:
    def __init__(self, parent, name, icon, tip):
        self.glob     = parent.glob
        self.obj      = parent.baseClass
        self.refresh  = parent.graphwindow
        self.macrodef = parent.macrodef      # pointer to macrodefinition
        self.target_repo = parent.target_repo # pointer for other targets
        self.macro_repo = parent.macro_repo # pointer for macro

        self.name = name
        self.icon = icon
        self.tip  = tip
        self.selected = False
        self.value = 0.0
        self.incr = None    # target "incr"
        self.decr = None    # target "decr"
        self.macro = None   # macro target
        self.m_influence = []   # all influences
        self.barycentric = None # map slider
        self.opposite = True # two.directional slider
        self.displayname = name
        self.group = None
        self.pattern = "None"

    def __str__(self):
        return (self.name + ": " + str(self.incr) + "/" + str(self.decr))

    def memInfo(self):
        if self.barycentric:
            text = ""
            value = "0"
            if isinstance(self.pattern, list):
                l = self.pattern
                text  = l[0]["name"] + " " + l[1]["name"] + " " + l[2]["name"]
                value = str(l[0]["value"] * 100) + " " + str(l[1]["value"] * 100) + "  " + str(l[2]["value"] * 100)
            t = [self.name, "barycentric", -1, "barycentric", -1, text, value]
        elif self.macro:
            t = [self.name, str(self.macro), -1, str(self.macro), -1, self.pattern, self.value]
        else:
            li = len(self.incr.verts) if self.incr else 0
            ld = len(self.decr.verts) if self.decr else 0
            t = [self.name, str(self.incr), li, str(self.decr), ld, self.pattern, self.value]
        return (t)


    def incr_target(self, fname):
        self.incr = fname

    def decr_target(self, fname):
        self.decr = fname

    def macro_target(self, name):
        self.macro = name

    def macro_influence(self, array):
        #
        self.m_influence = []
        if self.macrodef is not None:
            cnt = len(self.macrodef["macrodef"])

            # test boundaries to avoid crashes
            #
            for elem in array:
                if elem < cnt:
                    self.m_influence.append(elem)

    def macro_barycentric(self, val):
        text = ["A", "B", "C"]
        #value = [0.33, 0.33, 0.33]
        value = [0.0, 0.0, 1.0]
        i = 0
        for x in val:
            text[i] = x.split("/")[1] if "/" in x else x
            i += 1
        self.barycentric = [
                {"name": val[0], "text": text[0], "value": value[0] },
                {"name": val[1], "text": text[1], "value": value[1] },
                {"name": val[2], "text": text[2], "value": value[2] } ]

    def set_barycentric(self, val):
        self.barycentric[0]["value"] = val[0]
        self.barycentric[1]["value"] = val[1]
        self.barycentric[2]["value"] = val[2]

    def search_pattern(self):
        if self.barycentric:
            self.pattern = self.barycentric
            self.opposite = False
            return
        if self.macro:
            self.pattern = self.macro
            self.opposite = False
            return

        d = str(self.decr)
        i = str(self.incr)
        self.pattern = "None"
        if d.endswith("-decr") and i.endswith("-incr"):
            self.pattern = d + "|incr"
        elif d.endswith("-down") and i.endswith("-up"):
            self.pattern = d + "|up"
        elif d.endswith("-in") and i.endswith("-out"):
            self.pattern = d + "|out"
        elif d.endswith("-backward") and i.endswith("-forward"):
            self.pattern = d + "|forward"
        elif d.endswith("-concave") and i.endswith("-convex"):
            self.pattern = d + "|convex"
        elif i != "None":
            self.pattern = i
            self.opposite = False

    def set_refresh(self,refreshwindow):
        self.refresh = refreshwindow

    def set_displayname(self, name):
        self.displayname = name

    def set_group(self, name):
        self.group = name

    def initialize(self):
        factor = self.value / 100
        print("init  " + self.name)
        if self.incr is not None or self.decr is not None:
            self.obj.getInitialCopyForSlider(factor, self.decr, self.incr)

    def generateAllMacroWeights(self, targetlist, macroname, factor, weights):
        if len(weights) > 0:
            for i in range(0,3):
                if  weights[0].names[i] is not None:
                    self.generateAllMacroWeights(targetlist, macroname + "-" +  weights[0].names[i], factor * weights[0].values[i], weights[1:])
        else:
            if factor > 0.01:
                targetlist.append ({"name": macroname[1:], "factor": factor})

    def macroCalculation(self):
        influences = self.macrodef["macrodef"]
        components = self.macrodef["components"]
        for l in self.m_influence:
            print ("   " + influences[l]["name"])
            comps = influences[l]["comp"]
            weightarray = []
            for elem in comps:
                if elem in components:
                    pattern = components[elem]["pattern"]
                    values  = components[elem]["values"]
                    print ("\t\tPattern:" +  str(pattern) + " " + str(values))

                    if "steps" not in components[elem]:

                        # extra for sum of sliders (human phenotype)
                        #
                        sum = components[elem]["sum"]
                        m = MacroTree()
                        for i,v in enumerate(values):
                            p = pattern +  sum[i]
                            if p not in self.target_repo:
                                continue
                            current = self.target_repo[p]
                            b = current.barycentric[i]["value"]
                            if b > 0.001:
                                print ("\t\tCurrent value " + v + " " + str(b))
                                m.insert(v, b)
                        weightarray.append(m)
                    else:
                        steps = components[elem]["steps"]
                        if pattern not in self.target_repo:
                            continue
                        #print (self.target_repo[pattern])
                        current = self.target_repo[pattern].value / 100
                        print ("\t\tCurrent " + str(current) + " Divisions: " + str(len(steps)))

                        for i in range(0,len(steps)-1):
                            if current > steps[i+1]:
                                continue
                            else:
                                c = (current - steps[i]) / (steps[i+1] - steps[i])
                                m = MacroTree()
                                if c < 0.999:
                                    m.insert(values[i], 1-c)
                                if c > 0.001:
                                    m.insert(values[i+1], c)
                                weightarray.append(m)
                                break
                else:
                    if elem.startswith("!"):

                        # use component as name (always 100%)
                        #
                        m = MacroTree()
                        m.insert(elem[1:], 1.0)
                        weightarray.append(m)

            # all components done
            #
            targetlist = []
            self.generateAllMacroWeights(targetlist, "", 1.0, weightarray)

            # now the target list is found, last step: use real name and find double targets
            #
            sortedtargets = {}
            l = self.macrodef["targetlink"]

            for elem in targetlist:
                print (elem)
                name = elem["name"]
                if name in l:
                    if l[name] in sortedtargets:
                        sortedtargets[l[name]] += elem["factor"]
                    else:
                        sortedtargets[l[name]] = elem["factor"]

            # add them to screen first
            # TODO; must be replaced by set command
            #
            for elem in sortedtargets:
                if elem in self.macro_repo:
                    print (elem, sortedtargets[elem])
                    self.obj.updateByTarget(sortedtargets[elem], None, self.macro_repo[elem])
            self.refresh.Tweak()

    def callback(self, param=None):
        factor = self.value / 100
        if len(self.m_influence) > 0:
            print ("Macro change " +  str(self.m_influence))

            # extra parameter to get value from non-standard sliders
            # 
            if param is not None:
                self.set_barycentric(param.getValues())

            self.macroCalculation()
        elif self.incr is not None or self.decr is not None:
            print("change " + self.name)
            self.obj.updateByTarget(factor, self.decr, self.incr)
            self.refresh.Tweak()

    #def __del__(self):
    #    print (" -- __del__ Modelling: " + self.name)


class Morphtarget:
    """
    handle a single target
    """
    def __init__(self, env, name):
        self.dtype = [('index','u4'),('vector','(3,)f4')]
        self.name = name
        self.raw  = None
        self.verts= None
        self.data = []
        self.env  = env

    def __str__(self):
        return (self.name)

    def loadTextFile(self, path):
        filename = os.path.join(path, self.name) + ".target"
        try:
            fd = open(filename, 'r', encoding='utf-8')
        except:
            self.env.logLine(1, "Cannot load:" + filename)
        else:
            self.env.logLine(8, "Load: " + filename)
            for line in fd:
                line = line.strip()
                if line.startswith('#'):
                    continue
                translationData = line.split()
                if len(translationData) != 4:
                    continue
                vertIndex = int(translationData[0])
                translationVector = (float(translationData[1]), float(translationData[2]), float(translationData[3]))
                self.data.append((vertIndex, translationVector))
            self.raw = np.asarray(self.data, dtype=self.dtype)
            self.verts = self.raw['index']
            self.data = self.raw['vector']

    def releaseNumpy(self):
        if self.raw is not None:
            self.verts = None
            self.raw = None
            self.data = []

    def __del__(self):
        self.env.logLine(4, " -- __del__ Morphtarget: " + self.name)


class Targets:
    def __init__(self, glob):
        self.glob =glob
        self.env = glob.env
        self.modelling_targets = []
        self.target_repo = {} # will contain targets by pattern
        self.macro_repo = {}  # will contain macro targets
        glob.Targets = self
        self.collection = None
        self.macrodef = None
        self.baseClass = glob.baseClass
        self.graphwindow = glob.graphwindow

    def __str__(self):
        return ("Target-Collection: " + str(self.collection))

    def loadModellingJSON(self):
        targetpath = os.path.join(self.env.path_sysdata, "target", self.env.basename)

        filename = os.path.join(targetpath, "macro.json")
        self.macrodef = self.env.readJSON(filename)
        l = self.macrodef["targetlink"] = {}
        if "macrodef" in self.macrodef:
            for mtype in self.macrodef["macrodef"]:
                if "folder" in mtype:
                    folder = mtype["folder"]
                if "targets" in mtype:
                    for elem in mtype["targets"]:
                        if "name" in elem and "t" in elem:
                            l[elem["name"]] = os.path.join(folder, elem["t"])
                    mtype["targets"] = None  # no longer needed

        filename = os.path.join(targetpath, "modelling.json")
        targetjson = self.env.readJSON(filename)

        targetpath = os.path.join(self.env.path_userdata, "target", self.env.basename)
        filename = os.path.join(targetpath, "modelling.json")
        userjson = self.env.readJSON(filename)

        if targetjson is None:
            return (userjson)

        if userjson is not None:
            for elem in userjson:
                targetjson[elem] = userjson[elem]

        return (targetjson)

    def loadTargets(self):
        default_icon = os.path.join(self.env.path_sysicon, "empty_target.png")
        targetpath_sys = os.path.join(self.env.path_sysdata, "target", self.env.basename)
        targetpath_user = os.path.join(self.env.path_userdata, "target", self.env.basename)
        self.collection = self.env.basename

        tg = TargetCategories(self.glob)
        tg.readFiles()

        targetjson = self.loadModellingJSON()
        if targetjson is None:
            self.env.logLine(1, self.env.last_error )
            return
        
        # load macrotargets (atm only system path)
        #
        for link in self.macrodef["targetlink"]:
            name = self.macrodef["targetlink"][link]
            if name not in self.macro_repo:
                mt = Morphtarget(self.env, name)
                mt.loadTextFile(targetpath_sys)
                self.macro_repo[name] = mt

        # load targets mentioned in modelling.json
        #
        for name in targetjson:
            t = targetjson[name]
            tip = t["tip"] if "tip" in t else "Select to modify"
            targetpath = targetpath_user if "user" in t else targetpath_sys
            iconpath = os.path.join(targetpath, "icons")
            icon = os.path.join(iconpath, t["icon"]) if "icon" in t else default_icon
            m = Modelling(self, name, icon, tip)

            if "decr" in t:
                mt = Morphtarget(self.env, t["decr"])
                mt.loadTextFile(targetpath)
                m.decr_target(mt)
            if "incr" in t:
                mt = Morphtarget(self.env, t["incr"])
                mt.loadTextFile(targetpath)
                m.incr_target(mt)
            if "macro" in t:
                m.macro_target(t["macro"])
            if "macro_influence" in t:
                m.macro_influence(t["macro_influence"])
            if "barycentric" in t:
                m.macro_barycentric(t["barycentric"])
            if "name" in t:
                m.set_displayname(t["name"])
            if "group" in t:
                m.set_group(t["group"])
            m.search_pattern()
            if m.pattern != "None":
                if isinstance(m.pattern, list):
                    for l in m.pattern:
                        self.target_repo[l["name"]] = m
                else:
                    self.target_repo[m.pattern] = m
            self.modelling_targets.append(m)

    def refreshTargets(self, window):
        """
        refreshes Callbacks
        """
        for target in self.modelling_targets:
            target.set_refresh(window)

    def reset(self):
        #
        # TODO: might be a different value for certain targets later
        #
        for target in self.modelling_targets:
            target.value = 0.0

    def setTargetByName(self, key, value):
        """
        set values
        """
        if key in self.target_repo:
            t = self.target_repo[key]
            print (" >>> Found target: " + key)
            if t.barycentric is not None:
                for l in t.barycentric:
                    if l["name"] == key:
                        l["value"] = float(value)
            else:
                t.value = float(value) * 100.0

    def modifierPresets(self, presets):
        """
        set presets from base.json
        """
        for elem in presets:
            self.setTargetByName(elem, presets[elem])


    def destroyTargets(self):
        self.env.logLine (2, "destroy Targets:" + str(self.collection))

        for m in self.modelling_targets:
            if m.incr:
                m.incr.releaseNumpy()
            if m.decr:
                m.decr.releaseNumpy()

        self.modelling_targets = []

    def __del__(self):
        if self.collection is not None:
            self.env.logLine (4, " -- __del__ Targets: " + self.collection)

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
        print ("Name: " + name)
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
        if filename.endswith("incr"):
            if folder is not None:
                opposite = os.path.join(folder, filename.replace("incr", "decr"))
            else:
                opposite = filename.replace("incr", "decr")
            print ("Need to check for " + opposite)
            if opposite in cats:
                name = name[:-5]
                elem = elem[:-5]
                user_mod[elem] = ({"user": 1, "name": name, "group": group,  "incr": fname, "decr": opposite })

                iconname = iconname[:-5] + ".png"
                if iconname in self.icon_repos:
                    user_mod[elem]["icon"] = iconname
        elif filename.endswith("decr"):
            if folder is not None:
                opposite = os.path.join(folder, filename.replace("decr", "incr"))
            else:
                opposite = filename.replace("decr", "incr")

            print ("Need to check for " + opposite)
            if opposite not in cats:
                user_mod[elem] = ({"user": 1, "name": name, "group": group,  "incr": fname })
                iconname = iconname + ".png"
                if iconname in self.icon_repos:
                    user_mod[elem]["icon"] = iconname
        else:
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
            print (elem)
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
        #
        # system first (TODO: what about user only meshes?)
        #
        targetpath = os.path.join(self.env.path_sysdata, "target", self.basename)
        filename = os.path.join(targetpath, "target_cat.json")
        targetjson = self.env.readJSON(filename)

        # now user
        #
        targetpath = os.path.join(self.env.path_userdata, "target", self.basename)

        # if folder does not exists do nothing
        #
        if not os.path.isdir(targetpath):
            self.env.logLine(8, "No target folder for " + self.basename + " in user space")
            return (targetjson)

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
            targetjson["User"] = userjson["User"]

        # make it globally available
        #
        self.glob.targetCategories = targetjson

