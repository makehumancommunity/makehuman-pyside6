from PySide6.QtGui import QMatrix4x4, QVector3D, QOpenGLContext
import OpenGL
from OpenGL import GL as gl
from math import pi as M_PI

class Camera():
    """
    should always calculate view matrix and projection matrix
    """
    def __init__(self):
        """
        all parameters connected with camera
        """
        self.view_width = 0
        self.view_height = 0
        self.last_mousex = 0
        self.last_mousey = 0
        self.deltaAngleX = 0                    # movement left to right = 2*PI = 360 deg
        self.deltaAngleY = 0                    # movement top to bottom = PI = 180 deg
        self.view_matrix = QMatrix4x4()
        self.proj_matrix = QMatrix4x4()
        self.proj_view_matrix = QMatrix4x4()    # needed outside to draw
        self.cameraPos =  QVector3D()           # the position of the camera
        self.cameraDir =  QVector3D()           # direction of the camera (what is up, x is usually not changed)
        self.lookAt = QVector3D()               # the position to focus
        self.resetCamera()
        self.updateViewMatrix()

    def getViewMatrix(self):
        return self.view_matrix

    def getProjViewMatrix(self):
        return self.proj_view_matrix

    def getCameraPos(self):
        return self.cameraPos

    def getViewDirection(self):
        return -self.view_matrix.transposed().row(2).toVector3D()

    def getRightVector(self):
        return self.view_matrix.transposed().row(0).toVector3D()

    def updateViewMatrix(self):
        """
        new position of camera
        """
        print (self.cameraPos)
        self.view_matrix.setToIdentity()
        self.view_matrix.lookAt( self.cameraPos, self.lookAt, self.cameraDir)
        self.proj_view_matrix = self.proj_matrix * self.view_matrix

    def resetCamera(self):
        self.cameraPers = True
        self.cameraDist = 20
        self.cameraHeight = 0
        self.cameraPos =  QVector3D(0, self.cameraHeight, self.cameraDist)
        self.lookAt =  QVector3D(0, 0, 0)
        self.cameraDir =  QVector3D(0, 1, 0)

    def setCenter(self, center):
        print ("Center: " + str(center))
        self.lookAt = QVector3D(center[0], center[1], center[2])
        self.cameraHeight = center[1]
        self.cameraPos =  QVector3D(0, self.cameraHeight, self.cameraDist)
        print (self.lookAt)
        self.updateViewMatrix()

    def customView(self, direction):
        """
        the axis 6 views
        """
        self.cameraPos =  direction * self.cameraDist
        if direction.y()== 0:
            self.cameraPos.setY(self.cameraHeight)
            self.cameraDir =  QVector3D(0, 1, 0)
        else:
            self.cameraDir =  QVector3D(0, 0, 1)
        self.updateViewMatrix()


    def modifyDistance(self, distance):
        self.cameraDist += distance
        self.cameraPos.setZ(self.cameraDist)
        self.updateViewMatrix()

    def togglePerspective(self, mode):
        self.cameraPers = mode
        self.calculateProjMatrix()

    def setLastMousePosition(self, x, y):
        """
        called when mouse pressed inside graphics-window
        """
        self.last_mousex = x 
        self.last_mousey = y 

    def arcBallRotation(self, x, y):
        """
        mouse navigation (rotation with button pressed)
        TODO: without use of quaternions there will be a problem with the direction
        (top view, bottom view)
        """
        xAngle = (self.last_mousex - x) * self.deltaAngleX
        yAngle = (self.last_mousey - y) * self.deltaAngleY
        print (xAngle)
        print (yAngle)

        # avoid camera direction is identical to up vector
        #
        cosAngle = QVector3D.dotProduct(self.getViewDirection(), self.cameraDir)
        if abs(cosAngle) > .99:
            yangle = 0

        # x rotation
        #
        rotMatrixX = QMatrix4x4()                   # create as identity matrix
        rotMatrixX.rotate(xAngle, self.cameraDir)   # rotate in x
        position = rotMatrixX.map(self.cameraPos - self.lookAt) + self.lookAt

        # y rotation
        #
        rotMatrixY = QMatrix4x4()
        rotMatrixY.rotate(yAngle, self.getRightVector())
        position = rotMatrixY.map(position - self.lookAt) + self.lookAt
        self.cameraPos = position
        self.updateViewMatrix()

    def resizeViewPort(self, w, h):
        self.view_width = w
        self.view_height = h
        self.deltaAngleX = 2 * M_PI / w # movement left to right = 2*PI = 360 deg
        self.deltaAngleY = M_PI / h     # movement top to bottom = PI = 180 deg

    def calculateProjMatrix(self):
        w = float(self.view_width)
        h = float(self.view_height)

        self.proj_matrix.setToIdentity()
        if self.cameraPers:
            self.proj_matrix.perspective(50, w / h, 0.1, 100)
        else:
            w_o = w / 100
            h_o = h / 100
            self.proj_matrix.ortho(-w_o, w_o, -h_o, h_o, 0.1, 100)
        self.proj_view_matrix = self.proj_matrix * self.view_matrix


    
