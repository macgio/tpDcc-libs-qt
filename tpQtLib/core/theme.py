#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains theme implementation
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpQtLib
from tpQtLib.core import color, style


THEME_PRESETS = [
    {
        "name": "Blue",
        "accentColor": "rgb(50, 180, 240, 255)",
        "backgroundColor": None,
    },
    {
        "name": "Green",
        "accentColor": "rgb(80, 200, 140, 255)",
        "backgroundColor": None,
    },
    {
        "name": "Yellow",
        "accentColor": "rgb(250, 200, 0)",
        "backgroundColor": None,
    },
    {
        "name": "Orange",
        "accentColor": "rgb(255, 170, 0)",
        "backgroundColor": None,
    },
    {
        "name": "Peach",
        "accentColor": "rgb(255, 125, 100)",
        "backgroundColor": None,
    },
    {
        "name": "Red",
        "accentColor": "rgb(230, 60, 60)",
        "backgroundColor": None,
    },
    {
        "name": "Pink",
        "accentColor": "rgb(255, 87, 123)",
        "backgroundColor": None,
    },
    {
        "name": "Purple",
        "accentColor": "rgb(110, 110, 240)",
        "backgroundColor": None,
    },
    {
        "name": "Dark",
        "accentColor": None,
        "backgroundColor": "rgb(60, 64, 79)",
    },
    {
        "name": "Grey",
        "accentColor": None,
        "backgroundColor": "rgb(60, 60, 60)",
    },
    {
        "name": "Light",
        "accentColor": None,
        "backgroundColor": "rgb(245, 245, 255)",
    },
]


