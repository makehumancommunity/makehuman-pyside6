"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * AnimMode
    * AnimPlayer
    * ExpressionItem
    * AnimExpressionEdit
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QGroupBox, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from gui.common import IconButton, WorkerThread, ErrorBox, MHFileRequest
from gui.slider import ScaleComboItem, SimpleSlider
from obj3d.animation import FaceUnits, MHPose
import os
import time

class AnimMode():
    """
    used for Poses, Expressions
    """
    def __init__(self, glob):
        self.glob = glob
        self.view = glob.openGLWindow
        self.baseClass = glob.baseClass
        self.mesh = glob.baseClass.baseMesh
        self.mesh.createWCopy()
        self.baseClass.restPose()
        self.baseClass.precalculateAssetsInRestPose()
        self.baseClass.pose_skeleton.newGeometry()
        print ("init pose")
        self.view.prepareSkeleton(True)
        self.baseClass.in_posemode = True
        if self.baseClass.bvh:
            self.baseClass.showPose()
        if self.baseClass.expression:
            self.baseClass.showExpression()
            self.view.Tweak()

    def leave(self):
        self.mesh.resetFromCopy()
        self.baseClass.restPose()
        self.baseClass.updateAttachedAssets()
        self.baseClass.in_posemode = False
        self.view.prepareSkeleton(False)
        self.view.Tweak()


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
        self.loopbutton.setChecked(False)
        self.rotSkyBox.setChecked(False)
        self.mesh.createWCopy()
        self.bc.restPose()
        self.bc.precalculateAssetsInRestPose()
        self.bc.pose_skeleton.newGeometry()
        self.view.prepareSkeleton(True)

        self.view.setRotSkyBox(False)
        self.bc.in_posemode = True
        self.firstframe()

    def leave(self):
        self.view.stopTimer()
        self.view.stopRotate()
        self.view.setYRotation()        # reset to 0.0
        if self.anim:
            self.anim.identFinal()
        self.firstframe()
        self.mesh.resetFromCopy()
        self.bc.in_posemode = False         # must be before prepare skeleton
        self.view.prepareSkeleton(False)    # reset to unposed
        self.bc.updateAttachedAssets()
        self.view.Tweak()

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
        self.setFrame(self.anim.currentFrame - 1)

    def nextframe(self):
        self.setFrame(self.anim.currentFrame + 1)

    def lastframe(self):
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

class ExpressionItem(ScaleComboItem):
    def __init__(self, glob, name, icon, callback, expression):
        super().__init__(name, icon)    # inherit attributs
        self.glob = glob
        self.callback = callback
        self.mat = expression["bones"]
        self.measure = None
        if "group" in expression:
            self.group = expression["group"]

    def initialize(self):
        print ("In ExpressionItem initialize" + self.name)



