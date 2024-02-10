import sys
import json
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
        self.tags.append(filename.lower())
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
    def __init__(self, asset: MHPictSelectable, parent_update, information_update):

        self.asset = asset
        self.parent_update = parent_update
        self.information_update = information_update

        super().__init__(asset.name)
        if asset.icon is None:                 # will not be constant
            asset.icon = "data/icons/empty_clothes.png"
            self.picture_added = False
        else:
            self.picture_added = True
        self.setPicture(QPixmap(asset.icon))
        self.setCheckable(True)
        self.framecol  = (Qt.black, Qt.yellow, Qt.green)
        self.setToolTip(asset.name)

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
    def __init__(self, multiSel: False, parent: QWidget=None, margin: int=-1, hSpacing: int=-1, vSpacing: int=-1):

        super().__init__(parent)

        self.itemList = list()
        self.wList = list()
        self.m_hSpace = hSpacing
        self.m_vSpace = vSpacing
        self.multiSel = multiSel
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
                button1 = PictureButton(asset, self.refreshAllWidgets, displayInfo)
                button1.pressed.connect(button1.btnstate)
                self.addWidget (button1)

class PicSelectWidget(QWidget):
    """
    PicSelectWidget is a PicFlowLayout embedded in a QGroupBox with a QScrollArea
    addWidget will add a button to the PicFlowLayout
    :param name: headline (default selection)
    :param multiSel: multiple selection 
    """
    def __init__(self, parent_layout, name="Selection", multiSel=False):
        groupbox = QGroupBox(name)
        groupbox.setObjectName("subwindow")
        scrollArea = QScrollArea()
        self.multiSel =  multiSel
        self.layout = PicFlowLayout(multiSel=multiSel)

        groupbox.setLayout(self.layout)
        scrollArea.setWidget(groupbox)
        scrollArea.setWidgetResizable(True)
        scrollArea.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )

        parent_layout.addWidget(scrollArea)
        super().__init__()

    def refreshAllWidgets(self, current):
        self.layout.refreshAllWidgets(current)

    def populate(self, assetlist, ruleset, filtertext, displayInfo):
        self.layout.populate(assetlist, ruleset, filtertext, displayInfo)

    def addWidget(self, button):
        self.layout.addWidget (button)

