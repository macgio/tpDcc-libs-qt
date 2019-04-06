#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# """ ==================================================================
# Script Name: resource.py
# by Tomas Poveda
# Module that defines a base class to load resources
# ______________________________________________________________________
# ==================================================================="""

import os

from tpQtLib.Qt.QtGui import *

from tpPyUtils import folder
from tpQtLib.core import pixmap as pixmap_resource
from tpPyUtils import qtutils, path


def generate_resources_file(generate_qr_file=True):
    """
    Loop through resources adn generates a QR file with all of them
    :param generate_qr_file: bool, True if you want to generate the QR file
    """

    res_file_name = 'res'

    res_folder = os.path.dirname(os.path.abspath(__file__))
    res_out_folder = res_folder
    if not os.path.exists(res_folder):
        raise RuntimeError('Resources folder {0} does not exists!'.format(res_folder))

    res_folders = folder.get_sub_folders(res_folder)
    res_folders = [os.path.join(res_folder, x) for x in res_folders]
    res_folders = [x for x in res_folders if os.path.exists(x)]

    qrc_file = os.path.join(res_folder, res_file_name + '.qrc')
    qrc_py_file = os.path.join(res_out_folder, res_file_name + '.py')

    if generate_qr_file:
        qtutils.create_qrc_file(res_folders, qrc_file)
    if not os.path.isfile(qrc_file):
        return

    qtutils.create_python_qrc_file(qrc_file, qrc_py_file)


def get(*args):
    """
    Returns path for the given resource name
    :param args: str, name of the source to retrieve path of
    :return: str
    """

    return Resource().get(*args)


def icon(*args, **kwargs):
    """
    Returns icon for the given resource name
    :param name: str, name of the icon
    :param extension: str, extension of the icon
    :param color: QColor, color of the icon
    :return: QIcon
    """

    return Resource().icon(*args, **kwargs)


def pixmap(*args, **kwargs):
    """
    Returns QPixmap for the given resource name
    :param name: str, name of the pixmap
    :param category: str, category of the pixmap
    :param extension: str, extension of the pixmap
    :param color: QColor, color of the pixmap
    :return: QPixmap
    """

    return Resource().pixmap(*args, **kwargs)

def gui(*args, **kwargs):
    """
    Returns QWidget loaded from .ui file
    :param name: str, name of the UI file
    :return:
    """

    return Resource().ui(*args, **kwargs)


class Resource(object):

    RESOURCES_FOLDER = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, *args):
        dirname = ''
        if args:
            dirname = os.path.join(*args)
        if os.path.isfile(dirname):
            dirname = os.path.dirname(dirname)
        self._dirname = dirname or self.RESOURCES_FOLDER

    def dirname(self):
        """
        Returns absolute path to the resource
        :return: str
        """

        return self._dirname

    def get(self, *args):
        """
        Returns the resource path with the given paths
        :param args: str, resource name
        :return: str
        """

        return path.clean_path(os.path.join(self.dirname(), *args))

    def icon(self, name, extension='png', color=None):
        """
        Returns a QIcon object from the given resource name
        :param name: str, name of the icon
        :param extension: str, extension of the icon
        :param color: QColor, color of the icon
        :return: QIcon
        """

        p = self.pixmap(name=name, category='icons', extension=extension, color=color)
        return QIcon(p)

    def pixmap(self, name, category='images', extension='png', color=None):
        """
        Return a QPixmap object from the given resource anme
        :param name: str, name of the pixmap
        :param category: str, category of the pixmap
        :param extension: str, extension of the pixmap
        :param color: QColor, color of the pixmap
        :return: QPixmap
        """

        path = self.get(category, name + '.' + extension)
        p = pixmap_resource.Pixmap(path)
        if color:
            p.set_color(new_color=color)

        return p

    def ui(self, name):
        """
        Returns a QWidget loaded from .ui file
        :param name: str, name of the ui file you want to load
        :return: QWidget
        """

        return qtutils.ui_loader(ui_file=self.get('uis', name + '.ui'))
