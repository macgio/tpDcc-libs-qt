#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains library item widget implementation
"""

from __future__ import print_function, division, absolute_import

import os
from functools import partial

from tpQtLib.Qt.QtCore import *
from tpQtLib.Qt.QtWidgets import *
from tpQtLib.Qt.QtGui import *

from tpPyUtils import decorators, path as path_utils

from tpQtLib.core import image, qtutils
from tpQtLib.widgets.library import consts, exceptions


class LibraryItem(QTreeWidgetItem, object):
    """
    Stores information to work on Library views
    """

    SortRole = consts.ITEM_DEFAULT_SORT_ROLE
    DataRole = consts.ITEM_DEFAULT_DATA_ROLE

    ThreadPool = QThreadPool()
    DefaultThumbnailPath = consts.ITEM_DEFAULT_THUMBNAIL_PATH

    MAX_ICON_SIZE = consts.ITEM_DEFAULT_MAX_ICON_SIZE
    DEFAULT_FONT_SIZE = consts.ITEM_DEFAULT_FONT_SIZE
    DEFAULT_PLAYHEAD_COLOR = consts.ITEM_DEFAULT_PLAYHEAD_COLOR

    DEFAULT_THUMBNAIL_COLUMN = consts.ITEM_DEFAULT_THUMBNAIL_COLUMN
    ENABLE_THUMBNAIL_THREAD = consts.ITEM_DEFAULT_ENABLE_THUMBNAIL_THREAD

    EnableDelete = consts.ITEM_DEFAULT_ENABLE_DELETE
    EnableNestedItems = consts.ITEM_DEFAULT_ENABLE_NESTED_ITEMS

    MenuName = consts.ITEM_DEFAULT_MENU_NAME
    MenuOrder = consts.ITEM_DEFAULT_MENU_ORDER
    MenuIconPath = consts.ITEM_DEFAULT_MENU_ICON_PATH

    CreateWidgetClass = None
    PreviewWidgetClass = None

    _libraryItemSignals = consts.LibraryItemSignals()
    saved = _libraryItemSignals.saved
    saving = _libraryItemSignals.saving
    loaded = _libraryItemSignals.loaded
    copied = _libraryItemSignals.copied
    renamed = _libraryItemSignals.renamed
    deleted = _libraryItemSignals.deleted

    def __init__(self, path='', library=None, library_window=None, *args):

        self._url = None
        self._path = None
        self._size = None
        self._rect = None
        self._text_column_order = list()

        self._data = dict()
        self._item_data = dict()

        self._icon = dict()
        self._icon_path = None
        self._thumbnail_icon = None
        self._fonts = dict()
        self._thread = None
        self._pixmap = dict()
        self._pixmap_rect = None
        self._pixmap_scaled = None
        self._image_sequence = None
        self._image_sequence_path = None

        self._mime_text = None
        self._drag_enabled = True

        self._under_mouse = False
        self._search_text = None
        self._info_widget = None

        self._group_item = None
        self._group_column = 0

        self._viewer = None
        self._stretch_to_widget = None

        self._blend_value = 0.0
        self._blend_prev_value = 0.0
        self._blend_position = None
        self._blending_enabled = False

        self._worker = image.ImageWorker()
        self._worker.setAutoDelete(False)
        self._worker.signals.triggered.connect(self._on_thumbnail_from_image)
        self._worker_started = False

        self._library = None
        self._library_window = library_window

        super(LibraryItem, self).__init__(*args)

        if library_window:
            self.set_library_window(library_window)

        if library:
            self.set_library(library)

        if path:
            self.set_path(path)

    def __eq__(self, other):
        return id(other) == id(self)

    def __ne__(self, other):
        return id(other) != id(self)

    def __del__(self):
        """
        When the object is deleted we make sure the sequence is stopped
        """

        self.stop()

    """
    ##########################################################################################
    CLASS METHODS
    ##########################################################################################
    """

    @classmethod
    def create_action(cls, menu, library_window):
        """
        Returns the action to be displayed when the user clicks the "plus" icon
        :param menu: QMenu
        :param library_window: LibraryWindow
        :return: QAction
        """

        if cls.MenuName:
            action_icon = QIcon(cls.MenuIconPath)
            callback = partial(cls.show_create_widget, library_window)
            action = QAction(action_icon, cls.MenuName, menu)
            action.triggered.connect(callback)

            return action

    @classmethod
    def show_create_widget(cls, library_window):
        """
        Shows the create widget for creating a new item
        :param library_window: LibraryWindow
        """

        widget = cls.CreateWidgetClass()
        library_window.set_create_widget(widget)

    @decorators.abstractmethod
    def context_menu(self):
        """
        Returns the context men ufor the item
        This function MUST be implemented in subclass to return a custom context menu for the item
        :return: QMenu
        """

        raise NotImplementedError('LibraryItem context_menu() not implemented!')

    """
    ##########################################################################################
    LIBRARY
    ##########################################################################################
    """

    def set_library_window(self, library_window):
        """
        Sets the library widget containing the item
        :param library_window: LibraryWindow
        """

        self._library_window = library_window

    def set_library(self, library):
        """
        Sets the library model for the item
        :param library: Library
        """

        self._library = library

    def set_path(self, path):
        """
        Sets the path location on disk for the item
        :param path: str
        """

        if not path:
            raise exceptions.ItemError('Cannot set an empty item path')

        path = path_utils.normalize_path(path)
        self._path = path

    """
    ##########################################################################################
    DRAG & DROP
    ##########################################################################################
    """

    def drag_enabled(self):
        """
        Return whether the item can be dragged or not
        :return: bool
        """

        return self._drag_enabled

    def set_drag_enabled(self, flag):
        """
        Set whether item can be dragged or not
        :param flag: bool
        """

        self._drag_enabled = flag

    """
    ##########################################################################################
    ORDER STORAGE
    ##########################################################################################
    """

    def item_data(self, column_labels):
        """
        Returns all column data for the given column labels
        :param column_labels: list(str)
        :return: dict
        """

        data = dict()
        for item in self.items():
            key = item.id()
            for column_label in column_labels:
                column = self.treeWidget().column_from_label(column_label)
                value = item.data(column, Qt.EditRole)
                data.setdefault(key, dict())
                data[key].setdefault(column_label, value)

        return data

    def set_item_data(self, data):
        """
        Sets the item data for all the curren items
        :param data: dict
        """

        for item in self.items():
            key = item.id()
            if key in data:
                item.set_item_data(data[key])

    def update_columns(self):
        """
        Updates the columns labels with the curren item data
        """

        self.treeWidget().update_header_labels()

    def column_labels(self):
        """
        Returns all the column labels
        :return: list(str)
        """

        return self.treeWidget().column_labels()

    """
    ##########################################################################################
    THUMBNAIL
    ##########################################################################################
    """

    def thumbnail_path(self):
        """
        Return the thumbnail path for the item on disk
        :return: str
        """

        return ''

    """
    ##########################################################################################
    SEQUENCE
    ##########################################################################################
    """

    def image_sequence(self):
        """
        Return ImageSequence of the item
        :return: image.ImageSequence or QMovie
        """

        return self._image_sequence

    def set_image_sequence(self, image_sequence):
        """
        Set the image sequence of the item
        :param image_sequence: image.ImageSequence or QMovie
        """

        self._image_sequence = image_sequence

    def image_sequence_path(self):
        """
        Return the path where image sequence is located on disk
        :return: str
        """

        return self._image_sequence_path

    def set_image_sequence_path(self, path):
        """
        Set the path where image sequence is located on disk
        :param path: str
        """

        self._image_sequence_path = path

    def reset_image_sequence(self):
        """
        Reset image sequence
        """

        self._image_sequence = None

    def play(self):
        """
        Start play image sequence
        """

        self.reset_image_sequence()
        path = self.image_sequence_path() or self.thumbnail_path()
        movie = None

        if os.path.isfile(path) and path.lower().endswith('.gif'):
            movie = QMovie(path)
            movie.setCacheMode(QMovie.CacheAll)
            movie.frameChanged.connect(self._on_frame_changed)
        elif os.path.isdir(path):
            if not self.image_sequence():
                movie = image.ImageSequence(path)
                movie.frameChanged.connect(self._on_frame_changed)

        if movie:
            self.set_image_sequence(movie)
            self.image_sequence().start()

    def update_frame(self):
        """
        Function that updates the current frame
        """

        if self.image_sequence():
            pixmap = self.image_sequence().current_pixmap()
            self.setIcon(0, pixmap)

    def stop(self):
        """
        Stop play image sequence
        """

        if self.image_sequence():
            self.image_sequence().stop()

    def playhead_color(self):
        """
        Returns playehad color
        :return: QColor
        """

        return self.DEFAULT_PLAYHEAD_COLOR

    def paint_playhead(self, painter, option):
        """
        Pain the playhead if the item has an image sequence
        :param painter: QPainter
        :param option: QStyleOptionViewItem
        """

        image_sequence = self.image_sequence()
        if image_sequence and self.under_mouse():
            count = image_sequence.frame_count()
            current = image_sequence.current_frame_number()
            if count > 0:
                percent = float((count + current) + 1) / count - 1
            else:
                percent = 0

            r = self.icon_rect(option)
            c = self.playhead_color()

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(c))

            if percent <= 0:
                width = 0
            elif percent >= 1:
                width = r.width()
            else:
                width = (percent * r.width()) - 1

            height = 3 * self.dpi()
            y = r.y() + r.height() - (height - 1)

            painter.drawRect(r.x(), y, width, height)


    """
    ##########################################################################################
    CONTEXTUAL MENUS
    ##########################################################################################
    """

    def _context_edit_menu(self, menu, items=None):
        """
        This function is called when the user opens context menu
        The given menu is shown as a submenu of the main context menu
        This function can be override to create custom context menus in LibraryItems
        :param menu: QMenu
        :param items: list(LibraryItem)
        """

        if self.EnableDelete:
            delete_action = QAction('Delete', menu)
            delete_action.triggered.connect(self._on_show_delete_dialog)
            menu.addAction(delete_action)
            menu.addSeparator()

        rename_action = QAction('Rename', menu)
        move_to_action = QAction('Move to', menu)
        show_in_folder_action = QAction('Show in Folder', menu)
        copy_path_action = QAction('Copy Path', menu)

        rename_action.triggered.connect(self._on_show_delete_dialog)
        move_to_action.triggered.connect(self._on_move_dialog)
        show_in_folder_action.triggerered.connect(self._on_show_in_folder)
        copy_path_action.triggered.connect(self._on_copy_path)

        menu.addAction(rename_action)
        menu.addAction(move_to_action)
        menu.addAction(show_in_folder_action)
        menu.addAction(copy_path_action)

    """
    ##########################################################################################
    CALLBACKS
    ##########################################################################################
    """

    def _on_thumbnail_from_image(self):
        pass

    def _on_frame_changed(self, frame):
        """
        Internal callback function that is triggered when the movei object updates to the given
        frame
        :return:
        """

        if not qtutils.is_control_modifier():
            self.update_frame()

    def _on_show_delete_dialog(self):
        pass

    def _on_show_delete_dialog(self):
        pass

    def _on_move_dialog(self):
        pass

    def _on_show_in_folder(self):
        pass

    def _on_copy_path(self):
        pass


class LibraryGroupItem(LibraryItem, object):
    """
    Class that defines group of items
    """

    DEFAULT_FONT_SIZE = consts.GROUP_ITEM_DEFAULT_FONT_SIZE

    def __init__(self, *args):
        super(LibraryGroupItem, self).__init__(*args)

        self._children = list()

        self._font = self.font(0)
        self._font.setBold(True)

        self.setFont(0, self._font)
        self.setFont(1, self._font)
        self.set_drag_enabled(False)