class AnimExpressionEdit():
    def __init__(self, parent, glob):
        self.glob = glob
        self.view = glob.openGLWindow
        self.env = glob.env
        self.parent = parent
        self.baseClass = glob.baseClass
        self.mesh = glob.baseClass.baseMesh
        self.mesh.createWCopy()
        self.baseClass.restPose()
        self.baseClass.precalculateAssetsInRestPose()
        self.baseClass.pose_skeleton.newGeometry()
        self.view.prepareSkeleton(True)
        self.baseClass.in_posemode = True
        self.expressions = []
        self.thumbimage = None
        self.view.Tweak()

    def addClassWidgets(self):
        layout = QVBoxLayout()

        # photo
        #
        ilayout = QHBoxLayout()
        ilayout.addWidget(IconButton(10,  os.path.join(self.env.path_sysicon, "camera.png"), "create thumbnail", self.thumbnail))
        self.imglabel=QLabel()
        self.displayPixmap()
        ilayout.addWidget(self.imglabel, alignment=Qt.AlignRight)
        layout.addLayout(ilayout)

        # name
        #
        ilayout = QGridLayout()
        ilayout.addWidget(QLabel("Pose name:"), 0, 0)
        self.editname = QLineEdit("Pose")
        ilayout.addWidget(self.editname, 0, 1)

        ilayout.addWidget(QLabel("Author:"), 1, 0)
        self.author = QLineEdit()
        ilayout.addWidget(self.author, 1, 1)

        ilayout.addWidget(QLabel("License:"), 2, 0)
        self.license = QLineEdit("CC0")
        ilayout.addWidget(self.license, 2, 1)

        ilayout.addWidget(QLabel("Tags:"), 3, 0)
        # hint = (separate by ';')
        self.tagsline = QLineEdit()
        self.tagsline.setToolTip("tags to filter, use semicolon to separate if more than one")
        ilayout.addWidget(self.tagsline, 3, 1)
        layout.addLayout(ilayout)

        layout.addWidget(QLabel("Description:"))
        self.description = QLineEdit()
        layout.addWidget(self.description)



        ilayout = QHBoxLayout()
        ilayout.addWidget(IconButton(1,  os.path.join(self.env.path_sysicon, "f_load.png"), "load pose", self.loadButton))
        ilayout.addWidget(IconButton(2,  os.path.join(self.env.path_sysicon, "f_save.png"), "save pose", self.saveButton))
        ilayout.addWidget(IconButton(3,  os.path.join(self.env.path_sysicon, "reset.png"), "reset pose", self.resetButton))
        layout.addLayout(ilayout)
        return (layout)

    def displayPixmap(self):
        if self.thumbimage is None:
            pixmap = QPixmap(os.path.join(self.glob.env.path_sysicon, "empty_models.png"))
        else:
            pixmap = QPixmap.fromImage(self.thumbimage)
        self.imglabel.setPixmap(pixmap)

    def thumbnail(self):
        self.thumbimage = self.view.createThumbnail()
        self.displayPixmap()

    def loadButton(self):
        directory = self.env.stdUserPath("expressions")
        freq = MHFileRequest("Expressions", "expression files (*.mhpose)", directory)
        filename = freq.request()
        if filename is not None:
            pose = MHPose(self.glob, self.glob.baseClass.getFaceUnits(), "dummy")
            (res, text) =  pose.load(filename)
            if res is False:
                ErrorBox(self.parent.central_widget, text)
                return
            self.baseClass.restPose()
            self.editname.setText(pose.name)
            self.description.setText(pose.description)
            self.tagsline.setText(";".join(pose.tags))
            self.author.setText(pose.author)
            self.license.setText(pose.license)
            for elem in self.expressions:
                if elem.name in pose.poses:
                    elem.value =  pose.poses[elem.name] * 100
            self.parent.redrawNewExpression(None)
            self.baseClass.pose_skeleton.posebyBlends(pose.blends, self.baseClass.faceunits.bonemask)
            self.view.Tweak()

    def saveButton(self):
        directory = self.env.stdUserPath("expressions")
        freq = MHFileRequest("Expressions", "expression files (*.mhpose)", directory, save=".mhpose")
        filename = freq.request()
        if filename is not None:
            print ("Save " + filename)
            name = self.editname.text()
            if name == "":
                name= "pose"
            tags = self.tagsline.text().split(";")
            unit_poses = {}
            cnt = 0
            for elem in self.expressions:
                if elem.value != 0.0:
                    unit_poses[elem.name] = elem.value / 100
                    cnt += 1
            if cnt == 0:
                ErrorBox(self.parent.central_widget, "No changes to save as pose.")
                return
            savepose = MHPose(self.glob, self.glob.baseClass.getFaceUnits(), name)
            json = {"name": name, "author": self.author.text(),
                    "licence": self.license.text(), "description": self.description.text(),
                    "tags": tags, "unit_poses": unit_poses }
            if savepose.save(filename, json) is False:
                ErrorBox(self.parent.central_widget, self.env.last_error)

            if self.thumbimage is not None:
                iconpath = filename[:-7] + ".thumb"
                self.thumbimage.save(iconpath, "PNG", -1)


    def resetButton(self):
        self.resetExpressionSliders()
        self.parent.redrawNewExpression(None)
        self.baseClass.restPose()
        self.view.Tweak()

    def fillExpressions(self):
        if len(self.expressions) > 0:
            return(self.expressions)

        funits = self.glob.baseClass.getFaceUnits()
        if funits is None:
            return (expressions)

        default_icon = os.path.join(self.glob.env.path_sysicon, "empty_target.png")
        for elem in funits.units.keys():
            expression = funits.units[elem]
            if "bones" in expression:
                self.expressions.append(ExpressionItem(self.glob, elem, default_icon, self.changedExpressions, expression))
        return(self.expressions)

    def resetExpressionSliders(self):
        for elem in self.expressions:
            elem.value = 0.0

    def changedExpressions(self):
        blends = []
        for elem in self.expressions:
            if elem.value != 0.0:
                blends.append([elem.mat, elem.value])
        self.baseClass.pose_skeleton.posebyBlends(blends, None)
        self.view.Tweak()

    def leave(self):
        self.mesh.resetFromCopy()
        self.baseClass.updateAttachedAssets()
        self.baseClass.in_posemode = False
        self.view.prepareSkeleton(False)
        self.view.Tweak()


