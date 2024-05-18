from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from gui.common import IconButton, WorkerThread, ErrorBox
from gui.slider import ScaleComboItem
from obj3d.animation import FaceUnits, MHPose
import os
import time

class AnimMode():
    """
    used for Poses, Expressions
    """
    def __init__(self, glob, view):
        self.glob = glob
        self.view = view
        self.baseClass = glob.baseClass
        self.mesh = glob.baseClass.baseMesh
        self.mesh.createWCopy()
        self.baseClass.pose_skeleton.newJointPos()
        self.baseClass.pose_skeleton.restPose()
        self.view.addSkeleton(True)
        if self.baseClass.bvh:
            self.baseClass.showPose()
        if self.baseClass.expression:
            self.baseClass.pose_skeleton.posebyBlends(self.baseClass.expression.blends, self.baseClass.faceunits.bonemask)
            self.view.Tweak()

    def leave(self):
        self.mesh.resetFromCopy()
        self.baseClass.updateAttachedAssets()
        self.view.addSkeleton(False)
        self.view.Tweak()


class AnimPlayer(QVBoxLayout):
    """
    create a form with anim-player buttons (dummy)
    """
    def __init__(self, glob, view):
        self.glob = glob
        self.view = view
        env = glob.env
        self.bc  = glob.baseClass
        self.mesh = self.bc.baseMesh
        self.anim = self.bc.bvh
        super().__init__()

        ilayout = QHBoxLayout()
        ilayout.addWidget(IconButton(1,  os.path.join(env.path_sysicon, "minus.png"), "previous frame", self.prevframe))
        ilayout.addWidget(IconButton(2,  os.path.join(env.path_sysicon, "plus.png"), "next frame", self.nextframe))
        self.loopbutton = IconButton(3,  os.path.join(env.path_sysicon, "reset.png"), "toggle animation", self.loop)
        self.loopbutton.setCheckable(True)
        ilayout.addWidget(self.loopbutton)
        self.addLayout(ilayout)

    def enter(self):
        self.loopbutton.setChecked(False)
        self.view.addSkeleton(True)
        self.bc.pose_skeleton.newJointPos()
        self.mesh.createWCopy()

    def leave(self):
        self.view.stopTimer()
        self.mesh.resetFromCopy()
        self.view.addSkeleton(False)
        self.bc.updateAttachedAssets()
        self.view.Tweak()

    def prevframe(self):
        if self.anim is None:
            print ("No file loaded")
            return
        if self.anim.currentFrame > 0:
            self.anim.currentFrame -= 1
            self.bc.showPose()

    def nextframe(self):
        if self.anim is None:
            print ("No file loaded")
            return
        if self.anim.currentFrame < self.anim.frameCount -1:
            self.anim.currentFrame += 1
            self.bc.showPose()

    def loop(self):
        if self.anim is None:
            print ("No file loaded")
            return
        b = self.sender()
        v = b.isChecked()
        if v:
            self.view.startTimer()
        else:
            self.view.stopTimer()
        b.setChecked(v)

class ExpressionItem(ScaleComboItem):
    def __init__(self, glob, name, icon, callback, expression):
        super().__init__(name, icon)    # inherit attributs
        self.glob = glob
        self.callback = callback
        self.mat = expression["bones"]
        if "group" in expression:
            self.group = expression["group"]

    def initialize(self):
        print ("In ExpressionItem initialize" + self.name)



class AnimExpressionEdit():
    def __init__(self, parent, glob, view):
        self.glob = glob
        self.view = view
        self.env = glob.env
        self.parent = parent
        self.baseClass = glob.baseClass
        self.mesh = glob.baseClass.baseMesh
        self.mesh.createWCopy()
        self.view.addSkeleton(True)
        self.baseClass.pose_skeleton.newJointPos()
        self.baseClass.pose_skeleton.restPose()
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
        filename = self.parent.fileRequest("Expressions", "expression files (*.mhpose)", directory)
        if filename is not None:
            pose = MHPose(self.glob, self.glob.baseClass.getFaceUnits(), "dummy")
            (res, text) =  pose.load(filename)
            if res is False:
                ErrorBox(self.parent.central_widget, text)
                return
            self.baseClass.pose_skeleton.restPose()
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
        filename = self.parent.fileRequest("Expressions", "expression files (*.mhpose)", directory, save=".mhpose")
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
        self.baseClass.pose_skeleton.restPose()
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
                print (elem.name + " is changed")
                blends.append([elem.mat, elem.value])
        self.baseClass.pose_skeleton.posebyBlends(blends, None)
        self.view.Tweak()

    def leave(self):
        self.mesh.resetFromCopy()
        self.baseClass.updateAttachedAssets()
        self.view.addSkeleton(False)
        self.view.Tweak()


