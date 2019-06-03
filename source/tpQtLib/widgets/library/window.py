#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains main window widget used in libraries
"""

from __future__ import print_function, division, absolute_import

import os
import copy
from functools import partial

from tpQtLib.Qt.QtCore import *
from tpQtLib.Qt.QtWidgets import *
from tpQtLib.Qt.QtGui import *

from tpPyUtils import decorators, path as path_utils

import tpDccLib as tp

import tpQtLib
from tpQtLib.core import base, icon, menu, qtutils
from tpQtLib.widgets import stack, messagebox
from tpQtLib.widgets.library import consts, utils, library, viewer, widgets

if tp.is_maya():
    from tpMayaLib.core import decorators as maya_decorators
    show_wait_cursor_decorator = maya_decorators.show_wait_cursor
    show_arrow_cursor_decorator = maya_decorators.show_arrow_cursor
else:
    show_wait_cursor_decorator = decorators.empty_decorator
    show_arrow_cursor_decorator = decorators.empty_decorator


class LibraryWindow(tpQtLib.MainWindow, object):

    LIBRARY_CLASS = library.Library
    VIEWER_CLASS = viewer.LibraryViewer
    SEARCH_WIDGET_CLASS = widgets.LibrarySearchWidget
    STATUS_WIDGET_CLASS = widgets.LibraryStatusWidget
    MENUBAR_WIDGET_CLASS = widgets.LibraryToolbarWidget
    SIDEBAR_WIDGET_CLASS = widgets.LibrarySidebarWidget
    SORTBY_MENU_CLASS = widgets.SortByMenu
    GROUPBY_MENU_CLASS = widgets.GroupByMenu
    FILTERBY_MENU_CLASS = widgets.FilterByMenu

    class PreviewFrame(QFrame):
        pass

    class SidebarFrame(QFrame):
        pass

    def __init__(self, parent=None, name='', path='', library_icon_path=None, allow_non_path=False, **kwargs):

        self._dpi = 1.0
        self._items = list()
        self._name = name or consts.LIBRARY_DEFAULT_NAME
        self._is_debug = False
        self._is_locked = False
        self._is_loaded = False
        self._preview_widget = None
        self._progress_bar = None
        self._current_item = None
        self._library = None
        self._refresh_enabled = False
        self._library_icon_path = library_icon_path
        self._allow_non_path = allow_non_path

        self._trash_enabled = consts.TRASH_ENABLED
        self._recursive_search_enabled = consts.DEFAULT_RECURSIVE_SEARCH_ENABLED

        self._items_hidden_count = 0
        self._items_visible_count = 0

        self._is_trash_folder_visible = False
        self._sidebar_widget_visible = True
        self._preview_widget_visible = True
        self._status_widget_visible = True

        super(LibraryWindow, self).__init__(name=name, parent=parent, **kwargs)

        self.update_view_button()
        self.update_filters_button()
        self.update_preview_widget()

        if path:
            self.set_path(path)

    """
    ##########################################################################################
    ABSTRACT
    ##########################################################################################
    """

    @decorators.abstractmethod
    def manager(self):
        """
        Returns library managed used by this window
        Must be implemented in child classes
        :return: LibraryManager
        """

        raise NotImplementedError('LibraryWindow manager() function is not implemented!')

    """
    ##########################################################################################
    OVERLOADING FUNCTIONS
    ##########################################################################################
    """

    def ui(self):
        super(LibraryWindow, self).ui()

        self.setMinimumWidth(5)
        self.setMinimumHeight(5)

        self.stack = stack.SlidingStackedWidget()
        self.main_layout.addWidget(self.stack)

        lib = self.LIBRARY_CLASS(library_window=self)
        lib.dataChanged.connect(self.refresh)
        lib.searchTimeFinished.connect(self._on_search_finished)

        self._sidebar_frame = LibraryWindow.SidebarFrame(self)
        sidebar_frame_lyt = QVBoxLayout(self)
        sidebar_frame_lyt.setContentsMargins(0, 1, 0, 0)
        self._sidebar_frame.setLayout(sidebar_frame_lyt)

        self._preview_frame = LibraryWindow.PreviewFrame(self)
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

        sidebar_frame_lyt.addWidget(self._sidebar_widget)

        self._search_widget = self.SEARCH_WIDGET_CLASS(self)
        self._menubar_widget.addWidget(self._search_widget)

        self._splitter = QSplitter(Qt.Horizontal, self)
        self._splitter.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self._splitter.setHandleWidth(2)
        self._splitter.setChildrenCollapsible(False)

        self._splitter.addWidget(self._sidebar_frame)
        self._splitter.addWidget(self._viewer)
        # self._splitter.insertWidget(2, self._preview_frame)

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
        self.stack.addWidget(self._preview_frame)

        self._sort_by_menu.set_library(lib)
        self._group_by_menu.set_library(lib)
        self._filter_by_menu.set_library(lib)
        self._viewer.set_library(lib)
        self._search_widget.set_library(lib)
        self._sidebar_widget.set_library(lib)
        self.set_library(lib)

        self.menubar_widget().addWidget(self._search_widget)

        self._setup_menubar()

    def setup_signals(self):
        self._viewer.customContextMenuRequested.connect(self._on_show_items_context_menu)

    def _setup_menubar(self):
        icon_color = self.icon_color()
        name = 'New Item'
        icon = tpQtLib.resource.icon('add')
        # icon.set_color(icon_color)
        tip = 'Add a new item to the selected folder'
        self.add_menubar_action(name, icon, tip, callback=self._on_show_new_menu)

        name = 'Filters'
        icon = tpQtLib.resource.icon('filter')
        # icon.set_color(icon_color)
        tip = 'Filter the current results by type.\nCtrl + Click will hide the ohters and show the selected one.'
        self.add_menubar_action(name, icon, tip, callback=self._on_show_filter_by_menu)

        name = 'View'
        icon = tpQtLib.resource.icon('add')
        # icon.set_color(icon_color)
        tip = 'Choose to show/hide both the preview and navigation pane\nCtrl + click will hide the menu bar as well.'
        self.add_menubar_action(name, icon, tip, callback=self._on_toggle_view)

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
            item.keyReleaseEvent(event)
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

    def showEvent(self, event):
        """
        Overrides window.MainWindow showEvent function
        :param event: QEvent
        """

        super(LibraryWindow, self).showEvent(event)

        if not self.is_loaded():
            self.set_loaded(True)
            self.set_refresh_enabled(True)
            self.load_settings()

    def closeEvent(self, event):
        """
        Overrides window.MainWindow closeEvent function
        :param event: QEvent
        """

        self.save_settings()
        super(LibraryWindow, self).closeEvent(event)

    """
    ##########################################################################################
    BASE
    ##########################################################################################
    """

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

    def is_loaded(self):
        """
        Returns whether window has been shown or not
        :return: bool
        """

        return self._is_loaded

    def set_loaded(self, flag):
        """
        Set if window has been shown or not
        :param flag: flag
        """

        self._is_loaded = flag

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

        path = path_utils.real_path(path)
        if path == self.path():
            tpQtLib.logger.warning('Path is already set!')
            return

        library = self.library()
        library.set_path(path)
        if not os.path.exists(library.data_path()):
            library.sync()

        if self.stack.currentIndex() != 0:
            self.stack.slide_in_index(0)

        self.refresh()
        self.library().search()
        self.update_preview_widget()

    def set_create_widget(self, create_widget):
        """
        Set the widget that should be showed when creating a new item
        :param create_widget: QWidget
        """

        if not create_widget:
            return

        self.set_preview_widget_visible(True)
        self.viewer().clear_selection()

        # fsize, rsize, psize = self._splitter.sizes()
        # if psize < 150:
        #     self.set_sizes((fsize, rsize, 180))

        self.set_preview_widget(create_widget)
        self.stack.slide_in_index(1)

    def refresh(self):
        """
        Refresh all necessary items
        """

        if self.is_refresh_enabled():
            self.update()

    """
    ##########################################################################################
    SETTINGS
    ##########################################################################################
    """

    @show_wait_cursor_decorator
    def load_settings(self):
        """
        Loads the user settings from disk
        """

        self.reload_stylesheet()
        settings = self.read_settings()
        self.set_settings(settings)

    def read_settings(self):
        """
        Reads settings from dsik
        :return: dict
        """

        key = self.name()
        return self.settings.get(key, {})

    def save_settings(self, settings=None):
        """
        Save the settings to the settings path
        :param settings: dict
        """

        settings = settings or self.settings
        key = self.name()
        self.show_toast_message('Saved')

    def settings(self):
        """
        Return a dictionary with the widget settings
        :return: dict
        """

        settings = dict()

        settings['dpi'] = self.dpi()
        settings['kwargs'] = self._kwargs
        settings['geometry'] = self.geometry_settings()
        settings['paneSizes'] = self._splitter.sizes()

        if self.theme():
            settings['theme'] = self.theme().settings()

        settings['library'] = self.library().settings()
        settings['trahsFolderVisible'] = self.is_trash_folder_visible()
        settings['sidebarWidgetVisible'] = self.is_folders_widget_visible()
        settings['previewWidgetVisible'] = self.is_preview_widget_visible()
        settings['menubarWidgetVisible'] = self.is_menubar_widget_visible()
        settings['statusWidgetVisible'] = self.is_status_widget_visible()

        settings['viewerWidget'] = self.viewer().settings()
        settings['searchWidget'] = self.search_widget().settings()
        settings['sidebarWidget'] = self.sidebar_widget().settings()
        settings['recursiveSearchEnabled'] = self.is_recursive_search_enabled()

        settings['filterByMenu'] = self._filter_by_menu.settings()

        settings['path'] = self.path()

        return settings

    def geometry_settings(self):
        """
        Return the geometry values as a list
        :return: list(int)
        """

        settings = (
            self.window().geometry().x(),
            self.window().geometry().y(),
            self.window().geometry().width(),
            self.window().geometry().height()
        )

        return settings

    def set_theme_settings(self, settings):
        """
        Sets the theme from the given settings
        :param settings: dict
        :return:
        """

        pass

    def set_settings(self, settings):
        """
        Set the library window settings from the given dictionary
        :param settings: dict
        """

        defaults = copy.deepcopy(consts.DEFAULT_SETTINGS)
        settings = utils.update(defaults, settings)

        is_refresh_enabled = self.is_refresh_enabled()

        try:
            self.set_refresh_enabled(False)
            self.viewer().set_toast_enabled(False)

            geo = settings.get('geometry')
            if geo:
                self.set_geometry_settings(geo)

            theme_settings = settings.get('theme')
            if theme_settings:
                self.set_theme_settings(theme_settings)

            if not self.path():
                path = settings.get('path')
                if path and os.path.exists(path):
                    self.set_path(path)

            dpi = settings.get('dpi', 1.0)
            self.set_dpi(dpi)

            sizes = settings.get('paneSizes')
            if sizes and len(sizes) == 3:
                self.set_sizes(sizes)

            sidebar_visible = settings.get('sidebarWidgetVisible')
            if sidebar_visible:
                self.set_sidebar_widget_visible(sidebar_visible)

            menubar_visible = settings.get('menuBarWidgetVisible')
            if menubar_visible:
                self.set_menubar_widget_visible(menubar_visible)

            preview_visible = settings.get('previewWidgetVisible')
            if preview_visible:
                self.set_preview_widget_visible(preview_visible)

            status_visible = settings.get('statusBarWidgetVisible')
            if status_visible:
                self.set_status_widget_visible(status_visible)

            search_widget = settings.get('searchWidget')
            if search_widget:
                self.search_widget().set_settings(search_widget)

            recursive_search = settings.get('recursiveSearchEnabled')
            if recursive_search:
                self.set_recursive_search_enabled(recursive_search)

            filter_by_menu = settings.get('filterByMenu')
            if filter_by_menu:
                self._filter_by_menu.set_settings(filter_by_menu)
        finally:
            self.reload_stylesheet()
            self.set_refresh_enabled(is_refresh_enabled)
            self.refresh()

        library_settings = settings.get('library')
        if library_settings:
            self.library().set_settings(library_settings)

        trash_folder_visible = settings.get('trashFolderVisible')
        if trash_folder_visible:
            self.set_trash_folder_visible(trash_folder_visible)

        sidebar_widget = settings.get('sidebarWidget', dict())
        self.viewer().set_settings(sidebar_widget)

        self.viewer().set_toast_enabled(True)

        self.update_filters_button()

    def set_geometry_settings(self, settings):
        """
        Set the geometry of the widget with the given values
        :param settings: list(int)
        """

        x, y, width, height = settings

        screen_geo = QApplication.desktop().screenGeometry()
        screen_width = screen_geo.width()
        screen_height = screen_geo.height()

        if x <= 0 or y <= 0 or x >= screen_width or y >= screen_height:
            self.center(width, height)
        else:
            self.window().setGeometry(x, y, width, height)

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

    """
    ##########################################################################################
    VIEWER WIDGET
    ##########################################################################################
    """

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
            self._item_selection_changed()

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

    """
    ##########################################################################################
    MENUBAR WIDGET
    ##########################################################################################
    """

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

    """
    ##########################################################################################
    SIDEBAR WIDGET
    ##########################################################################################
    """

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

        queries = [{'filters': [('type', 'is', 'folder')]}]

        items = self.library().find_items(queries)
        trash_icon_path = tpQtLib.resource.icon('trash')

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

    """
    ##########################################################################################
    PREVIEW WIDGET
    ##########################################################################################
    """

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
            tpQtLib.logger.debug(msg)
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
            tpQtLib.logger.debug('The current item preview widget is already set!')
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

    """
    ##########################################################################################
    SEARCH WIDGET
    ##########################################################################################
    """

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

    """
    ##########################################################################################
    STATUS WIDGET
    ##########################################################################################
    """

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

    """
    ##########################################################################################
    TRASH FOLDER
    ##########################################################################################
    """

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

        folders = self.selected_follder_paths()
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
        self.move_items(items, dst=self.trash_path(), force=True)

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
            if result == QMessageBox.Yes:
                self.move_items_to_trash(items)

    """
    ##########################################################################################
    DPI SUPPORT
    ##########################################################################################
    """

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
    def sync(self):
        """
        Sync any data that might be out of date with the model
        """

        progress_bar = self.status_widget().progress_bar()

    """
    ##########################################################################################
    THEMES/STYLES
    ##########################################################################################
    """

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

    """
    ##########################################################################################
    TOAST/MESSAGES
    ##########################################################################################
    """

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

        tpQtLib.logger.debug(msg)

    @show_arrow_cursor_decorator
    def show_hello_dialog(self):
        """
        This function is called when there is not root path set for the library
        """

        text = 'Please choose a folder location for storing the data'
        dialog = messagebox.create_message_box(None, 'Welcome {}'.format(self.name()), text, header_pixmap=self._library_icon_path)
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
        :return: QMessageBox.StandardButton
        """

        buttons = QMessageBox.Ok
        return messagebox.MessageBox.question(self, title, text, buttons=buttons)

    def show_question_dialog(self, title, text, buttons):
        """
        Function that shows a question dialog to the user
        :param title: str
        :param text: str
        :param buttons: list(QMessageBox.StandardButton)
        :return: QMessageBox.StandardButton
        """

        buttons = buttons or QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        return messagebox.MessageBox.question(self, title, text, buttons=buttons)

    def show_error_dialog(self, title, text):
        """
        Function that shows an error dialog to the user
        :param title: str
        :param text: str
        :return: QMessageBox.StandardButton
        """

        self.show_error_message(text)
        return messagebox.MessageBox.critical(self, title, text)

    def show_exception_dialog(self, title, text):
        """
        Function that shows an exception dialog to the user
        :param title: str
        :param text: str
        :return: QMessageBox.StandardButton
        """

        tpQtLib.logger.exception(text)
        self.show_error_dialog(title, text)

    """
    ##########################################################################################
    OTHERS
    ##########################################################################################
    """

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
            icon = tpQtLib.resource.icon('view_all')
        else:
            icon = tpQtLib.resource.icon('view_compact')
        # icon.set_color(self.icon_color())
        action.setIcon(icon)

    def update_filters_button(self):
        """
        Updates the icon for the filters menu
        """

        action = self.menubar_widget().find_action('Filters')
        icon = tpQtLib.resource.icon('filter')
        # icon.set_color(self.icon_color())
        if self._filter_by_menu.is_active():
            icon.set_badge(18, 1, 9, 9, color=consts.ICON_BADGE_COLOR)
        action.setIcon(icon)

    def is_recursive_search_enabled(self):
        """
        Returns whether recursive search is enabled or not
        :return: bool
        """

        self.sidebar_widget().is_recursive()

    def set_recursive_search_enabled(self, flag):
        """
        Sets whether recursive search is enabled or not
        :param flag: bool
        """

        self.sidebar_widget().set_recursive(flag)

    """
    ##########################################################################################
    INTERNAL FUNCTIONS
    ##########################################################################################
    """

    def _get_add_icon(self, color):
        """
        Returns add icon
        :param color: QColor
        :return: QIcon
        """

        return tpQtLib.resource.icon('add', color=color)

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

        def _key(cls):
            return cls.MenuOrder

        for cls in sorted(self.manager().registered_items(), key=_key):
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
            item.context_menu(menu)

        if not self.is_locked():
            context_menu.addMenu(self._create_new_item_menu())
            if item:
                edit_menu = menu.Menu(context_menu)
                edit_menu.setTitle('Edit')
                context_menu.addMenu(edit_menu)
                item.context_edit_menu(edit_menu)
                if self.trash_enabled():
                    edit_menu.addSeparator()
                    callback = partial(self._show_move_items_to_trash_dialog, items)
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

        context_menu = menu.Menu('', self)
        context_menu.setTitle('Settings')

        if consts.SETTINGS_DIALOG_ENABLED:
            action = context_menu.addAction('Settings')
            action.triggered.connect(self._on_show_settings_dialog)

        sync_action = context_menu.addAction('Sync')
        sync_action.triggered.connect(self.sync)

        context_menu.addSeparator()

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

    """
    ##########################################################################################
    CALLBACK FUNCTIONS
    ##########################################################################################
    """

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

        self.sync()

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

        pass

    def _on_toggle_view(self):
        """
        Internal callback function called whe the user press view action
        """

        self.toggle_view()


