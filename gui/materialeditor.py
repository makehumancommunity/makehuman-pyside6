"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    * class TextureBox
    * class MHMaterialEditor
"""
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


class TextureBox(QGroupBox):
    """
    texture box with max of 2 sliders
    sliders work different without texture-map
    """
    def __init__(self, parent, obj, name, attrib, slider1=None, slider2=None):
        super().__init__(name)
        self.openGL = parent.glob.openGLWindow
        self.securityCheck = parent.checkLitsphere
        self.emptyIcon = parent.emptyIcon
        self.object = obj
        self.attrib = attrib
        self.material = obj.material
        self.slider1 = slider1
        self.slider2 = slider2
        self.slider1_factor = 100.0
        self.slider2_factor = 100.0
        self.setObjectName("subwindow")
        self.label = QLabel()
        self.sweep = IconButton(0, parent.sweep, "No texture", self.emptyMap, 32)
        self.map   = IconButton(0, parent.emptyIcon, name + " texture", self.setMap, 128)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.map)
        vlayout = QVBoxLayout()
        h2layout = QHBoxLayout()
        h2layout.addWidget(self.label)
        h2layout.addWidget(self.sweep)
        vlayout.addLayout(h2layout)

        if slider1:
            self.slider1attr = slider1[0]
            self.intensity1 = SimpleSlider("", 0, 100, self.slider1changed, minwidth=250)
            self.slider1text()
            vlayout.addWidget(self.intensity1)
            self.slider1set()
        else:
            self.intensity1 = None

        if slider2:
            self.slider2attr = slider2[0]
            self.intensity2 = SimpleSlider("", 0, 100, self.slider2changed, minwidth=250)
            self.slider2text()
            vlayout.addWidget(self.intensity2)
            self.slider2set()
        else:
            self.intensity2 = None

        hlayout.addLayout(vlayout)
        self.setLayout(hlayout)

    def shortenName(self, path):
        if len(path) > 38:
            return ("... " + path[len(path)-35:])
        return(path)

    def updateMap(self, obj, redisplay=True):
        """
        needs to accept new object
        """
        self.object = obj
        self.material = obj.material
        if hasattr(self.material, self.attrib):
            item = getattr(self.material, self.attrib)
            self.map.newIcon(item)
            self.label.setText(self.shortenName(item))
        else:
            self.map.newIcon(self.emptyIcon)
            self.label.setText("None")
        self.slider1text()
        self.slider2text()
        self.slider1set()
        self.slider2set()
        if redisplay:
            self.Tweak()

    def emptyMap(self):
        if hasattr(self.material, self.attrib):
            delattr(self.material, self.attrib)
            self.securityCheck()
            self.updateMap(self.object)

    def setMap(self):
        directory = self.material.objdir
        freq = MHFileRequest("Texture (PNG/JPG)", "Images (*.png *.jpg *.jpeg)", directory)
        filename = freq.request()
        if filename is not None:
            setattr(self.material, self.attrib, filename)
            self.updateMap(self.object)

    def slider1text(self):
        if self.slider1 is not None:
            if hasattr(self.material, self.attrib):
                self.intensity1.setLabelText(self.slider1[1])
            else:
                self.intensity1.setLabelText(self.slider1[2])

    def slider2text(self):
        if self.slider2 is not None:
            if hasattr(self.material, self.attrib):
                self.intensity2.setLabelText(self.slider2[1])
            else:
                self.intensity2.setLabelText(self.slider2[2])

    def setSlider1Factor(self, factor):
        self.slider1_factor = factor

    def slider1set(self):
        if self.slider1 is not None and hasattr(self.material, self.slider1attr):
                item = getattr(self.material, self.slider1attr)
                self.intensity1.setSliderValue(item * self.slider1_factor)

    def slider2set(self):
        if self.slider2 is not None and hasattr(self.material, self.slider2attr):
            item = getattr(self.material, self.slider2attr)
            self.intensity2.setSliderValue(item * self.slider2_factor)

    def slider1changed(self, value):
        if hasattr(self.material, self.slider1attr):
            setattr(self.material, self.slider1attr, value / self.slider1_factor)
            self.Tweak()

    def slider2changed(self, value):
        if hasattr(self.material, self.slider2attr):
            setattr(self.material, self.slider2attr, value / self.slider2_factor)
            self.Tweak()

    def Tweak(self):
        self.object.openGL.setMaterial(self.material)
        self.openGL.Tweak()

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
        self.TBoxes = []

        self.shadertypes = [ 
                [None, "Phong", "phong", "combination of ambient, diffuse and specular reflection"],
                [None, "Litpshere", "litsphere", "IBL (image based lighting), MatCap"],
                [None, "PBR", "pbr", "physical based rendering (openGL)"],
                [None, "Toon", "toon", "a silhouette based shader (openGL)"]
        ]

        self.factors = [
                ["metallicFactor", "[PBR] Metal map strength: ",     "[PBR] Metallic Factor: "],
                ["pbrMetallicRoughness", "[PBR] Roughness map strength: ", "[PBR] Roughness Factor: "],
                ["aomapIntensity", "[PBR/Phong] AO map strength: ",        "[PBR/Phong] Ambient Occlusion: "],
                ["normalmapIntensity", "Normalmap strength: ",  "--- no effect ---: "],
                ["emissiveFactor", "Emission map strength: ",  "Emission value strength: "],
                ["sp_AdditiveShading", "Litsphere additive shading: ",  "--- no effect ---: "]
        ]
        self.setWindowTitle("Material Editor")
        self.resize(600, 750)

        self.emptyIcon = os.path.join(self.env.path_sysdata, "icons", "noidea.png")
        self.sweep = os.path.join(self.env.path_sysicon, "sweep.png")

        layout = QVBoxLayout()
        self.namebox = QLineEdit(self.material.name)
        layout.addWidget(self.namebox)

        scrollContainer = QWidget()
        slayout = QVBoxLayout()

        gb = QGroupBox("OpenGL shader-specific")
        gb.setObjectName("subwindow")
        hlayout = QHBoxLayout()

        # shader buttons
        #
        vlayout = QVBoxLayout()
        #        ["Phong", "phong", "combination of ambient, diffuse and specular reflection", None],
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

        t = TextureBox (self, self.object, "Base color", "diffuseTexture")
        slayout.addWidget(t)
        self.TBoxes.append(t)

        t = TextureBox (self, self.object, "Normalmap", "normalmapTexture", self.factors[3])
        slayout.addWidget(t)
        self.TBoxes.append(t)

        t = TextureBox (self, self.object, "Ambient occlusion", "aomapTexture", self.factors[2])
        t.setSlider1Factor(50)
        slayout.addWidget(t)
        self.TBoxes.append(t)

        t = TextureBox (self, self.object, "Metallic/Roughness", "metallicRoughnessTexture", self.factors[1], self.factors[0])
        slayout.addWidget(t)
        self.TBoxes.append(t)

        t = TextureBox (self, self.object, "Emissive", "emissiveTexture", self.factors[4])
        slayout.addWidget(t)
        self.TBoxes.append(t)


        t = TextureBox (self, self.object, "Litsphere/Matcap", "sp_litsphereTexture", self.factors[5])
        slayout.addWidget(t)
        self.TBoxes.append(t)

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


    def Tweak(self):
        self.object.openGL.setMaterial(self.material)
        self.glob.openGLWindow.Tweak()

    def setShader(self):
        """
        activate shaderbuttons
        """
        for shader in self.shadertypes:
            shader[0].setChecked(self.material.shader == shader[2])

    def updateWidgets(self, obj):
        self.object = obj
        self.material = obj.material
        self.namebox.setText(self.material.name)

        self.setShader()

        self.transparent.setChecked(self.material.transparent)
        self.backfacecull.setChecked(self.material.backfaceCull)
        self.alphacov.setChecked(self.material.alphaToCoverage)

        for t in self.TBoxes:
            t.updateMap(self.object, False)
        self.Tweak()

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
            self.material.shader = "phong"
            self.setShader()
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

