import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QCheckBox, QSizePolicy, QScrollArea, 
        QPlainTextEdit
        )
from obj3d.object3d import object3d
from gui.common import MHTagEdit


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
    def __init__(self, parent, changefunc, asset):
        super().__init__()
        self.parent = parent
        self.changefunc = changefunc
        self.env = parent.env
        self.glob = parent.glob
        self.asset = asset
        self.origtags = ""
        self.origlist = []
        self.owntags = []

        # TODO change
        #
        self.setWindowTitle("Asset Editor")
        self.resize(360, 500)
        self.tagsFromDB()

        layout = QVBoxLayout()
        self.nameLabel = QLabel()
        self.setName()
        layout.addWidget(self.nameLabel)
        layout.addWidget(QLabel("Original tags:"))
        self.tagbox = QPlainTextEdit()
        self.tagbox.setPlainText(self.origtags)
        self.tagbox.setReadOnly(True)

        layout.addWidget(self.tagbox)

        self.tagedit = MHTagEdit(self.glob, self.owntags, "Use own tags:")
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

    def updateWidgets(self, asset):
        self.asset = asset
        if asset is None:
            self.origtags = ""
            self.tagedit.clearTags()
        else:
            self.tagsFromDB()
            self.tagedit.newTags(self.owntags)
        self.setName()
        self.tagbox.setPlainText(self.origtags)

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
            self.changefunc(self.asset)

        self.close()

    def cancel_call(self):
        self.close()

