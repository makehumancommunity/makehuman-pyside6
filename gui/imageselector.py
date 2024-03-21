import sys
import typing
import os
from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtGui import QPixmap, QPainter, QPen, QIcon, QColor, QFont, QStandardItemModel, QStandardItem

from PySide6.QtWidgets import QApplication, QWidget, QLayout, QLayoutItem, QStyle, QSizePolicy, QPushButton, QAbstractButton, QRadioButton, QCheckBox, QGroupBox, QVBoxLayout, QLabel, QLineEdit, QTreeView, QAbstractItemView, QScrollArea, QPlainTextEdit, QHBoxLayout

from gui.materialwindow import  MHMaterialWindow


class IconButton(QPushButton):
    def __init__(self, funcid, path, tip, func):
        self._funcid = funcid
        icon  = QIcon(path)
        super().__init__()
        self.setIcon(icon)
        self.setIconSize(QSize(36,36))
        self.setCheckable(True)
        self.setFixedSize(40,40)
        self.setToolTip(tip)
        if func is not None:
            self.clicked.connect(func)

    def setChecked(self, value):
        super().setChecked(value)
        if value is True:
            self.setStyleSheet("background-color : orange")
        else:
            self.setStyleSheet("background-color : lightgrey")

class MHPictSelectable:
    def __init__(self, name: str, icon: str, filename: str, author: str, tags: list):
        self.name = name
        self.icon = icon
        self.filename = filename
        self.author = author
        self.tags = tags
        self.basename = os.path.split(filename)[1].lower()
        #
        # append filename, author and  name as tags as well
        #
        self.tags.append(name.lower())
        self.tags.append(self.basename)    # only name, not path
        if author is not None:
            self.tags.append(author.lower())
        self.status = 0

    def __str__(self):
        return('\n'.join("%s: %s" % item for item in vars(self).items()))

class PictureButton(QPushButton):
    """
    tri-state picture button
    holds state in asset.status to be be reachable from outside
    :param asset: asset to be shown (used for name)
    """
    def __init__(self, asset: MHPictSelectable, scale, emptyicon):

        self.asset = asset
        self.scale = scale
        self.icon = None

        super().__init__()
        if asset.icon is None:                 # will not be constant
            self.icon = emptyicon
            self.picture_added = False
        else:
            self.picture_added = True
            self.icon = asset.icon
        self.setCheckable(True)
        self.framecol  = (Qt.black, Qt.yellow, Qt.green, Qt.blue)
        self.setToolTip(asset.name + "\n" + asset.basename)
        self.update()

    #def __del__(self):
    #    print (self.asset.name + " deleted")

    def update(self):
        self.picture = QPixmap(self.icon).scaled(self.scale,self.scale, Qt.AspectRatioMode.KeepAspectRatio)
        super().update()

    def setScale(self, scale):
        self.scale=scale
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

class PicFlowLayout(QLayout):
    """
    selmode: multiple selection, will change refresh method
    """
    def __init__(self, parent, assets, callback, printinfo, margin: int=-1, hSpacing: int=-1, vSpacing: int=-1):

        super().__init__()
        self.itemList = list()
        self.wList = list()
        self.m_hSpace = hSpacing
        self.m_vSpace = vSpacing
        self.selmode = parent.selmode
        self.imagescale = parent.imagescale
        self.empty = parent.emptyIcon
        self.callback = callback
        self.printinfo = printinfo
        self.assetlist = assets
        self.filter = None
        self.ruleset = None
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
        if self.selmode == 1:
            for widget in self.wList:
                if widget is not current and widget.asset.status == 1:
                    widget.asset.status = 2
                    widget.update()
        else:
            for widget in self.wList:
                if widget is not current and widget.asset.status > 0:
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

    def updateAsset(self):
        current = self.sender()
        print (current.asset)

        if current.asset.status == 0:
            #print ("button " + str (self.text) + " pressed")
            current.asset.status = 3 if self.selmode == 2 else 1
            if self.printinfo is not None:
                self.printinfo(current.asset)
        else:
            #print ("button released")
            current.asset.status = 1 if self.selmode == 2 else 0
        self.callback(current.asset)
        self.refreshAllWidgets(current)

    def setImageScale(self, scale):
        self.imagescale = scale
        self.removeAllWidgets()
        self.populate(self.ruleset, self.filter)

    def getSelected(self):
        for widget in self.wList:
            if widget.asset.status == 1:
                return(widget.asset)
        return(None)
    
    def newAssetList(self, assets):
        self.assetlist = assets
        
    def populate(self, ruleset, filtertext):
        """
        :assetlist: complete asset list to be considered
        :ruleset: list for comparison or None
        :param filtertext: additional filter text or None
        """
        if filtertext == "":
            filtertext = None

        self.filter = filtertext
        self.ruleset = ruleset

        for asset in self.assetlist:
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
                button1 = PictureButton(asset, self.imagescale, self.empty)
                button1.pressed.connect(self.updateAsset)
                self.addWidget (button1)

