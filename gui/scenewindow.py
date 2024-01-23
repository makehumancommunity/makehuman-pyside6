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
        self.setWindowTitle("Scene and Lighting")
        self.resize (800, 400)
        self._volume = 100.0 / (np.array(self.light.max_coords) - np.array(self.light.min_coords))

        layout = QVBoxLayout()

        self.ambVolume = SimpleSlider("Ambient luminance: ", 0, 100, self.ambChanged)
        layout.addWidget(self.ambVolume )

        self.ambColor = ColorButton("Ambient color: ", self.ambColorChanged)
        layout.addWidget(self.ambColor)

        y1 = self.light.min_coords[1]
        y2 = self.light.max_coords[1]
        # -- light 1
        #
        l1 = QGroupBox("Light Source 1")
        l1.setObjectName("subwindow")
        hlayout = QHBoxLayout()
        self.l1Volume = SimpleSlider("Luminance: ", 0, 100, self.l1Changed)
        hlayout.addWidget(self.l1Volume )

        self.l1Color = ColorButton("Color: ", self.l1ColorChanged)
        hlayout.addWidget(self.l1Color)

        self.l1map = MapXYCombo([0.5,0.5], self.l1pos, displayfunc=self.xzdisplay)
        hlayout.addWidget(self.l1map)

        self.l1Height = SimpleSlider("Height: ", y1, y2, self.l1posh, vertical=True)
        hlayout.addWidget(self.l1Height )

        l1.setLayout(hlayout)
        layout.addWidget(l1)

        # -- light 2

        l2 = QGroupBox("Light Source 2")
        l2.setObjectName("subwindow")
        hlayout = QHBoxLayout()
        self.l2Volume = SimpleSlider("Luminance: ", 0, 100, self.l2Changed)
        hlayout.addWidget(self.l2Volume )
    
        self.l2Color = ColorButton("Color: ", self.l2ColorChanged)
        hlayout.addWidget(self.l2Color)

        self.l2map = MapXYCombo([0.5,0.5], self.l2pos, displayfunc=self.xzdisplay)
        hlayout.addWidget(self.l2map)

        self.l2Height = SimpleSlider("Height: ", y1, y2, self.l2posh, vertical=True)
        hlayout.addWidget(self.l2Height )

        l2.setLayout(hlayout)
        layout.addWidget(l2)

        # -- light 3

        l3 = QGroupBox("Light Source 3")
        l3.setObjectName("subwindow")
        hlayout = QHBoxLayout()
        self.l3Volume = SimpleSlider("Luminance: ", 0, 100, self.l3Changed)
        hlayout.addWidget(self.l3Volume )

        self.l3Color = ColorButton("Color: ", self.l3ColorChanged)
        hlayout.addWidget(self.l3Color)

        self.l3map = MapXYCombo([0.5,0.5], self.l3pos, displayfunc=self.xzdisplay)
        hlayout.addWidget(self.l3map)

        self.l3Height = SimpleSlider("Height: ", y1, y2, self.l3posh, vertical=True)
        hlayout.addWidget(self.l3Height )

        l3.setLayout(hlayout)
        layout.addWidget(l3)

        button1 = QPushButton("Use")
        button1.clicked.connect(self.use_call)
        layout.addWidget(button1)
        self.setLayout(layout)
        self.getValues()

    def xzdisplay(self, x,y ):
        x = (x - 0.5 ) * 100 / self._volume[0]
        y = (y - 0.5 ) * 100 / self._volume[2]
        return (f"X: {x:.2f}\nZ: {y:.2f}")

    def vec4ToCol(self, vec4):
        color = QColor.fromRgbF(vec4.x(), vec4.y(), vec4.z())
        return(color)

    def getValues(self):
        self.ambVolume.setSliderValue(self.light.ambientLight.w() * 100)
        lights = self.light.lights
        self.l1Volume.setSliderValue(lights[0]["vol"].w() * 10)
        self.l2Volume.setSliderValue(lights[1]["vol"].w() * 10)
        self.l3Volume.setSliderValue(lights[2]["vol"].w() * 10)
        self.ambColor.setColorValue(self.vec4ToCol(self.light.ambientLight))
        self.l1Color.setColorValue(self.vec4ToCol(lights[0]["vol"]))
        self.l2Color.setColorValue(self.vec4ToCol(lights[1]["vol"]))
        self.l3Color.setColorValue(self.vec4ToCol(lights[2]["vol"]))
        # start with top-view
        self.l1map.mapInput.drawValues(lights[0]["pos"].x()* self._volume[0]+ 50, lights[0]["pos"].z()* self._volume[2] + 50)
        self.l2map.mapInput.drawValues(lights[1]["pos"].x()* self._volume[0]+ 50, lights[1]["pos"].z()* self._volume[2] + 50)
        self.l3map.mapInput.drawValues(lights[2]["pos"].x()* self._volume[0]+ 50, lights[2]["pos"].z()* self._volume[2] + 50)
        self.l1Height.setSliderValue(lights[0]["pos"].y())
        self.l2Height.setSliderValue(lights[1]["pos"].y())
        self.l3Height.setSliderValue(lights[2]["pos"].y())

    def ambChanged(self, value):
        self.light.setAmbientVolume(value / 100.0)
        self.view.Tweak()

    def ambColorChanged(self, color):
        self.light.setAmbColor(color)
        self.view.Tweak()

    def l1Changed(self, value):
        self.light.setLVolume(0, value / 10.0)
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
        self.light.setLVolume(1, value / 10.0)
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
        self.light.setLVolume(2, value / 10.0)
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

    def use_call(self):
        self.close()


