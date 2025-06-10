"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * PoseItem
    * GenericPoseEdit
    * AnimExpressionEdit
    * AnimPoseEdit
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QGroupBox, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from gui.common import IconButton, ErrorBox, HintBox, MHFileRequest
from gui.slider import ScaleComboItem, SimpleSlider
from obj3d.animation import PosePrims, MHPose, MHPoseFaceConverter
import os
import time

class PoseItem(ScaleComboItem):
    def __init__(self, glob, name, icon, callback, pose):
        super().__init__(name, icon)    # inherit attributs
        self.glob = glob
        self.callback = callback
        if "reverse" in pose:
            self.opposite = True
            self.rmat = pose["reverse"]
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
    def __init__(self, parent, glob, poses, redraw, units, infos, mask):
        self.glob = glob
        self.parent = parent
        self.redraw = redraw
        self.units = units
        self.infos = infos
        self.bonemask = mask
        self.view = glob.openGLWindow
        self.env = glob.env
        self.baseClass = glob.baseClass
        self.baseClass.setPoseMode()
        self.bvh = self.baseClass.bvh
        self.poses = poses
        self.preposed = False
        self.thumbimage = None

    def addClassWidgets(self, default):
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
        self.editname = QLineEdit(default)
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

        if self.bvh:
            self.posedButton = IconButton(1,  os.path.join(self.env.path_sysicon, "an_pose.png"), "character posed", self.togglePosed, checkable=True)
            ilayout = QHBoxLayout()
            ilayout.addWidget(self.posedButton)

            if self.bvh and self.bvh.frameCount > 1:
                self.frameSlider = SimpleSlider("Frame number: ", 0, self.bvh.frameCount-1, self.frameChanged, minwidth=250)
                self.frameSlider.setSliderValue(self.bvh.currentFrame)
                self.frameSlider.setEnabled(self.preposed)
                ilayout.addWidget(self.frameSlider)
            else:
                ilayout.addStretch()

            layout.addLayout(ilayout)


        ilayout = QHBoxLayout()
        ilayout.addWidget(IconButton(1,  os.path.join(self.env.path_sysicon, "f_load.png"), "load pose", self.loadButton))
        ilayout.addWidget(IconButton(2,  os.path.join(self.env.path_sysicon, "f_save.png"), "save pose", self.saveButton))
        ilayout.addWidget(IconButton(3,  os.path.join(self.env.path_sysicon, "reset.png"), "reset pose", self.resetButton))
        ilayout.addWidget(IconButton(4,  os.path.join(self.env.path_sysicon, "symm1.png"), "mirror from right to left", self.rightSymm))
        ilayout.addWidget(IconButton(5,  os.path.join(self.env.path_sysicon, "symm2.png"), "mirror from left to right", self.leftSymm))
        ilayout.addWidget(IconButton(6,  os.path.join(self.env.path_sysicon, "corr_bone.png"), "push to corrections", self.pushCorrections))
        layout.addLayout(ilayout)
        self.changedPoses()
        return (layout)

    def displayPixmap(self):
        if self.thumbimage is None:
            pixmap = QPixmap(os.path.join(self.glob.env.path_sysicon, "empty_models.png"))
        else:
            pixmap = QPixmap.fromImage(self.thumbimage)
        self.imglabel.setPixmap(pixmap)

    def setFrame(self, value):
        if self.bvh is None or value < 0 or value >= self.bvh.frameCount:
            return

        self.bvh.currentFrame = value
        self.baseClass.showPose()

    def showCorrectedPose(self):
        blends = self.getChangedValues()
        corrections = {}
        changed = self.baseClass.pose_skeleton.posebyBlends(blends, None)
        if len(blends) > 0:
            for bone in changed:
                elem = self.baseClass.pose_skeleton.bones[bone]
                corrections[bone] = elem.getRelativeCorrection()
            self.bvh.modCorrections(corrections)
        else:
            # no blends at all, reset
            #
            self.bvh.identFinal()
        self.baseClass.showPose()

    def togglePosed(self, param):
        self.preposed = param
        if param is False:
            self.baseClass.restPose()
            blends = self.getChangedValues()
            if len(blends) > 0:
                self.baseClass.pose_skeleton.posebyBlends(blends, None)
        else:
            self.showCorrectedPose()
        if self.bvh.frameCount > 1:
            self.frameSlider.setEnabled(param)
        self.view.Tweak()

    def frameChanged(self, value):
        self.setFrame(int(value))

    def fillPoses(self):

        # in case poses are already filled, change callback!
        #
        if len(self.poses) > 0 or self.units is None:
            for elem in self.poses:
                elem.callback = self.changedPoses
            return(self.poses)

        default_icon = os.path.join(self.glob.env.path_sysicon, "empty_target.png")
        for elem in self.units.units.keys():
            poses = self.units.units[elem]
            if "bones" in poses:
                self.poses.append(PoseItem(self.glob, elem, default_icon, self.changedPoses, poses))
        return(self.poses)

    def resetPoseSliders(self):
        for elem in self.poses:
            elem.value = 0.0

    def getChangedValues(self):
        blends = []
        for elem in self.poses:
            if elem.value < 0.0:
                blends.append([elem.rmat, -elem.value])
            elif elem.value > 0.0:
                blends.append([elem.mat, elem.value])
        return blends

    def changedPoses(self):

        # change if there are blends, otherwise reset to rest pose
        #
        if self.preposed:
            self.showCorrectedPose()
        else:
            blends = self.getChangedValues()
            if len(blends) > 0:
                self.baseClass.pose_skeleton.posebyBlends(blends, None)
            else:
                self.baseClass.restPose()
        self.view.Tweak()

    def thumbnail(self):
        self.thumbimage = self.view.createThumbnail()
        self.displayPixmap()

    def resetButton(self):
        self.resetPoseSliders()
        self.redraw(None)
        if self.preposed:
            self.bvh.identFinal()
            self.baseClass.showPose()
        else:
            self.baseClass.restPose()
        self.view.Tweak()

    def getValue(self, name):
        for elem in self.poses:
            if elem.name == name:
                return elem.value
        return 0

    def setValue(self, name, value):
        for elem in self.poses:
            if elem.name == name:
                elem.value = value
                return

    def Symm(self, sym):
        for key, elem in self.infos.items():
            if sym in elem:
                v = self.getValue(key)
                okey = elem[sym]
                self.setValue(okey, v)
        self.changedPoses()
        self.redraw(None)

    def rightSymm(self):
        self.Symm("lsym")

    def leftSymm(self):
        self.Symm("rsym")

    def pushCorrections(self):
        corrections = {}
        blends = self.getChangedValues()

        # get corrections before, if not in bonemask, keep them
        #
        for bone, elem in self.baseClass.posecorrections.items():
            if bone not in self.bonemask:
                corrections[bone] = elem

        if len(blends) == 0:

            # reset these corrections
            #
            self.baseClass.posecorrections = corrections
            HintBox(self.parent.central_widget, "Corrections reset")
            return

        changed = self.baseClass.pose_skeleton.posebyBlends(blends, self.bonemask, True)
        for bone in changed:
            elem = self.baseClass.pose_skeleton.bones[bone]
            corrections[bone] = elem.getRelativeCorrection()

        self.baseClass.posecorrections = corrections
        HintBox(self.parent.central_widget, "Corrections added to be used in animation.")

    def loadButton(self, path, convert=None):
        directory = self.env.stdUserPath(path)
        freq = MHFileRequest(path.capitalize(), path + " files (*.mhpose)", directory)
        filename = freq.request()
        if filename is not None:
            pose = MHPose(self.glob, self.units, "dummy")
            (res, text) =  pose.load(filename, convert)
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
            self.baseClass.pose_skeleton.posebyBlends(pose.blends, self.bonemask)
            self.view.Tweak()

            iconpath = filename[:-7] + ".thumb"
            if os.path.isfile(iconpath):
                pixmap = QPixmap(iconpath)
                self.thumbimage = pixmap.toImage()
                self.displayPixmap()


    def saveButton(self, path):
        directory = self.env.stdUserPath(path)
        freq = MHFileRequest(path.capitalize(), path + " files (*.mhpose)", directory, save=".mhpose")
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
            savepose = MHPose(self.glob, self.units, name)
            json = {"name": name, "author": self.author.text(),
                    "licence": self.license.text(), "description": self.description.text(),
                    "tags": tags, "unit_poses": unit_poses }
            if savepose.save(filename, json) is False:
                ErrorBox(self.parent.central_widget, self.env.last_error)

            if self.thumbimage is not None:
                iconpath = filename[:-7] + ".thumb"
                self.thumbimage.save(iconpath, "PNG", -1)

    def leave(self):
        self.setFrame(0)
        if self.bvh:
            self.bvh.identFinal()
        self.baseClass.setStandardMode()
        self.preposed = False

