"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QAbstractItemView, QRadioButton,
    QGroupBox, QCheckBox, QLineEdit, QGridLayout, QTabWidget, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtGui import QIntValidator, QKeySequence
from gui.common import ErrorBox

class KeyPrefFilter(QObject):
    def eventFilter(self, widget, event):
        if event.type() == QEvent.ShortcutOverride:
            key = QKeySequence(event.modifiers()|event.key()).toString()
            widget.keylabel.setText(key)
        return False

class MHPrefWindow(QWidget):
    """
    preferences window
    """
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        env = parent.env

        self.setWindowTitle("Preferences")
        self.resize (500, 600)

        self.apihost = env.config["apihost"] if "apihost" in env.config else "127.0.0.1"
        self.apiport = str(env.config["apiport"] if "apiport" in env.config else 12345)

        self.redirect_bool = env.config["redirect_messages"]
        self.redirect_path = env.path_error

        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.maintab = QWidget()
        self.keytab  = QWidget()
        self.tab_widget.addTab(self.maintab, "Main")
        self.tab_widget.addTab(self.keytab, "Input")
        layout.addWidget(self.tab_widget)
        self.initMainTab(self.maintab)
        self.initKeyTab(self.keytab)

        # buttons for cancel and save
        #
        hLayout = QHBoxLayout()
        button1 = QPushButton("Cancel")
        button1.clicked.connect(self.cancel_call)
        hLayout.addWidget(button1)

        button2 = QPushButton("Save")
        button2.clicked.connect(self.save_call)
        hLayout.addWidget(button2)
        layout.addLayout(hLayout)

        self.setLayout(layout)

    def initMainTab(self, maintab):
        """
        main preferences: folder, themes, preselected mesh, units, API, session
        """
        env = self.parent.env
        layout = QVBoxLayout(maintab)
        folders = QGroupBox("Folders")
        folders.setObjectName("subwindow")
        fo_layout = QGridLayout()
        fo_layout.addWidget(QLabel("MakeHuman user home"), 0, 0, 1, 2)
        self.ql_path_home = QLineEdit(env.path_home)
        self.ql_path_home.setToolTip('if you change this, be aware to move existent data to new folder')
        fo_layout.addWidget(self.ql_path_home, 1, 0, 1, 2)
        fo_layout.addWidget(QLabel("Errors and logging"), 2, 0)
        self.cb_redirect = QCheckBox("Redirect")
        self.cb_redirect.setLayoutDirection(Qt.RightToLeft)
        if self.redirect_bool is True:
            self.cb_redirect.setChecked(True)
        self.cb_redirect.setToolTip('if not checked, messages will be sent to CLI')
        fo_layout.addWidget(self.cb_redirect, 2, 1)
        self.ql_path_error  = QLineEdit(env.path_error)
        fo_layout.addWidget(self.ql_path_error, 3, 0, 1, 2)
        folders.setLayout(fo_layout)
        layout.addWidget(folders)

        # themes
        #
        themes = QGroupBox("Themes")
        themes.setObjectName("subwindow")
        th_layout = QVBoxLayout()
        self.themelist = env.getDataFileList("qss", "themes")
        self.listwidget = QListWidget()
        self.listwidget.addItems(self.themelist.keys())
        self.listwidget.setSelectionMode(QAbstractItemView.SingleSelection)
        items = self.listwidget.findItems(env.config["theme"],Qt.MatchExactly)
        if len(items) > 0:
            self.listwidget.setCurrentItem(items[0])

        th_layout.addWidget(self.listwidget)
        themes.setLayout(th_layout)
        layout.addWidget(themes)

        # prefered mesh
        #
        meshes = QGroupBox("Base mesh")
        meshes.setObjectName("subwindow")
        me_layout = QVBoxLayout()
        baselist = env.getDataDirList("base.obj", "base")
        self.basewidget = QListWidget()
        self.basewidget.addItems(baselist.keys())
        self.basewidget.setSelectionMode(QAbstractItemView.SingleSelection)
        if env.basename is not None:
            items = self.basewidget.findItems(env.basename,Qt.MatchExactly)
            if len(items) > 0:
                self.basewidget.setCurrentItem(items[0])
        me_layout.addWidget(self.basewidget)
        meshes.setLayout(me_layout)
        layout.addWidget(meshes)

        # units
        #
        self.u_metric =   QRadioButton("Metric")
        self.u_imperial = QRadioButton("Imperial")
        if env.config["units"] == "imperial":
            self.u_imperial.setChecked(True)
        else:
            self.u_metric.setChecked(True)
        units = QGroupBox("Units")
        units.setObjectName("subwindow")
        me_layout = QVBoxLayout()
        me_layout.addWidget(self.u_metric)
        me_layout.addWidget(self.u_imperial)
        units.setLayout(me_layout)
        layout.addWidget(units)

        # API
        #
        apigr = QGroupBox("API (socket communication)")
        apigr.setObjectName("subwindow")
        ap_layout = QGridLayout()
        ap_layout.addWidget(QLabel("Host"), 0, 0)
        ap_layout.addWidget(QLabel("Port"), 1, 0)
        self.ql_host = QLineEdit(self.apihost)
        self.ql_port = QLineEdit(self.apiport)
        self.ql_port.setToolTip('socket port number, range is 1024 to 49151')
        self.ql_port.setValidator(QIntValidator())
        ap_layout.addWidget(self.ql_host, 0, 1)
        ap_layout.addWidget(self.ql_port, 1, 1)
        apigr.setLayout(ap_layout)
        layout.addWidget(apigr)

        # session
        #
        sess = QGroupBox("Session")
        sess.setObjectName("subwindow")
        se_layout = QVBoxLayout()

        self.cb_keep = QCheckBox("remember window size")
        if env.config["remember_session"] is True:
            self.cb_keep.setChecked(True)
        se_layout.addWidget(self.cb_keep)
        sess.setLayout(se_layout)
        layout.addWidget(sess)

    def initKeyTab(self, keytab):
        glob = self.parent.glob
        layout = QVBoxLayout(keytab)

        rows = len(glob.keyDict)
        keylist = QTableWidget(rows, 2)
        i = 0
        for key, item in glob.keyDict.items():
            keylist.setItem(i, 0, QTableWidgetItem(key))
            keylist.setItem(i, 1, QTableWidgetItem(item))
            i += 1
        layout.addWidget(keylist)

        self.keylabel = QLabel("", self)
        self.eventFilter = KeyPrefFilter(parent=self)
        self.installEventFilter(self.eventFilter)
        layout.addWidget(self.keylabel)

    def cancel_call(self):
        self.close()

    def save_call(self):
        """
        does all the work to save configuration
        """
        env =  self.parent.env

        apiport = int(self.ql_port.text())
        if apiport < 1024 or apiport > 49152:
            ErrorBox(self.parent.central_widget, "Port must be in range 1024 to 49151.")
            return

        env.config["apiport"] = apiport
        env.config["apihost"] = self.ql_host.text()

        sel = self.listwidget.selectedItems()
        if len(sel) > 0:
            theme = sel[0].text()
            self.parent.glob.app.setStyles(self.themelist[theme])
        else:
            theme = "makehuman.qss"
        env.config["theme"] = theme

        sel = self.basewidget.selectedItems()
        if len(sel) > 0:
            basename = sel[0].text()
        else:
            basename = None
        env.config["basename"] = basename

        env.config["units"] = self.u_metric.text().lower() if self.u_metric.isChecked() else self.u_imperial.text().lower()
        env.config["remember_session"] = self.cb_keep.isChecked()
        env.config["units"] = self.u_metric.text().lower() if self.u_metric.isChecked() else self.u_imperial.text().lower()
        env.config["remember_session"] = self.cb_keep.isChecked()

        env.path_home = env.config["path_home"] = self.ql_path_home.text()
        #
        env.config["redirect_messages"] = self.cb_redirect.isChecked()
        env.path_error = env.config["path_error"] = self.ql_path_error.text()
        env.generateFolders()

        if self.redirect_bool != env.config["redirect_messages"] or self.redirect_path != env.path_error:
            env.reDirect()

        env.logLine(2, "Save preferences in " + env.path_userconf)
        if env.writeJSON(env.path_userconf, env.config) is False:
            env.logLine(1, env.last_error)
        self.close()
