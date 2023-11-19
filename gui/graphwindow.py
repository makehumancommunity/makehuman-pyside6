from PySide6.QtCore import QSize, Qt, QObject, QEvent
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
from PySide6.QtGui import QVector3D, QColor, QIcon
from core.baseobj import baseClass
from opengl.main import GraphWindow
import os

class NavigationEvent(QObject):
    def __init__(self, callback):
        self.win = callback
        super().__init__()

    def eventFilter(self, widget, event):
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

            print (key)
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

    def __init__(self, parent, env, glob):
        self.parent = parent
        self.env = env
        self.glob = glob
        self.attached = env.g_attach
        print ("Attach " + str(self.attached))
        super().__init__()
        #
        # keyboard actions
        #
        self.eventFilter = NavigationEvent(self)
        self.installEventFilter(self.eventFilter)


    def navButtons(self, vlayout):
        elems = [ 
            ["Front", "front.svg", self.front_button ],
            ["Back",  "back.svg",  self.back_button ],
            ["Left",  "left.svg",  self.left_button ],
            ["Right", "right.svg", self.right_button ],
            ["Top",   "top.svg",   self.top_button ],
            ["Bottom","bottom.svg",self.bottom_button ]
        ]
        for elem in elems:
            icon = os.path.join(self.env.path_sysicon, elem[1])
            button = QPushButton(elem[0])
            button.setStyleSheet("background-color : lightgrey")
            button.clicked.connect(elem[2])
            button.setIcon(QIcon(icon))
            button.setIconSize(QSize(50,50))
            button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            vlayout.addWidget(button)

        # perspective button is a toggle
        #
        icon = os.path.join(self.env.path_sysicon, "persp.svg")
        self.pers_button = QPushButton("Perspective")
        self.pers_button.setCheckable(True)
        self.pers_button.setChecked(True)
        self.pers_button.setStyleSheet("background-color : orange")
        self.pers_button.clicked.connect(self.toggle_perspective)
        self.pers_button.setIcon(QIcon(icon))
        self.pers_button.setIconSize(QSize(50,50))
        self.pers_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        vlayout.addWidget(self.pers_button)



    """
    creates layout for 3d window
    """
    def createLayout(self):
        self.view = GraphWindow(self.env, self.glob)          # must be saved in self!
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.view)

        vlayout = QVBoxLayout()
        self.navButtons(vlayout)
        vlayout.addStretch()

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
        self.parent.createCentralWidget()
        self.close()
        self.destroy()

    def disconnect_button(self):
        """
        disconnect the window from main window
        """
        print ("disconnect pressed")
        self.env.g_attach = False
        self.parent.createCentralWidget()
        self.parent.show()
        self.destroy()

    def back_button(self):
        self.view.customView(QVector3D(0, 0, -1))

    def front_button(self):
        self.view.customView(QVector3D(0, 0, 1))

    def left_button(self):
        self.view.customView(QVector3D(1, 0, 0))

    def right_button(self):
        self.view.customView(QVector3D(-1, 0, 0))

    def top_button(self):
        self.view.customView(QVector3D(0, 1, 0))

    def bottom_button(self):
        self.view.customView(QVector3D(0, -1, 0))

    def zoom(self, direction):
        self.view.modifyDistance(direction)

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

    def screenPosPan(self, pos):
        """
        calculate if mouse is over the area we want to work with (widget underMouse() does not work at all)
        """
        (b, x, y) = self.mouseInView(pos)
        if b:
            print ("panning")
            self.view.panning(float(x), float(y))


    def setPos(self, pos):
        (b, x, y) = self.mouseInView(pos)
        if b:
            self.view.arcBallCamStart(float(x), float(y))


    def toggle_perspective(self):
        if self.pers_button.isChecked():
            self.pers_button.setStyleSheet("background-color : orange")
        else:
            self.pers_button.setStyleSheet("background-color : lightgrey")
        self.view.togglePerspective(self.pers_button.isChecked())

    def show(self):
        """
        show window (only when not attached)
        """
        if self.attached is False:
            super().show()

