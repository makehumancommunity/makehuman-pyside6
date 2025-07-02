"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * TextureRepo
    * MH_Texture
    * MH_Thumb
"""

from PySide6.QtOpenGL import QOpenGLTexture
from PySide6.QtGui import QImage, QColor
from PySide6.QtCore import QSize, Qt
import os

class TextureRepo():
    """
    texture repo contains information about loaded textures
    key is the filename, values are: [ openGL texture, usage, filedate, mhtex ]
    if filedate is "0" it is a generated texture
    """
    def __init__(self, glob):
        self.glob = glob
        self.textures = {}
        self.systextures = {}

    def getTextures(self):
        return self.textures

    def show(self):
        for t in self.textures.keys():
            print (t, self.textures[t][1], self.textures[t][2])

    def add(self, path, texture, timestamp, mhtex, textype="user"):
        if textype == "system":
            self.systextures[path] = [texture, 1, 0, None]
        else:
            if path not in self.textures:
                self.textures[path] = [texture, 1, timestamp, mhtex]

    def exists(self, path):
        if path in self.textures:
            return self.textures[path][0]

    def inc(self, path):
        if path in self.textures:
            self.textures[path][1] += 1

    def delete(self, texture):
        t = self.textures
        for elem in t:
            if t[elem][0] == texture:
                if t[elem][1] > 1:
                    t[elem][1] -= 1
                else:
                    t[elem][0].destroy()
                    del t[elem]
                return

    def refresh(self):
        for name, v in self.textures.items():
            # do not work with filedate 0 (means generated map)
            if v[2] != 0:
                if os.path.isfile(name):
                    timestamp = int(os.stat(name).st_mtime)
                    if timestamp > v[2]:
                        v[0] = v[3].refresh(name)
                        v[2] = timestamp
                else:
                    self.glob.env.logLine(1, name + " does not exist, no reload.")

    def cleanup(self, textype="user"):
        """
        central location to delete textures
        (systextures only by demand)
        """
        t = self.textures
        for elem in t:
            t[elem][0].destroy()

        self.textures = {}

        if textype == "system":
            t = self.systextures
            for elem in t:
                t[elem][0].destroy()


class MH_Texture():
    def __init__(self, glob, textype="user"):
        self.glob = glob
        self.repo = glob.textureRepo
        self.textype = textype
        self.texture = QOpenGLTexture(QOpenGLTexture.Target2D)

    def create(self, name, image):
        """
        :param image: QImage
        :param name: image path, used in repo to identify object
        """
        self.texture.create()
        self.texture.setData(image)
        self.texture.setMinMagFilters(QOpenGLTexture.Linear, QOpenGLTexture.Linear)
        self.texture.setWrapMode(QOpenGLTexture.ClampToEdge)

        return self.texture

    def destroy(self):
        self.texture.destroy()

    def delete(self):
        self.repo.delete(self.texture)

    def unicolor(self, rgb = [0.5, 0.5, 0.5]):
        color = QColor.fromRgbF(rgb[0], rgb[1], rgb[2])
        name = "Generated color [" + hex(color.rgb()) + "]"
        texture = self.repo.exists(name)
        if texture is not None:
            self.repo.inc(name)
            self.texture = texture
            return texture

        image = QImage(QSize(1,1),QImage.Format_ARGB32)
        image.fill(color)
        self.texture = self.create(name, image)
        self.repo.add(name, self.texture, 0, None, self.textype)
        return self.texture

    def load(self, path, textype="user", modify=True):
        """
        load textures
        """
        texture = self.repo.exists(path)
        if texture is not None:
            if modify:
                self.repo.inc(path)
            self.texture = texture
            return texture

        if not os.path.isfile(path):
            return None

        timestamp = int(os.stat(path).st_mtime)
        image = QImage(path)
        self.glob.env.logLine(8, "Load: " + path + " " + str(image.format()))
        self.create(path, image)
        self.repo.add(path, self.texture, timestamp, self, textype)
        return self.texture

    def refresh(self, path):
        # print ("refresh: ", path)
        self.destroy()
        image = QImage(path)
        self.create(path, image)
        return self.texture


class MH_Thumb():
    def __init__(self, maxsize=128):
        self.maxsize = maxsize
        self.img = None

    def rescale(self, name):
        self.img = QImage(name)
        size = self.img.size()
        if size.height() > self.maxsize or size.width() > self.maxsize:
            newimage = self.img.scaled(self.maxsize, self.maxsize, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            newimage.save(name, "PNG", -1)

