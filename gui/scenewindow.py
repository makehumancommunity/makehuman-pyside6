from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QPushButton, QRadioButton, QGroupBox, QCheckBox, QSizePolicy, QColorDialog
from PySide6.QtGui import QColor, QPalette
from gui.slider import SimpleSlider, ColorButton
from gui.mapslider import MapXYCombo
import numpy as np

class MHSceneWindow(QWidget):
    """
    Message window to display scene setup
    """
    def __init__(self, parent, view):
        super().__init__()
        self.parent = parent
        self.env = parent.env
        self.glob = parent.glob
        self.view = view
        self.light = view.light
        y1 = self.light.min_coords[1]
        y2 = self.light.max_coords[1]
        self.setWindowTitle("Scene and Lighting")
        self._volume = 100.0 / (np.array(self.light.max_coords) - np.array(self.light.min_coords))

        layout = QVBoxLayout()

        l2layout = QHBoxLayout()
        l01 = QGroupBox("Ambient Light")
        l01.setObjectName("subwindow")

        vlayout = QVBoxLayout()
        self.ambLuminance = SimpleSlider("Luminance: ", 0, 100, self.ambChanged)
        vlayout.addWidget(self.ambLuminance )

        self.ambColor = ColorButton("Color: ", self.ambColorChanged)
        vlayout.addWidget(self.ambColor)
        l01.setLayout(vlayout)
        l2layout.addWidget(l01)

        l02 = QGroupBox("Specular Light")
        l02.setObjectName("subwindow")

        vlayout = QVBoxLayout()
        self.specFocus = SimpleSlider("Focus: ", 1, 64, self.specFocChanged)
        vlayout.addWidget(self.specFocus )
        l02.setLayout(vlayout)
        l2layout.addWidget(l02)

        # shader type
        #
        l03 = QGroupBox("Shader Method")
        l03.setObjectName("subwindow")
        vlayout = QVBoxLayout()
        self.phong = QRadioButton("Phong")
        self.blinn = QRadioButton("Blinn")
        self.phong.toggled.connect(self.setMethod)
        self.blinn.toggled.connect(self.setMethod)
        vlayout.addWidget(self.phong)
        vlayout.addWidget(self.blinn)

        self.clearColor = ColorButton("Background color: ", self.clearColorChanged)
        vlayout.addWidget(self.clearColor)

        self.skybox = QPushButton("Skybox")
        self.skybox.setCheckable(True)
        self.skybox.clicked.connect(self.setSkybox)
        vlayout.addWidget(self.skybox)

        l03.setLayout(vlayout)
        l2layout.addWidget(l03)
        layout.addLayout(l2layout)

        # -- light 1
        #
        l1 = QGroupBox("Light Source 1")
        l1.setObjectName("subwindow")
        hlayout = QHBoxLayout()
        self.l1Luminance = SimpleSlider("Luminance: ", 0, 100, self.l1Changed)
        hlayout.addWidget(self.l1Luminance )

        self.l1Color = ColorButton("Color: ", self.l1ColorChanged)
        hlayout.addWidget(self.l1Color)

        self.l1map = MapXYCombo([0.5,0.5], self.l1pos, displayfunc=self.xzdisplay, drawcenter=True)
        hlayout.addWidget(self.l1map)

        self.l1Height = SimpleSlider("Height: ", y1, y2, self.l1posh, vertical=True)
        hlayout.addWidget(self.l1Height )

        l1.setLayout(hlayout)
        layout.addWidget(l1)

        # -- light 2

        l2 = QGroupBox("Light Source 2")
        l2.setObjectName("subwindow")
        hlayout = QHBoxLayout()
        self.l2Luminance = SimpleSlider("Luminance: ", 0, 100, self.l2Changed)
        hlayout.addWidget(self.l2Luminance )
    
        self.l2Color = ColorButton("Color: ", self.l2ColorChanged)
        hlayout.addWidget(self.l2Color)

        self.l2map = MapXYCombo([0.5,0.5], self.l2pos, displayfunc=self.xzdisplay, drawcenter=True)
        hlayout.addWidget(self.l2map)

        self.l2Height = SimpleSlider("Height: ", y1, y2, self.l2posh, vertical=True)
        hlayout.addWidget(self.l2Height )

        l2.setLayout(hlayout)
        layout.addWidget(l2)

        # -- light 3

        l3 = QGroupBox("Light Source 3")
        l3.setObjectName("subwindow")
        hlayout = QHBoxLayout()
        self.l3Luminance = SimpleSlider("Luminance: ", 0, 100, self.l3Changed)
        hlayout.addWidget(self.l3Luminance )

        self.l3Color = ColorButton("Color: ", self.l3ColorChanged)
        hlayout.addWidget(self.l3Color)

        self.l3map = MapXYCombo([0.5,0.5], self.l3pos, displayfunc=self.xzdisplay, drawcenter=True)
        hlayout.addWidget(self.l3map)

        self.l3Height = SimpleSlider("Height: ", y1, y2, self.l3posh, vertical=True)
        hlayout.addWidget(self.l3Height )

        l3.setLayout(hlayout)
        layout.addWidget(l3)

        hlayout = QHBoxLayout()
        button1 = QPushButton("Cancel")
        button1.clicked.connect(self.cancel_call)
        button2 = QPushButton("Default")
        button2.clicked.connect(self.default_call)
        button3 = QPushButton("Reset")
        button3.clicked.connect(self.reset_call)
        button4 = QPushButton("Use")
        button4.clicked.connect(self.use_call)
        hlayout.addWidget(button1)
        hlayout.addWidget(button2)
        hlayout.addWidget(button3)
        hlayout.addWidget(button4)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        self.getValues()

    def newView(self, view):
        self.view = view
        #self.light = view.light

    def xzdisplay(self, x,y ):
        x = (x - 0.5 ) * 100 / self._volume[0]
        y = (y - 0.5 ) * 100 / self._volume[2]
        return (f"Position:\nX: {x:.2f}\nZ: {y:.2f}")

    def vec4ToCol(self, vec4):
        color = QColor.fromRgbF(vec4.x(), vec4.y(), vec4.z())
        return(color)

    def getSkyBox(self):
        if self.light.skybox:
            self.skybox.setStyleSheet("background-color : orange")
            self.skybox.setChecked(True)
        else:
            self.skybox.setStyleSheet("background-color : lightgrey")
            self.skybox.setChecked(False)

    def getValues(self):
        if self.light.blinn:
            self.blinn.setChecked(True)
        else:
            self.phong.setChecked(True)

        self.getSkyBox()

        self.ambLuminance.setSliderValue(self.light.ambientLight.w() * 100)
        self.specFocus.setSliderValue(self.light.lightWeight.y())
        self.clearColor.setColorValue(self.vec4ToCol(self.light.glclearcolor))
        lights = self.light.lights
        self.l1Luminance.setSliderValue(lights[0]["vol"].w() * 10)
        self.l2Luminance.setSliderValue(lights[1]["vol"].w() * 10)
        self.l3Luminance.setSliderValue(lights[2]["vol"].w() * 10)
        self.ambColor.setColorValue(self.vec4ToCol(self.light.ambientLight))
        self.l1Color.setColorValue(self.vec4ToCol(lights[0]["vol"]))
        self.l2Color.setColorValue(self.vec4ToCol(lights[1]["vol"]))
        self.l3Color.setColorValue(self.vec4ToCol(lights[2]["vol"]))

        # top-view
        #
        self.l1map.mapInput.drawValues(lights[0]["pos"].x()* self._volume[0]+ 50, lights[0]["pos"].z()* self._volume[2] + 50)
        self.l2map.mapInput.drawValues(lights[1]["pos"].x()* self._volume[0]+ 50, lights[1]["pos"].z()* self._volume[2] + 50)
        self.l3map.mapInput.drawValues(lights[2]["pos"].x()* self._volume[0]+ 50, lights[2]["pos"].z()* self._volume[2] + 50)

        # height
        #
        self.l1Height.setSliderValue(lights[0]["pos"].y())
        self.l2Height.setSliderValue(lights[1]["pos"].y())
        self.l3Height.setSliderValue(lights[2]["pos"].y())

    def clearColorChanged(self, color):
        self.light.setClearColor(color)
        self.view.Tweak()

    def ambChanged(self, value):
        self.light.setAmbientLuminance(value / 100.0)
        self.view.Tweak()

    def ambColorChanged(self, color):
        self.light.setAmbientColor(color)
        self.view.Tweak()

    def specFocChanged(self, value):
        self.light.setSpecularFocus(value)
        self.view.Tweak()

    def setMethod(self, value):
        if self.blinn.isChecked():
            self.light.useBlinn(True)
        else:
            self.light.useBlinn(False)
        self.view.Tweak()

    def l1Changed(self, value):
        self.light.setLLuminance(0, value / 10.0)
        self.view.Tweak()

    def l1ColorChanged(self, color):
        self.light.setLColor(0, color)
        self.view.Tweak()

    def l1pos(self):
        m = self.l1map.mapInput.getValues()
        x = (m[0] - 0.5 ) * 100 / self._volume[0]
        z = (m[1] - 0.5 ) * 100 / self._volume[2]
        self.light.setLPos(0, x, z)
        self.view.Tweak()

    def l1posh(self, value):
        self.light.setHPos(0, value)
        self.view.Tweak()

    def l2Changed(self, value):
        self.light.setLLuminance(1, value / 10.0)
        self.view.Tweak()

    def l2ColorChanged(self, color):
        self.light.setLColor(1, color)
        self.view.Tweak()

    def l2pos(self):
        m = self.l2map.mapInput.getValues()
        x = (m[0] - 0.5 ) * 100  / self._volume[0]
        z = (m[1] - 0.5 ) * 100  / self._volume[2]
        self.light.setLPos(1, x, z)
        self.view.Tweak()

    def l2posh(self, value):
        self.light.setHPos(1, value)
        self.view.Tweak()

    def l3Changed(self, value):
        self.light.setLLuminance(2, value / 10.0)
        self.view.Tweak()

    def l3ColorChanged(self, color):
        self.light.setLColor(2, color)
        self.view.Tweak()

    def l3pos(self):
        m = self.l3map.mapInput.getValues()
        x = (m[0] - 0.5 ) * 100  / self._volume[0]
        z = (m[1] - 0.5 ) * 100  / self._volume[2]
        self.light.setLPos(2, x, z)
        self.view.Tweak()

    def l3posh(self, value):
        self.light.setHPos(2, value)
        self.view.Tweak()

    def setSkybox(self):
        self.light.useSkyBox(self.skybox.isChecked())
        self.getSkyBox()
        self.view.Tweak()

    def reset_call(self):
        self.light.fromGlobal(False)
        self.getValues()
        self.view.Tweak()

    def default_call(self):
        self.light.fromGlobal(True)
        self.getValues()
        self.view.Tweak()

    def use_call(self):
        self.light.toGlobal()
        self.close()

    def cancel_call(self):
        self.reset_call()
        self.close()


