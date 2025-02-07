from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QComboBox, QLabel, QLabel, QListWidget, QAbstractItemView,
    QListWidgetItem
)

from PySide6.QtCore import QSize, Qt, QRect
from gui.slider import SimpleSlider
from core.randomizer import TargetRandomizer

class RandomForm(QVBoxLayout):
    def __init__(self, parent, view):
        self.view = view
        self.parent = parent
        self.glob = parent.glob
        super().__init__()
        self.tr = TargetRandomizer(self.glob)
        self.reset = True
        self.symmetric = True
        self.weirdofactor = 20
        self.idealfactor = 50

        if self.tr.hasGender():
            self.addWidget(QLabel("Gender:"))
            self.gendelem = QComboBox()
            self.gendelem.addItems(['any', 'female only', 'male only', 'male of female'])
            self.gendelem.currentIndexChanged.connect(self.genderChanged)
            self.addWidget(self.gendelem)

        groups = self.tr.getGroups()
        if len(groups) > 0:
            self.listWidget = QListWidget()
            self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
            i = 0
            for gname, preselect in groups.items():
                item = QListWidgetItem(gname)
                self.listWidget.addItem(item)
                self.listWidget.item(i).setSelected(preselect)  # does not work on item?
                i += 1
            self.listWidget.itemClicked.connect(self.groupChanged)
            self.addWidget(self.listWidget)

        self.weirdoelem = SimpleSlider("Weirdo factor: ", 0, 100, self.weirdoChanged)
        self.weirdoelem.setSliderValue(self.weirdofactor)
        self.addWidget(self.weirdoelem)

        if self.tr.hasIdeal():
            self.idealelem = SimpleSlider("Minimum ideal factor: ", 0, 100, self.idealChanged)
            self.idealelem.setSliderValue(self.idealfactor)
            self.addWidget(self.idealelem)

        self.symelem = QCheckBox("Symmetric character")
        self.symelem.setLayoutDirection(Qt.LeftToRight)
        self.symelem.toggled.connect(self.changeSym)
        self.symelem.setChecked(True)
        self.addWidget(self.symelem)
        
        self.resetelem = QCheckBox("Always reset character")
        self.resetelem.setLayoutDirection(Qt.LeftToRight)
        self.resetelem.toggled.connect(self.changeReset)
        self.resetelem.setChecked(True)
        self.addWidget(self.resetelem)

        self.addStretch()
        self.randbutton=QPushButton("Randomize")
        self.randbutton.clicked.connect(self.randomize)
        self.addWidget(self.randbutton)

        self.prepare()

    def prepare(self):
        self.tr.setFromDefault(self.reset)
        self.tr.setSym(self.symmetric)

    def groupChanged(self):
        items = self.listWidget.selectedItems()
        x = []
        for i in range(len(items)):
            x.append(str(self.listWidget.selectedItems()[i].text()))
        self.tr.setGroups(x)

    def changeReset(self, param):
        self.reset = param
        self.tr.setFromDefault(self.reset)

    def changeSym(self, param):
        self.symmetric = param
        self.tr.setSym(self.symmetric)

    def genderChanged(self, index):
        self.tr.setGender(index)

    def weirdoChanged(self, value):
        self.tr.setWeirdoFactor(value / 100)

    def idealChanged(self, value):
        self.tr.setIdealMinimum(value / 100)

    def randomize(self):
        if self.tr.do():
            self.tr.apply()


