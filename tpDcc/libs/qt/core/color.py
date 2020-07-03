#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that defines that extends QColor functionality
"""

from __future__ import print_function, division, absolute_import

import math
import random

from Qt.QtCore import *
from Qt.QtGui import *

from tpDcc.libs.python import python, mathlib

_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x + y for x in _NUMERALS for y in _NUMERALS)}

# TODO: Change by enum
_LOWERCASE, _UPPERCASE = 'x', 'X'

REGEX_QCOLOR = r"^(?:(?:#[A-Fa-f0-9]{3})|(?:#[A-Fa-f0-9]{6})|(?:[a-zA-Z]+))$"
REGEX_FN_RGB = r"(^rgb\s*\(\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*\)$)"
REGEX_HEX_RGBA = r"^#[A-Fa-f0-9]{8}$"
REGEX_FN_RGBA = r"(^rgba?\s*\(\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*\)$)"


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
        Gets a string formatted color from a QColor
        :param color: QColor, color to parse
        :return: (str)
        """

        color = ('rgba(%d, %d, %d, %d)' % color.getRgb())
        return cls.from_string(color)

    @classmethod
    def from_string(cls, text_color):
        """
        Returns a (int, int, int, int) format color from a string format color
        :param text_color: str, string format color to parse
        :param alpha: int, alpha of the color
        :return: (int, int, int, int)
        """

        a = 255
        if string_is_hex(text_color):
            r, g, b = cls.rgb_from_hex(text_color)
        else:
            try:
                if text_color.startswith('rgba'):
                    r, g, b, a = text_color.replace('rgba(', '').replace(')', '').split(',')
                else:
                    r, g, b, a = text_color.replace('rgb(', '').replace(')', '').split(',')
            except ValueError:
                if text_color.startswith('rgba'):
                    r, g, b = text_color.replace('rgba(', '').replace(')', '').split(',')
                else:
                    r, g, b = text_color.replace('rgb(', '').replace(')', '').split(',')

        return cls(int(r), int(g), int(b), int(a))

    @classmethod
    def rgb_from_hex(cls, triplet):
        """
        Returns a RGB triplet from an hexadecimal value
        :param triplet: r,g,b Hexadecimal Color tuple
        """

        if triplet.startswith('#'):
            triplet = triplet[1:]

        if len(triplet) == 3:
            r, g, b = triplet[0] * 2, triplet[1] * 2, triplet[2] * 2
            return tuple([float(int(v, 16)) for v in (r, g, b)])

        return _HEXDEC[triplet[0:2]], _HEXDEC[triplet[2:4]], _HEXDEC[triplet[4:6]]

    @classmethod
    def hex_from_rgb(cls, rgb, lettercase=_LOWERCASE):
        """
        Returns a hexadecimal value from a triplet
        :param rgb: tuple(r,g,b) RGB Color tuple
        :param lettercase: LOWERCASE if you want to get a lowercase or UPPERCASE
        """

        return format(rgb[0] << 16 | rgb[1] << 8 | rgb[2], '06' + lettercase)

    @classmethod
    def rgb_to_hex(cls, rgb):
        """
        Returns RGB color from hexadecimal
        :param rgb:
        :return: str
        """

        return '#%02x%02x%02x' % rgb

    @classmethod
    def get_random_hex(cls, return_sign=True):
        """
        Returns a random HEX value
        :param return_sign: bool, True if you want to get color sign
        :return: str
        """

        def _random_int():
            return random.randint(0, 255)

        if return_sign:
            return '#%02X%02X%02X' % (_random_int(), _random_int(), _random_int())
        else:
            return '%02X%02X%02X' % (_random_int(), _random_int(), _random_int())

    @classmethod
    def get_random_rgb(cls):
        """
        Returns a random RGB color
        """

        hex = cls.get_random_hex(return_sign=False)
        return cls.rgb_from_hex(hex)

    @classmethod
    def hex_to_qcolor(cls, hex_color):

        """
        Converts a Hexadecimal color to QColor
        """

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return QColor(r, g, b)

    @classmethod
    def get_complementary_color(cls, color):

        """
        Returns the complementary color of the given color
        :param color: QColor
        """

        hsl_hue = color.hslHueF()
        hsl_saturation = color.hslSaturationF()
        lightness = color.lightnessF()
        lightness = 1.0 - lightness
        hsl_hue += 0.5
        if hsl_hue >= 1.0:
            hsl_hue -= 1.0
        return cls.fromHslF(hsl_hue, hsl_saturation, lightness)

    @classmethod
    def get_option_color(cls, option):
        """
        Returns QColor depending of the option passed as argument
        :param option: str, Option to get color
        """

        if option == 'Grey':
            color = cls.fromRgbF(0.4, 0.4, 0.4)
        elif option == 'Cancel':
            color = cls.fromRgbF(0.7, 0.5, 0.4)
        elif option == 'OK' or option == 'ok':
            color = cls.fromRgbF(0.5, 0.7, 0.8)
        elif option == 'Warning' or option == 'Warn':
            color = cls.fromRgbF(0.7, 0.2, 0.2)
        elif option == 'Collapse':
            color = cls.fromRgbF(0.15, 0.15, 0.15)
        elif option == 'Subtle':
            color = cls.fromRgbF(0.48, 0.48, 0.6)
        else:
            color = cls.fromRgbF(0.48, 0.48, 0.6)
        if option:
            color.ann = option + ' Color'
        return color

    @classmethod
    def expand_normalized_rgb(cls, normalized_rgb):
        return tuple([float(normalized_rgb[0]) * 255, float(normalized_rgb[1]) * 255, float(normalized_rgb[2]) * 255])

    @classmethod
    def normalized_rgb(cls, rgb):
        return tuple([float(rgb[0]) / 255, float(rgb[1]) / 255, float(rgb[2]) / 255])

    def to_string(self):
        """
        Returns the color with string format
        :return: str
        """

        return 'rgba(%d, %d, %d, %d)' % self.getRgb()

    def is_dark(self):
        """
        Return True if the color is considered dark (RGB < 125(mid grey)) or False otherwise
        :return: bool
        """

        return self.red() < 125 and self.green() < 125 and self.blue() < 125


