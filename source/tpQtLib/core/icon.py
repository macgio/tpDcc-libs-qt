#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base class for icons
"""

from __future__ import print_function, division, absolute_import

import copy

from Qt.QtCore import *
from Qt.QtGui import *

from tpQtLib.core import color, pixmap as px


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
        size = size or icon.actualSize(QSize(256, 256))
        pixmap = icon.pixmap(size)

        if not self.isNull():
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.setBrush(new_color)
            painter.setPen(new_color)
            painter.drawRect(pixmap.rect())
            painter.end()

        icon = QIcon(pixmap)
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
        icon = QIcon(pixmap)
        self.swap(icon)
