from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QScreen

class MHApplication(QApplication):
    """
    classe to maintain QT parameters
    """
    def __init__(self, env, argv):
        self.env = env
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