class PicSelectWidget(QWidget):
    """
    PicSelectWidget is a PicFlowLayout embedded in a QGroupBox with a QScrollArea
    addWidget will add a button to the PicFlowLayout
    :param parent: for empty image, selection-mode
    :param callback: function to call when clicked
    """
    def __init__(self, parent, assets, callback, printinfo):
        self.layout = PicFlowLayout(parent, assets, callback, printinfo)
        super().__init__()

    def __del__(self):
        """
        this is a must, otherwise the widgets will use up complete memory
        """
        self.layout.removeAllWidgets()

    def refreshAllWidgets(self, current):
        self.layout.refreshAllWidgets(current)

    def populate(self, ruleset, filtertext):
        self.layout.populate(ruleset, filtertext)

    def getSelected(self):
        return(self.layout.getSelected())

    def addWidget(self, button):
        self.layout.addWidget (button)

    def setImageScale(self, scale):
        self.layout.setImageScale(scale)

class InformationBox(QWidget):
    def __init__(self, layout):
        super().__init__()
        self.layout = layout
        self.selectedName = QLabel("Name:\nAuthor:")
        self.layout.addWidget(self.selectedName)
        self.layout.addWidget(QLabel("Tags:"))
        self.tagbox = QPlainTextEdit()
        self.tagbox.setPlainText("")
        self.tagbox.setReadOnly(True)
        self.tagbox.setFixedHeight(120)
        self.layout.addWidget(self.tagbox)

    def setInformation(self, asset):
        self.selectedName.setText("Name: " + asset.name + "\n" + "Author: " + asset.author)
        self.tagbox.setPlainText("\n".join(l.replace(":", " \u23f5 ") for l in asset.tags)) # triangle as arrow

