from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QRadioButton, QGroupBox, QCheckBox, QTableView, QGridLayout
from PySide6.QtGui import QColor

import sys
import re

class TargetTableModel(QAbstractTableModel):
    def __init__(self, data):
        super(TargetTableModel, self).__init__()
        self.horizontalHeaders = [''] * 6

        self.setHeaderData(0, Qt.Horizontal, "Name")
        self.setHeaderData(1, Qt.Horizontal, "File Increment")
        self.setHeaderData(2, Qt.Horizontal, "Verts I")
        self.setHeaderData(3, Qt.Horizontal, "File Decrement")
        self.setHeaderData(4, Qt.Horizontal, "Verts D")
        self.setHeaderData(5, Qt.Horizontal, "Current")

        self._data = data

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
        layout = QVBoxLayout()

        self.table = QTableView()
        data = self.refreshTargetTable()

        self.model = TargetTableModel(data)
        self.table.setModel(self.model)
        layout.addWidget(self.table)

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
        else:
            data = [["no targets loaded"]]
        return (data)

    def redisplay_call(self):
        data = self.refreshTargetTable()
        self.model.beginResetModel()
        self.model.refreshData(data)
        self.model.endResetModel()
        self.table.viewport().update()


    def close_call(self):
        self.close()