# =================================================================================================================

DEFAULT_DARK_COLOR = Color(50, 50, 50, 255)
DEFAULT_LIGHT_COLOR = Color(180, 180, 180, 255)
BLACK = Color(0, 0, 0, 255)
GRAY = Color(110, 110, 110, 255)
RED = Color(255, 0, 0, 255)
GREEN = Color(0, 255, 0, 255)
BLUE = Color(0, 0, 255, 255)
YELLOW = Color(255, 255, 0, 255)
ORANGE = Color(209, 84, 0, 255)
MAGENTA = Color(1.0, 0.0, 1.0)
CYAN = Color(0.0, 1.0, 1.0)
WHITE = Color(1.0, 1.0, 1.0)
DARK_GRAY = Color(60, 60, 60, 255)
DARK_RED = Color(0.75, 0.0, 0.0)
DARK_GREEN = Color(0.0, 0.75, 0.0)
DARK_BLUE = Color(0.0, 0.0, 0.75)
DARK_YELLOW = Color(0.75, 0.75, 0.0)
DARK_MAGENTA = Color(0.75, 0.0, 0.75)
DARK_CYAN = Color(0.0, 0.75, 0.75)
LIGHT_GRAY = Color(0.75, 0.75, 0.75)
LIGHT_RED = Color(1.0, 0.25, 0.25)
LIGHT_GREEN = Color(0.25, 1.0, 0.25)
LIGHT_BLUE = Color(0.25, 0.25, 1.0)
LIGHT_YELLOW = Color(1.0, 1.0, 0.25)
LIGHT_MAGENTA = Color(1.0, 0.25, 1.0)
LIGHT_CYAN = Color(0.25, 1.0, 1.0)

