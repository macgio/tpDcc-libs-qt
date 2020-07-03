#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains combo option implementation
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import layouts, label, combobox
from tpDcc.libs.qt.widgets.options import option


class ComboOption(option.Option, object):
    def __init__(self, name, parent, main_widget):
        super(ComboOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'combo'

    def get_option_widget(self):
        return ComboWidget(name=self._name)

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


class ComboWidget(base.BaseWidget, object):
    valueChanged = Signal(object)

    def __init__(self, name, parent=None):
        self._name = name
        super(ComboWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)

        return main_layout

    def ui(self):
        super(ComboWidget, self).ui()

        self._label = label.BaseLabel(self._name)
        self._label.setAlignment(Qt.AlignRight)
        self._label.setMinimumWidth(75)
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._combo_widget = combobox.BaseComboBox()
        self._combo_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.main_layout.addWidget(self._label)
        self.main_layout.addWidget(self._combo_widget)

    def get_value(self):
        items_text = [self._combo_widget.itemText(i) for i in range(self._combo_widget.count())]
        return [items_text, [self._combo_widget.currentIndex(), self._combo_widget.currentText()]]

    def set_value(self, value):
        items = value[0]
        current_list = value[1] if len(value) > 1 else None
        for value in items:
            self._combo_widget.addItem(value)
        if current_list:
            index = current_list[0]
            if index >= 0:
                self._combo_widget.setCurrentIndex(index)

    def get_name(self):
        return self._label.text()

    def set_name(self, value):
        self._label.setText(value)

    def setup_signals(self):
        self._combo_widget.currentIndexChanged.connect(self.valueChanged.emit)
