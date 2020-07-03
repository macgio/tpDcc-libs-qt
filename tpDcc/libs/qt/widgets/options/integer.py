#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains integer option implementation
"""

from __future__ import print_function, division, absolute_import

from tpDcc.libs.qt.widgets import spinbox
from tpDcc.libs.qt.widgets.options import float


class IntegerOption(float.FloatOption, object):

    def __init__(self, name, parent, main_widget):
        super(IntegerOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'integer'

    def get_option_widget(self):
        return spinbox.BaseSpinBoxNumber(self._name)
