#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that defines that extends QColor functionality
"""

from __future__ import print_function, division, absolute_import

from tpQtLib.Qt.QtWidgets import *
from tpQtLib.Qt.QtGui import *

from tpQtLib.core import dialog


class Color(QColor, object):
    def __eq__(self, other):
        if other == self:
            return True
        elif isinstance(other, Color):
            return self.to_string() == other.to_string()
        else:
            return False

    @classmethod
    def from_color(cls, color):
        """
        Gets a string formateed color from a QColor
        :param color: QColor, color to parse
        :return: (str)
        """

        color = ('rgb(%d, %d, %d, %d)' % color.getRgb())
        return cls.from_string(color)

    @classmethod
    def from_string(cls, text_color):
        """
        Returns a (int, int, int, int) format color from a string format color
        :param text_color: str, string format color to parse
        :return: (int, int, int, int)
        """

        a = 255
        try:
            r, g, b, a = text_color.replace('rgb(', '').replace(')', '').split(',')
        except ValueError:
            r, g, b = text_color.replace('rgb(', '').replace(')', '').split(',')

        return cls(int(r), int(g), int(b), int(a))

    def to_string(self):
        """
        Returns the color with string format
        :return: str
        """

        return 'rgb(%d, %d, %d, %d)' % self.getRgb()

    def is_dark(self):
        """
        Return True if the color is considered dark (RGB < 125(mid grey)) or False otherwise
        :return: bool
        """

        return self.red() < 125 and self.green() < 125 and self.blue() < 125


class ColorSwatch(QToolButton, object):
    def __init__(self, parent=None, **kwargs):
        super(ColorSwatch, self).__init__(parent=parent)

        self.normalized = kwargs.get('normalized', True)
        self.color = kwargs.get('color', [1.0, 1.0, 1.0])
        self.qcolor = QColor()
        self.index_color = None
        self.set_color(self.color)

        self.clicked.connect(self._on_open_color_picker)

    # region Public Functions
    def set_color(self, color):
        """
        Sets an RGB color value
        :param color: list, list of RGB values
        """

        if type(color) is QColor:
            return color

        # if type(color[0]) is float:
        self.qcolor.setRgb(*color)
        # self.setToolTip("%.2f, %.2f, %.2f" % (color[0], color[1], color[2]))
        # else:
        #     self.qcolor.setRgb(*color)
        self.setToolTip("%d, %d, %d" % (color[0], color[1], color[2]))
        self._update()

        return self.color

    def get_color(self):
        """
        Returns the current color RGB values
        :return: list<int, int, int>, RGB color values
        """

        return self.color

    def get_rgb(self, normalized=True):
        """
        Returns a tuple of RGB values
        :param normalized:  bool, True if you want to get a normalized color, False otherwise
        :return: tuple, RGB color values
        """

        if not normalized:
            return self.qcolor.toRgb().red(), self.qcolor.toRgb().green(), self.qcolor.toRgb().blue()
        else:
            return self.qcolor.toRgb().redF(), self.qcolor.toRgb().greenF(), self.qcolor.toRgb().blueF()
    # endregion

    # region Private Functions
    def _update(self):
        """
        Updates the widget color
        """

        self.color = self.qcolor.getRgb()[0:3]
        self.setStyleSheet(
            """
            QToolButton
            {
                background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgb(%d, %d, %d), stop:1 rgb(%d, %d, %d))
            };
            """ % (self.color[0]*.45, self.color[1]*.45, self.color[2]*.45, self.color[0], self.color[1], self.color[2])
        )

    def _get_hsvF(self):
        return self.qcolor.getHsvF()

    def _set_hsvF(self, color):
        """
        Set the current color (HSV - normalized)
        :param color: tuple<int, int, int>, tuple  of HSV values
        """

        self.qcolor.setHsvF(color[0], color[1], color[2], 255)

    def _get_hsv(self):
        return self.qcolor.getHsv()

    def _set_hsv(self, color):
        """
        Sets teh current color (HSV)
        :param color: tuple<int, int, int, Tuple of HSV values (normalized)
        """

        self.qcolor.setHsv(color[0], color[1], color[2], 255)

    def _on_open_color_picker(self):

        # THIS ONLY WORKS ON MAYA

        color_picker = dialog.ColorDialog()
        color_picker.exec_()
        if color_picker.color is None:
          return

        if type(color_picker.color) == int:
            clr = dialog.ColorDialog.maya_colors[color_picker.color]
            self.index_color = color_picker.color
            self.set_color((clr[0] * 255, clr[1] * 255, clr[2] * 255))
