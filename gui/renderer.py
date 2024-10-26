from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QGridLayout, QLabel, QMessageBox,  QCheckBox

from gui.common import IconButton, MHFileRequest
from gui.slider import SimpleSlider

from opengl.buffers import PixelBuffer
from core.loopapproximation import LoopApproximation

import os

class Renderer(QVBoxLayout):
    """
    should do with a few methods in background
    """
    def __init__(self, parent, glob, view):
        super().__init__()
        self.parent = parent
        self.glob = glob
        self.env = glob.env
        self.view = view
        self.bc  = glob.baseClass
        self.mesh = self.bc.baseMesh
        self.anim = self.bc.bvh

        self.image = None
        self.transparent = False
        self.subdiv = False

        glayout = QGridLayout()
        glayout.addWidget(QLabel("Width"), 0, 0)
        self.width = QLineEdit("1000")
        self.width.editingFinished.connect(self.acceptIntegers)
        glayout.addWidget(self.width, 0, 1)

        glayout.addWidget(QLabel("Height"), 1, 0)
        self.height = QLineEdit("1000")
        self.height.editingFinished.connect(self.acceptIntegers)
        glayout.addWidget(self.height, 1, 1)
        self.addLayout(glayout)

        self.transButton = QCheckBox("transparent canvas")
        self.transButton.setLayoutDirection(Qt.LeftToRight)
        self.transButton.toggled.connect(self.changeTransparency)
        self.addWidget(self.transButton)

        self.subdivButton = QCheckBox("smooth mesh")
        self.subdivButton.setLayoutDirection(Qt.LeftToRight)
        self.subdivButton.toggled.connect(self.smoothMesh)
        self.addWidget(self.subdivButton)

        if self.anim:
            self.posed = True
            self.posedButton = QCheckBox("character posed")
            self.posedButton.setLayoutDirection(Qt.LeftToRight)
            self.posedButton.toggled.connect(self.changePosed)
            self.addWidget(self.posedButton)

            if self.anim.frameCount > 1:
                self.frameSlider = SimpleSlider("Frame number: ", 0, self.anim.frameCount-1, self.frameChanged, minwidth=250)
                self.frameSlider.setSliderValue(self.anim.currentFrame)
                self.addWidget(self.frameSlider )
        else:
            self.posed = False

        button = QPushButton("Render")
        button.clicked.connect(self.render)
        self.addWidget(button)

        self.saveButton = IconButton(1,  os.path.join(self.env.path_sysicon, "f_save.png"), "save image", self.saveImage)
        self.addWidget(self.saveButton)
        self.setButtons()

    def enter(self):
        if self.anim:
            self.view.addSkeleton(True)
            self.bc.pose_skeleton.newGeometry()
            self.mesh.createWCopy()
            self.setFrame(0)

    def leave(self):
        if self.subdiv:
            if self.bc.proxy is None:
                self.view.noGLObjects()
                self.view.createObject(self.bc.baseMesh)
            else:
                self.view.noGLObjects(leavebase=True)

            for elem in self.glob.baseClass.attachedAssets:
                self.view.createObject(elem.obj)


        if self.anim and self.posed:
            self.setFrame(0)
            self.mesh.resetFromCopy()
            self.view.addSkeleton(False)
            self.bc.updateAttachedAssets()


        self.view.Tweak()

    def setFrame(self, value):
        if self.anim is None:
            print ("No file loaded")
            return

        if value < 0:
            return

        if value >= self.anim.frameCount:
            return

        self.anim.currentFrame = value
        if self.anim.frameCount > 1:
            self.frameSlider.setSliderValue(value)
        self.bc.showPose()

    def frameChanged(self, value):
        self.setFrame(int(value))

    def changeTransparency(self, param):
        self.transparent = param

    def smoothMesh(self, param):
        self.subdiv = param

    def changePosed(self, param):
        if self.posed:
            self.leave()
        else:
            self.enter()
        self.posed = param

    def setButtons(self):
        self.saveButton.setEnabled(self.image is not None)
        self.transButton.setChecked(self.transparent)
        if self.anim:
            self.posedButton.setChecked(self.posed)

    def acceptIntegers(self):
        m = self.sender()
        try:
            i = int(m.text())
        except ValueError:
            m.setText("1000")
        else:
            if i < 64:
                i = 64
            elif i > 4096:
                i = 4096
            m.setText(str(i))

    def subdivideObjects(self):
        self.glob.openGLBlock = True

        if self.bc.proxy is None:
            self.view.noGLObjects()
            sobj = LoopApproximation(self.glob, self.bc.baseMesh)
            sobj.doCalculation()
        else:
            self.view.noGLObjects(leavebase=True)

        for elem in self.glob.baseClass.attachedAssets:
            sobj = LoopApproximation(self.glob, elem.obj)
            sobj.doCalculation()
        self.glob.openGLBlock = False

    def render(self):
        width  = int(self.width.text())
        height = int(self.height.text())
        if self.subdiv:
            self.subdivideObjects()

        pix = PixelBuffer(self.glob, self.view, self.transparent)
        #self.glob.openGLBlock = True
        pix.getBuffer(width, height)
        self.image = pix.bufferToImage()
        pix.releaseBuffer()
        self.setButtons()
        #self.glob.openGLBlock = False

    def saveImage(self):
        directory = self.env.stdUserPath()
        freq = MHFileRequest("Image (PNG)", "image files (*.png)", directory, save=".png")
        filename = freq.request()
        if filename is not None:
            self.image.save(filename, "PNG", -1)
            QMessageBox.information(self.parent.central_widget, "Done!", "Image saved as " + filename)


