from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QGroupBox, QListWidget, QAbstractItemView, QSizePolicy
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from gui.prefwindow import  MHPrefWindow
from gui.logwindow import  MHLogWindow
from gui.infowindow import  MHInfoWindow
from gui.graphwindow import  MHGraphicWindow
from gui.slider import ScaleComboArray
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
        self.graph = None
        self.in_close = False
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
        vLayout = QVBoxLayout()

        groupBox = QGroupBox("Basic Operations")

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
        vLayout.addWidget(bgroupBox)
        vLayout.addStretch()

        groupBox.setLayout(vLayout)
        hLayout.addWidget(groupBox)

        # create window for internal or external use
        #
        self.graph = MHGraphicWindow(self, self.env)
        gLayout = self.graph.createLayout()

        # in case of being attached, add external window in layout
        #
        if self.env.g_attach is True:
            groupBoxG = QGroupBox("Viewport")
            groupBoxG.setLayout(gLayout)
            hLayout.addWidget(groupBoxG)

        # ToolBox
        #
        groupTool = QGroupBox("Toolpanel")
        self.ToolBox = QVBoxLayout()

        self.drawToolPannel()
        groupTool.setLayout(self.ToolBox)
        hLayout.addWidget(groupTool)

        #
        central_widget.setLayout(hLayout)
        self.setCentralWidget(central_widget)

    def drawToolPannel(self):
        if self.glob.Targets is not None:
            widget = QWidget()
            scalerArray = ScaleComboArray(widget, self.glob.Targets.modelling_targets)
            widget.setLayout(scalerArray.layout)
            self.ToolBox.addWidget(widget)

    def emptyLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

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
            self.graph.view.paintGL()
            self.emptyLayout(self.ToolBox)
            self.drawToolPannel()
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
