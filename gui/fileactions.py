"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * BaseSelect
    * SaveMHMForm
    * ExportLeftPanel
    * ExportRightPanel
    * DownLoadImport
"""
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QAbstractItemView, QLineEdit, QLabel,
    QMessageBox, QRadioButton, QDialogButtonBox, QCheckBox, QComboBox
    )

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from gui.poseactions import AnimMode
from gui.imageselector import MHPictSelectable, PicSelectWidget
from gui.materialwindow import  MHMaterialSelect, MHAssetWindow
from gui.memwindow import MHSelectAssetWindow
from gui.common import DialogBox, ErrorBox, WorkerThread, MHBusyWindow, IconButton, MHTagEdit, MHFileRequest
from opengl.texture import MH_Thumb
from core.globenv import cacheRepoEntry
from core.importfiles import AssetPack
from core.export_gltf import gltfExport
from core.export_stl import stlExport
from core.export_obj import objExport
from core.export_bvh import bvhExport
from core.blender_communication import blendCom

import os

class BaseSelect(QVBoxLayout):
    def __init__(self, parent, callback):
        super().__init__()
        self.parent = parent
        self.glob = parent.glob
        self.env = parent.glob.env
        self.emptyIcon = os.path.join(self.env.path_sysdata, "icons", "empty_material.png")
        self.baseResultList = self.env.getDataDirList("base.obj", "base")

        if self.parent.glob.baseClass is None:
            self.addWidget(QLabel("<h1>You need to select<br>a basemesh first!</h1>"))

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
        self.materialbutton = IconButton(0, path, "Set material of body (skin).", self.materialCallback)
        vlayout.addWidget(self.materialbutton)

        path = os.path.join(self.env.path_sysicon, "information.png" )
        self.infobutton = IconButton(0, path, "Change skin information", self.assetCallback)
        vlayout.addWidget(self.infobutton)
        self.activateButtons()

        gb.setLayout(vlayout)
        self.addWidget(gb)
        self.addStretch()

    def activateButtons(self):
        enabled = self.parent.glob.baseClass is not None
        self.materialbutton.setEnabled(enabled)
        self.infobutton.setEnabled(enabled)

    def getCurrentMaterial(self):
        return (self.parent.glob.baseClass.skinMaterial)
        
    def assetCallback(self):
        material = self.getCurrentMaterial()

        if material is None:
            ErrorBox(self.parent, "No materials available")
            return

        # get filename and thumb file, if any
        #
        (folder, name) = os.path.split(material)
        thumb = material[:-6] + ".thumb"
        if not os.path.isfile(thumb):
            thumb =  None

        # create a cacheRepoEntry for skins (there are no skins in repo currently)
        #
        asset = cacheRepoEntry("base", "internal", material, "skins", None, thumb, "makehuman", "")
        proposals = []

        mw = self.glob.getSubwindow("asset")
        if mw is None:
            #
            # called with "skins" there is no change function
            #
            mw = self.glob.showSubwindow("asset", self.parent,  MHAssetWindow, None, asset, self.emptyIcon, proposals)
        else:
            mw.updateWidgets(asset, self.emptyIcon, proposals)
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

        mw = self.glob.getSubwindow("material")
        if mw is None:
            mw = self.glob.showSubwindow("material", self.parent, MHMaterialSelect, PicSelectWidget, matimg, basemesh)
        else:
            mw.updateWidgets(matimg, basemesh)
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

        # author
        #
        self.addWidget(QLabel("Author:"))
        self.authname = QLineEdit(self.bc.author)
        self.authname.editingFinished.connect(self.newauthor)
        self.addWidget(self.authname)

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

    def newauthor(self):
        text = self.authname.text()
        if len(text) == 0:
            self.editname.setText("unknown")
        self.bc.author = text

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
        self.animmode = None        # will keep animation mode
        self.binmode = True
        self.onground = True
        self.helper = False
        self.normals = False
        self.animation = False
        self.inpose = False
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

        self.posed= QCheckBox("character posed")
        self.posed.setLayoutDirection(Qt.LeftToRight)
        self.posed.toggled.connect(self.changePosed)
        self.posed.setChecked(True)
        self.posed.setToolTip('Export character posed instead of default pose (set pose in animation)')
        self.addWidget(self.posed)

        self.hverts= QCheckBox("save hidden vertices")
        self.hverts.setLayoutDirection(Qt.LeftToRight)
        self.hverts.toggled.connect(self.changeHVerts)
        self.hverts.setChecked(False)
        self.hverts.setToolTip('Export of hidden vertices is only useful, when destination is able to edit mesh')
        self.addWidget(self.hverts)

        self.anim= QCheckBox("save animation")
        self.anim.setLayoutDirection(Qt.LeftToRight)
        self.anim.toggled.connect(self.changeAnim)
        self.anim.setChecked(False)
        self.anim.setToolTip('If an animation is loaded it can be appended to the export')
        self.addWidget(self.anim)
        
        self.helperw= QCheckBox("save helper")
        self.helperw.setLayoutDirection(Qt.LeftToRight)
        self.helperw.toggled.connect(self.changeHelper)
        self.helperw.setChecked(False)
        self.helperw.setToolTip('For special purposes the invisible helper can be exported, vertices of the body are NOT hidden in this case')
        self.addWidget(self.helperw)

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

    def leave(self):
        if self.animmode is not None:
            self.animmode.leave()

    def setExportType(self, etype):
        common = "MakeHuman works with unit decimeter. "
        expAttrib = { ".stl":  {"tip": common + "STL files are unit less. When working with printers 1 unit equals 1 millimeter (preset scale 1:10)",
                "num": 3, "binset": True, "binmode": "both", "hiddenset": True, "hiddenmode": False,
                "animset": False, "animmode": False, "poseset": True, "posemode": False,
                "helpset": False, "helpmode": False, "normset": False, "normmode": False},
            ".glb": { "tip": common + "GLB/GLTF units are usually meters",
                "num": 0, "binset": False, "binmode": True, "hiddenset": True, "hiddenmode": False,
                "animset": True, "animmode": False, "poseset": False, "posemode": False,
                "helpset": False, "helpmode": False, "normset": False, "normmode": True},
            ".mh2b": { "tip": common + "Blender units are usually meters",
                "num": 0, "binset": False, "binmode": True, "hiddenset": True, "hiddenmode": False,
                "animset": True, "animmode": False, "poseset": False, "posemode": False,
                "helpset": False, "helpmode": False, "normset": False, "normmode": False},
            ".obj": { "tip": common + "Wavefront units are usually meters",
                "num": 0, "binset": False, "binmode": False, "hiddenset": True, "hiddenmode": False,
                "animset": False, "animmode": False, "poseset": False, "posemode": False,
                "helpset": True, "helpmode": False, "normset": True, "normmode": False},
            ".bvh": { "tip": common + "BVH units are usually the same as the internal scale",
                "num": 0, "binset": False, "binmode": False,  "hiddenset": False, "hiddenmode": False,
                "animset": False, "animmode": True, "poseset": False, "posemode": False,
                "helpset": False, "helpmode": False, "normset": False, "normmode": False}
            }

        # set options according to type
        #
        self.export_type = etype
        self.newfilename()
        if expAttrib[self.export_type]["binmode"] != "both":
            self.binsave.setChecked(expAttrib[self.export_type]["binmode"])
        self.binsave.setEnabled(expAttrib[self.export_type]["binset"])
        #
        self.hverts.setChecked(expAttrib[self.export_type]["hiddenmode"])
        self.hverts.setEnabled(expAttrib[self.export_type]["hiddenset"])

        self.helperw.setChecked(expAttrib[self.export_type]["helpmode"])
        self.helperw.setEnabled(expAttrib[self.export_type]["helpset"])

        self.norm.setChecked(expAttrib[self.export_type]["normmode"])
        self.norm.setEnabled(expAttrib[self.export_type]["normset"])

        self.anim.setChecked(expAttrib[self.export_type]["animmode"])
        self.anim.setEnabled(expAttrib[self.export_type]["animset"])

        self.posed.setChecked(expAttrib[self.export_type]["posemode"])
        self.posed.setEnabled(expAttrib[self.export_type]["poseset"])

        self.scalebox.setCurrentIndex(expAttrib[self.export_type]["num"])
        self.scalebox.setToolTip(expAttrib[self.export_type]["tip"])

    def changeBinary(self, param):
        self.binmode = param

    def changeHVerts(self, param):
        self.savehiddenverts = param

    def changeGround(self, param):
        self.onground = param

    def changePosed(self, param):
        if self.animmode is None:
            self.animmode = AnimMode(self.glob)
        else:
            self.animmode.leave()
            self.animmode = None
        self.inpose = param

    def changeHelper(self, param):
        self.helper = param

    def changeNormals(self, param):
        self.normals = param

    def changeAnim(self, param):
        self.animation = param

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
            gltf = gltfExport(self.glob, folder, self.savehiddenverts, self.onground,  self.animation, scale)
            success = gltf.binSave(self.bc, path)

        elif self.export_type == ".stl":
            stl = stlExport(self.glob, folder, self.savehiddenverts, scale)
            if self.binmode:
                success = stl.binSave(self.bc, path)
            else:
                success = stl.ascSave(self.bc, path)

        elif self.export_type == ".mh2b":
            blcom = blendCom(self.glob, folder, self.savehiddenverts, self.onground, self.animation, scale)
            success = blcom.binSave(self.bc, path)

        elif self.export_type == ".obj":
            obj = objExport(self.glob, folder, self.savehiddenverts, self.onground, self.helper, self.normals, scale)
            success = obj.ascSave(self.bc, path)

        elif self.export_type == ".bvh":
            bvh = bvhExport(self.glob, self.onground, scale)
            success = bvh.ascSave(self.bc, path)

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
                { "button": None, "icon": "wavefront_sym.png", "tip": "export as OBJ (Wavefront)", "func": self.exportobj},
                { "button": None, "icon": "bvh_sym.png", "tip": "export animation/pose as BVH (BioVision Hierarchy)", "func": self.exportbvh}
        ]
        for n, b in enumerate(self.exportimages):
            b["button"] = IconButton(n, os.path.join(self.env.path_sysicon, b["icon"]), b["tip"], b["func"], 130, checkable=True)
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

    def exportbvh(self):
        print ("export BVH called")
        self.leftPanel.setExportType(".bvh")
        self.setChecked(4)

class DownLoadImport(QVBoxLayout):
    def __init__(self, parent, view, displaytitle):
        self.parent = parent
        self.glob = parent.glob
        self.env = parent.env
        self.view = view
        self.displaytitle = displaytitle
        self.bckproc = None     # will contain process running in parallel
        self.error   = None     # will contain possible error text
        self.zipfile = None     # last loaded zipfile
        self.assetlistpath = None
        self.assetjson = None
        self.use_userpath = True
        self.assets = AssetPack()

        super().__init__()

        gb = QGroupBox("Single Asset")
        gb.setObjectName("subwindow")
        vlayout = QVBoxLayout()
        assetname = os.path.split(self.env.release_info["url_assetlist"])[1]
        self.assetlistpath = os.path.join(self.env.path_userdata, "downloads", self.env.basename, assetname)
        self.latest = self.assets.testAssetList(self.assetlistpath)
        if self.latest is None:
            self.asdlbutton=QPushButton("Download Asset List")
        else:
            self.asdlbutton=QPushButton("Replace Current Asset List [" + self.latest + "]")

        self.asdlbutton.clicked.connect(self.listDownLoad)
        self.asdlbutton.setToolTip("The asset list is needed to load single assets.<br>This must be done once.<br>Usually you only need to reload the list if new assets are available.")
        vlayout.addWidget(self.asdlbutton)

        vlayout.addWidget(QLabel("\nEnter title or URL of asset [copy/paste from browser]<br>or select from list"))
        hlayout = QHBoxLayout()
        self.selbutton=QPushButton("Select")
        self.selbutton.setEnabled(self.latest is not None)
        self.selbutton.clicked.connect(self.selectfromList)
        self.selbutton.setToolTip("Select asset from asset list.")
        hlayout.addWidget(self.selbutton)
        self.singlename = QLineEdit("")
        self.singlename.editingFinished.connect(self.singleinserted)
        hlayout.addWidget(self.singlename)
        vlayout.addLayout(hlayout)

        self.sidlbutton=QPushButton("Download Single Asset")
        self.sidlbutton.clicked.connect(self.singleDownLoad)
        vlayout.addWidget(self.sidlbutton)

        gb.setLayout(vlayout)
        self.addWidget(gb)

        gb = QGroupBox("Asset Pack")
        gb.setObjectName("subwindow")

        # name and link
        #
        ilayout = QVBoxLayout()
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel("Check name of asset pack here:"))
        linklabel = QLabel()
        ltext = "<a href='" + self.env.release_info["url_assetpacks"] + "'>Asset Packs</a>"
        linklabel.setText(ltext)
        linklabel.setOpenExternalLinks(True)
        hlayout.addWidget(linklabel)
        ilayout.addLayout(hlayout)

        ilayout.addWidget(QLabel("then copy URL into this box, press Download:"))
        self.packname = QLineEdit("")
        self.packname.editingFinished.connect(self.packinserted)
        ilayout.addWidget(self.packname)

        self.dlbutton=QPushButton("Download Asset Pack")
        self.dlbutton.clicked.connect(self.downLoad)
        ilayout.addWidget(self.dlbutton)

        userpath = QLabel("Destination user path for base: "  + self.env.basename + "\n"+ self.env.path_userdata)
        userpath.setToolTip("Files will be extracted to " + self.env.basename + " folders in "  + self.env.path_userdata)
        ilayout.addWidget(userpath)

        if self.env.admin:
            syspath = QLabel("Destination system path for base: " + self.env.basename + "\n"+ self.env.path_sysdata)
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
        self.filename.editingFinished.connect(self.fnameinserted)
        self.filename.setText(self.parent.glob.lastdownload)
        ilayout.addWidget(self.filename)

        self.savebutton=QPushButton("Extract")
        self.savebutton.clicked.connect(self.extractZip)
        ilayout.addWidget(self.savebutton)

        ilayout.addWidget(QLabel("\nIf the downloaded file is no longer needed,\npress cleanup to delete the temporary folder"))
        self.clbutton=QPushButton("Clean Up")
        self.clbutton.clicked.connect(self.cleanUp)
        ilayout.addWidget(self.clbutton)
        gb.setLayout(ilayout)
        self.addWidget(gb)
        self.singleinserted()
        self.packinserted()
        self.fnameinserted()

    def setMethod(self, value):
        if self.userbutton.isChecked():
            self.use_userpath = True
        else:
            self.use_userpath = False

    def singleinserted(self):
        self.sidlbutton.setEnabled(len(self.singlename.text()) > 0)

    def packinserted(self):
        self.dlbutton.setEnabled(len(self.packname.text()) > 0)

    def fnameinserted(self):
        self.savebutton.setEnabled(len(self.filename.text()) > 0)

    def fillSingleName(self, value):
        self.singlename.setText("%" + value)
        self.singleinserted()

    def selectfromList(self):
        if self.assetjson is None:
            self.assetjson =  self.assets.alistReadJSON(self.env, self.assetlistpath)
        w = self.glob.showSubwindow("loadasset", self, MHSelectAssetWindow, self.assetjson)
        w.setParam(self.fillSingleName)

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
        (err, text) = self.assets.getAssetPack(self.packname.text(), tempdir, filename)
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

    def finishListLoad(self):
        if self.prog_window is not None:
            self.prog_window.progress.close()
            self.prog_window = None
        if self.error:
            ErrorBox(self.parent, self.error)
        else:
            QMessageBox.information(self.parent, "Done!", self.bckproc.finishmsg)
        self.bckproc = None
        self.latest = self.assets.testAssetList(self.assetlistpath)
        self.selbutton.setEnabled(self.latest is not None)


    def downLoad(self):
        print ("Download")
        url = self.packname.text()
        if not (url.startswith("ftp:") or url.startswith("http:") or url.startswith("https:")):
            ErrorBox(self.parent, "URL must start with a known protocol [http, https, ftp]")
            return
        filename = os.path.split(url)[1]

        if self.bckproc == None:
            tempdir = self.assets.tempDir()
            self.parent.glob.lastdownload = os.path.join(tempdir, filename)
            self.filename.setText(self.parent.glob.lastdownload)
            self.fnameinserted()
            self.prog_window = MHBusyWindow("Download pack to " + tempdir, "loading ...")
            self.prog_window.progress.forceShow()
            self.bckproc = WorkerThread(self.par_download, tempdir, filename)
            self.bckproc.start()
            self.bckproc.finishmsg = "Download finished"
            self.bckproc.finished.connect(self.finishLoad)

    def par_listdownload(self, bckproc, *args):
        destination = args[0][0]
        self.error = None
        (err, text) = self.assets.getUrlFile(self.env.release_info["url_assetlist"], destination)
        self.error = text

    def listDownLoad(self):
        url = self.env.release_info["url_assetlist"]
        if self.bckproc == None:
            self.assetjson = None       # reset this
            self.prog_window = MHBusyWindow("Download list to " + self.assetlistpath, "loading ...")
            self.prog_window.progress.forceShow()
            self.bckproc = WorkerThread(self.par_listdownload, self.assetlistpath)
            self.bckproc.start()
            self.bckproc.finishmsg = "Download finished"
            self.bckproc.finished.connect(self.finishListLoad)

    def par_filesdownload(self, bckproc, *args):
        destination = args[0][0]
        files = args[0][1]
        self.error = None
        for elem in files:
            dest = os.path.split(elem)[1]
            self.env.logLine(8, "Get: " + elem + " >" + destination)
            self.prog_window.setLabelText("Loading: " + elem)
            destpath = os.path.join(destination, dest)
            (loaded, text) = self.assets.getUrlFile(elem, destpath)
            if loaded is False:
                self.error = text
                return
            #
            # resize thumbfile if needed or recreate targetlist
            #
            if destpath.endswith(".thumb"):
                thumb = MH_Thumb()
                thumb.rescale(destpath)
            elif destpath.endswith(".target"):
                self.glob.Targets.categories.newUserCategories()
                tname, t = self.glob.Targets.categories.findUserAsset(dest)
                if tname is not None:
                    self.glob.Targets.createTarget(tname, t)
                else:
                    self.error = "target not found, please restart makehuman"

        self.error = text

    def parentAsset(self, key):
        """
        calculate path of parent asset or return a path to type if possible
        """
        pobj = self.assetjson[key]["belongs_to"]
        if pobj["belonging_is_assigned"] is False:
            #
            # asset missing return User-data path
            return False, self.env.path_userdata
        else:
            if "belongs_to_core_asset" in pobj:
                #
                # core assets must be recalculated (basename added).
                # eyes will always go into a common folder

                (mtype, folder) = pobj["belongs_to_core_asset"].split("/", 2)
                if mtype == "eyes":
                    path = self.env.existDataDir(mtype, self.env.basename)
                else:
                    path = self.env.existDataDir(mtype, self.env.basename, folder)
                if path is None:
                    self.env.last_error = "core assets not found: " + pobj["belongs_to_core_asset"]
                    return False, None

                return True, path

            parentkey = str(pobj["belongs_to_id"])
            mtype = self.assetjson[parentkey]["type"]        # changed type includes hair, cannot use belongs_to_type
            folder = self.assets.titleToFileName(pobj["belongs_to_title"])

            path = self.env.existDataDir(mtype, self.env.basename, folder)
            if path is None:
                return False, self.env.existDataDir(mtype, self.env.basename)
            return True, path

    def singleDownLoad(self):

        supportedclasses = ["clothes", "hair", "eyes", "teeth", "eyebrows", "eyelashes", "expression",
                "pose", "skin", "rig", "proxy", "model", "target", "material" ]
        assetname = self.singlename.text()
        if assetname == "":
            ErrorBox(self.parent, "Please enter an asset name.")
            return

        # if not loaded, load json now
        if self.assetjson is None:
            self.assetjson = self.assets.alistReadJSON(self.env, self.assetlistpath)

        # if still None, error in JSON file
        if self.assetjson is None:
            ErrorBox(self.parent, self.env.last_error)
            return

        key, folder = self.assets.alistGetKey(self.assetjson, assetname)
        if key is None:
            ErrorBox(self.parent, "Asset '" + assetname + "' not found in list.")
            return
        mtype, flist = self.assets.alistGetFiles(self.assetjson, key)

        if mtype not in supportedclasses:
            ErrorBox(self.parent, "Supported classes until now: " + str(supportedclasses))
            return

        print (key, mtype, flist, folder)
        if mtype == "material":
            #
            # for materials the parent asset is needed and the path should be calculated

            okay, path = self.parentAsset(key)
            if okay is False:
                if path is None:
                    ErrorBox(self.parent, self.env.last_error)
                    return
                #
                # part of the path is known, create a file request box

                freq = MHFileRequest("Select a directory to save additional materials", None, path, save=".")
                path = freq.request()
                if path is None:
                    return              # cancel

                print ("Working with path: ", path)


            folder, err = self.assets.createMaterialsFolder(path)
        else:
            folder, err = self.assets.alistCreateFolderFromTitle(self.env.path_userdata, self.env.basename, mtype, folder)

        if folder is None:
            ErrorBox(self.parent, err)
            return

        if self.bckproc == None:
            self.prog_window = MHBusyWindow("Download files to " + folder, "loading ...")
            self.prog_window.progress.forceShow()
            self.bckproc = WorkerThread(self.par_filesdownload, folder, flist)
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
