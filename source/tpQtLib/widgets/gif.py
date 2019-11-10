#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for custom PySide/PyQt windows
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *


class GifLabel(QLabel, object):
    def __init__(self, gif_file):
        super(GifLabel, self).__init__('Name')

        self._movie = QMovie(gif_file, QByteArray(), self)
        self._movie.setCacheMode(QMovie.CacheAll)
        self._movie.setSpeed(100)
        self.setMovie(self._movie)
        self.setAlignment(Qt.AlignCenter)
        self._movie.start()
