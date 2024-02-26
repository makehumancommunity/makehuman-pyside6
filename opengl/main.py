from PySide6.QtOpenGLWidgets import QOpenGLWidget
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
        self.setMinimumSize(QSize(600, 600))
        self.buffers = []
        self.objects = []
        self.camera  = None
        self.skybox = None
        self.glob.openGLWindow = self
        if glob.Targets is not None:
            glob.Targets.refreshTargets(self)

    def createObject(self, obj, needtexture=False):
        glbuffer = OpenGlBuffers()
        glbuffer.VertexBuffer(obj.gl_coord, obj.gl_icoord, obj.n_glverts)
        glbuffer.NormalBuffer(obj.gl_norm)
        glbuffer.TexCoordBuffer(obj.gl_uvcoord)
        self.buffers.append(glbuffer)

        # TODO: material from mhmat file but not yet correct, these thing will be done in the shader
        #
        if needtexture is False:
            if hasattr(obj.material, 'diffuseTexture'):
                texture = obj.material.loadTexture(obj.material.diffuseTexture)
            else:
                default = self.env.existDataFile("skins", self.env.basename, "textures", "default.png")
                if default is not None:
                    texture = obj.material.loadTexture(default)
        else:
            if hasattr(obj.material, 'diffuseTexture'):
                texture = obj.material.loadTexture(obj.material.diffuseTexture)
        obj.openGL = RenderedObject(self.context(), glbuffer, self.mh_shaders._shaders[0], texture, pos=QVector3D(0, 0, 0))
        self.objects.append(obj.openGL)

    def deleteObject(self,obj):
        obj.openGL.delete()
        if hasattr(obj.material, 'diffuseTexture'):
            self.glob.freeTextures(obj.material.diffuseTexture)
        self.objects.remove(obj.openGL)
        self.Tweak()

    def newTexture(self, obj):
        
        if hasattr(obj.material, 'diffuseTexture'):
            self.texture = obj.material.loadTexture(obj.material.diffuseTexture)
            print (obj.material.diffuseTexture)
            self.objects[0].setTexture(self.texture)

    def initializeGL(self):

        self.env.GL_Info = GLVersion(True)
        baseClass = self.glob.baseClass
        o_size = baseClass.baseMesh.getHeightInUnits() if baseClass is not None else 100
        glfunc = self.context().functions()

        glfunc.glEnable(gl.GL_DEPTH_TEST)
        glfunc.glEnable(gl.GL_BLEND)
        #glfunc.glDisable(gl.GL_CULL_FACE)
        glfunc.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        self.mh_shaders = ShaderRepository(self.glob)
        id1 = self.mh_shaders.loadShaders("phong3l")
        print(id1)
        self.skyshader = self.mh_shaders.loadShaders("skybox")
        print(self.skyshader)

        #
        # get positions of variables
        #
        glfunc.glUseProgram( id1)
        self.mh_shaders.attribVertShader()
        self.mh_shaders.getUniforms()

        self.light = Light(self.mh_shaders, self.glob)
        self.light.setShader()

        self.camera = Camera(self.mh_shaders, o_size)
        self.camera.resizeViewPort(self.width(), self.height())

        if baseClass is not None:
            self.newMesh()
            #obj = baseClass.baseMesh
            #self.createObject(obj)
            #self.camera.setCenter(obj.getCenter())

        self.skybox = OpenGLSkyBox(self.env, self.mh_shaders._shaders[1], glfunc)
        self.skybox.create()

    def createThumbnail(self, name):
        image = self.grabFramebuffer()
        image = image.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image.save(name, "PNG", -1)

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
        if baseClass is not None:
            for obj in self.objects:
                obj.draw(self.mh_shaders._shaders[0], proj_view_matrix)

        if self.light.skybox and self.skybox:
            glfunc.glUseProgram(self.skyshader)
            self.skybox.setData(proj_view_matrix)
            self.skybox.draw()

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
        for elem in self.glob.baseClass.attachedAssets:
            # print ("   " + str(elem))
            self.createObject(elem.obj, True)

    def newMesh(self):
        baseClass = self.glob.baseClass
        for glbuffer in self.buffers:
            glbuffer.Delete()
        self.objects = []
        self.buffers = []

        if baseClass is not None:
            self.createObject(baseClass.baseMesh, False)
            for elem in baseClass.attachedAssets:
                # print ("   " + str(elem))
                self.createObject(elem.obj, True)
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
