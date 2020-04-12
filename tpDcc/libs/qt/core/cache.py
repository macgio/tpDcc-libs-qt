#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that defines a base class to cache resources
"""

from __future__ import print_function, division, absolute_import

import os

from Qt.QtCore import *
from Qt.QtGui import *
from Qt.QtSvg import *


class CacheResource(object):

    _render = QSvgRenderer()

    def __init__(self, cls):
        super(CacheResource, self).__init__()

        self._cls = cls
        self._cache_pixmap_dict = dict()

    def __call__(self, path, color=None):
        if not path or not os.path.isfile(path):
            return None

        key = '{}{}'.format(path.lower(), color or '')
        pixmap = self._cache_pixmap_dict.get(key, None)
        if not pixmap:
            if path.endswith('svg'):
                pixmap = self._render_svg(path, color)
            else:
                pixmap = self._cls(path)
                if color:
                    pixmap.set_color(color)

            self._cache_pixmap_dict.update({key: pixmap})

        return pixmap

    def _render_svg(self, svg_path, replace_color=None):
        if issubclass(self._cls, QIcon) and not replace_color:
            return QIcon(svg_path)

        with open(svg_path, 'r+') as f:
            data_content = f.read()
            if replace_color is not None:
                data_content = data_content.replace('#555555', replace_color)
                self._render.load(QByteArray(data_content))
                pix = QPixmap(128, 128)
                pix.fill(Qt.transparent)
                painter = QPainter(pix)
                self._render.render(painter)
                painter.end()
                if issubclass(self._cls, QPixmap):
                    return pix
                else:
                    return self._cls(pix)
