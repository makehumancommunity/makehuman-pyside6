"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * MHInfoWindow
"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QScreen
import os

class MHInfoWindow(QWidget):
    """
    splash-window, borderless (mouseclick)
    """
    def __init__(self, glob):
        super().__init__()
        self.glob = glob
        env = glob.env
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
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        #
        # display in screen center
        #
    def show(self):
        super().show()
        self.move(self.glob.app.topLeftCentered(self))

    def mousePressEvent(self, event):
        self.close()

