from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QAbstractItemView, QRadioButton, QGroupBox, QCheckBox, QLineEdit, QGridLayout

class MHPrefWindow(QWidget):
    """
    preferences window
    """
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        env = parent.glob

        self.setWindowTitle("Preferences")
        self.resize (500, 600)
        layout = QVBoxLayout()

        self.redirect_bool = env.config["redirect_messages"]
        self.redirect_path = env.path_error

        # folder boxes
        #
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
        if env.basemesh is not None:
            items = self.basewidget.findItems(env.basemesh,Qt.MatchExactly)
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

        self.cb_attach = QCheckBox("attach graphical window to main window")
        if env.config["graphicalgui_attached"] is True:
            self.cb_attach.setChecked(True)
        se_layout.addWidget(self.cb_attach)
        sess.setLayout(se_layout)
        layout.addWidget(sess)

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


    def cancel_call(self):
        self.close()

    def save_call(self):
        """
        does all the work to save configuration
        """
        env =  self.parent.glob

        sel = self.listwidget.selectedItems()
        if len(sel) > 0:
            theme = sel[0].text()
            self.parent.app.setStyles(self.themelist[theme])
        else:
            theme = "makehuman.qss"
        env.config["theme"] = theme

        sel = self.basewidget.selectedItems()
        if len(sel) > 0:
            basemesh = sel[0].text()
        else:
            basemesh = None
        env.config["basemesh"] = basemesh

        env.config["units"] = self.u_metric.text().lower() if self.u_metric.isChecked() else self.u_imperial.text().lower()
        env.config["remember_session"] = self.cb_keep.isChecked()
        env.config["units"] = self.u_metric.text().lower() if self.u_metric.isChecked() else self.u_imperial.text().lower()
        env.config["remember_session"] = self.cb_keep.isChecked()
        env.config["graphicalgui_attached"] = self.cb_attach.isChecked()

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
