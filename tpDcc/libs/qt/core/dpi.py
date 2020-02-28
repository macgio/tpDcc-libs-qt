#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base class to handle DPI functionality
"""

from __future__ import print_function, division, absolute_import

from tpDcc.libs.qt.core import qtutils


class DPIScaling(object):
    """
    Mixin class that can be used in any QWidget to add DPI scaling functionality to it
    """

    def setFixedSize(self, size):
        return super(DPIScaling, self).setFixedSize(qtutils.dpi_scale(size))

    def setFixedHeight(self, height):
        return super(DPIScaling, self).setFixedHeight(qtutils.dpi_scale(height))

    def setFixedWidth(self, width):
        return super(DPIScaling, self).setFixedWidth(qtutils.dpiScale(width))

    def setMaximumWidth(self, width):
        return super(DPIScaling, self).setMaximumWidth(qtutils.dpi_scale(width))

    def setMinimumWidth(self, width):
        return super(DPIScaling, self).setMinimumWidth(qtutils.dpi_scale(width))

    def setMaximumHeight(self, height):
        return super(DPIScaling, self).setMaximumHeight(qtutils.dpi_scale(height))

    def setMinimumHeight(self, height):
        return super(DPIScaling, self).setMinimumHeight(qtutils.dpi_scale(height))
