#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base class for icons
"""

from __future__ import print_function, division, absolute_import

import copy

from Qt.QtCore import *
from Qt.QtGui import *

from tpDcc.libs.python import python
from tpDcc.libs.qt.core import color, qtutils, cache, pixmap as px


class Icon(QIcon, object):

    @classmethod
    def state_icon(cls, path, **kwargs):
        """
        Creates a new icon with the given path and states
        :param path: str
        :param kwargs: dict
        :return: Icon
        """

        clr = kwargs.get('color', QColor(0, 0, 0))
        pixmap = px.Pixmap(path)
        pixmap.set_color(clr)

        valid_options = [
            'active',
            'selected',
            'disabled',
            'on',
            'off',
            'on_active',
            'on_selected',
            'on_disabled',
            'off_active',
            'off_selected',
            'off_disabled',
            'color',
            'color_on',
            'color_off',
            'color_active',
            'color_selected',
            'color_disabled',
            'color_on_selected',
            'color_on_active',
            'color_on_disabled',
            'color_off_selected',
            'color_off_active',
            'color_off_disabled',
        ]

        default = {
            "on_active": kwargs.get("active", px.Pixmap(path)),
            "off_active": kwargs.get("active", px.Pixmap(path)),
            "on_disabled": kwargs.get("disabled", px.Pixmap(path)),
            "off_disabled": kwargs.get("disabled", px.Pixmap(path)),
            "on_selected": kwargs.get("selected", px.Pixmap(path)),
            "off_selected": kwargs.get("selected", px.Pixmap(path)),
            "color_on_active": kwargs.get("color_active", clr),
            "color_off_active": kwargs.get("color_active", clr),
            "color_on_disabled": kwargs.get("color_disabled", clr),
            "color_off_disabled": kwargs.get("color_disabled", clr),
            "color_on_selected": kwargs.get("color_selected", clr),
            "color_off_selected": kwargs.get("color_selected", clr),
        }

        default.update(kwargs)
        kwargs = copy.copy(default)

        for option in valid_options:
            if 'color' in option:
                kwargs[option] = kwargs.get(option, clr)
            else:
                svg_path = kwargs.get(option, path)
                kwargs[option] = px.Pixmap(svg_path)

        options = {
            QIcon.On: {
                QIcon.Normal: (kwargs['color_on'], kwargs['on']),
                QIcon.Active: (kwargs['color_on_active'], kwargs['on_active']),
                QIcon.Disabled: (kwargs['color_on_disabled'], kwargs['on_disabled']),
                QIcon.Selected: (kwargs['color_on_selected'], kwargs['on_selected'])
            },

            QIcon.Off: {
                QIcon.Normal: (kwargs['color_off'], kwargs['off']),
                QIcon.Active: (kwargs['color_off_active'], kwargs['off_active']),
                QIcon.Disabled: (kwargs['color_off_disabled'], kwargs['off_disabled']),
                QIcon.Selected: (kwargs['color_off_selected'], kwargs['off_selected'])
            }
        }

        icon = cls(pixmap)

        for state in options:
            for mode in options[state]:
                clr, pixmap = options[state][mode]

                pixmap = px.Pixmap(pixmap)
                pixmap.set_color(clr)

                icon.addPixmap(pixmap, mode, state)

        return icon

    def __init__(self, *args):
        super(Icon, self).__init__(*args)

        self._color = None

    def set_color(self, new_color, size=None):
        """
        Sets icon color
        :param new_color: QColor, new color for the icon
        :param size: QSize, size of the icon
        """

        if isinstance(new_color, str):
            new_color = color.Color.from_string(new_color)

        icon = self
        size = size or icon.availableSizes()[0]
        pixmap = icon.pixmap(size)

        if not self.isNull():
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.setBrush(new_color)
            painter.setPen(new_color)
            painter.drawRect(pixmap.rect())
            painter.end()

        icon = Icon(pixmap)
        self.swap(icon)

    def set_badge(self, x, y, w, h, color=None):
        """
        Set badge for the icon
        :param x: int
        :param y: int
        :param w: int
        :param h: int
        :param color: QColor or None
        """

        color = color or QColor(240, 100, 100)
        size = self.actualSize(QSize(256, 256))
        pixmap = self.pixmap(size)
        painter = QPainter(pixmap)
        pen = QPen(color)
        pen.setWidth(0)
        painter.setPen(pen)
        painter.setBrush(color)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawEllipse(x, y, w, h)
        painter.end()
        icon = Icon(pixmap)
        self.swap(icon)

    def resize(self, size):
        """
        Resize the icon. Defaults to smooth bilinear scaling and keep aspect ratio
        :param QSize size: size to scale to
        """

        icon = resize_icon(self)
        if not icon:
            return

        self.swap(icon)

    def grayscale(self):
        """
        Converts this icon into grayscale
        """

        icon = grayscale_icon(self)
        if not icon:
            return

        self.swap(icon)

    def colorize(self, new_color, overlay_icon=None, overlay_color=(255, 255, 255)):
        """
        Colorizes current icon
        :param new_color:
        :param overlay_icon:
        :param overlay_color:
        :return:
        """

        icon = colorize_icon(icon=self, color=new_color, overlay_icon=overlay_icon, overlay_color=overlay_color)
        if not icon:
            return

        self.swap(icon)


def resize_icon(icon, size):
    """
    Resizes the icon. Defaults to smooth bilinear scaing and keep aspect ratio
    :param QSize size: size to scale to
    """

    if len(icon.availableSizes() == 0):
        return

    orig_size = icon.availableSizes()[0]
    pixmap = icon.pixmap(orig_size)
    pixmap = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    return Icon(pixmap)


def colorize_icon(icon, size=None, color=(255, 255, 255), overlay_icon=None, overlay_color=(255, 255, 255)):
    """
    Colorizes the icon
    :param icon: icon to colorize
    :param size:
    :param color:
    :param overlay_icon:
    :param overlay_color:
    :return:
    """

    size = size or icon.availableSizes()[0]
    size = qtutils.dpi_scale(size)

    orig_size = icon.availableSizes()[0]
    pixmap = px.colorize_pixmap(icon.pixmap(orig_size), color)
    if overlay_icon is not None:
        overlay_pixmap = overlay_icon.pixmap(orig_size)
        px.overlay_pixmap(pixmap, overlay_pixmap, overlay_color)

    pixmap = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    return Icon(pixmap)


def colorize_layered_icon(icons, size, colors=None, icon_scaling=None, tint_color=None,
                          tint_composition=QPainter.CompositionMode_Plus, grayscale=False):
    """
    Layers multiple icons with various colors into one icon
    :param icons:
    :param size:
    :param colors:
    :param icon_scaling:
    :param tint_color:
    :param tint_composition:
    :param grayscale:
    :return:
    """

    if not icons:
        return

    icons = python.force_list(icons)

    if not colors:
        colors = list()
    if not icon_scaling:
        icon_scaling = list()

    default_size = 1
    size = qtutils.dpi_scale(size)

    # Create copies of the lists
    icons = list(icons)
    icon_scaling = list(icon_scaling)
    colors = list(colors)

    if colors is None or (len(icons) > len(colors)):
        colors = colors or list()
        colors += [None] * (len(icons) - len(colors))

    if icon_scaling is None or len(icons) > len(icon_scaling):
        icon_scaling = icon_scaling or list()
        icon_scaling += [default_size] * (len(icons) - len(icon_scaling))

    icon_largest = icons.pop(0)

    orig_size = icon_largest.availableSizes()[0]
    col = colors.pop(0)
    scale = icon_scaling.pop(0)
    if col is not None:
        pixmap = px.colorize_pixmap(icon_largest.pixmap(orig_size * scale), col)
    else:
        pixmap = icon_largest.pixmap(orig_size * scale)

    for i in range(len(icons)):
        overlay_pixmap = icons[i].pixmap(orig_size * icon_scaling[i])
        px.overlay_pixmap(pixmap, overlay_pixmap, colors[i])

    if tint_color is not None:
        px.tint_pixmap(pixmap, tint_color, composition_mode=tint_composition)

    pixmap = pixmap.scaled(QSize(size, size), Qt.KeepAspectRatio, Qt.SmoothTransformation)

    icon = Icon(pixmap)
    if grayscale:
        pixmap = px.grayscale_pixmap(pixmap)
        icon = Icon(pixmap)
        icon.addPixmap(icon.pixmap(size, QIcon.Disabled))   # TODO: Use tint instead

    return icon


def grayscale_icon(icon):
    """
    Returns a grayscale version of the given icon or the original one if it cannot be converted
    :param icon:
    :param size:
    :return:
    """

    for size in icon.availableSizes():
        icon.addPixmap(icon.pixmap(size, QIcon.Disabled))

    return icon


IconCache = cache.CacheResource(Icon)
