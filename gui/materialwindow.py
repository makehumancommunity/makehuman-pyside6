import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QCheckBox, QSizePolicy, QScrollArea, 
        QPlainTextEdit
        )
from PySide6.QtGui import QPixmap
from obj3d.object3d import object3d
from gui.common import MHTagEdit, IconButton


class MHMaterialWindow(QWidget):
    """
    MaterialWindow
    """
    def __init__(self, parent, PicSelectWidget, materials, asset):
        super().__init__()
        self.parent = parent
        self.env = parent.env
        self.glob = parent.glob
        self.materials = materials
        self.oldmaterial = asset.material
        self.asset = asset

        self.setWindowTitle("Material")
        self.resize(360, 500)

        layout = QVBoxLayout()
        self.selmode = 0
        self.imagescale = 128
        self.emptyIcon = os.path.join(self.env.path_sysdata, "icons", "noidea.png")

        self.picwidget = PicSelectWidget(self, materials, self.picButtonChanged, None)
        self.picwidget.populate(None, None)
        widget = QWidget()
        widget.setLayout(self.picwidget.layout)
        scrollArea = QScrollArea()
        scrollArea.setWidget(widget)
        scrollArea.setWidgetResizable(True)
        scrollArea.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        layout.addWidget(scrollArea)

        button4 = QPushButton("Use")
        button4.clicked.connect(self.use_call)
        layout.addWidget(button4)
        self.setLayout(layout)

    def picButtonChanged(self, matelem):
        if matelem.status == 1:
            # check asset before, if different change
            if matelem.filename != self.oldmaterial:
                print ("change")

                # get new material (releases old stuff as well)
                # different for skin (object3d) and asset
                #
                if isinstance(self.asset, object3d):
                    obj = self.asset
                    self.glob.baseClass.skinMaterial = matelem.filename
                else:
                    obj = self.asset.obj
                    self.asset.material = matelem.filename

                obj.newMaterial(matelem.filename)
                #
                # todo errors
                # atm only changing texture, not shader

                if hasattr(obj.material, 'diffuseTexture'):
                    texture = obj.material.loadTexture(obj.material.diffuseTexture)
                else:
                    texture = obj.material.emptyTexture(obj.material.diffuseColor)

                # set texture
                #
                obj.openGL.setTexture(texture)
                self.parent.graph.view.Tweak()
                self.oldmaterial = matelem.filename

    def updateWidgets(self, materials, asset):
        self.materials = materials
        self.asset = asset
        self.picwidget.layout.removeAllWidgets()
        if asset is not None:
            self.oldmaterial = asset.material
            self.picwidget.layout.newAssetList(materials)
            self.picwidget.populate(None, None)

    def use_call(self):
        self.close()


class MHAssetWindow(QWidget):
    """
    AssetWindow
    """
    def __init__(self, parent, changefunc, asset, selected, empty, proposals=[]):
        super().__init__()
        self.parent = parent
        self.changefunc = changefunc
        self.env = parent.env
        self.glob = parent.glob
        self.asset = asset
        self.view = self.parent.graph.view
        self.emptyIcon = empty
        print(selected)
        self.icon = None
        self.thumb = selected.icon
        self.origtags = ""
        self.origlist = []
        self.owntags = []

        layout = QVBoxLayout()
        self.nameLabel = QLabel()
        self.setName()
        layout.addWidget(self.nameLabel)

        # photo
        #
        ilayout = QHBoxLayout()
        ilayout.addWidget(IconButton(1,  os.path.join(self.env.path_sysicon, "camera.png"), "Thumbnail", self.thumbnail))
        self.imglabel=QLabel()
        self.displayPixmap()
        ilayout.addWidget(self.imglabel, alignment=Qt.AlignRight)
        layout.addLayout(ilayout)

        self.setWindowTitle("Asset Editor")
        self.resize(360, 500)
        self.tagsFromDB()

        layout.addWidget(QLabel("Original tags:"))
        self.tagbox = QPlainTextEdit()
        self.tagbox.setPlainText(self.origtags)
        self.tagbox.setReadOnly(True)

        layout.addWidget(self.tagbox)

        self.tagedit = MHTagEdit(self.glob, self.owntags, "Use own tags:", copyfrom=self.origlist, predefined = proposals)
        layout.addLayout(self.tagedit)

        hlayout = QHBoxLayout()
        save = QPushButton("Save")
        save.clicked.connect(self.use_call)
        hlayout.addWidget(save)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.cancel_call)
        hlayout.addWidget(cancel)

        layout.addLayout(hlayout)
        self.setLayout(layout)

    def displayPixmap(self):
        if self.icon is None:
            if self.thumb is None:
                pixmap = QPixmap(self.emptyIcon)
            else:
                pixmap = QPixmap(self.thumb)
        else:
            pixmap = QPixmap.fromImage(self.icon)
        self.imglabel.setPixmap(pixmap)

    def thumbnail(self):
        self.icon = self.view.createThumbnail()
        self.displayPixmap()

    def setName(self):
        name = self.asset.name if self.asset is not None else "none"
        self.nameLabel.setText("Name: " + name)

    def tagsFromDB(self):
        rows = self.env.fileCache.getEditParamInfo(self.asset.uuid)
        self.origtags = ""
        for row in rows:
            self.origlist = row[0].split("|")
            self.origtags= "\n".join(self.origlist)

        rows = self.env.fileCache.getEditParamUser(self.asset.uuid)
        self.owntags = []
        for row in rows:
            self.owntags =row[0].split("|")

    def updateWidgets(self, asset, selected, empty):
        self.asset = asset
        self.emptyIcon = empty
        if asset is None:
            self.origtags = ""
            self.tagedit.clearTags()
            self.thumb = None
        else:
            self.tagsFromDB()
            self.tagedit.newTags(self.owntags, self.origlist)
            self.thumb = selected.icon
        self.setName()
        self.tagbox.setPlainText(self.origtags)
        self.displayPixmap()

    def use_call(self):
        if self.asset is not None:
            newtags = self.tagedit.getTags()
            if len(newtags) == 0:
                print ("Delete own entry")
                self.env.fileCache.deleteParamUser(self.asset.uuid)
                self.asset.tags = self.origlist
            else:
                insert = "|".join(newtags)
                self.env.fileCache.insertParamUser(self.asset.uuid, insert)
                self.asset.tags = newtags
            print (self.asset.tags)
            iconpath = None
            if self.icon is not None:
                iconpath = self.asset.filename[:-6] + ".thumb"
                print ("Save icon as " + iconpath)
                self.icon.save(iconpath, "PNG", -1)
                self.env.fileCache.updateParamInfo(self.asset.uuid, iconpath)
                # TODO ... update
            self.changefunc(self.asset, iconpath)

        self.close()

    def cancel_call(self):
        self.close()

