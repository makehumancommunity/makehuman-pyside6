from PySide6.QtWidgets import QLabel, QDialogButtonBox, QVBoxLayout, QDialog, QProgressDialog, QWidget, QApplication, QMessageBox, QFrame
from PySide6.QtCore import Qt, QThread, Signal

def ErrorBox(qw, text):
    button = QMessageBox.critical(qw, "An error occured!", text, buttons=QMessageBox.Close)
    dlg = QMessageBox()

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


