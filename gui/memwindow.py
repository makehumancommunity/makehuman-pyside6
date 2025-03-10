"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * MemTableModel
    * MHQTableView
    * MHMemWindow
    * MHSelectAssetWindow
"""

from PySide6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QPushButton, QRadioButton, QGroupBox, QCheckBox,
    QTableView, QGridLayout, QHeaderView, QAbstractItemView
    )
from PySide6.QtGui import QColor, QPixmap
from gui.common import IconButton, ErrorBox

import sys
import re
import os

class MemTableModel(QAbstractTableModel):
    def __init__(self, data, columns):
        super(MemTableModel, self).__init__()

        self.horizontalHeaders = [''] * len(columns)
        for i, c in enumerate(columns):
            self.setHeaderData(i, Qt.Horizontal, c)

        self._data = data

    def bestFit(self, table):
        h = table.horizontalHeader()
        for i in range(0, len(self.horizontalHeaders)):
            h.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    def refreshData(self, data):
        self._data = data

    def setHeaderData(self, section, orientation, data, role=Qt.EditRole):
        if orientation == Qt.Horizontal and role in (Qt.DisplayRole, Qt.EditRole):
            try:
                self.horizontalHeaders[section] = data
                return True
            except:
                return False
        return super().setHeaderData(section, orientation, data, role)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            try:
                return self.horizontalHeaders[section]
            except:
                pass
        return super().headerData(section, orientation, role)

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])

    def refreshWithReset(self, data):
        super().beginResetModel()
        self.refreshData(data)
        super().endResetModel()

class MHQTableView(QTableView):
    def __init__(self, parent, mtype, callback=None):
        super().__init__()
        self.type = mtype
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verticalHeader().setVisible(False)

        self.callback = callback
        if callback is not None:
            self.clicked.connect(self.sendResult)

    def addModel(self, refresh_func, header):

        self.refresh_func = refresh_func
        self.mtmodel = MemTableModel(refresh_func(self.type), header)

        filter_proxy_model = QSortFilterProxyModel()
        filter_proxy_model.setSourceModel(self.mtmodel)
        filter_proxy_model.setFilterKeyColumn(0)

        self.setModel(filter_proxy_model)
        self.mtmodel.bestFit(self)

    def refreshData(self):
        self.mtmodel.refreshWithReset(self.refresh_func(self.type))
        self.viewport().update()

    def createPage(self):
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)
        layout.addWidget(self)
        return page

    def sendResult(self):
        idx = self.selectionModel().currentIndex()
        value= idx.sibling(idx.row(),0).data()
        self.callback(value)

class MHMemWindow(QWidget):
    """
    Message window to display used data
    """
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.env = parent.env
        self.glob = parent.glob
        self.setWindowTitle("Memory Usage and Ressources")
        self.resize (800, 600)

        self.tables = []
        tab = QTabWidget()

        # assets
        #
        table = MHQTableView(self, "assets")
        table.addModel(self.refreshAssetTable, ["Group", "Name", "used", "UUID",  "Author", "File Name", "Tags"])
        tab.addTab(table.createPage(), "Asset Repository")
        self.tables.append(table)

        # targets
        #
        table = MHQTableView(self, "targets")
        table.addModel(self.refreshTargetTable, ["Name", "File Increment", "Verts I",  "File Decrement", "Verts D", "MHM Identifier", "Current"])
        tab.addTab(table, "Targets")
        self.tables.append(table)

        # macros
        #
        table = MHQTableView(self, "macros")
        table.addModel(self.refreshMacroTable, ["Name", "Verts"])
        tab.addTab(table, "Macro-Targets")
        self.tables.append(table)

        # meshes
        #
        table = MHQTableView(self, "objects")
        table.addModel(self.refreshObjectTable, ["Name", "UUID", "File Name"])
        tab.addTab(table, "Meshes")
        self.tables.append(table)

        # materials
        #
        table = MHQTableView(self, "material")
        table.addModel(self.refreshMaterialTable, ["Name", "File Name"])
        tab.addTab(table, "Materials")
        self.tables.append(table)

        # textures
        #
        table = MHQTableView(self, "textures")
        table.addModel(self.refreshTextureTable, ["#", "Name", "Width", "Height"])
        tab.addTab(table, "Textures")
        self.tables.append(table)

        # missing targets
        #
        table = MHQTableView(self, "missing targets")
        table.addModel(self.refreshMissTargetTable, ["Name"])
        tab.addTab(table, "Missing Targets (last load)")
        self.tables.append(table)

        layout = QVBoxLayout()
        layout.addWidget(tab)
        hlayout = QHBoxLayout()

        rbutton = QPushButton("Redisplay")
        rbutton.clicked.connect(self.redisplay_call)
        hlayout.addWidget(rbutton)

        button = QPushButton("Close")
        button.clicked.connect(self.close_call)
        hlayout.addWidget(button)

        layout.addLayout(hlayout)
        self.setLayout(layout)

    def refreshAssetTable(self, dummy):
        data = []
        if self.glob.baseClass is not None:
            for elem in self.glob.cachedInfo:
                tags = " ".join(elem.tag) if len(elem.tag) > 0 else ""
                used = "yes" if elem.used else "no"
                data.append([elem.folder, elem.name, used, elem.uuid, elem.author, elem.path, tags])
        if len(data) == 0:
            data = [["no assets discovered"]]
        return (data)

    def refreshTargetTable(self, dummy):
        data = []
        targets = self.glob.Targets
        if targets is not None:
            for target in targets.modelling_targets:
                data.append(target.memInfo())
        if len(data) == 0:
            data = [["no targets loaded"]]
        return (data)

    def refreshMacroTable(self, dummy):
        data = []
        macros = self.glob.macroRepo
        if macros is not None:
            for macro in macros:
                m = self.glob.macroRepo[macro]
                data.append([str(macro), len(m.verts)])
        if len(data) == 0:
            data = [["no macros loaded"]]
        return (data)

    def refreshObjectTable(self, dummy):
        data = []
        if self.glob.baseClass is not None:
            base = self.glob.baseClass
            for elem in base.attachedAssets:
                data.append([elem.name, elem.uuid, elem.obj_file])
        if len(data) == 0:
            data = [["no objects loaded"]]
        return (data)

    def refreshMaterialTable(self, dummy):
        data = []
        if self.glob.baseClass is not None:
            base = self.glob.baseClass
            data.append(["base", base.skinMaterial])
            for elem in base.attachedAssets:
                data.append([elem.name, elem.material])
        if len(data) == 0:
            data = [["no material loaded"]]
        return (data)

    def refreshTextureTable(self, dummy):
        data = []
        t = self.glob.textureRepo.getTextures()
        if len(t) > 0:
            for texture in t:
                data.append([t[texture][1], texture, t[texture][0].width(), t[texture][0].height()])
        else:
            data = [["no textures loaded"]]
        return (data)


    def refreshMissTargetTable(self, dummy):
        data = []
        targets = self.glob.missingTargets
        for target in targets:
            data.append([target])
        if len(data) == 0:
            data = [["no missing targets found"]]
        return (data)


    def redisplay_call(self):
        """
        refreshes all tabs
        """
        for table in self.tables:
            table.refreshData()

    def close_call(self):
        self.close()


class MHSelectAssetWindow(QWidget):
    """
    Message window to select assets from asset list
    """
    def __init__(self, parent, json):
        super().__init__()
        self.parent = parent
        self.env = parent.env
        self.glob = parent.glob
        self.json = json
        self.current_asset = None
        self.setWindowTitle("Select from asset list")
        self.resize (1000, 600)
        columns = ["id", "Name", "Category", "Author"]
        self.thumbpath = os.path.join(self.env.path_userdata, "downloads", self.env.basename, "thumb.png")

        self.textboxfill = None
        self.tables = []

        tab = QTabWidget()

        for name in ("clothes", "hair", "eyes", "eyebrows", "eyelashes", "teeth",
                "expression", "pose", "skin", "rig", "proxy", "target", "model", "material"):
            table = MHQTableView(self, name, self.callback)
            table.addModel(self.refreshGeneric, columns)
            tab.addTab(table.createPage(), name.capitalize())
            self.tables.append(table)

        layout = QHBoxLayout()
        layout.addWidget(tab)
        vlayout = QVBoxLayout()

        assetgb = QGroupBox("Selected asset")
        assetgb.setObjectName("subwindow")
        gblayout = QGridLayout()
        self.camera = IconButton(1,  os.path.join(self.env.path_sysicon, "camera.png"), "Load thumbnail (enabled if available)", self.loadThumb)
        gblayout.addWidget(self.camera, 0, 0)
        self.imglabel = QLabel()
        self.displayThumb(None)
        gblayout.addWidget(self.imglabel, 0, 1)

        gblayout.addWidget(QLabel("Created:"), 1, 0)
        gblayout.addWidget(QLabel("Changed:"), 2, 0)
        gblayout.addWidget(QLabel("License:"), 3, 0)
        self.created = QLabel()
        self.changed = QLabel()
        self.license = QLabel()
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setMaximumSize(300, 400)
        self.description.setToolTip("Description created by author.")

        gblayout.addWidget(self.created, 1, 1)
        gblayout.addWidget(self.changed, 2, 1)
        gblayout.addWidget(self.license, 3, 1)
        gblayout.addWidget(self.description, 4, 0, 1, 2)
        assetgb.setLayout(gblayout)
        vlayout.addWidget(assetgb)
        vlayout.addStretch()

        rbutton = QPushButton("Redisplay")
        rbutton.clicked.connect(self.redisplay_call)
        vlayout.addWidget(rbutton)

        button = QPushButton("Close")
        button.clicked.connect(self.close_call)
        vlayout.addWidget(button)

        layout.addLayout(vlayout)
        self.setLayout(layout)

    def setParam(self, callback):
        self.textboxfill = callback

    def displayThumb(self, name):
        if name is None:
            name = os.path.join(self.env.path_sysicon, "noidea.png")
        pixmap = QPixmap(name).scaled(128, 128, aspectMode=Qt.KeepAspectRatio)
        self.imglabel.setPixmap(pixmap)


    def loadThumb(self):
        v = self.current_asset
        if v is not None and v in self.json:
            m = self.json[v]
            if "thumb" in m["files"]:
                thumb_url = m["files"]["thumb"]
                print ("Load thumb", thumb_url)
                self.parent.assets.getUrlFile(thumb_url, self.thumbpath)
                self.displayThumb(self.thumbpath)
            else:
                ErrorBox(self, "Asset has no thumbnail.")

    def callback(self, value):
        if value in self.json:
            if value != self.current_asset:
                self.current_asset = value
                self.displayThumb(None)
            m = self.json[value]
            self.camera.setEnabled("thumb" in m["files"])
            self.created.setText(m["created"])
            self.changed.setText(m["changed"])
            self.license.setText(m["license"])
            self.description.setText(m["description"])

            self.textboxfill(value)

    def refreshGeneric(self, dtype):
        data = []
        for key, elem in self.json.items():
            mtype = elem.get("type")
            cat = elem.get("category")
            if mtype == dtype:
                author = elem.get("username")
                if author is None:
                    author = "unknown"
                data.append([key, elem["title"], cat, author])

        if len(data) == 0:
            data = [["no " + dtype + " discovered"]]
        return (data)

    def redisplay_call(self):
        """
        refreshes all tabs
        """
        for table in self.tables:
            table.refreshData()

    def close_call(self):
        self.close()
