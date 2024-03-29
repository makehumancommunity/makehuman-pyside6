from PySide6.QtCore import QSize, Qt, QObject, QEvent
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy, QLabel, QSlider
from PySide6.QtGui import QVector3D, QColor, QIcon
from core.baseobj import baseClass
from gui.imageselector import IconButton
from gui.slider import SimpleSlider
from opengl.main import OpenGLView
import os

class NavigationEvent(QObject):
    def __init__(self, callback):
        self.win = callback
        super().__init__()

    def eventFilter(self, widget, event):

        if not hasattr(event, "type"):
            return False

        if event.type() == QEvent.ShortcutOverride:
            key = event.key()
            if key == 55:
                self.win.bottom_button()
            elif key == 56:
                self.win.back_button()
            elif key == 57:
                self.win.top_button()
            elif key == 50:
                self.win.front_button()
            elif key == 52:
                self.win.left_button()
            elif key == 54:
                self.win.right_button()
            elif key == 16777235:
                self.win.zoom(-1)
            elif key == 16777237:
                self.win.zoom(1)

            #print (key)
            #text = event.text()
            #print (text)
            #if event.modifiers():
            #    text = event.keyCombination().key().name.decode(encoding="utf-8")

        elif event.type() == QEvent.MouseMove:
            if event.buttons() == Qt.MouseButton.LeftButton:
                self.win.screenPosArc(event.globalPosition())
            elif event.buttons() == Qt.MouseButton.RightButton:
                self.win.screenPosPan(event.globalPosition())
        elif event.type() == QEvent.MouseButtonPress:
            self.win.setPos(event.globalPosition())
        elif event.type() == QEvent.Wheel:
            y = event.angleDelta().y()
            direction = 1 if y > 0 else -1
            self.win.zoom(direction)

        return False

