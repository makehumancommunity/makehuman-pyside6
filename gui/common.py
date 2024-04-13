import os
from PySide6.QtWidgets import (
        QLabel, QDialogButtonBox, QVBoxLayout, QDialog, QProgressDialog, QWidget, QApplication, QMessageBox, QFrame,
        QHBoxLayout, QLineEdit, QPushButton
        )
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QThread, Signal, QSize

def ErrorBox(qw, text):
    button = QMessageBox.critical(qw, "An error occured!", text, buttons=QMessageBox.Close)
    dlg = QMessageBox()

class IconButton(QPushButton):
    def __init__(self, funcid, path, tip, func):
        self._funcid = funcid
        icon  = QIcon(path)
        super().__init__()
        self.setIcon(icon)
        self.setIconSize(QSize(36,36))
        self.setCheckable(True)
        self.setFixedSize(40,40)
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
    def __init__(self, glob, tags, label):
        super().__init__()
        self.edittags = tags
        ilayout = QHBoxLayout()
        ilayout.addWidget(QLabel(label))
        sweep = os.path.join(glob.env.path_sysicon, "sweep.png")
        clearbutton = IconButton(0, sweep, "Clear", self.clearTags)

        ilayout.addWidget(clearbutton, alignment=Qt.AlignBottom)
        self.addLayout(ilayout)
        self.tags  = []
        for l in range(5):
            self.tags.append(QLineEdit())
            self.tags[l].editingFinished.connect(self.reorderTags)
            self.addWidget(self.tags[l])
        self.displayTags()

    def displayTags(self):
        for l in range(5):
            tag = self.edittags[l] if l < len( self.edittags) else ""
            self.tags[l].setText(tag)

    def clearTags(self):
        self.edittags=[]
        for l in range(5):
            self.tags[l].clear()

    def reorderTags(self):
        self.edittags=[]
        for l in range(5):
            text = self.tags[l].text()
            if len(text):
                self.edittags.append(text)
        self.displayTags()

    def newTags(self, tags):
        self.edittags = tags
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

