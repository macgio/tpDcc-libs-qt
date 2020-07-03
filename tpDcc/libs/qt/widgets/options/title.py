#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains title option implementation
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *

from tpDcc.libs.qt.widgets import dividers
from tpDcc.libs.qt.widgets.options import option


class TitleOption(option.Option, object):
    def __init__(self, name, parent, main_widget):
        super(TitleOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

        self.main_layout.setContentsMargins(0, 2, 0, 2)
        self.main_layout.setAlignment(Qt.AlignCenter)

    def get_option_widget(self):
        return DividerWidget(text=self._name, alignment=Qt.AlignCenter)

    def get_option_type(self):
        return 'title'

    def get_name(self):
        name = self._option_widget.get_text()
        return name

    def set_name(self, name):
        self._option_widget.set_text(name)


class DividerWidget(dividers.Divider, object):

    def get_label_text(self):
        return self.get_text()

    def set_label_text(self, text):
        self.set_text(text)
