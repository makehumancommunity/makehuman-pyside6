from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QAbstractItemView, QLineEdit, QLabel,
    QMessageBox, QRadioButton, QDialogButtonBox, QCheckBox, QComboBox
    )

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from gui.imageselector import MHPictSelectable, PicSelectWidget
from gui.materialwindow import  MHMaterialWindow, MHAssetWindow
from gui.common import DialogBox, ErrorBox, WorkerThread, MHBusyWindow, IconButton, MHTagEdit
import os
from core.globenv import cacheRepoEntry
from core.importfiles import AssetPack
from core.export_gltf import gltfExport
from core.export_stl import stlExport
from core.export_obj import objExport
from core.blender_communication import blendCom

class BaseSelect(QVBoxLayout):
    def __init__(self, parent, callback):
        super().__init__()
        self.parent = parent
        self.env = parent.glob.env
        self.emptyIcon = os.path.join(self.env.path_sysdata, "icons", "empty_material.png")
        self.baseResultList = self.env.getDataDirList("base.obj", "base")

        self.basewidget = QListWidget()
        self.basewidget.setFixedSize(240, 200)
        self.basewidget.addItems(self.baseResultList.keys())
        self.basewidget.setSelectionMode(QAbstractItemView.SingleSelection)
        if self.env.basename is not None:
            items = self.basewidget.findItems(self.env.basename,Qt.MatchExactly)
            if len(items) > 0:
                self.basewidget.setCurrentItem(items[0])
        self.addWidget(self.basewidget)

        buttons = QPushButton("Select")
        buttons.clicked.connect(callback)
        self.addWidget(buttons)

        gb = QGroupBox("Base material")
        gb.setObjectName("subwindow")
        vlayout = QVBoxLayout()
        path = os.path.join(self.env.path_sysicon, "materials.png" )
        vlayout.addWidget(IconButton(0, path, "Set material of body (skin).", self.materialCallback))

        path = os.path.join(self.env.path_sysicon, "information.png" )
        vlayout.addWidget(IconButton(0, path, "Change skin information", self.assetCallback))

        gb.setLayout(vlayout)
        self.addWidget(gb)

    def getCurrentMaterial(self):
        return (self.parent.glob.baseClass.skinMaterial)
        
    def assetCallback(self):
        material = self.getCurrentMaterial()

        # get filename and thumb file, if any
        #
        (folder, name) = os.path.split(material)
        thumb = material[:-6] + ".thumb"
        if not os.path.isfile(thumb):
            thumb =  None

        # create a cacheRepoEntry for skins (there are no skins in repo currently)
        #
        asset = cacheRepoEntry("base", "internal", material, "skins", None, thumb, "makehuman", "")
        p = MHPictSelectable(name[:-6], thumb, material, None, [])
        proposals = []
        if self.parent.asset_window is None:
            #
            # called with "skins" there is no change function
            #
            self.parent.asset_window = MHAssetWindow(self.parent, None, asset, p, self.emptyIcon, proposals)
        else:
            self.parent.asset_window.updateWidgets(asset, p, self.emptyIcon, proposals)
        mw = self.parent.asset_window
        mw.show()
        mw.activateWindow()


    def materialCallback(self):
        p1 = self.env.stdUserPath("skins")
        p2 = self.env.stdSysPath("skins")
        baseClass = self.parent.glob.baseClass
        basemesh = baseClass.baseMesh
        matfiles = basemesh.material.listAllMaterials(p1)
        matfiles.extend(basemesh.material.listAllMaterials(p2))
        #
        # in case of proxy, change first asset
        # TODO: here skinMaterial seems not to be corrected
        #
        if baseClass.proxy:
            basemesh =  baseClass.attachedAssets[0]
        matimg = []
        oldmaterial = self.getCurrentMaterial()
        print(oldmaterial)
        for elem in matfiles:
            #print (elem)
            (folder, name) = os.path.split(elem)
            thumb = elem[:-6] + ".thumb"
            if not os.path.isfile(thumb):
                thumb =  os.path.join(self.env.path_sysicon, "empty_material.png" )
            p = MHPictSelectable(name[:-6], thumb, elem, None, [])
            if elem == oldmaterial:
                p.status = 1
            matimg.append(p)
        if self.parent.material_window is None:
            self.parent.material_window = MHMaterialWindow(self.parent, PicSelectWidget, matimg, basemesh)
        else:
            self.parent.material_window.updateWidgets(matimg, basemesh)

        mw = self.parent.material_window
        mw.show()
        mw.activateWindow()


    def getSelectedItem(self):
        sel = self.basewidget.selectedItems()
        if len(sel) > 0:
            name = sel[0].text()
            return (name, self.baseResultList[name])

        return (None, None)


