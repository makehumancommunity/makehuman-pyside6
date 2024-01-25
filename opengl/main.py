from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import QSize
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
        # print (env)
        self.glob.openGLWindow = self
        if glob.Targets is not None:
            glob.Targets.refreshTargets(self)

    def createObject(self, obj, texture=False):
        glbuffer = OpenGlBuffers()
        glbuffer.VertexBuffer(obj.gl_coord, obj.gl_icoord, obj.n_glverts)
        glbuffer.NormalBuffer(obj.gl_norm)
        glbuffer.TexCoordBuffer(obj.gl_uvcoord)
        self.buffers.append(glbuffer)

        # TODO: material from mhmat file but not yet correct, these thing will be done in the shader
        #
        if texture is False:
            if hasattr(obj.material, 'diffuseTexture'):
                self.texture = obj.material.loadTexture(obj.material.diffuseTexture)
            else:
                default = self.env.existDataFile("skins", self.env.basename, "textures", "default.png")
                if default is not None:
                    self.texture = obj.material.loadTexture(default)
        else:
            if hasattr(obj.material, 'diffuseTexture'):
                self.texture = obj.material.loadTexture(obj.material.diffuseTexture)

        obj = RenderedObject(self.context(), glbuffer, self.mh_shaders, self.texture, pos=QVector3D(0, 0, 0))
        self.objects.append(obj)

    def newTexture(self, obj):
        print ("in new texture")
        
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

        self.mh_shaders = ShaderRepository(self.env)
        self.mh_shaders.loadFragShader("phong3l")
        self.mh_shaders.loadVertShader("phong3l")
        #
        # get positions of variables
        #
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
                obj.draw(self.mh_shaders, proj_view_matrix)

    def Tweak(self):
        for glbuffer in self.buffers:
            glbuffer.Tweak()
        self.paintGL()
        self.update()

    def setCameraCenter(self):
        baseClass = self.glob.baseClass
        self.camera.setCenter(baseClass.baseMesh.getCenter())

    def newMesh(self):
        baseClass = self.glob.baseClass
        for glbuffer in self.buffers:
            glbuffer.Delete()
        self.objects = []

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