class FilterTree(QTreeView):
    """
    :param flowLayout: points to layout
    """

    def  __init__(self, assets, searchByFilterText, iconpath):

        self.assets = assets
        self.searchByFilterText = searchByFilterText
        self.flowLayout = None
        self.iconpath = iconpath
        self.shortcut = []
        self.shortcutbutton = []

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
            if find == "shortcut":
                for subelem in subtree[elem]:
                    self.shortcut.append(subelem)
                continue
            if find in ( "translate", "guessname"):
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

    def markSelectedButtons(self, funcid):
        for elem in self.shortcutbutton:
            elem.setChecked(elem._funcid == funcid)

    def shortCutPressed(self):
        """
        create a ruleset by a macro from button, so for an icon lingerie one has:
            gender:female&slot:top:layer1:bra|slot:bottom:layer1:panties
        what creates:
            {'gender': ['female'], 'slot': ['top:layer1:bra', 'bottom:layer1:panties']}
        """
        funcid = self.sender()._funcid
        text = self.shortcut[funcid][1]
        print ("Shortcut pressed: " + text)
        andOps = text.split("&")
        ruleset = {}
        for aelem in andOps:
            orOps = aelem.split("|")
            for oelem in orOps:
                layers = oelem.split(":")
                if len(layers) > 1:
                    key = layers[0]
                    if key in ruleset:
                        ruleset[key].append(":".join(layers[1:]))
                    else:
                        ruleset[key] = [ ":".join(layers[1:]) ]

        self.markSelectedButtons(funcid)
        self.flowLayout.removeAllWidgets()
        self.flowLayout.populate(ruleset, "")


    def addShortCuts(self):
        numicons = len(self.shortcut)
        if numicons == 0:
            return None
        i_per_row = 7

        layout=QVBoxLayout() if numicons > i_per_row else None
        row=QHBoxLayout()
        cnt = 0
        for funcid, elem in enumerate(self.shortcut):
            button = IconButton(funcid, os.path.join(self.iconpath, elem[0]), elem[2], self.shortCutPressed)
            row.addWidget(button)
            self.shortcutbutton.append(button)
            cnt += 1
            if cnt == i_per_row and layout is not None:
                row.addStretch()
                layout.addLayout(row)
                row =QHBoxLayout()
                cnt = 0
        if cnt != 0:
            row.addStretch()
            if layout is not None:
                layout.addLayout(row)

        return ( layout if numicons > i_per_row else row)


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
        self.markSelectedButtons(-1)
        self.flowLayout.removeAllWidgets()
        #print (ruleset)
        self.flowLayout.populate(ruleset, filtertext)

class editBox(QLineEdit):
    def  __init__(self, slayout, sweep):
        super().__init__()
        self.changeFilter = None
        self.empty = IconButton(0, sweep, "Clear filter", self.clearEditBox)
        slayout.addWidget(QLabel("Filter:"))
        slayout.addWidget(self)
        slayout.addStretch()
        slayout.addWidget(self.empty)
        self.setMaximumWidth(170)
        self.setFixedWidth(190)

    def addConnect(self, changeFilter):
        self.changeFilter = changeFilter
        self.returnPressed.connect(changeFilter)

    def clearEditBox(self):
        self.clear()
        if self.changeFilter is not None:
            self.changeFilter()

