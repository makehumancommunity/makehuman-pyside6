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
from opengl.prims import CoordinateSystem, Grid, BoneList

class OpenGLView(QOpenGLWidget):
    def __init__(self, glob):
        self.glob = glob
        self.env = glob.env
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.setMinimumSize(QSize(300, 560))
        self.setMaximumSize(QSize(2000, 2000))
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
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextFrame)
        self.blocked = False
        self.glfunc = None

    def delSkeleton(self):
        if "skeleton" in self.prims:
            self.prims["skeleton"].delete()
            del self.prims["skeleton"]
            self.Tweak()

    def setFPS(self, value):
        self.fps = value
        self.timer.stop()
        self.timer.start(1000 / self.fps)

    def startTimer(self, framefeedback):
        self.framefeedback = framefeedback
        self.timer.start(1000 / self.fps)

    def stopTimer(self):
        if self.framefeedback is not None:
            self.framefeedback()
        self.timer.stop()
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
            self.prims["skeleton"].delete()
            del self.prims["skeleton"]

        if skeleton is not None:
            self.prims["skeleton"] = BoneList("skeleton", skeleton, col, self.context(), self.mh_shaders._shaders[1])
            if self.objects_invisible is True:
                self.togglePrims("skeleton", True)
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
        self.prims["axes"] = CoordinateSystem("axes", 10.0, self.context(), self.mh_shaders._shaders[1])
        lowestPos = self.glob.baseClass.getLowestPos() if self.glob.baseClass is not None else 20
        self.prims["xygrid"] = Grid("xygrid", 10.0, lowestPos, self.context(), self.mh_shaders._shaders[1], "xy")
        self.prims["yzgrid"] = Grid("yzgrid", 10.0, lowestPos, self.context(), self.mh_shaders._shaders[1], "yz")
        self.prims["xzgrid"] = Grid("xzgrid", 10.0, lowestPos, self.context(), self.mh_shaders._shaders[1], "xz")

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
        obj.openGL = RenderedObject(self.glob, self.context(), obj, boundingbox, glbuffer, pos=QVector3D(0, 0, 0))
        self.objects.insert(cnt, obj.openGL)

    def deleteObject(self,obj):
        obj.openGL.delete()
        if obj.type != "proxy":
            obj.material.freeTextures()
        self.objects.remove(obj.openGL)
        self.Tweak()
        obj.openGL = None

    def newSkin(self, obj):
        self.objects[0].setMaterial(obj.material)

    def initializeGL(self):
        """
        automatically called by PySide6, terminates complete program if shader version < minversion (330)
        """
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
        self.glfunc = self.context().functions()

        self.glfunc.glEnable(gl.GL_DEPTH_TEST)

        #
        # load shaders and get  positions of variables 
        #
        self.mh_shaders = ShaderRepository(self.glob)

        for shader in ["phong3l", "fixcolor", "xray"]:
            s = self.mh_shaders.loadShaders(shader)
            self.mh_shaders.attribVertShader(s)
            self.mh_shaders.getUniforms(s)

        skb = self.mh_shaders.loadShaders("skybox")

        self.light = Light(self.mh_shaders, self.glob)
        self.light.setShader()

        self.camera = Camera(self.mh_shaders, o_size)
        self.camera.resizeViewPort(self.width(), self.height())

        self.blackmat = Material(self.glob, "black", "system")
        self.black = self.blackmat.emptyTexture(rgb = [0.0, 0.0, 0.0], noglob=True)
        self.whitemat = Material(self.glob, "white", "system")
        self.white = self.whitemat.emptyTexture(rgb = [1.0, 1.0, 1.0], noglob=True)

        if baseClass is not None:
            self.newMesh()

        self.skybox = OpenGLSkyBox(self.env, self.mh_shaders._shaders[skb], self.glfunc)
        self.skybox.create()
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
        proj_view_matrix = self.camera.getProjViewMatrix()
        baseClass = self.glob.baseClass

        if baseClass is not None and self.objects_invisible is False:
            if baseClass.proxy is True:
                body = self.objects[1]
                asset_start = 2
            else:
                body = self.objects[0]
                asset_start = 1
            if self.wireframe:
                body.drawWireframe(self.mh_shaders._shaders[0], proj_view_matrix, self.black, self.white)
            else:
                body.draw(self.mh_shaders._shaders[0], proj_view_matrix, self.light)

            # either with xray or normal shader draw assets
            #
            shader = 2 if self.xrayed else 0
            for obj in self.objects[asset_start:]:
                if self.wireframe:
                    obj.drawWireframe(self.mh_shaders._shaders[shader], proj_view_matrix, self.black, self.white)
                else:
                    obj.draw(self.mh_shaders._shaders[shader], proj_view_matrix, self.light, self.xrayed)

        if self.light.skybox and self.skybox and self.camera.cameraPers:
            self.skybox.draw(proj_view_matrix)

        if self.objects_invisible is True and "skeleton" in self.prims:
            posed = (baseClass.bvh is not None) or (baseClass.expression is not None)
            self.prims["skeleton"].newGeometry(posed)

        for name in self.prims:
            self.prims[name].draw(self.mh_shaders._shaders[1], proj_view_matrix)


    def Tweak(self):
        for glbuffer in self.buffers:
            glbuffer.Tweak()
        self.paintGL()
        self.update()

    def setCameraCenter(self):
        baseMesh = self.glob.baseClass.baseMesh
        self.camera.setCenter(baseMesh.getCenter(), baseMesh.getHeightInUnits())

    def noAssets(self):
        for glbuffer in self.buffers[1:]:
            glbuffer.Delete()
        self.objects = self.objects[:1]
        self.buffers = self.buffers[:1]

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
        for glbuffer in self.buffers:
            glbuffer.Delete()
        self.objects = []
        self.buffers = []

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
        self.blackmat.freeTextures(True)
        self.whitemat.freeTextures(True)
        if self.skybox is not None:
            self.skybox.delete()
            self.skybox = None
