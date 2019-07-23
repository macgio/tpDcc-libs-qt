#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base class for Qt pixmaps
"""

from __future__ import print_function, division, absolute_import

from Qt.QtGui import *

from tpQtLib.core import color


class Pixmap(QPixmap, object):
    def __init__(self, *args):
        super(Pixmap, self).__init__(*args)

        self._color = None

    def set_color(self, new_color):
        """
        Sets pixmap's color
        :param new_color: variant (str || QColor), color to apply to the pixmap
        """

        if isinstance(new_color, str):
            new_color = color.Color.from_string(new_color)

        if not self.isNull():
            painter = QPainter(self)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.setBrush(new_color)
            painter.setPen(new_color)
            painter.drawRect(self.rect())
            painter.end()

        self._color = new_color
