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
        oldf = self.view.context().functions()

        self.bufformat = QOpenGLFramebufferObjectFormat()

        # use same format for buffer
        #
        sformat = QSurfaceFormat()
        sformat.setDefaultFormat(self.glob.app.getFormat())

        if self.glob.env.noalphacover is False:
            self.bufformat.setSamples(4)
        self.bufformat.setAttachment(QOpenGLFramebufferObject.Attachment.CombinedDepthStencil)

        self.context = QOpenGLContext()
        self.context.setFormat(sformat)

        self.surface = QOffscreenSurface()
        self.surface.setFormat(self.view.format())
        self.surface.create()
        self.context.makeCurrent(self.surface)

        self.framebuffer = QOpenGLFramebufferObject(width, height, self.bufformat)
        self.framebuffer.bind()
        ogl = self.context.functions()

        self.view.camera.resizeViewPort(width, height)
        proj_view_matrix = self.view.camera.calculateProjMatrix()
        ogl.initializeOpenGLFunctions()

        ogl.glViewport(0, 0, width, height)

        c = self.view.light.glclearcolor
        if self.transparent:
            ogl.glClearColor(0.0, 0.0, 0.0, 0.0)
        else:
            ogl.glClearColor(c.x(), c.y(), c.z(), 1.0)
        ogl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        campos = self.view.camera.getCameraPos()
        baseClass = self.glob.baseClass
        start = 1 if baseClass.proxy is True else 0

        self.glob.openGLBlock = True
        for obj in self.view.objects[start:]:
            obj.setFunctions(self.context.functions())
            obj.draw(proj_view_matrix, campos, self.view.light)
            obj.setFunctions(oldf)
        self.glob.openGLBlock = False

    def bufferToImage(self):
        # check for self.framebuffer.hasOpenGLFramebufferBlit()
        if self.glob.env.noalphacover is False:
            #targetbuffer = QOpenGLFramebufferObject(self.width, self.height)
            #self.framebuffer.blitFramebuffer(targetbuffer, self.framebuffer)
            #img = targetbuffer.toImage()
            img =  self.framebuffer.toImage()

            # to avoid artifacts, we need to copy the image once
            #
            img = QImage(img.constBits(), img.width(), img.height(), QImage.Format_ARGB32)
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

