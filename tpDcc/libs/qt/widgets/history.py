#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt widgets related with version management
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.python import version
from tpDcc.libs.qt.core import base, qtutils
from tpDcc.libs.qt.widgets import treewidgets


class HistoryTreeWidget(treewidgets.FileTreeWidget, object):

    HEADER_LABELS = ['Version', 'Comment', 'Size MB', 'User', 'Time']

    def __init__(self):
        super(HistoryTreeWidget, self).__init__()

        if qtutils.is_pyside() or qtutils.is_pyside2():
            self.sortByColumn(0, Qt.SortOrder.DescendingOrder)

        self.setColumnWidth(0, 70)
        self.setColumnWidth(1, 200)
        self.setColumnWidth(2, 70)
        self.setColumnWidth(3, 70)
        self.setColumnWidth(4, 70)
        self._padding = 1

    def _get_files(self):
        if self._directory:
            version_file = version.VersionFile(file_path=self._directory)
            version_data = version_file.get_organized_version_data()
            if version_data:
                self._padding = len(str(len(version_data)))
                return version_data
            else:
                return list()

    def _add_item(self, version_data):
        version, comment, user, file_size, file_date, version_file = version_data
        version_str = str(version).zfill(self._padding)

        item = QTreeWidgetItem()
        item.setText(0, version_str)
        item.setText(1, comment)
        item.setText(2, str(file_size))
        item.setText(3, user)
        item.setText(4, file_date)
        self.addTopLevelItem(item)
        item.file_path = version_file

    def _add_items(self, version_list):
        if not version_list:
            self.clear()

        for version_data in version_list:
            self._add_item(version_data)

    def _on_item_activated(self, item):
        return


class HistoryFileWidget(base.DirectoryWidget, object):

    VERSION_LIST = HistoryTreeWidget

    def ui(self):
        super(HistoryFileWidget, self).ui()

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self._btn_layout = QHBoxLayout()
        self._open_btn = QPushButton('Open')
        self._open_btn.setMaximumWidth(100)
        self._btn_layout.addWidget(self._open_btn)
        self._version_list = self.VERSION_LIST()
        self.main_layout.addWidget(self._version_list)
        self.main_layout.addLayout(self._btn_layout)

    def setup_signals(self):
        self._open_btn.clicked.connect(self.open_version)

    def set_directory(self, directory):
        """
        Overrides base base.DirectoryWidget set_directory function
        :param directory: str
        """

        super(HistoryFileWidget, self).set_directory(directory)

        if self.isVisible():
            self._version_list.set_directory(directory, refresh=True)
        else:
            self._version_list.set_directory(directory, refresh=False)

    def open_version(self):
        """
        Opens selected version
        Override functionality for specific data
        """

        pass

    def refresh(self):
        """
        Updates version list
        """

        self._version_list.refresh()

    def set_data_class(self, data_class_instance):
        self._data_class = data_class_instance
        if self._directory:
            self._data_class.set_directory(self._directory)
