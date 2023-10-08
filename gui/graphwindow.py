from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
from PySide6.QtGui import QVector3D, QColor, QIcon
from core.fileops import baseClass
from opengl.main import GraphWindow
import os

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
        self.pers_button = QPushButton("Perpective")
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