class Theme(QObject, object):

    updated = Signal()

    DEFAULT_DARK_COLOR = QColor(60, 60, 60)
    DEFAULT_LIGHT_COLOR = QColor(220, 220, 220)
    DEFAULT_ACCENT_COLOR = QColor(0, 175, 255)
    DEFAULT_BACKGROUND_COLOR = QColor(60, 60, 80)

    def __init__(self):
        super(Theme, self).__init__()

        self._name = 'Default'
        self._dpi = 1
        self._accent_color = None
        self._background_color = None

        self.set_accent_color(self.DEFAULT_ACCENT_COLOR)
        self.set_background_color(self.DEFAULT_BACKGROUND_COLOR)

    def name(self):
        """
        Returns the name for this theme
        :return: str
        """

        return self._name

    def set_name(self, name):
        """
        Sets the name for this theme
        :param name: str
        """

        self._name = name

    def dpi(self):
        """
        Returns zoom amount for this theme
        :return: float
        """

        return self._dpi

    def set_dpi(self, dpi):
        """
        Sets the zoom amount for this theme
        :param dpi: float
        """

        self._dpi = dpi

    def is_dark(self):
        """
        Returns whether the current theme is dark or not
        :return: bool
        """

        red = self.background_color().redF() * 0.299
        green = self.background_color().greenF() * 0.587
        blue = self.background_color().blueF() * 0.114

        darkness = red + green + blue
        if darkness < 0.6:
            return True

        return False

    def set_dark(self):
        """
        Sets the current theme to the default dark color
        """

        self.set_background_color(self.DEFAULT_DARK_COLOR)

    def set_light(self):
        """
        Sets the current theme to the default light color
        """

        self.set_background_color(self.DEFAULT_LIGHT_COLOR)

    def background_color(self):
        """
        Returns the background color for this theme
        :return: color.Color
        """

        return self._background_color

    def set_background_color(self, background_color):
        """
        Sets the background color for this theme
        :param background_color: variant, str or QColor or color.Color
        """

        if isinstance(background_color, (str, unicode)):
            background_color = color.Color.from_string(background_color)
        elif isinstance(background_color, QColor):
            background_color = color.Color.from_color(background_color)
        self._background_color = background_color
        self.updated.emit()

    def foreground_color(self):
        """
        Returns the foreground color for this theme
        :return: color.Color
        """

        if self.is_dark():
            return color.Color(250, 250, 250, 255)
        else:
            return color.Color(0, 40, 80, 180)

    def accent_color(self):
        """
        Returns the accent color for this theme
        :return: color.Color
        """

        return self._accent_color

    def set_accent_color(self, accent_color):
        """
        Sets the accent color for this theme
        :param accent_color: variant, str or QColor or color.Color
        """

        if isinstance(accent_color, (str, unicode)):
            accent_color = color.Color.from_string(accent_color)
        elif isinstance(accent_color, QColor):
            accent_color = color.Color.from_color(accent_color)
        self._accent_color = accent_color
        self.updated.emit()

    def icon_color(self):
        """
        Returns the icon color for this theme
        :return: color.Color
        """

        return self.foreground_color()

    def accent_foreground_color(self):
        """
        Returns the foregound color for the accent color
        """

        return color.Color(255, 255, 255, 255)

    def item_background_color(self):
        """
        Returns the item background color
        :return: color.Color
        """

        if self.is_dark():
            return color.Color(255, 255, 255, 20)
        else:
            return color.Color(255 ,255, 255, 120)

    def item_background_hover_color(self):
        """
        Returns the item background color when the mouse hovers over the item
        :return: color.Color
        """

        return color.Color(255, 255, 255, 60)

    def settings(self):
        """
        Returns a dictionary of settings for the current theme
        :return: dict
        """

        return {
            'name': self.name(),
            'accentColor': self.accent_color().to_string(),
            'backgroundColor': self.background_color().to_string()
        }

    def set_settings(self, settings):
        """
        Sets a dictionary of settings for the current theme
        :param settings: dict
        """

        name = settings.get('name')
        self.set_name(name)

        accent_color = settings.get('accentColor')
        if accent_color:
            accent_color = color.Color.from_string(accent_color)
            self.set_accent_color(accent_color)

        background_color = settings.get('backgroundColor')
        if background_color:
            background_color = color.Color.from_string(background_color)
            self.set_background_color(background_color)

    def options(self):
        """
        Returns the variables used to customize the style sheet
        :return: dict
        """

        accent_color = self.accent_color()
        accent_foreground_color = self.accent_foreground_color()
        foreground_color = self.foreground_color()
        background_color = self.background_color()
        item_background_color = self.item_background_color()
        item_background_hover_color = self.item_background_hover_color()

        if self.is_dark():
            darkness = 'white'
        else:
            darkness = 'black'

        resource_dirname = tpQtLib.resource().dirname.replace('\\', '/')

        options = {
            "DARKNESS": darkness,
            "RESOURCE_DIRNAME": resource_dirname,

            "ACCENT_COLOR": accent_color.to_string(),
            "ACCENT_COLOR_DARKER": color.Color(accent_color.darker(150)).to_string(),
            "ACCENT_COLOR_LIGHTER": color.Color(accent_color.lighter(150)).to_string(),
            "ACCENT_COLOR_R": str(accent_color.red()),
            "ACCENT_COLOR_G": str(accent_color.green()),
            "ACCENT_COLOR_B": str(accent_color.blue()),

            "ACCENT_FOREGROUND_COLOR": accent_foreground_color.to_string(),
            "ACCENT_FOREGROUND_COLOR_DARKER": color.Color(accent_foreground_color.darker(150)).to_string(),

            "FOREGROUND_COLOR": foreground_color.to_string(),
            "FOREGROUND_COLOR_R": str(foreground_color.red()),
            "FOREGROUND_COLOR_G": str(foreground_color.green()),
            "FOREGROUND_COLOR_B": str(foreground_color.blue()),

            "BACKGROUND_COLOR": background_color.to_string(),
            "BACKGROUND_COLOR_LIGHTER": color.Color(background_color.lighter(150)).to_string(),
            "BACKGROUND_COLOR_DARKER": color.Color(background_color.darker(150)).to_string(),
            "BACKGROUND_COLOR_R": str(background_color.red()),
            "BACKGROUND_COLOR_G": str(background_color.green()),
            "BACKGROUND_COLOR_B": str(background_color.blue()),

            "ITEM_TEXT_COLOR": foreground_color.to_string(),
            "ITEM_TEXT_SELECTED_COLOR": accent_foreground_color.to_string(),

            "ITEM_BACKGROUND_COLOR": item_background_color.to_string(),
            "ITEM_BACKGROUND_HOVER_COLOR": item_background_hover_color.to_string(),
            "ITEM_BACKGROUND_SELECTED_COLOR": accent_color.to_string(),
        }

        return options

    def stylesheet(self):
        """
        Returns the style sheet for this theme
        :return: str
        """

        options = self.options()
        path = tpQtLib.resource.get('styles', 'default.css')
        stylesheet = style.StyleSheet.from_path(path, options=options, dpi=self.dpi())

        return stylesheet.data()

    def create_color_dialog(self, parent, standard_colors=None, current_color=None):
        """
        Creates a new instance of color dialog
        :param parent: QWidget
        :param standard_colors: list(int)
        :param current_color: QColor
        :return: QColorDialog
        """

        dlg = QColorDialog(parent)
        if standard_colors:
            index = -1
            for r, g, b in standard_colors:
                index += 1
                clr = QColor(r, g, b).rgba()
                try:
                    clr = QColor(clr)
                    dlg.setStandardColor(index, clr)
                except Exception:
                    clr = QColor(clr).rgba()
                    dlg.setStandardColor(index, clr)

        # PySide2 does not supports d.open(), we pass a blank slot
        dlg.open(self, Slot('blankSlot()'))

        if current_color:
            dlg.setCurrentColor(current_color)

        return dlg

    def browse_accent_color(self, parent=None):
        """
        Shows the color dialog for changing the accent color
        :param parent: QWidget
        """

        standard_colors = [
            (230, 60, 60), (210, 40, 40), (190, 20, 20), (250, 80, 130),
            (230, 60, 110), (210, 40, 90), (255, 90, 40), (235, 70, 20),
            (215, 50, 0), (240, 100, 170), (220, 80, 150), (200, 60, 130),
            (255, 125, 100), (235, 105, 80), (215, 85, 60), (240, 200, 150),
            (220, 180, 130), (200, 160, 110), (250, 200, 0), (230, 180, 0),
            (210, 160, 0), (225, 200, 40), (205, 180, 20), (185, 160, 0),
            (80, 200, 140), (60, 180, 120), (40, 160, 100), (80, 225, 120),
            (60, 205, 100), (40, 185, 80), (50, 180, 240), (30, 160, 220),
            (10, 140, 200), (100, 200, 245), (80, 180, 225), (60, 160, 205),
            (130, 110, 240), (110, 90, 220), (90, 70, 200), (180, 160, 255),
            (160, 140, 235), (140, 120, 215), (180, 110, 240), (160, 90, 220),
            (140, 70, 200), (210, 110, 255), (190, 90, 235), (170, 70, 215)
        ]

        current_color = self.accent_color()

        dialog = self.create_color_dialog(parent, standard_colors, current_color)
        dialog.currentColorChanged.connect(self.set_accent_color)

        if dialog.exec_():
            self.set_accent_color(dialog.selectedColor())
        else:
            self.set_accent_color(current_color)

    def browse_background_color(self, parent=None):
        """
        Shows the color dialog for changing the background color
        :param parent: QWidget
        """

        standard_colors = [
            (0, 0, 0), (20, 20, 20), (40, 40, 40), (60, 60, 60),
            (80, 80, 80), (100, 100, 100), (20, 20, 30), (40, 40, 50),
            (60, 60, 70), (80, 80, 90), (100, 100, 110), (120, 120, 130),
            (0, 30, 60), (20, 50, 80), (40, 70, 100), (60, 90, 120),
            (80, 110, 140), (100, 130, 160), (0, 60, 60), (20, 80, 80),
            (40, 100, 100), (60, 120, 120), (80, 140, 140), (100, 160, 160),
            (0, 60, 30), (20, 80, 50), (40, 100, 70), (60, 120, 90),
            (80, 140, 110), (100, 160, 130), (60, 0, 10), (80, 20, 30),
            (100, 40, 50), (120, 60, 70), (140, 80, 90), (160, 100, 110),
            (60, 0, 40), (80, 20, 60), (100, 40, 80), (120, 60, 100),
            (140, 80, 120), (160, 100, 140), (40, 15, 5), (60, 35, 25),
            (80, 55, 45), (100, 75, 65), (120, 95, 85), (140, 115, 105)
        ]

        current_color = self.background_color()

        dialog = self.create_color_dialog(parent, standard_colors, current_color)
        dialog.currentColorChanged.connect(self.set_background_color)

        if dialog.exec_():
            self.set_background_color(dialog.selectedColor())
        else:
            self.set_background_color(current_color)


def theme_presets():
    """
    Returns the default theme presets.
    :return: list(str)
    """

    themes = list()

    for data in THEME_PRESETS:
        theme = Theme()
        theme.set_name(data.get("name"))
        theme.set_accent_color(data.get("accentColor"))
        theme.set_background_color(data.get("backgroundColor"))

        themes.append(theme)

    return themes
