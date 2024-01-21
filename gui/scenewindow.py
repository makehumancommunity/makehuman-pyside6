from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QPushButton, QRadioButton, QGroupBox, QCheckBox, QSlider, QSizePolicy, QColorDialog
from PySide6.QtGui import QColor, QPalette


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

        self.ambLabel = QLabel("")
        layout.addWidget(self.ambLabel)
        self.ambSlider =QSlider(Qt.Horizontal, self)
        self.ambSlider.setMinimum(0.0)
        self.ambSlider.setMaximum(100.0)
        self.ambSlider.setMinimumWidth(150)
        #self.ambSlider.setTickPosition(QSlider.TicksBelow)
        #self.ambSlider.setTickInterval(10)
        self.ambSlider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.ambSlider.valueChanged.connect(self.ambChanged)
        layout.addWidget(self.ambSlider)

        self.ambientColor = QPushButton("Ambient color")
        self.ambientColor.clicked.connect(self.getColor)
        layout.addWidget(self.ambientColor)

        button1 = QPushButton("Cancel")
        button1.clicked.connect(self.cancel_call)
        layout.addWidget(button1)
        self.setLayout(layout)


    def setAmbText(self, value):
        self.ambLabel.setText("Ambient luminance: " + str(round(value,2)))

    def ambChanged(self):
        value = self.ambSlider.value()
        self.setAmbText(value)
        self.light.setAmbientVolume(value / 100.0)
        self.view.Tweak()

    def getColor(self):
        color = QColorDialog.getColor() 
        print (color.name())
        # TODO: maybe different but a quick hack
        #
        self.ambientColor.setStyleSheet("background-color : " + color.name())
        self.light.setAmbientColor(color)
        self.view.Tweak()

    def cancel_call(self):
        self.close()


