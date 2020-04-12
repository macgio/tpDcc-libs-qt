#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom widgets to handle file/folder browser related tasks
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.qt.widgets import buttons


def browse_file(self):
    filter_list = 'File({})'.format(' '.join(['*' + e for e in self.filters])) if self.filters else 'Any File(*)'
    if self.multiple:
        r_files, _ = QFileDialog.getOpenFileNames(self, 'Browse Files', self.path, filter_list)
        if r_files:
            self.filesChanged.emit(r_files)
            self.path = r_files[0]
    else:
        r_file, _ = QFileDialog.getOpenFileName(self, 'Browse File', self.path, filter_list)
        if r_file:
            self.fileChanged.emit(r_file)
            self.path = r_file


def browse_folder(self):
    r_folder = QFileDialog.getExistingDirectory(self, 'Browse Folder', self.path)
    if not r_folder:
        return

    if self.multiple:
        self.foldersChanged.emit([r_folder])
    else:
        self.folderChanged.emit(r_folder)
    self.path = r_folder


def save_file(self):
    filter_list = 'File({})'.format(' '.join(['*' + e for e in self.filters])) if self.filters else 'Any File(*)'
    r_file, _ = QFileDialog.getSaveFileName(self, 'Save File', self.path, filter_list)
    if not r_file:
        return

    self.fileChanged.emit(r_file)
    self.path = r_file


class ClickBrowserFileButton(buttons.BaseButton, object):
    fileChanged = Signal(str)
    filesChanged = Signal(list)

    _on_browse_file = browse_file

    def __init__(self, text='Browse', multiple=False, parent=None):
        super(ClickBrowserFileButton, self).__init__(text=text, parent=parent)

        self._path = None
        self._multiple = multiple
        self._filters = list()

        self.setToolTip('Click to browse file')
        self.clicked.connect(self._on_browse_file)

    @property
    def filters(self):
        """
        Returns browse filters
        :return: list(str)
        """

        return self._filters

    @filters.setter
    def filters(self, value):
        """
        Sets browse filters
        :param value: list(str)
        """

        self._filters = value

    @property
    def path(self):
        """
        Returns last browse file path
        :return: str
        """

        return self._path

    @path.setter
    def path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self._path = value

    @property
    def multiple(self):
        """
        Returns whether or not browse can select multiple files
        :return: bool
        """

        return self._multiple

    @multiple.setter
    def multiple(self, flag):
        """
        Sets whether or not browse can select multiple files
        :param flag: bool
        """

        self._multiple = flag


class ClickBrowserFolderButton(buttons.BaseButton, object):
    folderChanged = Signal(str)
    foldersChanged = Signal(list)

    _on_browse_folder = browse_folder

    def __init__(self, text='', multiple=False, parent=None):
        super(ClickBrowserFolderButton, self).__init__(text=text, parent=parent)

        self._path = None
        self._multiple = multiple

        self.setToolTip('Click to browse folder')
        self.clicked.connect(self._on_browse_folder)

    @property
    def path(self):
        """
        Returns last browse file path
        :return: str
        """

        return self._path

    @path.setter
    def path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self._path = value

    @property
    def multiple(self):
        """
        Returns whether or not browse can select multiple files
        :return: bool
        """

        return self._multiple

    @multiple.setter
    def multiple(self, flag):
        """
        Sets whether or not browse can select multiple files
        :param flag: bool
        """

        self._multiple = flag


class ClickBrowserFileToolButton(buttons.BaseToolButton, object):
    fileChanged = Signal(str)
    filesChanged = Signal(list)

    _on_browse_file = browse_file

    def __init__(self, multiple=False, parent=None):
        super(ClickBrowserFileToolButton, self).__init__(parent=parent)

        self._path = None
        self._multiple = multiple
        self._filters = list()

        self.image('folder')
        self.icon_only()
        self.setToolTip('Click to browse file')
        self.clicked.connect(self._on_browse_file)

    @property
    def filters(self):
        """
        Returns browse filters
        :return: list(str)
        """

        return self._filters

    @filters.setter
    def filters(self, value):
        """
        Sets browse filters
        :param value: list(str)
        """

        self._filters = value

    @property
    def path(self):
        """
        Returns last browse file path
        :return: str
        """

        return self._path

    @path.setter
    def path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self._path = value

    @property
    def multiple(self):
        """
        Returns whether or not browse can select multiple files
        :return: bool
        """

        return self._multiple

    @multiple.setter
    def multiple(self, flag):
        """
        Sets whether or not browse can select multiple files
        :param flag: bool
        """

        self._multiple = flag
