import sys
import typing
import os
from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtGui import QPixmap, QPainter, QPen, QIcon, QColor, QFont, QStandardItemModel, QStandardItem

from PySide6.QtWidgets import QApplication, QWidget, QLayout, QLayoutItem, QStyle, QSizePolicy, QPushButton, QAbstractButton, QRadioButton, QCheckBox, QGroupBox, QVBoxLayout, QLabel, QLineEdit, QTreeView, QAbstractItemView, QScrollArea, QPlainTextEdit, QHBoxLayout

class MHPictSelectable:
    def __init__(self, name: str, icon: str, filename: str, author: str, tags: list):
        self.name = name
        self.icon = icon
        self.filename = filename
        self.author = author
        self.tags = tags
        #
        # append filename, author and  name as tags as well
        #
        self.tags.append(name.lower())
        self.tags.append(os.path.split(filename)[1].lower())    # only name, not path
        self.tags.append(author.lower())
        self.status = 0

    def __str__(self):
        return('\n'.join("%s: %s" % item for item in vars(self).items()))

class PictureButton(QPushButton):
    """
    tri-state picture button
    holds state in asset.status to be be reachable from outside
    :param asset: asset to be shown (used for name)
    :param parent_update:      refresh function for widget where this button is contained
    :param information_update: refresh function for widget where information will be written
    """
    def __init__(self, asset: MHPictSelectable, emptyicon,  parent_update, information_update):

        self.asset = asset
        self.parent_update = parent_update
        self.information_update = information_update
        self.icon = None

        super().__init__()
        if asset.icon is None:                 # will not be constant
            self.icon = emptyicon
            self.picture_added = False
        else:
            self.picture_added = True
            self.icon = asset.icon
        #self.setPicture(QPixmap(self.icon))
        self.setPicture(QPixmap(self.icon).scaled(96,96, Qt.AspectRatioMode.KeepAspectRatio))
        self.setCheckable(True)
        self.framecol  = (Qt.black, Qt.yellow, Qt.green)
        self.setToolTip(asset.name)

    #def __del__(self):
    #    print (self.asset.name + " deleted")

    def setPicture(self, icon):
        self.picture = icon
        self.update()

    def sizeHint(self):
        return self.picture.size()

    def paintEvent(self, e):
        painter = QPainter(self)
        if self.asset.status != 0:
            painter.setOpacity(1)
            painter.drawPixmap(0, 0, self.picture)
            pen = QPen()
            pen.setColor(self.framecol[self.asset.status])
            pen.setWidth(5)

            painter.setPen(pen)
            painter.drawRect(self.rect())
        else:
            painter.setOpacity(0.4)
            painter.drawPixmap(0, 0, self.picture)

        if self.picture_added is False:
            painter.setPen(Qt.black)
            painter.drawText(10, 15, self.asset.name)

        painter.end()

    def btnstate(self):
        if self.asset.status == 0:
            #print ("button " + str (self.text) + " pressed")
            self.asset.status = 1
            self.information_update(self.asset)
        else:
            #print ("button released")
            self.asset.status = 0
        self.parent_update(self)


