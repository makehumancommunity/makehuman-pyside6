from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QMatrix4x4, QVector3D, QOpenGLContext

# try to keep only constants here
#
import re
import os
from OpenGL import GL as gl
from opengl.info import GLDebug
from opengl.shaders import ShaderRepository
from opengl.material import Material
from opengl.buffers import OpenGlBuffers, RenderedObject
from opengl.camera import Camera, Light
from opengl.skybox import OpenGLSkyBox
from opengl.prims import CoordinateSystem, Grid, BoneList, VisLights, DiamondSkeleton

class OpenGLView(QOpenGLWidget):
    def __init__(self, glob):
        self.glob = glob
        self.env = glob.env
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.setMinimumSize(QSize(300, 560))
        self.setMaximumSize(QSize(2000, 2000))
        self.sysmaterials = []
        self.buffers = []
        self.objects = []
        self.objects_invisible = False
        self.xrayed = False
        self.wireframe = False
        self.prims = {}
        self.camera  = None
        self.skybox = None
        self.framefeedback = None
        self.fps = 24
        self.timer1 = QTimer()
        self.timer2 = QTimer()
        self.timer1.timeout.connect(self.nextFrame)
        self.timer2.timeout.connect(self.yRotator)
        self.yangle = 0.0
        self.yrot = 2.0
        self.resetbuttons = None
        self.rotSkyBox = False
        self.blocked = False
        self.glfunc = None
        self.visLights = None
        self.diamondskel = None

    def delSkeleton(self):
        if "skeleton" in self.prims:
            self.prims["skeleton"].delete()
            del self.prims["skeleton"]
            if self.diamondskel is not None:
                self.diamondskel.delete()

    def setFPS(self, value, callback=None):
        self.fps = value
        if callback is not None:
            self.resetbuttons = callback
        self.timer1.stop()
        self.timer1.start(1000 / self.fps)

    def setYRotAngle(self, value, callback=None):
        self.yrot = value
        if callback is not None:
            self.resetbuttons = callback

    def setRotSkyBox(self, param):
        self.rotSkyBox = param

    def startTimer(self, framefeedback):
        self.framefeedback = framefeedback
        self.timer1.start(1000 / self.fps)

    def stopTimer(self):
        if self.framefeedback is not None:
            self.framefeedback()
        self.timer1.stop()
        self.blocked = False

    def nextFrame(self):
        if self.blocked:
            return
        self.blocked = True
        skeleton = self.glob.baseClass.pose_skeleton
        bvh = self.glob.baseClass.bvh
        # this slows animation down, better way?
        #if self.framefeedback is not None:
        #    self.framefeedback()
        skeleton.pose(bvh.joints, bvh.currentFrame, self.objects_invisible)
        if bvh.currentFrame < (bvh.frameCount-1):
            bvh.currentFrame += 1
        else:
            bvh.currentFrame = 0
        self.Tweak()
        self.blocked = False

    def startRotate(self):
        self.timer2.start(1000 / 24)

    def stopRotate(self):
        self.timer2.stop()
        self.blocked = False

    def yRotator(self):
        if self.blocked:
            return
        self.blocked = True
        self.yangle = self.yangle + self.yrot
        if self.yangle >= 360.0:
            self.yangle = self.yangle - 360.0
        elif self.yangle < 0.0:
            self.yangle = self.yangle + 360.0
        self.setYRotation(float(self.yangle))
        self.Tweak()
        self.blocked = False

    def stopAnimation(self):
        if self.resetbuttons is not None:
            self.resetbuttons()
            self.resetbuttons = None
        self.stopTimer()
        self.blocked = True
        self.stopRotate()

    def addSkeleton(self, pose=False):
        """
        add a white skeleton for the one added to character or pose skeleton in animation mode
        """
        if pose:
            skeleton = self.glob.baseClass.pose_skeleton
            col = [1.0, 0.5, 0.0]
        else:
            skeleton = self.glob.baseClass.skeleton 
            col = [1.0, 1.0, 1.0]

        if "skeleton" in self.prims:
            self.delSkeleton()

        if skeleton is not None:
            shader = self.mh_shaders.getShader("fixcolor")
            self.prims["skeleton"] = BoneList(self.context(), shader, "skeleton", skeleton, col)
            if self.objects_invisible is True:
                self.togglePrims("skeleton", True)
            # self.diamondskel = DiamondSkeleton(self.context(), self.mh_shaders, "diamondskel", skeleton, self.white)

        self.Tweak()

    def toggleObjects(self, status):
        """
        makes objects invisible and switches skeleton to on
        """
        self.objects_invisible = status
        if self.glob.baseClass and (self.glob.baseClass.skeleton or self.glob.baseClass.pose_skeleton):
            self.togglePrims("skeleton", self.objects_invisible)
            self.Tweak()

    def toggleTranspAssets(self, status):
        self.xrayed = status
        if self.glob.baseClass is not None:
            self.Tweak()

    def toggleWireframe(self, status):
        self.wireframe = status
        if self.glob.baseClass is not None:
            self.Tweak()

    def toggleSkybox(self, status):
        self.light.skybox = status
        self.Tweak()

    def togglePrims(self, name, status):
        if name in self.prims:
            self.prims[name].setVisible(status)
            if status is True:
                if name.endswith("grid"):
                    direction = name[:2]
                    baseClass = self.glob.baseClass
                    lowestPos = baseClass.getLowestPos() if self.glob.baseClass is not None else 20
                    self.prims[name].newGeometry(lowestPos, direction)
                elif name == "skeleton":
                    posed = (self.glob.baseClass.bvh is not None) or (self.glob.baseClass.expression is not None)
                    self.prims[name].newGeometry(posed)
            self.Tweak()


    def createPrims(self):
        shader = self.mh_shaders.getShader("fixcolor")
        self.prims["axes"] = CoordinateSystem(self.context(), shader, "axes", 10.0)
        lowestPos = self.glob.baseClass.getLowestPos() if self.glob.baseClass is not None else 20
        self.prims["xygrid"] = Grid(self.context(), shader, "xygrid", 10.0, lowestPos, "xy")
        self.prims["yzgrid"] = Grid(self.context(), shader, "yzgrid", 10.0, lowestPos, "yz")
        self.prims["xzgrid"] = Grid(self.context(), shader, "xzgrid", 10.0, lowestPos, "xz")

        # visualization of lamps (if obj is not found, no lamps are presented)
        #
        self.visLights = VisLights(self, self.light)
        success =self.visLights.setup()
        if not success:
            self.visLights = None

    def compareBoundingBoxes(self, box1, box2):
        n = 0
        for i in range(0,3):
            if box2[i] < box1[i]:
                n += 1
            if box2[i+3] > box1[i+3]:
                n += 1
        return (n>3)

    def createObject(self, obj):
        """
        creates a rendered object and inserts it to a list according to zdepth and, if equal to bounding box
        """
        glbuffer = OpenGlBuffers()
        glbuffer.GetBuffers(obj.gl_coord, obj.gl_norm, obj.gl_uvcoord)
        self.buffers.append(glbuffer)

        boundingbox = obj.boundingBox()

        cnt = 0
        for elem in self.objects:
            if obj.z_depth < elem.z_depth:
                break
            if obj.z_depth == elem.z_depth:
                if (self.compareBoundingBoxes(elem.boundingbox, boundingbox)) is False:
                    break
            cnt += 1
        obj.openGL = RenderedObject(self, obj, boundingbox, glbuffer, pos=QVector3D(0, 0, 0))
        self.objects.insert(cnt, obj.openGL)

    def deleteObject(self,obj):
        obj.openGL.delete()
        if obj.type != "proxy":
            obj.material.freeTextures()
        self.objects.remove(obj.openGL)
        obj.openGL = None

    def setYRotation(self, angle=0.0):
        self.yangle = angle
        for obj in self.objects:
            obj.setYRotation(angle)
        if "skeleton" in self.prims:
            self.prims["skeleton"].setYRotation(angle)
        if self.skybox is not None and self.rotSkyBox is True:
            self.skybox.setYRotation(angle)

    def newSkin(self, obj):
        self.objects[0].setMaterial(obj.material)

    def createSysMaterials(self):
        for name in ("black", "white", "grey"):
            m = Material(self.glob, name, "system")
            self.sysmaterials.append(m)

        self.black = self.sysmaterials[0].uniColor([0.0, 0.0, 0.0])
        self.white = self.sysmaterials[1].uniColor([1.0, 1.0, 1.0])
        self.grey  = self.sysmaterials[2].uniColor([0.5, 0.5, 0.5])

    def initializeGL(self):
        """
        automatically called by PySide6, terminates complete program if shader version < minversion (330)
        """
        self.glfunc = self.context().functions()

        deb = GLDebug()
        if deb.checkVersion() is False:
            self.env.logLine(1, "Shader version is not sufficient, minimum version is " + str(deb.minVersion() + ". Available languages are:") )
            lang = deb.getShadingLanguages()
            for l in lang:
                if l != "":
                    self.env.logLine(1, l)
            exit(20)

        baseClass = self.glob.baseClass
        o_size = baseClass.baseMesh.getHeightInUnits() if baseClass is not None else 20

        self.glfunc.glEnable(gl.GL_DEPTH_TEST)

        # initialize shaders
        #
        self.mh_shaders = ShaderRepository(self.glob)
        self.mh_shaders.loadShaders(["phong3l", "fixcolor", "xray", "litsphere", "pbr", "toon","skybox"])

        self.light = Light(self.mh_shaders, self.glob)
        self.light.setShader()
        self.createSysMaterials()

        self.camera = Camera(self.mh_shaders, o_size)
        self.camera.resizeViewPort(self.width(), self.height())


        if baseClass is not None:
            self.newMesh()

        # create environment
        #
        shader = self.mh_shaders.getShader("skybox")
        self.skybox = OpenGLSkyBox(self.glob, shader, self.glfunc)
        if self.skybox.create(self.light.skyboxname) is False:
            self.skybox = None
        self.createPrims()


    def createThumbnail(self):
        image = self.grabFramebuffer()
        return (image.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def customView(self, direction):
        self.camera.customView(direction)
        self.paintGL()
        self.update()

    def getCamera(self):
        return(self.camera)

    def modifyDistance(self, distance):
        self.camera.modifyDistance(distance)
        self.paintGL()
        self.update()

    def togglePerspective(self, mode):
        self.camera.togglePerspective(mode)
        self.paintGL()
        self.update()

    def arcBallCamStart(self, x, y):
        self.camera.setLastMousePosition(x, y)

    def arcBallCamera(self, x, y):
        self.camera.arcBallRotation(x, y)
        self.paintGL()
        self.update()

    def panning(self, x, y):
        self.camera.panning(x,y)
        self.paintGL()
        self.update()

    def modifyFov(self, value):
        self.camera.setFocalLength(value)
        self.paintGL()
        self.update()

    def paintGL(self):
        if self.glob.openGLBlock:
            # print ("open GL is blocked")
            return 
        c = self.light.glclearcolor
        self.glfunc.glClearColor(c.x(), c.y(), c.z(), c.w())
        self.glfunc.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        proj_view_matrix = QMatrix4x4(self.camera.getProjViewMatrix().copyDataTo())
        baseClass = self.glob.baseClass

        if baseClass is not None and self.objects_invisible is False:
            if baseClass.proxy is True:
                body = self.objects[1]
                asset_start = 2
            else:
                body = self.objects[0]
                asset_start = 1
            if self.wireframe:
                body.drawWireframe(proj_view_matrix, self.black, self.white)
            else:
                body.draw(proj_view_matrix, self.light)

            # either with xray or normal shader draw assets
            #
            for obj in self.objects[asset_start:]:
                if self.wireframe:
                    obj.drawWireframe(proj_view_matrix, self.black, self.white)
                else:
                    obj.draw(proj_view_matrix, self.light, self.xrayed)

        if self.visLights is not None and self.prims["axes"].isVisible():
            self.visLights.draw(proj_view_matrix)

        if self.light.skybox and self.skybox and self.camera.cameraPers:
            self.skybox.draw(proj_view_matrix)

        if self.diamondskel is not None:
            posed = (baseClass.bvh is not None) or (baseClass.expression is not None)
            self.diamondskel.draw(proj_view_matrix, posed)

        if self.objects_invisible is True and "skeleton" in self.prims:
            posed = (baseClass.bvh is not None) or (baseClass.expression is not None)
            self.prims["skeleton"].newGeometry(posed)

        for name in self.prims:
            self.prims[name].draw(proj_view_matrix)

    def Tweak(self):
        for glbuffer in self.buffers:
            glbuffer.Tweak()
        self.paintGL()
        self.update()

    def setCameraCenter(self):
        baseMesh = self.glob.baseClass.baseMesh
        self.camera.setCenter(baseMesh.getCenter(), baseMesh.getHeightInUnits())

    def noGLObjects(self, leavebase=False):
        """
        should be called with block
        """
        for elem in self.glob.baseClass.attachedAssets:
            obj = elem.obj
            if obj.openGL is not None:
                self.deleteObject(obj)

        if leavebase is False:
            obj = self.glob.baseClass.baseMesh
            if obj.openGL is not None:
                self.deleteObject(obj)

        start = 1 if leavebase else 0
        for glbuffer in self.buffers[start:]:
            glbuffer.Delete()
        self.objects = self.objects[:start]
        self.buffers = self.buffers[:start]

    def addAssets(self):
        """
        add all assets to a basemesh
        """
        for elem in self.glob.baseClass.attachedAssets:
            self.createObject(elem.obj)

    def newMesh(self):
        """
        create of complete new mesh with assets
        """
        self.noGLObjects()

        if "skeleton" in self.prims:
            self.prims["skeleton"].delete()
            del self.prims["skeleton"]

        if self.glob.baseClass is not None:
            self.createObject(self.glob.baseClass.baseMesh)
            self.addAssets()
            if self.glob.baseClass.skeleton is not None:
                self.addSkeleton(False)
            self.setCameraCenter()
            self.paintGL()
            self.update()

    def resizeGL(self, w, h):
        self.window_width = w
        self.window_height = h
        self.glfunc.glViewport(0, 0, w, h)
        self.camera.resizeViewPort(w, h)
        self.camera.calculateProjMatrix()

    def cleanUp(self):
        print ("cleanup openGL")
        for m in self.sysmaterials:
            m.freeTextures()
        if self.skybox is not None:
            self.skybox.delete()
            self.skybox = None
