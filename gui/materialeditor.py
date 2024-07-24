import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QCheckBox, QSizePolicy, QScrollArea, 
        QLineEdit
        )
from PySide6.QtGui import QPixmap
from obj3d.object3d import object3d
from gui.common import MHTagEdit, IconButton
from gui.slider import SimpleSlider


class MHMaterialEditor(QWidget):
    """
    MaterialEditor
    """
    def __init__(self, parent, obj):
        super().__init__()
        self.parent = parent
        self.env = parent.env
        self.glob = parent.glob
        self.object = obj
        self.material = obj.material
        print (self.material)

        self.setWindowTitle("Material Editor")
        self.resize(360, 500)

        layout = QVBoxLayout()
        self.namebox = QLineEdit(self.material.name)

        layout.addWidget(self.namebox)
        self.metalNess = SimpleSlider("Metallic Factor: ", 0, 100, self.metalchanged, minwidth=250)
        self.metalRoughness = SimpleSlider("Roughness Factor: ", 0, 100, self.metalroughchanged, minwidth=250)

        layout.addWidget(self.metalNess)
        layout.addWidget(self.metalRoughness)
        layout.addStretch()
        hlayout = QHBoxLayout()
        savebutton = QPushButton("Use")
        savebutton.clicked.connect(self.save_call)
        hlayout.addWidget(savebutton)
        self.updateWidgets(obj)
        layout.addLayout(hlayout)
        self.setLayout(layout)

    def updateWidgets(self, obj):
        self.object = obj
        self.material = obj.material
        self.namebox.setText(self.material.name)
        self.metalRoughness.setSliderValue(self.material.pbrMetallicRoughness * 100)
        self.metalNess.setSliderValue(self.material.metallicFactor * 100)


    def metalchanged(self, value):
        self.material.metallicFactor =  value / 100.0

    def metalroughchanged(self, value):
        self.material.pbrMetallicRoughness = value / 100.0

    def save_call(self):
        self.close()

    def cancel_call(self):
        self.close()

