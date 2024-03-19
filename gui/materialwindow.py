import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QCheckBox, QSizePolicy, QScrollArea

class MHMaterialWindow(QWidget):
    """
    MaterialWindow
    """
    def __init__(self, parent, PicSelectWidget, materials):
        super().__init__()
        self.parent = parent
        self.env = parent.env
        self.glob = parent.glob
        self.materials = materials

        self.setWindowTitle("Material")
        self.resize(360, 500)

        layout = QVBoxLayout()
        self.selmode = 0
        self.imagescale = 128
        self.emptyIcon = os.path.join(self.env.path_sysdata, "icons", "noidea.png")

        self.picwidget = PicSelectWidget(self, materials, self.picButtonChanged, None)
        self.picwidget.populate(None, None)
        widget = QWidget()
        widget.setLayout(self.picwidget.layout)
        scrollArea = QScrollArea()
        scrollArea.setWidget(widget)
        scrollArea.setWidgetResizable(True)
        scrollArea.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        layout.addWidget(scrollArea)

        button4 = QPushButton("Use")
        button4.clicked.connect(self.use_call)
        layout.addWidget(button4)
        self.setLayout(layout)

    def picButtonChanged(self, asset):
        print(asset)

    def updateWidgets(self, materials):
        self.materials = materials
        self.picwidget.layout.removeAllWidgets()
        self.picwidget.layout.newAssetList(materials)
        self.picwidget.populate(None, None)

    def use_call(self):
        print ("hallo")
        self.close()