# =================================================================================================================


def string_is_hex(color_str):
    """
    Returns whether or not given string is a valid hexadecimal color
    :param color_str: str
    :return: bool
    """

    if color_str.startswith('#'):
        color_str = color_str[1:]
    hex_regex1 = QRegExp('^[0-9A-F]{3}$', Qt.CaseInsensitive)
    hex_regex2 = QRegExp('^[0-9A-F]{6}$', Qt.CaseInsensitive)
    hex_regex3 = QRegExp('^[0-9A-F]{8}$', Qt.CaseInsensitive)
    if hex_regex1.exactMatch(color_str) or hex_regex2.exactMatch(color_str) or hex_regex3.exactMatch(color_str):
        return True

    return False


def convert_2_hex(color):
    """
    Converts given color to hexadecimal value
    :param color:
    :return: str
    """

    if python.is_string(color) and string_is_hex(color):
        return color

    hex = '#'
    for var in color:
        var = format(var, 'x')
        if len(var) == 1:
            hex += '0' + str(var)
        else:
            hex += str(var)

    if len(hex) == 9:
        hex = '#{}{}'.format(hex[-2:], hex[1:-2])

    return hex


def generate_color(primary_color, index):
    """
    Generates a new color from the given one and with given index (between 1 and 10)
    https://github.com/phenom-films/dayu_widgets/blob/master/dayu_widgets/utils.py
    :param primary_color: base color (RRGGBB)
    :param index: color step from 1 (light) to 10 (dark)
    :return: out color Color
    """

    hue_step = 2
    saturation_step = 16
    saturation_step2 = 5
    brightness_step1 = 5
    brightness_step2 = 15
    light_color_count = 5
    dark_color_count = 4

    def _get_hue(color, i, is_light):
        h_comp = color.hue()
        if 60 <= h_comp <= 240:
            hue = h_comp - hue_step * i if is_light else h_comp + hue_step * i
        else:
            hue = h_comp + hue_step * i if is_light else h_comp - hue_step * i
        if hue < 0:
            hue += 359
        elif hue >= 359:
            hue -= 359
        return hue / 359.0

    def _get_saturation(color, i, is_light):
        s_comp = color.saturationF() * 100
        if is_light:
            saturation = s_comp - saturation_step * i
        elif i == dark_color_count:
            saturation = s_comp + saturation_step
        else:
            saturation = s_comp + saturation_step2 * i
        saturation = min(100.0, saturation)
        if is_light and i == light_color_count and saturation > 10:
            saturation = 10
        saturation = max(6.0, saturation)
        return round(saturation * 10) / 1000.0

    def _get_value(color, i, is_light):
        v_comp = color.valueF()
        if is_light:
            return min((v_comp * 100 + brightness_step1 * i) / 100, 1.0)
        return max((v_comp * 100 - brightness_step2 * i) / 100, 0.0)

    light = index <= 6
    hsv_color = Color(primary_color) if python.is_string(primary_color) else primary_color
    index = light_color_count + 1 - index if light else index - light_color_count - 1

    return Color.fromHsvF(
        _get_hue(hsv_color, index, light),
        _get_saturation(hsv_color, index, light),
        _get_value(hsv_color, index, light)
    ).name()


def string_from_color(color, alpha):
    if not alpha or color.alpha() == 255:
        return color.name()
    return color.name() + '{}'.format(color.alpha())
    # color.name()+QStringLiteral("%1").arg(color.alpha(), 2, 16, QChar('0'));


