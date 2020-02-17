#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementations for different types of progress bars
"""

from __future__ import print_function, division, absolute_import

from Qt.QtWidgets import *


class ProgressBar(QFrame, object):
    def __init__(self, *args):
        super(ProgressBar, self).__init__(*args)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._label = QLabel('', self)
        self._label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        layout.addWidget(self._label)

        self._progress_bar = QProgressBar(self)
        self._progress_bar.setFormat('')
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        layout.addWidget(self._progress_bar)

    def reset(self):
        """
        Reset progress bar
        """

        self._progress_bar.reset()

    def set_text(self, text):
        """
        Set the text of the progress bar
        :param text: str
        """

        self._label.setText(text)

    def set_value(self, value):
        """
        Set the value of the progress bar
        :param value: int or float
        """

        self._progress_bar.setValue(value)

    def set_range(self, min_, max_):
        """
        Set the range of the progress bar
        :param min_: int
        :param max_: int
        """

        self._progress_bar.setRange(min_, max_)