class SaveMHMForm(QVBoxLayout):
    """
    create a form with name, tags, uuid, thumbnail, filename
    """
    def __init__(self, parent, view, characterselection, displaytitle):
        self.view = view
        self.parent = parent
        self.glob = parent.glob
        env = self.glob.env
        self.bc  = self.glob.baseClass
        self.displaytitle = displaytitle
        super().__init__()

        # photo
        #
        ilayout = QHBoxLayout()
        ilayout.addWidget(IconButton(1,  os.path.join(env.path_sysicon, "camera.png"), "Thumbnail", self.thumbnail))
        self.imglabel=QLabel()
        self.displayPixmap()
        ilayout.addWidget(self.imglabel, alignment=Qt.AlignRight)
        self.addLayout(ilayout)

        # name
        #
        self.addWidget(QLabel("Name of character:"))
        self.editname = QLineEdit(self.bc.name)
        self.editname.editingFinished.connect(self.newname)
        self.addWidget(self.editname)

        # uuid
        #
        ilayout = QHBoxLayout()
        ilayout.addWidget(QLabel("\nUUID:"))
        self.regenbutton=QPushButton("Generate UUID")
        self.regenbutton.clicked.connect(self.genuuid)
        ilayout.addWidget(self.regenbutton, alignment=Qt.AlignBottom)
        self.addLayout(ilayout)
        uuid = self.bc.uuid if hasattr(self.bc, "uuid") else ""
        self.uuid = QLineEdit(uuid)
        self.uuid.editingFinished.connect(self.newuuid)
        self.addWidget(self.uuid)

        # tags
        #
        self.tagedit = MHTagEdit(self.glob, self.bc.tags, "\nTags:",
                predefined= characterselection.getTagProposals())
        self.addLayout(self.tagedit)

        # filename
        #
        self.addWidget(QLabel("\nFilename:"))
        self.filename = QLineEdit(self.bc.name + ".mhm")
        self.filename.editingFinished.connect(self.newfilename)
        self.addWidget(self.filename)
        self.savebutton=QPushButton("Save")
        self.savebutton.clicked.connect(self.savefile)
        self.addWidget(self.savebutton)

    def savefile(self):
        """
        path calculation
        ask if is already exists
        save file, save icon
        """
        path = self.glob.env.stdUserPath("models", self.filename.text())
        self.bc.tags = self.tagedit.getTags()
        if os.path.isfile(path):
            dbox = DialogBox("Replace " + path + "?", QDialogButtonBox.Ok)
            confirmed = dbox.exec()
            if confirmed != 1:
                return

        if self.bc.saveMHMFile(path):
            QMessageBox.information(self.parent, "Done!", "Character saved as " + path)
        else:
            ErrorBox(self.parent, self.glob.env.last_error)
        if self.bc.photo is not None:
            iconpath = path[:-4] + ".thumb"
            self.bc.photo.save(iconpath, "PNG", -1)

    def newfilename(self):
        """
        not empty, always ends with mhm
        """
        text = self.filename.text()
        if len(text) == 0:
            text = self.editname.text()
        if not text.endswith(".mhm"):
            self.filename.setText(text + ".mhm")

    def newname(self):
        """
        when empty, then 'base', create filename in case of no filename available
        """
        text = self.editname.text()
        if len(text) == 0:
            self.editname.setText("base")

        self.bc.name = text
        self.displaytitle(text)
        if self.filename.text() == "":
            self.filename.setText(text + ".mhm")

    def genuuid(self):
        self.bc.uuid = self.glob.gen_uuid()
        self.uuid.setText(self.bc.uuid)

    def newuuid(self):
        self.bc.uuid = self.uuid.text()

    def displayPixmap(self):
        if self.bc.photo is None:
            pixmap = QPixmap(os.path.join(self.glob.env.path_sysicon, "empty_models.png"))
        else:
            pixmap = QPixmap.fromImage(self.bc.photo)
        self.imglabel.setPixmap(pixmap)

    def thumbnail(self):
        self.bc.photo = self.view.createThumbnail()
        self.displayPixmap()

    def addDataFromSelected(self, asset):
        """
        copies data from a selected asset to filename
        """
        self.filename.setText(asset.basename)
        self.editname.setText(asset.name)
        #
        # tags: last 3 tags are name, filename, author, tags with ';' only take last element
        #
        tags = []
        for elem in asset.tags[:-3]:
            if ":" in elem:
                elem = elem.split(":")[-1]
            tags.append(elem)
        self.tagedit.newTags(tags, None)

        # generate the icon from selected icon
        #
        if asset.icon is not None:
            pixmap = QPixmap(asset.icon)
            self.bc.photo = pixmap.toImage()
        else:
            self.bc.photo = None
        self.displayPixmap()


