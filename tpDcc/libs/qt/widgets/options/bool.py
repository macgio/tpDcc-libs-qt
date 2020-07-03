#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains bool option implementation
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *

from tpDcc.libs.qt.widgets import spinbox, checkbox
from tpDcc.libs.qt.widgets.options import option


class BooleanOption(option.Option, object):

    def __init__(self, name, parent, main_widget):
        super(BooleanOption, self).__init__(name=name, parent=parent, main_widget=main_widget)
        self.main_layout.setContentsMargins(0, 2, 0, 2)

    def get_option_type(self):
        return 'boolean'

    def get_option_widget(self):
        return BooleanWidget(self._name)

    def get_value(self):
        return self._option_widget.get_value()

    def set_value(self, value):
        self._option_widget.set_value(value)

    def _setup_option_widget_value_change(self):
        self._option_widget.valueChanged.connect(self._on_value_changed)


class BooleanWidget(spinbox.BaseNumberWidget, object):
    def __init__(self, name, parent=None):
        super(BooleanWidget, self).__init__(name, parent)
        self._number_widget.stateChanged.connect(self._on_value_changed)

    def get_number_widget(self):
        return checkbox.BaseCheckBox()

    def get_value(self):
        value = self._number_widget.isChecked()
        if value is None:
            value = False

        return value

    def set_value(self, new_value):
        if new_value:
            state = Qt.CheckState.Checked
        else:
            state = Qt.CheckState.Unchecked
        self._number_widget.setCheckState(state)

    def _on_value_changed(self):
        self.valueChanged.emit(self.get_value())