class PicFlowLayout(QLayout):
    """
    multiSel: multiple selection, will change refresh method
    """
    def __init__(self, multiSel: False, callback, emptyIcon: str="", parent: QWidget=None, margin: int=-1, hSpacing: int=-1, vSpacing: int=-1):

        super().__init__(parent)
        self.itemList = list()
        self.wList = list()
        self.m_hSpace = hSpacing
        self.m_vSpace = vSpacing
        self.multiSel = multiSel
        self.empty = emptyIcon
        self.callback = callback
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        # copied for consistency, not sure this is needed or ever called
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item: QLayoutItem):
        self.itemList.append(item)

    def addWidget(self, widget: QWidget):
        self.wList.append(widget)
        super().addWidget(widget)

    def removeAllWidgets(self):
        while ((child := self.takeAt(0)) != None):
            if child.widget() is not None:
                child.widget().deleteLater()
        self.itemList = list()
        self.wList = list()

    def refreshAllWidgets(self, current):
        if self.multiSel:
            for widget in self.wList:
                if widget is not current and widget.asset.status == 1:
                    widget.asset.status = 2
                    widget.update()
        else:
            for widget in self.wList:
                if widget is not current and widget.asset.status == 1:
                    # print("item " + widget.text + " toggle")
                    widget.asset.status = 0
                    widget.update()


    def horizontalSpacing(self) -> int:
        if self.m_hSpace >= 0:
            return self.m_hSpace
        else:
            return self.smartSpacing(QStyle.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self) -> int:
        if self.m_vSpace >= 0:
            return self.m_vSpace
        else:
            return self.smartSpacing(QStyle.PM_LayoutVerticalSpacing)

    def count(self) -> int:
        return len(self.itemList)

    def itemAt(self, index: int) -> typing.Union[QLayoutItem, None]:
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        else:
            return None

    def takeAt(self, index: int) -> typing.Union[QLayoutItem, None]:
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        else:
            return None

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def smartSpacing(self, pm: QStyle.PixelMetric) -> int:
        parent = self.parent()
        if not parent:
            return -1
        elif parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        else:
            return parent.spacing()

    def doLayout(self, rect: QRect, testOnly: bool) -> int:
        left, top, right, bottom = self.getContentsMargins()
        effectiveRect = rect.adjusted(+left, +top, -right, -bottom)
        x = effectiveRect.x()
        y = effectiveRect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.horizontalSpacing()
            if spaceX == -1:
                spaceX = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = self.verticalSpacing()
            if spaceY == -1:
                spaceY = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)

            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > effectiveRect.right() and lineHeight > 0:
                x = effectiveRect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y() + bottom

    def updateAsset(self, current):
        self.callback(current.asset)
        self.refreshAllWidgets(current)

    def populate(self, assetlist, ruleset, filtertext, displayInfo):
        """
        :assetlist: complete asset list to be considered
        :ruleset: list for comparison or None
        :param filtertext: additional filter text or None
        displayInfo: function for infobox
        """
        if filtertext == "":
            filtertext = None
        for asset in assetlist:
            #
            # when ruleset in not empty or none check rules per base
    
            if ruleset is not None and bool(ruleset) == True :
                display = True
                for tagelem in asset.tags:
                    basedisplay = False
                    if ":" in tagelem:
                        [base, rest]= tagelem.split(":", 1)
                        if base in ruleset:
                            for rule in ruleset[base]:
                                #
                                # rule as a string is found

                                if rest.startswith(rule):
                                    basedisplay = True
                        else:
                            # no base tag given in rules
                            #
                            basedisplay = True
                    else:
                        # no ':' in tag, no test (should be for wildcards later)
                        #
                        basedisplay = True

                    # all bases form the summary
                    #
                    display = basedisplay & display

            else:
                display = True

            if filtertext is not None:
                fdisplay = False
                for tagelem in asset.tags:
                    if filtertext in tagelem:
                        fdisplay = True
                display = fdisplay & display

            if display:
                button1 = PictureButton(asset, self.empty, self.updateAsset, displayInfo)
                button1.pressed.connect(button1.btnstate)
                self.addWidget (button1)

class PicSelectWidget(QWidget):
    """
    PicSelectWidget is a PicFlowLayout embedded in a QGroupBox with a QScrollArea
    addWidget will add a button to the PicFlowLayout
    :param name: headline (default selection)
    :param multiSel: multiple selection 
    """
    def __init__(self, name="Selection", callback=None, multiSel=False, emptyIcon=""):
        self.multiSel =  multiSel
        self.layout = PicFlowLayout(multiSel=multiSel, callback=callback,  emptyIcon=emptyIcon)
        super().__init__()

    def __del__(self):
        """
        this is a must, otherwise the widgets will use up complete memory
        """
        self.layout.removeAllWidgets()

    def refreshAllWidgets(self, current):
        self.layout.refreshAllWidgets(current)

    def populate(self, assetlist, ruleset, filtertext, displayInfo):
        self.layout.populate(assetlist, ruleset, filtertext, displayInfo)

    def addWidget(self, button):
        self.layout.addWidget (button)

