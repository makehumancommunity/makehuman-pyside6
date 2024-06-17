from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QGridLayout, QLabel

from opengl.buffers import PixelBuffer

class Renderer(QVBoxLayout):
    """
    should do with a few methods in background
    """
    def __init__(self, glob, view):
        super().__init__()
        self.glob = glob
        self.view = view

        glayout = QGridLayout()
        glayout.addWidget(QLabel("Width"), 0, 0)
        self.width = QLineEdit("1000")
        self.width.editingFinished.connect(self.acceptIntegers)
        glayout.addWidget(self.width, 0, 1)

        glayout.addWidget(QLabel("Height"), 1, 0)
        self.height = QLineEdit("1000")
        self.height.editingFinished.connect(self.acceptIntegers)
        glayout.addWidget(self.height, 1, 1)

        button = QPushButton("Render")
        button.clicked.connect(self.render)
        self.addLayout(glayout)
        self.addWidget(button)

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
        pix = PixelBuffer(self.view.context())
        pix.getBuffer(width, height)
        pix.saveBuffer()
        pix.releaseBuffer()
