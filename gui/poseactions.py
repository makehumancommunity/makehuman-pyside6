"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * AnimMode
    * AnimPlayer
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QGroupBox, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from gui.common import IconButton, WorkerThread, ErrorBox, MHFileRequest
from gui.slider import SimpleSlider
from obj3d.animation import PosePrims, MHPose
import os
import time

class AnimMode():
    """
    used for Poses, Expressions (selections only)
    """
    def __init__(self, glob):
        self.glob = glob
        self.view = glob.openGLWindow
        self.bc = glob.baseClass
        self.bc.setPoseMode()
        self.bc.showPoseAndExpression()
        self.view.Tweak()

    def leave(self):
        self.bc.setStandardMode()

class AnimPlayer(QVBoxLayout):
    """
    create a form with anim-player buttons
    """
    def __init__(self, glob):
        self.glob = glob
        self.view = glob.openGLWindow
        env = glob.env
        self.bc  = glob.baseClass
        self.mesh = self.bc.baseMesh
        self.anim = self.bc.bvh
        self.speedValue = 24
        self.rotAngle = 2
        super().__init__()

        layout = QVBoxLayout()
        if self.anim:
            name = self.anim.name
            frames = self.anim.frameCount
            self.anim.identFinal()
        else:
            name = "(no animation loaded)"
            frames = 0

        gb = QGroupBox("Animation")
        gb.setObjectName("subwindow")

        vlayout = QVBoxLayout()
        vlayout.addWidget(QLabel(name))
        vlayout.addWidget(QLabel("Frames: " + str(frames)))

        ilayout = QHBoxLayout()
        ilayout.addWidget(IconButton(1,  os.path.join(env.path_sysicon, "playerfirstimage.png"), "first frame", self.firstframe))
        ilayout.addWidget(IconButton(2,  os.path.join(env.path_sysicon, "playerprevimage.png"), "previous frame", self.prevframe))
        ilayout.addWidget(IconButton(3,  os.path.join(env.path_sysicon, "playernextimage.png"), "next frame", self.nextframe))
        ilayout.addWidget(IconButton(4,  os.path.join(env.path_sysicon, "playerlastimage.png"), "last frame", self.lastframe))
        self.loopbutton = IconButton(5,  os.path.join(env.path_sysicon, "reset.png"), "toggle animation (ESC = stop animation)", self.loop)
        self.loopbutton.setCheckable(True)
        ilayout.addWidget(self.loopbutton)

        vlayout.addLayout(ilayout)
        if frames > 0:
            self.frameSlider = SimpleSlider("Frame number: ", 0, frames-1, self.frameChanged, minwidth=250)
            self.frameSlider.setSliderValue(self.anim.currentFrame)
            vlayout.addWidget(self.frameSlider )

            self.speedSlider = SimpleSlider("Frames per Second: ", 1, 70, self.speedChanged, minwidth=250)
            self.speedSlider.setSliderValue(self.speedValue)
            vlayout.addWidget(self.speedSlider )

        self.faceanim = QCheckBox("allow face animation")
        self.faceanim.setLayoutDirection(Qt.LeftToRight)
        self.faceanim.setChecked(True)
        self.faceanim.toggled.connect(self.changeFaceAnim)
        vlayout.addWidget(self.faceanim)
        gb.setLayout(vlayout)
        layout.addWidget(gb)

        gb = QGroupBox("Rotator")
        gb.setObjectName("subwindow")
        vlayout = QVBoxLayout()
        ilayout = QHBoxLayout()
        ilayout.addWidget(IconButton(6,  os.path.join(env.path_sysicon, "none.png"), "reset to 0 degrees", self.resetrot))
        self.rotatorbutton = IconButton(7,  os.path.join(env.path_sysicon, "reset.png"), "rotator", self.rotator)
        self.rotatorbutton.setCheckable(True)
        ilayout.addWidget(self.rotatorbutton)
        vlayout.addLayout(ilayout)

        self.rotangSlider = SimpleSlider("Rotation in degrees per frame: ", -20, 20, self.rotangChanged, minwidth=250, factor=0.25)
        self.rotangSlider.setSliderValue(self.rotAngle)
        vlayout.addWidget(self.rotangSlider )

        self.rotSkyBox = QCheckBox("also rotate skybox")
        self.rotSkyBox.setLayoutDirection(Qt.LeftToRight)
        self.rotSkyBox.toggled.connect(self.changeRotSkyBox)
        vlayout.addWidget(self.rotSkyBox)

        gb.setLayout(vlayout)
        layout.addWidget(gb)
        self.addLayout(layout)

    def enter(self):
        self.glob.midColumn.poseViews(True)
        self.loopbutton.setChecked(False)
        self.rotSkyBox.setChecked(False)

        self.bc.setPoseMode()
        self.view.setRotSkyBox(False)
        self.firstframe()

    def leave(self):
        self.view.stopTimer()
        self.view.stopRotate()
        self.view.setYRotation()        # reset to 0.0
        if self.anim:
            self.anim.identFinal()
        self.firstframe()
        self.bc.setStandardMode()
        self.glob.midColumn.poseViews(False)

    def changeFaceAnim(self, param):
        if self.anim:
            if param is False:
                self.anim.noFaceAnimation()
            else:
                self.anim.identFinal()

    def changeRotSkyBox(self, param):
        self.view.setRotSkyBox(param)

    def setFrame(self, value):
        if self.anim is None:
            print ("No file loaded")
            return

        if value < 0:
            return

        if value >= self.anim.frameCount:
            return

        self.anim.currentFrame = value
        self.frameSlider.setSliderValue(value)
        self.bc.showPose()

    def frameChanged(self, value):
        self.setFrame(int(value))

    def speedChanged(self, value):
        self.speedValue = value
        if self.loopbutton.isChecked():
            self.view.setFPS(self.speedValue)

    def rotangChanged(self, value):
        self.rotAngle = value
        if self.rotatorbutton.isChecked():
            self.view.setYRotAngle(self.rotAngle)

    def firstframe(self):
        self.setFrame(0)

    def prevframe(self):
        if self.anim is not None:
            self.setFrame(self.anim.currentFrame - 1)

    def nextframe(self):
        if self.anim is not None:
            self.setFrame(self.anim.currentFrame + 1)

    def lastframe(self):
        if self.anim is not None:
            self.setFrame(self.anim.frameCount -1)

    def frameFeedback(self):
        self.frameSlider.setSliderValue(self.anim.currentFrame)

    def loop(self):
        if self.anim is None:
            print ("No file loaded")
            return
        b = self.sender()
        v = b.isChecked()
        if v:
            self.view.setFPS(self.speedValue, self.resetAnimbutton)
            self.view.startTimer(self.frameFeedback)
        else:
            self.view.stopTimer()
        b.setChecked(v)

    def rotator(self):
        b = self.sender()
        v = b.isChecked()
        if v:
            self.view.setYRotAngle(self.rotAngle, self.resetAnimbutton)
            self.view.startRotate()
        else:
            self.view.stopRotate()
        b.setChecked(v)

    def resetrot(self):
        self.view.setYRotation()    # reset rotation
        self.view.Tweak()

    def resetAnimbutton(self):
        self.rotatorbutton.setChecked(False)
        self.loopbutton.setChecked(False)


