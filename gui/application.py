from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QScreen, QImageReader
from PySide6.QtCore import qVersion, QCoreApplication
import os

def QTVersion(pinfo):
    qversion = {}
    qversion["version"] = [ int(x) for x in qVersion().split(".")]
    formats = [ s.data().decode(encoding='utf-8').lower() for s in QImageReader.supportedImageFormats() ]
    qversion["jpg_support"] = "jpg" in formats
    qversion["plugin_path"] = os.path.pathsep.join( [pinfo.pathToUnicode(p) for p in QCoreApplication.libraryPaths()])
    qversion["plugin_path_env"] = pinfo.pathToUnicode(os.environ['QT_PLUGIN_PATH'] if 'QT_PLUGIN_PATH' in os.environ else "")
    #
    # qt.conf is no longer tested (reason: other versions like qt6.conf etc. can be used
    #
    return (qversion)

class MHApplication(QApplication):
    """
    class to maintain QT parameters
    """
    def __init__(self, glob, argv):
        self.env = glob.env
        super().__init__(argv)


    def setStyles(self, theme):
        if theme is None:
            return (False)
        try:
            with open(theme, "r") as fh:
                self.setStyleSheet(fh.read())
            return (True)
        except:
            self.env.last_error("cannot read " + theme)
            return (False)

    def getCenter(self):
        return(QScreen.availableGeometry(self.primaryScreen()).center())
