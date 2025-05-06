"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    classes:
    * RandomValues
    * RandomForm
"""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QComboBox, QLabel, QLabel, QListWidget, QAbstractItemView,
    QListWidgetItem
)

from PySide6.QtCore import QSize, Qt, QRect
from gui.slider import SimpleSlider
from core.randomizer import TargetRandomizer

class RandomValues():
    """
    class to keep the values, when called again
    """
    def __init__(self, glob):
        self.symfactor   = 100
        self.idealfactor = 50
        self.weirdofactor= 20
        self.reset = True
        self.gender = 0
        self.genderitems = ['any', 'female only', 'male only', 'male or female']
        self.tr = TargetRandomizer(glob)
        self.groups = self.tr.getGroups()
        self.lgroup = {}
        for gname, preselect in self.groups.items():
            self.lgroup[gname] = preselect

class RandomForm(QVBoxLayout):
    def __init__(self, parent, view):
        self.view = view
        self.parent = parent
        self.glob = parent.glob
        values = self.values = self.glob.randomValues
        super().__init__()

        values.tr.storeAllValues()

        if values.tr.hasGender():
            self.addWidget(QLabel("Gender:"))
            self.gendelem = QComboBox()
            self.gendelem.addItems(values.genderitems)
            self.gendelem.currentIndexChanged.connect(self.genderChanged)
            self.gendelem.setToolTip("If not any, it creates only male and/or female characters")
            self.addWidget(self.gendelem)
        else:
            self.gendelem = None

        if len(values.lgroup) > 0:
            self.listWidget = QListWidget()
            self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
            for gname, preselect in values.lgroup.items():
                item = QListWidgetItem(gname)
                self.listWidget.addItem(item)
            self.listWidget.itemClicked.connect(self.groupChanged)
            self.addWidget(self.listWidget)

        self.weirdoelem = SimpleSlider("Weirdo factor: ", 0, 100, self.weirdoChanged)
        self.weirdoelem.setToolTip("The higher the values, the funnier the result.")
        self.addWidget(self.weirdoelem)

        if values.tr.hasIdeal():
            self.idealelem = SimpleSlider("Minimum ideal factor: ", 0, 100, self.idealChanged)
            self.idealelem.setToolTip("This should improve the proportions. 75 means, that nicer characters are create (75-100)")
            self.addWidget(self.idealelem)
        else:
            self.idealelem = None

        self.symelem = SimpleSlider("Symmetry factor: ", 0, 100, self.symChanged)
        self.symelem.setToolTip("100 means full symmetry, low values can create bizarre geometries.")
        self.addWidget(self.symelem)

        self.resetelem = QCheckBox("Reset character to default before")
        self.resetelem.setToolTip("Without this, you can alter a character randomly only for the selected targets.")
        self.resetelem.setLayoutDirection(Qt.LeftToRight)
        self.resetelem.toggled.connect(self.changeReset)
        self.addWidget(self.resetelem)

        self.addStretch()

        self.nonrandbutton=QPushButton("Reset to initial character")
        self.nonrandbutton.setToolTip("The character is set to the status before this randomizer was started.")
        self.nonrandbutton.clicked.connect(self.norandom)
        self.addWidget(self.nonrandbutton)

        self.randbutton=QPushButton("Random character [linear]")
        self.randbutton.setToolTip("The character is changed according to parameters using a linear distribution.")
        self.randbutton.clicked.connect(self.randomize)
        self.addWidget(self.randbutton)

        self.gaussbutton=QPushButton("Random character [gauss]")
        self.gaussbutton.setToolTip("The character is changed according to parameters using a gaussian distribution.")
        self.gaussbutton.clicked.connect(self.randomgauss)
        self.addWidget(self.gaussbutton)

        self.setValues()

    def setValues(self):
        v = self.values
        self.symelem.setSliderValue(v.symfactor)
        v.tr.setSym(v.symfactor / 100)

        if self.idealelem is not None:
            self.idealelem.setSliderValue(v.idealfactor)
            v.tr.setIdealMinimum(v.idealfactor / 100)

        self.weirdoelem.setSliderValue(v.weirdofactor)
        v.tr.setWeirdoFactor(v.weirdofactor / 100)

        self.resetelem.setChecked(v.reset)
        v.tr.setFromDefault(v.reset)

        if self.gendelem is not None:
            self.gendelem.setCurrentIndex(v.gender)
            v.tr.setGender(v.gender)

        i = 0
        for preselect in v.lgroup.values():
            self.listWidget.item(i).setSelected(preselect)
            i += 1

    def groupChanged(self):
        v = self.values
        i = 0
        x = []
        for name in v.lgroup:
            item = self.listWidget.item(i)
            b = item.isSelected()
            if b:
                x.append(str(item.text()))
            v.lgroup[name] = b
            i += 1
        v.tr.setGroups(x)

    def changeReset(self, param):
        v = self.values
        v.reset = param
        v.tr.setFromDefault(param)

    def symChanged(self, value):
        v = self.values
        v.symfactor = value
        v.tr.setSym(value / 100)

    def genderChanged(self, index):
        v = self.values
        v.gender = index
        v.tr.setGender(index)

    def weirdoChanged(self, value):
        v = self.values
        v.weirdofactor = value
        v.tr.setWeirdoFactor(value / 100)

    def idealChanged(self, value):
        v = self.values
        v.idealfactor = value
        v.tr.setIdealMinimum(value / 100)

    def randomize(self):
        tr = self.values.tr
        if tr.do(0):
            tr.apply()

    def randomgauss(self):
        tr = self.values.tr
        if tr.do(1):
            tr.apply()

    def norandom(self):
        tr = self.values.tr
        tr.restore()

