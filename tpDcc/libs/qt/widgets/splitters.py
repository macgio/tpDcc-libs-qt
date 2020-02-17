#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt splitter widgets
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *


class Splitter(QWidget, object):
    def __init__(self, text=None, shadow=False, color=(150, 150, 150)):
        """
        Basic standard splitter with optional text
        :param str text: Optional text to include as title in the splitter
        :param bool shadow: True if you want a shadow above the splitter
        :param tuple(int) color: Color of the slitter's text
        """

        super(Splitter, self).__init__()

        self.setMinimumHeight(10)
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.layout().setAlignment(Qt.AlignVCenter)

        first_line = QFrame()
        first_line.setMaximumHeight(1)
        first_line.setFrameStyle(QFrame.HLine)
        self.layout().addWidget(first_line)

        main_color = 'rgba(%s, %s, %s, 255)' % color
        shadow_color = 'rgba(45, 45, 45, 255)'

        bottom_border = ''
        if shadow:
            bottom_border = 'border-bottom:1px solid %s;' % shadow_color

        style_sheet = "border:0px solid rgba(0,0,0,0); \
                      background-color: %s; \
                      line-height: 1px; \
                      %s" % (main_color, bottom_border)

        first_line.setStyleSheet(style_sheet)

        if text is None:
            self.setMinimumHeight(2)
            return

        first_line.setMaximumWidth(5)

        font = QFont()
        font.setBold(True)

        self._text_width = QFontMetrics(font)
        width = self._text_width.width(text) + 6

        self._label = QLabel()
        self._label.setText(text)
        self._label.setFont(font)
        self._label.setMaximumWidth(width)
        self._label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.layout().addWidget(self._label)

        second_line = QFrame()
        second_line.setMaximumHeight(1)
        second_line.setFrameStyle(QFrame.HLine)
        second_line.setStyleSheet(style_sheet)

        self.layout().addWidget(second_line)

    def set_text(self, text):
        self._label.setText(text)
        width = self._text_width.width(text) + 6
        self._label.setMaximumWidth(width)


class SplitterLayout(QHBoxLayout, object):
    """
    Basic splitter to separate layouts
    """

    def __init__(self):
        super(SplitterLayout, self).__init__()

        self.setContentsMargins(40, 2, 40, 2)

        splitter = Splitter(shadow=False, color=(60, 60, 60))
        splitter.setFixedHeight(2)

        self.addWidget(splitter)


def get_horizontal_separator_widget(max_height=30):

    v_div_w = QWidget()
    v_div_l = QVBoxLayout()
    v_div_l.setAlignment(Qt.AlignLeft)
    v_div_l.setContentsMargins(5, 5, 5, 5)
    v_div_l.setSpacing(0)
    v_div_w.setLayout(v_div_l)
    v_div = QFrame()
    v_div.setMaximumHeight(max_height)
    v_div.setFrameShape(QFrame.VLine)
    v_div.setFrameShadow(QFrame.Sunken)
    v_div_l.addWidget(v_div)
    return v_div_w
