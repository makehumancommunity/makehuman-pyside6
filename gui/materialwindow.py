import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QCheckBox, QSizePolicy, QScrollArea, 
        QPlainTextEdit
        )
from PySide6.QtGui import QPixmap
from obj3d.object3d import object3d
from gui.common import MHTagEdit, IconButton
from gui.materialeditor import MHMaterialEditor


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

        self.setWindowTitle("Material Selection")
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

        hlayout = QHBoxLayout()
        usebutton = QPushButton("Use")
        usebutton.clicked.connect(self.use_call)
        hlayout.addWidget(usebutton)
        editbutton = QPushButton("Edit")
        editbutton.clicked.connect(self.edit_call)
        hlayout.addWidget(editbutton)
        layout.addLayout(hlayout)
        self.setLayout(layout)

    def relMatFileName(self, path):
        """
        create relative materialpath
        """
        itype = self.asset.type
        if itype == "base" or itype == "proxy":
            itype = "skins"
        p1 = self.env.stdSysPath(itype)
        p2 = self.env.stdUserPath(itype)
        if path.startswith(p1):
            path = path[len(p1)+1:]
        elif path.startswith(p2):
            path = path[len(p2)+1:]

        # in case of a common material add type before
        # (e.g. for eyes)
        #
        # otherwise delete leftmost folder
        # except for skins

        if path.startswith("materials"):
            path = os.path.join(itype, path)
        else:
            if itype == "skins":
                path = os.path.join("skins", path)
            else:
                path = os.sep.join(path.split(os.sep)[1:])

        return (path)


    def picButtonChanged(self, matelem):
        if matelem.status == 1:
            # check asset before, if different change
            if matelem.filename != self.oldmaterial:

                # get new material (releases old stuff as well)
                # different for skin (object3d) and asset
                #
                if isinstance(self.asset, object3d):
                    obj = self.asset
                    self.glob.baseClass.skinMaterial = matelem.filename
                    self.glob.baseClass.skinMaterialName = self.relMatFileName(matelem.filename)
                else:
                    # when changing the proxy, the base mesh should get same material
                    #
                    if self.asset.type == "proxy":
                        self.glob.baseClass.skinMaterial = matelem.filename
                        self.glob.baseClass.skinMaterialName = self.relMatFileName(matelem.filename)
                        mainobj = self.glob.baseClass.baseMesh
                        mainobj.newMaterial(matelem.filename)
                        mainobj.openGL.setMaterial(mainobj.material)

                    obj = self.asset.obj
                    self.asset.material = matelem.filename
                    self.asset.materialsource = matelem.filename
                    self.asset.materialsource = self.relMatFileName(matelem.filename)


                obj.newMaterial(matelem.filename)
                #
                # TODO: atm only changing material

                obj.openGL.setMaterial(obj.material)
                self.parent.graph.view.Tweak()
                self.oldmaterial = matelem.filename

        self.picwidget.layout.deselectAllWidgets()
        matelem.status = 1
        self.picwidget.layout.refreshAllWidgets()

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

    def edit_call(self):
        mw = self.parent.material_editor
        if isinstance(self.asset, object3d):
            obj = self.asset
        else:
            obj = self.asset.obj

        if mw is None:
            mw = self.parent.material_editor = MHMaterialEditor(self.parent, obj)
        else:
            mw.updateWidgets(obj)
        mw.show()
        mw.activateWindow()
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
        self.matPath = None
        print(selected)
        self.icon = None
        self.thumb = selected.icon
        self.origtags = ""
        self.origlist = []
        self.owntags = []

        self.currentMatPath(selected.filename)

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
        #
        # different materials are used like this
        # if we have a material, generate name of thumbnail
        # if the thumbnail is the same as the standard material or we still have no thumb we have "no material"
        # then test if file is existent, use empty icon or own icon
        #
        if self.matPath is not None:
            if self.matPath.endswith(".mhmat"):
                matthumb = self.matPath[:-6] + ".thumb"
                print ("Matfile would be: " + matthumb)
                if matthumb == self.thumb or self.thumb is None:
                    print ("but is the standard thumb")
                    self.matPath = None
                else:
                    if os.path.isfile(matthumb):
                        self.thumb = matthumb
                    else:
                        self.thumb = None

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
        if self.matPath is not None:
            self.nameLabel.setText("Name: " + name + "\nMaterial: " +  os.path.basename(self.matPath))
        else:
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

    def currentMatPath(self, filename):
        attached = self.glob.baseClass.getAttachedByFilename(filename)
        if attached is not None:
            self.matPath = attached.obj.getMaterialFilename()
        else:
            self.matPath = None

    def updateWidgets(self, asset, selected, empty, proposals=[]):
        self.asset = asset
        self.emptyIcon = empty
        self.currentMatPath(selected.filename)
        self.icon = None
        if asset is None:
            self.origtags = ""
            self.tagedit.clearTags()
            self.thumb = None
        else:
            self.tagsFromDB()
            self.tagedit.newTags(self.owntags, self.origlist)
            self.thumb = selected.icon
        self.tagedit.newPredefinedTags(proposals)
        self.setName()
        self.tagbox.setPlainText(self.origtags)
        self.displayPixmap()

        self.currentMatPath(selected.filename)

    def use_call(self):
        """
        asset is None: nothing should be done
        skins are only saving a new icon
        materials are using the material path
        """
        if self.asset is None:
            self.close()
            return

        if self.asset.folder != "skins":
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
                #
                # decide if material path

                if self.matPath is not None:
                    path = self.matPath
                else:
                    path = self.asset.path
                    
                iconpath, extension = os.path.splitext(path)
                iconpath += ".thumb"
                print ("Save icon as " + iconpath)
                self.icon.save(iconpath, "PNG", -1)

                # only update database when object icon was changed (not material)
                #
                if self.matPath is None:
                    self.env.fileCache.updateParamInfo(self.asset.uuid, iconpath)
            if self.matPath is None:
                self.changefunc(self.asset, iconpath)
        else:
            if self.icon is not None:
                iconpath, extension = os.path.splitext(self.asset.path)
                iconpath += ".thumb"
                print ("Save icon as " + iconpath)
                self.icon.save(iconpath, "PNG", -1)

        self.close()

    def cancel_call(self):
        self.close()

