from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from gui.prefwindow import  MHPrefWindow
from gui.logwindow import  MHLogWindow
from gui.infowindow import  MHInfoWindow
from gui.graphwindow import  MHGraphicWindow
import os

class MHMainWindow(QMainWindow):
    """
    Main Window class
    """
    def __init__(self, glob, app):
        self.app = app
        self.glob = glob
        self.pref_window = None
        self.info_window = None
        self.log_window = None
        self.graph = None
        self.in_close = False
        super().__init__()

        s = glob.session["mainwinsize"]
        title = glob.release_info["name"]
        self.setWindowTitle(title)
        self.resize (s["w"], s["h"])

        menu_bar = self.menuBar()
        about_menu = menu_bar.addMenu(QIcon(os.path.join(glob.path_sysicon, "makehuman.svg")), "&About")
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
        central_widget = QWidget()
        hLayout = QHBoxLayout()

        # create window for internal or external use
        #
        self.graph = MHGraphicWindow(self, self.glob)
        gLayout = self.graph.createLayout()

        # in case of being attached, add external window in layout
        #
        if self.glob.g_attach is True:
            graph_widget = QWidget()
            graph_widget.setAttribute(Qt.WA_StyledBackground, True)
            graph_widget.setStyleSheet('background-color: grey;')
            graph_widget.setLayout(gLayout)
            hLayout.addWidget(graph_widget)

        # just another button
        #
        button1 = QPushButton("Test")
        hLayout.addWidget(button1)

        #
        central_widget.setLayout(hLayout)
        self.setCentralWidget(central_widget)

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



    def quit_call(self):
        """
        save session (if desired)
        """
        if self.in_close is False:
            self.in_close = True                # avoid double call by closeAllWindows
            s = self.glob.session["mainwinsize"]
            s["w"] = self.width()
            s["h"] = self.height()
            self.glob.saveSession()
            self.glob.cleanup()
            self.app.closeAllWindows()
            self.app.quit()
