"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck
"""
from PySide6.QtWidgets import (
        QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy, QLabel,
        QSlider, QCheckBox, QMessageBox, QGridLayout
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
        self.buttons = [ 
            [None, "Top",   "top.png",   self.top_button,   0, 1, False],
            [None, "Left",  "left.png",  self.left_button,  1, 0, False],
            [None, "Front", "front.png", self.front_button, 1, 1, False],
            [None, "Right", "right.png", self.right_button, 1, 2, False],
            [None, "Back",  "back.png",  self.back_button,  1, 3, False],
            [None, "Bottom","bottom.png",self.bottom_button,2, 1, False],
            [None, "Axes","3dcoord.png", self.toggle_axes,  3, 0, True ],
            [None, "XY-Grid","xygrid.png", self.toggle_grid,3, 1, True ],
            [None, "YZ-Grid","yzgrid.png", self.toggle_grid,3, 2, True ],
            [None, "Floor-Grid","xzgrid.png", self.toggle_grid, 3, 3, True ],
            [None, "Show hidden vertices", "unhide.png", self.changeHidden, 4, 0, True ],
            [None, "Visualize skeleton", "an_skeleton.png", self.toggle_objects, 4, 1, True ],
            [None, "Visualize mesh", "eq_proxy.png", self.toggle_wireframe, 4, 2, True ],
            [None, "Visualize hidden geometry", "ghost.png", self.toggle_transpassets, 4, 3, True ],
            [None, "Perspective", "persp.png", self.toggle_perspective, 5, 0, True ],
            [None, "Skybox","skybox.png",self.toggle_skybox, 5, 1, True ],
            [None, "Recalculate normals","normals.png",self.recalc_normals, 5, 2, False ],
            [None, "Grab screen", "camera.png",  self.screenShot, 5, 3, False]
        ]

        # create a grid layout for the buttons and generate them from array
        #
        glayout = QGridLayout()
        glayout.setSpacing(1)

        for i in range(len(self.buttons)):
            r = self.buttons[i]
            r[0] = IconButton(i, os.path.join(self.env.path_sysicon, r[2]), r[1], r[3], checkable=r[6])
            glayout.addWidget(r[0], r[4], r[5])


        # now prepare hidden vertices
        #
        self.renderView(False)
        if self.glob.baseClass is not None and self.glob.baseClass.hide_verts is False:
            self.buttons[10][0].setChecked(True)

        # skybox and perspective are checked
        #
        self.buttons[14][0].setChecked(True)
        self.buttons[15][0].setChecked(True)

        vlayout.addLayout(glayout)

        self.focusSlider = SimpleSlider("Focal Length: ", 15, 200, self.focusChanged)
        vlayout.addWidget(self.focusSlider )

    def renderView(self, param):
        hbutton = self.buttons[10][0]
        if param:
            hbutton.setEnabled(False)
            hbutton.setToolTip('hidden geometry cannot be changed in render view')
        else:
            hbutton.setEnabled(True)
            hbutton.setToolTip('do not delete vertices under clothes')

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

    def recalc_normals(self):
        if self.glob.baseClass is not None:
            self.glob.baseClass.updateNormals()

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
        b = self.buttons[14][0]
        v = b.isChecked()
        self.focusSlider.setEnabled(v)
        b.setChecked(v)
        self.view.togglePerspective(v)

    def toggle_perspective_key(self):
        b = self.buttons[14][0]
        b.setChecked(not b.isChecked())
        self.toggle_perspective()

    def cleanUp(self):
        self.glob.textureRepo.cleanup("system")
        if self.view is not None:
            self.view.cleanUp()
