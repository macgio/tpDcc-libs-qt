#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom layout implementations
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *


class FlowLayout(QLayout, object):
    """
    Layout that automatically adjust widgets position depending on the available space
    """

    def __init__(self, expand_last=(False, False), parent=None):
        super(FlowLayout, self).__init__(parent)

        self._item_list = list()
        self._expand_h = expand_last[0]
        self._expand_v = expand_last[1]
        self._expand_last = expand_last[0] or expand_last[1]

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        """
        Overrides base QLayout addItem function
        :param item: QObject
        """

        self._item_list.append(item)

    def count(self):
        """
        Overrides baes QLayout count function
        :return: int
        """

        return len(self._item_list)

    def itemAt(self, index):
        """
        Overrides base QLayout itemAt function
        :param index: int
        :return: QWidget or None
        """

        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
        """
        Overrides base QLayout takeAt function
        :param index: int
        :return: QWidget or None
        """

        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):
        """
        Overrides base QLayout expandingDirections function
        :return:Qt.Orientation
        """

        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        """
        Overrides base QLayout hasHeightForWidth function
        :param width: int
        :return: bool
        """

        return True

    def heightForWidth(self, width):
        """
        Overrides base QLayout heightForWidth function
        :param width: int
        :return: int
        """

        height = self._generate_layout(QRect(0, 0, width, 0))
        return height

    def setGeometry(self, rect):
        """
        Overrides base QLayout setGeometry function
        :param rect: QRect
        """

        super(FlowLayout, self).setGeometry(rect)
        self._generate_layout(rect, False)

    def sizeHint(self):
        """
        Overrides base QLayout sizeHint function
        :return: QSize
        """

        return self.minimumSize()

    def minimumSize(self):
        """
        Overrides base minimumSize function
        :return: QSize
        """

        size = QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def insert_widget(self, index, widget):
        """
        Inserts a new widget into the given index
        :param index: int
        :param widget: QWidget
        """

        self.addWidget(widget)
        self._item_list.insert(index, self._item_list.pop(-1))

    def remove_at(self, index):
        """
        Removes widget at given index
        :param index: int
        :return: bool, Whether the deletion operation was successful or not
        """

        item = self.takeAt(index)
        if not item:
            return False

        item.widget().setParent(None)
        item.widget().deleteLater()

        return True

    def _generate_layout(self, rect, test_only=True):
        """
        Generates layout with proper flow
        :param rect: QRect
        :param test_only: bool
        :return: int
        """

        x = rect.x()
        y = rect.y()
        line_height = 0

        for item in self._item_list:
            widget = item.widget()
            space_x = self.spacing() + widget.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            space_y = self.spacing() + widget.style().layoutSpacing(
                QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical) + 1

            next_x = x + widget.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + widget.sizeHint().width() + space_x
                line_height = 0

            if item == self._item_list[-1] and self._expand_last:
                width = rect.width() - x - 1 if self._expand_h else item.sizeHint().width()
                height = rect.height() - y - 1 if self._expand_v else item.sizeHint().height()
                size = QSize(width, height)
            else:
                size = item.sizeHint()

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), size))

            x = next_x

            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()
