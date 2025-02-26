"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck
"""
from PySide6.QtGui import QMatrix4x4, QVector3D, QVector4D, QOpenGLContext
import OpenGL
from OpenGL import GL as gl
from math import pi as M_PI, atan, degrees, sqrt

class Camera():
    """
    should always calculate view matrix and projection matrix
    """
    def __init__(self, shaders, o_size):
        """
        all parameters connected with camera
        """
        self.shaders = shaders
        self.o_height =  o_size
        self.focalLength = 50.0                # start with a norm focal length
        self.verticalAngle = 0.0                # vertical angle
        self.start_dist = 50.0                  # initial camera distance
        self.ortho_magnification =4.8
        self.view_width = 0
        self.view_height = 0
        self.last_mousex = 0
        self.last_mousey = 0
        self.deltaAngleX = 0                    # movement left to right = 2*PI = 360 deg
        self.deltaAngleY = 0                    # movement top to bottom = PI = 180 deg
        self.deltaMoveX = 0                     # movement left to right for panning
        self.deltaMoveY = 0                     # movement top to bottom for panning
        self.view_matrix = QMatrix4x4()
        self.proj_matrix = QMatrix4x4()
        self.proj_view_matrix = QMatrix4x4()    # needed outside to draw

        self.cameraPos =  QVector3D()           # the position of the camera
        self.cameraDir =  QVector3D()           # direction of the camera (what is up, x is usually not changed)
        self.lookAt = QVector3D()               # the position to focus
        self.center = QVector3D()               # the center of the object to focus on
        self.resetCamera()
        self.updateViewMatrix()

    def __str__(self):
        x   = self.cameraPos.toTuple()
        pos = list(map(lambda x: round(x,2), x))

        x   = self.lookAt.toTuple()
        lookat = list(map(lambda x: round(x,2), x))

        direct = self.cameraDir.toTuple()
        return ("Pos: " + str(pos) + "\nAim: " + str(lookat) + "\nDir: " +  str(direct) + "\nAng: " + str(round(self.verticalAngle,2)))

    def calculateVerticalAngle(self):
        height = self.o_height * 1.05
        self.verticalAngle = 2 * degrees(atan(height/(2*self.focalLength)))
        return(self.verticalAngle)

    def getFocalLength(self):
        return(self.focalLength)

    def setFocalLength(self, value):
        self.focalLength = value
        #
        v = self.cameraPos - self.lookAt
        l = v.length() /value
        self.cameraPos =  (v / l) + self.center
        #
        self.updateViewMatrix()
        self.calculateProjMatrix()

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
        self.view_matrix.setToIdentity()
        self.view_matrix.lookAt( self.cameraPos, self.lookAt, self.cameraDir)
        self.proj_view_matrix = self.proj_matrix * self.view_matrix

    def calculateOrthoMatrix(self):
        self.proj_matrix.setToIdentity()
        factor = self.o_height* self.ortho_magnification
        w_o = float(self.view_width) / factor
        h_o = float(self.view_height) / factor
        self.proj_matrix.ortho(-w_o, w_o, -h_o, h_o, 0.1, 100)
        
    def resetCamera(self):
        self.cameraPers = True
        self.cameraHeight = 0
        self.focalLength = 50.0                # start with a norm focal length
        self.cameraDist = self.start_dist       # calculate distance by trigonometric functions later
        self.cameraPos =  QVector3D(0, self.cameraHeight, self.cameraDist)
        self.lookAt =  self.center.__copy__()
        self.cameraDir =  QVector3D(0, 1, 0)
        print ("Reset:")
        print (self)

    def setCenter(self, center, size):
        self.o_height = size
        self.calculateVerticalAngle()
        self.lookAt = QVector3D(center[0], center[1], center[2])
        self.center = self.lookAt.__copy__()
        self.setFocalLength(50)
        self.cameraHeight = center[1]
        self.cameraDist = self.cameraPos.z()
        self.updateViewMatrix()
        print ("Set Center: " + str(center) + ", Size: " + str(size))
        print (self)

    def customView(self, direction):
        """
        the axis 6 views
        """
        self.cameraDist = self.center.z() + self.start_dist
        self.cameraPos =  self.center + direction * self.cameraDist
        if direction.y()== 0:
            self.cameraPos.setY(self.cameraHeight)
            self.cameraDir =  QVector3D(0, 1, 0)
        else:
            self.cameraDir =  QVector3D(0, 0, 1)
        self.lookAt =  self.center.__copy__()
        self.updateViewMatrix()

    def modifyDistance(self, distance):
        """
        move one unit on vector (zoom by vector length)
        """
        if self.cameraPers:
            v = self.cameraPos - self.lookAt
            l = v.length() * distance
            self.cameraPos += ( v / l)
            self.updateViewMatrix()
        else:
            if distance > 0 and self.ortho_magnification < 1.1 or \
                distance < 0 and self.ortho_magnification > 100:
                return
            self.ortho_magnification -= (self.ortho_magnification / 20 ) * distance
            self.calculateOrthoMatrix()
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

    def panning(self, x, y):
        #
        # works kinda, but there is a better way for sure
        #
        diffx = (self.last_mousex - x) * self.deltaMoveX
        diffy = (self.last_mousey - y) * self.deltaMoveY
        self.setLastMousePosition(x, y)

        direct = self.cameraPos - self.center
        xv = direct.x()
        zv = direct.z()
        lenx = abs(xv)
        lenz = abs(zv)

        if lenx > lenz:
            if lenz > 10.0:
                if zv > 10.0:
                    diffz = diffx *  (xv/zv)
                else:
                    diffz = -diffx * (xv/zv)
                diffx = diffx *  (lenx/zv)
            else:
                if xv > 0:
                    diffz = diffx
                else:
                    diffz = -diffx
                diffx = 0

        else:
            if lenx > 10.0:
                diffz = diffx *  (lenz/xv)
                if xv > 10.0:
                    diffx = diffx *  (zv/xv)
                else:
                    diffx = -diffx *  (zv/xv)
            else:
                if zv < 0:
                    diffx = -diffx
                diffz = 0


        diffx *= 10.0
        diffy *= 10.0
        diffz *= 10.0

        self.lookAt.setX(self.lookAt.x() + diffx)
        self.lookAt.setZ(self.lookAt.z() - diffz)
        self.lookAt.setY(self.lookAt.y() - diffy)
        self.cameraPos.setX(self.cameraPos.x() + diffx)
        self.cameraPos.setZ(self.cameraPos.z() - diffz)
        self.cameraPos.setY(self.cameraPos.y() - diffy)

        self.updateViewMatrix()

    def resizeViewPort(self, w, h):
        self.view_width = w
        self.view_height = h
        self.deltaAngleX = 2 * M_PI / w # movement left to right = 2*PI = 360 deg
        self.deltaAngleY = M_PI / h     # movement top to bottom = PI = 180 deg
        self.deltaMoveX = 1 / w         # same for panning
        self.deltaMoveY = 1 / h         # same for panning

    def calculateProjMatrix(self):
        w = float(self.view_width)
        h = float(self.view_height)

        if self.cameraPers:
            va = self.calculateVerticalAngle()
            self.proj_matrix.setToIdentity()
            self.proj_matrix.perspective(va, w / h, 0.1, 500)
        else:
            self.calculateOrthoMatrix()
        self.proj_view_matrix = self.proj_matrix * self.view_matrix


class Light():
    """
    can be used to manipulate light in scene, used for up to 3 lights
    """

    def __init__(self, shaders, glob):
        self.glob = glob
        self.shaderInit = glob.shaderInit
        self.shaders = shaders
        self.phong = shaders.getShader("phong3l")
        self.pbr = shaders.getShader("pbr")
        self.normal = shaders.getShader("normal")
        self.toon = shaders.getShader("toon")
        #
        # volume of scene in units
        #
        self.min_coords = [-25.0, -25.0, -25.0 ]
        self.max_coords = [25.0, 25.0, 25.0 ]

        self.glclearcolor = QVector4D()
        self.ambientLight = QVector4D()
        self.lightWeight = QVector3D()
        self.blinn = False
        self.skybox = True
        self.skyboxname = None

        self.lights = [ 
                { "pos": QVector3D(), "vol": QVector3D(), "int": 0.0, "type": 0 }, 
                { "pos": QVector3D(), "vol": QVector3D(), "int": 0.0, "type": 0 },
                { "pos": QVector3D(), "vol": QVector3D(), "int": 0.0, "type": 0 },
                ]
        self.fromGlobal(False)
    
    def listTo3D(self, v, elems):
        v.setX(elems[0])
        v.setY(elems[1])
        v.setZ(elems[2])

    def listTo4D(self, v, elems):
        v.setX(elems[0])
        v.setY(elems[1])
        v.setZ(elems[2])
        v.setW(elems[3])

    def q3ToList(self, v):
        return (v.x(), v.y(), v.z())

    def q4ToList(self, v):
        return (v.x(), v.y(), v.z(), v.w())

    def fromGlobal(self, load_json):
        if load_json:
            self.shaderInit = self.glob.readShaderInitJSON()
        self.blinn = self.shaderInit["blinn"]
        self.skybox = self.shaderInit["skybox"]
        self.skyboxname = self.shaderInit["skyboxname"]
        self.listTo4D(self.glclearcolor, self.shaderInit["glclearcolor"])
        self.listTo4D(self.ambientLight, self.shaderInit["ambientcolor"])
        self.lightWeight.setY(self.shaderInit["specularfocus"])
        for i, d in enumerate(self.lights):
            s = self.shaderInit["lamps"][i]
            self.listTo3D(d["pos"], s["position"])
            self.listTo3D(d["vol"], s["color"][:3])     # color + intensity are in one array in json
            d["int"] = s["color"][3]
            d["type"] = s["type"]
        self.setShader()

    def toGlobal(self):
        self.shaderInit["blinn"] = self.blinn
        self.shaderInit["glclearcolor"] = self.q4ToList(self.glclearcolor)
        self.shaderInit["ambientcolor"] = self.q4ToList(self.ambientLight)
        self.shaderInit["specularfocus"] =  self.lightWeight.y()
        self.shaderInit["skyboxname"] = self.skyboxname
        for i, s in enumerate(self.lights):
            d = self.shaderInit["lamps"][i]
            d["position"] = self.q3ToList(s["pos"])

            d["color"]    = list(self.q3ToList(s["vol"]))  # recombine array
            d["color"].append(s["int"])

            d["type"] = s["type"]

    def setShader(self):
        for shader in [self.phong, self.pbr, self.toon, self.normal]:
            self.shaders.bindShader(shader)
            for i, elem in enumerate(self.lights):
                self.shaders.setShaderArrayStruct(shader, "pointLights", i, "position", elem["pos"])
                self.shaders.setShaderArrayStruct(shader, "pointLights", i, "color", elem["vol"])
                self.shaders.setShaderArrayStruct(shader, "pointLights", i, "intensity", elem["int"])
                self.shaders.setShaderArrayStruct(shader, "pointLights", i, "type", elem["type"])
            self.shaders.setShaderUniform(shader, "ambientLight", self.ambientLight)
        
        # next ones are only for phong
        #
        self.shaders.bindShader(self.phong)
        self.shaders.setShaderUniform(self.phong, "blinn", self.blinn)
        self.shaders.setShaderUniform(self.phong, "lightWeight", self.lightWeight)

    def useBlinn(self, value):
        if value != self.blinn:
            self.blinn = value
            self.setShader()

    def useSkyBox(self, value):
        self.skybox = value

    def setAmbientLuminance(self, value):
        self.ambientLight.setW(value)
        self.setShader()

    def setSpecularLuminance(self, value):
        self.lightWeight.setX(value)
        self.setShader()

    def setSpecularFocus(self, value):
        self.lightWeight.setY(value)
        self.setShader()

    def setClearColor(self, value):
        self.glclearcolor.setX(value.redF())
        self.glclearcolor.setY(value.greenF())
        self.glclearcolor.setZ(value.blueF())
        self.glclearcolor.setW(1.0)

    def setAmbientColor(self, value):
        self.ambientLight.setX(value.redF())
        self.ambientLight.setY(value.greenF())
        self.ambientLight.setZ(value.blueF())
        self.setShader()

    def setHPos(self, num, y):
        m =  self.lights[num]["pos"]
        m.setY(y)
        self.setShader()

    def setLPos(self, num, x, z):
        m =  self.lights[num]["pos"]
        m.setX(x)
        m.setZ(z)
        self.setShader()

    def setType(self, num, ltype):
        self.lights[num]["type"] = ltype
        self.setShader()

    def setLLuminance(self, num, value):
        self.lights[num]["int"] = value
        self.setShader()

    def setLColor(self, num, value):
        m =  self.lights[num]["vol"]
        m.setX(value.redF())
        m.setY(value.greenF())
        m.setZ(value.blueF())
        self.setShader()

