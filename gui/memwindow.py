from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QPushButton, QRadioButton, QGroupBox, QCheckBox, QTableView, QGridLayout, QHeaderView
from PySide6.QtGui import QColor

import sys
import re

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

        tab = QTabWidget()

        # assets
        #
        assetpage = QWidget()
        layout = QVBoxLayout()
        assetpage.setLayout(layout)

        self.assetTable = QTableView()
        data = self.refreshAssetTable()

        self.assetModel = MemTableModel(data, ["Group", "Name", "used", "UUID",  "Author", "File Name", "Tags"])
        self.assetTable.setModel(self.assetModel)
        self.assetModel.bestFit(self.assetTable)
        layout.addWidget(self.assetTable)

        # targets
        #
        targetpage = QWidget()
        layout = QVBoxLayout()
        targetpage.setLayout(layout)

        self.targetTable = QTableView()
        data = self.refreshTargetTable()

        self.targetModel = MemTableModel(data, ["Name", "File Increment", "Verts I",  "File Decrement", "Verts D", "MHM Identifier", "Current"])
        self.targetTable.setModel(self.targetModel)
        self.targetModel.bestFit(self.targetTable)
        layout.addWidget(self.targetTable)

        # macros
        #
        macropage = QWidget()
        layout = QVBoxLayout()
        macropage.setLayout(layout)

        self.macroTable = QTableView()
        data = self.refreshMacroTable()

        self.macroModel = MemTableModel(data, ["Name", "Verts"])
        self.macroTable.setModel(self.macroModel)
        self.macroModel.bestFit(self.macroTable)
        layout.addWidget(self.macroTable)

        # objects
        #
        objectpage = QWidget()
        layout = QVBoxLayout()
        objectpage.setLayout(layout)

        self.objectTable = QTableView()
        data = self.refreshObjectTable()

        self.objectModel = MemTableModel(data, ["Name", "UUID", "File Name"])
        self.objectTable.setModel(self.objectModel)
        self.objectModel.bestFit(self.objectTable)
        layout.addWidget(self.objectTable)

        # materials
        #
        materialpage = QWidget()
        layout = QVBoxLayout()
        materialpage.setLayout(layout)

        self.materialTable = QTableView()
        data = self.refreshMaterialTable()

        self.materialModel = MemTableModel(data, ["Name", "File Name"])
        self.materialTable.setModel(self.materialModel)
        self.materialModel.bestFit(self.materialTable)
        layout.addWidget(self.materialTable)

        # images
        #
        imagepage = QWidget()
        layout = QVBoxLayout()
        imagepage.setLayout(layout)

        self.textureTable = QTableView()
        data = self.refreshTextureTable()

        self.textureModel = MemTableModel(data, ["Name", "Width", "Height"])
        self.textureTable.setModel(self.textureModel)
        self.textureModel.bestFit(self.textureTable)
        layout.addWidget(self.textureTable)

        # missing targets
        #
        misstargetpage = QWidget()
        layout = QVBoxLayout()
        misstargetpage.setLayout(layout)

        self.missTargetTable = QTableView()
        data = self.refreshMissTargetTable()

        self.missTargetModel = MemTableModel(data, ["Name"])
        self.missTargetTable.setModel(self.missTargetModel)
        self.missTargetModel.bestFit(self.missTargetTable)
        layout.addWidget(self.missTargetTable)

        tab.addTab(assetpage, "Asset Repository")
        tab.addTab(targetpage, "Targets")
        tab.addTab(macropage, "Macro-Targets")
        tab.addTab(objectpage, "Meshes")
        tab.addTab(materialpage, "Materials")
        tab.addTab(imagepage, "Textures")
        tab.addTab(misstargetpage, "Missing Targets (last load)")

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


    def show(self):
        """
        normal show + flush to get the newest entries
        """
        super().show()

    def refreshAssetTable(self):
        data = []
        if self.glob.baseClass is not None:
            base = self.glob.baseClass
            for elem in base.cachedInfo:
                tags = " ".join(elem.tag) if len(elem.tag) > 0 else ""
                used = "yes" if elem.used else "no"
                data.append([elem.folder, elem.name, used, elem.uuid, elem.author, elem.path, tags])
        if len(data) == 0:
            data = [["no assets discovered"]]
        return (data)

    def refreshTargetTable(self):
        data = []
        targets = self.glob.Targets
        if targets is not None:
            for target in targets.modelling_targets:
                data.append(target.memInfo())
        if len(data) == 0:
            data = [["no targets loaded"]]
        return (data)

    def refreshMacroTable(self):
        data = []
        macros = self.glob.macroRepo
        if macros is not None:
            for macro in macros:
                m = self.glob.macroRepo[macro]
                data.append([str(macro), len(m.verts)])
        if len(data) == 0:
            data = [["no macros loaded"]]
        return (data)

    def refreshObjectTable(self):
        data = []
        if self.glob.baseClass is not None:
            base = self.glob.baseClass
            for elem in base.attachedAssets:
                data.append([elem.name, elem.uuid, elem.obj_file])
        if len(data) == 0:
            data = [["no objects loaded"]]
        return (data)

    def refreshMaterialTable(self):
        data = []
        if self.glob.baseClass is not None:
            base = self.glob.baseClass
            data.append(["base", base.skinMaterial])
            for elem in base.attachedAssets:
                data.append([elem.name, elem.material])
        if len(data) == 0:
            data = [["no material loaded"]]
        return (data)

    def refreshTextureTable(self):
        data = []
        t = self.glob.textures
        if len(t) > 0:
            for texture in t:
                data.append([texture, t[texture].width(), t[texture].height()])
        else:
            data = [["no textures loaded"]]
        return (data)


    def refreshMissTargetTable(self):
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
        self.assetModel.refreshWithReset(self.refreshAssetTable())
        self.assetTable.viewport().update()

        self.targetModel.refreshWithReset(self.refreshTargetTable())
        self.targetTable.viewport().update()

        self.macroModel.refreshWithReset(self.refreshMacroTable())
        self.macroTable.viewport().update()

        self.objectModel.refreshWithReset(self.refreshObjectTable())
        self.objectTable.viewport().update()

        self.materialModel.refreshWithReset(self.refreshMaterialTable())
        self.materialTable.viewport().update()

        self.textureModel.refreshWithReset(self.refreshTextureTable())
        self.textureTable.viewport().update()

        self.missTargetModel.refreshWithReset(self.refreshMissTargetTable())
        self.missTargetTable.viewport().update()


    def close_call(self):
        self.close()

