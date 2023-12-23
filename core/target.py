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
    def __init__(self, glob, name, icon, tip):
        self.glob     = glob
        self.obj      = glob.baseClass
        self.gwindow  = glob.openGLWindow

        self.name = name
        self.icon = icon
        self.tip  = tip
        self.selected = False
        self.value = 0.0
        self.default = 0.0
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
        if self.glob.targetMacros is not None:
            cnt = len(self.glob.targetMacros["macrodef"])

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

    def setDefault(self,default):
        self.default = default

    def resetValue(self):
        self.value = self.default
        if self.barycentric is not None:
            self.barycentric[0]["value"] = 0.33
            self.barycentric[1]["value"] = 0.33
            self.barycentric[2]["value"] = 0.34

    def set_barycentric(self, val):
        self.barycentric[0]["value"] = val[0]
        self.barycentric[1]["value"] = val[1]
        self.barycentric[2]["value"] = val[2]

    def search_pattern(self, user):
        """
        creates a pattern to be found in the target repo,
        for macros it is of a different type
        dual targets will be referenced by dual patterns, the opposites are defined in base.json
        single targets will be referenced by just the name
        user targets will get a "custom/" in front
        """

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
        if i == "None":
            return

        # use target opposites to find pattern (from base.json)
        #
        if "target-opposites" in self.obj.baseInfo:
            test = self.obj.baseInfo["target-opposites"]
            for elem in test:
                if d.endswith("-" + elem) and i.endswith("-" + test[elem]):
                    self.pattern = d + "|" + test[elem]
                    break

        if self.pattern == "None":
            self.pattern = i
            self.opposite = False

        if user == 1:
            self.pattern = "custom/" + self.pattern

    def set_refresh(self,refreshwindow):
        self.gwindow = refreshwindow

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
        """
        recursive function to generate weights.  Since for example 4 different components will change the character,
        one need to figure out how much each component will be used. Therefore one need to consider the components like a tree
        for the leaf the value itself is added, otherwise we do an recursion
        """
        if len(weights) > 0:
            for i in range(0,3):
                if  weights[0].names[i] is not None:
                    self.generateAllMacroWeights(targetlist, macroname + "-" +  weights[0].names[i], factor * weights[0].values[i], weights[1:])
        else:
            if factor > 0.01:
                targetlist.append ({"name": macroname[1:], "factor": factor})

    def macroCalculation(self, m_influence):
        macros = self.glob.targetMacros
        macrodef = macros["macrodef"]
        components = macros["components"]
        targetlist = []
        for l in m_influence:
            print ("   " + macrodef[l]["name"])
            comps = macrodef[l]["comp"]
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
                            if p not in self.glob.targetRepo:
                                continue
                            current = self.glob.targetRepo[p]
                            b = current.barycentric[i]["value"]
                            if b > 0.001:
                                print ("\t\tCurrent value " + v + " " + str(b))
                                m.insert(v, b)
                        weightarray.append(m)
                    else:
                        steps = components[elem]["steps"]
                        if pattern not in self.glob.targetRepo:
                            continue
                        #print (self.glob.targetRepo[pattern])
                        current = self.glob.targetRepo[pattern].value / 100
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

            self.generateAllMacroWeights(targetlist, "", 1.0, weightarray)

        # all components done, calculate weights as a product
        #
        #targetlist = []

        # The last step is the optimization: Some weightfiles are not existing.
        # So they would be a factor of 0. Sometimes targets are identical.
        # All targets are in memory and there are no duplicates. The calculated
        # target name will be mapped to the targets (using the value "t")
        # So it either add them the new targetname to a list or add the second factor if allready exists.

        sortedtargets = {}
        l = macros["targetlink"]

        for elem in targetlist:
            print (elem)
            name = elem["name"]
            if name is not None:
                if name in l:
                    if l[name] in sortedtargets:
                        sortedtargets[l[name]] += elem["factor"]
                    else:
                        sortedtargets[l[name]] = elem["factor"]
                else:
                    pass
                    #print (name + " not found")

        # add them to screen first
        #
        self.obj.baseMesh.clearMacroBuffer()
        for elem in sortedtargets:
            if elem in self.glob.macroRepo:
                print (elem, sortedtargets[elem])
                self.obj.baseMesh.addTargetToMacroBuffer(sortedtargets[elem], self.glob.macroRepo[elem])
        self.obj.baseMesh.addMacroBuffer()

    def callback(self, param=None):
        factor = self.value / 100
        if len(self.m_influence) > 0:
            print ("Macro change " +  str(self.m_influence))

            # extra parameter to get value from non-standard sliders
            # 
            if param is not None:
                self.set_barycentric(param.getValues())

            self.obj.baseMesh.subtractMacroBuffer()
            self.macroCalculation(self.m_influence)
            self.obj.updateAttachedAssets()
            self.glob.project_changed = True
            self.glob.mhViewport.setSizeInfo()
            self.gwindow.Tweak()

        elif self.incr is not None or self.decr is not None:
            print("change " + self.name)
            self.obj.updateByTarget(factor, self.decr, self.incr)
            self.glob.project_changed = True
            self.glob.mhViewport.setSizeInfo()
            self.gwindow.Tweak()

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

    def loadTargetData(self, path, bintargets=None):
        """
        get Target data either from pre-loaded npz file or from single targets
        """
        if bintargets is not None:
            if self.name in bintargets.files:
                self.env.logLine(8, "Use Data for " + self.name + " from binary file")
                self.raw = bintargets[self.name]
                self.verts = self.raw['index']
                self.data = self.raw['vector']
                return

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
        glob.Targets = self
        self.collection = None
        self.macrodef = None
        self.baseClass = glob.baseClass

    def __str__(self):
        return ("Target-Collection: " + str(self.collection))

    def loadModellingJSON(self):
        targetpath = os.path.join(self.env.path_sysdata, "target", self.env.basename)

        filename = os.path.join(targetpath, "macro.json")
        self.macrodef = self.env.readJSON(filename)
        if self.macrodef is not None:
            l = self.macrodef["targetlink"] = {}
            if "macrodef" in self.macrodef:
                for mtype in self.macrodef["macrodef"]:
                    if "folder" in mtype:
                        folder = mtype["folder"]
                    if "targets" in mtype:
                        for elem in mtype["targets"]:
                            if "name" in elem and "t" in elem:
                                if elem["t"] is not None:
                                    l[elem["name"]] = os.path.join(folder, elem["t"])
                                else:
                                    l[elem["name"]] = None # to support empty or non-existent targets
                        mtype["targets"] = None  # no longer needed
            self.glob.targetMacros = self.macrodef

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
        target_env = [ {
            "targetpath": os.path.join(self.env.path_sysdata, "target", self.env.basename),
            "targets": None
            }, {
            "targetpath": os.path.join(self.env.path_userdata, "target", self.env.basename),
            "targets": None
        }]

        default_icon = os.path.join(self.env.path_sysicon, "empty_target.png")
        self.collection = self.env.basename

        tg = TargetCategories(self.glob)
        tg.readFiles()

        targetjson = self.loadModellingJSON()
        if targetjson is None:
            self.env.logLine(1, self.env.last_error )
            return
       
        # load binary targets
        #
        for x in target_env:
            bintargets = os.path.join(x["targetpath"], "compressedtargets.npz")
            if os.path.exists(bintargets):
                print (bintargets + " are available")
                x["targets"] = np.load(bintargets)

        # load macrotargets (atm only system path)
        #
        if  self.macrodef is not None:
            for link in self.macrodef["targetlink"]:
                name = self.macrodef["targetlink"][link]
                if name is not None and name not in self.glob.macroRepo:
                    mt = Morphtarget(self.env, name)
                    mt.loadTargetData(target_env[0]["targetpath"], target_env[0]["targets"])
                    self.glob.macroRepo[name] = mt

        # load targets mentioned in modelling.json
        #
        for name in targetjson:
            t = targetjson[name]
            tip = t["tip"] if "tip" in t else "Select to modify"

            mode = 1 if "user" in t else 0
            targetpath = target_env[mode]["targetpath"]
            bintargets = target_env[mode]["targets"]

            iconpath = os.path.join(targetpath, "icons")
            icon = os.path.join(iconpath, t["icon"]) if "icon" in t else default_icon
            m = Modelling(self.glob, name, icon, tip)

            if "decr" in t:
                mt = Morphtarget(self.env, t["decr"])
                mt.loadTargetData(targetpath, bintargets)
                m.decr_target(mt)
            if "incr" in t:
                mt = Morphtarget(self.env, t["incr"])
                mt.loadTargetData(targetpath, bintargets)
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
            if "default" in t:
                m.setDefault(t["default"] * 100)
            m.search_pattern(mode)
            if m.pattern != "None":
                if isinstance(m.pattern, list):
                    for l in m.pattern:
                        self.glob.targetRepo[l["name"]] = m
                else:
                    self.glob.targetRepo[m.pattern] = m
            self.modelling_targets.append(m)

    def saveBinaryTargets(self, sys_user = 3):
        """
        save targets as compressed binary
        :param sys_user: 1 = system, 2 = user (3 is both)
        """
        # get a content list of all targets and add them to either system content or user content
        #
        # TODO; check files ...

        contentsys = {}
        contentuser = {}
        for target in self.glob.macroRepo.values():
            contentsys[target.name] = target.raw
        for target in self.glob.targetRepo.values():
            if target.group is not None and target.group.startswith("user|"):
                if target.incr is not None:
                    contentuser[target.incr.name] = target.incr.raw
                if target.decr is not None:
                    contentuser[target.decr.name] = target.decr.raw
            else:
                if target.incr is not None:
                    contentsys[target.incr.name] = target.incr.raw
                if target.decr is not None:
                    contentsys[target.decr.name] = target.decr.raw

        if sys_user & 1:
            sysbinpath = os.path.join(self.env.path_sysdata, "target", self.env.basename, "compressedtargets.npz")
            f = open(sysbinpath, "wb")
            np.savez_compressed(f, **contentsys)
            f.close()

        if sys_user & 2:
            userbinpath = os.path.join(self.env.path_userdata, "target", self.env.basename, "compressedtargets.npz")
            f = open(userbinpath, "wb")
            np.savez_compressed(f, **contentuser)
            f.close()




    def refreshTargets(self, window):
        """
        refreshes Callbacks
        """
        for target in self.modelling_targets:
            target.set_refresh(window)

    def reset(self):
        for target in self.modelling_targets:
            target.resetValue()

    def setTargetByName(self, key, value):
        """
        set values
        """
        if key in self.glob.targetRepo:
            t = self.glob.targetRepo[key]
            print (" >>> Found target: " + key)
            if t.barycentric is not None:
                for l in t.barycentric:
                    if l["name"] == key:
                        l["value"] = float(value)
            else:
                t.value = float(value) * 100.0
        else:
            self.glob.missingTargets.append(key)

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
        #
        # system first (TODO: what about user only meshes?)
        #
        targetpath = os.path.join(self.env.path_sysdata, "target", self.basename)
        filename = os.path.join(targetpath, "target_cat.json")
        categoryjson = self.env.readJSON(filename)

        # now user
        #
        targetpath = os.path.join(self.env.path_userdata, "target", self.basename)

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
            categoryjson["User"] = userjson["User"]

        # make it globally available
        #
        self.glob.targetCategories = categoryjson

