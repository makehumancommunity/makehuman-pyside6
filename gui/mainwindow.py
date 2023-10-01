from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QGroupBox, QListWidget, QAbstractItemView, QSizePolicy, QScrollArea
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from gui.prefwindow import  MHPrefWindow
from gui.logwindow import  MHLogWindow
from gui.infowindow import  MHInfoWindow
from gui.graphwindow import  MHGraphicWindow
from gui.slider import ScaleComboArray
from gui.qtreeselect import MHTreeView
from core.fileops import baseClass
import os

class MHMainWindow(QMainWindow):
    """
    Main Window class
    """
    def __init__(self, env, glob, app):
        self.app = app
        self.env = env
        self.glob = glob
        self.pref_window = None
        self.info_window = None
        self.log_window = None
        self.rightColumn = None
        self.graph = None
        self.in_close = False
        self.targetfilter = "main|macro"  # TODO that is certainly not correct here ;)
        super().__init__()

        s = env.session["mainwinsize"]
        title = env.release_info["name"]
        self.setWindowTitle(title)
        self.resize (s["w"], s["h"])

        menu_bar = self.menuBar()
        about_menu = menu_bar.addMenu(QIcon(os.path.join(env.path_sysicon, "makehuman.svg")), "&About")
        about_act = about_menu.addAction("Info")
        about_act.triggered.connect(self.info_call)

        file_menu = menu_bar.addMenu("&File")
        quit_act = file_menu.addAction("Quit")
        quit_act.triggered.connect(self.quit_call)

        set_menu = menu_bar.addMenu("&Settings")
        pref_act = set_menu.addAction("Preferences")
        pref_act.triggered.connect(self.pref_call)
        log_act = set_menu.addAction("Messages")
        log_act.triggered.connect(self.log_call)

        self.createCentralWidget()


    def createCentralWidget(self):
        """
        create central widget, shown by default or by using connect/disconnect button from graphics window
        """
        env = self.env
        central_widget = QWidget()
        hLayout = QHBoxLayout()

        # left side, BasePanel
        #
        groupBase = QGroupBox("Basic Operations")
        self.BaseBox = QVBoxLayout()

        self.drawBasePanel()
        groupBase.setLayout(self.BaseBox)
        hLayout.addWidget(groupBase)

        # create window for internal or external use
        #
        self.graph = MHGraphicWindow(self, self.env, self.glob)
        gLayout = self.graph.createLayout()

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

        self.drawToolPanel(self.targetfilter)
        self.rightColumn.setMinimumWidth(500)
        self.rightColumn.setLayout(self.ToolBox)
        hLayout.addWidget(self.rightColumn)

        #
        central_widget.setLayout(hLayout)
        self.setCentralWidget(central_widget)

    def drawBasePanel(self):
        """
        draw left panel
        """
        env = self.env

        bgroupBox = QGroupBox("base mesh")
        bgroupBox.setObjectName("subwindow")

        bvLayout = QVBoxLayout()

        baselist = env.getDataDirList("base.obj", "base")
        self.basewidget = QListWidget()
        self.basewidget.setFixedSize(240, 200)
        self.basewidget.addItems(baselist.keys())
        self.basewidget.setSelectionMode(QAbstractItemView.SingleSelection)
        if env.basename is not None:
            items = self.basewidget.findItems(env.basename,Qt.MatchExactly)
            if len(items) > 0:
                self.basewidget.setCurrentItem(items[0])

        bvLayout.addWidget(self.basewidget)

        buttons = QPushButton("Select")
        buttons.clicked.connect(self.selectmesh_call)
        bvLayout.addWidget(buttons)
        bgroupBox.setLayout(bvLayout)
        self.BaseBox.addWidget(bgroupBox)

        if env.basename is not None:
            targetpath = os.path.join(env.path_sysdata, "target", env.basename)
            filename = os.path.join(targetpath, "target_cat.json")

            targetjson = env.readJSON(filename)
            if targetjson is not None:
                qtree = MHTreeView(targetjson, "Modelling", self.redrawNewCategory, None)
                self.BaseBox.addWidget(qtree)
            else:
                env.logLine(1, env.last_error )

        self.BaseBox.addStretch()

    def drawToolPanel(self, filterparam, text="Toolpanel"):
        #
        # will work according to mode later
        #
        if self.glob.Targets is not None:
            widget = QWidget()
            scalerArray = ScaleComboArray(widget, self.glob.Targets.modelling_targets, filterparam)
            widget.setLayout(scalerArray.layout)
            scrollArea = QScrollArea()
            scrollArea.setWidget(widget)
            scrollArea.setWidgetResizable(True)

            self.ToolBox.addWidget(scrollArea)
            self.rightColumn.setTitle("Modify character, category: " + text)

    def emptyLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                #else:
                #    self.clearLayout(item.layout())

    def show(self):
        """
        also shows graphic screen
        """
        self.graph.show()
        super().show()

    def closeEvent(self, event):
        self.quit_call()

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

    def info_call(self):
        """
        show about/information window
        """
        if self.info_window is None:
            self.info_window = MHInfoWindow(self, self.app)
        self.info_window.show()

    def selectmesh_call(self):
        sel = self.basewidget.selectedItems()
        if len(sel) > 0:
            base = sel[0].text()
            #
            # do nothing if not changes
            #
            if base == self.env.basename:
                return
            base = baseClass(self.env, self.glob, base)
            base.prepareClass()
            self.graph.view.newMesh()
            self.emptyLayout(self.ToolBox)
            self.drawToolPanel(self.targetfilter)
            self.ToolBox.update()

            self.emptyLayout(self.BaseBox)
            self.drawBasePanel()
            self.BaseBox.update()

            self.graph.update()

    def redrawNewCategory(self, category, text):
        print (category)
        self.emptyLayout(self.ToolBox)
        self.targetfilter = category
        self.drawToolPanel(category, text)
        self.ToolBox.update()



    def quit_call(self):
        """
        save session (if desired)
        """
        if self.in_close is False:
            self.in_close = True                # avoid double call by closeAllWindows
            s = self.env.session["mainwinsize"]
            s["w"] = self.width()
            s["h"] = self.height()
            self.env.saveSession()
            self.env.cleanup()
            self.app.closeAllWindows()
            self.app.quit()
