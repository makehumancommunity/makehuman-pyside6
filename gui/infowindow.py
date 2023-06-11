from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QScreen
import os

class MHInfoWindow(QWidget):
    """
    demonstration of an info window, borderless (mouseclick)
    """
    def __init__(self, parent, app):
        super().__init__()
        self.parent = parent
        env = parent.env
        rel = env.release_info
        version = ".".join(str(l) for l in env.release_info["version"])
        text = " ".join([rel["name"], version, "     Authors:", rel["author"]])
        title = QLabel(text)

        pixmap = QPixmap(os.path.join(env.path_sysicon,"splash.png"))
        lbl = QLabel(self)
        lbl.setPixmap(pixmap)
        layout =QVBoxLayout(self)
        layout.addWidget(lbl)
        layout.addWidget(title)
        self.setLayout(layout)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        center = app.getCenter()
        self.move(center - self.frameGeometry().center())   # not really center ;)


    def mousePressEvent(self, event):
        self.close()