class InformationBox(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.selectedName = QLabel("Name: ")
        self.selectedAuthor = QLabel("Author: ")

        self.layout.addWidget(QLabel("Information:"))
        self.layout.addWidget(self.selectedName)
        self.layout.addWidget(self.selectedAuthor)
        self.layout.addWidget(QLabel("Tags:"))
        self.tagbox = QPlainTextEdit()
        self.tagbox.setPlainText("")
        self.tagbox.setReadOnly(True)
        self.tagbox.setFixedHeight(120)
        self.layout.addWidget(self.tagbox)
        self.setLayout(self.layout)

    def setInformation(self, asset):
        self.selectedName.setText("Name: " + asset.name)
        self.selectedAuthor.setText("Author: " + asset.author)
        self.tagbox.setPlainText("\n".join(l.replace(":", " >> ") for l in asset.tags))

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


# --- image this in a dateabase
#


assets = [
        {"name": "Gumby glasses", "author": "punkduck", "file": "gumby_glasses.mhclo", "icon": "/data/punkduck/Dokumente/makehuman2/data/clothes/hm08/gumby_glasses/gumby_glasses.thumb", 
            "tags": ["gumby", "slot:headgear", "epoch:contemporary"] },
        {"name": "Gumby boots", "author": "elvaerwyn", "file": "gumby_boots.mhclo", "icon": "/data/punkduck/Dokumente/makehuman2/data/clothes/hm08/gumby_boots/gumby_boots.thumb" ,
            "tags": ["gumby", "slot:feet:layer2:boots", "epoch:contemporary"] },
        {"name": "Gumby shirt", "author": "elvaerwyn", "file": "gumby_shirt.mhclo", "icon": "/data/punkduck/Dokumente/makehuman2/data/clothes/hm08/gumby_shirt/gumby_shirt.thumb",
            "tags": ["gumby", "slot:top:layer2:shirt", "epoch:contemporary", "gender:male"] },
        {"name": "Gumby vest", "author": "elvaerwyn", "file": "gumby_vest.mhclo", "icon": "/data/punkduck/Dokumente/makehuman2/data/clothes/hm08/gumby_vest/gumby_vest.thumb",
            "tags": ["gumby", "slot:top:layer2", "epoch:contemporary", "gender:male"] },
        {"name": "Gumby trousers", "author": "elvaerwyn", "file": "gumby_trousers.mhclo", "icon": "/data/punkduck/Dokumente/makehuman2/data/clothes/hm08/gumby_trousers/gumby_trousers.thumb",
            "tags": ["gumby", "slot:bottom:layer2:pants", "epoch:contemporary", "gender:male"] },
        {"name": "Sleeveless crop top", "author": "punkduck", "file": "sleevelesscroptop.mhclo", "icon": "/data/punkduck/Dokumente/makehuman2/data/clothes/hm08/sleevelesscroptop/sleevelesscroptop.thumb",
            "tags": ["slot:top:layer2:shirt", "epoch:contemporary", "gender:female"] },
        {"name": "Short bodysuit", "author": "punkduck", "file": "shortbodysuit.mhclo", "icon": "/data/punkduck/Dokumente/makehuman2/data/clothes/hm08/shortbodysuit/shortbodysuit.thumb",
            "tags": ["slot:top:layer2:suit", "epoch:contemporary", "gender:female"] },
        {"name": "French bra", "author": "punkduck", "file": "frenchbra.mhclo", "icon": "/data/punkduck/Dokumente/makehuman2/data/clothes/hm08/frenchbra/frenchbra.thumb",
            "tags": ["slot:top:layer1:bra", "epoch:contemporary", "gender:female"] },
        {"name": "French bottom", "author": "punkduck", "file": "frenchbottom.mhclo", "icon": "/data/punkduck/Dokumente/makehuman2/data/clothes/hm08/frenchbottom/frenchbottom.thumb",
            "tags": ["slot:bottom:layer1:panties", "epoch:contemporary", "gender:female"] },
        {"name": "assetwithoutimage", "author": "punkduck", "file": "noidea.mhclo", "icon": None, 
            "tags": ["epoch:future", "slot:bottom" ] },
        ]


class Equipment():
    def __init__(self, glob, eqtype):
        self.glob = glob
        self.env = glob.env
        self.type = eqtype
        self.filterjson = None
        self.picwidget = None
        self.filterview = None
        self.asset_category = []
        for elem in assets:
            self.asset_category.append(MHPictSelectable(elem["name"], elem["icon"], elem["file"],  elem["author"], elem["tags"]))

    def prepare(self):
        # load filter from file according to base mesh
        #
        path = os.path.join(self.env.path_sysdata, self.type, self.env.basename, "selection_filter.json")
        with open(path, 'r') as f:
            self.filterjson = json.load(f)


    def leftPanel(self):
        """
        done first
        """
        self.infobox = InformationBox()
        slayout = QHBoxLayout()  # layout for textbox + empty button
        v1layout = QVBoxLayout()    # this is for searching
        gbox = QGroupBox("Filtering")
        gbox.setObjectName("subwindow")


        widget = QWidget()
        widget.setStyleSheet("""background-color: #323232;
            color: #ffffff;
            """)

        filteredit = editBox(slayout, widget)
        self.filterview = FilterTree(self.asset_category, filteredit, self.infobox.setInformation)
        self.filterview.addTree(self.filterjson)
        self.filterview.selectionModel().selectionChanged.connect(self.filterview.filterChanged)
        filteredit.addConnect(self.filterview.filterChanged)

        v1layout.addWidget(self.filterview)
        v1layout.addWidget(QLabel("Filter:"))
        v1layout.addLayout(slayout)

        v1layout.addWidget(self.infobox)
        gbox.setLayout(v1layout)
        return(gbox)

    def rightPanel(self):
        """
        draw tools Panel
        """
        self.v2layout = QVBoxLayout()    # and this to display data
        self.picwidget = PicSelectWidget(self.v2layout, "Clothes", multiSel=True)
        self.filterview.setPicLayout(self.picwidget.layout)
        self.picwidget.populate(self.asset_category, None, None, self.infobox.setInformation)
        return(self.v2layout)

