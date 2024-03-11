from PySide6.QtWidgets import QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QAbstractItemView, QLineEdit, QLabel, QMessageBox
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from gui.imageselector import IconButton
from gui.dialogs import DialogBox, ErrorBox, WorkerThread, MHBusyWindow
import os
from core.importfiles import AssetPack

class BaseSelect(QVBoxLayout):
    def __init__(self, glob, callback):
        super().__init__()
        env = glob.env
        self.baseResultList = env.getDataDirList("base.obj", "base")

        self.basewidget = QListWidget()
        self.basewidget.setFixedSize(240, 200)
        self.basewidget.addItems(self.baseResultList.keys())
        self.basewidget.setSelectionMode(QAbstractItemView.SingleSelection)
        if env.basename is not None:
            items = self.basewidget.findItems(env.basename,Qt.MatchExactly)
            if len(items) > 0:
                self.basewidget.setCurrentItem(items[0])
        self.addWidget(self.basewidget)

        buttons = QPushButton("Select")
        buttons.clicked.connect(callback)
        self.addWidget(buttons)

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
        self.assets = None
        self.bck_proc = None

        super().__init__()

        # name
        #
        self.addWidget(QLabel("\nZip Filename:"))
        self.filename = QLineEdit("")
        self.addWidget(self.filename)
        self.savebutton=QPushButton("Extract")
        self.savebutton.clicked.connect(self.extractZip)
        self.addWidget(self.savebutton)

    def parallelunzip(self, bckproc, *args):
        tempdir = self.assets.unZip(self.filename.text())
        print (tempdir, self.env.path_userdata, self.env.basename)
        #self.assets.copyAssets(tempdir, self.env.path_userdata, self.env.basename)

    def finishLoad(self):
        self.assets.cleanupUnzip()
        if self.prog_window is not None:
            self.prog_window.progress.close()
            self.prog_window = None
        QMessageBox.information(self.parent, "Done!", self.bckproc.finishmsg)
        self.bckproc = None

    def extractZip(self):
        print ("extract Zipfile")
        self.assets = AssetPack(None, None)
        self.prog_window = MHBusyWindow("Extract ZIP file", "extracting ...")
        self.prog_window.progress.forceShow()
        self.bckproc = WorkerThread(self.parallelunzip, None)
        self.bckproc.start()
        self.bckproc.finishmsg = "Zip file has been imported"
        self.bckproc.finished.connect(self.finishLoad)
