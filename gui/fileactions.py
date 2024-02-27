from PySide6.QtWidgets import QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QAbstractItemView, QLineEdit, QLabel
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from gui.imageselector import IconButton
import os

class BaseSelect(QGroupBox):
    def __init__(self, glob, callback):
        super().__init__("base mesh")
        env = glob.env
        self.setObjectName("subwindow")
        self.baseResultList = env.getDataDirList("base.obj", "base")

        bvLayout = QVBoxLayout()

        self.basewidget = QListWidget()
        self.basewidget.setFixedSize(240, 200)
        self.basewidget.addItems(self.baseResultList.keys())
        self.basewidget.setSelectionMode(QAbstractItemView.SingleSelection)
        if env.basename is not None:
            items = self.basewidget.findItems(env.basename,Qt.MatchExactly)
            if len(items) > 0:
                self.basewidget.setCurrentItem(items[0])
        bvLayout.addWidget(self.basewidget)

        buttons = QPushButton("Select")
        buttons.clicked.connect(callback)
        bvLayout.addWidget(buttons)
        self.setLayout(bvLayout)

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
        self.filename = QLineEdit()
        self.addWidget(self.filename)
        self.savebutton=QPushButton("Save")
        self.addWidget(self.savebutton)

    def newname(self):
        text = self.editname.text()
        if len(text):
            self.bc.name = text
            self.displaytitle(text)

    def genuuid(self):
        self.uuid.setText(self.glob.gen_uuid())

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
            pixmap = QPixmap(os.path.join(self.glob.env.path_sysicon, "empty_char.png"))
        else:
            pixmap = QPixmap.fromImage(self.bc.photo)
        self.imglabel.setPixmap(pixmap)


    def thumbnail(self):
        self.bc.photo = self.view.createThumbnail()
        self.displayPixmap()
        #image.save(name, "PNG", -1)
