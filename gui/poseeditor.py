"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * PoseItem
    * AnimExpressionEdit
    * AnimPoseEdit
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QGroupBox, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from gui.common import IconButton, ErrorBox, MHFileRequest
from gui.slider import ScaleComboItem
from obj3d.animation import PosePrims, MHPose
import os
import time

class PoseItem(ScaleComboItem):
    def __init__(self, glob, name, icon, callback, pose):
        super().__init__(name, icon)    # inherit attributs
        self.glob = glob
        self.callback = callback
        self.mat = pose["bones"]
        self.measure = None
        if "group" in pose:
            self.group = pose["group"]

    def initialize(self):
        """
        is void for poses
        """
        pass

class GenericPoseEdit():
    def __init__(self, parent, glob, redraw):
        self.glob = glob
        self.view = glob.openGLWindow
        self.env = glob.env
        self.parent = parent
        self.redraw = redraw
        self.baseClass = glob.baseClass
        self.baseClass.setPoseMode()
        self.poses = []
        self.thumbimage = None

    def addClassWidgets(self):
        layout = QVBoxLayout()

        # name
        #
        ilayout = QGridLayout()
        ilayout.addWidget(QLabel("Pose name:"), 0, 0)
        self.editname = QLineEdit("Pose")
        ilayout.addWidget(self.editname, 0, 1)
        ilayout.addWidget(IconButton(3,  os.path.join(self.env.path_sysicon, "reset.png"), "reset pose", self.resetButton))
        layout.addLayout(ilayout)
        return (layout)

    def fillPoses(self, funits):
        if len(self.poses) > 0 or funits is None:
            return(self.poses)

        default_icon = os.path.join(self.glob.env.path_sysicon, "empty_target.png")
        for elem in funits.units.keys():
            poses = funits.units[elem]
            if "bones" in poses:
                self.poses.append(PoseItem(self.glob, elem, default_icon, self.changedPoses, poses))
        return(self.poses)

    def resetPoseSliders(self):
        for elem in self.poses:
            elem.value = 0.0

    def changedPoses(self):
        blends = []
        for elem in self.poses:
            if elem.value != 0.0:
                blends.append([elem.mat, elem.value])

        # change if there are blends, otherwise reset to rest pose
        #
        if len(blends) > 0:
            self.baseClass.pose_skeleton.posebyBlends(blends, None)
        else:
            self.baseClass.restPose()
        self.view.Tweak()

    def resetButton(self):
        self.resetPoseSliders()
        self.redraw(None)
        self.baseClass.restPose()
        self.view.Tweak()

    def leave(self):
        self.baseClass.setStandardMode()

class AnimExpressionEdit(GenericPoseEdit):
    def __init__(self, parent, glob):
        super().__init__(parent, glob, parent.redrawNewExpression)    # inherit attributs

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
        self.editname = QLineEdit("Expression")
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
            for elem in self.poses:
                if elem.name in pose.poses:
                    elem.value =  pose.poses[elem.name] * 100
            self.redraw(None)
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
            for elem in self.poses:
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

    def fillExpressions(self):
        return (super().fillPoses(self.glob.baseClass.getFaceUnits()))


class AnimPoseEdit(GenericPoseEdit):
    def __init__(self, parent, glob):
        super().__init__(parent, glob, parent.redrawNewPose)    # inherit attributs

    def fillPoses(self):
        return (super().fillPoses(self.glob.baseClass.getBodyUnits()))

