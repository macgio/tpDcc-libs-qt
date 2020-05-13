#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains main window widget used in libraries
"""

from __future__ import print_function, division, absolute_import

import os
import re
import time
import operator
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc as tp
from tpDcc.libs.python import decorators, path as path_utils
from tpDcc.libs import qt
from tpDcc.libs.qt.core import base, icon, menu, qtutils, animation, window
from tpDcc.libs.qt.widgets import stack, messagebox, action
from tpDcc.libs.qt.widgets.library import consts, utils, library, viewer, widgets

if tp.is_maya():
    from tpDcc.dccs.maya.core import decorators as maya_decorators
    show_wait_cursor_decorator = maya_decorators.show_wait_cursor
    show_arrow_cursor_decorator = maya_decorators.show_arrow_cursor
else:
    show_wait_cursor_decorator = decorators.empty_decorator
    show_arrow_cursor_decorator = decorators.empty_decorator


class GlobalSignal(QObject):
    """
    Signals that are triggered by all library instances
    """

    debugModeChanged = Signal(object, object)
    folderSelectionChanged = Signal(object, object)


class PreviewFrame(QFrame):
    pass


class SidebarFrame(QFrame):
    pass


class LibraryWindow(window.BaseWindow, object):
    LIBRARY_CLASS = library.Library
    VIEWER_CLASS = viewer.LibraryViewer
    SEARCH_WIDGET_CLASS = widgets.LibrarySearchWidget
    STATUS_WIDGET_CLASS = widgets.LibraryStatusWidget
    MENUBAR_WIDGET_CLASS = widgets.LibraryToolbarWidget
    SIDEBAR_WIDGET_CLASS = widgets.LibrarySidebarWidget
    SORTBY_MENU_CLASS = widgets.SortByMenu
    GROUPBY_MENU_CLASS = widgets.GroupByMenu
    FILTERBY_MENU_CLASS = widgets.FilterByMenu
    PROGRESS_BAR_VISIBLE = consts.PROGRESS_BAR_VISIBLE

    globalSignal = GlobalSignal()
    loaded = Signal()
    lockChanged = Signal(object)
    debugModeChanged = Signal(object)
    itemRenamed = Signal(str, str)
    itemSelectionChanged = Signal(object)
    folderRenamed = Signal(str, str)
    folderSelectionChanged = Signal(object)

    def __init__(self, parent=None, name='', path='', library_icon_path=None, allow_non_path=False, **kwargs):

        self._items = list()
        self._name = name or consts.LIBRARY_DEFAULT_NAME
        self._is_debug = False
        self._is_locked = False
        self._preview_widget = None
        self._new_item_widget = None
        self._progress_bar = None
        self._current_item = None
        self._library = None
        self._refresh_enabled = False
        self._library_icon_path = library_icon_path
        self._allow_non_path = allow_non_path
        self._superusers = None
        self._lock_reg_exp = None
        self._unlock_reg_exp = None

        self._trash_enabled = consts.TRASH_ENABLED
        self._recursive_search_enabled = consts.DEFAULT_RECURSIVE_SEARCH_ENABLED

        self._items_hidden_count = 0
        self._items_visible_count = 0

        self._is_trash_folder_visible = False
        self._sidebar_widget_visible = True
        self._preview_widget_visible = True
        self._status_widget_visible = True
        self._new_item_widget_visible = False

        super(LibraryWindow, self).__init__(parent=parent)
        # super(LibraryWindow, self).__init__(name=name, parent=parent, show_dragger=False, auto_load=False, **kwargs)

        self.set_refresh_enabled(True)

        self.update_view_button()
        self.update_filters_button()
        self.update_preview_widget()

        if path:
            self.set_path(path)

    # ============================================================================================================
    # ABSTRACT
    # ============================================================================================================

    @decorators.abstractmethod
    def manager(self):
        """
        Returns library managed used by this window
        Must be implemented in child classes
        :return: LibraryManager
        """

        raise NotImplementedError('LibraryWindow manager() function is not implemented!')

    # ============================================================================================================
    # OVERLOADING FUNCTIONS
    # ============================================================================================================

    def ui(self):
        super(LibraryWindow, self).ui()

        self.setMinimumWidth(5)
        self.setMinimumHeight(5)

        self.stack = stack.SlidingStackedWidget()
        self.main_layout.addWidget(self.stack)

        lib = self.LIBRARY_CLASS(library_window=self)
        lib.dataChanged.connect(self.refresh)
        lib.searchTimeFinished.connect(self._on_search_finished)

        self._sidebar_frame = SidebarFrame(self)
        sidebar_frame_lyt = QVBoxLayout(self)
        sidebar_frame_lyt.setContentsMargins(0, 1, 0, 0)
        self._sidebar_frame.setLayout(sidebar_frame_lyt)

        self._new_item_frame = PreviewFrame(self)
        self._new_item_frame.setMinimumWidth(5)
        new_item_lyt = QVBoxLayout()
        new_item_lyt.setSpacing(0)
        new_item_lyt.setContentsMargins(0, 0, 0, 0)
        self._new_item_frame.setLayout(new_item_lyt)

        self._preview_frame = PreviewFrame(self)
        self._preview_frame.setMinimumWidth(5)
        preview_frame_lyt = QVBoxLayout()
        preview_frame_lyt.setSpacing(0)
        preview_frame_lyt.setContentsMargins(0, 0, 0, 0)
        self._preview_frame.setLayout(preview_frame_lyt)

        self._viewer = self.VIEWER_CLASS(self)
        self._viewer.setContextMenuPolicy(Qt.CustomContextMenu)

        self._sort_by_menu = self.SORTBY_MENU_CLASS(self)
        self._group_by_menu = self.GROUPBY_MENU_CLASS(self)
        self._filter_by_menu = self.FILTERBY_MENU_CLASS(self)
        self._status_widget = self.STATUS_WIDGET_CLASS(self)
        self._menubar_widget = self.MENUBAR_WIDGET_CLASS(self)

        self._sidebar_widget = self.SIDEBAR_WIDGET_CLASS(self)
        self._sidebar_widget.setContextMenuPolicy(Qt.CustomContextMenu)

        sidebar_frame_lyt.addWidget(self._sidebar_widget)

        self._search_widget = self.SEARCH_WIDGET_CLASS(self)

        self._splitter = QSplitter(Qt.Horizontal, self)
        self._splitter.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self._splitter.setHandleWidth(2)
        self._splitter.setChildrenCollapsible(False)

        self._splitter.addWidget(self._sidebar_frame)
        self._splitter.addWidget(self._viewer)
        self._splitter.addWidget(self._preview_frame)

        self._splitter.setStretchFactor(0, False)
        self._splitter.setStretchFactor(1, True)
        self._splitter.setStretchFactor(2, False)

        base_widget = QWidget()
        base_layout = QVBoxLayout()
        base_layout.setContentsMargins(0, 0, 0, 0)
        base_layout.setSpacing(0)
        base_widget.setLayout(base_layout)
        base_layout.addWidget(self._menubar_widget)
        base_layout.addWidget(self._splitter)
        base_layout.addWidget(self._status_widget)

        self.stack.addWidget(base_widget)
        self.stack.addWidget(self._new_item_frame)

        self._sort_by_menu.set_library(lib)
        self._group_by_menu.set_library(lib)
        self._filter_by_menu.set_library(lib)
        self._viewer.set_library(lib)
        self._search_widget.set_library(lib)
        self._sidebar_widget.set_library(lib)
        self.set_library(lib)

        self._setup_menubar()

    def setup_signals(self):
        self._viewer.setContextMenuPolicy(Qt.CustomContextMenu)
        self._viewer.itemMoved.connect(self._on_item_moved)
        self._viewer.itemDropped.connect(self._on_item_dropped)
        self._viewer.itemSelectionChanged.connect(self._on_item_selection_changed)
        self._viewer.customContextMenuRequested.connect(self._on_show_items_context_menu)

        self._sidebar_widget.itemDropped.connect(self._on_item_dropped)
        self._sidebar_widget.itemSelectionChanged.connect(self._on_folder_selection_changed)
        self._sidebar_widget.customContextMenuRequested.connect(self._on_show_folder_menu)

        self.folderSelectionChanged.connect(self.update_lock)

    def _setup_menubar(self):
        icon_color = self.icon_color()
        name = 'New Item'
        icon = tp.ResourcesMgr().icon('plus', theme='black')
        icon.set_color(icon_color)
        tip = 'Add a new item to the selected folder'
        self.add_menubar_action(name, icon, tip, callback=self._on_show_new_menu)

        self._menubar_widget.addWidget(self._search_widget)

        name = 'Filters'
        icon = tp.ResourcesMgr().icon('filter', theme='black')
        icon.set_color(icon_color)
        tip = 'Filter the current results by type.\nCtrl + Click will hide the ohters and show the selected one.'
        self.add_menubar_action(name, icon, tip, callback=self._on_show_filter_by_menu)

        name = 'Item View'
        icon = tp.ResourcesMgr().icon('slider', theme='black')
        icon.set_color(icon_color)
        tip = 'Change the style of the item view'
        self.add_menubar_action(name, icon, tip, callback=self._on_show_item_view_menu)

        name = 'Group By'
        icon = tp.ResourcesMgr().icon('grid_view', theme='black')
        icon.set_color(icon_color)
        tip = 'Group the current items in the view by column'
        self.add_menubar_action(name, icon, tip, callback=self._on_show_group_by_menu)

        name = 'Sort By'
        icon = tp.ResourcesMgr().icon('descending_sorting', theme='black')
        icon.set_color(icon_color)
        tip = 'Sort the current items in the view by column'
        self.add_menubar_action(name, icon, tip, callback=self._on_show_sort_by_menu)

        name = 'View'
        icon = tp.ResourcesMgr().icon('add')
        # icon.set_color(icon_color)
        tip = 'Choose to show/hide both the preview and navigation pane\nCtrl + click will hide the menu bar as well.'
        self.add_menubar_action(name, icon, tip, callback=self._on_toggle_view)

        name = 'Sync Items'
        icon = tp.ResourcesMgr().icon('sync', theme='black')
        icon.set_color(icon_color)
        tip = 'Sync with the filesystem'
        self.add_menubar_action(name, icon, tip, callback=self._on_sync)

        name = 'Settings'
        icon = tp.ResourcesMgr().icon('settings', theme='black')
        icon.set_color(icon_color)
        tip = 'Settings menu'
        self.add_menubar_action(name, icon, tip, callback=self._on_show_settings_menu)

    # def event(self, ev):
    #     """
    #     Overrides window.MainWindow event function
    #     :param ev: QEvent
    #     :return: QEvent
    #     """
    #
    #     if isinstance(ev, QKeyEvent):
    #         if qtutils.is_control_modifier() and ev.key() == Qt.Key_F:
    #             self.search_widget().setFocus()
    #
    #     if isinstance(ev, QStatusTipEvent):
    #         self.status_widget().show_info_message(ev.tip())
    #
    #     return super(LibraryWindow, self).event(ev)

    def keyReleaseEvent(self, event):
        """
        Overrides window.MainWindow keyReleaseEvent function
        :param event: QKeyEvent
        """

        for item in self.selected_items():
            item.key_release_event(event)
        super(LibraryWindow, self).keyReleaseEvent(event)

    def show(self, **kwargs):
        """
        Overrides window.MainWindow show function
        We always raise_ the widget on show
        Use **kwargs to set platform dependent show options used in subclasses
        :param kwargs:
        :return:
        """

        # super(LibraryWindow, self).show(self)
        super(LibraryWindow, self).show()
        self.setWindowState(Qt.WindowNoState)
        self.raise_()

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def library(self):
        """
        Returns muscle library
        :return: MuscleLibrary
        """

        return self._library

    def set_library(self, library):
        """
        Sets the muscle library
        :param library: MuscleLibrary
        """

        self._library = library

    def set_sizes(self, sizes):
        """
        Set sizes of window splitters
        :param sizes: list(int, int, int)
        """

        f_size, c_size, p_size = sizes
        p_size = p_size if p_size > 0 else 200
        f_size = f_size if f_size > 0 else 120
        self._splitter.setSizes([f_size, c_size, p_size])
        self._splitter.setStretchFactor(1, 1)

    def is_locked(self):
        """
        Returns whether the library is locked or not
        :return: bool
        """

        return self._is_locked

    def set_locked(self, flag):
        """
        Sets the state of the library to be editable or not
        :param flag: bool
        """

        self._is_locked = flag

        self.sidebar_widget().set_locked(flag)
        self.viewer().set_locked(flag)
        self.update_create_item_button()
        self.update_window_title()
        self.lockChanged.emit(flag)

    def superusers(self):
        """
        Returns the superusers for the window
        :return: list(str)
        """

        return self._superusers

    def set_superusers(self, superusers):
        """
        Sets the valid superusres for the library widget
        This will lock all folders unless the current user is a superuser
        :param superusers: list(str)
        """

        self._superusers = superusers
        self.update_lock()

    def lock_reg_exp(self):
        """
        Returns the lock regular expression used for locking the widget
        :return: str
        """

        return self._lock_reg_exp

    def set_lock_reg_exp(self, reg_exp):
        """
        Sets the lock regular expression used for locking the widget
        Locks only folders that contain the given regular expression in their path
        :param reg_exp: str
        """

        self._lock_reg_exp = reg_exp
        self.update_lock()

    def unlock_reg_exp(self):
        """
        Returns the unlock regular expression used for unlocking the widget
        :return: str
        """

        return self._unlock_reg_exp

    def set_unlock_reg_exp(self, reg_exp):
        """
        Sets the unlock regular expression used for locking the widget
        Unlocks only folders that contain the given regular expression in their path
        :param reg_exp: str
        """

        self._unlock_reg_exp = reg_exp
        self.update_lock()

    def is_lock_reg_exp_enabled(self):
        """
        Returns whether the lock regular expression or unlock regular expression has been set
        :return: bool
        """

        return not (self.superusers() is None and self.lock_reg_exp() is None and self.unlock_reg_exp() is None)

    def update_lock(self):
        """
        Updates the lock state for the library
        """

        if not self.is_lock_reg_exp_enabled():
            return

        superusers = self.superusers() or list()
        re_locked = re.compile(self.lock_reg_exp() or '')
        re_unlocked = re.compile(self.unlock_reg_exp() or '')

        print('Updating Lock ...')

    def is_refresh_enabled(self):
        """
        Returns whether refresh is enabled or not
        If not, all updates will be ignored
        :return: bool
        """

        return self._refresh_enabled

    def set_refresh_enabled(self, flag):
        """
        Whether widgets should be updated or not
        :param flag: bool
        """

        self.library().set_search_enabled(flag)
        self._refresh_enabled = flag

    def update(self):
        """
        Overrides base QMainWindow update function
        Update the library widget and the data
        """

        self.refresh_sidebar()
        self.update_window_title()

    def update_window_title(self):
        """
        Updates the window title
        """

        pass

    def name(self):
        """
        Return the name of the library
        :return: str
        """

        if not self._library:
            return

        return self._library.name()

    def path(self):
        """
        Returns the path being used by the library
        :return: str
        """

        if not self._library:
            return

        return self._library.path()

    def set_path(self, path):
        """
        Set the path being used by the library
        :param path: str
        """

        if path is None:
            path = ''
        else:
            path = path_utils.real_path(path)

        if path == self.path():
            qt.logger.warning('Path is already set!')
            return

        library = self.library()
        library.set_path(path)

        # if not os.path.exists(library.data_path()):
        #     library.sync()
        self.sync(force_start=True, force_searh=True)

        if self.stack.currentIndex() != 0:
            self.stack.slide_in_index(0)

        self.refresh()
        # self.library().search()
        self.update_preview_widget()

    def set_create_widget(self, create_widget):
        """
        Set the widget that should be showed when creating a new item
        :param create_widget: QWidget
        """

        if not create_widget:
            return

        self.set_new_item_widget_visible(True)
        # self.viewer().clear_selection()

        # fsize, rsize, psize = self._splitter.sizes()
        # if psize < 150:
        #     self.set_sizes((fsize, rsize, 180))

        # self.set_preview_widget(create_widget)
        self.set_new_item_widget(create_widget)
        self.stack.slide_in_index(1)

    def refresh(self):
        """
        Refresh all necessary items
        """

        if self.is_refresh_enabled():
            self.update()

    # ============================================================================================================
    # SETTINGS
    # ============================================================================================================

    # @show_wait_cursor_decorator
    # def load_settings(self):
    #     """
    #     Loads the user settings from disk
    #     """
    #
    #     self.reload_stylesheet()
    #     settings = self.read_settings()
    #     self.set_settings(settings)
    #
    # def read_settings(self):
    #     """
    #     Reads settings from dsik
    #     :return: dict
    #     """
    #
    #     key = self.name()
    #     return self.settings().get(key, {})
    #
    # def save_settings(self, settings=None):
    #     """
    #     Save the settings to the settings path
    #     :param settings: dict
    #     """
    #
    #     settings = settings or self.settings()
    #     key = self.name()
    #     self.show_toast_message('Saved')

    # def settings(self):
    #     """
    #     Return a dictionary with the widget settings
    #     :return: dict
    #     """
    #
    #     settings = dict()
    #
    #     settings['kwargs'] = self._kwargs
    #
    #     if self.theme():
    #         settings['theme'] = self.theme().settings()
    #
    #     settings['library'] = self.library().settings()
    #
    #     settings['viewerWidget'] = self.viewer().settings()
    #     settings['searchWidget'] = self.search_widget().settings()
    #     settings['sidebarWidget'] = self.sidebar_widget().settings()
    #
    #     settings['filterByMenu'] = self._filter_by_menu.settings()
    #
    #     settings['path'] = self.path()
    #
    #     return settings

    def save_settings(self, settings=None):

        settings = settings or self.settings()
        if not settings:
            return

        library_name = self.objectName().upper()
        self.settings().set('{}/path'.format(library_name), self.path())
        self.settings().set('{}/dpi'.format(library_name), self.dpi())
        self.settings().set('{}/panelSizes'.format(library_name), self._splitter.sizes())
        self.settings().set('{}/sidebarWidgetVisible'.format(library_name), self.is_sidebar_widget_visible())
        self.settings().set('{}/menuBarWidgetVisible'.format(library_name), self.is_menubar_widget_visible())
        self.settings().set('{}/previewWidgetVisible'.format(library_name), self.is_menubar_widget_visible())
        self.settings().set('{}/statusBarWidgetVisible'.format(library_name), self.is_menubar_widget_visible())
        self.settings().set('{}/searchWidget'.format(library_name), self.search_widget().settings())
        self.settings().set('{}/recursiveSearchEnabled'.format(library_name), self.is_recursive_search_enabled())
        self.settings().set('{}/filterByMenu'.format(library_name), self._filter_by_menu.settings())
        self.settings().set('{}/library'.format(library_name), self.library().settings())
        self.settings().set('{}/trashFolderVisible'.format(library_name), self.is_trash_folder_visible())
        self.settings().set('{}/viewerWidget'.format(library_name), self.viewer().settings())

    def set_settings(self, settings):
        """
        Set the library window settings from the given dictionary
        :param settings: dict
        """

        super(LibraryWindow, self).set_settings(settings)

        is_refresh_enabled = self.is_refresh_enabled()
        library_name = self.objectName().upper()

        try:
            self.set_refresh_enabled(False)
            self.viewer().set_toast_enabled(False)

            # if not self.path():
            #     path = self.settings().get('{}/path'.format(library_name))
            #     if path and os.path.exists(path):
            #         self.set_path(path)

            dpi = float(self.settings().get('{}/dpi'.format(library_name), 1.0))
            self.set_dpi(dpi)

            sizes = self.settings().get('{}/panelSizes'.format(library_name), [160, 280, 180])
            sizes = [int(i) for i in sizes]
            if sizes and len(sizes) == 3:
                self.set_sizes(sizes)

            sidebar_visible = bool(self.settings().get('{}/sidebarWidgetVisible'.format(library_name), True))
            if sidebar_visible:
                self.set_sidebar_widget_visible(sidebar_visible)

            menubar_visible = bool(self.settings().get('{}/menuBarWidgetVisible'.format(library_name), True))
            if menubar_visible:
                self.set_menubar_widget_visible(menubar_visible)

            preview_visible = bool(self.settings().get('{}/previewWidgetVisible'.format(library_name), True))
            if preview_visible:
                self.set_preview_widget_visible(preview_visible)

            status_visible = bool(self.settings().get('{}/statusBarWidgetVisible'.format(library_name), True))
            if status_visible:
                self.set_status_widget_visible(status_visible)

            search_widget = dict(self.settings().get('{}/searchWidget'.format(library_name), {'text': ''}))
            if search_widget:
                self.search_widget().set_settings(search_widget)

            recursive_search = bool(self.settings().get('{}/recursiveSearchEnabled'.format(library_name), True))
            if recursive_search:
                self.set_recursive_search_enabled(recursive_search)

            filter_by_menu = dict(self.settings().get('{}/filterByMenu'.format(library_name), {'Folder': False}))
            if filter_by_menu:
                self._filter_by_menu.set_settings(filter_by_menu)
        finally:
            self.reload_stylesheet()
            self.set_refresh_enabled(is_refresh_enabled)
            self.refresh()

        library_settings = dict(self.settings().get(
            '{}/library'.format(library_name), {'sortBy': ['name:asc'], 'groupBy': ['category:asc']}))
        if library_settings:
            self.library().set_settings(library_settings)

        trash_folder_visible = bool(self.settings().get(
            '{}/trashFolderVisible'.format(library_name), False))
        if trash_folder_visible:
            self.set_trash_folder_visible(trash_folder_visible)

        viewer_settings = dict(self.settings().get(
            '{}/viewerWidget'.format(library_name),
            {'spacing': 2, 'padding': 6, 'zoomAmount': 80, 'textVisible': True}))
        if viewer_settings:
            self.viewer().set_settings(viewer_settings)

        self.viewer().set_toast_enabled(True)

        self.update_filters_button()

    def update_settings(self, settings):
        """
        Save the given path to the settins on disk
        :param settings: dict
        """

        data = self.read_settings()
        data.update(settings)
        self.save_settings(data)

    def reset_settings(self):
        """
        Reset the settings to the default settings
        """

        self.set_settings(self.DEFAULT_SETTINGS)

    # ============================================================================================================
    # DRAG & DROP
    # ============================================================================================================

    def save_custom_order(self):
        """
        Function used for save the custom order
        """

        self.library().save_item_data(self.items(), emit_data_changed=True)

    def is_custom_order_enabled(self):
        """
        Returns whether custom order is enabled or not
        :return: bool
        """

        return 'Custom Order' in str(self.library().sort_by())

    def is_move_items_enabled(self):
        """
        Returns whether moving items via drag and drop is enabled or not
        :return: bool
        """

        paths = self.selected_folder_paths()
        if len(paths) != 1:
            return False
        if self.selected_items():
            return False

        return True

    def create_move_items_dialog(self):
        """
        Creates and returns a dialog for moving items
        :return: MessageBox
        """

        dlg = messagebox.create_message_box(
            self, 'Move or Copy Items?', 'Would you like to copy or move the selected item/s?')
        dlg.button_box().clear()
        dlg.add_button('Copy', QDialogButtonBox.AcceptRole)
        dlg.add_button('Move', QDialogButtonBox.AcceptRole)
        dlg.add_button('Cancel', QDialogButtonBox.RejectRole)

        return dlg

    def show_move_items_dialog(self, items, target_folder):
        """
        Shows the move items dialog for the given items
        :param items: list(LibraryItem)
        :param dst: target_folder
        """

        Copy = 0
        Cancel = 2

        for item in items:
            if item.dirname() == target_folder:
                return

        dlg = self.create_move_items_dialog()
        res = dlg.exec_()
        dlg.close()

        if res == Cancel:
            return

        copy = res == Copy

        self.move_items(items, target_folder, copy=copy)

    def move_items(self, items, target_folder, copy=False, force=False):
        """
        Moves the given items to the target folder path
        :param items: list(LibraryItem)
        :param target_folder: str
        :param copy: bool
        :param force: bool
        """

        self.viewer().clear_selection()
        moved_items = list()
        try:
            self.library().blockSignals(True)
            for item in items:
                path = target_folder + '/' + item.name()
                if force:
                    path = utils.generate_unique_path(path)
                if copy:
                    item.copy(path)
                else:
                    item.rename(path)
                moved_items.append(item)
        except Exception as e:
            self.show_exception_dialog('Move Error', e)
        finally:
            self.library().blockSignals(False)

            self.refresh()
            self.select_items(moved_items)
            self.scroll_to_selected_item()

    # ============================================================================================================
    # VIEWER WIDGET
    # ============================================================================================================

    def viewer(self):
        """
        Returns muscle viewer widget
        :return:
        """

        return self._viewer

    def add_item(self, item, select=False):
        """
        Add the given item to the viewer widget
        :param item: LibraryItem
        :param select: bool
        """

        self.add_items([item], select=select)

    def add_items(self, items, select=False):
        """
        Add the given items to the viewer widget
        :param items: list(LibraryItem)
        :param select: bool
        """

        self.viewer().add_items(items)
        self._items.extend(items)

        if select:
            self.select_Items(items)
            self.scroll_to_selected_item()

    def create_items_from_urls(self, urls):
        """
        Return a new list of items from the given urls
        :param urls: list(QUrl)
        :return: list(LibraryItem)
        """

        return self.manager().items_from_urls(urls, library_window=self)

    def items(self):
        """
        Return all the loaded items
        :return: list(LibraryItem)
        """

        return self._items

    def selected_items(self):
        """
        Return selected items
        :return: list(LibraryItem)
        """

        return self.viewer().selected_items()

    def select_path(self, path):
        """
        Select the item with the given path
        :param path: str
        """

        self.select_paths([path])

    def select_paths(self, paths):
        """
        Select the items with the given paths
        :param paths: list(str)
        """

        selection = self.selected_items()
        self.clear_preview_widget()
        self.viewer().clear_selection()
        self.viewer().select_paths(paths)

        if self.selected_items() != selection:
            self._on_item_selection_changed()

    def select_items(self, items):
        """
        Select the given items
        :param items: list(LibraryItem)
        :return:
        """

        paths = [item.path() for item in items]
        self.select_paths(paths)

    def scroll_to_selected_item(self):
        """
        Scroll the item widget to the selected item
        """

        self.viewer().scroll_to_selected_item()

    def refresh_selection(self):
        """
        Refresh teh current item selection
        """

        items = self.selected_items()
        self.viewer().clear_selection()
        self.select_items(items)

    def clear_items(self):
        """
        Remove all the loaded items
        """

        self.viewer().clear()

    # ============================================================================================================
    # MENUBAR WIDGET
    # ============================================================================================================

    def menubar_widget(self):
        """
        Returns menu bar widget
        :return: LibraryMenuBarWidget
        """

        return self._menubar_widget

    def add_menubar_action(self, name, icon, tip, callback=None):
        """
        Add a button/action into menu bar widget
        :param name: str
        :param icon: QIcon
        :param tip: str
        :param callback: fn
        :return: QAction
        """

        # We need to do this to avoid PySide2 errors
        def _callback():
            callback()

        action = self.menubar_widget().addAction(name)
        if icon:
            action.setIcon(icon)
        if tip:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if callback:
            action.triggered.connect(_callback)

        return action

    def is_menubar_widget_visible(self):
        """
        Returns whether MenuBar widget is visible or not
        :return: bool
        """

        return self.menubar_widget().is_expanded()

    def set_menubar_widget_visible(self, flag):
        """
        Sets whether menubar widget is visible or not
        :param flag: bool
        """

        flag = bool(flag)
        if flag:
            self.menubar_widget().expand()
        else:
            self.menubar_widget().collapse()

    # ============================================================================================================
    # SIDEBAR WIDGET
    # ============================================================================================================

    def sidebar_widget(self):
        """
        Return the sidebar widget
        :return: LibrarySidebarWidget
        """

        return self._sidebar_widget

    def is_sidebar_widget_visible(self):
        """
        Return whether SideBar widget is visible or not
        :return: bool
        """

        return self._sidebar_widget_visible

    def set_sidebar_widget_visible(self, flag):
        """
        Set whether SideBar widget is visible or not
        :param flag: bool
        """

        flag = bool(flag)
        self._sidebar_widget_visible = flag

        if flag:
            self._sidebar_frame.show()
        else:
            self._sidebar_frame.hide()

        self.update_view_button()

    @show_wait_cursor_decorator
    def refresh_sidebar(self):
        """
        Refresh the state of the sidebar widget
        """

        path = self.path()
        if not path and self._allow_non_path:
            return
        else:
            if not path:
                return self.show_hello_dialog()
            elif not os.path.exists(path):
                return self.show_path_error_dialog()

            self.update_sidebar()

    def update_sidebar(self):
        """
        Update the folders to be shown in the folders widget
        """

        data = dict()
        root = self.path()

        queries = [{'filters': [('type', 'is', 'Folder')]}]

        items = self.library().find_items(queries)
        trash_icon_path = tp.ResourcesMgr().get('icons', 'black', 'trash')

        for item in items:
            path = item.path()
            if item.path().endswith('Trash'):
                data[path] = {'iconPath': trash_icon_path}
            else:
                data[path] = dict()

        self.sidebar_widget().set_data(data, root=root)

    def selected_folder_path(self):
        """
        Return the selected folder items
        :return: str or None
        """

        return self.sidebar_widget().selected_path()

    def selected_folder_paths(self):
        """
        Return the selected folder items
        :return: list(str)
        """

        return self.sidebar_widget().selected_paths()

    def select_folder_path(self, path):
        """
        Select the given folder path
        :param path: str
        """

        self.select_folder_paths([path])

    def select_folder_paths(self, paths):
        """
        Select the given folder paths
        :param paths: list(str)
        """

        self.sidebar_widget().select_paths(paths)

    def create_folder_context_menu(self):
        """
        Returns the folder menu for the selected folders
        :return: QMenu
        """

        path = self.selected_folder_path()
        items = list()
        if path:
            item = self.manager().item_from_path(path, library_window=self)
            if item:
                items = [item]

        return self._create_item_context_menu(items)

    # ============================================================================================================
    # NEW ITEM WIDGET
    # ============================================================================================================

    def new_item_widget(self):
        """
        Returns the current new item widget
        :return: QWidget
        """

        return self._new_item_widget

    def set_new_item_widget(self, widget):
        """
        Sets the new item widget
        :param widget: QWidget
        """

        if self._new_item_widget == widget:
            msg = 'New Item widget already contains widghet {}'.format(widget)
            qt.logger.debug(msg)
        else:
            self.close_new_item_widget()
            self._new_item_widget = widget
            if self._new_item_widget:
                self._new_item_frame.layout().addWidget(self._new_item_widget)
                self._new_item_widget.show()

    def is_new_item_widget_visible(self):
        """
        Returns whether new item widget is visible or not
        :return: bool
        """

        return self._new_item_widget_visible

    def set_new_item_widget_visible(self, flag):
        """
        Set if the New Item widget should be showed or not
        :param flag: bool
        """

        flag = bool(flag)
        self._new_item_widget_visible = flag

        if flag:
            self.stack.slide_in_index(1)
            self._new_item_frame.show()
        else:
            self.stack.slide_in_index(0)
            self._new_item_frame.hide()

        self.update_view_button()

    def clear_new_item_widget(self):
        """
        Set the default new item widget
        """

        self._new_item_widget = None
        widget = base.PlaceholderWidget()
        self.set_new_item_widget(widget)

    def close_new_item_widget(self):
        """
        Close and delete the new item widget
        """

        lyt = self._new_item_frame.layout()

        while lyt.count():
            item = lyt.takeAt(0)
            item.widget().hide()
            item.widget().close()
            item.widget().deleteLater()

        self._new_item_widget = None

    # ============================================================================================================
    # PREVIEW WIDGET
    # ============================================================================================================

    def preview_widget(self):
        """
        Returns the current preview widget
        :return: QWidget
        """

        return self._preview_widget

    def set_preview_widget(self, widget):
        """
        Set the preview widget
        :param widget: QWidget
        """

        if self._preview_widget == widget:
            msg = 'Preview widget already contains widget {}'.format(widget)
            qt.logger.debug(msg)
        else:
            self.close_preview_widget()
            self._preview_widget = widget
            if self._preview_widget:
                self._preview_frame.layout().addWidget(self._preview_widget)
                self._preview_widget.show()

    def is_preview_widget_visible(self):
        """
        Returns whether preview widget is visible or not
        :return: bool
        """

        return self._preview_widget_visible

    def set_preview_widget_visible(self, flag):
        """
        Set if the PreviewWidget should be showed or not
        :param flag: bool
        """

        flag = bool(flag)
        self._preview_widget_visible = flag

        if flag:
            self._preview_frame.show()
        else:
            self._preview_frame.hide()

        self.update_view_button()

    def update_preview_widget(self):
        """
        Update the current preview widget
        """

        self.set_preview_widget_from_item(self._current_item, force=True)

    def set_preview_widget_from_item(self, item, force=True):
        """
        Set the preview widget from the given item
        :param item: LibvraryItem
        :param force: bool
        """

        if not force and self._current_item == item:
            qt.logger.debug('The current item preview widget is already set!')
            return

        self._current_item = item

        if item:
            self.close_preview_widget()
            try:
                item.show_preview_widget(self)
            except Exception as e:
                self.show_error_message(e)
                self.clear_preview_widget()
                raise
        else:
            self.clear_preview_widget()

    def clear_preview_widget(self):
        """
        Set the default preview widget
        """

        self._preview_widget = None
        widget = base.PlaceholderWidget()
        self.set_preview_widget(widget)

    def close_preview_widget(self):
        """
        Close and delete the preview widget
        """

        lyt = self._preview_frame.layout()

        while lyt.count():
            item = lyt.takeAt(0)
            item.widget().hide()
            item.widget().close()
            item.widget().deleteLater()

        self._preview_widget = None

    # ============================================================================================================
    # SEARCH WIDGET
    # ============================================================================================================

    def search_widget(self):
        """
        Returns search widget
        :return: LibrarySearchWidget
        """

        return self._search_widget

    def set_search_text(self, text):
        """
        Set the search widget text
        :param text: str
        """

        self.search_widget().setText(text)

    def items_visible_count(self):
        """
        Return the number of visible items
        :return: int
        """

        return self._items_visible_count

    def items_hidden_count(self):
        """
        Return the number of hidden items
        :return: int
        """

        return self._items_hidden_count

    # ============================================================================================================
    # STATUS WIDGET
    # ============================================================================================================

    def status_widget(self):
        """
        Returns the status widget
        :return: StatusWidget
        """

        return self._status_widget

    def is_status_widget_visible(self):
        """
        Return whether StatusWidget is visible or not
        :return: bool
        """

        return self._status_widget_visible

    def set_status_widget_visible(self, flag):
        """
        Set whether StatusWidget is visible or not
        :param flag: bool
        """

        flag = bool(flag)
        self._status_widget_visible = flag
        if flag:
            self.status_widget().show()
        else:
            self.status_widget().hide()

    # ============================================================================================================
    # TRASH FOLDER
    # ============================================================================================================

    def trash_enabled(self):
        """
        Returns True if moving items to trash
        :return: bool
        """

        return self._trash_enabled

    def set_trash_enabled(self, flag):
        """
        Sets if items can be trashed or not
        :param flag: bool
        """

        self._trash_enabled = flag

    def is_path_in_trash(self, path):
        """
        Returns whether given path is in trash or not
        :param path: str
        :return: bool
        """

        return consts.TRASH_NAME in path.lower()

    def trash_path(self):
        """
        Returns the trash path for the library
        :return: str
        """

        path = self.path()
        return '{}/{}'.format(path, consts.TRASH_NAME.title())

    def trash_folder_exists(self):
        """
        Returns whether trash folder exists or not
        :return: bool
        """

        return os.path.exists(self.trash_path())

    def create_trash_folder(self):
        """
        Create the trash folder if it does not already exists
        """

        trash_path = self.trash_path()
        if not os.path.exists(trash_path):
            os.makedirs(trash_path)

    def is_trash_folder_visible(self):
        """
        Return whether trash folder is visible or not
        :return: bool
        """

        return self._is_trash_folder_visible

    def set_trash_folder_visible(self, flag):
        """
        Set whether trash folder is visible or not
        :param flag: bool
        """

        self._is_trash_folder_visible = flag

        if flag:
            query = {
                'name': 'trash_query',
                'filters': list()
            }
        else:
            query = {
                'name': 'trash_query',
                'filters': [('path', 'not_contains', 'Trash')]
            }

        self.library().add_to_global_query(query)
        self.update_sidebar()
        self.library().search()

    def is_trash_selected(self):
        """
        Return whether the selected folders are in the trash or not
        :return: bool
        """

        folders = self.selected_folder_paths()
        for folder in folders:
            if self.is_path_in_trash(folder):
                return True

        items = self.selected_items()
        for item in items:
            if self.is_path_in_trash(item.path()):
                return True

        return False

    def move_items_to_trash(self, items):
        """
        Move the given items to trash path
        :param items: list(LibraryItem)
        """

        self.create_trash_folder()
        self.move_items(items, target_folder=self.trash_path(), force=True)

    def show_move_items_to_trash_dialog(self, items=None):
        """
        Show the "Move to Trash" dialog for the selected items
        :param items: list(LibraryItem) or None
        """

        items = items or self.selected_items()
        if items:
            title = 'Move to Trash?'
            text = 'Are you sure you want to move the selected item/s to the trash?'
            result = self.show_question_dialog(title, text)
            if result == QDialogButtonBox.Yes:
                self.move_items_to_trash(items)

    # ============================================================================================================
    # DPI SUPPORT
    # ============================================================================================================

    def dpi(self):
        """
        Return the current dpi for the library widget
        :return: float
        """

        return float(self._dpi)

    def set_dpi(self, dpi):
        """
        Set the current dpi for the library widget
        :param dpi: float
        """

        if not consts.DPI_ENABLED:
            dpi = 1.0

        self._dpi = dpi

        self.viewer().set_dpi(dpi)
        self.menubar_widget().set_dpi(dpi)
        self.sidebar_widget().set_dpi(dpi)
        self.status_widget().setFixedHeight(20 * dpi)

        self._splitter.setHandleWidth(2 * dpi)

        self.show_toast_message('DPI: {}'.format(int(dpi * 100)))

        self.reload_stylesheet()

    @show_wait_cursor_decorator
    def sync(self, force_start=False, force_searh=False):
        """
        Sync any data that might be out of date with the model
        """

        @show_wait_cursor_decorator
        def _sync():
            elapsed_time = time.time()
            self.library().sync(percent_callback=self.set_progress_bar_value)
            elapsed_time = time.time() - elapsed_time
            self.status_widget().show_info_message('Synced items in {0:.3f} seconds'.format(elapsed_time))
            self.set_progress_bar_value('Done')
            if force_start:
                progress_bar.close()
            else:
                animation.fade_out_widget(progress_bar, duration=500, on_finished=progress_bar.close)

            if force_searh and self.library():
                self.library().set_dirty(True)
                self.library().search()

        progress_bar = self.status_widget().progress_bar()
        if self.PROGRESS_BAR_VISIBLE:
            progress_bar.show()
        self.set_progress_bar_value('Syncing')

        if force_start:
            _sync()
        else:
            animation.fade_in_widget(progress_bar, duration=1, on_finished=_sync)

    def set_progress_bar_value(self, label, value=-1):
        """
        Sets the progress bar label and value
        :param label: str
        :param value: int
        """

        progress_bar = self.status_widget().progress_bar()
        if value == -1:
            self.status_widget().progress_bar().reset()
            progress_bar.set_value(100)
            progress_bar.set_text(label)
        else:
            percent = value * 100.0
            text = '{0} {1:.0f}%'.format(label, percent)
            progress_bar.set_value(percent)
            progress_bar.set_text(text)

    # ============================================================================================================
    # THEMES/STYLES
    # ============================================================================================================

    def icon_color(self):
        """
        Returns the icon color
        :return: Color
        """

        return consts.ICON_COLOR

    def reload_stylesheet(self):
        """
        Reloads the style to the current theme
        """

        pass

    # ============================================================================================================
    # TOAST/MESSAGES
    # ============================================================================================================

    def show_toast_message(self, text, duration=1000):
        """
        Shows toast widget with the given text and duration
        :param text: str
        :param duration:int
        """

        self.viewer().show_toast_message(text, duration)

    def show_info_message(self, text, msecs=None):
        """
        Shows info message to the user
        :param text: str
        :param msecs: int or None
        """

        self.status_widget().show_info_message(text)

    def show_warning_message(self, text, msecs=None):
        """
        Shows warning message to the user
        :param text: str
        :param msecs: int or None
        """

        self.status_widget().show_warning_message(text, msecs)
        self.set_status_widget_visible(True)

    def show_error_message(self, text, msecs=None):
        """
        Shows error message to the user
        :param text:str
        :param msecs: int or None
        """

        self.status_widget().show_error_message(text, msecs)
        self.set_status_widget_visible(True)

    def show_refresh_message(self):
        """
        Show long the current refresh took
        """

        item_count = len(self.library().results())
        elapsed_time = self.library().search_time()

        plural = ''
        if item_count > 1:
            plural = 's'

        msg = 'Found {0} item{1} in {2:.3f} seconds.'.format(item_count, plural, elapsed_time)
        self.status_widget().show_info_message(msg)

        qt.logger.debug(msg)

    @show_arrow_cursor_decorator
    def show_hello_dialog(self):
        """
        This function is called when there is not root path set for the library
        """

        text = 'Please choose a folder location for storing the data'
        dialog = messagebox.create_message_box(
            None, 'Welcome {}'.format(self.name()), text, header_pixmap=self._library_icon_path)
        dialog.accepted.connect(self.show_change_path_dialog)
        dialog.exec_()

    @show_arrow_cursor_decorator
    def show_path_error_dialog(self):
        """
        This function is called when the root path does not exists during refresh
        """

        path = self.path()
        text = 'The current root path does not exists "{}". Please select a new root path to continue.'.format(path)
        dialog = messagebox.create_message_box(self, 'Path Error', text)
        dialog.show()
        dialog.accepted.connect(self.show_change_path_dialog)

    def show_change_path_dialog(self):
        """
        Shows a file browser dialog for changing the root path
        :return: str
        """

        path = self._show_change_path_dialog()
        if path:
            self.set_path(path)
        else:
            self.refresh()

    def show_info_dialog(self, title, text):
        """
        Function that shows an information dialog to the user
        :param title: str
        :param text: str
        :return: QDialogButtonBox.StandardButton
        """

        buttons = QDialogButtonBox.Ok
        return messagebox.MessageBox.question(self, title, text, buttons=buttons)

    def show_question_dialog(self, title, text, buttons=None):
        """
        Function that shows a question dialog to the user
        :param title: str
        :param text: str
        :param buttons: list(QDialogButtonBox.StandardButton)
        :return: QDialogButtonBox.StandardButton
        """

        buttons = buttons or QDialogButtonBox.Yes | QDialogButtonBox.No | QDialogButtonBox.Cancel
        return messagebox.MessageBox.question(self, title, text, buttons=buttons)

    def show_error_dialog(self, title, text):
        """
        Function that shows an error dialog to the user
        :param title: str
        :param text: str
        :return: QDialogButtonBox.StandardButton
        """

        self.show_error_message(text)
        return messagebox.MessageBox.critical(self, title, text)

    def show_exception_dialog(self, title, text):
        """
        Function that shows an exception dialog to the user
        :param title: str
        :param text: str
        :return: QDialogButtonBox.StandardButton
        """

        qt.logger.exception(text)
        self.show_error_dialog(title, text)

    def show_folder_menu(self, pos=None):
        """
        Shows the folder context menu at the current cursor position
        :param pos: variant, QPoint or None
        :return: QAction
        """

        menu = self.create_folder_context_menu()
        point = QCursor.pos()
        point.setX(point.x() + 3)
        point.setY(point.y() + 3)
        action = menu.exec_(point)
        menu.close()

        return action

    # ============================================================================================================
    # OTHERS
    # ============================================================================================================

    def is_compact_view(self):
        """
        Returns whether the folder and preview widget are hidden
        :return: bool
        """

        return not self.is_sidebar_widget_visible() and not self.is_preview_widget_visible()

    def toggle_view(self):
        """
        Toggles the preview widget and folder widget visibility
        """

        compact = self.is_compact_view()
        if qtutils.is_control_modifier():
            compact = False
            self.set_menubar_widget_visible(compact)

        self.set_preview_widget_visible(compact)
        self.set_sidebar_widget_visible(compact)

    def update_view_button(self):
        """
        Updates the icon for the view action
        """

        compact = self.is_compact_view()
        action = self.menubar_widget().find_action('View')
        if not compact:
            icon = tp.ResourcesMgr().icon('view_all', theme='black')
        else:
            icon = tp.ResourcesMgr().icon('view_compact', theme='black')
        icon.set_color(self.icon_color())
        action.setIcon(icon)

    def update_filters_button(self):
        """
        Updates the icon for the filters menu
        """

        action = self.menubar_widget().find_action('Filters')
        icon = tp.ResourcesMgr().icon('filter', theme='black')
        icon.set_color(self.icon_color())
        if self._filter_by_menu.is_active():
            icon.set_badge(18, 1, 9, 9, color=consts.ICON_BADGE_COLOR)
        action.setIcon(icon)

    def is_recursive_search_enabled(self):
        """
        Returns whether recursive search is enabled or not
        :return: bool
        """

        return self.sidebar_widget().is_recursive()

    def set_recursive_search_enabled(self, flag):
        """
        Sets whether recursive search is enabled or not
        :param flag: bool
        """

        self.sidebar_widget().set_recursive(flag)

    # ============================================================================================================
    # INTERNAL FUNCTIONS
    # ============================================================================================================

    def _get_add_icon(self, color):
        """
        Returns add icon
        :param color: QColor
        :return: QIcon
        """

        return tp.ResourcesMgr().icon('add')

    def _create_new_item_menu(self):
        """
        Internal function that creates a new item menu for adding new items
        :return: QMenu
        """

        color = self.icon_color()

        item_icon = self._get_add_icon(color=color)
        menu = QMenu(self)
        menu.setIcon(item_icon)
        menu.setTitle('New')

        for cls in sorted(self.manager().registered_items(), key=operator.attrgetter('MenuOrder')):
            action = cls.create_action(menu, self)
            if action:
                action_icon = icon.Icon(action.icon())
                # action_icon.set_color(self.icon_color())
                action.setIcon(action_icon)
                menu.addAction(action)

        return menu

    def _create_item_context_menu(self, items):
        """
        Internal function that returns the item context menu for the given items
        :param items: list(LibraryItem)
        :return:
        """

        context_menu = menu.Menu(self)

        item = None
        if items:
            item = items[-1]
            item.context_menu(context_menu)

        if not self.is_locked():
            context_menu.addMenu(self._create_new_item_menu())
            if item:
                edit_icon = tp.ResourcesMgr().icon('edit')
                edit_menu = menu.Menu(context_menu)
                edit_menu.setTitle('Edit')
                edit_menu.setIcon(edit_icon)
                context_menu.addMenu(edit_menu)
                item.context_edit_menu(edit_menu)
                if self.trash_enabled():
                    edit_menu.addSeparator()
                    callback = partial(self.show_move_items_to_trash_dialog, items)
                    action = QAction('Move to Trash', edit_menu)
                    action.setEnabled(not self.is_trash_selected())
                    action.triggered.connect(callback)
                    edit_menu.addAction(action)

        context_menu.addSeparator()
        context_menu.addMenu(self._create_settings_menu())

        return context_menu

    def _create_settings_menu(self):
        """
        Returns the settings menu for changing the lirary widget
        :return: QMenu
        """

        settings_icon = tp.ResourcesMgr().icon('settings')
        context_menu = menu.Menu('', self)
        context_menu.setTitle('Settings')
        context_menu.setIcon(settings_icon)

        if consts.SETTINGS_DIALOG_ENABLED:
            settings_action = context_menu.addAction('Settings')
            settings_action.triggered.connect(self._on_show_settings_dialog)

        sync_action = context_menu.addAction('Sync')
        sync_action.triggered.connect(self.sync)

        context_menu.addSeparator()

        if consts.DPI_ENABLED:
            dpi_action = action.SliderAction('Dpi', context_menu)
            dpi = self.dpi() * 100.0
            dpi_action.slider().setRange(consts.DPI_MIN_VALUE, consts.DPI_MAX_VALUE)
            dpi_action.slider().setValue(dpi)
            dpi_action.valueChanged.connect(self._on_dpi_slider_changed)
            context_menu.addAction(dpi_action)
            context_menu.addSeparator()

        show_menu_action = QAction('Show Menu', context_menu)
        show_menu_action.setCheckable(True)
        show_menu_action.setChecked(self.is_menubar_widget_visible())
        show_menu_action.triggered[bool].connect(self.set_menubar_widget_visible)
        context_menu.addAction(show_menu_action)

        show_sidebar_action = QAction('Show Sidebar', context_menu)
        show_sidebar_action.setCheckable(True)
        show_sidebar_action.setChecked(self.is_sidebar_widget_visible())
        show_sidebar_action.triggered[bool].connect(self.set_sidebar_widget_visible)
        context_menu.addAction(show_sidebar_action)

        show_preview_action = QAction('Show Preview', context_menu)
        show_preview_action.setCheckable(True)
        show_preview_action.setChecked(self.is_preview_widget_visible())
        show_preview_action.triggered[bool].connect(self.set_preview_widget_visible)
        context_menu.addAction(show_preview_action)

        show_status_action = QAction('Show Status', context_menu)
        show_status_action.setCheckable(True)
        show_status_action.setChecked(self.is_status_widget_visible())
        show_status_action.triggered[bool].connect(self.set_status_widget_visible)
        context_menu.addAction(show_status_action)

        context_menu.addSeparator()

        if self.trash_enabled():
            show_trash_action = QAction('Show Trash Folder', context_menu)
            show_trash_action.setEnabled(self.trash_folder_exists())
            show_trash_action.setCheckable(True)
            show_trash_action.setChecked(self.is_trash_folder_visible())
            show_trash_action.triggered[bool].connect(self.set_trash_folder_visible)
            context_menu.addAction(show_trash_action)

        context_menu.addSeparator()

        recursive_search_action = QAction('Enable Recrusive Search', context_menu)
        recursive_search_action.setCheckable(True)
        recursive_search_action.setChecked(self.is_recursive_search_enabled())
        recursive_search_action.triggered[bool].connect(self.set_recursive_search_enabled)
        context_menu.addAction(recursive_search_action)

        context_menu.addSeparator()

        view_menu = self.viewer().create_settings_menu()
        context_menu.addMenu(view_menu)

        # context_menu.addSeparator()
        #
        # debug_mode_action = QAction('Debug Mode')
        # debug_mode_action.setCheckable(True)
        # debug_mode_action.setChecked(self.is_debug())
        # debug_mode_action.triggered[bool].connect(self.set_debug_mode)
        # context_menu.addAction(debug_mode_action)

        return context_menu

    @show_arrow_cursor_decorator
    def _show_change_path_dialog(self):
        """
        Internal function that opens a file dialog for setting a new root path
        :return: str
        """

        path = self.path()
        directory = path
        if not directory:
            directory = os.path.expanduser('~')
        dialog = QFileDialog(None, Qt.WindowStaysOnTopHint)
        dialog.setWindowTitle('Choose the root location')
        dialog.setDirectory(directory)
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        if dialog.exec_() == QFileDialog.Accepted:
            selected_files = dialog.selectedFiles()
            if selected_files:
                path = selected_files[0]

        if not path:
            return

        path = path_utils.normalize_path(path)

        return path

    # ============================================================================================================
    # CALLBACK FUNCTIONS
    # ============================================================================================================

    def _on_search_finished(self):
        self.show_refresh_message()

    def _on_show_items_context_menu(self, pos=None):
        """
        Internal callback function that is called when user right clicks on muscle viewer
        Shows the item context menu at the current cursor position
        :param pos, QPoint
        :return: QAction
        """

        items = self.viewer().selected_items()
        menu = self._create_item_context_menu(items)
        point = QCursor.pos()
        point.setX(point.x() + 3)
        point.setY(point.y() + 3)
        action = menu.exec_(point)

        return action

    def _on_show_settings_dialog(self):
        pass

    def _on_sync(self):
        """
        Internal callback function that is executed when the user selects the Sync
        context menu action
        """

        self.sync(force_searh=True)

    def _on_show_new_menu(self):
        """
        Internal callback function triggered when the user presses New Item Action
        Creates and shows the new menu at the new action button
        :return: QAction
        """

        menu = self._create_new_item_menu()
        point = self.menubar_widget().rect().bottomLeft()
        point = self.menubar_widget().mapToGlobal(point)
        menu.show()

        return menu.exec_(point)

    def _on_show_settings_menu(self):
        """
        Internal callback function triggered when the user show settings
        Show the settings menu at the current cursor position
        :return: QAction
        """

        menu = self._create_settings_menu()
        point = self.menubar_widget().rect().bottomRight()
        point = self.menubar_widget().mapToGlobal(point)
        menu.show()
        point.setX(point.x() - menu.width())

        return menu.exec_(point)

    def _on_show_filter_by_menu(self):
        """
        Internal callback function called when the user clicks on the filter action
        """

        widget = self.menubar_widget().find_tool_button('Filters')
        point = widget.mapToGlobal(QPoint(0, widget.height()))
        self._filter_by_menu.show(point)
        self.update_filters_button()

    def _on_show_item_view_menu(self):
        """
        Internal callback function when triggered when the user clicks on item view action
        """

        menu = self.viewer().create_item_settings_menu()
        item_view_widget = self.menubar_widget().find_tool_button('Item View')
        point = item_view_widget.mapToGlobal(QPoint(0, item_view_widget.height()))
        menu.exec_(point)

    def _on_show_group_by_menu(self):
        """
        Internal callback function called when the user presses group by action
        """

        widget = self.menubar_widget().find_tool_button('Group By')
        point = widget.mapToGlobal(QPoint(0, widget.height()))
        self._group_by_menu.show(point)

    def _on_show_sort_by_menu(self):
        """
        Internal callback function called when the user presses Sort by action
        """

        widget = self.menubar_widget().find_tool_button('Sort By')
        point = widget.mapToGlobal(QPoint(0, widget.height()))
        self._sort_by_menu.show(point)

    def _on_toggle_view(self):
        """
        Internal callback function called whe the user press view action
        """

        self.toggle_view()

    def _on_item_moved(self, item):
        """
        Internal callback function that is triggered when the custom order has changed
        :param item, LibraryItem
        """

        self.save_custom_order()

    def _on_item_dropped(self, event):
        """
        Internal callback function that is triggered when items are dropped on the viewer or sidebar widget
        :param event: QEvent
        """

        mime_data = event.mimeData()
        print(mime_data)

    def _on_item_selection_changed(self):
        """
        Internal callback function that is triggered when an item is selected or deselected
        """

        item = self.viewer().selected_item()

        self.set_preview_widget_from_item(item)
        self.itemSelectionChanged.emit(item)

    def _on_folder_selection_changed(self):
        """
        Internal callback function that is triggered when a folder is selected or deselected
        """

        path = self.selected_folder_path()
        self.library().search()
        self.folderSelectionChanged.emit(path)
        self.globalSignal.folderSelectionChanged.emit(self, path)

    def _on_show_folder_menu(self, pos=None):
        """
        Internal callback function that is triggered when the user left click on sidebar widget
        """

        self.show_folder_menu(pos=pos)

    def _on_dpi_slider_changed(self, value):
        """
        Internal callback function triggered when the dpi action slider changes its values
        :param value: float
        """

        dpi = value / 100.0
        self.set_dpi(dpi)
