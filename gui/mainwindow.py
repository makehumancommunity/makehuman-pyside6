from PySide6.QtWidgets import ( 
        QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QGroupBox, QListWidget,
        QAbstractItemView, QSizePolicy, QScrollArea, QFileDialog, QDialogButtonBox, QMessageBox
        )
from PySide6.QtGui import QIcon, QCloseEvent, QAction
from PySide6.QtCore import QSize, Qt
from gui.prefwindow import  MHPrefWindow
from gui.logwindow import  MHLogWindow
from gui.infowindow import  MHInfoWindow
from gui.memwindow import  MHMemWindow
from gui.scenewindow import  MHSceneWindow
from gui.graphwindow import  MHGraphicWindow, NavigationEvent
from gui.fileactions import BaseSelect, SaveMHMForm, DownLoadImport
from gui.slider import ScaleComboArray
from gui.imageselector import ImageSelection, IconButton
from gui.dialogs import DialogBox, ErrorBox, WorkerThread, MHBusyWindow
from gui.qtreeselect import MHTreeView
from core.baseobj import baseClass

import os

class MHMainWindow(QMainWindow):
    """
    Main Window class
    """
    def __init__(self, glob):
        self.env = glob.env
        env = glob.env
        self.glob = glob
        self.pref_window = None
        self.mem_window = None
        self.scene_window = None
        self.material_window = None
        self.info_window = None
        self.log_window = None
        self.rightColumn = None
        self.leftColumn = None
        self.graph = None
        self.qTree = None

        self.BaseBox = None         # layouts to fill
        self.ToolBox = None
        self.ButtonBox = None
        self.CategoryBox = None
        self.baseSelector = None

        self.in_close = False
        self.targetfilter = None
        self.bckproc = None         # background process is running
        self.prog_window = None     # will hold the progress window

        self.tool_mode = 0          # 0 = files, 1 = modelling, 2 = equipment, 3 = pose, 4 render
        self.category_mode = 0      # the categories according to tool_mode

        self.equipment = [
                { "func": None, "menu": None, "name": "clothes", "mode": 1 },
                { "func": None, "menu": None, "name": "hair", "mode": 0 },
                { "func": None, "menu": None, "name": "eyes", "mode": 0 },
                { "func": None, "menu": None, "name": "eyebrows", "mode": 0 },
                { "func": None, "menu": None, "name": "eyelashes", "mode": 0 },
                { "func": None, "menu": None, "name": "teeth", "mode": 0 },
                { "func": None, "menu": None, "name": "tongue", "mode": 0 },
                { "func": None, "menu": None, "name": "topology", "mode": 0 }
        ]

        self.model_buttons = [ 
                { "button": None, "icon": "reset.png", "tip": "Reset all targets", "func": self.reset_call},
                { "button": None, "icon": "symm1.png", "tip": "Symmetry, right to left", "func": self.symRToL },
                { "button": None, "icon": "symm2.png", "tip": "Symmetry, left to right", "func": self.symLToR },
                { "button": None, "icon": "symm.png", "tip": "Symmetry applied always", "func": self.symSwitch }
        ]

        self.tool_buttons = [ 
                { "button": None, "icon": "files.png", "tip": "Files", "func": self.setCategoryIcons},
                { "button": None, "icon": "sculpt.png", "tip": "Modelling, Change character", "func": self.setCategoryIcons},
                { "button": None, "icon": "equip.png", "tip": "Add equipment", "func": self.setCategoryIcons },
                { "button": None, "icon": "pose.png", "tip": "Pose", "func": self.setCategoryIcons },
                { "button": None, "icon": "render.png", "tip": "Render", "func": self.setCategoryIcons }
        ]
        self.category_buttons = [
            [ 
                { "button": None, "icon": "f_newbase.png", "tip": "new basemesh", "func": self.callCategory},
                { "button": None, "icon": "f_load.png", "tip": "load character", "func": self.callCategory},
                { "button": None, "icon": "f_save.png", "tip": "save character", "func": self.callCategory},
                { "button": None, "icon": "f_export.png", "tip": "export character", "func": self.callCategory},
                { "button": None, "icon": "f_download.png", "tip": "download assets", "func": self.callCategory}
            ], [ 
            ], [
                { "button": None, "icon": "eq_clothes.png", "tip": "Clothes", "func": self.callCategory },
                { "button": None, "icon": "eq_hair.png", "tip": "Hair", "func": self.callCategory },
                { "button": None, "icon": "eq_eyes.png", "tip": "Eyes", "func": self.callCategory },
                { "button": None, "icon": "eq_eyebrows.png", "tip": "Eyebrows", "func": self.callCategory },
                { "button": None, "icon": "eq_eyelashes.png", "tip": "Eyelashes", "func": self.callCategory },
                { "button": None, "icon": "eq_teeth.png", "tip": "Teeth", "func": self.callCategory },
                { "button": None, "icon": "eq_tongue.png", "tip": "Tongue", "func": self.callCategory },
                { "button": None, "icon": "eq_proxy.png", "tip": "Topology, Proxies", "func": self.callCategory }
            ], [
                { "button": None, "icon": "an_skeleton.png", "tip": "Skeleton", "func": self.callCategory},
                { "button": None, "icon": "an_pose.png", "tip": "Single pose", "func": self.callCategory},
                { "button": None, "icon": "an_movie.png", "tip": "Animation", "func": self.callCategory},
                { "button": None, "icon": "an_expression.png", "tip": "Expressions", "func": self.callCategory},
                { "button": None, "icon": "an_expressedit.png", "tip": "Expression editor", "func": self.callCategory}
            ], [
            ]
        ]

        super().__init__()

        s = env.session["mainwinsize"]
        self.resize (s["w"], s["h"])

        menu_bar = self.menuBar()
        about_menu = menu_bar.addMenu(QIcon(os.path.join(env.path_sysicon, "makehuman.png")), "&About")
        about_act = about_menu.addAction("Info")
        about_act.triggered.connect(self.info_call)

        file_menu = menu_bar.addMenu("&File")
        mem_act = file_menu.addAction("MemInfo")
        mem_act.triggered.connect(self.memory_call)

        load_act = file_menu.addAction("Load Model")
        load_act.triggered.connect(self.loadmhm_call)

        save_act = file_menu.addAction("Save Model")
        save_act.triggered.connect(self.savemhm_call)

        quit_act = file_menu.addAction("Quit")
        quit_act.triggered.connect(self.quit_call)

        set_menu = menu_bar.addMenu("&Settings")
        pref_act = set_menu.addAction("Preferences")
        pref_act.triggered.connect(self.pref_call)

        pref_act = set_menu.addAction("Lights and Scene")
        pref_act.triggered.connect(self.scene_call)

        log_act = set_menu.addAction("Messages")
        log_act.triggered.connect(self.log_call)

        self.deb_act = QAction('Debug Camera', set_menu, checkable=True)
        set_menu.addAction(self.deb_act)
        self.deb_act.triggered.connect(self.deb_cam)

        binaries = set_menu.addMenu("Create Binaries")
        cuserobj_act = binaries.addAction("User 3d Objects")
        cuserobj_act.triggered.connect(self.compress_user3dobjs)

        cusertar_act = binaries.addAction("User Targets")
        cusertar_act.triggered.connect(self.compress_usertargets)

        if env.admin:
            csysobj_act = binaries.addAction("System 3d Objects")
            csysobj_act.triggered.connect(self.compress_sys3dobjs)

            csystar_act = binaries.addAction("System Targets")
            csystar_act.triggered.connect(self.compress_systargets)

        set_menu.addSeparator()
        regenerate = set_menu.addMenu("Regenerate all Binaries")
        ruserobj_act = regenerate.addAction("User 3d Objects")
        ruserobj_act.triggered.connect(self.regenerate_user3dobjs)

        if env.admin:
            rsystar_act = regenerate.addAction("System 3d Objects")
            rsystar_act.triggered.connect(self.regenerate_sys3dobjs)

        tools_menu = menu_bar.addMenu("&Tools")
        base_act = tools_menu.addAction("Change Base")
        base_act.triggered.connect(self.base_call)
        morph_act = tools_menu.addAction("Change Character")
        morph_act.triggered.connect(self.morph_call)

        equip = tools_menu.addMenu("Equipment")

        # TODO: when starting or baseclass changes, what will happen then?!?!
        #
        if self.glob.baseClass is not None:
            for elem in self.equipment:
                elem["func"] = ImageSelection(self, self.glob.baseClass.mhclo_namemap, elem["name"], elem["mode"], self.equipCallback)
                elem["func"].prepare()
                elem["menu"] = equip.addAction(elem["name"])
                elem["menu"].triggered.connect(self.equip_call)

        scanned = self.env.fileScanFolderMHM()
        self.charselect = ImageSelection(self, scanned, "models", 2, self.loadByIconCallback, 3)
        self.charselect.prepare()

        # generate tool buttons, model_buttons (save ressources)
        #
        for elem in (self.tool_buttons, self.model_buttons):
            for n, b in enumerate(elem):
                b["button"] = IconButton(n, os.path.join(self.env.path_sysicon, b["icon"]), b["tip"], b["func"])
        self.markSelectedButtons(self.tool_buttons, self.tool_buttons[0])

        # generate category buttons
        #
        for m, tool in enumerate(self.category_buttons):
            offset = (m + 1) * 100
            for n, b in enumerate(tool):
                b["button"] = IconButton(offset+n, os.path.join(self.env.path_sysicon, b["icon"]), b["tip"], b["func"])
        self.markSelectedButtons(self.category_buttons[0], self.category_buttons[0][0])

        self.createCentralWidget()
        self.setWindowTitle("default character")

    def updateScene(self):
        if self.scene_window:
            self.scene_window.destroy()
            del self.scene_window
            self.scene_window = None
            #self.scene_window.newView(self.graph.view)
            #print ("Scene Window open")

    def setWindowTitle(self, text):
        title = self.env.release_info["name"] + " (" + text + ")"
        super().setWindowTitle(title)


    def equipCallback(self, asset, eqtype, multi):
        if asset.status == 0:
            self.glob.baseClass.delAsset(asset.filename)
        elif asset.status == 1:
            self.glob.baseClass.addAndDisplayAsset(asset.filename, eqtype, multi)


    def fileRequest(self, ftext, pattern, directory, save=None):
        """
        Simplified file request
        """
        dialog = QFileDialog()
        dialog.setNameFilter(pattern)
        dialog.setDirectory(directory)
        if save is None:
            dialog.setWindowTitle("Load " + str(ftext) + " file")
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            dialog.setAcceptMode(QFileDialog.AcceptOpen)
        else:
            dialog.setWindowTitle("Save " + str(ftext) + " file")
            dialog.setFileMode(QFileDialog.FileMode.AnyFile)
            dialog.setAcceptMode(QFileDialog.AcceptSave)
        success = dialog.exec()
        if success:
            filename = dialog.selectedFiles()[0]

            if save is not None:
                # add suffix for save (security check for overwriting is done by request)
                #
                if not filename.endswith(save):
                    filename += save
            return(filename)
        return (None)


    def buttonRow(self, subtool):
        if len(subtool) == 0:
            return (None)
        row=QHBoxLayout()
        for n, b in enumerate(subtool):
            row.addWidget(b["button"])
        row.addStretch()
        return(row)

    def markSelectedButtons(self, row, button):
        sel = button["button"]
        for elem in row:
            b = elem["button"]
            b.setChecked(b == sel)

    def setCategoryIcons(self):
        s = self.sender()
        self.setToolModeAndPanel(s._funcid, 0)

    def callCategory(self):
        s = self.sender()
        m = s._funcid -100
        self.setToolModeAndPanel(m // 100, m % 100)

    def createCentralWidget(self):
        """
        create central widget, shown by default or by using connect/disconnect button from graphics window
        """
        env = self.env
        self.central_widget = QWidget()

        hLayout = QHBoxLayout()         # 3 columns

        # left side, first button box, then base panel
        #
        self.ButtonBox = QVBoxLayout()

        row = self.buttonRow(self.tool_buttons)
        self.ButtonBox.addLayout(row)

        self.CategoryBox= self.buttonRow(self.category_buttons[0])
        self.ButtonBox.addLayout(self.CategoryBox)

        self.leftColumn = QGroupBox()
        self.leftColumn.setMinimumWidth(300)
        self.BaseBox = QVBoxLayout()

        self.drawLeftPanel()
        self.leftColumn.setMaximumWidth(400)
        self.leftColumn.setLayout(self.BaseBox)
        self.ButtonBox.addWidget(self.leftColumn)
        hLayout.addLayout(self.ButtonBox)

        # create window for internal or external use
        #
        self.graph = MHGraphicWindow(self, self.glob)

        gLayout = self.graph.createLayout()
        #
        # keyboard
        #
        self.eventFilter = NavigationEvent(self.graph)
        self.installEventFilter(self.eventFilter)

        # in case of being attached, add external window in layout
        #
        if self.env.g_attach is True:
            groupBoxG = QGroupBox("Viewport")
            groupBoxG.setLayout(gLayout)
            hLayout.addWidget(groupBoxG)

        # right side, ToolBox
        #
        self.rightColumn = QGroupBox("Toolpanel")
        self.ToolBox = QVBoxLayout()

        self.drawRightPanel()
        self.rightColumn.setMinimumWidth(500)
        self.rightColumn.setMaximumWidth(500)
        self.rightColumn.setLayout(self.ToolBox)
        hLayout.addWidget(self.rightColumn)

        #
        self.central_widget.setLayout(hLayout)
        self.setCentralWidget(self.central_widget)


    def drawLeftPanel(self):
        """
        draw left panel
        """
        env = self.env

        # extra code for no basemesh selected
        #
        if (self.tool_mode == 0 and self.category_mode == 0) or env.basename is None:
            self.leftColumn.setTitle("Base mesh :: selection")
            self.baseSelector = BaseSelect(self.glob, self.selectmesh_call)
            self.BaseBox.addLayout(self.baseSelector)
            self.BaseBox.addStretch()
            return
        
        if self.tool_mode == 0:
            if self.category_mode == 1:
                self.leftColumn.setTitle("Load file :: filter")
                layout = self.charselect.leftPanel()
                self.BaseBox.addLayout(layout)
            elif self.category_mode == 2:
                self.leftColumn.setTitle("Save file :: additional parameters")
                self.saveForm = SaveMHMForm(self.glob, self.graph.view, self.setWindowTitle)
                self.BaseBox.addLayout(self.saveForm)
            elif self.category_mode == 4:
                self.leftColumn.setTitle("Import file :: additional parameters")
                dlform = DownLoadImport(self, self.graph.view, self.setWindowTitle)
                self.BaseBox.addLayout(dlform)
            self.BaseBox.addStretch()
            return

        
        if self.tool_mode == 1:
            if self.glob.targetCategories is not None:
                self.leftColumn.setTitle("Modify character :: categories")
                self.qTree = MHTreeView(self.glob.targetCategories, "Modelling", self.redrawNewCategory, None)
                self.targetfilter = self.qTree.getStartPattern()
                self.BaseBox.addWidget(self.qTree)
                row = self.buttonRow(self.model_buttons)
                self.BaseBox.addLayout(row)
            else:
                self.env.logLine(1, self.env.last_error )
        elif self.tool_mode == 2:
            self.leftColumn.setTitle("Character equipment :: filter")
            layout = self.equipment[self.category_mode]["func"].leftPanel()
            self.BaseBox.addLayout(layout)
        self.BaseBox.addStretch()


    def drawMorphPanel(self, text=""):
        self.rightColumn.setTitle("Modify character, category: " + text)
        if self.glob.Targets is not None:
            widget = QWidget()
            sweep = os.path.join(self.glob.env.path_sysicon, "sweep.png")
            self.scalerArray = ScaleComboArray(widget, self.glob.Targets.modelling_targets, self.targetfilter, sweep)
            widget.setLayout(self.scalerArray.layout)
            scrollArea = QScrollArea()
            scrollArea.setWidget(widget)
            scrollArea.setWidgetResizable(True)

            self.ToolBox.addWidget(scrollArea)

    def drawCharSelectPanel(self):
        self.rightColumn.setTitle("Files")
        widget = QWidget()
        picwidget = self.charselect.rightPanel()
        widget.setLayout(picwidget.layout)
        scrollArea = QScrollArea()
        scrollArea.setWidget(widget)
        scrollArea.setWidgetResizable(True)
        scrollArea.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        self.ToolBox.addWidget(scrollArea)

    def drawEquipPanel(self, category, text):
        self.rightColumn.setTitle("Character equipment, category: " + text)
        widget = QWidget()
        picwidget = category.rightPanel()
        widget.setLayout(picwidget.layout)
        scrollArea = QScrollArea()
        scrollArea.setWidget(widget)
        scrollArea.setWidgetResizable(True)
        scrollArea.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        self.ToolBox.addWidget(scrollArea)

    def drawRightPanel(self, text="None"):
        #
        # works according to tool_mode and category_mode
        #
        print (self.tool_mode, self.category_mode)
        if self.tool_mode == 0:
            if self.category_mode == 1:
                self.drawCharSelectPanel()
        elif self.tool_mode == 1:
            self.drawMorphPanel(text)
        elif self.tool_mode == 2:
            equip = self.equipment[self.category_mode]
            self.drawEquipPanel(equip["func"], equip["name"])


    def emptyLayout(self, layout):
        if layout is not None:
            #print("-- -- input layout: "+str(layout))
            for i in reversed(range(layout.count())):
                layoutItem = layout.itemAt(i)
                if layoutItem.widget() is not None:
                    widgetToRemove = layoutItem.widget()
                    widgetToRemove.setParent(None)
                    layout.removeWidget(widgetToRemove)
                    #print("found widget: " + str(widgetToRemove))
                elif layoutItem.spacerItem() is not None:
                    layout.removeItem(layoutItem)
                else:
                    layoutToRemove = layout.itemAt(i)
                    self.emptyLayout(layoutToRemove)

    def setToolModeAndPanel(self, tool, category):
        if self.tool_mode != tool or self.category_mode != category:
            self.emptyLayout(self.BaseBox)
            self.emptyLayout(self.ToolBox)
            self.emptyLayout(self.CategoryBox)
            self.tool_mode = tool
            self.category_mode = category
            self.markSelectedButtons(self.tool_buttons, self.tool_buttons[tool])
            buttons = self.category_buttons[tool]
            self.CategoryBox= self.buttonRow(buttons)
            if self.CategoryBox is not None:
                self.ButtonBox.insertLayout(1, self.CategoryBox)
                self.markSelectedButtons(buttons, buttons[category])
            self.drawLeftPanel()
            self.drawRightPanel()

    def show(self):
        """
        also shows graphic screen
        """
        self.graph.show()
        super().show()

    def deb_cam(self):
        self.graph.setDebug(self.deb_act.isChecked())

    def closeEvent(self, event):
        self.quit_call(event)

    def base_call(self):
        self.setToolModeAndPanel(0, 0)

    def morph_call(self):
        self.setToolModeAndPanel(1, 0)

    def equip_call(self):
        s = self.sender()
        for n, elem in enumerate(self.equipment):
            if elem["menu"] == s:
                self.setToolModeAndPanel(2, n)
                break

    def pref_call(self):
        """
        show preferences window
        """
        if self.pref_window is None:
            self.pref_window = MHPrefWindow(self)
        self.pref_window.show()

    def log_call(self):
        """
        show logfiles window
        """
        if self.log_window is None:
            self.log_window = MHLogWindow(self)
        self.log_window.show()

    def memory_call(self):
        """
        show memory window
        """
        if self.mem_window is None:
            self.mem_window = MHMemWindow(self)
        self.mem_window.show()

    def scene_call(self):
        """
        show scene window
        """
        if self.scene_window is None:
            self.scene_window = MHSceneWindow(self, self.graph.view)
        self.scene_window.show()

    def changesLost(self, text):
        confirmed = 1
        if self.glob.project_changed:
            dbox = DialogBox(text + ": all recent changes will be lost.\nPress cancel to abort", QDialogButtonBox.Ok)
            confirmed = dbox.exec()
        return(confirmed)

    def parallelLoad(self, bckproc, *args):
        self.glob.baseClass.loadMHMFile(args[0][0])

    def finishLoad(self):
        self.graph.view.addAssets()
        self.graph.view.newTexture(self.glob.baseClass.baseMesh)
        self.graph.view.Tweak()
        self.setWindowTitle(self.glob.baseClass.name)
        self.glob.mhViewport.setSizeInfo()
        self.glob.parallel = None

    def newCharacter(self, filename):
        if filename is not None and self.glob.parallel is None:
            self.setToolModeAndPanel(0, 0)
            self.graph.view.noAssets()
            self.glob.freeTextures()
            self.glob.parallel = WorkerThread(self.parallelLoad, filename)
            self.glob.parallel.start()
            self.glob.parallel.finished.connect(self.finishLoad)
        self.glob.project_changed = False

    def loadmhm_call(self):
        if self.glob.baseClass is not None:
            if self.changesLost("Load character"):
                directory = self.env.stdUserPath("models")
                filename = self.fileRequest("Model", "Model files (*.mhm)", directory)
                self.newCharacter(filename)

    def loadByIconCallback(self, asset, eqtype, multi):
        if asset.status != 1:
            return
        if self.changesLost("Load character"):
            self.newCharacter(asset.filename)

    def savemhm_call(self):
        if self.glob.baseClass is not None:
            directory = self.env.stdUserPath("models")
            filename = self.fileRequest("Model", "Model files (*.mhm)", directory, save=".mhm")
            if filename is not None:
                self.glob.baseClass.saveMHMFile(filename)

    def initParams(self):
        self.graph.getFocusText()

    def info_call(self):
        """
        show about/information window
        """
        if self.info_window is None:
            self.info_window = MHInfoWindow(self.glob)
        self.info_window.show()

    def reset_call(self):
        if self.glob.Targets is not None:
            if self.changesLost("Reset character"):
                print ("Reset")
                self.glob.Targets.reset()
                self.glob.project_changed = False
                self.redrawNewCategory(self.targetfilter)
                self.glob.baseClass.applyAllTargets()
                self.graph.setSizeInfo()
                self.graph.view.Tweak()

    def symSwitch(self):
        self.scalerArray.comboUnexpand()
        v = not self.glob.Targets.getSym()
        self.glob.Targets.setSym(v)
        self.sender().setChecked(v)

    def symLToR(self):
        self.glob.Targets.makeSym(False)
        self.glob.baseClass.parApplyTargets()
        #self.graph.view.Tweak()

    def symRToL(self):
        self.glob.Targets.makeSym(True)
        self.glob.baseClass.parApplyTargets()
        #self.graph.view.Tweak()

    def selectmesh_call(self):
        (base, filename) = self.baseSelector.getSelectedItem()
        if base is not None:
            #
            if base == self.env.basename:
                return
            if self.changesLost("New basemesh") == 0:
                return
            dirname = os.path.dirname(filename)
            base = baseClass(self.glob, base, dirname)
            okay = base.prepareClass()
            if not okay:
                ErrorBox(self.central_widget, self.env.last_error)
                return

            self.graph.view.newMesh()
            self.emptyLayout(self.ToolBox)
            self.drawRightPanel()
            self.ToolBox.update()

            self.emptyLayout(self.BaseBox)
            self.drawLeftPanel()
            self.BaseBox.update()
            self.graph.setSizeInfo()

            self.graph.update()

    def redrawNewCategory(self, category, text=None):
        print (category)
        if text is None:
            text =self.qTree.getLastHeadline()
        self.emptyLayout(self.ToolBox)
        self.targetfilter = category
        self.drawMorphPanel(text)
        self.ToolBox.update()

    def finished_bckproc(self):
        if self.prog_window is not None:
            self.prog_window.progress.close()
            self.prog_window = None
        QMessageBox.information(self, "Done!", self.bckproc.finishmsg)
        self.bckproc = None

    def compress_systargets(self):
        if self.glob.Targets is not None and self.bckproc is None:
            self.prog_window = MHBusyWindow("System targets", "compressing ...")
            self.prog_window.progress.forceShow()
            self.bckproc = WorkerThread(self.glob.Targets.saveBinaryTargets, 1)
            self.bckproc.finishmsg = "System targets had been compressed"
            self.bckproc.start()
            self.bckproc.finished.connect(self.finished_bckproc)

    def compress_usertargets(self):
        if self.glob.Targets is not None and self.bckproc is None:
            self.prog_window = MHBusyWindow("User targets", "compressing ...")
            self.prog_window.progress.forceShow()
            self.bckproc = WorkerThread(self.glob.Targets.saveBinaryTargets, 2)
            self.bckproc.finishmsg = "User targets had been compressed"
            self.bckproc.start()
            self.bckproc.finished.connect(self.finished_bckproc)

    def compressObjs(self, bckproc, *args):
        """
        compresses assets (atm obj files)
        :param bck_proc: unused pointer to background process
        :param args: [0][0] True = system, False user
        """
        system = args[0][0]
        force = args[0][1]
        bc = self.glob.baseClass
        if system:
            (okay, err) = bc.baseMesh.exportBin()
            if not okay:
                bckproc.finishmsg = err
                return

        elems_compressed = 0
        elems_untouched = 0
        for elem in bc.mhclo_namemap:
            syspath = elem.path.startswith(self.env.path_sysdata)
            if syspath == system:
                okay = False
                if force or self.env.isSourceFileNewer(elem.npz_file, elem.obj_file):
                    self.prog_window.setLabelText(elem.folder + ": create binary " + os.path.split(elem.path)[1])
                    (attach, err) = bc.loadMHCLO(elem.path, elem.folder)
                    if attach is not None:
                        (okay, err) =attach.obj.exportBin()
                    if not okay:
                        bckproc.finishmsg = err
                        return
                    elems_compressed += 1
                else:
                    elems_untouched += 1

        bckproc.finishmsg = "Binaries created: " + str(elems_compressed) + "\nEntries up-to-date before: " + str(elems_untouched)
        return

    def compressObjsWorker(self, system, force):
        if self.glob.baseClass is not None and self.bckproc is None:
            objects = "System Objects" if system else "User Objects"
            self.prog_window = MHBusyWindow(objects, "creating binaries ...")
            self.prog_window.progress.forceShow()
            self.bckproc = WorkerThread(self.compressObjs, system, force)
            self.bckproc.start()
            self.bckproc.finished.connect(self.finished_bckproc)

    def compress_sys3dobjs(self):
        self.compressObjsWorker(True, False)

    def compress_user3dobjs(self):
        self.compressObjsWorker(False, False)

    def regenerate_sys3dobjs(self):
        self.compressObjsWorker(True, True)

    def regenerate_user3dobjs(self):
        self.compressObjsWorker(False, True)

    def quit_call(self, event=None):
        """
        save session (if desired)
        also make a check, when project was changed
        """
        if self.in_close is True:
            return

        if self.graph is not None:
            self.graph.cleanUp()

        confirmed =  self.changesLost("Exit program")
        if confirmed == 0:
            if isinstance(event,QCloseEvent):
                event.ignore()
                print ("Close event")
            return

        self.glob.freeTextures()
        if self.in_close is False:
            self.in_close = True                # avoid double call by closeAllWindows
            s = self.env.session["mainwinsize"]
            s["w"] = self.width()
            s["h"] = self.height()
            self.env.saveSession()
            self.env.cleanup()
            self.glob.app.closeAllWindows()
            self.glob.app.quit()
