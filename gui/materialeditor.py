import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QCheckBox, QSizePolicy, QScrollArea, 
        QLineEdit, QMessageBox, QRadioButton
        )
from PySide6.QtGui import QPixmap
from obj3d.object3d import object3d
from gui.common import MHTagEdit, IconButton, MHFileRequest,  ErrorBox
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
        self.shadertypes = [ 
                [None, "Phong", "phong3l", "combination of ambient, diffuse and specular reflection"],
                [None, "Litpshere", "litsphere", "IBL (image based lighting), MatCap"],
                [None, "PBR", "pbr", "physical based rendering (openGL)"]
        ]

        self.factors = [
                ["[PBR] Metal map strength: ",     "[PBR] Metallic Factor: "],
                ["[PBR] Roughness map strength: ", "[PBR] Roughness Factor: "],
                ["[PBR] AO map strength: ",        "[PBR] Ambient Occlusion: "]
        ]
        self.setWindowTitle("Material Editor")
        self.resize(600, 750)

        self.emptyIcon = os.path.join(self.env.path_sysdata, "icons", "noidea.png")
        sweep = os.path.join(self.env.path_sysicon, "sweep.png")

        layout = QVBoxLayout()
        self.namebox = QLineEdit(self.material.name)

        layout.addWidget(self.namebox)
        self.metalness = SimpleSlider(self.factors[0][0], 0, 100, self.metalchanged, minwidth=250)
        self.roughness = SimpleSlider(self.factors[1][0], 0, 100, self.metalroughchanged, minwidth=250)
        self.aomapIntensity = SimpleSlider(self.factors[2][0], 0, 100, self.aomapchanged, minwidth=250)
        self.normalmapIntensity = SimpleSlider("Normal Map Scale: ", 0, 100, self.normalmapchanged, minwidth=250)
        self.litsphereAddShade = SimpleSlider("Litsphere additive shading: ", 0, 100, self.litspherechanged, minwidth=250)

        self.diffuselab = QLabel()
        self.normlab = QLabel()
        self.aolab = QLabel()
        self.mrlab = QLabel()
        self.litlab = QLabel()
        self.diffuse = IconButton(1, self.emptyIcon, "base color texture", self.change_diff, 128)
        self.normtex = IconButton(2, self.emptyIcon, "normalmap texture", self.change_diff, 128)
        self.aotex = IconButton(3, self.emptyIcon, "ambient occlusion texture", self.change_diff, 128)
        self.mrtex = IconButton(4, self.emptyIcon, "metallic roughness texture", self.change_diff, 128)
        self.littex = IconButton(5, self.emptyIcon, "litsphere texture", self.change_diff, 128)

        self.sweep1 = IconButton(1, sweep, "No texture", self.noTexture, 32)
        self.sweep2 = IconButton(2, sweep, "No texture", self.noTexture, 32)
        self.sweep3 = IconButton(3, sweep, "No texture", self.noTexture, 32)
        self.sweep4 = IconButton(4, sweep, "No texture", self.noTexture, 32)
        self.sweep5 = IconButton(5, sweep, "No texture", self.noTexture, 32)

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
        vlayout.addWidget(self.metalness)
        vlayout.addWidget(self.roughness)
        hlayout.addLayout(vlayout)
        gb.setLayout(hlayout)
        slayout.addWidget(gb)

        gb = QGroupBox("OpenGL shader-specific")
        gb.setObjectName("subwindow")
        hlayout = QHBoxLayout()

        # shader buttons
        #
        vlayout = QVBoxLayout()
        #        ["Phong", "phong3l", "combination of ambient, diffuse and specular reflection", None],
        for shader in self.shadertypes:
            shader[0] = QRadioButton(shader[1])
            shader[0].setToolTip(shader[3])
            shader[0].toggled.connect(self.updateShaderType)
            vlayout.addWidget(shader[0])

        hlayout.addLayout(vlayout)

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
        hlayout.addLayout(vlayout)
        gb.setLayout(hlayout)
        slayout.addWidget(gb)

        gb = QGroupBox("OpenGL only valid inside MakeHuman")
        gb.setObjectName("subwindow")
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.littex)
        vlayout = QVBoxLayout()
        h2layout =  QHBoxLayout()
        h2layout.addWidget(self.litlab)
        h2layout.addWidget(self.sweep5)
        vlayout.addLayout(h2layout)
        vlayout.addWidget(self.litsphereAddShade)
        hlayout.addLayout(vlayout)
        gb.setLayout(hlayout)
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

    def Tweak(self):
        self.object.openGL.setMaterial(self.material)
        self.glob.openGLWindow.Tweak()

    def updateWidgets(self, obj):
        self.object = obj
        self.material = obj.material
        self.namebox.setText(self.material.name)

        # activate shaderbuttons
        #
        for shader in self.shadertypes:
            shader[0].setChecked(self.material.shader == shader[2])

        self.roughness.setSliderValue(self.material.pbrMetallicRoughness * 100)
        self.metalness.setSliderValue(self.material.metallicFactor * 100)
        self.aomapIntensity.setSliderValue(self.material.aomapIntensity * 100)
        self.normalmapIntensity.setSliderValue(self.material.normalmapIntensity * 100)
        self.litsphereAddShade.setSliderValue(self.material.sp_AdditiveShading * 100)

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
            self.aomapIntensity.setLabelText(self.factors[2][0])
            self.aotex.newIcon(self.material.aomapTexture)
            self.aolab.setText(self.shortenName(self.material.aomapTexture))
        else:
            self.aomapIntensity.setLabelText(self.factors[2][1])
            self.aotex.newIcon(self.emptyIcon)
            self.aolab.setText("None")

        if hasattr(self.material, "metallicRoughnessTexture"):
            self.roughness.setLabelText(self.factors[0][0])
            self.metalness.setLabelText(self.factors[1][0])
            self.mrtex.newIcon(self.material.metallicRoughnessTexture)
            self.mrlab.setText(self.shortenName(self.material.metallicRoughnessTexture))
        else:
            self.roughness.setLabelText(self.factors[0][1])
            self.metalness.setLabelText(self.factors[1][1])
            self.mrtex.newIcon(self.emptyIcon)
            self.mrlab.setText("None")

        if hasattr(self.material, "sp_litsphereTexture"):
            self.littex.newIcon(self.material.sp_litsphereTexture)
            self.litlab.setText(self.shortenName(self.material.sp_litsphereTexture))
        else:
            self.littex.newIcon(self.emptyIcon)
            self.litlab.setText("None")

    def updateShaderType(self, _):
        m = self.sender()
        if m.isChecked():
            for shader in self.shadertypes:
                if m is shader[0]:
                    self.material.shader =  shader[2]
        if self.checkLitsphere() is False:
            self.updateWidgets(self.object)
        else:
            self.Tweak()

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
                self.aomapIntensity.setLabelText(self.factors[2][0])
            elif m==4:
                self.material.metallicRoughnessTexture = filename
                self.mrtex.newIcon(self.material.metallicRoughnessTexture)
                self.mrlab.setText(self.shortenName(self.material.metallicRoughnessTexture))
                self.roughness.setLabelText(self.factors[0][0])
                self.metalness.setLabelText(self.factors[1][0])
            elif m==5:
                self.material.sp_litsphereTexture = filename
                self.littex.newIcon(self.material.sp_litsphereTexture)
                self.litlab.setText(self.shortenName(self.material.sp_litsphereTexture))
        self.Tweak()


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
            self.aomapIntensity.setLabelText(self.factors[2][1])
        elif m==4 and hasattr(self.material, "metallicRoughnessTexture"):
            delattr( self.material, "metallicRoughnessTexture")
            self.mrtex.newIcon(self.emptyIcon)
            self.mrlab.setText("None")
            self.roughness.setLabelText(self.factors[0][1])
            self.metalness.setLabelText(self.factors[1][1])
        elif m==5 and hasattr(self.material, "sp_litsphereTexture"):
            delattr( self.material, "sp_litsphereTexture")
            self.littex.newIcon(self.emptyIcon)
            self.litlab.setText("None")
        self.Tweak()

    def metalchanged(self, value):
        self.material.metallicFactor =  value / 100.0
        self.Tweak()

    def metalroughchanged(self, value):
        self.material.pbrMetallicRoughness = value / 100.0
        self.Tweak()

    def aomapchanged(self, value):
        self.material.aomapIntensity = value / 100.0
        self.Tweak()

    def normalmapchanged(self, value):
        self.material.normalmapIntensity = value / 100.0
        self.Tweak()

    def litspherechanged(self, value):
        self.material.sp_AdditiveShading = value / 100.0
        self.Tweak()

    def backfacecullchanged(self):
        self.material.backfaceCull = self.backfacecull.isChecked()
        self.Tweak()

    def transparentchanged(self):
        self.material.transparent = self.transparent.isChecked()
        self.Tweak()

    def alphacovchanged(self):
        self.material.alphaToCoverage = self.alphacov.isChecked()
        self.Tweak()

    def checkLitsphere(self):
        if self.material.shader == "litsphere" and not hasattr(self.material, "sp_litsphereTexture"):
            self.material.shader = "phong3l"
            ErrorBox(self, "Litpshere cannot be used without a litsphere texture.")
            return False
        return True

    def save_call(self):
        if self.checkLitsphere() is False:
            return
        directory = self.material.objdir
        freq = MHFileRequest("Material (MHMAT)", "material files (*.mhmat)", directory, save=".mhmat")
        filename = freq.request()
        if filename is not None:
            self.material.name = self.namebox.text()
            self.material.saveMatFile(filename)
            QMessageBox.information(self.parent.central_widget, "Done!", "Material saved as " + filename)

        self.close()

    def use_call(self):
        if self.checkLitsphere() is False:
            return
        self.Tweak()
        self.close()

    def closeEvent(self, event):
        self.checkLitsphere()

