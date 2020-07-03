#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains vector3 option implementation
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *

from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import layouts, label, spinbox
from tpDcc.libs.qt.widgets.options import option


class Vector3FloatOption(option.Option, object):
    def __init__(self, name, parent, main_widget):
        super(Vector3FloatOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'vector3f'

    def get_option_widget(self):
        return GetVector3FloatWidget(name=self._name)

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


class GetVector3FloatWidget(base.BaseWidget, object):
    valueChanged = Signal(object)

    def __init__(self, name, parent=None):
        self._name = name
        super(GetVector3FloatWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)

        return main_layout

    def ui(self):
        super(GetVector3FloatWidget, self).ui()

        self._label = label.BaseLabel(self._name)
        self._label.setAlignment(Qt.AlignRight)
        self._label.setMinimumWidth(75)
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._x_spinbox = spinbox.DragDoubleSpinBoxLineAxis(axis='x', min=-9999, max=9999, parent=self)
        self._y_spinbox = spinbox.DragDoubleSpinBoxLineAxis(axis='y', min=-9999, max=9999, parent=self)
        self._z_spinbox = spinbox.DragDoubleSpinBoxLineAxis(axis='z', min=-9999, max=9999, parent=self)

        self.main_layout.addWidget(self._label)
        self.main_layout.addWidget(self._x_spinbox)
        self.main_layout.addWidget(self._y_spinbox)
        self.main_layout.addWidget(self._z_spinbox)

    def get_value(self):
        return [self._x_spinbox.value(), self._y_spinbox.value(), self._z_spinbox.value()]

    def set_value(self, value):
        self._x_spinbox.setValue(value[0])
        self._y_spinbox.setValue(value[1])
        self._z_spinbox.setValue(value[2])

    def get_name(self):
        return self._label.text()

    def set_name(self, value):
        self._label.setText(value)

    def setup_signals(self):
        self._x_spinbox.textChanged.connect(self._on_spinboxes_value_changed)
        self._y_spinbox.textChanged.connect(self._on_spinboxes_value_changed)
        self._z_spinbox.textChanged.connect(self._on_spinboxes_value_changed)

    def _on_spinboxes_value_changed(self, *args, **kwargs):
        self.valueChanged.emit([self._x_spinbox.value(), self._y_spinbox.value(), self._z_spinbox.value()])
