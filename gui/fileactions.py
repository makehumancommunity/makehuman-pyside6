from PySide6.QtWidgets import QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QAbstractItemView, QLineEdit, QLabel, QMessageBox, QRadioButton
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from gui.imageselector import IconButton, MHPictSelectable, PicSelectWidget
from gui.materialwindow import  MHMaterialWindow
from gui.dialogs import DialogBox, ErrorBox, WorkerThread, MHBusyWindow
import os
from core.importfiles import AssetPack

class BaseSelect(QVBoxLayout):
    def __init__(self, parent, callback):
        super().__init__()
        self.parent = parent
        self.env = parent.glob.env
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

        matpath = os.path.join(self.env.path_sysicon, "materials.png" )
        matbutton = IconButton(0, matpath, "Change material", self.materialCallback)
        self.addWidget(matbutton)

    def materialCallback(self):
        p1 = self.env.stdUserPath("skins")
        p2 = self.env.stdSysPath("skins")
        basemesh = self.parent.glob.baseClass.baseMesh
        matfiles = basemesh.material.listAllMaterials(p1)
        matfiles.extend(basemesh.material.listAllMaterials(p2))
        matimg = []
        oldmaterial = self.parent.glob.baseClass.skinMaterial
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
    def __init__(self, glob, view, displaytitle):
        self.view = view
        self.glob = glob
        env = glob.env
        self.bc  = glob.baseClass
        self.displaytitle = displaytitle
        super().__init__()
        print (self.bc)

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
        ilayout = QHBoxLayout()
        ilayout.addWidget(QLabel("\nTags:"))
        self.clearbutton=QPushButton("Clear")
        self.clearbutton.clicked.connect(self.cleartags)
        ilayout.addWidget(self.clearbutton, alignment=Qt.AlignBottom)
        self.addLayout(ilayout)
        self.tags  = []
        for l in range(5):
            self.tags.append(QLineEdit())
            self.tags[l].editingFinished.connect(self.reordertags)
            self.addWidget(self.tags[l])

        self.displaytags()

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
        path calculation, save file, save icon
        """
        path = self.glob.env.stdUserPath("models", self.filename.text())
        self.bc.saveMHMFile(path)
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

    def cleartags(self):
        for l in range(5):
            self.tags[l].clear()

    def displaytags(self):
        for l in range(5):
            tag = self.bc.tags[l] if l < len( self.bc.tags) else ""
            self.tags[l].setText(tag)

    def reordertags(self):
        self.bc.tags=[]
        for l in range(5):
            text = self.tags[l].text()
            if len(text):
                self.bc.tags.append(text)
        self.displaytags()

    def displayPixmap(self):
        if self.bc.photo is None:
            pixmap = QPixmap(os.path.join(self.glob.env.path_sysicon, "empty_models.png"))
        else:
            pixmap = QPixmap.fromImage(self.bc.photo)
        self.imglabel.setPixmap(pixmap)


    def thumbnail(self):
        self.bc.photo = self.view.createThumbnail()
        self.displayPixmap()


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
