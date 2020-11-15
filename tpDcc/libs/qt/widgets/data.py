#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt widgets related with data management
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QSizePolicy

from tpDcc.managers import resources
from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import layouts, buttons


class SaveFileWidet(base.DirectoryWidget):

    fileChanged = Signal()

    TIP = ''

    def __init__(self, parent=None):

        self._data_class = None

        super(SaveFileWidet, self).__init__(parent=parent)

        self._tip = self.TIP
        if self._tip:
            self._create_tip()

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout()
        main_layout.setAlignment(Qt.AlignTop)

        return main_layout

    def ui(self):
        super(SaveFileWidet, self).ui()

        self.setContentsMargins(1, 1, 1, 1)

        self._save_button = buttons.BaseButton('Save', parent=self)
        self._load_button = buttons.BaseButton('Open', parent=self)
        self._save_button.setMaximumWidth(100)
        self._load_button.setMaximumWidth(100)
        self._save_button.setMinimumWidth(60)
        self._load_button.setMinimumWidth(60)
        self._save_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._load_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self._save_button.setIcon(resources.icon('save'))
        self._load_button.setIcon(resources.icon('folder'))

        self.main_layout.addWidget(self._save_button)
        self.main_layout.addWidget(self._load_button)

    def setup_signals(self):
        self._save_button.clicked.connect(self._on_save)
        self._load_button.clicked.connecxt(self._on_load)

    def set_directory(self, directory, data_class=None):
        super(SaveFileWidet, self).set_directory(directory)

        if data_class:
            self._data_class = data_class
        if not data_class and self._data_class:
            self._data_class.set_directory(self._directory)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_tip(self, value):
        self._tip = value
        if self._tip:
            self._create_tip()

    def set_no_save(self):
        self._save_button.setEnabled(False)

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _create_tip(self):
        self.setToolTip(self._tip)

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_save(self):
        self.fileChanged.emit()

    def _on_load(self):
        pass
