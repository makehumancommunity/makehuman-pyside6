from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PySide6.QtGui import QVector3D, QColor
from core.fileops import baseClass
from opengl.main import GraphWindow

class MHGraphicWindow(QWidget):
    """
    the graphic window, either attached or as an own window
    init creates widget itself, then createLayout is called
    """

    def __init__(self, parent, env, glob):
        self.parent = parent
        self.env = env
        self.glob = glob
        self.attached = env.g_attach
        print ("Attach " + str(self.attached))
        super().__init__()

    """
    creates layout for 3d window
    """
    def createLayout(self):
        self.view = GraphWindow(self.env, self.glob)          # must be saved in self!
        glayout = QHBoxLayout()
        glayout.addWidget(self.view)

        if self.attached is True:
            self.disconnectbutton = QPushButton("Disconnect")
            self.disconnectbutton.clicked.connect(self.disconnect_button)
            glayout.addWidget(self.disconnectbutton)
        else:
            self.connectbutton = QPushButton("Connect")
            self.connectbutton.clicked.connect(self.connect_button)
            glayout.addWidget(self.connectbutton)
            self.setLayout(glayout)
            self.setWindowTitle("3D View")
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
            self.resize (750, 650)
        return (glayout)

    """
    connect the window to main window
    """
    def connect_button(self):
        print ("connect pressed")
        self.env.g_attach = True
        self.parent.createCentralWidget()
        self.close()
        self.destroy()

    """
    disconnect the window from main window
    """
    def disconnect_button(self):
        print ("disconnect pressed")
        self.env.g_attach = False
        self.parent.createCentralWidget()
        self.parent.show()
        self.destroy()

    """
    show window (only when not attached)
    """
    def show(self):
        if self.attached is False:
            super().show()

