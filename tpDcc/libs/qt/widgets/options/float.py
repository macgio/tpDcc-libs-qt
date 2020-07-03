#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains float option implementation
"""

from __future__ import print_function, division, absolute_import

from tpDcc.libs.qt.widgets import spinbox
from tpDcc.libs.qt.widgets.options import option


class FloatOption(option.Option, object):

    def __init__(self, name, parent, main_widget):
        super(FloatOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'float'

    def get_option_widget(self):
        return spinbox.BaseDoubleNumberSpinBox(self._name)

    def get_value(self):
        return self._option_widget.get_value()

    def set_value(self, value):
        self._option_widget.set_value(value)

    def _setup_option_widget_value_change(self):
        self._option_widget.valueChanged.connect(self._on_value_changed)
