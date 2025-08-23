"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * OffScreenRender
"""

from PySide6.QtGui import QSurfaceFormat, QOffscreenSurface, QOpenGLContext, QImage
from PySide6.QtOpenGL import QOpenGLFramebufferObjectFormat, QOpenGLFramebufferObject

from OpenGL import GL as gl

class OffScreenRender:
    def __init__(self, glob, view, transparent=False):
        self.glob = glob
        self.view = view
        self.transparent = transparent
        self.framebuffer = None
        self.width = 0
        self.height = 0
        self.oldheight = self.view.window_height
        self.oldwidth = self.view.window_width
        self.context = None

    def getBuffer(self, width, height):
        self.width = width
        self.height = height
        self.oldheight = self.view.window_height
        self.oldwidth = self.view.window_width

        bufformat = QOpenGLFramebufferObjectFormat()
        sformat = QSurfaceFormat()
        if self.glob.env.noalphacover is False:
            bufformat.setSamples(4)
            sformat.setSamples(4)

        self.surface = QOffscreenSurface()
        self.surface.setFormat(sformat)

        self.context = QOpenGLContext()
        self.context.create()

        self.framebuffer = QOpenGLFramebufferObject(width, height, bufformat)
        self.framebuffer.setAttachment(QOpenGLFramebufferObject.Attachment.Depth)
        self.framebuffer.addColorAttachment(width, height)
        self.framebuffer.bind()
        self.context.makeCurrent(self.surface)
        ogl = self.context.functions()

        self.view.camera.resizeViewPort(width, height)
        proj_view_matrix = self.view.camera.calculateProjMatrix()
        ogl.initializeOpenGLFunctions()

        ogl.glViewport(0, 0, width, height)
        ogl.glEnable(gl.GL_DEPTH_TEST)

        c = self.view.light.glclearcolor
        transp = 0 if self.transparent else c.w()
        print (transp)
        ogl.glClearColor(c.x(), c.y(), c.z(), transp)
        ogl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        campos = self.view.camera.getCameraPos()
        baseClass = self.glob.baseClass
        start = 1 if baseClass.proxy is True else 0

        self.glob.openGLBlock = True
        for obj in self.view.objects[start:]:
            obj.setContext(self.context)
            obj.draw(proj_view_matrix, campos, self.view.light)
            obj.setContext(self.view.context())
        self.glob.openGLBlock = False
        ogl.glDisable(gl.GL_DEPTH_TEST)

    def bufferToImage(self):
        # check for self.framebuffer.hasOpenGLFramebufferBlit()
        if self.glob.env.noalphacover is False:
            targetbuffer = QOpenGLFramebufferObject(self.width, self.height)
            self.framebuffer.blitFramebuffer(targetbuffer, self.framebuffer)
            img =  targetbuffer.toImage()
        else:
            img =  self.framebuffer.toImage()

        imgmode = QImage.Format_RGBA8888 if self.transparent else QImage.Format_RGB888
        img =  img.convertToFormat(imgmode)
        self.context.doneCurrent()
        self.framebuffer.bindDefault()
        return img

    def releaseBuffer(self):
        self.view.resizeGL(self.oldwidth, self.oldheight)
        self.framebuffer.release()
        self.surface.destroy()

