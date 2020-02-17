#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt spinner widgets
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpDcc.libs.qt.core import base


class BaseSpinBox(base.BaseNumberWidget):
    enterPressed = Signal()

    def __init__(self, name='', parent=None):
        super(BaseSpinBox, self).__init__(name=name, parent=parent)

        self._setup_spin_widget()

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.enterPressed.emit()

    def get_number_widget(self):
        spin_box = QSpinBox()
        spin_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return spin_box

    def _setup_spin_widget(self):
        if hasattr(self._number_widget, 'CorrectToNearestValue'):
            self._number_widget.setCorrectionMode(self._number_widget.CorrectToNearestValue)
        if hasattr(self._number_widget, 'setWrapping'):
            self._number_widget.setWrapping(False)
        if hasattr(self._number_widget, 'setDecimals'):
            self._number_widget.setDecimals(3)

        self._number_widget.setMaximum(100000000)
        self._number_widget.setMinimum(-100000000)
        # self._number_widget.setButtonSymbols(self._number_widget.NoButtons)

        self._number_widget.valueChanged.connect(self._on_value_changed)


class BaseDoubleSpinBox(BaseSpinBox, object):
    def __init__(self, name='', parent=None):
        super(BaseDoubleSpinBox, self).__init__(name=name, parent=parent)

    def get_number_widget(self):
        spin_box = QDoubleSpinBox()
        spin_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return spin_box


class DragDoubleSpinBox(base.BaseNumberWidget, object):
    def __init__(self, name='', parent=None):
        super(DragDoubleSpinBox, self).__init__(name=name, parent=parent)

    def get_number_widget(self):
        spin_box = DragDoubleSpinBoxLine()
        spin_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return spin_box


class DragDoubleSpinBoxLine(QLineEdit, object):
    """
    Using middle mouse from left to right will scale the value and a little bar will show the
    percent of the current value
    """

    valueChanged = Signal(float)

    def __init__(self, start=0.0, max=10, min=-10, positive=False, parent=None):
        super(DragDoubleSpinBoxLine, self).__init__(parent=parent)

        self._click = False
        self._default = str(start)
        self._mouse_position = QPoint(0, 0)
        self._min = 0.01 if positive else min
        self._max = max
        self._sup = positive
        self.setText(str(start))

        self._setup_validator()

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._click = True
            self._mouse_position = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._click = False

    def mouseDoubleClickEvent(self, event):
        self.setText(self._default)

    def mouseMoveEvent(self, event):
        if self._click:
            delta = event.x() - self._mouse_position.x()
            v = float(self.text()) + delta / 100.0
            v = max(self._min, min(self._max, v))
            self.setText(str(v))
            self._mouse_position = event.pos()
            self.valueChanged.emit(v)

    def paintEvent(self, event):
        super(DragDoubleSpinBoxLine, self).paintEvent(event)
        p = QPainter()
        p.begin(self)

        try:
            v = float(self.text())
        except Exception:
            v = 0.0000001

        try:
            v /= self._max if v > 0 else (self._min * -1)
        except Exception:
            pass
        if self._sup:
            p.fillRect(QRect(0, self.height() - 2, v * self.width(), 2), QColor(0, 255, 0))
        else:
            p.fillRect(
                QRect(self.width() * 0.5, self.height() - 2, v * self.width() * 0.5, 2),
                QColor(0, 255, 0) if v > 0 else QColor(255, 0, 0))
        p.end()

    def get_validator(self):
        return QDoubleValidator()

    def value(self):
        try:
            return float(self.text())
        except Exception:
            return 0.0

    # NOTE: Here I'm breaking naming nomenclature on purpose. Doing this we follow nomenclature of Qt SpinBoxes
    def setValue(self, new_value):
        self.setText(str(new_value))

    # region Private Functions
    def _setup_validator(self):
        self.setValidator(self.get_validator())