class ExportLeftPanel(QVBoxLayout):
    """
    create a form with filename (+ other features later)
    """
    def __init__(self, parent):
        self.parent = parent
        self.glob = parent.glob
        self.bc  = parent.glob.baseClass
        self.binmode = True
        self.onground = True
        self.helper = False
        self.normals = False
        self.savehiddenverts = False
        self.export_type = ".glb"
        super().__init__()
        self.scale_items = [
            [ 0.1, "Meter"],
            [ 1.0, "Decimeter"],
            [ 3.937, "Inch"],
            [ 10.0, "Centimeter"],
            [ 100.0, "Millimeter"]
        ]

        scaletexts = []
        for elem in self.scale_items:
            scaletexts.append(str(elem[0]) + "   " + elem[1])

        # filename
        #
        self.addWidget(QLabel("\nFilename:"))
        self.filename = QLineEdit(self.bc.name + self.export_type)
        self.filename.editingFinished.connect(self.newfilename)
        self.addWidget(self.filename)

        self.binsave= QCheckBox("binary mode")
        self.binsave.setLayoutDirection(Qt.LeftToRight)
        self.binsave.toggled.connect(self.changeBinary)
        self.binsave.setChecked(True)
        self.binsave.setToolTip('Some exports offer binary and ASCII modes, binary mode is usually faster and smaller')
        self.addWidget(self.binsave)

        self.ground= QCheckBox("feet on ground")
        self.ground.setLayoutDirection(Qt.LeftToRight)
        self.ground.toggled.connect(self.changeGround)
        self.ground.setChecked(True)
        self.ground.setToolTip('When characters origin is not at the ground, this option corrects the position')
        self.addWidget(self.ground)

        self.hverts= QCheckBox("save hidden vertices")
        self.hverts.setLayoutDirection(Qt.LeftToRight)
        self.hverts.toggled.connect(self.changeHVerts)
        self.hverts.setChecked(False)
        self.hverts.setToolTip('Export of hidden vertices is only useful, when destination is able to edit mesh')
        self.addWidget(self.hverts)
        
        self.helper= QCheckBox("save helper")
        self.helper.setLayoutDirection(Qt.LeftToRight)
        self.helper.toggled.connect(self.changeHelper)
        self.helper.setChecked(False)
        self.helper.setToolTip('For special purposes the invisible helper can be exported, vertices of the body are NOT hidden in this case')
        self.addWidget(self.helper)

        self.norm= QCheckBox("normals")
        self.norm.setLayoutDirection(Qt.LeftToRight)
        self.norm.toggled.connect(self.changeNormals)
        self.norm.setChecked(False)
        self.norm.setToolTip('Some applications need the vertex normals to create a smoothed mesh')
        self.addWidget(self.norm)

        self.addWidget(QLabel("Scaling:"))
        self.scalebox = QComboBox()
        self.scalebox.addItems(scaletexts)
        self.scalebox.setToolTip('MakeHuman works with decimeter system, destination system usually differs')
        self.addWidget(self.scalebox)

        self.exportbutton=QPushButton("Export")
        self.exportbutton.clicked.connect(self.exportfile)
        self.addWidget(self.exportbutton)
        #
        # start with glb
        #
        self.setExportType(self.export_type)

    def setExportType(self, etype):
        common = "MakeHuman works with unit decimeter. "
        expAttrib = { ".stl":  {"tip": common + "STL files are unit less. When working with printers 1 unit equals 1 millimeter (preset scale 1:10)",
                "num": 3, "binset": True, "binmode": "both", "helpset": False, "helpmode": False, "normset": False, "normmode": False},
            ".glb": { "tip": common + "GLB/GLTF units are usually meters",
                "num": 0, "binset": False, "binmode": True, "helpset": False, "helpmode": False, "normset": False, "normmode": True},
            ".mh2b": { "tip": common + "Blender units are usually meters",
                "num": 0, "binset": False, "binmode": True, "helpset": False, "helpmode": False, "normset": False, "normmode": False},
            ".obj": { "tip": common + "Wavefront units are usually meters",
                "num": 0, "binset": False, "binmode": False, "helpset": True, "helpmode": False, "normset": True, "normmode": False}
            }

        # set options according to type
        #
        self.export_type = etype
        self.newfilename()
        if expAttrib[self.export_type]["binmode"] != "both":
            self.binsave.setChecked(expAttrib[self.export_type]["binmode"])
        self.binsave.setEnabled(expAttrib[self.export_type]["binset"])

        self.helper.setChecked(expAttrib[self.export_type]["helpmode"])
        self.helper.setEnabled(expAttrib[self.export_type]["helpset"])

        self.norm.setChecked(expAttrib[self.export_type]["normmode"])
        self.norm.setEnabled(expAttrib[self.export_type]["normset"])

        self.scalebox.setCurrentIndex(expAttrib[self.export_type]["num"])
        self.scalebox.setToolTip(expAttrib[self.export_type]["tip"])

    def changeBinary(self, param):
        self.binmode = param

    def changeHVerts(self, param):
        self.savehiddenverts = param

    def changeGround(self, param):
        self.onground = param

    def changeHelper(self, param):
        self.helper = param

    def changeNormals(self, param):
        self.normals = param

    def newfilename(self):
        """
        not empty, always ends with export type
        """
        text = self.filename.text()
        if not text.endswith(self.export_type):
            text = os.path.splitext(text)[0]
            self.filename.setText(text + self.export_type)

    def exportfile(self):
        """
        path calculation, save file, save icon
        """
        folder = self.glob.env.stdUserPath("exports")
        path = os.path.join(folder, self.filename.text())
        current = self.scalebox.currentIndex()
        scale = self.scale_items[current][0]

        if self.export_type == ".glb":
            gltf = gltfExport(self.glob, folder, self.savehiddenverts, self.onground, scale)
            success = gltf.binSave(self.bc, path)

        elif self.export_type == ".stl":
            stl = stlExport(self.glob, folder, self.savehiddenverts, scale)
            if self.binmode:
                success = stl.binSave(self.bc, path)
            else:
                success = stl.ascSave(self.bc, path)

        elif self.export_type == ".mh2b":
            blcom = blendCom(self.glob, folder, self.savehiddenverts, self.onground, scale)
            success = blcom.binSave(self.bc, path)

        elif self.export_type == ".obj":
            obj = objExport(self.glob, folder, self.savehiddenverts, self.onground, self.helper, self.normals, scale)
            success = obj.ascSave(self.bc, path)
        else:
            print ("not yet implemented")
            return

        if success:
            QMessageBox.information(self.parent, "Done!", "Character exported as " + path)
        else:
            ErrorBox(self.parent, self.glob.env.last_error)


