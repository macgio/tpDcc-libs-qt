#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base load widget for items
"""

from __future__ import print_function, division, absolute_import

import os

from tpQtLib.Qt.QtCore import *
from tpQtLib.Qt.QtWidgets import *
from tpQtLib.Qt.QtGui import *

import tpQtLib
from tpQtLib.core import base
from tpQtLib.widgets import formwidget
from tpQtLib.widgets.library import widgets


class LoadWidget(base.BaseWidget, object):
    def __init__(self, item, parent=None):
        super(LoadWidget, self).__init__(parent=parent)

        self._item = None
        self._icon_path = ''
        self._script_job = None
        self._options_widget = None

        self.set_item(item)
        # self.load_settings()

        self.create_sequence_widget()
        self.update_thumbnail_size()

    def ui(self):
        super(LoadWidget, self).ui()

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(2, 2, 0, 0)
        title_layout.setSpacing(2)
        self._icon_lbl = QLabel('')
        self._icon_lbl.setMaximumSize(QSize(14, 14))
        self._icon_lbl.setMinimumSize(QSize(14, 14))
        self._icon_lbl.setScaledContents(True)
        self._title_lbl = QLabel('Title')
        title_layout.addWidget(self._icon_lbl)
        title_layout.addWidget(self._title_lbl)

        icon_toggle_box = QFrame()
        icon_toggle_box.setFrameShape(QFrame.NoFrame)
        icon_toggle_box.setFrameShadow(QFrame.Plain)
        icon_toggle_box_lyt = QVBoxLayout()
        icon_toggle_box_lyt.setContentsMargins(0, 3, 0, 0)
        icon_toggle_box_lyt.setSpacing(3)
        icon_toggle_box.setLayout(icon_toggle_box_lyt)

        icon_toggle_box_header = QFrame()
        icon_toggle_box_header.setFrameShape(QFrame.NoFrame)
        icon_toggle_box_header.setFrameShadow(QFrame.Plain)
        icon_toggle_box_header_lyt = QVBoxLayout()
        icon_toggle_box_header.setContentsMargins(0, 0, 0, 0)
        icon_toggle_box_header_lyt.setSpacing(0)
        icon_toggle_box_header.setLayout(icon_toggle_box_header_lyt)

        icon_toggle_box_btn = QPushButton('ICON')
        icon_toggle_box_btn.setCheckable(True)
        icon_toggle_box_btn.setChecked(True)
        icon_toggle_box_btn.setFlat(True)
        icon_toggle_box_header_lyt.addWidget(icon_toggle_box_btn)

        icon_toggle_box_frame = QFrame()
        icon_toggle_box_frame.setFrameShape(QFrame.NoFrame)
        icon_toggle_box_frame.setFrameShadow(QFrame.Plain)
        icon_toggle_box_frame_lyt = QVBoxLayout()
        icon_toggle_box_frame_lyt.setContentsMargins(0, 3, 0, 0)
        icon_toggle_box_frame_lyt.setSpacing(3)
        icon_toggle_box_frame.setLayout(icon_toggle_box_frame_lyt)

        thumbnail_layout = QHBoxLayout()
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        thumbnail_layout.setSpacing(0)
        icon_toggle_box_frame_lyt.addLayout(thumbnail_layout)

        thumbnail_frame_layout = QVBoxLayout()
        thumbnail_frame_layout.setContentsMargins(0, 0, 0, 0)
        thumbnail_frame_layout.setSpacing(0)
        self._thumbnail_frame = QFrame()
        self._thumbnail_frame.setFrameShape(QFrame.NoFrame)
        self._thumbnail_frame.setFrameShadow(QFrame.Plain)
        self._thumbnail_frame.setLayout(thumbnail_frame_layout)
        thumbnail_layout.addWidget(self._thumbnail_frame)
        self._thumbnail_btn = QToolButton()
        self._thumbnail_btn.setMinimumSize(QSize(0, 0))
        self._thumbnail_btn.setMaximumSize(QSize(150, 150))
        self._thumbnail_btn.setStyleSheet('color: rgb(40, 40, 40);\nborder: 1px solid rgb(0, 0, 0, 0);\nbackground-color: rgb(254, 255, 230, 0);')
        self._thumbnail_btn.setLayoutDirection(Qt.LeftToRight)
        self._thumbnail_btn.setText('Snapshot')
        self._thumbnail_btn.setIcon(tpQtLib.resource.icon('thumbnail'))
        thumbnail_frame_layout.addWidget(self._thumbnail_btn)

        icon_toggle_box_lyt.addWidget(icon_toggle_box_header)
        icon_toggle_box_lyt.addWidget(icon_toggle_box_frame)

        info_toggle_box = QFrame()
        info_toggle_box.setFrameShape(QFrame.NoFrame)
        info_toggle_box.setFrameShadow(QFrame.Plain)
        info_toggle_box_lyt = QVBoxLayout()
        info_toggle_box_lyt.setContentsMargins(0, 0, 0, 0)
        info_toggle_box_lyt.setSpacing(0)
        info_toggle_box.setLayout(info_toggle_box_lyt)

        info_toggle_box_header = QFrame()
        info_toggle_box_header.setFrameShape(QFrame.NoFrame)
        info_toggle_box_header.setFrameShadow(QFrame.Plain)
        info_toggle_box_header_lyt = QVBoxLayout()
        info_toggle_box_header.setContentsMargins(0, 0, 0, 0)
        info_toggle_box_header_lyt.setSpacing(0)
        info_toggle_box_header.setLayout(info_toggle_box_header_lyt)

        self._info_toggle_box_btn = QPushButton('INFO')
        self._info_toggle_box_btn.setCheckable(True)
        self._info_toggle_box_btn.setChecked(True)
        self._info_toggle_box_btn.setFlat(True)
        info_toggle_box_header_lyt.addWidget(self._info_toggle_box_btn)

        self._info_toggle_box_frame = QFrame()
        self._info_toggle_box_frame.setFrameShape(QFrame.NoFrame)
        self._info_toggle_box_frame.setFrameShadow(QFrame.Plain)
        info_toggle_box_frame_lyt = QVBoxLayout()
        info_toggle_box_frame_lyt.setContentsMargins(0, 3, 0, 0)
        info_toggle_box_frame_lyt.setSpacing(3)
        self._info_toggle_box_frame.setLayout(info_toggle_box_frame_lyt)

        self._info_frame = QFrame()
        self._info_frame.setFrameShape(QFrame.NoFrame)
        self._info_frame.setFrameShadow(QFrame.Plain)
        info_frame_lyt = QVBoxLayout()
        info_frame_lyt.setContentsMargins(0, 0, 0, 0)
        info_frame_lyt.setSpacing(0)
        self._info_frame.setLayout(info_frame_lyt)
        info_toggle_box_frame_lyt.addWidget(self._info_frame)

        info_toggle_box_lyt.addWidget(info_toggle_box_header)
        info_toggle_box_lyt.addWidget(self._info_toggle_box_frame)

        # options_toggle_box = QFrame()
        # options_toggle_box.setFrameShape(QFrame.NoFrame)
        # options_toggle_box.setFrameShadow(QFrame.Plain)
        # options_toggle_box_lyt = QVBoxLayout()
        # options_toggle_box_lyt.setContentsMargins(0, 0, 0, 0)
        # options_toggle_box_lyt.setSpacing(0)
        # options_toggle_box.setLayout(info_toggle_box_lyt)
        #
        # options_toggle_box_header = QFrame()
        # options_toggle_box_header.setFrameShape(QFrame.NoFrame)
        # options_toggle_box_header.setFrameShadow(QFrame.Plain)
        # options_toggle_box_header_lyt = QVBoxLayout()
        # options_toggle_box_header.setContentsMargins(0, 0, 0, 0)
        # options_toggle_box_header_lyt.setSpacing(0)
        # options_toggle_box_header.setLayout(options_toggle_box_header_lyt)
        #
        # options_toggle_box_btn = QPushButton('ICON')
        # options_toggle_box_btn.setCheckable(True)
        # options_toggle_box_btn.setChecked(True)
        # options_toggle_box_btn.setFlat(True)
        # options_toggle_box_header_lyt.addWidget(info_toggle_box_btn)
        #
        # options_toggle_box_frame = QFrame()
        # options_toggle_box_frame.setFrameShape(QFrame.NoFrame)
        # options_toggle_box_frame.setFrameShadow(QFrame.Plain)
        # options_toggle_box_frame_lyt = QVBoxLayout()
        # options_toggle_box_frame_lyt.setContentsMargins(0, 3, 0, 3)
        # options_toggle_box_frame_lyt.setSpacing(3)
        # options_toggle_box_frame.setLayout(info_toggle_box_frame_lyt)
        #
        # options_frame = QFrame()
        # options_frame.setFrameShape(QFrame.NoFrame)
        # options_frame.setFrameShadow(QFrame.Plain)
        # options_frame_lyt = QVBoxLayout()
        # options_frame_lyt.setContentsMargins(0, 0, 0, 0)
        # options_frame_lyt.setSpacing(0)
        # options_frame.setLayout(info_toggle_box_frame_lyt)
        # options_toggle_box_lyt.addWidget(options_frame)
        #
        # options_toggle_box_lyt.addWidget(options_toggle_box_header)
        # options_toggle_box_lyt.addWidget(info_toggle_box_frame)
        #
        # preview_buttons_frame = QFrame()
        # preview_buttons_frame.setFrameShape(QFrame.NoFrame)
        # preview_buttons_frame.setFrameShadow(QFrame.Plain)
        # preview_buttons_frame_lyt = QVBoxLayout()
        # preview_buttons_frame_lyt.setContentsMargins(9, 9, 9, 9)
        # preview_buttons_frame_lyt.setSpacing(0)
        # preview_buttons_frame_lyt.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))
        # apply_btn = QPushButton('Apply')
        # preview_buttons_frame_lyt.addWidget(apply_btn)
        # preview_buttons_frame_lyt.addItem(QSpacerItem(10, 0, QSizePolicy.Expanding, QSizePolicy.Preferred))

        self.main_layout.addLayout(title_layout)
        self.main_layout.addWidget(icon_toggle_box)
        self.main_layout.addWidget(info_toggle_box)
        # self.main_layout.addWidget(options_toggle_box)
        self.main_layout.addItem(QSpacerItem(0, 250, QSizePolicy.Preferred, QSizePolicy.Expanding))

    def setup_signals(self):
        self._info_toggle_box_btn.clicked.connect(self.save_settings)
        self._info_toggle_box_btn.toggled[bool].connect(self._info_toggle_box_frame.setVisible)

    def icon_path(self):
        """
        Returns the icon path to be used for the thumbnail
        :return: str
        """

        return self._icon_path

    def set_icon_path(self, path):
        """
        Sets the icon path to be used for the thumbnail
        :param path: str
        """

        self._icon_path = path
        icon = QIcon(QPixmap(path))
        self.set_icon(icon)
        self.update_thumbnail_size()
        self.item().update()

    def set_icon(self, icon):
        """
        Sets the icon to be shown for the preview
        :param icon: QIcon
        """

        self._thumbnail_btn.setIcon(icon)
        self._thumbnail_btn.setIconSize(QSize(200, 200))
        self._thumbnail_btn.setText('')

    def item(self):
        """
        Returns the library item to load
        :return: LibraryItem
        """

        return self._item

    def set_item(self, item):
        """
        Sets the library item to load
        :param item: LibraryItem
        """

        self._item = item

        self._title_lbl.setText(item.MenuName)
        self._icon_lbl.setPixmap(QPixmap(item.TypeIconPath))

        info_widget = formwidget.FormWidget(self)
        info_widget.set_schema(item.info())
        self._info_frame.layout().addWidget(info_widget)

    def create_sequence_widget(self):
        """
        Creates a sequence widget to replace the static thumbnail widget
        """

        self._sequence_widget = widgets.LibraryImageSequenceWidget(self)
        self._sequence_widget.setStyleSheet(self._thumbnail_btn.styleSheet())
        self._sequence_widget.setToolTip(self._thumbnail_btn.toolTip())
        self._thumbnail_frame.layout().insertWidget(0, self._sequence_widget)
        self._thumbnail_btn.hide()
        self._thumbnail_btn = self._sequence_widget
        path = self.item().thumbnail_path()
        if os.path.exists(path):
            self.set_icon_path(path)
        if self.item().image_sequence_path():
            self._sequence_widget.set_dirname(self.item().image_sequence_path())

    def update_thumbnail_size(self):
        """
        Updates the thumbnail button to the size of the widget
        """

        width = self.width() - 10
        if width > 250:
            width = 250
        size = QSize(width, width)
        self._thumbnail_btn.setIconSize(size)
        self._thumbnail_btn.setMaximumSize(size)
        self._thumbnail_frame.setMaximumSize(size)

    def save_settings(self):
        pass