class InformationBox(QWidget):
    def __init__(self, layout):
        super().__init__()
        self.layout = layout
        #self.layout = QVBoxLayout()
        self.selectedName = QLabel("Name:\nAuthor:")
        self.layout.addWidget(self.selectedName)
        self.layout.addWidget(QLabel("Tags:"))
        self.tagbox = QPlainTextEdit()
        self.tagbox.setPlainText("")
        self.tagbox.setReadOnly(True)
        self.tagbox.setFixedHeight(120)
        self.layout.addWidget(self.tagbox)
        #self.setLayout(self.layout)

    def setInformation(self, asset):
        self.selectedName.setText("Name: " + asset.name + "\n" + "Author: " + asset.author)
        self.tagbox.setPlainText("\n".join(l.replace(":", " \u23f5 ") for l in asset.tags)) # triangle as arrow

class FilterTree(QTreeView):
    """
    :param flowLayout: points to layout
    :param displayInfo: points to information box
    """

    def  __init__(self, assets, searchByFilterText, displayInfo):

        self.assets = assets
        self.searchByFilterText = searchByFilterText
        self.flowLayout = None
        self.displayInfo = displayInfo

        super().__init__()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.MultiSelection)
        self.model = QStandardItemModel()
        self.setHeaderHidden(True)
        self.setMaximumWidth(200)
        self.setModel(self.model)
        self.setUniformRowHeights(True)
        self.setFirstColumnSpanned(1, self.rootIndex(), True)

    def setPicLayout(self, layout):
        self.flowLayout = layout

    def addTree(self, subtree, layer=None, base="", search=""):
        """
        recursively try to create a tree from definition, could change depending on structure
        """
        for elem in subtree:
            #
            # set base when layer is None, otherwise keep old one and create substring by appending layer
            find = elem.lower()
            if find == "translate":
                continue
            if base == "":
                substring = ""
                nbase = find
            else:
                nbase = base
                substring = find if search =="" else  search + ":" + find

            if type(elem) is dict:
                self.addTree(elem, layer, nbase, substring)
            else:
                child = QStandardItem(elem)
                if layer is None:
                    child.setSelectable(False)
                    self.model.appendRow([child])
                    child.searchbase = None
                    child.searchpattern = None
                else:
                    layer.appendRow([child])
                    child.searchbase = nbase
                    child.searchpattern = substring
                if type(subtree) is dict:
                    self.addTree(subtree[elem], child, nbase, substring)

    def filterChanged(self):
        """
        create a ruleset from selected items and repopulate the flow-Layout
        """
        if self.flowLayout is None:
            return
        ruleset = {}
        for ix in self.selectedIndexes():
            index = self.model.itemFromIndex(ix)
            base = index.searchbase
            if base not in ruleset:
                ruleset[base] = []
            ruleset[base].append(index.searchpattern)
        filtertext = self.searchByFilterText.text().lower()
        self.flowLayout.removeAllWidgets()
        self.flowLayout.populate(self.assets, ruleset, filtertext, self.displayInfo)

