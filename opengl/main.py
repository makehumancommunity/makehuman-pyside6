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
from opengl.camera import Camera

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

class GraphWindow(QOpenGLWidget):
    def __init__(self, env, glob):
        self.env = env
        self.glob = glob
        super().__init__()
        self.setMinimumSize(QSize(600, 600))
        self.buffers = None
        self.camera  = None
        print (env)
        self.glob.graphwindow = self
        if glob.Targets is not None:
            glob.Targets.refreshTargets(self)

    def createObject(self):
        baseClass = self.glob.baseClass
        self.buffers = OpenGlBuffers()
        self.buffers.VertexBuffer(baseClass.gl_coord, baseClass.gl_icoord, baseClass.n_glverts)
        self.buffers.NormalBuffer(baseClass.gl_norm)
        self.buffers.TexCoordBuffer(baseClass.gl_uvcoord)

        # TODO: material not yet correct, will be connect to object later and of course not with predefined path name
        #
        self.material = Material(self.env)
        self.texture = self.material.loadTexture(os.path.join (self.env.path_sysdata, "skins", self.env.basename, "textures", "default.png"))

        self.obj = RenderedObject(self.context(), self.buffers, self.mh_shaders, self.texture, pos=QVector3D(0, 0, 0))

    def initializeGL(self):

        self.env.GL_Info = GLVersion(True)
        self.camera = Camera()
        self.camera.resizeViewPort(self.width(), self.height())
        baseClass = self.glob.baseClass
        glfunc = self.context().functions()

        glfunc.glClearColor(0.2, 0.2, 0.2, 1)
        glfunc.glEnable(gl.GL_DEPTH_TEST)

        self.mh_shaders = ShaderRepository(self.env)
        self.mh_shaders.loadFragShader("testshader")
        self.mh_shaders.loadVertShader("testshader")
        self.mh_shaders.attribVertShader()
        self.mh_shaders.getVertLocations()


        if baseClass is not None:
            self.createObject()
            self.camera.setCenter(self.obj.getCenter())

    def customView(self, direction):
        self.camera.customView(direction)
        self.paintGL()
        self.update()

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

    def paintGL(self):
        glfunc = self.context().functions()

        glfunc.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        proj_view_matrix = self.camera.getProjViewMatrix()
        baseClass = self.glob.baseClass
        if baseClass is not None:
            self.obj.draw(self.mh_shaders, proj_view_matrix)

    def Tweak(self):
        if self.buffers is not None:
            self.buffers.Tweak()
            self.paintGL()
            self.update()

    def newMesh(self):
        baseClass = self.glob.baseClass
        if self.buffers is not None:
            self.buffers.Delete()
            del self.obj

        if baseClass is not None:
            self.createObject()
            self.camera.setCenter(baseClass.getCenter())
            self.paintGL()
            self.update()

    def resizeGL(self, w, h):
        glfunc = self.context().functions()
        glfunc.glViewport(0, 0, w, h)
        self.camera.resizeViewPort(w, h)
        self.camera.calculateProjMatrix()

