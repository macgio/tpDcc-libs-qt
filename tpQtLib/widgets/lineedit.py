#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to create different kind of line edits
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *


class BaseLineEdit(QLineEdit, object):
    """
    Basic line edit that takes a different color if it's empty
    """

    def __init__(self, default='', off_color=(125, 125, 125), on_color=(255, 255, 255), parent=None):
        super(BaseLineEdit, self).__init__(parent=parent)

        self._value = ''
        self._default = ''
        self._off_color = off_color
        self._on_color = on_color

        self.set_default(default)
        self.textChanged.connect(self._on_change)

    # region Properties
    def get_value(self):
        if self.text() == self._default:
            return ''
        else:
            return self._value

    def set_value(self, value):
        self._value = value

    value = property(get_value, set_value)
    # endregion

    # region Override Functions
    def focusInEvent(self, event):
        if self.text() == self._default:
            self.setText('')
            self.setStyleSheet(self._get_on_style())

    def focusOutEvent(self, event):
        if self.text() == '':
            self.setText(self._default)
            self.setStyleSheet(self._get_off_style())
    # endregion

    # region Public Functions
    def set_default(self, text):
        self.setText(text)
        self._default = text
        self.setStyleSheet(self._get_off_style())
    # endregion

    # region Private Functions
    def _get_on_style(self):
        return 'QLineEdit{color:rgb(%s, %s, %s);}' % (self._on_color[0], self._on_color[1], self._on_color[2])

    def _get_off_style(self):
        return 'QLineEdit{color:rgb(%s, %s, %s);}' % (self._off_color[0], self._off_color[1], self._off_color[2])

    def _on_change(self, text):
        if text != self._default:
            self.setStyleSheet(self._get_on_style())
            self._value = text
        else:
            self.setStyleSheet(self._get_off_style())
    # endregion


class BaseAttrLineEdit(QLineEdit, object):
    attr_type = None
    valueChanged = Signal()

    def __init__(self, parent=None):
        super(BaseAttrLineEdit, self).__init__(parent=parent)

        self.returnPressed.connect(self.update)
        self.editingFinished.connect(self.update)

    # region Properties
    def get_value(self):
        return None

    value = property(get_value)
    # endregion


class FloatLineEdit(BaseAttrLineEdit, object):
    attr_type = 'float'
    valueChanged = Signal(float)

    def __init__(self, parent=None):
        super(FloatLineEdit, self).__init__(parent=parent)

    # region Override Properties
    def get_value(self):
        if not self.text():
            return 0.0
        return float(self.text())

    value = property(get_value)
    # endregion

    # region Override Functions
    def setText(self, text):
        super(FloatLineEdit, self).setText('%.2f' % float(text))

    def update(self):
        if self.text():
            self.setText(self.text())
        super(FloatLineEdit, self).update()
        self.valueChanged.emit(float(self.text()))
    # endregion


class IntLineEdit(QLineEdit, object):
    attr_type = 'int'
    valueChanged = Signal(int)

    def __init__(self, parent=None):
        super(IntLineEdit, self).__init__(parent=parent)

    # region Override Properties
    def get_value(self):
        if not self.text():
            return 0
        return int(self.text())

    value = property(get_value)
    # endregion

    # region Override Functions
    def setText(self, text):
        super(IntLineEdit, self).setText('%s' % int(text))

    def update(self):
        if self.text():
            self.setText(self.text())
        super(IntLineEdit, self).update()
        self.valueChanged.emit(int(self.text()))
    # endregion