class editBox(QLineEdit):
    def  __init__(self, slayout, widget):
        self.changeFilter = None
        self.empty = QPushButton("")
        self.empty.setIcon(widget.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.empty.setMaximumWidth(30)
        self.empty.clicked.connect(self.clearEditBox)
        super().__init__()
        slayout.addWidget(self)
        slayout.addWidget(self.empty)
        self.setMaximumWidth(170)

    def addConnect(self, changeFilter):
        self.changeFilter = changeFilter
        self.returnPressed.connect(changeFilter)

    def clearEditBox(self):
        self.clear()
        if self.changeFilter is not None:
            self.changeFilter()

class Equipment():
    def __init__(self, glob, assetrepo, eqtype, multisel):
        self.glob = glob
        self.env = glob.env
        self.assetrepo = assetrepo
        self.type = eqtype
        self.multisel = multisel
        self.tagreplace = {}
        self.filterjson = None
        self.picwidget = None
        self.filterview = None
        self.asset_category = []
        self.emptyIcon = os.path.join(self.env.path_sysdata, "icons", "empty_" + self.type + ".png")
        if not os.path.isfile(self.emptyIcon):
            self.emptyIcon = os.path.join(self.env.path_sysdata, "icons", "noidea.png")

    def createTagGroups(self, subtree, path):
        """
        create texts to prepend certain tags, can also translate tags
        """
        for elem in subtree:
            if isinstance(elem, str):
                if isinstance(subtree[elem], dict):
                    self.createTagGroups(subtree[elem], path + ":" + elem.lower())
                elif isinstance(subtree[elem], list):
                    for l in subtree[elem]:
                        repl = path + ":" + elem.lower()
                        self.tagreplace[l.lower()] = repl[1:]       # get rid of first ":"
                if elem == "Translate":                             # extra, change by word
                    for l in subtree[elem]:
                        self.tagreplace[l.lower()] = subtree[elem][l]

    def completeTags(self, tags):
        """
        replace tags by tags with prepended strings
        """
        newtags = []
        for tag in tags:
            ltag = tag.lower()
            if ltag in self.tagreplace:
                elem = self.tagreplace[ltag]
                if elem is not None:
                    if elem.startswith("="):        # complete replacement
                        ntag = elem[1:]
                    else:
                        ntag = elem+":"+ltag
                    if ntag not in newtags:
                        newtags.append(ntag)
            else:
                if tag not in newtags:
                    newtags.append(tag)
        return (newtags)

    def prepare(self):
        # load filter from file according to base mesh
        #
        path = self.env.stdSysPath(self.type, "selection_filter.json")
        self.filterjson = self.env.readJSON(path)
        if self.filterjson is None:
            self.filterjson = {}
        self.createTagGroups(self.filterjson, "")

        for elem in self.assetrepo:
            if elem.folder == self.type:
                elem.tag = self.completeTags(elem.tag)
                self.asset_category.append(MHPictSelectable(elem.name, elem.thumbfile, elem.path,  elem.author, elem.tag))

    def changeStatus(self):
        checked = []
        for elem in self.assetrepo:
            if elem.folder == self.type and elem.used is True:
                checked.append(elem.path)

        for elem in self.asset_category:
            elem.status = 1 if elem.filename in checked else 0

    def equipAsset(self, asset):
        print (asset)
        if asset.status == 0:
            self.glob.baseClass.delAsset(asset.filename)
        elif asset.status == 1:
            self.glob.baseClass.addAndDisplayAsset(asset.filename, self.type, self.multisel)

    def leftPanel(self):
        """
        done first
        """
        v1layout = QVBoxLayout()    # this is for searching
        self.infobox = InformationBox(v1layout)
        gbox = QGroupBox("Filtering")
        gbox.setObjectName("subwindow")

        widget = QWidget()
        slayout = QHBoxLayout()  # layout for textbox + empty button
        filteredit = editBox(slayout, widget)
        self.filterview = FilterTree(self.asset_category, filteredit, self.infobox.setInformation)
        self.filterview.addTree(self.filterjson)
        self.filterview.selectionModel().selectionChanged.connect(self.filterview.filterChanged)
        filteredit.addConnect(self.filterview.filterChanged)

        v1layout.addWidget(self.filterview)
        v1layout.addWidget(QLabel("Filter:"))
        v1layout.addLayout(slayout)

        gbox.setLayout(v1layout)
        return(gbox)

    def rightPanel(self):
        """
        draw tools Panel
        """
        self.picwidget = PicSelectWidget("Clothes", multiSel=self.multisel, callback=self.equipAsset, emptyIcon=self.emptyIcon)
        self.filterview.setPicLayout(self.picwidget.layout)
        self.picwidget.populate(self.asset_category, None, None, self.infobox.setInformation)
        self.changeStatus()
        return(self.picwidget)

