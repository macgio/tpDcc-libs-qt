#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base load widget for items
"""

from __future__ import print_function, division, absolute_import

import os

from Qt.QtCore import Qt, QSize
from Qt.QtWidgets import QSizePolicy, QWidget, QFrame, QToolButton, QSpacerItem
from Qt.QtGui import QPixmap, QIcon

from tpDcc.managers import resources
from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import layouts, buttons, label, formwidget, dividers, history, tabs
from tpDcc.libs.qt.widgets.library import widgets


# class BaseLoadWidget(base.BaseWidget, object):
#     def __init__(self, item, parent=None):
#         super(BaseLoadWidget, self).__init__(parent=parent)
#
#         self._item = None
#
#         self.setObjectName('Load')
#         self.set_item(item)
#
#     def item(self):
#         """
#         Returns the library item to load
#         :return: LibraryItem
#         """
#
#         return self._item
#
#     def set_item(self, item):
#         """
#         Sets the library item to load
#         :param item: LibraryItem
#         """
#
#         self._item = item


class OptionsFileWidget(base.DirectoryWidget, object):
    def __init__(self, parent=None):
        super(OptionsFileWidget, self).__init__(parent)

        self._data_object = None

    def set_directory(self, directory):
        super(OptionsFileWidget, self).set_directory(directory)

        if self._data_object:
            self._data_object.set_directory(self.directory)
            self.refresh()

    def set_data_object(self, data_object_instance):
        self._data_object = data_object_instance
        if self.directory:
            self._data_object.set_directory(self.directory)
        self.refresh()

    def refresh(self):
        pass