class MHGraphicWindow(QWidget):
    """
    the graphic window, either attached or as an own window
    init creates widget itself, then createLayout is called
    """

    def __init__(self, parent, glob):
        self.parent = parent
        self.glob = glob
        self.env = glob.env
        self.attached =self.env.g_attach
        self.debug = False
        print ("Attach " + str(self.attached))
        super().__init__()
        glob.mhViewport = self
        #
        # keyboard actions
        #
        self.eventFilter = NavigationEvent(self)
        self.installEventFilter(self.eventFilter)


    def navButtons(self, vlayout):
        elems = [ 
            ["Top",   "top.png",   self.top_button ],
            ["Left",  "left.png",  self.left_button ],
            ["Front", "front.png", self.front_button ],
            ["Right", "right.png", self.right_button ],
            ["Back",  "back.png",  self.back_button ],
            ["Bottom","bottom.png",self.bottom_button ]
        ]
        button = IconButton(1, os.path.join(self.env.path_sysicon, elems[0][1]), elems[0][0], elems[0][2])
        vlayout.addWidget(button)
        hlayout = QHBoxLayout()
        for i in range(1,5):
            button = IconButton(1, os.path.join(self.env.path_sysicon, elems[i][1]), elems[i][0], elems[i][2])
            hlayout.addWidget(button)
        vlayout.addLayout(hlayout)

        button = IconButton(1, os.path.join(self.env.path_sysicon, elems[5][1]), elems[5][0], elems[5][2])
        vlayout.addWidget(button)

        # perspective button is a toggle
        #
        icon = os.path.join(self.env.path_sysicon, "persp.png")
        self.pers_button = QPushButton("Perspective")
        self.pers_button.setCheckable(True)
        self.pers_button.setChecked(True)
        self.pers_button.setStyleSheet("background-color : orange")
        self.pers_button.clicked.connect(self.toggle_perspective)
        self.pers_button.setIcon(QIcon(icon))
        self.pers_button.setIconSize(QSize(24,24))
        self.pers_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        vlayout.addWidget(self.pers_button)

        self.focusSlider = SimpleSlider("Focal Length: ", 15, 200, self.focusChanged)
        vlayout.addWidget(self.focusSlider )

    def getFocusText(self):
        cam = self.view.getCamera()
        if cam is not None:
            focalLength = cam.getFocalLength()
            self.focusSlider.setSliderValue(focalLength)

    def focusChanged(self, value):
        self.view.modifyFov(value)
        if self.debug:
            self.camChanged()
        
    def setSizeInfo(self):
        value=self.glob.baseClass.baseMesh.getHeightInUnits()
        text = ""
        for idx,slot in enumerate(self.glob.textSlot):
            if slot is not None:
                text += slot() + "\n"
        text += "Size: " + self.env.toUnit(value)
        self.sizeInfo.setText(text)

    def setDebug(self,val):
        self.debug = val
        if val:
            self.camChanged()
        else:
            self.infoDebug.setText("")

    def debugInfos(self,vlayout):
        self.infoDebug = QLabel()
        vlayout.addWidget(self.infoDebug)

    def camChanged(self):
        cam = self.view.getCamera()
        if cam is not None:
            text = str(cam)
        else:
            text = "Camera unknown"
        self.infoDebug.setText(text)

    def objInfos(self,vlayout):
        self.sizeInfo = QLabel()
        self.sizeInfo.setMinimumSize(150, 20)
        self.sizeInfo.setWordWrap(True)
        if self.glob.baseClass is not None:
            self.setSizeInfo()
        vlayout.addWidget(self.sizeInfo)

    """
    creates layout for 3d window
    """
    def createLayout(self):
        self.view = OpenGLView(self.glob)          # must be saved in self!
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.view)

        vlayout = QVBoxLayout()
        self.navButtons(vlayout)
        self.debugInfos(vlayout)
        vlayout.addStretch()
        self.objInfos(vlayout)

        if self.attached is True:
            self.disconnectbutton = QPushButton("Disconnect")
            self.disconnectbutton.clicked.connect(self.disconnect_button)
            self.disconnectbutton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            vlayout.addWidget(self.disconnectbutton)
            hlayout.addLayout(vlayout)
        else:
            self.connectbutton = QPushButton("Connect")
            self.connectbutton.clicked.connect(self.connect_button)
            self.connectbutton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            vlayout.addWidget(self.connectbutton)
            hlayout.addLayout(vlayout)
            self.setLayout(hlayout)
            self.setWindowTitle("3D View")
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
            self.resize (750, 650)

        return (hlayout)

    def connect_button(self):
        """
        connect the window to main window
        """
        print ("connect pressed")
        self.env.g_attach = True
        self.cleanUp()
        self.parent.base_call()
        self.parent.createCentralWidget()
        self.close()
        self.destroy()
        self.parent.updateScene()

    def disconnect_button(self):
        """
        disconnect the window from main window
        """
        print ("disconnect pressed")
        self.env.g_attach = False
        self.cleanUp()
        self.parent.base_call()
        self.parent.createCentralWidget()
        self.parent.show()
        self.destroy()
        self.parent.updateScene()

    def back_button(self):
        self.view.customView(QVector3D(0, 0, -1))
        if self.debug:
            self.camChanged()

    def front_button(self):
        self.view.customView(QVector3D(0, 0, 1))
        if self.debug:
            self.camChanged()

    def left_button(self):
        self.view.customView(QVector3D(1, 0, 0))
        if self.debug:
            self.camChanged()

    def right_button(self):
        self.view.customView(QVector3D(-1, 0, 0))
        if self.debug:
            self.camChanged()

    def top_button(self):
        self.view.customView(QVector3D(0, 1, 0))
        if self.debug:
            self.camChanged()

    def bottom_button(self):
        self.view.customView(QVector3D(0, -1, 0))
        if self.debug:
            self.camChanged()

    def zoom(self, direction):
        self.view.modifyDistance(direction)
        if self.debug:
            self.camChanged()

    def mouseInView(self, pos):
        window= self.view.mapToGlobal(self.view.pos())
        mx = int(pos.x())
        my = int(pos.y())
        wx = window.x()
        wy = window.y()
        hx = wx + self.view.width()
        hy = wy + self.view.height()
        if mx >= wx and my >=wy and mx < hx and my < hy:
            return (True, mx-wx, my-wy)
        else:
            return (False, 0, 0)

    def screenPosArc(self, pos):
        """
        calculate if mouse is over the area we want to work with (widget underMouse() does not work at all)
        """
        (b, x, y) = self.mouseInView(pos)
        if b:
            self.view.arcBallCamera(float(x), float(y))
            if self.debug:
                self.camChanged()

    def screenPosPan(self, pos):
        """
        calculate if mouse is over the area we want to work with (widget underMouse() does not work at all)
        """
        (b, x, y) = self.mouseInView(pos)
        if b:
            self.view.panning(float(x), float(y))
            if self.debug:
                self.camChanged()


    def setPos(self, pos):
        (b, x, y) = self.mouseInView(pos)
        if b:
            self.view.arcBallCamStart(float(x), float(y))


    def toggle_perspective(self):
        if self.pers_button.isChecked():
            self.pers_button.setStyleSheet("background-color : orange")
            self.focusSlider.setEnabled(True)
        else:
            self.pers_button.setStyleSheet("background-color : lightgrey")
            self.focusSlider.setEnabled(False)
        self.view.togglePerspective(self.pers_button.isChecked())

    def show(self):
        """
        show window (only when not attached)
        """
        if self.attached is False:
            super().show()

    def cleanUp(self):
        self.glob.freeTextures()
        if self.view is not None:
            self.view.cleanUp()
