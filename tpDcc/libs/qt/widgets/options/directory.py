#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains directory option implementation
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *

from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import directory
from tpDcc.libs.qt.widgets.options import option


class DirectoryOption(option.Option, object):
    def __init__(self, name, parent, main_widget):
        super(DirectoryOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'directory'

    def get_option_widget(self):
        return DirectoryWidget(self._name)

    def get_value(self):
        value = self._option_widget.get_directory()
        if not value:
            value = ''

        return value

    def set_value(self, value):
        value = str(value)
        self._option_widget.set_directory(value)

    def _setup_option_widget_value_change(self):
        self._option_widget.directoryChanged.connect(self._on_value_changed)


class DirectoryWidget(base.BaseWidget, object):

    directoryChanged = Signal(object)

    def __init__(self, name, parent=None):
        self._name = name
        super(DirectoryWidget, self).__init__(parent=parent)

    def ui(self):
        super(DirectoryWidget, self).ui()

        self.directory_widget = directory.GetDirectoryWidget()
        self.main_layout.addWidget(self.directory_widget)

    def setup_signals(self):
        self.directory_widget.directoryChanged.connect(self.directoryChanged.emit)

    def get_directory(self):
        return self.directory_widget.get_directory()

    def set_directory(self, value):
        self.directory_widget.set_directory(value)

    def get_label_text(self):
        return self._name
