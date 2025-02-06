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

        self.addWidget(QLabel("Gender:"))
        self.gendelem = QComboBox()
        self.gendelem.addItems(['any', 'female only', 'male only', 'male of female'])
        self.gendelem.currentIndexChanged.connect(self.genderChanged)
        self.addWidget(self.gendelem)

        # TODO: flexible selection etc.
        self.listWidget = QListWidget()
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.listWidget.setGeometry(QRect(10, 10, 211, 291))

        for elem in ("main", "face", "torso", "arms", "legs", "gender|breast", "shapes|female shapes", "shapes|female hormonal", 
                "shapes|male shapes", "shapes|fale hormonal"):
            item = QListWidgetItem(elem)
            self.listWidget.addItem(item)
        self.listWidget.itemClicked.connect(self.groupChanged)
        self.addWidget(self.listWidget)

        self.weirdoelem = SimpleSlider("Weirdo factor: ", 0, 100, self.weirdoChanged)
        self.weirdoelem.setSliderValue(self.weirdofactor)
        self.addWidget(self.weirdoelem)

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
        self.tr.setNonSymGroups(["trans-in", "trans-out"])
        self.tr.setFromDefault(self.reset)
        self.tr.setSym(self.symmetric)
        for i in range(5):
            self.listWidget.item(i).setSelected(True)
        self.tr.setGroups(["main", "face", "torso", "arms", "legs"])

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