class AnimExpressionEdit(GenericPoseEdit):
    def __init__(self, parent, glob):
        poses = glob.baseClass.faceposes
        units = glob.baseClass.getFaceUnits()
        infos = glob.baseClass.faceunitsinfo
        mask  = glob.baseClass.faceunits.bonemask
        super().__init__(parent, glob, poses, parent.redrawNewExpression, units, infos, mask)

    def addClassWidgets(self):
        return(super().addClassWidgets("Expression"))

    def loadButton(self):
        converter = MHPoseFaceConverter()
        super().loadButton("expressions", converter.convert)

    def saveButton(self):
        super().saveButton("expressions")

    def fillExpressions(self):
        return (super().fillPoses())


class AnimPoseEdit(GenericPoseEdit):
    def __init__(self, parent, glob):
        poses = glob.baseClass.bodyposes
        units = glob.baseClass.getBodyUnits()
        infos = glob.baseClass.bodyunitsinfo
        mask  = glob.baseClass.bodyunits.bonemask
        super().__init__(parent, glob, poses, parent.redrawNewPose, units, infos, mask)

    def fillPoses(self):
        return (super().fillPoses())

    def addClassWidgets(self):
        return(super().addClassWidgets("Pose"))

    def saveButton(self):
        super().saveButton("poses")

    def loadButton(self):
        super().loadButton("poses")

