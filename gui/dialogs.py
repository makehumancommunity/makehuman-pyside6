from PySide6.QtWidgets import QLabel, QDialogButtonBox, QVBoxLayout, QDialog, QProgressDialog, QWidget, QApplication
from PySide6.QtCore import Qt


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
    def __init__(self, glob, text):
        super().__init__()
        env = glob.env
        title = QLabel(text)
        layout =QVBoxLayout(self)
        layout.addWidget(title)
        self.setLayout(layout)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        center = glob.app.getCenter()
        self.move(center - self.frameGeometry().center())





