import os
from PySide6.QtWidgets import (
        QLabel, QDialogButtonBox, QVBoxLayout, QDialog, QProgressDialog, QWidget, QApplication, QMessageBox, QFrame,
        QHBoxLayout, QLineEdit, QPushButton, QComboBox, QProgressBar
        )
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QThread, Signal, QSize

def ErrorBox(qw, text):
    button = QMessageBox.critical(qw, "An error occured!", text, buttons=QMessageBox.Close)
    dlg = QMessageBox()

class clickableProgressBar(QProgressBar):
    """
    progressBar which is clicked can be use to open an active slider
    """
    def __init__(self, callback, parent=None):
        self.callback = callback
        QProgressBar.__init__(self, parent)

    def mousePressEvent(self, event):
        self.callback()

class IconButton(QPushButton):
    def __init__(self, funcid, path, tip, func, fsize=36):
        self._funcid = funcid
        icon  = QIcon(path)
        super().__init__()
        self.setIcon(icon)
        self.setIconSize(QSize(fsize,fsize))
        self.setCheckable(True)
        self.setFixedSize(fsize+4,fsize+4)
        self.setToolTip(tip)
        if func is not None:
            self.clicked.connect(func)

    def setChecked(self, value):
        super().setChecked(value)
        if value is True:
            self.setStyleSheet("background-color : orange")
        else:
            self.setStyleSheet("background-color : lightgrey")

class MHGroupBox(QFrame):
    def __init__(self, title):
        super().__init__()
        self.vlabel = QLabel(title)
        self.vlabel.setObjectName("groupbox")
        self.vlabel.setAlignment( Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.setObjectName("groupbox")

    def MHLayout(self, parentlayout):
        self.setLayout(parentlayout)
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.vlabel)
        layout.addWidget(self)
        return(layout)

    def setTitle(self, title):
        self.vlabel.setText(title)


class MHTagEdit(QVBoxLayout):
    def __init__(self, glob, tags, label, numtags=5, copyfrom=None, predefined=None):
        super().__init__()
        self.edittags = tags
        self.sourcetags = copyfrom
        self.numtags = numtags

        ilayout = QHBoxLayout()
        ilayout.addWidget(QLabel(label))
        sweep = os.path.join(glob.env.path_sysicon, "sweep.png")
        clearbutton = IconButton(0, sweep, "Clear own tags", self.clearTags)

        if copyfrom is not None:
            copy = os.path.join(glob.env.path_sysicon, "redo.png")
            copybutton = IconButton(0, copy, "Copy tags from original asset", self.copyTags)
            ilayout.addWidget(copybutton)

        ilayout.addWidget(clearbutton)
        self.addLayout(ilayout)

        if predefined is not None:
            ilayout = QHBoxLayout()
            self.combobox = QComboBox()
            self.combobox.addItems(predefined)
            ilayout.addWidget(self.combobox)
            plus = os.path.join(glob.env.path_sysicon, "plus.png")
            plusbutton = IconButton(0, plus, "Add predefined tag to own tags", self.addPredefinedTag)
            ilayout.addWidget(plusbutton)
            self.addLayout(ilayout)
        else:
            self.combobox = None

        self.tags  = []
        for l in range(self.numtags):
            self.tags.append(QLineEdit())
            self.tags[l].editingFinished.connect(self.reorderTags)
            self.addWidget(self.tags[l])
        self.displayTags()

    def newPredefinedTags(self, predefined):
        if self.combobox is not None:
            self.combobox.clear()
            self.combobox.addItems(predefined)

    def displayTags(self):
        for l in range(self.numtags):
            tag = self.edittags[l] if l < len(self.edittags) else ""
            self.tags[l].setText(tag)

    def copyTags(self):
        self.edittags=self.sourcetags
        self.displayTags()

    def clearTags(self):
        self.edittags=[]
        for l in range(self.numtags):
            self.tags[l].clear()

    def reorderTags(self):
        self.edittags=[]
        for l in range(self.numtags):
            text = self.tags[l].text()
            if len(text):
                self.edittags.append(text)
        self.displayTags()

    def newTags(self, tags, copyfrom):
        self.edittags = tags
        if copyfrom is not None:
            self.sourcetags = copyfrom
        self.displayTags()

    def addPredefinedTag(self):
        newtag = self.combobox.currentText()
        if newtag not in self.edittags and len(self.edittags) < self.numtags:
            newtag = newtag.split(":")[-1] if ":" in newtag else newtag
            self.edittags.append(newtag)
            self.displayTags()

    def getTags(self):
        return(self.edittags)

class WorkerThread(QThread):
    update_progress = Signal(int)

    def __init__(self, function, *args):
        super().__init__()
        self.mh_function = function
        self.mh_args = args
        self.finishmsg = "Background process completed"

    def run(self):
        self.mh_function(self, self.mh_args)

class DialogBox(QDialog):
    def __init__(self, question, button):
        super().__init__()

        self.setWindowTitle("Dialog")

        QBtn = button | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel(question)
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

class MHProgWindow():
    """
    Progress Window to display progress, more or less a wrapper of
    QProgressDialog
    """
    def __init__(self, title, maximum):
        self.progress = QProgressDialog("started", None, 0, maximum, None)
        self.progress.setWindowTitle(title)
        self.progress.setMinimumWidth(600)
        self.progress.setMinimumDuration(500)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setAttribute(Qt.WA_DeleteOnClose, True)

    def setValueAndText(self, l, text):
        self.progress.setValue(l)
        self.progress.setLabelText(text)

    def setValue(self, l):
        self.progress.setValue(l)

    def setLabelText(self, text):
        self.progress.setLabelText(text)

    def setMaximum(self, l):
        self.progress.setMaximum(l)


class MHBusyWindow(QWidget):
    """
    a small busy window
    """
    def __init__(self, title, text):
        self.progress = QProgressDialog(text, None, 0, 0, None)
        self.progress.setWindowTitle(title)
        self.progress.setMinimumWidth(600)
        self.progress.setMinimumDuration(200)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setAttribute(Qt.WA_DeleteOnClose, True)

    def setLabelText(self, text):
        self.progress.setLabelText(text)

    def setValue(self, l):
        self.progress.setValue(l)


