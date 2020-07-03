#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains color option implementation
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import layouts, label, color
from tpDcc.libs.qt.widgets.options import option


class ColorOption(option.Option, object):
    def __init__(self, name, parent, main_widget):
        super(ColorOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'color'

    def get_option_widget(self):
        return GetColorWidget(name=self._name)

    def get_name(self):
        name = self._option_widget.get_name()
        return name

    def set_name(self, name):
        self._option_widget.set_name(name)

    def get_value(self):
        return self._option_widget.get_value()

    def set_value(self, value):
        self._option_widget.set_value(value)

    def _setup_option_widget_value_change(self):
        self._option_widget.valueChanged.connect(self._on_value_changed)


class GetColorWidget(base.BaseWidget, object):
    valueChanged = Signal(object)

    def __init__(self, name, parent=None):
        self._name = name
        super(GetColorWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)

        return main_layout

    def ui(self):
        super(GetColorWidget, self).ui()

        self._label = label.BaseLabel(self._name)
        self._label.setAlignment(Qt.AlignRight)
        self._label.setMinimumWidth(75)
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._color_widget = color.ColorSelector(parent=self)
        self._color_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._color_widget.set_display_mode(color.ColorSelector.DisplayMode.NO_ALPHA)
        self._color_widget.set_color(QColor(240, 245, 255))
        self._color_widget.set_show_mode(self._color_widget.ShowMode.DIALOG)

        self.main_layout.addWidget(self._label)
        self.main_layout.addWidget(self._color_widget)

    def get_value(self):
        return self._color_widget.color().getRgbF()

    def set_value(self, value):
        self._color_widget.set_color(QColor.fromRgbF(*value))

    def get_name(self):
        return self._label.text()

    def set_name(self, value):
        self._label.setText(value)

    def setup_signals(self):
        self._color_widget.colorChanged.connect(self.valueChanged.emit)
