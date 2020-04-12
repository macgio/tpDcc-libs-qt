#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base class for Qt pixmaps
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtGui import *

from tpDcc.libs.qt.core import color, cache


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

    def overlay_pixmap(self, over_pixmap, new_color, align=Qt.AlignCenter):
        """
        Overlays a new pixmap pixmap on top of this pixmap
        :param over_pixmap:
        :param new_color:
        :param align:
        :return:
        """

        overlay_pixmap(pixmap=self, over_pixmap=over_pixmap, overlay_color=new_color, align=align)

    def tint(self, tint_color=(255, 255, 255, 100), composition_mode=QPainter.CompositionMode_Plus):
        """
        Tints current pixmap
        :param color:
        :param composition_mode:
        :return:
        """

        tint_pixmap(self, tint_color=tint_color, composition_mode=composition_mode)

    def grayscale(self):
        """
        Converts this pixmap into grayscale
        """

        pixmap = grayscale_pixmap(self)
        self.swap(pixmap)


def colorize_pixmap(pixmap, new_color):
    """
    Colorizes the given pixmap with a new color based on its alpha map
    :param QPixmap pixmap: Pixmap
    :param tuple new_color: new color in tuple format (255, 255, 255)
    :return:  Pixmap
    """

    if isinstance(new_color, str):
        new_color = color.Color.from_string(new_color)
    elif isinstance(new_color, (tuple, list)):
        new_color = color.Color(*new_color)

    mask = pixmap.mask()
    pixmap.fill(new_color)
    pixmap.setMask(mask)

    return pixmap


def overlay_pixmap(pixmap, over_pixmap, overlay_color, align=Qt.AlignCenter):
    """
    Overlays one pixmap over the other
    :param pixmap:
    :param over_pixmap:
    :param overlay_color:
    :param align:
    :return:
    """

    if isinstance(overlay_color, str):
        overlay_color = color.Color.from_string(overlay_color)

    if overlay_color is not None:
        over_pixmap = colorize_pixmap(over_pixmap, overlay_color)

    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

    x = 0
    y = 0
    if align is Qt.AlignCenter:
        x = pixmap.width() / 2 - over_pixmap.width() / 2
        y = pixmap.height() / 2 - over_pixmap.height() / 2
    elif align is None:
        x = 0
        y = 0

    painter.drawPixmap(x, y, over_pixmap.width(), over_pixmap.height(), over_pixmap)
    painter.end()


def tint_pixmap(pixmap, tint_color=(255, 255, 255, 100), composition_mode=QPainter.CompositionMode_Plus):
    """
    Composite one pixmap on top of another
    :param pixmap:
    :param tint_color:
    :param composition_mode:
    :return:
    """

    tint_color = QColor(*tint_color)
    over_pixmap = QPixmap(pixmap.width(), pixmap.height())
    over_pixmap.fill(tint_color)
    over_pixmap.setMask(pixmap.mask())
    painter = QPainter(pixmap)
    painter.setCompositionMode(composition_mode)
    painter.drawPixmap(0, 0, over_pixmap.width(), over_pixmap.height(), over_pixmap)
    painter.end()


def grayscale_pixmap(pixmap):
    """
    Grayscale given pixmap
    :param pixmap:
    :return:
    """

    image = pixmap.toImage()
    alpha = image.alphaChannel()
    gray = image.convertToFormat(QImage.Format_Grayscale8)
    image = gray.convertToFormat(QImage.Format_ARGB32)
    image.setAlphaChannel(alpha)

    return QPixmap(image)


PixmapCache = cache.CacheResource(Pixmap)