def color_from_string(string, alpha):
    xs = string.strip()
    regex = QRegExp(REGEX_QCOLOR)
    match = regex.exactMatch(xs)
    if match:
        return QColor(xs)

    regex = QRegExp(REGEX_FN_RGB)
    match = regex.exactMatch(xs)
    if match:
        captured_texts = regex.capturedTexts()
        return QColor(int(captured_texts[-3]), int(captured_texts[-2]), int(captured_texts[-1]))

    if alpha:
        regex = QRegExp(REGEX_HEX_RGBA)
        match = regex.exactMatch(xs)
        if match:
            return QColor(_HEXDEC[xs[1:3]], _HEXDEC[xs[3:5]], _HEXDEC[xs[5:7]], _HEXDEC[xs[7:9]])

        regex = QRegExp(REGEX_FN_RGBA)
        match = regex.exactMatch(xs)
        if match:
            captured_texts = regex.capturedTexts()
            return QColor(
                int(captured_texts[-4]), int(captured_texts[-3]), int(captured_texts[-2]), int(captured_texts[-1]))

    return QColor()


def color_chroma_float(color):
    max_value = max(color.redF(), max(color.greenF(), color.blueF()))
    min_value = min(color.redF(), min(color.greenF(), color.blueF()))

    return max_value - min_value


def color_luma_float(color):
    return 0.30 * color.redF() + 0.59 * color.greenF() + 0.11 * color.blueF()


def color_from_lch(hue, chroma, luma, alpha=1):
    h1 = hue * 6
    x = chroma * (1 - abs(math.fmod(h1, 2) - 1))
    col = QColor()
    if 0 <= h1 < 1:
        col = QColor.fromRgbF(chroma, x, 0)
    elif h1 < 2:
        col = QColor.fromRgbF(x, chroma, 0)
    elif h1 < 3:
        col = QColor.fromRgbF(0, chroma, x)
    elif h1 < 4:
        col = QColor.fromRgbF(0, x, chroma)
    elif h1 < 5:
        col = QColor.fromRgbF(x, 0, chroma)
    elif h1 < 6:
        col = QColor.fromRgbF(chroma, 0, x)

    m = luma - color_luma_float(col)

    return QColor.fromRgbF(
        mathlib.clamp(col.redF() + m, 0.0, 1.0),
        mathlib.clamp(col.greenF() + m, 0.0, 1.0),
        mathlib.clamp(col.blueF() + m, 0.0, 1.0),
        alpha
    )


def rainbow_lch(hue):
    return color_from_lch(hue, 1, 1)


def rainbow_hsv(hue):
    return QColor.fromHsvF(hue, 1, 1)


def color_lightnes_float(color):
    return (max(color.redF(), max(
        color.greenF(), color.blueF())) + min(color.redF(), min(color.greenF(), color.blueF()))) / 2


def color_hsl_saturation_float(color):
    chroma_value = color_chroma_float(color)
    lightness_value = color_lightnes_float(color)
    if qFuzzyCompare(lightness_value + 1, 1) or qFuzzyCompare(lightness_value + 1, 2):
        return 0

    return chroma_value / (1 - abs(2 * lightness_value - 1))


def color_from_hsl(hue, sat, lig, alpha):
    chroma = (1 - abs(2 * lig - 1)) * sat
    h1 = hue * 6
    x = chroma * (1 - abs(math.fmod(h1, 2) - 1))
    col = QColor()
    if 0 <= h1 < 1:
        col = QColor.fromRgbF(chroma, x, 0)
    elif h1 < 2:
        col = QColor.fromRgbF(x, chroma, 0)
    elif h1 < 3:
        col = QColor.fromRgbF(0, chroma, x)
    elif h1 < 4:
        col = QColor.fromRgbF(0, x, chroma)
    elif h1 < 5:
        col = QColor.fromRgbF(x, 0, chroma)
    elif h1 < 6:
        col = QColor.fromRgbF(chroma, 0, x)

    m = lig - chroma / 2

    return QColor.fromRgbF(
        mathlib.clamp(col.redF() + m, 0.0, 1.0),
        mathlib.clamp(col.greenF() + m, 0.0, 1.0),
        mathlib.clamp(col.blueF() + m, 0.0, 1.0),
        alpha
    )
