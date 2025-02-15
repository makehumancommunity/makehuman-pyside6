"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck
"""
from PySide6.QtWidgets import (
        QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy, QLabel,
        QSlider, QCheckBox, QMessageBox
)
from PySide6.QtCore import QSize, Qt, QObject, QEvent
from PySide6.QtGui import QVector3D, QColor, QIcon, QKeySequence
from core.baseobj import baseClass
from gui.common import IconButton
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
            key = QKeySequence(event.modifiers()|event.key()).toString()
            self.win.keyToFunction(key)

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
    the graphic window
    init creates widget itself, then createLayout is called
    """

    def __init__(self, glob):
        self.glob = glob
        self.env = glob.env
        self.debug = False
        super().__init__()

        # bind keys to action and set up event filter
        #
        self.funcDict = {
                "Top": self.top_button, "Left": self.left_button,
                "Right": self.right_button, "Front": self.front_button,
                "Back": self.back_button, "Bottom": self.bottom_button,
                "Zoom-In": self.zoom_in, "Zoom-Out": self.zoom_out, "Stop Animation": self.stop_anim,
                "Toggle Perspective": self.toggle_perspective_key
        }
        self.key2Func = {}
        self.generateKeyDict()
        self.eventFilter = NavigationEvent(self)
        self.installEventFilter(self.eventFilter)
        self.hiddenbutton = None

    def generateKeyDict(self):
        """
        create dictionary from configurable keys
        """
        for key, item in self.glob.keyDict.items():
            self.key2Func[item] = self.funcDict[key]

    def keyToFunction(self, code):
        """
        this is called, when key-event took place
        """
        if code in self.key2Func:
            self.key2Func[code]()

    def navButtons(self, vlayout):
        elems = [ 
            ["Top",   "top.png",   self.top_button ],
            ["Left",  "left.png",  self.left_button ],
            ["Front", "front.png", self.front_button ],
            ["Right", "right.png", self.right_button ],
            ["Back",  "back.png",  self.back_button ],
            ["Bottom","bottom.png",self.bottom_button ],
            ["Axes","3dcoord.png", self.toggle_axes ],
            ["XY-Grid","xygrid.png",  self.toggle_grid ],
            ["YZ-Grid","yzgrid.png",  self.toggle_grid ],
            ["Floor-Grid","xzgrid.png",  self.toggle_grid ],
            ["Skybox","skybox.png",self.toggle_skybox ],
            ["Visualize skeleton", "an_skeleton.png", self.toggle_objects ],
            ["Visualize mesh", "eq_proxy.png", self.toggle_wireframe ],
            ["Visualize hidden vertices", "ghost.png", self.toggle_transpassets ]
        ]

        # hidden geometry
        #
        self.hiddenbutton= QCheckBox("show hidden geometry")
        self.hiddenbutton.setLayoutDirection(Qt.LeftToRight)
        self.hiddenbutton.toggled.connect(self.changeHidden)
        if self.glob.baseClass is not None and self.glob.baseClass.hide_verts is False:
            self.hiddenbutton.setChecked(True)
        self.renderView(False)
        vlayout.addWidget(self.hiddenbutton )

        button = IconButton(1, os.path.join(self.env.path_sysicon, elems[0][1]), elems[0][0], elems[0][2])
        vlayout.addWidget(button)
        hlayout = QHBoxLayout()
        hlayout.setSpacing(1)
        for i in range(1,5):
            button = IconButton(1, os.path.join(self.env.path_sysicon, elems[i][1]), elems[i][0], elems[i][2])
            hlayout.addWidget(button)
        vlayout.addLayout(hlayout)

        button = IconButton(1, os.path.join(self.env.path_sysicon, elems[5][1]), elems[5][0], elems[5][2])
        vlayout.addWidget(button)

        # grid, axes
        hlayout = QHBoxLayout()
        hlayout.setSpacing(1)
        for i in range(6,10):
            button = IconButton(i, os.path.join(self.env.path_sysicon, elems[i][1]), elems[i][0], elems[i][2], checkable=True)
            hlayout.addWidget(button)
        vlayout.addLayout(hlayout)

        # ghost, skybox
        hlayout = QHBoxLayout()
        for i in range(10,14):
            button = IconButton(1, os.path.join(self.env.path_sysicon, elems[i][1]), elems[i][0], elems[i][2], checkable=True)
            button.setChecked(False if i != 10 else True) # skybox is true
            hlayout.addWidget(button)
        vlayout.addLayout(hlayout)

        # perspective button is a toggle
        #
        hlayout = QHBoxLayout()
        self.persbutton = IconButton(1, os.path.join(self.env.path_sysicon, "persp.png"), "Perspective", self.toggle_perspective, checkable=True)
        self.persbutton.setChecked(True)
        hlayout.addWidget(self.persbutton)

        button = IconButton(1, os.path.join(self.env.path_sysicon, "camera.png"), "Grab screen", self.screenShot)
        hlayout.addWidget(button)

        vlayout.addLayout(hlayout)

        self.focusSlider = SimpleSlider("Focal Length: ", 15, 200, self.focusChanged)
        vlayout.addWidget(self.focusSlider )

    def renderView(self, param):
        if param:
            self.hiddenbutton.setEnabled(False)
            self.hiddenbutton.setToolTip('hidden geometry cannot be changed in render view')
        else:
            self.hiddenbutton.setEnabled(True)
            self.hiddenbutton.setToolTip('do not delete vertices under clothes')

    def screenShot(self, param):
        icon = self.view.grabFramebuffer()
        name = self.env.dateFileName("grab-", ".png")
        name = os.path.join(self.env.path_userdata, "grab", name)
        icon.save(name, "PNG", -1)
        QMessageBox.information(self.view, "Done!", "Screenshot saved as " + name)

    def changeHidden(self, param):
        if self.glob.baseClass is None:
            return
        self.glob.baseClass.hide_verts = not param
        self.glob.baseClass.calculateDeletedVerts()
        self.view.Tweak()

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
        self.sizeInfo.setMinimumSize(140, 20)
        self.sizeInfo.setWordWrap(True)
        if self.glob.baseClass is not None:
            self.setSizeInfo()
        vlayout.addWidget(self.sizeInfo)

    def createLayout(self):
        """
        creates layout for 3d window
        """
        self.view = OpenGLView(self.glob)          # must be saved in self!

        # disable multisampling in case format return no sample buffers
        #
        self.env.noalphacover = (self.view.format().samples() == -1)

        self.glob.openGLWindow = self.view
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.view)

        vlayout = QVBoxLayout()
        self.navButtons(vlayout)
        self.debugInfos(vlayout)
        vlayout.addStretch()
        self.objInfos(vlayout)
        hlayout.addLayout(vlayout)
        return (hlayout)

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

    def stop_anim(self):
        self.view.stopAnimation()

    def toggle_grid(self):
        pat = ["xygrid", "yzgrid", "xzgrid"]
        b = self.sender()
        v = b.isChecked()
        b.setChecked(v)
        self.view.togglePrims(pat[b._funcid - 7], v)

    def toggle_axes(self):
        b = self.sender()
        v = b.isChecked()
        b.setChecked(v)
        self.view.togglePrims("axes", v)

    def toggle_skybox(self):
        b = self.sender()
        v = b.isChecked()
        b.setChecked(v)
        self.view.toggleSkybox(v)

    def toggle_objects(self):
        b = self.sender()
        v = b.isChecked()
        b.setChecked(v)
        self.view.toggleObjects(v)

    def toggle_wireframe(self):
        b = self.sender()
        v = b.isChecked()
        b.setChecked(v)
        self.view.toggleWireframe(v)

    def toggle_transpassets(self):
        b = self.sender()
        v = b.isChecked()
        b.setChecked(v)
        self.view.toggleTranspAssets(v)

    def zoom(self, direction):
        self.view.modifyDistance(direction)
        if self.debug:
            self.camChanged()

    def zoom_in(self):
        self.zoom(-1)

    def zoom_out(self):
        self.zoom(1)

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
        b = self.persbutton
        v = b.isChecked()
        self.focusSlider.setEnabled(v)
        b.setChecked(v)
        self.view.togglePerspective(v)

    def toggle_perspective_key(self):
        b = self.persbutton
        b.setChecked(not b.isChecked())
        self.toggle_perspective()

    def cleanUp(self):
        self.glob.textureRepo.cleanup("system")
        if self.view is not None:
            self.view.cleanUp()
