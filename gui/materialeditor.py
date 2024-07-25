import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QCheckBox, QSizePolicy, QScrollArea, 
        QLineEdit, QMessageBox
        )
from PySide6.QtGui import QPixmap
from obj3d.object3d import object3d
from gui.common import MHTagEdit, IconButton, MHFileRequest
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

        self.emptyIcon = os.path.join(self.env.path_sysdata, "icons", "noidea.png")

        layout = QVBoxLayout()
        self.namebox = QLineEdit(self.material.name)

        layout.addWidget(self.namebox)
        self.metalNess = SimpleSlider("Metallic Factor: ", 0, 100, self.metalchanged, minwidth=250)
        self.metalRoughness = SimpleSlider("Roughness Factor: ", 0, 100, self.metalroughchanged, minwidth=250)

        layout.addWidget(self.metalNess)
        layout.addWidget(self.metalRoughness)

        self.diffuselab = QLabel()
        self.normlab = QLabel()
        self.diffuse = IconButton(1, self.emptyIcon, "diffuse texture", self.change_diff, 256)
        self.normtex = IconButton(2, self.emptyIcon, "normalmap texture", self.change_diff, 256)
        layout.addWidget(self.diffuselab)
        layout.addWidget(self.diffuse)
        layout.addWidget(self.normlab)
        layout.addWidget(self.normtex)

        hlayout = QHBoxLayout()
        usebutton = QPushButton("Use")
        usebutton.clicked.connect(self.use_call)
        savebutton = QPushButton("Save")
        savebutton.clicked.connect(self.save_call)
        hlayout.addWidget(usebutton)
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
        if hasattr(self.material, "diffuseTexture"):
            self.diffuse.newIcon(self.material.diffuseTexture)
            self.diffuselab.setText(self.material.diffuseTexture)
        else:
            self.diffuse.newIcon(self.emptyIcon)
            self.diffuselab.setText("None")

        if hasattr(self.material, "normalmapTexture"):
            self.normtex.newIcon(self.material.normalmapTexture)
            self.normlab.setText(self.material.normalmapTexture)
        else:
            self.normtex.newIcon(self.emptyIcon)
            self.normlab.setText("None")

    def change_diff(self, value):
        print ("in change texture" + str(value))

    def metalchanged(self, value):
        self.material.metallicFactor =  value / 100.0

    def metalroughchanged(self, value):
        self.material.pbrMetallicRoughness = value / 100.0

    def save_call(self):
        directory = self.material.objdir
        freq = MHFileRequest("Material (MHMAT)", "material files (*.mhmat)", directory, save=".mhmat")
        filename = freq.request()
        if filename is not None:
            self.material.saveMatFile(filename)
            QMessageBox.information(self.parent.central_widget, "Done!", "Material saved as " + filename)

        self.close()

    def use_call(self):
        self.close()

