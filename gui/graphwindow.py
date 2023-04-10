from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PySide6.QtGui import QVector3D, QColor
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender


class window3d(Qt3DExtras.Qt3DWindow):
    """
    3D Window, a dummy at the moment displaying a sphere
    """
    def __init__(self):
        super().__init__()

        cam = self.camera()
        cam.lens().setPerspectiveProjection(45, 16 / 9, 0.1, 1000)
        cam.setPosition(QVector3D(0, 0, 40))
        cam.setViewCenter(QVector3D(0, 0, 0))

        rootentity = self.createScene()
        self.rootEntity = rootentity
        self.setRootEntity(rootentity)

    def createScene(self):
        # Root entity
        rootentity = Qt3DCore.QEntity()

        pmaterial1 = Qt3DExtras.QPhongMaterial(rootentity)
        pmaterial1.setDiffuse(QColor(255,0,0))
        pmaterial1.setAmbient(QColor(128,128,128))


        sphereMesh = Qt3DExtras.QSphereMesh(rootentity)
        sphereMesh.setRadius(5)

        trans = Qt3DCore.QTransform(rootentity)
        trans.setTranslation(QVector3D(0.0, 0.0, 0.0))
        baseentity = Qt3DCore.QEntity(rootentity)
        baseentity.addComponent(sphereMesh)
        baseentity.addComponent(pmaterial1)
        baseentity.addComponent(trans)

        return rootentity


class MHGraphicWindow(QWidget):
    """
    the graphic window, either attached or as an own window
    init creates widget itself, then createLayout is called
    """
    def __init__(self, parent, environment):
        self.parent = parent
        self.environment = environment
        self.attached = environment.g_attach
        print ("Attach " + str(self.attached))
        super().__init__()

    """
    creates layout for 3d window
    """
    def createLayout(self):
        self.view = window3d()          # must be saved in self!
        widget = QWidget()
        container = widget.createWindowContainer(self.view)
        screenSize = self.view.screen().size()
        container.setMinimumSize(QSize(600, 600))
        container.setMaximumSize(screenSize)
        glayout = QHBoxLayout()
        glayout.addWidget(container)

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
        self.environment.g_attach = True
        self.parent.createCentralWidget()
        self.close()
        self.destroy()

    """
    disconnect the window from main window
    """
    def disconnect_button(self):
        print ("disconnect pressed")
        self.environment.g_attach = False
        self.parent.createCentralWidget()
        self.parent.show()
        self.destroy()

    """
    show window (only when not attached)
    """
    def show(self):
        if self.attached is False:
            super().show()

"""
no longer working because of additional parameters
if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = MHGraphicWindow(True)
    layout = widget.createLayout()

    widget.show()
    sys.exit(app.exec())
"""

