#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for preferences window
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import stack


class PreferencesWidget(base.BaseWidget, object):

    closed = Signal(bool)

    def __init__(self, settings, parent=None):
        self._settings = settings
        super(PreferencesWidget, self).__init__(
            parent=parent
        )

        self._indexes = dict()
        self._category_buttons = dict()

        self._try_create_defaults()

    def ui(self):
        super(PreferencesWidget, self).ui()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._splitter = QSplitter()
        self._splitter.setOrientation(Qt.Horizontal)
        self._splitter.setSizes([150, 450])
        self._splitter.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self._scroll_area.setMinimumWidth(200)
        self._scroll_area_widget_contents = QWidget()
        self._scroll_area_widget_contents.setGeometry(QRect(0, 0, 480, 595))
        self._scroll_area_layout = QVBoxLayout()
        self._scroll_area_layout.setContentsMargins(1, 1, 1, 1)
        self._scroll_area_layout.setSpacing(2)
        self._scroll_area_widget_contents.setLayout(self._scroll_area_layout)
        self._categories_layout = QVBoxLayout()
        self._categories_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self._stack = stack.SlidingStackedWidget()
        self._stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._stack.set_vertical_mode()
        self._buttons_layout = QHBoxLayout()
        self._save_prefs_btn = QPushButton('Save as Default')
        self._save_prefs_close_btn = QPushButton('Save and Close')
        self._close_btn = QPushButton('Close')
        self._close_btn.setMaximumWidth(65)

        self._buttons_layout.addWidget(self._save_prefs_btn)
        self._buttons_layout.addWidget(self._save_prefs_close_btn)
        self._buttons_layout.addWidget(self._close_btn)
        self._categories_layout.addLayout(self._buttons_layout)
        self._scroll_area_layout.addLayout(self._categories_layout)
        self._scroll_area.setWidget(self._scroll_area_widget_contents)
        self._splitter.addWidget(self._scroll_area)
        self._splitter.addWidget(self._stack)

        self.main_layout.addWidget(self._splitter)

    def setup_signals(self):
        self._save_prefs_btn.clicked.connect(self._on_save_prefs)
        self._save_prefs_close_btn.clicked.connect(self._on_save_and_close_prefs)
        self._close_btn.clicked.connect(self._on_close)

    def showEvent(self, event):
        settings = self.settings()
        groups = settings.childGroups()
        for name, index_widget in self._indexes.items():
            index, widget = index_widget
            settings.beginGroup(name)
            if name not in groups:
                widget.init_defaults(settings)
            widget.show_widget(settings)
            settings.endGroup()

    def settings(self):
        return self._settings

    def add_category(self, name, widget):
        category_button = CategoryButton(text=name)
        self._categories_layout.insertWidget(self._categories_layout.count() - 2, category_button)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        index = self._stack.addWidget(widget)
        self._indexes[name] = (index, widget)
        self._category_buttons[index] = category_button
        category_button.clicked.connect(lambda checked=False, idx=index: self._on_switch_category_content(idx))

    def select_by_name(self, name):
        if name not in self._indexes:
            return
        index = self._indexes[name][0]
        self._stack.setCurrentIndex(index)
        self._category_buttons[index].setChecked(True)

    def _try_create_defaults(self):
        settings = self.settings()
        groups = settings.childGroups()
        for name, index_widget in self._indexes.items():
            index, widget = index_widget
            init_defaults = False
            if name not in groups:
                init_defaults = True
            settings.beginGroup(name)
            if init_defaults:
                widget.init_defaults(settings)
            settings.endGroup()
        settings.sync()

    def _on_switch_category_content(self, index):
        self._stack.slide_in_index(index)
        self._category_buttons[index].toggle()

    def _on_save_prefs(self):
        settings = self.settings()
        for name, index_widget in self._indexes.items():
            index, widget = index_widget
            settings.beginGroup(name)
            widget.serialize(settings)
            settings.endGroup()
        settings.sync()

    def _on_save_and_close_prefs(self):
        self._on_save_prefs()
        self.close()
        self.closed.emit(True)

    def _on_close(self):
        self.close()
        self.closed.emit(False)


class CategoryButton(QPushButton, object):
    def __init__(self, icon=None, text='test', parent=None):
        super(CategoryButton, self).__init__(text, parent)
        self.setMinimumHeight(30)
        self.setCheckable(True)
        self.setAutoExclusive(True)


class CategoryWidgetBase(QScrollArea, object):

    CATEGORY = 'GeneralPrefs'

    def __init__(self, parent=None):
        super(CategoryWidgetBase, self).__init__(parent)
        self.setWidgetResizable(True)

    def init_defaults(self, settings):
        pass

    def serialize(self, settings):
        pass

    def show_widget(self, settings):
        pass