class ImageSelection():
    def __init__(self, parent, assetrepo, eqtype, selmode, callback, scale=2):
        self.parent = parent
        self.env = parent.glob.env
        self.assetrepo = assetrepo
        self.type = eqtype
        self.selmode = selmode
        self.callback = callback
        self.tagreplace = {}
        self.tagfromname = {}
        self.filterjson = None
        self.picwidget = None
        self.filterview = None
        self.asset_category = []
        self.scales = [48, 64, 96, 128]
        self.emptyIcon = os.path.join(self.env.path_sysdata, "icons", "empty_" + self.type + ".png")
        self.scaleindex = scale
        self.imagescale = self.scales[scale]
        if not os.path.isfile(self.emptyIcon):
            self.emptyIcon = os.path.join(self.env.path_sysdata, "icons", "noidea.png")

    def createTagGroups(self, subtree, path):
        """
        create texts to prepend certain tags, can also translate tags
        """
        for elem in subtree:
            if isinstance(elem, str):
                if elem == "Translate":                             # extra, change by word
                    for l in subtree[elem]:
                        self.tagreplace[l.lower()] = subtree[elem][l]
                    continue
                if elem == "GuessName":                             # extra, change by word
                    for l in subtree[elem]:
                        self.tagfromname[l.lower()] = subtree[elem][l]
                    continue
                if isinstance(subtree[elem], dict):
                    self.createTagGroups(subtree[elem], path + ":" + elem.lower())
                elif isinstance(subtree[elem], list):
                    if elem == "Shortcut":
                        pass
                    else:
                        for l in subtree[elem]:
                            repl = path + ":" + elem.lower()
                            self.tagreplace[l.lower()] = repl[1:]       # get rid of first ":"

    def completeTags(self, name, tags):
        """
        replace tags by tags with prepended strings or check name
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

        for tag in self.tagfromname:
            if tag in name:
                ntag = self.tagfromname[tag]
                if ntag not in newtags:
                    newtags.append(ntag)
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
                elem.tag = self.completeTags(elem.name, elem.tag)
                self.asset_category.append(MHPictSelectable(elem.name, elem.thumbfile, elem.path,  elem.author, elem.tag))

    def changeStatus(self):
        checked = []
        for elem in self.assetrepo:
            if elem.folder == self.type and elem.used is True:
                checked.append(elem.path)

        for elem in self.asset_category:
            elem.status = 1 if elem.filename in checked else 0

    def picButtonChanged(self, asset):
        multi = (self.selmode == 1)
        self.callback(asset, self.type, multi)
        if self.parent.material_window is not None:
            self.materialCallback()

    def scaleImages(self):
        # toggle through 4 scales
        self.scaleindex = (self.scaleindex + 1) % 4
        self.imagescale = self.scales[self.scaleindex]
        self.picwidget.setImageScale(self.imagescale)

    def materialCallback(self):
        selected = self.picwidget.getSelected()
        found = None
        if selected is not None:
            print ("Material change")
            print (selected)
            for elem in self.parent.glob.baseClass.attachedAssets:
                if elem.filename == selected.filename:
                    found = elem
                    break
        if found is not None:
            matimg = []
            print (found)   # asset in inventory
            oldmaterial = found.material
            matfiles = found.obj.material.listAllMaterials()
            for elem in matfiles:
                (folder, name) = os.path.split(elem)
                thumb = elem[:-6] + ".thumb"
                if not os.path.isfile(thumb):
                    thumb = None
                p = MHPictSelectable(name[:-6], thumb, elem, None, [])
                if elem == oldmaterial:
                    p.status = 1
                matimg.append(p)
            if self.parent.material_window is None:
                self.parent.material_window = MHMaterialWindow(self.parent, PicSelectWidget, matimg, found)
            else:
                self.parent.material_window.updateWidgets(matimg, found)

            mw = self.parent.material_window
            mw.show()
            mw.activateWindow()


    def leftPanel(self):
        """
        done first
        """
        iconpath = os.path.join(self.env.stdSysPath(self.type), "icons")
        
        v1layout = QVBoxLayout()    # this is for searching
        self.infobox = InformationBox(v1layout)

        slayout = QHBoxLayout()  # layout for textbox + empty button
        filteredit = editBox(slayout, os.path.join(self.env.path_sysicon, "sweep.png" ))
        self.filterview = FilterTree(self.asset_category, filteredit, iconpath)
        self.filterview.addTree(self.filterjson)
        self.filterview.selectionModel().selectionChanged.connect(self.filterview.filterChanged)
        shortcuts = self.filterview.addShortCuts()
        filteredit.addConnect(self.filterview.filterChanged)

        v1layout.addWidget(self.filterview)
        if shortcuts is not None:
            v1layout.addLayout(shortcuts)
        #v1layout.addWidget(QLabel("Filter:"))
        v1layout.addLayout(slayout)
        hlayout = QHBoxLayout()
        resize = os.path.join(self.env.path_sysicon, "resize.png" )
        sizebutton = IconButton(0, resize, "Resize thumbnails", self.scaleImages)
        hlayout.addWidget(sizebutton)
        hlayout.addStretch()

        matpath = os.path.join(self.env.path_sysicon, "materials.png" )
        matbutton = IconButton(0, matpath, "Change material", self.materialCallback)
        hlayout.addWidget(matbutton)

        v1layout.addLayout(hlayout)

        return(v1layout)

    def rightPanel(self):
        """
        draw tools Panel
        """
        self.picwidget = PicSelectWidget(self, self.asset_category, self.picButtonChanged, self.infobox.setInformation)
        self.filterview.setPicLayout(self.picwidget.layout)
        self.picwidget.populate(None, None)
        self.changeStatus()
        return(self.picwidget)