class ExportRightPanel(QVBoxLayout):
    def __init__(self, parent, connector):
        super().__init__()
        self.parent = parent
        self.glob = parent.glob
        self.env = self.glob.env
        self.leftPanel = connector
        self.exportimages = [
                { "button": None, "icon": "gltf_sym.png", "tip": "export as GLTF2/GLB", "func": self.exportgltf},
                { "button": None, "icon": "stl_sym.png", "tip": "export as STL (Stereolithography)", "func": self.exportstl},
                { "button": None, "icon": "blend_sym.png", "tip": "export as MH2B (Blender)", "func": self.exportmh2b},
                { "button": None, "icon": "wavefront_sym.png", "tip": "export as OBJ (Wavefront)", "func": self.exportobj}
        ]
        for n, b in enumerate(self.exportimages):
            b["button"] = IconButton(n, os.path.join(self.env.path_sysicon, b["icon"]), b["tip"], b["func"], 130)
            self.addWidget(b["button"])

        self.setChecked(0)
        self.addStretch()

    def setChecked(self, num):
        for i, elem in enumerate(self.exportimages):
            elem["button"].setChecked(i==num)

    def exportgltf(self):
        print ("export GLTF called")
        self.leftPanel.setExportType(".glb")
        self.setChecked(0)

    def exportstl(self):
        print ("export STL called")
        self.leftPanel.setExportType(".stl")
        self.setChecked(1)

    def exportmh2b(self):
        print ("export MH2B called")
        self.leftPanel.setExportType(".mh2b")
        self.setChecked(2)

    def exportobj(self):
        print ("export OBJ called")
        self.leftPanel.setExportType(".obj")
        self.setChecked(3)

