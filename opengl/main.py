from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import QSize
from PySide6.QtGui import QMatrix4x4, QVector3D, QOpenGLContext

# try to keep only constants here
#
import OpenGL
from OpenGL import GL as gl
from opengl.shaders import ShaderRepository
from opengl.buffers import OpenGlBuffers, Object3D

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
        self.obj = Object3D(self.context(), self.buffers, self.mh_shaders, self.texture, pos=QVector3D(0, 0, 0))

    def initializeGL(self):

        self.env.GL_Info = GLVersion(True)
        baseClass = self.glob.baseClass
        glfunc = self.context().functions()

        glfunc.glClearColor(0.2, 0.2, 0.2, 1)
        glfunc.glEnable(gl.GL_DEPTH_TEST)

        self.mh_shaders = ShaderRepository(self.env)
        self.mh_shaders.loadFragShader("testshader")
        self.mh_shaders.loadVertShader("testshader")
        self.mh_shaders.attribVertShader()
        self.mh_shaders.getVertLocations()

        self.texture = self.mh_shaders.loadTexture("cube")


        # view
        self.proj_view_matrix = QMatrix4x4()
        self.proj_matrix = QMatrix4x4()
        self.view_matrix = QMatrix4x4()
        self.view_matrix.lookAt(
            QVector3D(2, 5, 20),
            QVector3D(0, 0, 0),
            QVector3D(0, 1, 0))

        if baseClass is not None:
            self.createObject()


    def paintGL(self):
        glfunc = self.context().functions()

        glfunc.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self.proj_view_matrix = self.proj_matrix * self.view_matrix
        baseClass = self.glob.baseClass
        if baseClass is not None:
            self.obj.draw(self.mh_shaders, self.proj_view_matrix)

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
            self.paintGL()
            self.update()

    def resizeGL(self, w, h):
        glfunc = self.context().functions()
        glfunc.glViewport(0, 0, w, h)
        self.proj_matrix.setToIdentity()
        self.proj_matrix.perspective(50, float(w) / float(h), 0.1, 100)

