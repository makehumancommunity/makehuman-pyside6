from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QPushButton, QRadioButton, QGroupBox, QCheckBox, QSizePolicy, QColorDialog
from PySide6.QtGui import QColor, QPalette
from gui.slider import SimpleSlider, ColorButton
from gui.mapslider import MapXYCombo

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
        self.resize (800, 600)

        layout = QVBoxLayout()

        self.ambVolume = SimpleSlider("Ambient luminance: ", 0, 100, self.ambChanged)
        layout.addWidget(self.ambVolume )

        self.ambColor = ColorButton("Ambient color: ", self.ambColorChanged)
        layout.addWidget(self.ambColor)

        # -- light 1

        hlayout = QHBoxLayout()
        v2layout = QHBoxLayout()
        self.l1Volume = SimpleSlider("Light1 luminance: ", 0, 100, self.l1Changed)
        v2layout.addWidget(self.l1Volume )

        self.l1Color = ColorButton("Light1 color: ", self.l1ColorChanged)
        v2layout.addWidget(self.l1Color)
        hlayout.addLayout(v2layout)

        self.l1map = MapXYCombo([0.5,0.5], self.l1pos)
        hlayout.addWidget(self.l1map)
        layout.addLayout(hlayout)

        # -- light 2

        hlayout = QHBoxLayout()
        v2layout = QHBoxLayout()
        self.l2Volume = SimpleSlider("Light2 luminance: ", 0, 100, self.l2Changed)
        v2layout.addWidget(self.l2Volume )
    
        self.l2Color = ColorButton("Light2 color: ", self.l2ColorChanged)
        v2layout.addWidget(self.l2Color)
        hlayout.addLayout(v2layout)

        self.l2map = MapXYCombo([0.5,0.5], self.l2pos)
        hlayout.addWidget(self.l2map)
        layout.addLayout(hlayout)

        # -- light 3

        hlayout = QHBoxLayout()
        v2layout = QHBoxLayout()
        self.l3Volume = SimpleSlider("Light3 luminance: ", 0, 100, self.l3Changed)
        v2layout.addWidget(self.l3Volume )

        self.l3Color = ColorButton("Light3 color: ", self.l3ColorChanged)
        v2layout.addWidget(self.l3Color)
        hlayout.addLayout(v2layout)

        self.l3map = MapXYCombo([0.5,0.5], self.l3pos)
        hlayout.addWidget(self.l3map)
        layout.addLayout(hlayout)

        button1 = QPushButton("Use")
        button1.clicked.connect(self.use_call)
        layout.addWidget(button1)
        self.setLayout(layout)
        self.getValues()

    def vec4ToCol(self, vec4):
        color = QColor.fromRgbF(vec4.x(), vec4.y(), vec4.z())
        return(color)

    def getValues(self):
        self.ambVolume.setSliderValue(self.light.ambientLight.w() * 100)
        self.l1Volume.setSliderValue(self.light.lights[0]["vol"].w() * 10)
        self.l2Volume.setSliderValue(self.light.lights[1]["vol"].w() * 10)
        self.l3Volume.setSliderValue(self.light.lights[2]["vol"].w() * 10)
        self.ambColor.setColorValue(self.vec4ToCol(self.light.ambientLight))
        self.ambColor.setColorValue(self.vec4ToCol(self.light.lights[0]["vol"]))
        self.ambColor.setColorValue(self.vec4ToCol(self.light.lights[1]["vol"]))
        self.ambColor.setColorValue(self.vec4ToCol(self.light.lights[2]["vol"]))
        # start with top-view
        self.l1map.mapInput.drawValues(self.light.lights[0]["pos"].x()+ 50, self.light.lights[0]["pos"].z() + 50)
        self.l2map.mapInput.drawValues(self.light.lights[1]["pos"].x()+ 50, self.light.lights[1]["pos"].z() + 50)
        self.l3map.mapInput.drawValues(self.light.lights[2]["pos"].x()+ 50, self.light.lights[2]["pos"].z() + 50)

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
        x = (m[0] - 0.5 ) * 100
        z = (m[1] - 0.5 ) * 100
        self.light.setLPos(0, x, z)
        self.view.Tweak()

    def l2pos(self):
        m = self.l2map.mapInput.getValues()
        x = (m[0] - 0.5 ) * 100
        z = (m[1] - 0.5 ) * 100
        self.light.setLPos(1, x, z)
        self.view.Tweak()

    def l3pos(self):
        m = self.l3map.mapInput.getValues()
        x = (m[0] - 0.5 ) * 100
        z = (m[1] - 0.5 ) * 100
        self.light.setLPos(2, x, z)
        self.view.Tweak()

    def l2Changed(self, value):
        self.light.setLVolume(1, value / 10.0)
        self.view.Tweak()

    def l2ColorChanged(self, color):
        self.light.setLColor(1, color)
        self.view.Tweak()

    def l3Changed(self, value):
        self.light.setLVolume(2, value / 10.0)
        self.view.Tweak()

    def l3ColorChanged(self, color):
        self.light.setLColor(2, color)
        self.view.Tweak()

    def use_call(self):
        self.close()


