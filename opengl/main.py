from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import QSize
from PySide6.QtGui import QMatrix4x4, QVector3D

import OpenGL
from OpenGL import GL as gl
from core.mesh import dummyMesh
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
    def __init__(self, env):
        self.env = env
        super().__init__()
        self.setMinimumSize(QSize(600, 600))
        self.vert_buffers = None
        print (env)

    def initializeGL(self):

        self.env.GL_Info = GLVersion(True)

        gl.glClearColor(0.2, 0.2, 0.2, 1)
        gl.glEnable(gl.GL_DEPTH_TEST)
        self.mh_shaders = ShaderRepository(self.env)
        self.mh_shaders.loadFragShader("testshader")
        self.mh_shaders.loadVertShader("testshader")
        self.mh_shaders.attribVertShader()
        self.mh_shaders.getVertLocations()
        texture = self.mh_shaders.loadTexture("cube")

        self.object = dummyMesh()
        self.object.load()

        self.buffers = OpenGlBuffers()
        self.buffers.VertexBuffer(self.object.verts, self.object.amount_of_vertices)
        self.buffers.NormalBuffer(self.object.normals)
        self.buffers.TexCoordBuffer(self.object.tex_coords)

        # view
        self.proj_view_matrix = QMatrix4x4()
        self.proj_matrix = QMatrix4x4()
        self.view_matrix = QMatrix4x4()
        self.view_matrix.lookAt(
            QVector3D(2, 3, 5),
            QVector3D(0, 0, 0),
            QVector3D(0, 1, 0))

        self.obj = Object3D(self.buffers, self.mh_shaders, texture, pos=QVector3D(0, 0, 0))



    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self.proj_view_matrix = self.proj_matrix * self.view_matrix
        self.obj.draw(self.mh_shaders, self.proj_view_matrix)


    def resizeGL(self, w, h):
        gl.glViewport(0, 0, w, h)
        self.proj_matrix.setToIdentity()
        self.proj_matrix.perspective(50, float(w) / float(h), 0.1, 100)


