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

        # imagess
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

        tab.addTab(targetpage, "Targets")
        tab.addTab(macropage, "Macro-Targets")
        tab.addTab(imagepage, "Textures")

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

    def refreshTextureTable(self):
        data = []
        t = self.glob.textures
        if len(t) > 0:
            for texture in t:
                data.append([texture, t[texture].width(), t[texture].height()])
        else:
            data = [["no textures loaded"]]
        return (data)


    def redisplay_call(self):
        """
        refreshes all tabs
        """
        self.targetModel.refreshWithReset(self.refreshTargetTable())
        self.targetTable.viewport().update()

        self.macroModel.refreshWithReset(self.refreshMacroTable())
        self.macroTable.viewport().update()

        self.textureModel.refreshWithReset(self.refreshTextureTable())
        self.textureTable.viewport().update()


    def close_call(self):
        self.close()