class LoadWidget(BaseLoadWidget, object):

    HISTORY_WIDGET = history.HistoryFileWidget
    OPTIONS_WIDGET = None

    def __init__(self, item, parent=None):

        self._icon_path = ''
        self._script_job = None
        self._options_widget = None

        super(LoadWidget, self).__init__(item, parent=parent)

        self.load_settings()

        self.create_sequence_widget()
        self.update_thumbnail_size()

    def ui(self):
        super(LoadWidget, self).ui()

        tabs_widget = tabs.BaseTabWidget(parent=self)

        info_widget = QWidget()
        info_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        info_widget.setLayout(info_layout)

        if self.OPTIONS_WIDGET:
            self._options_widget = self.OPTIONS_WIDGET(parent=self)

        title_layout = layouts.HorizontalLayout(spacing=1, margins=(1, 1, 0, 0))
        self._icon_lbl = label.BaseLabel('', parent=self)
        self._icon_lbl.setMaximumSize(QSize(14, 14))
        self._icon_lbl.setMinimumSize(QSize(14, 14))
        self._icon_lbl.setScaledContents(True)
        self._title_lbl = label.BaseLabel('Title', parent=self)
        title_layout.addWidget(self._icon_lbl)
        title_layout.addWidget(self._title_lbl)

        icon_toggle_box = QFrame()
        icon_toggle_box.setFrameShape(QFrame.NoFrame)
        icon_toggle_box.setFrameShadow(QFrame.Plain)
        icon_toggle_box_lyt = layouts.VerticalLayout(spacing=1, margins=(0, 1, 0, 0))
        icon_toggle_box.setLayout(icon_toggle_box_lyt)

        icon_toggle_box_header = QFrame()
        icon_toggle_box_header.setFrameShape(QFrame.NoFrame)
        icon_toggle_box_header.setFrameShadow(QFrame.Plain)
        icon_toggle_box_header_lyt = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        icon_toggle_box_header.setLayout(icon_toggle_box_header_lyt)

        self._icon_toggle_box_btn = buttons.BaseButton('ICON', parent=self)
        self._icon_toggle_box_btn.setObjectName('iconButton')
        self._icon_toggle_box_btn.setCheckable(True)
        self._icon_toggle_box_btn.setChecked(True)
        icon_toggle_box_header_lyt.addWidget(self._icon_toggle_box_btn)

        self._icon_toggle_box_frame = QFrame()
        self._icon_toggle_box_frame.setFrameShape(QFrame.NoFrame)
        self._icon_toggle_box_frame.setFrameShadow(QFrame.Plain)
        icon_toggle_box_frame_lyt = layouts.VerticalLayout(spacing=1, margins=(0, 1, 0, 0))
        self._icon_toggle_box_frame.setLayout(icon_toggle_box_frame_lyt)

        thumbnail_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        icon_toggle_box_frame_lyt.addLayout(thumbnail_layout)

        thumbnail_frame_layout = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        self._thumbnail_frame = QFrame()
        self._thumbnail_frame.setFrameShape(QFrame.NoFrame)
        self._thumbnail_frame.setFrameShadow(QFrame.Plain)
        self._thumbnail_frame.setLayout(thumbnail_frame_layout)
        thumbnail_layout.addWidget(self._thumbnail_frame)
        self._thumbnail_btn = QToolButton()
        self._thumbnail_btn.setObjectName('thumbnailButton')
        self._thumbnail_btn.setMinimumSize(QSize(0, 0))
        self._thumbnail_btn.setMaximumSize(QSize(150, 150))
        self._thumbnail_btn.setStyleSheet(
            'color: rgb(40, 40, 40);\nborder: 1px solid rgb(0, 0, 0, 0);\nbackground-color: rgb(254, 255, 230, 0);')
        self._thumbnail_btn.setLayoutDirection(Qt.LeftToRight)
        self._thumbnail_btn.setText('Snapshot')
        self._thumbnail_btn.setIcon(resources.icon('thumbnail'))
        thumbnail_frame_layout.addWidget(self._thumbnail_btn)

        icon_toggle_box_lyt.addWidget(icon_toggle_box_header)
        icon_toggle_box_lyt.addWidget(self._icon_toggle_box_frame)

        info_toggle_box = QFrame()
        info_toggle_box.setFrameShape(QFrame.NoFrame)
        info_toggle_box.setFrameShadow(QFrame.Plain)
        info_toggle_box_lyt = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        info_toggle_box.setLayout(info_toggle_box_lyt)

        info_toggle_box_header = QFrame()
        info_toggle_box_header.setFrameShape(QFrame.NoFrame)
        info_toggle_box_header.setFrameShadow(QFrame.Plain)
        info_toggle_box_header_lyt = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        info_toggle_box_header.setLayout(info_toggle_box_header_lyt)

        self._info_toggle_box_btn = buttons.BaseButton('INFO', parent=self)
        self._info_toggle_box_btn.setObjectName('infoButton')
        self._info_toggle_box_btn.setCheckable(True)
        self._info_toggle_box_btn.setChecked(True)
        info_toggle_box_header_lyt.addWidget(self._info_toggle_box_btn)

        self._info_toggle_box_frame = QFrame()
        self._info_toggle_box_frame.setFrameShape(QFrame.NoFrame)
        self._info_toggle_box_frame.setFrameShadow(QFrame.Plain)
        info_toggle_box_frame_lyt = layouts.VerticalLayout(spacing=1, margins=(0, 1, 0, 0))
        self._info_toggle_box_frame.setLayout(info_toggle_box_frame_lyt)

        self._info_frame = QFrame()
        self._info_frame.setFrameShape(QFrame.NoFrame)
        self._info_frame.setFrameShadow(QFrame.Plain)
        info_frame_lyt = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        self._info_frame.setLayout(info_frame_lyt)
        info_toggle_box_frame_lyt.addWidget(self._info_frame)

        info_toggle_box_lyt.addWidget(info_toggle_box_header)
        info_toggle_box_lyt.addWidget(self._info_toggle_box_frame)

        version_toggle_box = QFrame()
        version_toggle_box.setFrameShape(QFrame.NoFrame)
        version_toggle_box.setFrameShadow(QFrame.Plain)
        version_toggle_box_lyt = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        version_toggle_box.setLayout(version_toggle_box_lyt)

        version_toggle_box_header = QFrame()
        version_toggle_box_header.setFrameShape(QFrame.NoFrame)
        version_toggle_box_header.setFrameShadow(QFrame.Plain)
        version_toggle_box_header_lyt = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        version_toggle_box_header.setLayout(version_toggle_box_header_lyt)

        self._version_toggle_box_btn = buttons.BaseButton('VERSION', parent=self)
        self._version_toggle_box_btn.setObjectName('versionButton')
        self._version_toggle_box_btn.setCheckable(True)
        self._version_toggle_box_btn.setChecked(True)
        version_toggle_box_header_lyt.addWidget(self._version_toggle_box_btn)

        self._version_toggle_box_frame = QFrame()
        self._version_toggle_box_frame.setFrameShape(QFrame.NoFrame)
        self._version_toggle_box_frame.setFrameShadow(QFrame.Plain)
        version_toggle_box_frame_lyt = layouts.VerticalLayout(spacing=1, margins=(0, 1, 0, 0))
        self._version_toggle_box_frame.setLayout(version_toggle_box_frame_lyt)

        self._version_frame = QFrame()
        self._version_frame.setFrameShape(QFrame.NoFrame)
        self._version_frame.setFrameShadow(QFrame.Plain)
        version_frame_lyt = layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))
        self._version_frame.setLayout(version_frame_lyt)
        version_toggle_box_frame_lyt.addWidget(self._version_frame)

        self._history_widget = self.HISTORY_WIDGET()
        version_frame_lyt.addWidget(self._history_widget)

        version_toggle_box_lyt.addWidget(version_toggle_box_header)
        version_toggle_box_lyt.addWidget(self._version_toggle_box_frame)

        preview_buttons_frame = QFrame()
        preview_buttons_frame.setObjectName('previewButtons')
        preview_buttons_frame.setFrameShape(QFrame.NoFrame)
        preview_buttons_frame.setFrameShadow(QFrame.Plain)
        self._preview_buttons_frame_lyt = layouts.VerticalLayout(spacing=0, margins=(2, 2, 2, 2))
        self._preview_buttons_lyt = layouts.HorizontalLayout(spacing=2, margins=(0, 0, 0, 0))
        self._load_btn = buttons.BaseButton('Load', parent=self)
        self._load_btn.setObjectName('loadButton')
        self._load_btn.setMinimumSize(QSize(60, 35))
        self._load_btn.setMaximumSize(QSize(125, 35))
        self._preview_buttons_frame_lyt.addStretch()
        self._preview_buttons_frame_lyt.addLayout(self._preview_buttons_lyt)
        self._preview_buttons_frame_lyt.addStretch()
        self._preview_buttons_lyt.addWidget(self._load_btn)
        preview_buttons_frame.setLayout(self._preview_buttons_frame_lyt)

        info_layout.addLayout(title_layout)
        info_layout.addWidget(icon_toggle_box)
        info_layout.addWidget(info_toggle_box)
        info_layout.addWidget(version_toggle_box)

        tabs_widget.addTab(info_widget, 'Info')
        if self._options_widget:
            tabs_widget.addTab(self._options_widget, 'Options')

        self.main_layout.addWidget(tabs_widget)
        self.main_layout.addWidget(dividers.Divider())
        self.main_layout.addWidget(preview_buttons_frame)
        self.main_layout.addItem(QSpacerItem(0, 250, QSizePolicy.Preferred, QSizePolicy.Expanding))

    def setup_signals(self):

        self._info_toggle_box_btn.clicked.connect(self.save_settings)
        self._info_toggle_box_btn.toggled[bool].connect(self._info_toggle_box_frame.setVisible)
        self._icon_toggle_box_btn.clicked.connect(self.save_settings)
        self._icon_toggle_box_btn.toggled[bool].connect(self._icon_toggle_box_frame.setVisible)
        self._version_toggle_box_btn.clicked.connect(self.save_settings)
        self._version_toggle_box_btn.toggled[bool].connect(self._version_toggle_box_frame.setVisible)
        self._load_btn.clicked.connect(self.load)

    def resizeEvent(self, event):
        """
        Function that overrides base.BaseWidget function
        :param event: QSizeEvent
        """

        self.update_thumbnail_size()

    def set_item(self, item):
        """
        Sets the library item to load
        :param item: LibraryItem
        """

        super(LoadWidget, self).set_item(item)

        self._title_lbl.setText(item.MenuName)
        self._icon_lbl.setPixmap(QPixmap(item.type_icon_path()))

        info_widget = formwidget.FormWidget(self)
        info_widget.set_schema(item.info())
        self._info_frame.layout().addWidget(info_widget)

        self.refresh()

    def load_btn(self):
        """
        Returns button that loads the data
        :return: QPushButton
        """

        return self._load_btn

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

    def refresh(self):
        """
        Refreshes load widgetz
        """

        self.update_history()
        self.update_options()

    def update_history(self):
        """
        Updates history version of the current selected item
        """

        if not self._item:
            return

        data_object = self._item.data_object()
        if not data_object:
            return

        self._history_widget.set_directory(data_object.directory)
        self._history_widget.refresh()

    def update_options(self):
        """
        Updates options widget
        """

        if not self._options_widget:
            return

        if not self._item:
            return

        data_object = self._item.data_object()
        if not data_object:
            return

        self._options_widget.set_data_object(data_object)

    def is_editable(self):
        """
        Returns whether the user can edit the item or not
        :return: bool
        """

        item = self.item()
        editable = True

        if item and item.library_window():
            editable = not item.library_window().is_locked()

        return editable

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
        if path and os.path.exists(path):
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

    def settings(self):
        """
        Returns the current state of the widget
        :return: dict
        """

        settings = dict()

        settings['iconToggleBoxChecked'] = self._icon_toggle_box_btn.isChecked()
        settings['infoToggleBoxChecked'] = self._info_toggle_box_btn.isChecked()
        settings['versionToggleBoxChecked'] = self._version_toggle_box_btn.isChecked()

        return settings

    def save_settings(self):
        pass

    def load_settings(self):
        pass

    def load(self):
        """
        Loads current item
        """

        if not self.item():
            return

        self.item().load_from_current_options()
