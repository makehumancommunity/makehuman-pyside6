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
        self.resize(600, 750)

        self.emptyIcon = os.path.join(self.env.path_sysdata, "icons", "noidea.png")
        sweep = os.path.join(self.env.path_sysicon, "sweep.png")

        layout = QVBoxLayout()
        self.namebox = QLineEdit(self.material.name)

        layout.addWidget(self.namebox)
        self.metalNess = SimpleSlider("Metallic Factor: ", 0, 100, self.metalchanged, minwidth=250)
        self.metalRoughness = SimpleSlider("Roughness Factor: ", 0, 100, self.metalroughchanged, minwidth=250)
        self.aomapIntensity = SimpleSlider("AO map Strength: ", 0, 100, self.aomapchanged, minwidth=250)
        self.normalmapIntensity = SimpleSlider("Normal Map Scale: ", 0, 100, self.normalmapchanged, minwidth=250)

        self.diffuselab = QLabel()
        self.normlab = QLabel()
        self.aolab = QLabel()
        self.mrlab = QLabel()
        self.diffuse = IconButton(1, self.emptyIcon, "base color texture", self.change_diff, 128)
        self.normtex = IconButton(2, self.emptyIcon, "normalmap texture", self.change_diff, 128)
        self.aotex = IconButton(3, self.emptyIcon, "ambient occlusion texture", self.change_diff, 128)
        self.mrtex = IconButton(4, self.emptyIcon, "metallic roughness texture", self.change_diff, 128)

        self.sweep1 = IconButton(1, sweep, "No texture", self.noTexture, 32)
        self.sweep2 = IconButton(2, sweep, "No texture", self.noTexture, 32)
        self.sweep3 = IconButton(3, sweep, "No texture", self.noTexture, 32)
        self.sweep4 = IconButton(4, sweep, "No texture", self.noTexture, 32)

        scrollContainer = QWidget()
        slayout = QVBoxLayout()
        gb = QGroupBox("Base color")
        gb.setObjectName("subwindow")
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.diffuse)
        hlayout.addWidget(self.diffuselab)
        hlayout.addWidget(self.sweep1)
        gb.setLayout(hlayout)
        slayout.addWidget(gb)

        gb = QGroupBox("Normalmap")
        gb.setObjectName("subwindow")
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.normtex)
        vlayout = QVBoxLayout()
        h2layout =  QHBoxLayout()
        h2layout.addWidget(self.normlab)
        h2layout.addWidget(self.sweep2)
        vlayout.addLayout(h2layout)
        vlayout.addWidget(self.normalmapIntensity)
        hlayout.addLayout(vlayout)
        gb.setLayout(hlayout)
        slayout.addWidget(gb)

        gb = QGroupBox("Ambient occlusion")
        gb.setObjectName("subwindow")
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.aotex)
        vlayout = QVBoxLayout()
        h2layout =  QHBoxLayout()
        h2layout.addWidget(self.aolab)
        h2layout.addWidget(self.sweep3)
        vlayout.addLayout(h2layout)
        vlayout.addWidget(self.aomapIntensity)
        hlayout.addLayout(vlayout)
        gb.setLayout(hlayout)
        slayout.addWidget(gb)

        gb = QGroupBox("Metallic/Roughness")
        gb.setObjectName("subwindow")
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.mrtex)
        vlayout = QVBoxLayout()
        h2layout =  QHBoxLayout()
        h2layout.addWidget(self.mrlab)
        h2layout.addWidget(self.sweep4)
        vlayout.addLayout(h2layout)
        vlayout.addWidget(self.metalNess)
        vlayout.addWidget(self.metalRoughness)
        hlayout.addLayout(vlayout)
        gb.setLayout(hlayout)
        slayout.addWidget(gb)

        
        gb = QGroupBox("Shader-specific")
        gb.setObjectName("subwindow")
        vlayout = QVBoxLayout()
        self.transparent = QCheckBox("Material is transparent")
        self.transparent.stateChanged.connect(self.transparentchanged)
        self.backfacecull = QCheckBox("Backface culling")
        self.backfacecull.stateChanged.connect(self.backfacecullchanged)
        self.alphacov = QCheckBox("Alpha to coverage")
        self.alphacov.stateChanged.connect(self.alphacovchanged)
        vlayout.addWidget(self.transparent)
        vlayout.addWidget(self.backfacecull)
        vlayout.addWidget(self.alphacov)
        gb.setLayout(vlayout)
        slayout.addWidget(gb)

        scrollContainer.setLayout(slayout)
        scroll = QScrollArea()
        scroll.setWidget(scrollContainer)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

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


    def shortenName(self, path):
        if len(path) > 38:
            return ("... " + path[len(path)-35:])
        return(path)

    def updateWidgets(self, obj):
        self.object = obj
        self.material = obj.material
        self.namebox.setText(self.material.name)
        self.metalRoughness.setSliderValue(self.material.pbrMetallicRoughness * 100)
        self.metalNess.setSliderValue(self.material.metallicFactor * 100)
        self.aomapIntensity.setSliderValue(self.material.aomapIntensity * 100)
        self.normalmapIntensity.setSliderValue(self.material.normalmapIntensity * 100)

        self.transparent.setChecked(self.material.transparent)
        self.backfacecull.setChecked(self.material.backfaceCull)
        self.alphacov.setChecked(self.material.alphaToCoverage)

        if hasattr(self.material, "diffuseTexture"):
            self.diffuse.newIcon(self.material.diffuseTexture)
            self.diffuselab.setText(self.shortenName(self.material.diffuseTexture))
        else:
            self.diffuse.newIcon(self.emptyIcon)
            self.diffuselab.setText("None")

        if hasattr(self.material, "normalmapTexture"):
            self.normtex.newIcon(self.material.normalmapTexture)
            self.normlab.setText(self.shortenName(self.material.normalmapTexture))
        else:
            self.normtex.newIcon(self.emptyIcon)
            self.normlab.setText("None")

        if hasattr(self.material, "aomapTexture"):
            self.aotex.newIcon(self.material.aomapTexture)
            self.aolab.setText(self.shortenName(self.material.aomapTexture))
        else:
            self.aotex.newIcon(self.emptyIcon)
            self.aolab.setText("None")

        if hasattr(self.material, "metallicRoughnessTexture"):
            self.mrtex.newIcon(self.material.metallicRoughnessTexture)
            self.mrlab.setText(self.shortenName(self.material.metallicRoughnessTexture))
        else:
            self.mrtex.newIcon(self.emptyIcon)
            self.mrlab.setText("None")

    def change_diff(self):
        s = self.sender()
        m = s._funcid
        print ("in change texture " + str(m))
        directory = self.material.objdir
        freq = MHFileRequest("Texture (PNG/JPG)", "Images (*.png *.jpg *.jpeg)", directory)
        filename = freq.request()
        if filename is not None:
            if m==1:
                self.material.diffuseTexture = filename
                self.diffuse.newIcon(self.material.diffuseTexture)
                self.diffuselab.setText(self.shortenName(self.material.diffuseTexture))
            elif m==2:
                self.material.normalmapTexture = filename
                self.normtex.newIcon(self.material.normalmapTexture)
                self.normlab.setText(self.shortenName(self.material.normalmapTexture))
            elif m==3:
                self.material.aomapTexture = filename
                self.aotex.newIcon(self.material.aomapTexture)
                self.aolab.setText(self.shortenName(self.material.aomapTexture))
            elif m==4:
                self.material.metallicRoughnessTexture = filename
                self.mrtex.newIcon(self.material.metallicRoughnessTexture)
                self.mrlab.setText(self.shortenName(self.material.metallicRoughnessTexture))


    def noTexture(self):
        s = self.sender()
        m = s._funcid
        if m==1 and hasattr(self.material, "diffuseTexture"):
            delattr( self.material, "diffuseTexture")
            self.diffuse.newIcon(self.emptyIcon)
            self.diffuselab.setText("None")
        elif m==2 and hasattr(self.material, "normalmapTexture"):
            delattr( self.material, "normalmapTexture")
            self.normtex.newIcon(self.emptyIcon)
            self.normlab.setText("None")
        elif m==3 and hasattr(self.material, "aomapTexture"):
            delattr( self.material, "aomapTexture")
            self.aotex.newIcon(self.emptyIcon)
            self.aolab.setText("None")
        elif m==4 and hasattr(self.material, "metallicRoughnessTexture"):
            delattr( self.material, "metallicRoughnessTexture")
            self.mrtex.newIcon(self.emptyIcon)
            self.mrlab.setText("None")

    def metalchanged(self, value):
        self.material.metallicFactor =  value / 100.0

    def metalroughchanged(self, value):
        self.material.pbrMetallicRoughness = value / 100.0

    def aomapchanged(self, value):
        self.material.aomapIntensity = value / 100.0

    def normalmapchanged(self, value):
        self.material.normalmapIntensity = value / 100.0

    def backfacecullchanged(self):
        self.material.backfaceCull = self.backfacecull.isChecked()

    def transparentchanged(self):
        self.material.transparent = self.transparent.isChecked()

    def alphacovchanged(self):
        self.material.alphaToCoverage = self.alphacov.isChecked()

    def save_call(self):
        directory = self.material.objdir
        freq = MHFileRequest("Material (MHMAT)", "material files (*.mhmat)", directory, save=".mhmat")
        filename = freq.request()
        if filename is not None:
            self.material.name = self.namebox.text()
            self.material.saveMatFile(filename)
            QMessageBox.information(self.parent.central_widget, "Done!", "Material saved as " + filename)

        self.close()

    def use_call(self):
        self.close()

