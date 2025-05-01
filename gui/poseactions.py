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
        self.view.newFloorPosition(posed=True)
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

        self.playerButtons = [
            [None, "playerfirstimage.png", "first frame", self.firstframe, False],
            [None, "playerprevimage.png", "previous frame", self.prevframe, False],
            [None, "playernextimage.png", "next frame", self.nextframe, False],
            [None, "playerlastimage.png", "last frame", self.lastframe, False],
            [None, "reset.png", "toggle animation (ESC = stop animation)", self.loop, True]
        ]
        self.bc  = glob.baseClass
        self.mesh = self.bc.baseMesh
        self.anim = self.bc.bvh
        self.posemod = self.bc.posemodifier
        self.speedValue = 24
        self.rotAngle = 2
        self.looping = False
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

        # generate buttons for player
        #
        ilayout = QHBoxLayout()
        for num, button in enumerate(self.playerButtons):
            button[0] = IconButton(num+1,  os.path.join(env.path_sysicon, button[1]), button[2], button[3])
            button[0].setCheckable(button[4])
            ilayout.addWidget(button[0])

        vlayout.addLayout(ilayout)
        if frames > 1:
            self.frameSlider = SimpleSlider("Frame number: ", 0, frames-1, self.frameChanged, minwidth=250)
            self.frameSlider.setSliderValue(self.anim.currentFrame)
            vlayout.addWidget(self.frameSlider )

            self.speedSlider = SimpleSlider("Frames per Second: ", 1, 70, self.speedChanged, minwidth=250)
            self.speedSlider.setSliderValue(self.speedValue)
            vlayout.addWidget(self.speedSlider )
        else:
            self.frameSlider = None
            self.speedSlider = None

        self.faceAnim = QCheckBox("allow face animation")
        self.faceAnim.setLayoutDirection(Qt.LeftToRight)
        self.faceAnim.setChecked(True)
        self.faceAnim.toggled.connect(self.changeAnim)
        vlayout.addWidget(self.faceAnim)

        self.corrAnim = QCheckBox("overlay corrections")
        self.corrAnim.setLayoutDirection(Qt.LeftToRight)
        self.corrAnim.setChecked(False)
        self.corrAnim.toggled.connect(self.changeAnim)
        vlayout.addWidget(self.corrAnim)

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

    def refreshPlayerButtons(self):
        enable = (self.anim is not None and self.anim.frameCount > 1)
        for button in self.playerButtons:
            button[0].setEnabled(enable)
        self.corrAnim.setEnabled(len(self.bc.bodyposes) > 0)

    def enter(self):
        self.glob.midColumn.poseViews(True)
        self.playerButtons[4][0].setChecked(False)
        self.rotSkyBox.setChecked(False)

        self.bc.setPoseMode()
        self.view.setRotSkyBox(False)
        if self.anim:
            self.firstframe()
        elif self.posemod:
            self.bc.showPose()
        self.view.newFloorPosition(posed=True)
        self.refreshPlayerButtons()

    def leave(self):
        self.view.stopTimer()
        self.view.stopRotate()
        self.view.setYRotation()        # reset to 0.0
        if self.anim:
            self.anim.identFinal()
            self.firstframe()
        self.looping = False
        self.bc.setStandardMode()
        self.glob.midColumn.poseViews(False)

    def changeAnim(self):
        if self.anim:
            feat = int(self.faceAnim.isChecked() | (int (self.corrAnim.isChecked()) << 1))
            if feat == 0:
                self.anim.noFaceAnimation()
            elif feat == 1:
                self.anim.identFinal()
            elif feat == 2:
                self.anim.modCorrections()
                self.anim.noFaceAnimation()
            else:
                self.anim.modCorrections()
            if not self.looping:
                self.bc.showPose()

    def changeRotSkyBox(self, param):
        self.view.setRotSkyBox(param)

    def setFrame(self, value):
        if value < 0 or value >= self.anim.frameCount:
            return

        self.anim.currentFrame = value
        if self.frameSlider:
            self.frameSlider.setSliderValue(value)
        self.bc.showPose()

    def frameChanged(self, value):
        self.setFrame(int(value))

    def speedChanged(self, value):
        self.speedValue = value
        if self.playerButtons[4][0].isChecked():
            self.view.setFPS(self.speedValue)

    def rotangChanged(self, value):
        self.rotAngle = value
        if self.rotatorbutton.isChecked():
            self.view.setYRotAngle(self.rotAngle)

    def firstframe(self):
        self.setFrame(0)

    def prevframe(self):
        self.setFrame(self.anim.currentFrame - 1)

    def nextframe(self):
        self.setFrame(self.anim.currentFrame + 1)

    def lastframe(self):
        self.setFrame(self.anim.frameCount -1)

    def frameFeedback(self):
        self.frameSlider.setSliderValue(self.anim.currentFrame)

    def loop(self):
        b = self.sender()
        v = b.isChecked()
        if v:
            self.looping = True
            self.view.setFPS(self.speedValue, self.resetAnimbutton)
            self.view.startTimer(self.frameFeedback)
        else:
            self.looping = False
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
        self.playerButtons[4][0].setChecked(False)


