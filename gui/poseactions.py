from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from gui.common import IconButton, WorkerThread
from gui.slider import ScaleComboItem
from obj3d.animation import FaceUnits
import os
import time

class AnimMode():
    def __init__(self, glob, view):
        self.glob = glob
        self.view = view
        self.mesh = glob.baseClass.baseMesh
        self.mesh.createWCopy()

    def leave(self):
        self.mesh.resetFromCopy()
        self.glob.baseClass.updateAttachedAssets()
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
        self.mesh.createWCopy()

    def leave(self):
        self.view.stopTimer()
        self.mesh.resetFromCopy()
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
            self.group = "main|" + expression["group"]

    def initialize(self):
        print ("In ExpressionItem initialize" + self.name)



class AnimExpressionEdit():
    def __init__(self, glob, view):
        self.glob = glob
        self.view = view
        self.mesh = glob.baseClass.baseMesh
        self.mesh.createWCopy()
        self.expressions = []

    def fillExpressions(self):
        self.expressions = []

        funits = self.glob.baseClass.getFaceUnits()
        if funits is None:
            return (expressions)

        default_icon = os.path.join(self.glob.env.path_sysicon, "empty_target.png")
        for elem in funits.units.keys():
            expression = funits.units[elem]
            if "bones" in expression:
                self.expressions.append(ExpressionItem(self.glob, elem, default_icon, self.changedExpressions, expression))
        return(self.expressions)

    def changedExpressions(self):
        blends = []
        for elem in self.expressions:
            if elem.value != 0.0:
                print (elem.name + " is changed")
                blends.append([elem.mat, elem.value])
        self.glob.baseClass.pose_skeleton.posebyBlends(blends)
        self.view.Tweak()

    def leave(self):
        self.mesh.resetFromCopy()
        self.glob.baseClass.updateAttachedAssets()
        self.view.Tweak()


