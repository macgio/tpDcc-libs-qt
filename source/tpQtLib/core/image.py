#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utility functions related with images
"""

from __future__ import print_function, division, absolute_import

import os
import base64

from tpQtLib.Qt.QtCore import *
from tpQtLib.Qt.QtGui import *


# region Public Functions
def image_to_base64(image_path):
    """
    Converts image file to base64
    :param image_path: str
    :return: str
    """

    if os.path.isfile(image_path):
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read())


def base64_to_image(base64_string, image_format='PNG'):
    """
    Converts base64 to QImage
    :param base64_string: str
    :param image_format: str
    :return: QImage
    """

    if isinstance(base64_string, basestring):
        ba = QByteArray.fromBase64(base64_string)
        image = QImage.fromData(ba, image_format)
        return image


def base64_to_bitmap(base64_string, bitmap_format='PNG'):
    """
    Converts base64 to QBitmap
    :param base64_string: str
    :param image_format: str
    :return: QBitmap
    """

    if isinstance(base64_string, basestring):
        image = base64_to_image(base64_string, bitmap_format)
        if image is not None:
            bitmap = QBitmap.fromImage(image)
            return bitmap


def base64_to_icon(base64_string, icon_format='PNG'):
    """
    Converts base64 to QIcon
    :param base64_string: str
    :param icon_format: str
    :return: QIcon
    """

    if isinstance(base64_string, basestring):
        bitmap = base64_to_bitmap (base64_string, icon_format)
        if bitmap is not None:
            icon = QIcon(bitmap)
            return icon
# endregion
