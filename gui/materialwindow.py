import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QCheckBox, QSizePolicy, QScrollArea, 
        QPlainTextEdit
        )
from obj3d.object3d import object3d
from gui.dialogs import MHTagEdit


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
        self.oldmaterial = asset.material
        self.asset = asset
        self.picwidget.layout.removeAllWidgets()
        self.picwidget.layout.newAssetList(materials)
        self.picwidget.populate(None, None)

    def use_call(self):
        self.close()


class MHAssetWindow(QWidget):
    """
    AssetWindow
    """
    def __init__(self, parent, asset):
        super().__init__()
        self.parent = parent
        self.env = parent.env
        self.glob = parent.glob
        self.asset = asset

        # TODO change
        #
        self.setWindowTitle("Asset Editor")
        self.resize(360, 500)
        rows = self.env.fileCache.getEditParamInfo(asset.uuid)
        tags = ""
        for row in rows:
            tags= "\n".join(row[0].split("|"))

        rows = self.env.fileCache.getEditParamUser(asset.uuid)
        self.owntags = []
        for row in rows:
            self.owntags =row[0].split("|")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Original tags:"))
        self.tagbox = QPlainTextEdit()
        self.tagbox.setPlainText(tags)
        self.tagbox.setReadOnly(True)

        layout.addWidget(self.tagbox)

        self.tagedit = MHTagEdit(self.owntags)
        layout.addLayout(self.tagedit)

        button4 = QPushButton("Use")
        button4.clicked.connect(self.use_call)
        layout.addWidget(button4)
        self.setLayout(layout)

    def use_call(self):
        newtags = self.tagedit.getTags()
        if len(newtags) == 0:
            print ("Delete own entry")
            self.env.fileCache.deleteParamUser(self.asset.uuid)
        else:
            insert = "|".join(newtags)
            self.env.fileCache.insertParamUser(self.asset.uuid, insert)
            print(insert)
        # update tags in assetList
        self.close()

