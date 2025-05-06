"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * JsonItem
    * QTreeMain
    * MHTreeView
"""

from PySide6.QtWidgets import QApplication, QMainWindow, QTreeView, QAbstractItemView, QWidget, QGroupBox, QVBoxLayout, QCheckBox
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QFont

class JsonItem(QStandardItem):
    def __init__(self, txt="", cat = None, color=QColor(0,0,0)):
        super().__init__()
        self.setEditable(False)
        if cat is None:
            myFont=QFont()
            myFont.setBold(True)
            self.setFont(myFont)
        self.setText(txt)
        self.cat = cat
        self.text = txt

class QTreeMain(QTreeView):
    """
    Main selection of a tree with only one sub-category or as a list
    """
    def __init__(self, data, callback_redraw, autocollapse=True):
        super().__init__()

        self.autocollapse = autocollapse
        self.setHeaderHidden(True)
        self.lastparentindex = None
        self.lastcategory = None
        self.lastHeadline = ""
        self.callback_redraw = callback_redraw
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        treeModel = QStandardItemModel()

        self.rootNode = treeModel.invisibleRootItem()

        for elem in data:
            if isinstance(data, dict):
                layer1 = JsonItem(elem)
                self.rootNode.appendRow(layer1)
                group =  data[elem]["group"] if "group" in data[elem] else "default"
                if "items" in data[elem]:
                    l = data[elem]["items"]
                    for sublayer in l:
                        layer1.appendRow(JsonItem(sublayer["title"], group + "|" + sublayer["cat"]))
            else:
                layer1 = JsonItem(elem.capitalize(), elem)
                self.rootNode.appendRow(layer1)

        self.setModel(treeModel)
        self.collapseAll()
        self.clicked.connect(self.getValue)

    def setAutoCollapse(self, val):
        """
        toggle mode to collapse branches, when collapsing is used
        collapse everything but not the currently selected folder
        """
        self.autocollapse = val
        if val is True:
            if self.rootNode.hasChildren():
                for index in range (self.rootNode.rowCount()):
                    child = self.rootNode.child(index,0)
                    pindex = self.model().indexFromItem(child)
                    if pindex != self.lastparentindex:
                        self.collapse(pindex)

    def preSelect(self, pre):
        """
        preselect an item by category, expanding is done by engine
        """
        if self.rootNode.hasChildren():
            for index in range (self.rootNode.rowCount()):
                child = self.rootNode.child(index,0)
                if child.hasChildren:
                    numchild = child.rowCount()
                    if numchild == 0:
                        if child.cat == pre:
                            cindex = self.model().indexFromItem(child)
                            self.lastparentindex = self.model().indexFromItem(self.rootNode)
                            self.setCurrentIndex(cindex)
                            self.category = child.text      # identical for one layer
                            self.lastHeadline = child.text
                            self.lastcategory = None
                            return
                    for childindex in range(numchild):
                        grandchild=child.child(childindex,0)
                        if grandchild is not None:
                            if grandchild.cat == pre:
                                cindex = self.model().indexFromItem(grandchild)
                                self.lastparentindex = self.model().indexFromItem(child)
                                self.setCurrentIndex(cindex)
                                self.category = child.text
                                self.lastHeadline = child.text + ", " + grandchild.text
                                self.lastcategory = None
                                return

    def getLastHeadline(self):
        return(self.lastHeadline)

    def getLastCategory(self):
        return(self.lastcategory)

    def getValue(self, val):
        """
        print value on screen and remember parentindex for collapsing
        """
        index = self.currentIndex()
        oldpindex = self.lastparentindex

        if index is not None:
            item = self.model().itemFromIndex(index)
            newp = item.parent()
            if newp is not None:
                pindex = self.model().indexFromItem(newp)

                if self.autocollapse and oldpindex is not None and oldpindex != pindex:
                    self.collapse(oldpindex)

                self.lastparentindex = pindex
            if item.cat is not None and self.lastcategory != item.cat:
                if newp is None:
                    self.lastHeadline = item.text
                else:
                    self.lastHeadline = newp.text + ", " + item.text
                self.callback_redraw(item.cat, self.lastHeadline)
                self.lastcategory = item.cat
        
class MHTreeView(QWidget):
    def __init__(self, data, name="Selection", callback_redraw = None, pre=None, autocollapse=True):
        super().__init__()
        self.start = self._getStartColumn(data)
        layoutout = QVBoxLayout()
        gbox = QGroupBox(name)
        gbox.setObjectName("subwindow")

        layout = QVBoxLayout()
        self.mt = QTreeMain(data, callback_redraw, autocollapse)
        if isinstance(data, dict):
            self.b1 = QCheckBox("Collapse non selected branches")
            self.b1.stateChanged.connect(self.btnstate)
            self.b1.setChecked(autocollapse)
            layout.addWidget(self.b1)

        layout.addWidget(self.mt)
        gbox.setLayout(layout)

        layoutout.addWidget(gbox)
        self.setLayout(layoutout)

        # preselect first value
        #
        if pre is None:
            pre = self.start
        self.mt.preSelect(pre)

    def _getStartColumn(self, data):
        if len(data) > 0:
            if isinstance(data, list):
                return(data[0])
            name = next(iter(data))
            elem = data[name]
            if "items" in elem:
                if len(elem["items"]) > 0:
                    line = elem["items"][0]
                    return (elem["group"] + "|" + line["cat"])
        return ("Unknown")

    def getLastHeadline(self):
        return(self.mt.getLastHeadline())

    def getLastCategory(self):
        return(self.mt.getLastCategory())

    def getStartPattern(self):
        return self.start

    def setStart(self):
        self.mt.preSelect(self.start)
        return self.start

    def btnstate(self):
        state = self.b1.isChecked()
        self.mt.setAutoCollapse(state)

