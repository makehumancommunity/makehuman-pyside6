from PySide6.QtWidgets import ( 
        QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QGroupBox, QListWidget, QLabel,
        QAbstractItemView, QSizePolicy, QScrollArea, QDialogButtonBox, QMessageBox
        )
from PySide6.QtGui import QIcon, QCloseEvent, QAction, QDesktopServices
from PySide6.QtCore import QSize, Qt, QUrl
from gui.prefwindow import  MHPrefWindow
from gui.logwindow import  MHLogWindow
from gui.infowindow import  MHInfoWindow
from gui.memwindow import  MHMemWindow
from gui.scenewindow import  MHSceneWindow
from gui.graphwindow import  MHGraphicWindow, NavigationEvent
from gui.fileactions import BaseSelect, SaveMHMForm, DownLoadImport, ExportLeftPanel, ExportRightPanel
from gui.poseactions import AnimPlayer, AnimMode, AnimExpressionEdit
from gui.slider import ScaleComboArray
from gui.imageselector import ImageSelection
from gui.renderer import Renderer
from gui.common import DialogBox, ErrorBox, WorkerThread, MHBusyWindow, MHGroupBox, IconButton, TextBox, MHFileRequest
from gui.qtreeselect import MHTreeView
from core.baseobj import baseClass
from core.attached_asset import attachedAsset
from opengl.info import GLDebug

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
        self.material_editor = None
        self.asset_window = None
        self.info_window = None
        self.log_window = None
        self.prog_window = None     # will hold the progress bar

        self.leftColumn = None
        self.LeftBox = None         # layouts to fill
        self.lastClass = None       # needed for close functions

        self.rightColumn = None
        self.ToolBox = None

        self.graph = None
        self.qTree = None

        self.ButtonBox = None
        self.CategoryBox = None
        self.baseSelector = None

        self.in_close = False
        self.targetfilter = None
        self.expressionfilter = None
        self.bckproc = None         # background process is running

        self.tool_mode = 0          # 0 = files, 1 = modelling, 2 = equipment, 3 = pose, 4 = render, 10 = help
        self.category_mode = 0      # the categories according to tool_mode

        self.equipment = [
                { "func": None, "menu": None, "name": "clothes", "mode": 1 },
                { "func": None, "menu": None, "name": "hair", "mode": 0 },
                { "func": None, "menu": None, "name": "eyes", "mode": 0 },
                { "func": None, "menu": None, "name": "eyebrows", "mode": 0 },
                { "func": None, "menu": None, "name": "eyelashes", "mode": 0 },
                { "func": None, "menu": None, "name": "teeth", "mode": 0 },
                { "func": None, "menu": None, "name": "tongue", "mode": 0 },
                { "func": None, "menu": None, "name": "proxy", "mode": 0 }
        ]
        self.animation = [
                { "func": None, "menu": None, "name": "rigs", "mode": 0 },
                { "func": None, "menu": None, "name": "poses", "mode": 0 },
                { "func": None, "menu": None, "name": "animation", "mode": 0 },
                { "func": None, "menu": None, "name": "expressions", "mode": 0 },
                { "func": None, "menu": None, "name": "expression editor", "mode": 0 }
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

        set_menu.addSeparator()
        exportuserdb = set_menu.addAction("Backup User Database")
        exportuserdb.triggered.connect(self.exportUserDB)

        importuserdb = set_menu.addAction("Restore User Database")
        importuserdb.triggered.connect(self.importUserDB)

        tools_menu = menu_bar.addMenu("&Tools")
        base_act = tools_menu.addAction("Change Base")
        base_act.triggered.connect(self.base_call)
        morph_act = tools_menu.addAction("Change Character")
        morph_act.triggered.connect(self.morph_call)

        self.equip = tools_menu.addMenu("Equipment")
        self.animenu = tools_menu.addMenu("Animation")

        help_menu = menu_bar.addMenu("&Help")
        entry = help_menu.addAction("Local OpenGL Information")
        entry.triggered.connect(self.glinfo_call)

        entry = help_menu.addAction("License")
        entry.triggered.connect(self.lic_call)
        lics = help_menu.addMenu("3rd Party licenses")
        for elem in ["PySide6", "PyOpenGL", "NumPy"]:
            entry = lics.addAction(elem)
            entry.triggered.connect(self.lic_call)

        entry = help_menu.addAction("Credits")
        entry.triggered.connect(self.lic_call)

        if "support_urls" in self.env.release_info:
            for elem in self.env.release_info["support_urls"]:
                urlname = self.env.release_info["support_urls"][elem]
                if urlname in self.env.release_info:
                    entry = help_menu.addAction(elem)
                    entry.triggered.connect(self.help_call)

        if self.glob.baseClass is not None:
            self.createImageSelection()

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

    def createImageSelection(self):
        for elem in self.equipment:
            elem["func"] = ImageSelection(self, self.glob.cachedInfo, elem["name"], elem["mode"], self.equipCallback)
            elem["func"].prepare()
            elem["menu"] = self.equip.addAction(elem["name"])
            elem["menu"].triggered.connect(self.equip_call)

        self.charselect = ImageSelection(self, self.glob.cachedInfo, "models", 0, self.loadByIconCallback, 3)
        self.charselect.prepare()

        for elem in self.animation:
            elem["func"] = ImageSelection(self, self.glob.cachedInfo, elem["name"], elem["mode"], self.animCallback)
            elem["func"].prepare()
            elem["menu"] = self.animenu.addAction(elem["name"])
            elem["menu"].triggered.connect(self.anim_call)

    def setWindowTitle(self, text):
        title = self.env.release_info["name"] + " (" + text + ")"
        super().setWindowTitle(title)


    def equipCallback(self, selected, eqtype, multi):
        self.glob.project_changed = True
        if isinstance(selected, str):
            self.glob.baseClass.delAsset(selected)
            return
        if selected.status == 0:
            self.glob.baseClass.delAsset(selected.filename)
        elif selected.status == 1:
            self.glob.baseClass.addAndDisplayAsset(selected.filename, eqtype, multi)

    def animCallback(self, selected, eqtype, multi):
        self.glob.project_changed = True
        if eqtype == "rigs":
            if selected.status == 0:
                self.glob.baseClass.delSkeleton(selected.filename)
            else:
                self.glob.baseClass.addSkeleton(selected.name, selected.filename)
        elif eqtype == "poses":
            if selected.status == 0:
                self.glob.baseClass.delPose(selected.filename)
            else:
                if not self.glob.baseClass.addPose(selected.name, selected.filename):
                    ErrorBox(self.central_widget, self.env.last_error)
            self.graph.view.Tweak()
        elif eqtype == "expressions":
            if selected.status == 0:
                self.glob.baseClass.delExpression(selected.filename)
            else:
                self.glob.baseClass.addExpression(selected.name, selected.filename)
            self.graph.view.Tweak()

    def buttonRow(self, subtool):
        if len(subtool) == 0:
            return (None)

        row=QHBoxLayout()
        row.setSpacing(2)
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
        create central widget containing 3 columns
        """
        env = self.env
        self.central_widget = QWidget()
        self.glob.centralWidget = self.central_widget

        hLayout = QHBoxLayout()         # 3 columns
        hLayout.setSpacing(2)
        hLayout.setContentsMargins(2, 3, 2, 3)

        # left side, first button box
        #
        b2group  = QFrame()
        b2group.setObjectName("gboxnontitle")
        b2group.setMaximumWidth(400)

        self.ButtonBox = QVBoxLayout()
        row = self.buttonRow(self.tool_buttons)
        self.ButtonBox.addLayout(row)

        self.CategoryBox= self.buttonRow(self.category_buttons[0])
        self.ButtonBox.addLayout(self.CategoryBox)

        b2group.setLayout(self.ButtonBox)

        # left side base panel
        #
        self.LeftBox = QVBoxLayout()
        self.leftColumn = MHGroupBox("Base")
        self.leftColumn.setMinimumWidth(300)
        self.leftColumn.setMaximumWidth(400)
        self.drawLeftPanel()

        v2Layout = QVBoxLayout()
        v2Layout.addWidget(b2group)
        v2Layout.addLayout(self.leftColumn.MHLayout(self.LeftBox),1)

        hLayout.addLayout(v2Layout)

        # create window for internal or external use
        #
        self.glob.midColumn = self.graph = MHGraphicWindow(self.glob)
        gLayout = self.graph.createLayout()
        #
        # keyboard
        #
        self.eventFilter = NavigationEvent(self.graph)
        self.installEventFilter(self.eventFilter)

        # add view in layout
        #
        frame = MHGroupBox("Viewport")
        hLayout.addLayout(frame.MHLayout(gLayout),3)

        # right side, ToolBox
        #
        self.ToolBox = QVBoxLayout()
        self.drawRightPanel()
        self.rightColumn = MHGroupBox("No additional infomation")
        self.rightColumn.setMinimumWidth(300)
        hLayout.addLayout(self.rightColumn.MHLayout(self.ToolBox), 2)

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
            self.baseSelector = BaseSelect(self, self.selectmesh_call)
            self.LeftBox.addLayout(self.baseSelector)
            self.LeftBox.addStretch()
            return

        if self.tool_mode == 0:
            if self.category_mode == 1:
                self.leftColumn.setTitle("Load file :: filter")
                layout = self.charselect.leftPanel()
                self.LeftBox.addLayout(layout)
            elif self.category_mode == 2:
                self.leftColumn.setTitle("Save file :: parameters")
                self.saveForm = SaveMHMForm(self, self.graph.view, self.charselect, self.setWindowTitle)
                self.LeftBox.addLayout(self.saveForm)
            elif self.category_mode == 3:
                self.leftColumn.setTitle("Export file :: parameters")
                self.exportForm = ExportLeftPanel(self)
                self.LeftBox.addLayout(self.exportForm)
            elif self.category_mode == 4:
                self.leftColumn.setTitle("Import file :: parameters")
                dlform = DownLoadImport(self, self.graph.view, self.setWindowTitle)
                self.LeftBox.addLayout(dlform)
            self.LeftBox.addStretch()
            return

        
        if self.tool_mode == 1:
            if self.glob.targetCategories is not None:
                self.leftColumn.setTitle("Modify character :: categories")
                self.qTree = MHTreeView(self.glob.targetCategories, "Modelling", self.redrawNewCategory, None)
                self.targetfilter = self.qTree.getStartPattern()
                self.LeftBox.addWidget(self.qTree)
                row = self.buttonRow(self.model_buttons)
                self.LeftBox.addLayout(row)
            else:
                self.env.logLine(1, self.env.last_error )

        elif self.tool_mode == 2:
            self.leftColumn.setTitle("Character equipment :: filter")
            layout = self.equipment[self.category_mode]["func"].leftPanel()
            self.LeftBox.addLayout(layout)

        elif self.tool_mode == 3:
            if self.category_mode == 0:
                self.leftColumn.setTitle("Rigs :: filter")
                layout = self.animation[self.category_mode]["func"].leftPanel()
                self.LeftBox.addLayout(layout)
            elif self.category_mode == 1:
                self.leftColumn.setTitle("Poses :: filter")
                self.lastClass = AnimMode(self.glob, self.graph.view)
                layout = self.animation[self.category_mode]["func"].leftPanel()
                self.LeftBox.addLayout(layout)
            elif self.category_mode == 2:
                self.leftColumn.setTitle("Animation Player")
                self.lastClass = AnimPlayer(self.glob, self.graph.view)
                self.lastClass.enter()
                self.LeftBox.addLayout(self.lastClass)
                self.LeftBox.addStretch()
            elif self.category_mode == 3:
                self.leftColumn.setTitle("Expressions :: filter")
                self.lastClass = AnimMode(self.glob, self.graph.view)
                layout = self.animation[self.category_mode]["func"].leftPanel()
                self.LeftBox.addLayout(layout)
            else:
                self.leftColumn.setTitle("Expressions :: editor")
                self.lastClass = AnimExpressionEdit(self, self.glob, self.graph.view)
                filterparam = self.glob.baseClass.getFaceUnits().createFilterDict()
                self.qTree = MHTreeView(filterparam, "Expressions", self.redrawNewExpression, None)
                self.expressionfilter = self.qTree.getStartPattern()
                self.LeftBox.addWidget(self.qTree)
                layout = self.lastClass.addClassWidgets()
                self.LeftBox.addLayout(layout)

        elif self.tool_mode == 4:
            self.leftColumn.setTitle("Rendering :: parameters")
            self.lastClass = Renderer(self, self.glob, self.graph.view)
            self.lastClass.enter()
            self.LeftBox.addLayout(self.lastClass)
            self.LeftBox.addStretch()
        else:
            self.leftColumn.setTitle("Not yet implemented")


    def drawExpressionPanel(self, text=""):
        self.rightColumn.setTitle("Expressions, category: " + text)
        widget = QWidget()
        sweep = os.path.join(self.glob.env.path_sysicon, "sweep.png")
        expressions = self.lastClass.fillExpressions()
        self.exprArray = ScaleComboArray(widget, expressions, self.expressionfilter, sweep)
        widget.setLayout(self.exprArray.layout)
        scrollArea = QScrollArea()
        scrollArea.setWidget(widget)
        scrollArea.setWidgetResizable(True)
        self.ToolBox.addWidget(scrollArea)

    def drawMorphPanel(self, text=""):
        self.rightColumn.setTitle("Morph, category: " + text)
        if self.glob.Targets is not None:
            widget = QWidget()
            sweep = os.path.join(self.glob.env.path_sysicon, "sweep.png")
            self.scalerArray = ScaleComboArray(widget, self.glob.Targets.modelling_targets, self.targetfilter, sweep)
            widget.setLayout(self.scalerArray.layout)
            scrollArea = QScrollArea()
            scrollArea.setWidget(widget)
            scrollArea.setWidgetResizable(True)
            self.ToolBox.addWidget(scrollArea)

    def drawImageSelector(self, category, text, buttonmask=3):
        self.rightColumn.setTitle(text)
        layout = category.rightPanel(buttonmask)
        self.ToolBox.addLayout(layout)

    def drawExportPanel(self, connector, text):
        self.rightColumn.setTitle(text)
        layout = ExportRightPanel(self, connector)
        self.ToolBox.addLayout(layout)

    def drawRightPanel(self, text="None"):
        #
        # works according to tool_mode and category_mode
        #
        print (self.tool_mode, self.category_mode)
        if self.glob.baseClass is None:
            return
        if self.tool_mode == 0:
            if self.category_mode == 0:
                if self.rightColumn is None:
                    return
                self.rightColumn.setTitle("No additional infomation")
            elif self.category_mode == 1:
                self.drawImageSelector(self.charselect, "Character MHM Files", 4)
            elif self.category_mode == 2:
                self.drawImageSelector(self.charselect, "Character MHM Files (select to get data)", 0)
            elif self.category_mode == 3:
                self.drawExportPanel(self.exportForm, "Export character")
            elif self.category_mode == 4:
                self.rightColumn.setTitle("No additional infomation")
            else:
                self.rightColumn.setTitle("Not yet implemented")
        elif self.tool_mode == 1:
            self.drawMorphPanel(text)
        elif self.tool_mode == 2:
            equip = self.equipment[self.category_mode]
            text = "Equipment, category: " + equip["name"]
            self.drawImageSelector(equip["func"], text, 15)
        elif self.tool_mode == 3:
            if self.category_mode == 0 or self.category_mode == 1 or self.category_mode == 3:
                equip = self.animation[self.category_mode]
                text = "Pose and animation, category: " + equip["name"]
                self.drawImageSelector(equip["func"], text, 13)
            elif self.category_mode == 4:
                self.drawExpressionPanel(text)
            else:
                self.rightColumn.setTitle("Not yet implemented")
        else:
            self.rightColumn.setTitle("Not yet implemented")


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
            if self.lastClass is not None:
                self.lastClass.leave()
                self.lastClass = None
            self.emptyLayout(self.LeftBox)
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

    def anim_call(self):
        s = self.sender()
        for n, elem in enumerate(self.animation):
            if elem["menu"] == s:
                self.setToolModeAndPanel(3, n)
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
        self.glob.baseClass.loadMHMFile(args[0][0], self.prog_window)
        # self.prog_window.setLabelText(elem.folder + ": create binary " + os.path.split(elem.path)[1])

    def finishLoad(self):
        self.graph.view.setCameraCenter()
        self.graph.view.addAssets()
        self.graph.view.newSkin(self.glob.baseClass.baseMesh)
        self.graph.view.addSkeleton()
        if self.prog_window is not None:
            self.prog_window.progress.close()
            self.prog_window = None
        self.glob.openGLBlock = False
        self.graph.view.Tweak()
        self.setWindowTitle(self.glob.baseClass.name)
        self.graph.setSizeInfo()
        self.glob.parallel = None

    def newCharacter(self, filename):
        if filename is not None and self.glob.parallel is None:
            self.setToolModeAndPanel(0, 0)
            self.glob.openGLBlock = True
            self.graph.view.noGLObjects(leavebase=True)
            self.glob.freeTextures()
            self.glob.baseClass.reset()
            self.prog_window = MHBusyWindow("Load character", "start")
            self.prog_window.progress.forceShow()
            self.glob.parallel = WorkerThread(self.parallelLoad, filename)
            self.glob.parallel.start()
            self.glob.parallel.finished.connect(self.finishLoad)
        self.glob.project_changed = False

    def loadmhm_call(self):
        if self.glob.baseClass is not None:
            self.setToolModeAndPanel(0, 1)

    def loadByIconCallback(self, asset, eqtype, multi):

        # in case of save add data into formular only
        #
        if self.category_mode == 2:
            self.saveForm.addDataFromSelected(asset)
            return

        if asset.status != 1:
            return
        if self.changesLost("Load character"):
            self.newCharacter(asset.filename)

    def savemhm_call(self):
        if self.glob.baseClass is not None:
            self.setToolModeAndPanel(0, 2)

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
                self.glob.Targets.reset(True)
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

    def loadNewClass(self, basename, filename=None):
        print (basename, filename)
        if filename is None:
            dirname  = self.env.existDataDir("base", basename)
        else:
            dirname = os.path.dirname(filename)

        base = baseClass(self.glob, basename, dirname)
        okay = base.prepareClass()
        if not okay:
            ErrorBox(self.central_widget, self.env.last_error)
            return

        self.glob.openGLBlock = True
        self.graph.view.newMesh()
        self.createImageSelection()
        self.emptyLayout(self.ToolBox)
        self.drawRightPanel()
        self.ToolBox.update()

        self.emptyLayout(self.LeftBox)
        self.drawLeftPanel()
        self.LeftBox.update()
        self.graph.setSizeInfo()

        self.graph.update()
        self.glob.openGLBlock = False

    def selectmesh_call(self):
        (base, filename) = self.baseSelector.getSelectedItem()
        if base is not None:
            #
            if base == self.env.basename:
                return
            if self.changesLost("New basemesh") == 0:
                return
            self.loadNewClass(base, filename)

    def redrawNewCategory(self, category, text=None):
        print (category)
        if text is None:
            text =self.qTree.getLastHeadline()
        self.emptyLayout(self.ToolBox)
        self.targetfilter = category
        self.drawMorphPanel(text)
        self.ToolBox.update()

    def redrawNewExpression(self, category, text=None):
        print (category)
        if category is None:
            category =self.qTree.getLastCategory()
        if text is None:
            text =self.qTree.getLastHeadline()
        self.emptyLayout(self.ToolBox)
        self.expressionfilter = category
        self.drawExpressionPanel(text)
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
        compresses assets (either objects or mhclo)
        :param bck_proc: unused pointer to background process
        :param args: [0][0] True = system, False user
        """
        system = args[0][0]
        force = args[0][1]
        bc = self.glob.baseClass

        # first compress base itself
        #
        syspath =  bc.baseMesh.filename.startswith(self.env.path_sysdata)
        if syspath == system:
            (okay, err) = bc.baseMesh.exportBinary()
            if not okay:
                bckproc.finishmsg = err
                return

        elems_compressed = 0
        elems_untouched = 0
        for elem in self.glob.cachedInfo:

            if elem.folder in ["clothes", "eyebrows", "eyelashes", "eyes", "hair", "proxy", "teeth", "tongue"]:
                syspath = elem.path.startswith(self.env.path_sysdata)
                if syspath == system:
                    okay = False
                    if force or self.env.isSourceFileNewer(elem.mhbin_file, elem.path):
                        self.prog_window.setLabelText(elem.folder + ": create binary " + os.path.split(elem.path)[1])

                        attach = attachedAsset(self.glob, elem.folder)
                        (okay, err) = attach.mhcloToMHBin(elem.path)
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

    def exportUserDB(self):
        if self.glob.baseClass is None:
            return
        directory = self.env.stdUserPath()
        freq = MHFileRequest("Database export for backup", "Json-files (*.json)", directory, save=".json")
        filename = freq.request()
        if filename is not None:
            if self.env.fileCache.exportUserInfo(filename):
                QMessageBox.information(self.central_widget, "Done!", "User database exported as " + filename)
            else:
                ErrorBox(self.central_widget, self.env.last_error)

    def importUserDB(self):
        if self.glob.baseClass is None:
            return
        directory = self.env.stdUserPath()
        freq = MHFileRequest("Database import to restore tags", "Json-files (*.json)", directory)
        filename = freq.request()
        if filename is not None:
            if self.env.fileCache.importUserInfo(filename):
                QMessageBox.information(self.central_widget, "Done!", "User database restored, please restart program.")
                #self.glob.rescanAssets()
                # TODO: better way?
            else:
                ErrorBox(self.central_widget, self.env.last_error)

    def help_call(self):
        """
        open an URL
        """
        s = self.sender().text()
        urlname = self.env.release_info["support_urls"][s]
        if urlname in self.env.release_info:
            QDesktopServices.openUrl(QUrl(self.env.release_info[urlname], QUrl.TolerantMode))

    def lic_call(self):
        """
        open a text box with license
        """
        name =  self.sender().text()
        if name == "License":
            licname = "makehuman_license.txt"
            boxname = "MakeHuman License"
            image = os.path.join(self.env.path_sysicon, "makehuman.png")
        if name == "Credits":
            licname = "credits.txt"
            boxname = "Credits"
            image = os.path.join(self.env.path_sysicon, "makehuman.png")
        else:
            licname = name.lower() + "-license.txt"
            boxname = name + " License"
            image = None

        text = self.env.convertToRichFile(os.path.join(self.env.path_sysdata, "licenses", licname))
        TextBox(self, boxname, image, text)

    def glinfo_call(self):
        deb = GLDebug()
        text = deb.getTextInfo()
        image = os.path.join(self.env.path_sysicon, "makehuman.png")
        TextBox(self, "Local OpenGL Information", image, text)

    def quit_call(self, event=None):
        """
        save session (if desired)
        also make a check, when project was changed
        """
        if self.in_close is True:
            return

        confirmed =  self.changesLost("Exit program")
        if confirmed == 0:
            if isinstance(event,QCloseEvent):
                event.ignore()
                print ("Close event")
            return

        if self.graph is not None:
            self.graph.cleanUp()

        if self.in_close is False:
            self.in_close = True                # avoid double call by closeAllWindows
            s = self.env.session["mainwinsize"]
            s["w"] = self.width()
            s["h"] = self.height()
            self.env.saveSession()
            self.env.cleanup()
            self.glob.app.closeAllWindows()
            self.glob.app.quit()
