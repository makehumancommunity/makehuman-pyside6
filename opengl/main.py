from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QMatrix4x4, QVector3D, QOpenGLContext

# try to keep only constants here
#
import os
import OpenGL
from OpenGL import GL as gl
from opengl.shaders import ShaderRepository
from opengl.material import Material
from opengl.buffers import OpenGlBuffers, RenderedObject
from opengl.camera import Camera, Light
from opengl.skybox import OpenGLSkyBox
from opengl.prims import CoordinateSystem, Grid, BoneList

def GLVersion(initialized):
    glversion = {}
    glversion["version"] = OpenGL.__version__

    if initialized:
        glversion["card"] = gl.glGetString(gl.GL_VERSION).decode("utf-8")
    print (glversion)
    # print (gl.glGetString(gl.GL_VERSION)) TODO, add context etc.
    #
    # no shaders support will be outside this file
    #
    # without a context all other OpenGL parameter will not appear
    #
    return(glversion)


class OpenGLView(QOpenGLWidget):
    def __init__(self, glob):
        self.glob = glob
        self.env = glob.env
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.setMinimumSize(QSize(600, 600))
        self.setMaximumSize(QSize(2000, 2000))
        self.buffers = []
        self.objects = []
        self.objects_invisible = False
        self.prims = {}
        self.camera  = None
        self.skybox = None
        self.glob.openGLWindow = self

    def textureFromMaterial(self, obj):
        if hasattr(obj.material, 'diffuseTexture'):
            return(obj.material.loadTexture(obj.material.diffuseTexture))
        if hasattr(obj.material, 'diffuseColor'):
            return(obj.material.emptyTexture(obj.material.diffuseColor))
        return(obj.material.emptyTexture())

    def delSkeleton(self):
        if "skeleton" in self.prims:
            self.prims["skeleton"].delete()
            del self.prims["skeleton"]
            self.Tweak()

    def addSkeleton(self):
        skeleton = self.glob.baseClass.skeleton
        self.prims["skeleton"] = BoneList("skeleton", skeleton, self.context(), self.mh_shaders._shaders[1])
        if self.objects_invisible is True:
            self.togglePrims("skeleton", True)
        self.Tweak()

    def toggleObjects(self, status):
        self.objects_invisible = status
        if self.glob.baseClass is not None and self.glob.baseClass.skeleton is not None:
            skeleton = self.glob.baseClass.skeleton
            if self.objects_invisible is True:
                skeleton.newJointPos()
                self.prims["skeleton"].newGeometry()
                self.togglePrims("skeleton", True)
            else:
                self.togglePrims("skeleton", False)
            self.Tweak()


    def toggleSkybox(self, status):
        self.light.skybox = status
        self.Tweak()

    def togglePrims(self, name, status):
        if name in self.prims:
            self.prims[name].setVisible(status)
            self.Tweak()


    def createPrims(self):
        self.prims["axes"] = CoordinateSystem("axes", 10.0, self.context(), self.mh_shaders._shaders[1])
        self.prims["grid"] = Grid("grid", 10.0, self.context(), self.mh_shaders._shaders[1])

    def createObject(self, obj):
        """
        creates a rendered object and inserts it to a list according to zdepth
        """
        glbuffer = OpenGlBuffers()
        glbuffer.GetBuffers(obj.gl_coord, obj.gl_norm, obj.gl_uvcoord)
        self.buffers.append(glbuffer)

        texture = self.textureFromMaterial(obj)

        cnt = 0
        for elem in self.objects:
            if obj.z_depth < elem.z_depth:
                break
            cnt += 1
        obj.openGL = RenderedObject(self.context(), obj.getOpenGLIndex, obj.filename, obj.z_depth, glbuffer, self.mh_shaders._shaders[0], texture, pos=QVector3D(0, 0, 0))
        self.objects.insert(cnt, obj.openGL)

    def deleteObject(self,obj):
        obj.openGL.delete()
        obj.material.freeTextures()
        self.objects.remove(obj.openGL)
        self.Tweak()
        obj.openGL = None

    def newSkin(self, obj):
        texture = self.textureFromMaterial( obj)
        self.objects[0].setTexture(texture)

    def initializeGL(self):

        self.env.GL_Info = GLVersion(True)
        baseClass = self.glob.baseClass
        o_size = baseClass.baseMesh.getHeightInUnits() if baseClass is not None else 100
        glfunc = self.context().functions()

        glfunc.glEnable(gl.GL_DEPTH_TEST)
        glfunc.glEnable(gl.GL_BLEND)
        #glfunc.glDisable(gl.GL_CULL_FACE)
        glfunc.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        #
        # load shaders and get  positions of variables 
        #
        self.mh_shaders = ShaderRepository(self.glob)
        self.mh_shaders.loadShaders("phong3l")          # TODO: return Index 
        self.mh_shaders.attribVertShader()
        self.mh_shaders.getUniforms()

        self.mh_shaders.loadShaders("fixcolor")
        self.mh_shaders.attribVertShader(1)
        self.mh_shaders.getUniforms(1)

        self.mh_shaders.loadShaders("skybox")

        self.light = Light(self.mh_shaders, self.glob)
        self.light.setShader()

        self.camera = Camera(self.mh_shaders, o_size)
        self.camera.resizeViewPort(self.width(), self.height())

        if baseClass is not None:
            self.newMesh()

        self.skybox = OpenGLSkyBox(self.env, self.mh_shaders._shaders[2], glfunc)
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
        glfunc = self.context().functions()
        c = self.light.glclearcolor
        glfunc.glClearColor(c.x(), c.y(), c.z(), c.w())
        glfunc.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        proj_view_matrix = self.camera.getProjViewMatrix()
        baseClass = self.glob.baseClass
        if baseClass is not None and self.objects_invisible is False:
            start = 1 if baseClass.proxy is True else 0
            for obj in self.objects[start:]:
                obj.draw(self.mh_shaders._shaders[0], proj_view_matrix)

        if self.light.skybox and self.skybox and self.camera.cameraPers:
            self.skybox.draw(proj_view_matrix)

        if self.objects_invisible is True and "skeleton" in self.prims:
            skeleton = self.glob.baseClass.skeleton
            skeleton.newJointPos()
            self.prims["skeleton"].newGeometry()

        for name in self.prims:
            self.prims[name].draw(self.mh_shaders._shaders[1], proj_view_matrix)


    def Tweak(self):
        for glbuffer in self.buffers:
            glbuffer.Tweak()
        self.paintGL()
        self.update()

    def setCameraCenter(self):
        baseClass = self.glob.baseClass
        self.camera.setCenter(baseClass.baseMesh.getCenter())

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
            self.setCameraCenter()
            self.paintGL()
            self.update()

    def resizeGL(self, w, h):
        glfunc = self.context().functions()
        glfunc.glViewport(0, 0, w, h)
        self.camera.resizeViewPort(w, h)
        self.camera.calculateProjMatrix()

    def cleanUp(self):
        print ("cleanup openGL")
        if self.skybox is not None:
            self.skybox.delete()
            self.skybox = None
