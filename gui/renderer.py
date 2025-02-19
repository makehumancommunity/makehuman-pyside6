"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QGridLayout, QLabel, QMessageBox,  QCheckBox

from gui.common import IconButton, MHFileRequest, MHBusyWindow, WorkerThread
from gui.slider import SimpleSlider

from opengl.buffers import PixelBuffer
from core.loopapproximation import LoopApproximation

import os

class Renderer(QVBoxLayout):
    """
    should do with a few methods in background
    """
    def __init__(self, parent, glob):
        super().__init__()
        self.parent = parent
        self.glob = glob
        self.env = glob.env
        self.view = glob.openGLWindow
        self.bc  = glob.baseClass
        self.mesh = self.bc.baseMesh
        self.anim = self.bc.bvh

        self.image = None
        self.transparent = False
        self.subdiv = False

        self.prog_window = None     # progressbar

        # store used n_objects (used for unsubdividing)
        #
        self.n_objects = []
        if self.bc.proxy is None:
            self.n_objects.append(self.bc.baseMesh)
        for elem in self.glob.baseClass.attachedAssets:
            self.n_objects.append(elem.obj)

        # subdivided objects
        self.s_objects = []

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

        self.subdivbutton = QPushButton("Smooth (subdivided)")
        self.subdivbutton.clicked.connect(self.toggleSmooth)
        self.subdivbutton.setCheckable(True)
        self.subdivbutton.setChecked(False)
        self.subdivbutton.setToolTip("select all other options before using subdivision!")
        self.addWidget(self.subdivbutton)

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
        self.glob.midColumn.renderView(True)

    def setUnsubdivided(self):
        self.subdivbutton.setChecked(False)
        if self.subdiv:
            self.unSubdivide()
            self.subdiv = False

    def leave(self):
        self.setUnsubdivided()

        if self.anim and self.posed:
            self.setFrame(0)
            self.mesh.resetFromCopy()
            self.view.addSkeleton(False)
            self.bc.updateAttachedAssets()

        self.view.Tweak()
        self.glob.midColumn.renderView(False)

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
        self.setUnsubdivided()
        self.setFrame(int(value))

    def changeTransparency(self, param):
        self.transparent = param

    def changePosed(self, param):
        if self.posed:
            self.leave()
        else:
            self.setUnsubdivided()
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

    def Subdivide(self, bckproc, *args):
        """
        replaces meshes
        """
        self.s_objects = []
        if self.bc.proxy is None:
            self.prog_window.setLabelText("Subdiving basemesh")
            sobj = LoopApproximation(self.glob, self.bc.baseMesh)
            self.bc.baseMesh = sobj.doCalculation()
            self.s_objects.append(self.bc.baseMesh)
            #self.view.createObject(self.bc.baseMesh)

        for elem in self.glob.baseClass.attachedAssets:
            self.prog_window.setLabelText("Subdiving " + elem.obj.name)
            sobj = LoopApproximation(self.glob, elem.obj)
            elem.obj = sobj.doCalculation()
            self.s_objects.append(elem.obj)
            #self.view.createObject(elem.obj)


    def finishSubdivide(self):
        if self.prog_window is not None:
            self.prog_window.progress.close()
            self.prog_window = None
            for obj in self.s_objects:
                self.view.createObject(obj)
            self.glob.openGLBlock = False
            self.view.Tweak()
            self.glob.parallel = None

    def parSubdivide(self):
        if self.glob.parallel is None:
            self.prog_window = MHBusyWindow("Subdivision", "start")
            self.prog_window.progress.forceShow()
            self.glob.openGLBlock = True
            if self.bc.proxy is None:
                self.view.noGLObjects()
            else:
                self.view.noGLObjects(leavebase=True)
            self.glob.parallel = WorkerThread(self.Subdivide)
            self.glob.parallel.start()
            self.glob.parallel.finished.connect(self.finishSubdivide)


    def unSubdivide(self):
        """
        replaces meshes back to normal
        """
        self.glob.openGLBlock = True

        if self.bc.proxy is None:
            self.view.noGLObjects()
            self.bc.baseMesh = self.n_objects[0]
            self.view.createObject(self.bc.baseMesh)
            n = 1
        else:
            self.view.noGLObjects(leavebase=True)
            n = 0

        for elem in self.glob.baseClass.attachedAssets:
            elem.obj = self.n_objects[n]
            self.view.createObject(elem.obj)
            n +=1
        self.glob.openGLBlock = False
        self.view.Tweak()

    def toggleSmooth(self):
        b = self.sender()
        self.subdiv = b.isChecked()
        if self.subdiv:
            self.parSubdivide()
        else:
            self.unSubdivide()

    def render(self):
        width  = int(self.width.text())
        height = int(self.height.text())

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


