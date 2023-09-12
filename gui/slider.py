import os
import sys
import json
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QPixmap, QPen

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QStyle, QStyleOptionSlider, QLabel, QPushButton, QSizePolicy, QDoubleSpinBox, QProgressBar



class ScalePictureButton(QPushButton):
    def __init__(self, name, icon, tip):
        self.icon = icon
        super().__init__(name)
        image = QPixmap(icon)
        self.setPicture(image)
        self.setCheckable(True)
        self.setMaximumSize(image.size())
        self.setToolTip(tip)

    def setPicture(self, icon):
        self.picture = icon
        self.update()

    def sizeHint(self):
        return self.picture.size()

    def paintEvent(self, e):
        painter = QPainter(self)
        if self.isChecked():
            painter.drawPixmap(0, 0, self.picture)
            pen = QPen()
            pen.setColor(Qt.yellow)
            pen.setWidth(5)

            painter.setPen(pen)
            painter.drawRect(self.rect())
        else:
            painter.drawPixmap(0, 0, self.picture)

class ScaleCombo(QWidget):
    def __init__(self, elem, minimum, maximum, step=1, parent=None, update=None):
        super(ScaleCombo, self).__init__(parent=parent)

        self.parentUpdate = update
        self.resetIcon = parent.resetIcon
        i_units=range(minimum, maximum+step, step)
        self.units=list(zip(i_units,map(str,i_units)))

        self.margin = 10
        self.min = minimum
        self.max = maximum
        self.step = step
        self.elem = elem
        self.expanded = False
        self.dSpinBox = None
        self.resetButton = None
        self.slider = None

        self.comboLayout=QVBoxLayout(self)

        if self.expanded:
            self.addExpandedFeatures()
        else:
            self.addNonExpandedFeatures()

        self.ilayout=QHBoxLayout()

        self.image = ScalePictureButton(elem.displayname, elem.icon, elem.tip)
        self.image.setChecked(self.expanded)
        self.image.pressed.connect(self.selectButtonPressed)
        self.ilayout.addWidget(self.image)

        self.rightCol = QVBoxLayout()
        self.rightCol.addWidget(QLabel(elem.displayname))
        if self.expanded:
            self.rightCol.addLayout(self.spinLayout)
        else:
            self.rightCol.addWidget(self.gvalue)

        self.ilayout.addLayout(self.rightCol)
        self.comboLayout.addLayout(self.ilayout)
        if self.expanded:
            self.comboLayout.addWidget(self.slider)

    def addNonExpandedFeatures(self):
        """
        add progress bar as indicator
        """
        self.comboLayout.setContentsMargins(self.margin,0, self.margin,0 )
        self.gvalue = QProgressBar()
        self.gvalue.setRange(-100,100)
        self.gvalue.setValue(self.elem.value)
        self.gvalue.setMaximumHeight(15)
        self.gvalue.setFormat("%v")

    def addExpandedFeatures(self):
        """
        add double-spin box with reset button
        add slider
        """
        self.comboLayout.setContentsMargins(self.margin,self.margin, self.margin,self.margin +5)
        self.spinLayout = QHBoxLayout()
        self.dSpinBox = QDoubleSpinBox()
        self.dSpinBox.setRange(-100.0, 100.0)
        self.dSpinBox.setSingleStep(0.01)
        self.dSpinBox.setValue(self.elem.value)
        self.dSpinBox.valueChanged.connect(self.dspinValueChanged)
        self.resetButton = QPushButton()
        self.resetButton.setToolTip("Reset to 0.0")
        self.resetButton.setIcon(self.resetIcon)
        self.resetButton.setMaximumWidth(30)
        self.resetButton.pressed.connect(self.resetButtonPressed)
        self.spinLayout.addWidget(self.dSpinBox)
        self.spinLayout.addWidget(self.resetButton)

        self.slider=QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(self.min)
        self.slider.setMaximum(self.max)
        self.slider.setMinimumWidth(300)
        self.slider.setValue(self.elem.value)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(self.step)
        #self.slider.setStyleSheet("QSlider { background-color:#c0c0c0;}")
        #self.slider.setStyleSheet("QSlider { background-color: transparent;} QSlider::groove:horizontal {height: 8px; background-color: #d7801a;}")
        self.slider.valueChanged.connect(self.sliderValueChanged)

    def sliderValueChanged(self):
        """
        change dspin-box and element  accordingly
        """
        value = self.slider.value()
        self.dSpinBox.setValue(value)
        self.elem.value = value

    def dspinValueChanged(self):
        """
        change slider and element accordingly 
        """
        value = self.dSpinBox.value()
        self.slider.setValue(value)
        self.elem.value = value
        self.elem.callback()

    def resetButtonPressed(self):
        """
        change sliders and element accordingly
        """
        self.slider.setValue(0)
        self.dSpinBox.setValue(0)
        self.elem.value = 0

    def selectButtonPressed(self):
        """
        call parent function to disable other buttons
        """
        self.parentUpdate(self)
        self.image.setChecked(not self.expanded)

    def comboUpdate(self, expand):
        """
        called from combo array, sliders will be displayed
        or only progress bars according to expanded mode
        """
        if expand is False:
            self.dSpinBox.deleteLater()
            self.resetButton.deleteLater()
            self.spinLayout.deleteLater()
            self.slider.deleteLater()
            self.addNonExpandedFeatures()
            self.rightCol.addWidget(self.gvalue)
            self.expanded = False
            self.image.setChecked(self.expanded)
            self.elem.selected = False
        else:
            self.gvalue.deleteLater()
            self.addExpandedFeatures()
            self.rightCol.addLayout(self.spinLayout)
            self.comboLayout.addWidget(self.slider)
            self.expanded = True
            self.elem.selected = True

    def paintEvent(self, e):
        """
        avoid to paint it when expanded is false
        (could lead to race condition otherwise)
        """
        if self.expanded is False:
            return
        super(ScaleCombo,self).paintEvent(e)
        style=self.slider.style()
        st_slider=QStyleOptionSlider()
        st_slider.initFrom(self.slider)

        slength=style.pixelMetric(QStyle.PM_SliderLength, st_slider, self.slider) // 2
        available=style.pixelMetric(QStyle.PM_SliderSpaceAvailable, st_slider, self.slider)
        ypos=self.rect().bottom()

        painter=QPainter(self)

        for v, v_str in self.units:

            # get the size of the label
            rect=painter.drawText(QRect(), Qt.TextDontPrint, v_str)

            x_loc=QStyle.sliderPositionFromValue(self.min, self.max, v, available)+slength
            xpos=x_loc-rect.width()//2+self.margin

            pos=QPoint(xpos, ypos)
            painter.drawText(pos, v_str)

class ScaleComboArray(QWidget):
    """
    a slider array of all the elements in modelling
    """
    def __init__(self, mainwidget, modelling, filterparam=None,  parent=None):
        super(ScaleComboArray, self).__init__(parent=parent)
        self.layout=QVBoxLayout(self)
        self.scaleComboArray = []
        self.resetIcon = mainwidget.style().standardIcon(QStyle.SP_DialogResetButton)
        for elem in modelling:
            if filterparam is None or elem.group == filterparam:
                scalecombo = ScaleCombo(elem,  -100, 100, 25, parent=self, update=self.comboArrayUpdate)
                self.scaleComboArray.append(scalecombo)
                self.layout.addWidget(scalecombo)
        self.layout.addStretch()

    def comboArrayUpdate(self, elem):
        """
        update all widgets
        """
        if elem.expanded:
            elem.comboUpdate(False)
        else:
            for scalecombo in self.scaleComboArray:
                if scalecombo.expanded:
                    scalecombo.comboUpdate(False)
            elem.comboUpdate(True)

