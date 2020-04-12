#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt splitter widgets
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpDcc.libs.qt.widgets import label


class Divider(QWidget, object):

    _ALIGN_MAP = {
        Qt.AlignCenter: 50,
        Qt.AlignLeft: 20,
        Qt.AlignRight: 80
    }

    def __init__(self, text=None, shadow=True, color=(150, 150, 150),
                 orientation=Qt.Horizontal, alignment=Qt.AlignLeft, parent=None):
        """
        Basic standard splitter with optional text
        :param str text: Optional text to include as title in the splitter
        :param bool shadow: True if you want a shadow above the splitter
        :param tuple(int) color: Color of the slitter's text
        :param Qt.Orientation orientation: Orientation of the splitter
        :param Qt.Align alignment: Alignment of the splitter
        :param QWidget parent: Parent of the splitter
        """

        super(Divider, self).__init__(parent=parent)

        self._orient = orientation
        self._text = None

        main_color = 'rgba(%s, %s, %s, 255)' % color
        shadow_color = 'rgba(45, 45, 45, 255)'

        # bottom_border = ''
        # if shadow:
        #     bottom_border = 'border-bottom:1px solid %s;' % shadow_color
        #
        # style_sheet = "border:0px solid rgba(0,0,0,0); \
        #                  background-color: %s; \
        #                  line-height: 1px; \
        #                  %s" % (main_color, bottom_border)

        font = QFont()
        if shadow:
            font.setBold(True)
        self._text_width = QFontMetrics(font)
        width = self._text_width.width(text) + 6

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self._label = label.BaseLabel().secondary()
        # self._label.setFont(font)
        # self._label.setMaximumWidth(width)

        first_line = QFrame()
        self._second_line = QFrame()
        # first_line.setStyleSheet(style_sheet)
        # self._second_line.setStyleSheet(style_sheet)

        main_layout.addWidget(first_line)
        main_layout.addWidget(self._label)
        main_layout.addWidget(self._second_line)

        if orientation == Qt.Horizontal:
            first_line.setFrameShape(QFrame.HLine)
            first_line.setFrameShadow(QFrame.Sunken)
            first_line.setFixedHeight(2) if shadow else first_line.setFixedHeight(1)
            self._second_line.setFrameShape(QFrame.HLine)
            self._second_line.setFrameShadow(QFrame.Sunken)
            self._second_line.setFixedHeight(2) if shadow else self._second_line.setFixedHeight(1)
        else:
            self._label.setVisible(False)
            self._second_line.setVisible(False)
            first_line.setFrameShape(QFrame.VLine)
            first_line.setFrameShadow(QFrame.Plain)
            self.setFixedWidth(2)
            first_line.setFixedWidth(2) if shadow else first_line.setFixedWidth(1)

        main_layout.setStretchFactor(first_line, self._ALIGN_MAP.get(alignment, 50))
        main_layout.setStretchFactor(self._second_line, 100 - self._ALIGN_MAP.get(alignment, 50))

        self.set_text(text)

    @classmethod
    def left(cls, text=''):
        """
        Creates an horizontal splitter with text at left
        :param text:
        :return:
        """

        return cls(text, alignment=Qt.AlignLeft)

    @classmethod
    def right(cls, text=''):
        """
        Creates an horizontal splitter with text at right
        :param text:
        :return:
        """

        return cls(text, alignment=Qt.AlignRight)

    @classmethod
    def center(cls, text=''):
        """
        Creates an horizontal splitter with text at center
        :param text:
        :return:
        """

        return cls(text, alignment=Qt.AlignCenter)

    @classmethod
    def vertical(cls):
        """
        Creates a vertical splitter
        :return:
        """

        return cls(orientation=Qt.Vertical)

    def get_text(self):
        """
        Returns splitter text
        :return: str
        """

        return self._label.text()

    def set_text(self, text):
        """
        Sets splitter text
        :param str text:
        """

        self._text = text
        self._label.setText(text)
        if self._orient == Qt.Horizontal:
            self._label.setVisible(bool(text))
            self._second_line.setVisible(bool(text))

        # width = self._text_width.width(text) + 6
        # self._label.setMaximumWidth(width)


class DividerLayout(QHBoxLayout, object):
    """
    Basic splitter to separate layouts
    """

    def __init__(self):
        super(DividerLayout, self).__init__()

        self.setContentsMargins(40, 2, 40, 2)

        splitter = Divider(shadow=False, color=(60, 60, 60))
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