class DownLoadImport(QVBoxLayout):
    def __init__(self, parent, view, displaytitle):
        self.parent = parent
        self.view = view
        self.env = parent.env
        self.displaytitle = displaytitle
        self.bckproc = None     # will contain process running in parallel
        self.error   = None     # will contain possible error text
        self.zipfile = None     # last loaded zipfile
        self.use_userpath = True
        self.assets = AssetPack()

        super().__init__()

        # name
        #
        ilayout = QVBoxLayout()
        ilayout.addWidget(QLabel("To download an asset pack, check name here:"))
        #
        # link
        #
        linklabel = QLabel()
        ltext = "<a href='" + self.env.release_info["url_assetpacks"] + "'>Asset Packs</a>"
        linklabel.setText(ltext)
        linklabel.setOpenExternalLinks(True)
        ilayout.addWidget(linklabel)


        ilayout.addWidget(QLabel("then copy URL into this box, press Download:"))
        self.url = QLineEdit("")
        ilayout.addWidget(self.url)
        self.dlbutton=QPushButton("Download")
        self.dlbutton.clicked.connect(self.downLoad)
        ilayout.addWidget(self.dlbutton)

        ilayout.addWidget(QLabel("\nBase is: " + self.env.basename))
        userpath = QLabel("Destination user path:\n"+ self.env.path_userdata)
        userpath.setToolTip("Files will be extracted to " + self.env.basename + " folders in "  + self.env.path_userdata)
        ilayout.addWidget(userpath)

        if self.env.admin:
            syspath = QLabel("Destination system path:\n"+ self.env.path_sysdata)
            syspath.setToolTip("Files will be extracted to " + self.env.basename + " folders in "  + self.env.path_sysdata)
            ilayout.addWidget(syspath)

            self.userbutton = QRadioButton("Install in your user path")
            self.userbutton.setChecked(True)
            self.systembutton = QRadioButton("Install in system path")
            self.userbutton.toggled.connect(self.setMethod)
            self.systembutton.toggled.connect(self.setMethod)
            ilayout.addWidget(self.userbutton)
            ilayout.addWidget(self.systembutton)


        ilayout.addWidget(QLabel("\nAfter download use the filename inserted by\nprogram or type in a name of an already\ndownloaded file and press extract:"))
        self.filename = QLineEdit("")
        self.filename.setText(self.parent.glob.lastdownload)
        ilayout.addWidget(self.filename)

        self.savebutton=QPushButton("Extract")
        self.savebutton.clicked.connect(self.extractZip)
        ilayout.addWidget(self.savebutton)

        ilayout.addWidget(QLabel("\nIf the downloaded file is no longer needed,\npress cleanup to delete the temporary folder"))
        self.clbutton=QPushButton("Clean Up")
        self.clbutton.clicked.connect(self.cleanUp)
        ilayout.addWidget(self.clbutton)
        self.addLayout(ilayout)

    def setMethod(self, value):
        if self.userbutton.isChecked():
            self.use_userpath = True
        else:
            self.use_userpath = False

    def par_unzip(self, bckproc, *args):
        tempdir = self.assets.unZip(self.filename.text())
        destpath = self.env.path_sysdata if self.use_userpath is False else self.env.path_userdata
        print (tempdir, destpath, self.env.basename)
        #self.assets.copyAssets(tempdir, destpath, self.env.basename)

    def finishUnzip(self):
        self.assets.cleanupUnzip()
        if self.prog_window is not None:
            self.prog_window.progress.close()
            self.prog_window = None
        QMessageBox.information(self.parent, "Done!", self.bckproc.finishmsg)
        self.bckproc = None

    def extractZip(self):
        print ("extract Zipfile")
        fname = self.filename.text()
        if not fname.endswith(".zip"):
            ErrorBox(self.parent, "Filename should have the suffix .zip")
            return

        if self.bckproc == None:
            self.prog_window = MHBusyWindow("Extract ZIP file", "extracting ...")
            self.prog_window.progress.forceShow()
            self.bckproc = WorkerThread(self.par_unzip, None)
            self.bckproc.start()
            self.bckproc.finishmsg = "Zip file has been imported"
            self.bckproc.finished.connect(self.finishUnzip)

    def par_download(self, bckproc, *args):
        tempdir = args[0][0]
        filename = args[0][1]
        self.error = None
        print (tempdir)
        print (filename)
        (err, text) = self.assets.getAssetPack(self.url.text(), tempdir, filename)
        self.error = text

    def finishLoad(self):
        if self.prog_window is not None:
            self.prog_window.progress.close()
            self.prog_window = None
        if self.error:
            ErrorBox(self.parent, self.error)
        else:
            QMessageBox.information(self.parent, "Done!", self.bckproc.finishmsg)
        self.bckproc = None

    def downLoad(self):
        print ("Download")
        url = self.url.text()
        if not (url.startswith("ftp:") or url.startswith("http:") or url.startswith("https:")):
            ErrorBox(self.parent, "URL must start with a known protocol [http, https, ftp]")
            return
        filename = os.path.split(url)[1]

        if self.bckproc == None:
            tempdir = self.assets.tempDir()
            self.parent.glob.lastdownload = os.path.join(tempdir, filename)
            self.filename.setText(self.parent.glob.lastdownload)
            self.prog_window = MHBusyWindow("Download Assetfile to " + tempdir, "loading ...")
            self.prog_window.progress.forceShow()
            self.bckproc = WorkerThread(self.par_download, tempdir, filename)
            self.bckproc.start()
            self.bckproc.finishmsg = "Download finished"
            self.bckproc.finished.connect(self.finishLoad)

    def cleanUp(self):
        fullpath = self.parent.glob.lastdownload
        if fullpath is not None:
            (fpath, fname ) = os.path.split(fullpath)
            if os.path.isfile(fullpath):
                os.remove(fullpath)
            os.rmdir(fpath)
            self.parent.glob.lastdownload = None
            self.filename.setText(self.parent.glob.lastdownload)
