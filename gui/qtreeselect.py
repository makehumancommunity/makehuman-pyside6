from PySide6.QtWidgets import QApplication, QMainWindow, QTreeView, QAbstractItemView, QWidget, QGroupBox, QVBoxLayout, QCheckBox
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QFont

class JsonItem(QStandardItem):
    def __init__(self, txt="", cat = "default", color=QColor(0,0,0)):
        super().__init__()
        self.setEditable(False)
        if cat == "default":
            myFont=QFont()
            myFont.setBold(True)
            self.setFont(myFont)
        self.setText(txt)
        self.cat = cat

class QTreeMain(QTreeView):
    """
    Main selection of a tree with only one sub-category
    """
    def __init__(self, data, autocollapse=True):
        super().__init__()

        self.autocollapse = True
        self.setHeaderHidden(True)
        self.lastparentindex = None
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        treeModel = QStandardItemModel()

        self.rootNode = treeModel.invisibleRootItem()

        for elem in data:
            layer1 = JsonItem(elem)
            self.rootNode.appendRow(layer1)
            if "items" in data[elem]:
                l = data[elem]["items"]
                for sublayer in l:
                    layer1.appendRow(JsonItem(sublayer["title"], sublayer["cat"]))

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
                    for childindex in range(child.rowCount()):
                        grandchild=child.child(childindex,0)
                        if grandchild is not None:
                            if grandchild.cat == pre:
                                cindex = self.model().indexFromItem(grandchild)
                                self.lastparentindex = self.model().indexFromItem(child)
                                self.setCurrentIndex(cindex)



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
            # for now print the category
            print (item.cat)
        
class MHTreeView(QWidget):
    def __init__(self, data, name="Selection", pre = None, autocollapse=True):
        super().__init__()
        layoutout = QVBoxLayout()
        gbox = QGroupBox(name)
        gbox.setObjectName("subwindow")

        layout = QVBoxLayout()
        self.b1 = QCheckBox("Collapse non selected branches")
        self.b1.stateChanged.connect(self.btnstate)
        self.mt = QTreeMain(data, autocollapse)
        self.b1.setChecked(autocollapse)
        layout.addWidget(self.b1)
        layout.addWidget(self.mt)
        gbox.setLayout(layout)

        layoutout.addWidget(gbox)
        self.setLayout(layoutout)

        if pre is not None:
            self.mt.preSelect(pre)

    def btnstate(self):
        state = self.b1.isChecked()
        self.mt.setAutoCollapse(state)

