from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QGridLayout, QLabel, QMessageBox,  QCheckBox

from gui.common import IconButton, MHFileRequest
from opengl.buffers import PixelBuffer

import os

class Renderer(QVBoxLayout):
    """
    should do with a few methods in background
    """
    def __init__(self, parent, glob, view):
        super().__init__()
        self.parent = parent
        self.glob = glob
        self.env = glob.env
        self.view = view
        self.image = None
        self.transparent = False

        glayout = QGridLayout()
        glayout.addWidget(QLabel("Width"), 0, 0)
        self.width = QLineEdit("1000")
        self.width.editingFinished.connect(self.acceptIntegers)
        glayout.addWidget(self.width, 0, 1)

        glayout.addWidget(QLabel("Height"), 1, 0)
        self.height = QLineEdit("1000")
        self.height.editingFinished.connect(self.acceptIntegers)
        glayout.addWidget(self.height, 1, 1)
        self.addLayout(glayout)

        self.transButton = QCheckBox("transparent canvas")
        self.transButton.setLayoutDirection(Qt.LeftToRight)
        self.transButton.toggled.connect(self.changeTransparency)
        self.addWidget(self.transButton)

        button = QPushButton("Render")
        button.clicked.connect(self.render)
        self.addWidget(button)

        self.saveButton = IconButton(1,  os.path.join(self.env.path_sysicon, "f_save.png"), "save image", self.saveImage)
        self.addWidget(self.saveButton)
        self.setButtons()

    def changeTransparency(self, param):
        self.transparent = param

    def setButtons(self):
        self.saveButton.setEnabled(self.image is not None)
        self.transButton.setChecked(self.transparent)

    def acceptIntegers(self):
        m = self.sender()
        try:
            i = int(m.text())
        except ValueError:
            m.setText("1000")
        else:
            if i < 64:
                i = 64
            elif i > 4096:
                i = 4096
            m.setText(str(i))

    def render(self):
        width  = int(self.width.text())
        height = int(self.height.text())
        pix = PixelBuffer(self.glob, self.view, self.transparent)
        #self.glob.openGLBlock = True
        pix.getBuffer(width, height)
        self.image = pix.bufferToImage()
        pix.releaseBuffer()
        self.setButtons()
        #self.glob.openGLBlock = False

    def saveImage(self):
        directory = self.env.stdUserPath()
        freq = MHFileRequest("Image (PNG)", "image files (*.png)", directory, save=".png")
        filename = freq.request()
        if filename is not None:
            self.image.save(filename, "PNG", -1)
            QMessageBox.information(self.parent.central_widget, "Done!", "Image saved as " + filename)


