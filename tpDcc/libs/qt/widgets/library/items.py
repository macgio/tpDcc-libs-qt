#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains library item widget implementation
"""

from __future__ import print_function, division, absolute_import

import os
import math
import shutil
import tempfile
import traceback
from datetime import datetime
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc as tp
from tpDcc.core import consts as dcc_consts

from tpDcc.libs.python import decorators, timedate, fileio, path as path_utils, folder as folder_utils

from tpDcc.libs import qt
from tpDcc.libs.qt.core import image, qtutils
from tpDcc.libs.qt.widgets import messagebox
from tpDcc.libs.qt.widgets.library import consts, savewidget, loadwidget, exceptions, utils

if tp.is_maya():
    from tpDcc.dccs.maya.core import decorators as maya_decorators
    show_wait_cursor_decorator = maya_decorators.show_wait_cursor
else:
    show_wait_cursor_decorator = decorators.empty_decorator


class GlobalSignals(QObject, object):
    blendChanged = Signal(float)


class LibraryItem(QTreeWidgetItem, object):
    """
    Stores information to work on Library views
    """

    SortRole = consts.ITEM_DEFAULT_SORT_ROLE
    DataRole = consts.ITEM_DEFAULT_DATA_ROLE

    ThreadPool = QThreadPool()

    MAX_ICON_SIZE = consts.ITEM_DEFAULT_MAX_ICON_SIZE
    DEFAULT_FONT_SIZE = consts.ITEM_DEFAULT_FONT_SIZE
    DEFAULT_PLAYHEAD_COLOR = consts.ITEM_DEFAULT_PLAYHEAD_COLOR

    DEFAULT_THUMBNAIL_COLUMN = consts.ITEM_DEFAULT_THUMBNAIL_COLUMN
    ENABLE_THUMBNAIL_THREAD = consts.ITEM_DEFAULT_ENABLE_THUMBNAIL_THREAD

    _globalSignals = GlobalSignals()
    blendChanged = _globalSignals.blendChanged

    EnableDelete = consts.ITEM_DEFAULT_ENABLE_DELETE
    EnableNestedItems = consts.ITEM_DEFAULT_ENABLE_NESTED_ITEMS

    DataType = None
    Extension = consts.ITEM_DEFAULT_EXTENSION
    Extensions = list()

    MenuName = consts.ITEM_DEFAULT_MENU_NAME
    MenuOrder = consts.ITEM_DEFAULT_MENU_ORDER
    MenuIconName = consts.ITEM_DEFAULT_MENU_ICON

    RegisterOrder = 10
    TypeIconName = ''
    DisplayInSidebar = False
    DefaultThumbnailName = 'thumbnail.png'
    CreateWidgetClass = savewidget.SaveWidget
    PreviewWidgetClass = loadwidget.LoadWidget

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

        self._metadata = None
        self._type_pixmap = None
        self._modal = None
        self._library = None
        self._library_window = None
        self._type_icon_path = tp.ResourcesMgr().get('icons', self.TypeIconName)
        self._menu_icon_path = tp.ResourcesMgr().get('icons', self.MenuIconName)
        self._default_thumbnail_path = tp.ResourcesMgr().get('icons', self.DefaultThumbnailName)

        super(LibraryItem, self).__init__(*args)

        self._worker = image.ImageWorker()
        self._worker.setAutoDelete(False)
        self._worker.signals.triggered.connect(self._on_thumbnail_from_image)
        self._worker_started = False

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
            action_icon = tp.ResourcesMgr().icon(cls.MenuIconName)
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

        settings = library_window.settings()

        widget = cls.CreateWidgetClass(item=cls(), settings=settings, parent=library_window)
        widget.set_library_window(library_window)
        library_window.set_create_widget(widget)

    @classmethod
    def match(cls, path):
        """
        Returns whether the given path locations is supported by the item
        :param path: str
        :return: bool
        """

        for ext in cls.Extensions:
            if path.endswith(ext):
                return True

        return False

    @decorators.abstractmethod
    def context_menu(self, menu):
        """
        Returns the context menu for the item
        This function MUST be implemented in subclass to return a custom context menu for the item
        :return: QMenu
        """

        raise NotImplementedError('LibraryItem context_menu() not implemented!')

    """
    ##########################################################################################
    OVERRIDES
    ##########################################################################################
    """

    def sizeHint(self, column=0):
        """
        Returns the current size of the item
        :param column: int
        :return: QSize
        """

        if self.stretch_to_widget():
            if self._size:
                size = self._size
            else:
                size = self.viewer().icon_size()
            w = self.stretch_to_widget().width()
            h = size.height()
            return QSize(w - 20, h)

        if self._size:
            return self._size
        else:
            icon_size = self.viewer().icon_size()
            if self.is_text_visible():
                w = icon_size.width()
                h = icon_size.width() + self.text_height()
                icon_size = QSize(w, h)

            return icon_size

    def setHidden(self, value):
        """
        Overrides base QTreeWidgetItem.setHidden function
        Set the item hidden
        :param value: bool
        """

        super(LibraryItem, self).setHidden(value)
        row = self.treeWidget().index_from_item(self).row()
        self.viewer().list_view().setRowHidden(row, value)

    def backgroundColor(self):
        """
        Returns the background color for the item
        :return: QColor
        """

        return self.viewer().background_color()

    def icon(self, column):
        """
        Overrides base QTreeWidgetItem icon function
        Overrides icon to add support for thumbnail icon
        :param column: int
        :return: QIcon
        """

        ic = QTreeWidgetItem.icon(self, column)
        if not ic and column == self.DEFAULT_THUMBNAIL_COLUMN:
            ic = self.thumbnail_icon()

        return ic

    def setIcon(self, column, icon, color=None):
        """
        Overrides base QTreeWidgetItem setIcon function
        :param column: int or str
        :param icon: QIcon
        :param color: QColor or None
        """

        is_app_running = bool(QApplication.instance())
        if not is_app_running:
            return

        if isinstance(icon, (str, unicode)):
            if not os.path.exists(icon):
                color = color or QColor(255, 255, 255, 20)
                icon = tp.ResourcesMgr().icon('image', color=color)
            else:
                icon = QIcon(icon)
        if isinstance(column, (str, unicode)):
            self._icon[column] = icon
        else:
            self._pixmap[column] = None
            super(LibraryItem, self).setIcon(column, icon)

        self.update_icon()

    def setFont(self, column, font):
        """
        Overrides base QTreeWidgetItem setFont function
        Sets the font for the given column
        :param column: int
        :param font: QFont
        """

        self._fonts[column] = font

    def textAlignment(self, column):
        """
        Returns the text alinment for the label in the given column
        :param column: int
        :return: QAlignmentFlag
        """

        if self.viewer().is_icon_view():
            return Qt.AlignCenter
        else:
            return QTreeWidgetItem.textAlignment(self, column)

    """
    ##########################################################################################
    BASE
    ##########################################################################################
    """

    def id(self):
        """
        Returns the unique id for the item
        :return: str
        """

        return self.path()

    def name(self):
        """
        Returns text for the name column
        :return: str
        """

        return self.item_data().get('name')

    def set_name(self, text):
        """
        Sets the name that is shown under the icon and in the name column
        :param text: str
        """

        item_data = self.item_data()
        item_data['icon'] = text
        item_data['name'] = text

    def display_text(self, label):
        """
        Returns the sort dat afor the given column
        :param label: str
        :return: str
        """

        return str(self.item_data().get(label, ''))

    def sort_text(self, label):
        """
        Returns the sort data for the given column
        :param label: str
        :return: str
        """

        return str(self.item_data().get(label, ''))

    def dirname(self):
        """
        Returns item directory name
        :return: str
        """

        return os.path.dirname(self.path())

    def extension(self):
        """
        Returns item file extension
        :return: str
        """

        _, extension = os.path.splitext(self.path())
        return extension

    def exists(self):
        """
        Returns whether item exists in disk or not
        :return: bool
        """

        return os.path.exists(self.path())

    def mtime(self):
        """
        Returns mtime of the item file
        :return: str
        """

        return os.path.getmtime(self.path())

    def ctime(self):
        """
        Returns when the item was created
        :return: int
        """

        if not os.path.exists(self.path()):
            return None

        return int(os.path.getctime(self.path()))

    def move(self, target):
        """
        Moves the current item to the given destination
        :param target: str
        """

        self.rename(target)

    def rename(self, target, extension=None, rename_file=False):
        """
        Renames the current path to the give destination path
        :param target: str
        :param extension: bool or None
        :param rename_file: bool or None
        """

        library = self.library()
        if not library:
            qt.logger.error('Impossible to rename item because library is not defined!')
            return

        source = self.path()
        self.library().rename_item(self, target, extension)

        self.renamed.emit(self, source, target)

    def copy(self, target):
        """
        Makes a copy/duplicate the current item to the given destination
        :param target: str
        """

        source = self.path()
        target = utils.copy_path(source, target)
        if self.library():
            self.library().copy_path(source, target)
        self.copied.emit(self, source, target)
        if self.library_window():
            self.library_window().refresh()

    def delete(self):
        """
        Deletes the item from disk and the library model
        """

        utils.remove_path(self.path())
        if self.library():
            self.library().remove_path(self.path())
        self.deleted.emit(self)

    def stretch_to_widget(self):
        """
        Returns the stretch to widget widget
        :return: QWidget
        """

        return self._stretch_to_widget

    def set_stretch_to_widget(self, widget):
        """
        Sets the width of the item to the width of the given widget
        :param widget: QWidget
        """

        self._stretch_to_widget = widget

    def set_size(self, size):
        """
        Sets the size for the item
        :param size: QSize
        """

        self._size = size

    def pixmap(self, column):
        """
        Returns the pixmap for the given column
        :param column: int
        :return: QPixmap
        """

        if not self._pixmap.get(column):
            icon = self.icon(column)
            if icon:
                size = QSize(self.MAX_ICON_SIZE, self.MAX_ICON_SIZE)
                icon_size = icon.actualSize(size)
                self._pixmap[column] = icon.pixmap(icon_size)

        return self._pixmap.get(column)

    def set_pixmap(self, column, pixmap):
        """
        Sets the pixmap to be displayed in the given column
        :param column: int
        :param pixmap: QPixmap
        """

        self._pixmap[column] = pixmap

    def take_from_tree(self):
        """
        Takes this item from the tree
        """

        tree = self.treeWidget()
        parent = self.parent()
        if parent:
            parent.takeChild(parent.indexOfChild(self))
        else:
            tree.takeTopLevelItem(tree.indexOfTopLevelItem(self))

    def group_item(self):
        """
        Returns current group item
        :return: LibraryGroupItem
        """

        return self._group_item

    def set_group_item(self, group_item):
        """
        Sets current group item
        :param group_item: LibraryGroupItem
        """

        self._group_item = group_item

    def info(self):
        """
        Returns the info to display to the user
        :return: list(dict)
        """

        return list()

    def show_in_folder(self):
        """
        Opens folder in OS folder explorer where file is located
        """

        path = self.path()
        if not os.path.isdir(path):
            return

        folder_utils.open_folder(path)

    """
    ##########################################################################################
    MOUSE/KEYBOARD
    ##########################################################################################
    """

    def under_mouse(self):
        """
        Returns whether the items is under the mouse cursor or not
        :return: bool
        """

        return self._under_mouse

    def context_menu(self, menu):
        """
        Returns the context menu for the item
        This function must be implemented in a subclass to return a custom context menu for the item
        :param menu: QMenu
        """

        pass

    def drop_event(self, event):
        """
        Reimplement in subclass to receive drop items for the item
        :param event: QDropEvent
        """

        pass

    def mouse_enter_event(self, event):
        """
        Reimplement in subclass to receive mouse enter events for the item
        :param event: QMouseEvent
        """

        self._under_mouse = True
        self.play()

    def mouse_leave_event(self, event):
        """
        Reimplement in subclass to receive mouse leave events for the item
        :param event: QMouseEvent
        """

        self._under_mouse = False
        self.stop()

    def mouse_move_event(self, event):
        """
        Reimplement in subclass to receive mouse move events for the item
        :param event: QMouseEvent
        """

        self.blending_event(event)
        self.image_sequence_event(event)

    def mouse_press_event(self, event):
        """
        Reimplement in subclass to receive mouse press events for the item
        :param event: QMouseEvent
        """

        if event.button() == Qt.MidButton:
            self._blend_position = event.pos()

    def mouse_release_event(self, event):
        """
        Reimplement in subclass to receive mouse release events for the item
        :param event: QMouseEvent
        """

        if self.is_blending():
            self._blend_position = None
            self._blend_prev_value = self.blend_value()

    def key_press_event(self, event):
        """
        Reimplement in subclass to receive key press events for the item
        :param event: QKeyEvent
        """

        pass

    def key_release_event(self, event):
        """
        Reimplement in subclass to receive key release events for the item
        :param event: QKeyEvent
        """

        pass

    def clicked(self):
        """
        Triggered when an item is clicked
        """

        pass

    def double_clicked(self):
        """
        Triggered when an item is double clicked
        """

        self.load_from_current_options()

    def selection_changed(self):
        """
        Triggered when an item has been either selected or deselected
        """

        self.reset_blending()

    """
    ##########################################################################################
    LIBRARY
    ##########################################################################################
    """

    def library_window(self):
        """
        Returns the library widget containing the item
        :return: LibraryWindow
        """

        return self._library_window

    def set_library_window(self, library_window):
        """
        Sets the library widget containing the item
        :param library_window: LibraryWindow
        """

        self._library_window = library_window

    def library(self):
        """
        Returns the library model for the item
        :return: Library
        """

        if not self._library and self.library_window():
            return self.library_window().library()

        return self._library

    def set_library(self, library):
        """
        Sets the library model for the item
        :param library: Library
        """

        self._library = library

    def path(self):
        """
        Returns the path for the item
        :return: str
        """

        return self._path

    def set_path(self, path):
        """
        Sets the path location on disk for the item
        :param path: str
        """

        if not path:
            raise exceptions.ItemError('Cannot set an empty item path')

        self.reset_image_sequence()

        path = path_utils.normalize_path(path)
        self._path = path

        self.update_item_data()

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

    def mime_text(self):
        """
        Returns the mime text for drag and drop
        :return: str
        """

        if self.path():
            file_path = path_utils.clean_path(os.path.join(self.path(), self.name()))
            if not os.path.isfile(file_path):
                file_path = self.path()
            return file_path

        return self._mime_text or self.text(0)

    def set_mime_text(self, text):
        """
        Sets the mime text for drag and drop
        :param text: str

        """

        self._mime_text = text

    def url(self):
        """
        Used by the mime data when dragging/droping the item
        :return: Qurl
        """

        if self.path():
            file_path = path_utils.clean_path(os.path.join(self.path(), self.name()))
            if not os.path.isfile(file_path):
                file_path = self.path()
            return QUrl('file:///{}'.format(file_path))

        if not self._url:
            self._url = QUrl(self.text(0))

        return self._url

    def set_url(self, url):
        """
        Sets the url object of the current item
        :param url: QUrl or None
        """

        self._url = url

    """
    ##########################################################################################
    ORDER STORAGE
    ##########################################################################################
    """

    def item_data(self):
        """
        Returns the current item data
        :return: dict
        """

        return self._item_data

    def set_item_data(self, data):
        """
        Sets the given dictionary as teh data for the item
        :param data: dict
        """

        self._item_data = data

    def create_item_data(self):
        """
        Creates item data
        """

        path = self.path()
        dirname, basename, extension = path_utils.split_path(path)
        name = os.path.basename(path)
        category = os.path.basename(dirname)

        item_data = {
            'name': name,
            'path': path,
            'type': extension,
            'folder': dirname,
            'category': category
        }

        return item_data

    def update_item_data(self):
        """
        Updates item data
        """

        item_data = self.create_item_data()
        self.set_item_data(item_data)

    def save_item_data(self):
        """
        Syncs the item data to the library
        """

        self.update_item_data()
        if self.library():
            self.library().update_item(self)

    """
    ##########################################################################################
    SEARCH
    ##########################################################################################
    """

    def search_text(self):
        """
        Returns the search string used for finding the item
        :return: str
        """

        if not self._search_text:
            self._search_text = str(self._data)

        return self._search_text

    """
    ##########################################################################################
    METADATA
    ##########################################################################################
    """

    def metadata(self):
        """
        Returns the metadata for the given item
        :return: dict
        """

        return self._metadata

    def set_metadata(self, metadata):
        """
        Sets the given metadata for the item
        :param metadata: dict
        """

        self._metadata = metadata

    """
    ##########################################################################################
    TREE WIDGET
    ##########################################################################################
    """

    def column_from_label(self, label):
        """
        Returns column fro mlabel
        :param label: str
        :return: str
        """

        if self.treeWidget():
            return self.treeWidget().column_from_label(label)

        return None

    def label_from_column(self, column):
        """
        Returns label of the given column
        :param column: int
        :return: str
        """

        if self.treeWidget():
            return self.treeWidget().label_from_column(column)

        return None

    """
    ##########################################################################################
    VIEWER WIDGET
    ##########################################################################################
    """

    def viewer(self):
        """
        Returns the viewer widget that contains the item
        :return: libraryViewer
        """

        viewer_widget = None
        if self.treeWidget():
            viewer_widget = self.treeWidget().parent()

        return viewer_widget

    def dpi(self):
        """
        Return current dpi
        :return: int
        """

        if self.viewer():
            return self.viewer().dpi()

        return 1

    def padding(self):
        """
        Returns the padding/border size for the item
        :return: int
        """

        return self.viewer().padding()

    def text_height(self):
        """
        Retuns the heigh of the text for the item
        :return: int
        """

        return self.viewer().item_text_height()

    def is_text_visible(self):
        """
        Retursn whether the text is visible or not
        :return: bool
        """

        return self.viewer().is_item_text_visible()

    """
    ##########################################################################################
    PREVIEW WIDGET
    ##########################################################################################
    """

    def preview_widget(self, library_window):
        """
        Returns the widget to be shown when the user clicks on the item
        :param library_window: LibraryWindow
        :return: QWidget or None
        """

        widget = None

        if self.PreviewWidgetClass:
            widget = self.PreviewWidgetClass(item=self)

        return widget

    def show_preview_widget(self, library_window):
        """
        Shows the preview widget for the item instance
        :param library_window: LibraryWindow
        """

        widget = self.preview_widget(library_window)
        library_window.set_preview_widget(widget)

    """
    ##########################################################################################
    THUMBNAIL
    ##########################################################################################
    """

    def type_icon_path(self):
        """
        Returns the type icon path on disk
        :return: str
        """

        return self._type_icon_path

    def thumbnail_path(self):
        """
        Return the thumbnail path for the item on disk
        :return: str
        """

        if not self.path():
            return self._default_thumbnail_path

        thumbnail_path = self.path() + '/thumbnail.jpg'
        if os.path.exists(thumbnail_path):
            return thumbnail_path

        thumbnail_path = thumbnail_path.replace('.jpg', '.png')
        if os.path.exists(thumbnail_path):
            return thumbnail_path

        return self._default_thumbnail_path

    """
    ##########################################################################################
    LOAD/SAVE
    ##########################################################################################
    """

    def write(self, path, *args, **kwargs):
        """
        Writes the item IO data to the given path
        :param path: str
        :param args: list
        :param kwargs: kwargs
        """

        raise NotImplementedError('write method for {} has not been implemented!'.format(self.__class__.__name__))

    def load(self, *args, **kwargs):
        """
        This function MUST be reimplemented to load any item data
        :param args: list
        :param kwargs: dict
        """

        qt.logger.debug('Loading "{}"'.format(self.name()))
        qt.logger.debug('Loading kwargs {}'.format(kwargs))
        self.loaded.emit(self)

    @show_wait_cursor_decorator
    def save(self, path=None, *args, **kwargs):
        """
        Saves current item
        :param path:
        :param args:
        :param kwargs:
        :return:
        """

        path = path or self.path()
        if path and not path.endswith(self.Extension):
            extension = self.Extension if self.Extension.startswith('.') else '.{}'.format(self.Extension)
            path += extension

        self.set_path(path)

        qt.logger.debug('Item Saving: {}'.format(path))
        self.saving.emit(self)

        if os.path.exists(path):
            self.show_already_existing_dialog()

        temp_path = tempfile.mkdtemp()
        if not os.path.isdir(temp_path):
            os.mkdir(temp_path)
        valid_save = self.write(temp_path, *args, **kwargs)
        if not valid_save:
            qt.logger.warning('Item {} not saved!'.format(path))
            if self.library_window():
                self.library_window().show_warning_message('Item {} not saved!'.format(path))
            if os.path.isdir(temp_path):
                folder_utils.delete_folder(temp_path)
            return False

        new_path = os.path.join(os.path.dirname(path), self.name())
        if not os.path.isdir(new_path):
            shutil.move(temp_path, new_path)
        else:
            folder_utils.move_folder(temp_path, new_path, only_contents=True)
            folder_utils.delete_folder(temp_path)

        self.set_path(new_path)
        self.save_item_data()

        comment = kwargs.get('comment', None)
        self.save_version(new_path, comment)

        if self.library_window():
            self.library_window().select_items([self])

        self.saved.emit(self)
        qt.logger.debug('Item Saved: {}'.format(self.path()))

        return True

    def save_version(self, path, comment):
        """
        Function that creates a new version of the item data
        :param path: str
        :param comment: str
        """

        version = fileio.FileVersion(os.path.join(path, self.name()))
        if not comment:
            comment = qtutils.get_comment()
            if not comment:
                comment = '-'
        version.save(comment)

    """
    ##########################################################################################
    DIALOGS
    ##########################################################################################
    """

    def show_toast_message(self, text):
        """
        Function that shows the toast widget with the given text
        :param text: str
        """

        if self.library_window():
            self.library_window().show_toast_message(text)

    def show_error_dialog(self, title, text):
        """
        Function that shows an error dialog to the user
        :param title: str
        :param text: str
        :return: QMessageBox.StandardButton or None
        """

        if self.library_window():
            self.library_window().show_error_message(text)

        btn = None
        if not self._modal:
            self._modal = True
            try:
                btn = messagebox.MessageBox.critical(self.library_window(), title, text)
            finally:
                self._modal = False

        return btn

    def show_exception_dialog(self, title, error, exception):
        """
        Function that shows a question dialog to the user
        :param title: str
        :param error: str
        :param exception: str
        """

        qt.logger.exception(exception)
        return self.show_error_dialog(title, error)

    def show_question_dialog(self, title, text):
        """
        Function that shows a question dialog to the user
        :param title: str
        :param text: str
        :return: QMessageBox.StandardButton
        """

        return messagebox.MessageBox.question(self.library_window(), title, text)

    def show_rename_dialog(self, parent=None):
        """
        Shows the rename dialog
        :param parent: QWidget
        """

        select = False
        if self.library_window():
            parent = parent or self.library_window()
            select = self.library_window().selected_folder_path() == self.path()

        name, btn = messagebox.MessageBox.input(
            parent, 'Rename item', 'Rename the current item to:', input_text=self.name())
        if btn == QDialogButtonBox.Ok:
            try:
                self.rename(name)
                if select:
                    self.library_window().select_folder_path(self.path())
            except Exception as e:
                self.show_exception_dialog('Rename Error', e, traceback.format_exc())
                raise

        return btn

    def show_move_dialog(self, parent=None):
        """
        Shows the move to browser dialog
        :param parent: QWidget
        """

        path = os.path.dirname(self.dirname())
        target = QFileDialog.getExistingDirectory(parent, 'Move To ...', path)
        if target:
            try:
                self.move(target)
            except Exception as e:
                self.show_exception_dialog('Move Error', e, traceback.format_exc())
                raise

    def show_delete_dialog(self):
        """
        Shows the delete item dialog
        """

        btn = self.show_question_dialog('Delete Item', 'Are you sure you want to delete this item?')
        if btn == QDialogButtonBox.Yes:
            try:
                self.delete()
            except Exception as e:
                self.show_exception_dialog('Delete Error', e, traceback.format_exc())
                raise

    def show_already_existing_dialog(self):
        """
        Shows a warning dialog if the item already exists on save
        """

        if not self.library_window():
            raise exceptions.ItemSaveError('Item already exists!')

        path = self.path()
        buttons = QMessageBox.Yes | QMessageBox.Cancel

        try:
            QApplication.setOverrideCursor(Qt.ArrowCursor)
            btn = self.library_window().show_question_dialog(
                'Item already exists',
                'Would you like to move the existing item "{}" to trash?'.format(self.name()), buttons
            )
        finally:
            QApplication.restoreOverrideCursor()

        if btn == QMessageBox.Yes:
            library = self.library()
            item = LibraryItem(path=path, library=library)
            self.library_window().move_items_to_trash([item])
            self.set_path(path)
        else:
            raise exceptions.ItemSaveError('You cannot save over an existing item.')

        return btn

    """
    ##########################################################################################
    SCHEMA
    ##########################################################################################
    """

    def current_load_value(self, name):
        """
        Returns the current filed value for the given name
        :param name: str
        :return: variant
        """

        return self._current_load_values.get(name, None)

    def save_schema(self):
        """
        Returns the schema used for saving the item
        :return: dict
        """

        return list()

    def load_schema(self):
        """
        Gets the options used to load the item
        :return: list(dict)
        """

        return list()

    def save_validator(self, **fields):
        """
        Validates the given save fields
        :param fields: dict
        :return: list(dict)
        """

        return list()

    def load_validator(self, **options):
        """
        Validates the current load options
        :param options: dict
        :return: list(dict)
        """

        return list()

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

        if not path:
            return

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

    def update_icon(self):
        """
        Clears the pixmap cache for the item
        """

        self.clear_cache()

    def clear_cache(self):
        """
        Clears the thumbnail cache
        """

        self._pixmap = dict()
        self._pixmap_rect = None
        self._pixmap_scaled = None
        self._thumbnail_icon = None

    def update(self):
        """
        Refresh teh visual state of the icon
        """

        self.update_icon()
        self.update_frame()

    def image_sequence_event(self, event):
        """
        :param event: QEvent
        """

        if self.image_sequence():
            if qtutils.is_control_modifier():
                if self.rect():
                    x = event.pos().x() - self.rect().x()
                    width = self.rect().width()
                    percent = 1.0 - (float(width - x) / float(width))
                    frame = int(self.image_sequence().frameCount() * percent)
                    self.image_sequence().jumpToFrame(frame)
                    self.update_frame()

    # ============================================================================================================
    # THUMBNAIL
    # ============================================================================================================

    def default_thumbnail_path(self):
        """
        Returns the default thumbnail path
        :return: str
        """
        return self._default_thumbnail_path

    def default_thumbnail_icon(self):
        """
        Returns the default thumbnail icon
        :return: QIcon
        """

        return QIcon(self.default_thumbnail_path())

    def thumbnail_icon(self):
        """
        Returns the thumbnail icon
        :return: QIcon
        """

        thumbnail_path = self.thumbnail_path()
        if not self._thumbnail_icon:
            if self.ENABLE_THUMBNAIL_THREAD and not self._worker_started:
                self._worker_started = True
                self._worker.set_path(thumbnail_path)
                self.ThreadPool.start(self._worker)
                self._thumbnail_icon = self.default_thumbnail_icon()
            else:
                self._thumbnail_icon = QIcon(thumbnail_path)

        return self._thumbnail_icon

    def _thumbnail_from_image(self, image):
        """
        Called after the given image object has finished loading
        :param image: QImage
        """

        self.clear_cache()
        pixmap = QPixmap()
        pixmap.convertFromImage(image)
        icon = QIcon(pixmap)
        self._thumbnail_icon = icon
        if self.viewer():
            self.viewer().update()

    # ============================================================================================================
    # PAINT
    # ============================================================================================================

    def font_size(self):
        """
        Returns the font size for the item
        :return: int
        """

        return self.DEFAULT_FONT_SIZE

    def font(self, column):
        """
        Returns the font for the given column
        :param column: int
        :return: QFont
        """

        default = QTreeWidgetItem.font(self, column)
        font = self._fonts.get(column, default)
        font.setPixelSize(self.font_size() * self.dpi())
        return font

    def text_width(self, column):
        """
        Returns the text width of the given column
        :param column: int
        :return: int
        """

        text = self.text(column)
        font = self.font(column)
        metrics = QFontMetrics(font)
        text_width = metrics.width(text)
        return text_width

    def text_color(self):
        """
        Returns the text color for the item
        :return: QColor
        """

        # TODO: change to use foreground role
        # return self.itemsWidget().palette().color(self.itemsWidget().foregroundRole())
        return self.viewer().text_color()

    def text_selected_color(self):
        """
        Returns the selected txt color for the item
        :return: QColor
        """

        return self.viewer().text_selected_color()

    def background_hover_color(self):
        """
        Returns the background color when the mouse is over the item
        :return: QColor
        """

        return self.viewer().background_hover_color()

    def background_selected_color(self):
        """
        Returns the background color when the item is selected
        :return: QColor
        """

        return self.viewer().background_selected_color()

    def rect(self):
        """
        Returns the rect for the current paint frame
        :return: QRect
        """

        return self._rect

    def set_rect(self, rect):
        """
        Sets the rect for the current paint frame
        :param rect: QRect
        """

        self._rect = rect

    def visualRect(self, option):
        """
        Returns the visual rect for the item
        :param option: QStyleOptionViewItem
        :return: QRect
        """

        rect = QRect(option.rect)
        return rect

    def paint_row(self, painter, option, index):
        """
        Paint performs low-level painting for the item
        :param painter: QPainter
        :param option: QStyleOptionViewItem
        :param index: QModelIndex
        """

        QTreeWidget.drawRow(self.treeWidget(), painter, option, index)

    def paint(self, painter, option, index):
        """
        Paint performs low-level painting for the item
        :param painter: QPainter
        :param option: QStyleOptionViewItem
        :param index: QModelIndex
        """

        self.set_rect(QRect(option.rect))
        painter.save()
        try:
            self.paint_background(painter, option, index)
            if self.is_text_visible():
                self.paint_text(painter, option, index)
            self.paint_icon(painter, option, index)
            if index.column() == 0:
                if self.image_sequence():
                    self.paint_playhead(painter, option)
        finally:
            painter.restore()

    def paint_background(self, painter, option, index):
        """
        Draw the background for the item
        :param painter: QPainter
        :param option: QStyleOptionViewItem
        :param index:QModelIndex
        """

        is_selected = option.state & QStyle.State_Selected
        is_mouse_over = option.state & QStyle.State_MouseOver
        painter.setPen(QPen(Qt.NoPen))
        visual_rect = self.visualRect(option)
        if is_selected:
            color = self.background_selected_color()
        elif is_mouse_over:
            color = self.background_hover_color()
        else:
            color = self.backgroundColor()
        painter.setBrush(QBrush(color))

        painter.drawRect(visual_rect)

    def icon_rect(self, option):
        """
        Returns the icon rect for the item
        :param option: QStyleOptionViewItem
        :return: QRect
        """

        padding = self.padding()
        rect = self.visualRect(option)
        width = rect.width()
        height = rect.height()
        if self.is_text_visible() and self.viewer().is_icon_view():
            height -= self.text_height()
        width -= padding
        height -= padding
        rect.setWidth(width)
        rect.setHeight(height)

        x = 0
        x += float(padding) / 2
        x += float((width - rect.width())) / 2

        y = float((height - rect.height())) / 2
        y += float(padding) / 2
        rect.translate(x, y)

        return rect

    def scale_pixmap(self, pixmap, rect):
        """
        Scale the given pixmap to given rect size
        The scaled pixmap is cached and its reused if its called with the same size
        :param pixmap: QPixmap
        :param rect: QRect
        :return: QPixmap
        """

        rect_changed = True

        if self._pixmap_rect:
            width_changed = self._pixmap_rect.width() != rect.width()
            height_changed = self._pixmap_rect.height() != rect.height()
            rect_changed = width_changed or height_changed

        if not self._pixmap_scaled or rect_changed:
            self._pixmap_scaled = pixmap.scaled(
                rect.width(), rect.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._pixmap_rect = rect

        return self._pixmap_scaled

    def paint_icon(self, painter, option, index, align=None):
        """
        Draws the icon for the item
        :param painter: QPainter
        :param option: QStyleOptionViewItem
        :param index: int
        :param align: Qt.Align
        """

        column = index.column()
        pixmap = self.pixmap(column)
        if not pixmap:
            return

        rect = self.icon_rect(option)
        pixmap = self.scale_pixmap(pixmap, rect)
        pixmap_rect = QRect(rect)
        pixmap_rect.setWidth(pixmap.width())
        pixmap_rect.setHeight(pixmap.height())

        x, y = 0, 0
        align = Qt.AlignHCenter | Qt.AlignVCenter
        align_bottom_a = Qt.AlignBottom | Qt.AlignLeft
        align_bottom_b = align == Qt.AlignBottom | Qt.AlignHCenter or align == Qt.AlignBottom | Qt.AlignRight
        align_h_center_a = Qt.AlignHCenter or align == Qt.AlignCenter
        align_h_center_b = align == Qt.AlignHCenter | Qt.AlignBottom or align == Qt.AlignHCenter | Qt.AlignTop
        align_v_center_a = align == Qt.AlignVCenter | Qt.AlignLeft or align == Qt.AlignVCenter | Qt.AlignRight
        align_v_center_b = Qt.AlignVCenter or align == Qt.AlignCenter

        is_align_bottom = align == align_bottom_a or align_bottom_b
        is_align_h_center = align == align_h_center_a or align_h_center_b
        is_align_v_center = align == align_v_center_a or align_v_center_b
        if is_align_h_center:
            x += float(rect.width() - pixmap.width()) / 2
        elif is_align_v_center:
            y += float(rect.height() - pixmap.height()) / 2
        elif is_align_bottom:
            y += float(rect.height() - pixmap.height()) / 2

        pixmap_rect.translate(x, y)
        painter.drawPixmap(pixmap_rect, pixmap)

    def draw_icon_border(self, painter, pixmap_rect):
        """
        Draws a border around the icon
        :param painter: QPainter
        :param pixmap_rect: QRect
        """

        pixmap_rect = QRect(pixmap_rect)
        pixmap_rect.setX(pixmap_rect.x() - 5)
        pixmap_rect.setY(pixmap_rect.y() - 5)
        pixmap_rect.setWidth(pixmap_rect.width() + 5)
        pixmap_rect.setHeight(pixmap_rect.height() + 5)
        color = QColor(255, 255, 255, 10)
        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(color))
        painter.drawRect(pixmap_rect)

    def paint_text(self, painter, option, index):
        """
        Draws the text for the item
        :param painter: QPainter
        :param option: QStyleOptionViewItem
        :param index: int
        """

        column = index.column()
        if column == 0 and self.viewer().is_table_view():
            return

        self._paint_text(painter, option, column)

    def _paint_text(self, painter, option, column):
        """
        Internal function used to paint the text
        :param painter: QPainter
        :param option: QStyleOption
        :param column: int
        """

        if self.viewer().is_icon_view():
            text = self.name()
        else:
            label = self.label_from_column(column)
            text = self.display_text(label)

        color = self.text_color()
        is_selected = option.state & QStyle.State_Selected
        if is_selected:
            color = self.text_selected_color()

        visual_rect = self.visualRect(option)
        width = visual_rect.width()
        height = visual_rect.height()
        padding = self.padding()
        x = padding / 2
        y = padding / 2
        visual_rect.translate(x, y)
        visual_rect.setWidth(width - padding)
        visual_rect.setHeight(height - padding)

        font = self.font(column)
        align = self.textAlignment(column)
        metrics = QFontMetrics(font)
        text_width = 1
        if text:
            text_width = metrics.width(text)
        if text_width > visual_rect.width() - padding:
            visual_width = visual_rect.width()
            text = metrics.elidedText(text, Qt.ElideRight, visual_width)
            align = Qt.AlignLeft
        if self.viewer().is_icon_view():
            align = align | Qt.AlignBottom
        else:
            align = align | Qt.AlignVCenter

        pen = QPen(color)
        painter.setPen(pen)
        painter.setFont(font)
        painter.drawText(visual_rect, align, text)

    # ============================================================================================================
    # BLENDING
    # ============================================================================================================

    def is_blending_enabled(self):
        """
        Returns whether blending is enabled or not
        :return: bool
        """

        return self._blending_enabled

    def set_blending_enabled(self, flag):
        """
        Sets whether blending is enabled or not
        :param flag: bool
        """

        self._blending_enabled = flag

    def is_blending(self):
        """
        Returns whether blending is playing or not
        :return: bool
        """

        return self.blend_position() is not None

    def blend_value(self):
        """
        Returns the curreent blend value
        :return: float
        """

        return self._blend_value

    def set_blend_value(self, blend):
        """
        Sets the current blend value
        :param blend: float
        """

        if self.is_blending_enabled():
            self._blend_value = blend
            self.blendChanged.emit(blend)

    def blend_previous_value(self):
        """
        Returns the blend previous current value
        :return: float
        """

        return self._blend_prev_value

    def blend_position(self):
        """
        Returns current blend position
        :return: QPoint
        """

        return self._blend_position

    def blending_event(self, event):
        """
        Function that is called when the mouse moves while the middle mouse button is held down
        :param event: QMouseEvent
        """

        if self.is_blending():
            value = math.ceil((event.pos().x() - self.blend_position().x()) * 1.5) + self.blend_previous_value()
            try:
                self.set_blend_value(value)
            except Exception:
                self.stop_blending()

    def start_blending_event(self, event):
        """
        Called when the middle mouse button is pressed
        :param event: QMouseEvent
        """

        if self.is_blending_enabled():
            if event.button() == Qt.MidButton:
                self._blend_position = event.pos()

    def stop_blending(self):
        """
        Called when the middle mouse button is released
        :return: QMouseEvent
        """

        self._blend_position = None
        self._blend_prev_value = self.blend_value()

    def reset_blending(self):
        """
        Resets the blending value to zero
        """

        self._blend_value = 0.0
        self._blend_prev_value = 0.09

    # ============================================================================================================
    # CONTEXTUAL MENUS
    # ============================================================================================================

    def context_edit_menu(self, menu, items=None):
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

        rename_action.triggered.connect(self._on_show_rename_dialog)
        move_to_action.triggered.connect(self._on_move_dialog)
        show_in_folder_action.triggered.connect(self._on_show_in_folder)
        copy_path_action.triggered.connect(self._on_copy_path)

        menu.addAction(rename_action)
        menu.addAction(move_to_action)
        menu.addAction(show_in_folder_action)
        menu.addAction(copy_path_action)

        if self.library_window():
            select_folder_action = QAction('Select Folder', menu)
            select_folder_action.triggered.connect(self._on_select_folder)
            menu.addAction(select_folder_action)

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_thumbnail_from_image(self, image):
        """
        Internal callback function that is called when an image object has finished loading
        """

        self.clear_cache()
        pixmap = QPixmap()
        pixmap.convertFromImage(image)
        icon = QIcon(pixmap)
        self._thumbnail_icon = icon
        if self.viewer():
            self.viewer().update()

    def _on_frame_changed(self, frame):
        """
        Internal callback function that is triggered when the movei object updates to the given
        frame
        :return:
        """

        if not qtutils.is_control_modifier():
            self.update_frame()

    def _on_show_rename_dialog(self):
        self.show_rename_dialog()

    def _on_show_delete_dialog(self):
        pass

    def _on_move_dialog(self):
        pass

    def _on_show_in_folder(self):
        """
        Internal callback function that is called when Show in Folder action is clicked
        """

        self.show_in_folder()

    def _on_copy_path(self):
        pass

    def _on_select_folder(self):
        """
        Internal callback function that is triggered when Select Folder action is clicked
        """

        if self.library_window():
            path = '/'.join(path_utils.normalize_path(self.path()).split('/')[:-1])
            self.library_window().select_folder_path(path)


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

    def textAlignment(self, column):
        """
        Overrides base LibraryItem textAlignment function
        :param column: int
        """

        return QTreeWidgetItem.textAlignment(self, column)

    def sizeHint(self, column=0):
        """
        Overrides base sizeHint textAlignment function
        Returns the size hint of the item
        :param column: int
        :return: QSize
        """

        width = self.viewer().width() - 20
        return QSize(width, 40 * self.dpi())

    def visualRect(self, option):
        """
        Overrides base sizeHint visualRect function
        Returns the visual rect for the item
        :param option: QStyleOptionViewItem
        :return: QRect
        """
        rect = QRect(option.rect)
        rect.setX(10 * self.dpi())
        rect.setWidth(self.sizeHint().width())
        return rect

    def backgroundColor(self):
        """
        Overrides base sizeHint backgroundColor function
        Return the background color for the item.
        :rtype: QtWidgets.QtColor
        """
        return QColor(0, 0, 0, 0)

    def icon(*args):
        """
        Overrides base sizeHint icon function
        Overrided so icon is not displayed
        :param args:
        :return:
        """
        return None

    def paint_row(self, painter, option, index):
        """
        Overrides base paint_row icon function
        Paint performs low-level painting for the item
        :param painter: QPainter
        :param option: QStyleOptionViewItem
        :param index: QModelIndex
        """

        self.set_rect(QRect(option.rect()))
        painter.save()
        try:
            pass
            # self.paint_background(painter, option, index)
            # if self.is_text_visible():
            #     self._paint_text(painter, option, 1)
            # self.paint_icon(painter, option, index)
        finally:
            painter.restore()

    def paint_background(self, painter, option, index):
        """
        Overrides base paint_background icon function
        Draw the background for the item
        :param painter: QPainter
        :param option: QStyleOptionViewItem
        :param index: QModelIndex
        """

        super(LibraryGroupItem, self).paint_background(painter, option, index)

        painter.setPen(QPen(Qt.NoPen))
        visual_rect = self.visualRect(option)
        text = self.name()
        metrics = QFontMetrics(self._font)
        text_width = metrics.width(text)
        padding = (25 * self.dpi())
        visual_rect.setX(text_width + padding)
        visual_rect.setY(visual_rect.y() + (visual_rect.height() / 2))
        visual_rect.setHeight(2 * self.dpi())
        visual_rect.setWidth(visual_rect.width() - padding)

        color = QColor(self.text_color().red(), self.text_color().green(), self.text_color().blue(), 10)
        painter.setBrush(QBrush(color))
        painter.drawRect(visual_rect)

    def children(self):
        """
        Returns the children for the group
        :return: list(LibraryItem)
        """

        return self._children

    def set_children(self, children):
        """
        Sets the children for the group
        :param children: list(LibraryItem)
        """

        self._children = children

    def children_hidden(self):
        """
        Returns whether childrens are hidden or not
        :return: bool
        """

        for child in self.children():
            if not child.isHidden():
                return False

        return True

    def update_children(self):
        """
        Updates the visibility if all children are hidden
        :return:
        """

        self.setHidden(self.children_hidden())

    def is_text_visible(self):
        """
        Returns whether the text is visible or not
        :return: bool
        """

        return True

    def text_selected_color(self):
        """
        Returns the selected text color for the item
        :return: QColor
        """

        return self.viewer().text_color()

    def background_hover_color(self):
        """
        Return the background color when the mouse is over the item.
        :rtype: QtWidgets.QtColor
        """
        return QColor(0, 0, 0, 0)

    def background_selected_color(self):
        """
        Return the background color when the item is selected.
        :rtype: QtWidgets.QtColor
        """
        return QColor(0, 0, 0, 0)


class LibraryFolderItem(LibraryItem, object):

    RegisterOrder = 100
    EnableNestedItems = True
    DisplayInSidebar = True

    MenuName = 'Folder'
    MenuOrder = 1
    MenuIconName = 'folder.png'
    DefaultThumbnailName = 'folder.png'
    TrashIconName = 'trash.png'

    def __init__(self, path='', library=None, library_window=None, *args):
        self._trash_icon_path = tp.ResourcesMgr().get('icons', self.TrashIconName)

        super(LibraryFolderItem, self).__init__(path=path, library=library, library_window=library_window, *args)

    @classmethod
    def match(cls, path):
        """
        Returns whether the given path is supported by the item or not
        :param path: str
        :return: bool
        """

        if os.path.isdir(path):
            return True

        return False

    @classmethod
    def show_create_widget(cls, library_window):
        """
        Shows the dialog for creating a new folder
        :param library_window: LibraryWindow
        """

        path = library_window.selected_folder_path() or library_window.path()
        name, btn = messagebox.MessageBox.input(library_window, 'Create folder', 'Create a new folder with the name:')
        name = name.strip()
        if name and btn == QDialogButtonBox.Ok:
            path = os.path.join(path, name)
            item = cls(path, library_window=library_window)
            item.save(path)
            if library_window:
                library_window.refresh()
                library_window.select_folder_path(path)

    def save_version(self, path, comment):
        """
        Overrides base save_version function
        When creating folders we do not create any kind of version
        :param path: str
        :param comment: str
        """

        return

    def info(self):
        """
        Returns the info to display to the user
        :return: list(dict)
        """

        created = os.stat(self.path()).st_ctime
        created = datetime.fromtimestamp(created).strftime("%Y-%m-%d %H:%M %p")
        modified = os.stat(self.path()).st_mtime
        modified = datetime.fromtimestamp(modified).strftime("%Y-%m-%d %H:%M %p")

        return [
            {
                "name": "name",
                "value": self.name()
            },
            {
                "name": "path",
                "value": self.path()
            },
            {
                "name": "created",
                "value": created,
            },
            {
                "name": "modified",
                "value": modified,
            }
        ]

    def double_clicked(self):
        """
        Overrides this method to show the items contained in the folder
        """

        self.library_window().select_folder_path(self.path())

    def write(self, path, *args, **kwargs):
        """
        Overrides function to avoid not implemented exception
        :param path: str
        :param args: list
        :param kwargs: dict
        """

        return True

    def create_item_data(self):
        """
        Overrides this function to force the item type to Folder
        """

        item_data = super(LibraryFolderItem, self).create_item_data()
        item_data['type'] = 'Folder'
        return item_data

    def item_data(self):
        """
        Overrides this function to set the trash icon
        :return: dict
        """

        data = super(LibraryFolderItem, self).item_data()
        if data.get('path').endswith('Trash'):
            data['iconPath'] = self._trash_icon_path

        return data


class NamespaceOption(object):
    FromFile = 'file'
    FromCustom = 'custom'
    FromSelection = 'selection'


class BaseItem(LibraryItem, object):
    def __init__(self, *args, **kwargs):
        super(BaseItem, self).__init__(*args, **kwargs)

        self._current_load_values = dict()
        self._current_load_schema = list()
        self._current_save_schema = list()

        self._namespaces = list()
        self._namespace_options = NamespaceOption.FromSelection

        self._transfer_class = None
        self._transfer_object = None
        self._transfer_basename = None

        # In standard files we only use the data JSON to store properties of the file
        # We can use transfer object to store other data in specific situations
        self.set_transfer_class(utils.TransferObject)
        self.set_transfer_basename(dcc_consts.DATA_FILE)

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def load(self, objects=None, namespaces=None, **kwargs):
        """
        Loads the data from the transfer object
        :param objects: list(str) or None
        :param namespaces: list(str) or None
        :param kwargs: dict
        """

        qt.logger.debug('Loading: {}'.format(self.transfer_path()))
        self.transfer_object().load(objects=objects, namespaces=namespaces, **kwargs)
        qt.logger.debug('Loaded: {}'.format(self.transfer_path()))

        return True

    def save(self, path=None, *args, **kwargs):
        """
        Saves current item
        :param path:
        :param args:
        :param kwargs:
        :return:
        """

        valid_save = super(BaseItem, self).save(path=path, *args, **kwargs)
        if not valid_save:
            transfer_path = self.transfer_path()
            if os.path.isfile(transfer_path):
                folder_utils.delete_folder(os.path.dirname(transfer_path))
            return False

        return True

    def write(self, path, objects, icon_path='', sequence_path='', **options):
        """
        Writes all the given object data to the given path on disk
        This function just setup the basic setup prior or doing the write, overrides
        this function in custom items to implement the write functionality
        :param path: str
        :param objects: list(str)
        :param icon_path: str
        :param sequence_path: str
        :param options: dict
        """

        # if icon_path:
        #     base_name = os.path.basename(icon_path)
        #     shutil.copy(icon_path, path + '/' + base_name)

        if icon_path:
            shutil.copyfile(icon_path, path + '/thumbnail.jpg')
        if sequence_path:
            shutil.move(sequence_path, path + '/sequence')

        objects = objects or list()
        self.transfer_object().add(objects)

        return True

    def load_validator(self, **options):
        """
        Validates the current load options
        :param options: dict
        :return: list(dict)
        """

        self._current_load_values = options

    def save_validator(self, **fields):
        """
        Validates the given save fields
        :param fields: dict
        :return: list(dict)
        """

        self._current_save_schema = fields

        selection = tp.Dcc.selected_nodes(full_path=True) or list()
        count = len(selection)
        plural = 's' if count > 1 else ''
        msg = '{} object{} selected for saving'.format(count, plural)

        return [
            {
                'name': 'contains',
                'value': msg
            }
        ]

    def save_schema(self):
        """
        Returns the schema used for saving the item
        :return: dict
        """

        return [
            {
                'name': 'name',
                'type': 'string',
                'layout': 'vertical'
            },
            {
                'name': 'comment',
                'type': 'text',
                'layout': 'vertical'
            },
            {
                'name': 'contains',
                'type': 'label',
                'label': {'visible': False}
            }
        ]

    def info(self):
        """
        Returns the info to display to the user
        :return: list(dict)
        """

        ctime = self.ctime()
        if ctime:
            ctime = timedate.time_ago(ctime)

        count = self.object_count()
        plural = 's' if count > 1 else ''
        contains = str(count) + ' Object' + plural

        return [
            {
                'name': 'name',
                'value': self.name()
            },
            {
                "name": "owner",
                "value": self.owner(),
            },
            {
                "name": "created",
                "value": ctime,
            },
            {
                "name": "contains",
                "value": contains,
            },
            {
                "name": "comment",
                "value": self.description() or "No comment",
            },
        ]

    # ============================================================================================================
    # LOAD/SAVE
    # ============================================================================================================

    def load_from_current_options(self):
        """
        Loads the data of the item
        """

        kwargs = self.options_from_settings()
        namespaces = self.namespaces()
        objects = tp.Dcc.selected_nodes(full_path=False) or list()

        try:
            self.load(objects=objects, namespaces=namespaces, **kwargs)
        except Exception as e:
            self.show_error_dialog('Item Error', str(e))
            raise

    # ============================================================================================================
    # SCHEMA
    # ============================================================================================================

    def settings(self):
        """
        Returns tpRigBuilder library settings file
        :return: JSONSettings
        """

        raise NotImplementedError('settings function bor BaseItem not implemented!')

    def default_options(self):
        """
        Returns default options
        :return: dict
        """

        options = dict()
        for option in self.load_schema():
            options[option.get('name')] = option.get('default')

        return options

    def options_from_settings(self):
        """
        Returns the options from the user settings
        :return: dict
        """

        settings = self.settings()
        settings = settings.get(self.__class__.__name__, {})
        options = settings.get('loadOptions', {})
        default_options = self.default_options()

        if options:
            for option in self.load_schema():
                name = option.get('name')
                persistent = option.get('persistent')
                if not persistent and name in options:
                    options[name] = default_options[name]

        return options

    def current_load_value(self, name):
        """
        Returns the current filed value for the given name
        :param name: str
        :return: variant
        """

        return self._current_load_values.get(name, None)

    def current_load_schema(self):
        """
        Returns the current options ste by the user
        :return: dict
        """

        return self._current_load_schema or self.options_from_settings()

    # ============================================================================================================
    # ITEM PROPERTIES
    # ============================================================================================================

    def transfer_class(self):
        """
        Returns the transfer class used to read and write data
        :return: TransferObject
        """

        return self._transfer_class

    def set_transfer_class(self, class_name):
        """
        Sets the transfer class used to read and write the data
        :param class_name: TransferObject
        """

        self._transfer_class = class_name

    def transfer_basename(self):
        """
        Returns the filename of the transfer path
        :return: str
        """

        return self._transfer_basename

    def set_transfer_basename(self, transfer_basename):
        """
        Sets the filename of the transfer path
        :param transfer_basename: str
        """

        self._transfer_basename = transfer_basename

    def transfer_path(self):
        """
        Returns the disk location to transfer path
        :return: str
        """

        if self.transfer_basename():
            return os.path.join(self.path(), self.transfer_basename())
        else:
            return self.path()

    def transfer_object(self):
        """
        Returns the transfer object used to read and write the data
        :return: TransferObject
        """

        if not self._transfer_object:
            path = self.transfer_path()
            force_creation = bool(os.path.isfile(path))
            self._transfer_object = self.transfer_class().from_path(path, force_creation=force_creation)

        return self._transfer_object

    def owner(self):
        """
        Returns the user who created this item
        :return: str or None
        """

        transfer_object = self.transfer_object()
        if not transfer_object:
            return 'Unknown'

        return transfer_object.metadata().get('user', 'Unknown')

    def description(self):
        """
        Returns the user description for this item
        :return: str
        """

        transfer_object = self.transfer_object()
        if not transfer_object:
            return ''

        return transfer_object.metadata().get('description', '')

    def object_count(self):
        """
        Returns the number of objects this item contains
        :return: int
        """

        transfer_object = self.transfer_object()
        if not transfer_object:
            return 0

        return transfer_object.count()

    # ============================================================================================================
    # SCENE
    # ============================================================================================================

    def namespaces(self):
        """
        Returns the namespaces for this item depending on the namespace option
        :return: list(str)
        """

        return list()
