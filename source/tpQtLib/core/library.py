#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains basic classes to create visual library of objects
"""

from __future__ import print_function, division, absolute_import

import os
import json
import time
import copy
from functools import partial
from collections import OrderedDict, Mapping

try:
    from tpPyUtils.externals.scandir import walk
except ImportError:
    from os import walk

from tpQtLib.Qt.QtCore import *
from tpQtLib.Qt.QtWidgets import *
from tpQtLib.Qt.QtGui import *

import tpQtLib
import tpDccLib as tp
from tpPyUtils import decorators, path as path_utils, osplatform
from tpQtLib.core import base, menu, icon, image, qtutils, animation
from tpQtLib.widgets import toolbar, statusbar, progressbar, toast

if tp.is_maya():
    from tpMayaLib.core import decorators as maya_decorators
    show_wait_cursor_decorator = maya_decorators.repeat_static_command
    show_arrow_cursor_decorator = maya_decorators.show_arrow_cursor
else:
    show_wait_cursor_decorator = decorators.empty_decorator
    show_arrow_cursor_decorator = decorators.empty_decorator


class LibraryConsts(object):
    """
    Class that contains consts definitions used by libraries
    """

    LIBRARY_DEFAULT_NAME = 'DefaultLibrary'

    DEFAULT_ICON_MODE = 'icon'
    DEFAULT_TABLE_MODE = 'table'

    DPI_ENABLED = False
    DPI_MIN_VALUE = 80
    DPI_MAX_VALUE = 250

    ITEM_DEFAULT_SORT_ROLE = 'SortRole'
    ITEM_DEFAULT_DATA_ROLE = 'DataRole'
    ITEM_DEFAULT_THUMBNAIL_PATH = ''
    ITEM_DEFAULT_MAX_ICON_SIZE = 256
    ITEM_DEFAULT_FONT_SIZE = 13
    ITEM_DEFAULT_PLAYHEAD_COLOR = QColor(255, 255, 255, 220)
    ITEM_DEFAULT_THUMBNAIL_COLUMN = 0
    ITEM_DEFAULT_ENABLE_THUMBNAIL_THREAD = True
    ITEM_DEFAULT_ENABLE_DELETE = False
    ITEM_DEFAULT_ENABLE_NESTED_ITEMS = False
    ITEM_DEFAULT_MENU_NAME = ''
    ITEM_DEFAULT_MENU_ORDER = 10
    ITEM_DEFAULT_MENU_ICON_PATH  = ''

    GROUP_ITEM_DEFAULT_FONT_SIZE = 24

    TREE_MINIMUM_WIDTH = 5
    TREE_DEFAULT_WIDTH = 100

    LIST_DEFAULT_DRAG_THRESHOLD = 10

    VIEWER_DEFAULT_PADDING = 5
    VIEWER_DEFAULT_ZOOM_AMOUNT = 90
    VIEWER_DEFAULT_TEXT_HEIGHT = 20
    VIEWER_DEFAULT_WHEEL_SCROLL_STEP = 2
    VIEWER_DEFAULT_MIN_SPACING = 0
    VIEWER_DEFAULT_MAX_SPACING = 50
    VIEWER_DEFAULT_MIN_LIST_SIZE = 15
    VIEWER_DEFAULT_MIN_ICON_SIZE = 50
    VIEWER_DEFAULT_TEXT_COLOR = QColor(255, 255, 255, 200)
    VIEWER_DEFAULT_SELECTED_TEXT_COLOR = QColor(255, 255, 255, 200)
    VIEWER_DEFAULT_BACKGROUND_COLOR = QColor(255, 255, 255, 30)
    VIEWER_DEFAULT_BACKGROUND_HOVER_COLOR = QColor(255, 255, 255, 35)
    VIEWER_DEFAULT_BACKGROUND_SELECTED_COLOR = QColor(30, 150, 255)

    ICON_COLOR = QColor(255, 255, 255)
    ICON_BADGE_COLOR = QColor(230, 230, 0)

    PROGRESS_BAR_VISIBLE = False
    SETTINGS_DIALOG_ENABLED = False
    RECURSIVE_SEARCH_ENABLED = False

    TRASH_NAME = 'trash'
    TRASH_ENABLED = True

    DEFAULT_RECURSIVE_DEPTH = 4
    DEFAULT_RECURSIVE_SEARCH_ENABLED = False

    DEFAULT_SETTINGS = {
        "library": {
            "sortBy": ["name:asc"],
            "groupBy": ["category:asc"]
        },
        "paneSizes": [160, 280, 180],
        "geometry": [-1, -1, 860, 720],
        "trashFolderVisible": False,
        "sidebarWidgetVisible": True,
        "previewWidgetVisible": True,
        "menuBarWidgetVisible": True,
        "statusBarWidgetVisible": True,
        "recursiveSearchEnabled": True,
        "itemsWidget": {
            "spacing": 2,
            "padding": 6,
            "zoomAmount": 80,
            "textVisible": True,
        },
        "searchWidget": {
            "text": "",
        },
        "filterByMenu": {
            "Folder": False
        },
        "theme": {
            "accentColor": "rgb(0, 175, 240, 255)",
            "backgroundColor": "rgb(60, 64, 79, 255)",
        }
    }


class LibraryException(object):

    class ItemError(Exception):
        pass

    class ItemSaveError(Exception):
        pass

    class ItemLoadError(Exception):
        pass


class LibraryUtils(object):
    """
    Class that contains static utils functions for library
    """

    @staticmethod
    def absolute_path(data, start):
        """
        Returns an absolute version of all the paths in data using the start path
        :param data: str
        :param start: str
        :return: str
        """

        rel_path1 = path_utils.normalize_path(os.path.dirname(start))
        rel_path2 = path_utils.normalize_path(os.path.dirname(rel_path1))
        rel_path3 = path_utils.normalize_path(os.path.dirname(rel_path2))

        if not rel_path1.endswith("/"):
            rel_path1 += "/"

        if not rel_path2.endswith("/"):
            rel_path2 += "/"

        if not rel_path3.endswith("/"):
            rel_path3 += "/"

        data = data.replace('../../../', rel_path3)
        data = data.replace('../../', rel_path2)
        data = data.replace('../', rel_path1)

        return data

    @staticmethod
    def update(data, other):
        """
        Update teh value of a nested dictionary of varying depth
        :param data: dict
        :param other: dict
        :return: dict
        """

        for key, value in other.items():
            if isinstance(value, Mapping):
                data[key] = LibraryUtils.update(data.get(key, {}), value)
            else:
                data[key] = value

        return data

    @staticmethod
    def read(path):
        """
        Returns the contents of the given file
        :param path: str
        :return: str
        """

        data = ''
        path = path_utils.normalize_path(path)
        if os.path.isfile(path):
            with open(path) as f:
                data = f.read() or data
        data = LibraryUtils.absolute_path(data, path)

        return data

    @staticmethod
    def write(path, data):
        """
        Writes the given data to the given file on disk
        :param path: str
        :param data: str
        """

        path = path_utils.normalize_path(path)
        data = path_utils.get_relative_path(data, path)

        tmp = path + '.tmp'
        bak = path + '.bak'

        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if os.path.exists(tmp):
            msg = 'The path is locked for writing and cannot be accessed {}'.format(tmp)
            raise IOError(msg)

        try:
            with open(tmp, 'w') as f:
                f.write(data)
                f.flush()

            if os.path.exists(bak):
                os.remove(bak)
            if os.path.exists(path):
                os.rename(path, bak)
            if os.path.exists(tmp):
                os.rename(tmp, path)
            if os.path.exists(path) and os.path.exists(bak):
                os.remove(bak)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            if not os.path.exists(path) and os.path.exists(bak):
                os.rename(bak, path)
                
            raise

    @staticmethod
    def update_json(path, data):
        """
        Update a JSON file with the given data
        :param path: str
        :param data: dict
        """

        data_ = LibraryUtils.read_json(path)
        data_ = LibraryUtils.update(data_, data)
        LibraryUtils.save_json(path, data_)

    @staticmethod
    def read_json(path):
        """
        Reads the given JSON file and deserialize it to a Python object
        :param path: str
        :return: dict
        """

        path = path_utils.normalize_path(path)
        data = LibraryUtils.read(path) or '{}'
        data = json.loads(data)

        return data

    @staticmethod
    def save_json(path, data):
        """
        Serialize given tdata to a JSON string and write it to the given path
        :param path: str
        :param data: dict
        """

        path = path_utils.normalize_path(path)
        data = OrderedDict(sorted(data.items(), key=lambda t: t[0]))
        data = json.dumps(data, indent=4)
        LibraryUtils.write(path, data)


class LibraryManager(object):
    """
    Class that manages library items registration
    """

    def __init__(self):
        super(LibraryManager, self).__init__()

        self._item_classes = OrderedDict()

    def register_item(self, cls):
        """
        Register the given item class to the given extension
        :param cls: LibraryItem
        """

        self._item_classes[cls.__name__] = cls

    def registered_items(self):
        """
        Returns all registered library item classes
        :return: list(LibraryItem)
        """

        def key(cls):
            return cls.RegisterOrder

        return sorted(self._item_classes.values(), key=key)

    def clear_registered_items(self):
        """
        Remove all registered item classes
        """

        self._item_classes = OrderedDict()

    def get_ignore_paths(self):
        """
        Returns paths that manager should ignore when creating new items
        Implements in specific class to set custom paths
        :return: list(str)
        """

        return list()

    def item_from_path(self, path, **kwargs):
        """
        Return a new item instance for the given path
        :param path: str
        :param kwargs: dict
        :return: LibraryItem or None
        """

        path = path_utils.normalize_path(path)
        for ignore in self.get_ignore_paths():
            if ignore in path:
                return None

        for cls in self.registered_items():
            if cls.match(path):
                return cls(path, **kwargs)

    def items_from_paths(self, paths, **kwargs):
        """
        Return new item instances for the given paths
        :param paths: list(str)
        :param kwargs: dict
        :return: Iterable(LibraryItem)
        """

        for path in paths:
            item = self.item_from_path(path, **kwargs)
            if item:
                yield  item

    def items_from_urls(self, urls, **kwargs):
        """
        Return new item instances for the given QUrl objects
        :param urls: list(QUrl)
        :param kwargs: dict
        :return: list(LibraryItem)
        """

        items = list()
        for path in self.paths_from_urls(urls):
            item = self.item_from_path(path, **kwargs)
            if item:
                items.append(item)
            else:
                msg = 'Cannot find the item for path "{}"'.format(path)
                tpQtLib.logger.warning(msg)

        return items

    def paths_from_urls(self, urls):
        """
    Returns the local file paths from the given QUrls
        :param urls: list(QUrl)
        :return: Iterable(str)
        """

        for url in urls:
            path =  url.toLocalFile()

            if osplatform.is_window():
                if path.startswith('/'):
                    path = path[1:]

            yield path

    def find_items(self, path, depth=3, **kwargs):
        """
        Find and create items by walking the given path
        :param path: str
        :param depth: int
        :param kwargs: dict
        :return: Iterable(LibraryItem)
        """

        path = path_utils.normalize_path(path)
        max_depth = depth
        start_depth = path.count(os.path.sep)

        for root, dirs, files in walk(path, followlinks=True):
            files.extend(dirs)
            for filename in files:
                path = os.path.join(root, filename)
                item = self.item_from_path(path, **kwargs)
                if item:
                    yield item
                    if not item.EnableNestedItems:
                        remove = True
                if remove and filename and dirs:
                    dirs.remove(filename)

            if depth == 1:
                break

            # Stop walking the directory if the maximum depth has been reached
            current_depth = root.count(os.path.sep)
            if (current_depth - start_depth) >= max_depth:
                del dirs[:]

    @staticmethod
    def find_items_in_folders(folders, depth=3, **kwargs):
        """
        Find and create new item instances by walking the given paths
        :param folders: list(str)
        :param depth: int
        :param kwargs: dict
        :return: Iterable(LibraryItem)
        """

        for folder in folders:
            for item in LibraryUtils.find_items(folder, depteh=depth, **kwargs):
                yield item


class Library(QObject, object):

    Name = LibraryConsts.LIBRARY_DEFAULT_NAME
    Fields = list()

    dataChanged = Signal()
    searchStarted = Signal()
    searchFinished = Signal()
    searchTimeFinished = Signal()

    def __init__(self, path=None, library_window=None, *args):

        self._path = path
        self._mtime = None
        self._data = dict()
        self._items = list()
        self._fields = list()
        self._sort_by = list()
        self._group_by = list()
        self._results = list()
        self._grouped_results = dict()
        self._queries = dict()
        self._global_queries = dict()
        self._search_time = 0
        self._search_enabled = True
        self._library_window = library_window

        super(Library, self).__init__(*args)

        self.set_path(path)
        self.set_dirty(True)

    @decorators.abstractmethod
    def data_path(self):
        """
        Returns path where library data base is located
        :return: str
        """

        raise NotImplementedError('Library data_path() not implemented!')

    @staticmethod
    def match(data, queries):
        """
        Match the given data with the given queries
        :param data: dict
        :param queries: list(dict)
        :return: list
        """

        matches = list()

        for query in queries:
            filters = query.get('filters')
            operator = query.get('operator', 'and')
            if not filters:
                continue

            match = False
            for key, cond, value in filters:
                if key == '*':
                    item_value = str(data)
                else:
                    item_value = data.get(key)

                if isinstance(value, (unicode, str)):
                    value = value.lower()
                if isinstance(item_value, (unicode, str)):
                    item_value = item_value.lower()
                if not item_value:
                    match = False
                elif cond == 'contains':
                    match = value in item_value
                elif cond == 'not_contains':
                    match = value not in item_value
                elif cond == 'is':
                    match = value == item_value
                elif cond == 'not':
                    match = value != item_value
                elif cond == 'startswith':
                    match = item_value.startswith(value)

                if operator == 'or' and match:
                    break
                if operator == 'and' and not match:
                    break

            matches.append(match)

        return all(matches)

    @staticmethod
    def sorted(items, sort_by):
        """
        Return the given data sorted using the sorty_by argument
        :param items: list(LibraryItem)
        :param sort_by: list(str)
        :return: list(LibraryItem)
        """

        tpQtLib.logger.debug('Sort by: {}'.format(sort_by))
        t = time.time()
        for field in reversed(sort_by):
            tokens = field.split(':')
            reverse = False
            if len(tokens) > 1:
                field = tokens[0]
                reverse = tokens[1] != 'asc'

            def sort_key(item):
                default = False if reverse else ''
                return item.item_data().get(field, default)

            items = sorted(items, key=sort_key, reverse=reverse)
        tpQtLib.logger.debug('Sort items took {}'.format(time.time() - t))

        return items

    @staticmethod
    def group_items(items, fields):
        """
        Group the given items by the given field
        :param items: list(LibraryItem)
        :param fields: list(str)
        :return: dict
        """

        tpQtLib.logger.debug('Group by: {}'.format(fields))

        # TODO: Implement support for multiple grups not only top level group

        if fields:
            field = fields[0]
        else:
            return {'None': items}

        t = time.time()
        results_ = dict()
        tokens = field.split(':')

        reverse = False
        if len(tokens) > 1:
            field = tokens[0]
            reverse = tokens[1] != 'asc'

        for item in items:
            value = item.item_data().get(field)
            if value:
                results_.setdefault(value, list())
                results_[value].append(item)

        groups = sorted(results_.keys(), reverse=reverse)

        results = OrderedDict()
        for group in groups:
            results[group] = results_[group]

        tpQtLib.logger.debug('Group Items Took {}'.format(time.time() - t))

        return results

    def name(self):
        """
        Returns the name of the library
        :return: str
        """

        return self.Name

    def path(self):
        """
        Returns the path where library is located
        :return: str
        """

        return self._path

    def set_path(self, path):
        """
        Sets path where muscle data is located
        :param path: str
        """

        self._path = path

    def mtime(self):
        """
        Returns when the data was last modified
        :return: float or None
        """

        path = self.data_path()
        mtime = None
        if os.path.exists(path):
            mtime = os.path.getmtime(path)

        return mtime

    def sort_by(self):
        """
        Return the list of fields to sorty by
        :return: list(str)
        """

        return self._sort_by

    def set_sorty_by(self, fields):
        """
        Set the list of fields to group by
        >>> set_sorty_by(['name:asc', 'type:asc'])
        :param fields: list(str)
        """

        self._sort_by = fields

    def group_by(self):
        """
        Return the list of fields to group by
        :return: list(str)
        """

        return self._group_by

    def set_group_by(self, fields):
        """
        Set the list of fields to group by
        >>> set_group_by(['name:asc', 'type:asc'])
        :param fields: list(str)
        """

        self._group_by = fields

    def fields(self):
        """
        Returns all the fields for the library
        :return: list(str)
        """

        return self._fields

    def is_dirty(self):
        """
        Returns whether the data has changed on disk or not
        :return: bool
        """

        return not self._items or self._mtime != self.mtime()

    def set_dirty(self, value):
        """
        Updates the model object with the current data timestamp
        :param value: bool
        """

        if value:
            self._mtime = None
        else:
            self._mtime = self.mtime()

    def read(self):
        """
        Read the data from disk and returns it a dictionary object
        :return: dict
        """

        if not self.path():
            tpQtLib.logger.info('No path set for reading the data from disk')
            return

        if self.is_dirty():
            self._data = LibraryUtils.read_json(self.data_path())
            self.set_dirty(False)

        return self._data

    def save(self, data):
        """
        Write the given data dict object to the data on disk
        :param data: dict
        """

        if not self.path():
            tpQtLib.logger.info('No path set for saving the data to disk')

        LibraryUtils.save_json(self.data_path(), data)
        self.set_dirty(True)

    def is_search_enabled(self):
        """
        Returns whether search functionality is enabled or not
        :return: bool
        """

        return self._search_enabled

    def set_search_enabled(self, flag):
        """
        Sets whether search functionality is enabled or not
        :param flag: bool
        """

        self._search_enabled = flag

    def recursive_depth(self):
        """
        Return the recursive search depth
        :return: int
        """

        return LibraryConsts.DEFAULT_RECURSIVE_DEPTH

    def add_item(self, item):
        """
        Add the given item to the library data
        :param item: LibraryItem
        """

        self.save_item_data([item])

    def add_items(self, items):
        """
        Add the given items to the library data
        :param items: list(LibraryItem)
        """

        self.save_item_data(items)

    def update_item(self, item):
        """
        Update the given item in the library data
        :param item: LibraryItem
        """

        self.save_item_data([item])

    def save_item_data(self, items, emit_data_changed=True):
        """
        Add the given items to the library data
        :param items: list(LibraryItem)
        :param emit_data_changed: bool
        """

        tpQtLib.logger.debug('Saving Items: {}'.format(items))

        data_ = self.read()
        for item in items:
            path = item.path()
            data = item.item_data()
            data_.setdefault(path, {})
            data_[path].update(data)

        self.save(data_)

        if emit_data_changed:
            self.search()
            self.dataChanged.emit()

    def load_item_data(self, items):
        """
        load the item data from the library data to the given items
        :param items: list(LibraryItem)
        """

        tpQtLib.logger.debug('Loading item data: {}'.format(items))

        data = self.read()
        for item in items:
            key = item.id()
            if key in data:
                item.set_item_idata(data[key])

    def find_items(self, queries):
        """
        Get the items that match the given queries
        :param queries: list(dict)
        :return: list(LibraryItem)
        """

        fields = list()
        results = list()

        queries = copy.copy(queries)
        queries.extend(self._global_queries.values())

        items = self.create_items()
        for item in items:
            match = self.match(item.item_data(), queries)
            if match:
                results.append(item)
            fields.extend(item.item_data().keys())

        self._fields = list(set(fields))

        if self.sort_by():
            results = self.sorted(results, self.sort_by())

        return results

    def queries(self, exclude=None):
        """
        Return all queries for the data excluding the given ones
        :param exclude: list(str) or None
        :return: list(dict)
        """

        queries = list()
        exclude = exclude or list()

        for query in self._queries.values():
            if query.get('name') not in exclude:
                queries.append(query)

        return queries

    def query_exists(self, name):
        """
        Check if the given queryh name exists
        :param name: str
        :return: bool
        """

        return name in self._queries

    def add_to_global_query(self, query):
        """
        Add a global query to library
        :param query: dict
        """

        self._global_queries[query['name']] = query

    def add_query(self, query):
        """
        Add a search query to the library
        >>> add_query({
        >>>    'name': 'Test Query',
        >>>    'operator': 'or',
        >>>    'filters': [
        >>>        ('folder', 'is', '/lib/proj/test'),
        >>>        ('folder', 'startswith', '/lib/proj/test'),
        >>>    ]
        >>>})
        :param query: dict
        """

        self._queries[query['name']] = query

    def remove_query(self, name):
        """
        Remove the query with the given name
        :param name: str
        """

        if name in self._queries:
            del self._queries[name]

    def search(self):
        """
        Run a search using the queries added to library data
        """

        if not self.is_search_enabled():
            return

        t = time.time()
        tpQtLib.logger.debug('Searching items ...')
        self.searchStarted.emit()
        self._results = self.find_items(self.queries())
        self._grouped_results = self.group_items(self._results, self.group_by())
        self.searchFinished.emit()
        self._search_time = time.time() - t
        self.searchTimeFinished.emit()
        tpQtLib.logger.debug('Search time: {}'.format(self._search_time))

    def results(self):
        """
        Return the items found after a search is executed
        :return: list(LibraryItem)
        """

        return self._results

    def grouped_results(self):
        """
        Return the results grouped after a search is executed
        :return: dict
        """

        return self._grouped_results

    def search_time(self):
        """
        Return the time taken to run a search
        :return: float
        """

        return self._search_time

    def sync(self, percent_callback=lambda message, percent: None):
        """
        Sync the file sytem wit hthe library data
        """

        if not self.path():
            tpQtLib.logger.warning('No path set for syncing data')
            return

        data = self.read()

        for path in data.keys():
            if not os.path.exists(path):
                del data[path]

        depth = self.recursive_depth()
        items = list(self._library_window.manager().find_items(self.path(), depth=depth))
        count = len(items)
        for i, item in enumerate(items):
            percent = (float(i+1)/float(count))
            percent_callback('', percent)
            path = item.path()
            item_data = data.get(path, {})
            item_data.update(item.item_data())
            data[path] = item_data

        percent_callback('Post Sync', -1)
        self.post_sync(data)

        percent_callback('Saving Cache', -1)
        self.save(data)

        self.dataChanged.emit()

    def post_sync(self, data):
        """
        This function is called after a data sync, but before save and dataChanged signal is emitted
        :param data: dict
        """

        pass

    def create_items(self):
        """
        Create all teh items for the library model
        :return: list(LibraryItem)
        """

        if self.is_dirty():
            paths = self.read().keys()
            items = self._library_window.manager().items_from_paths(
                paths=paths,
                library=self,
                library_window=self._library_window
            )
            self._items = list(items)
            self.load_item_data(self._items)

        return self._items

    def clear(self):
        """
        Clear all the item data
        """

        self._items = list()
        self._results = list()
        self._grouped_results = dict()
        self.dataChanged.emit()


class LibraryItemSignals(QObject, object):
    """
    Class that contains definition for LibraryItem signals
    """

    saved = Signal(object)
    saving = Signal(object)
    loaded = Signal(object)
    copied = Signal(object, object, object)
    deleted = Signal(object)
    renamed = Signal(object, object, object)


class LibraryItemDelegate(QStyledItemDelegate, object):
    """
    Class that defines visual style in LibraryViewer of LibraryItems
    """

    def __init__(self):
        super(LibraryItemDelegate, self).__init__()

        self._viewer = None

    """
    ##########################################################################################
    OVERRIDES
    ##########################################################################################
    """

    def sizeHint(self, option, index):
        """
        Overrides base QStyledItemDelegate sizeHint function
        Return the size for the given id¡ndex
        :param option: QStylOptionViewItem
        :param index: QModelIndex
        :return: QSize
        """

        item = self.viewr().item_from_index(index)
        if isinstance(item, LibraryGroupItem):
            return item.sizeHint()

        return self.viewer().item_size_hint(index)

    def paint(self, painter, option, index):
        """
        Overrides base QStyledItemDelegate paint function
        Paint performs low-level painting for the given model index
        :param painter: QPainter
        :param option: QStyleOptionViewItem
        :param index: QModelIndex
        """

        item = self.viewer().item_from_index(index)
        item.paint(painter, option, index)

    """
    ##########################################################################################
    VIEWER
    ##########################################################################################
    """

    def viewer(self):
        """
        Returns LibraryViewer object associated to this delegate
        :return: LibraryViewer
        """

        return self._viewer

    def set_viewer(self, viewer):
        """
        Set LibraryViewer associated to this delegate
        :param viewer: LibraryViewer
        """

        self._viewer = viewer


class LibraryItem(QTreeWidgetItem, object):
    """
    Stores information to work on Library views
    """

    SortRole = LibraryConsts.ITEM_DEFAULT_SORT_ROLE
    DataRole = LibraryConsts.ITEM_DEFAULT_DATA_ROLE

    ThreadPool = QThreadPool()
    DefaultThumbnailPath = LibraryConsts.ITEM_DEFAULT_THUMBNAIL_PATH

    MAX_ICON_SIZE = LibraryConsts.ITEM_DEFAULT_MAX_ICON_SIZE
    DEFAULT_FONT_SIZE = LibraryConsts.ITEM_DEFAULT_FONT_SIZE
    DEFAULT_PLAYHEAD_COLOR = LibraryConsts.ITEM_DEFAULT_PLAYHEAD_COLOR

    DEFAULT_THUMBNAIL_COLUMN = LibraryConsts.ITEM_DEFAULT_THUMBNAIL_COLUMN
    ENABLE_THUMBNAIL_THREAD = LibraryConsts.ITEM_DEFAULT_ENABLE_THUMBNAIL_THREAD

    EnableDelete = LibraryConsts.ITEM_DEFAULT_ENABLE_DELETE
    EnableNestedItems = LibraryConsts.ITEM_DEFAULT_ENABLE_NESTED_ITEMS

    MenuName = LibraryConsts.ITEM_DEFAULT_MENU_NAME
    MenuOrder = LibraryConsts.ITEM_DEFAULT_MENU_ORDER
    MenuIconPath = LibraryConsts.ITEM_DEFAULT_MENU_ICON_PATH

    CreateWidgetClass = None
    PreviewWidgetClass = None

    _libraryItemSignals = LibraryItemSignals()
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
            raise LibraryException.ItemError('Cannot set an empty item path')

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

    DEFAULT_FONT_SIZE = LibraryConsts.GROUP_ITEM_DEFAULT_FONT_SIZE

    def __init__(self, *args):
        super(LibraryGroupItem, self).__init__(*args)

        self._children = list()

        self._font = self.font(0)
        self._font.setBold(True)

        self.setFont(0, self._font)
        self.setFont(1, self._font)
        self.set_drag_enabled(False)


class LibraryViewWidgetMixin(object):
    """
    Class that contains generic functionality for view widgets that
    work with QAbstractItemView
    """

    def __init__(self):
        self._hover_item = None
        self._mouse_press_button = None
        self._current_item = None
        self._current_selection = list()

    def wheelEvent(self, event):
        """
        Triggered on any wheel events for the current viewport
        :param event: QWheelEvent
        """

        if self.is_control_modifier():
            event.ignore()
        else:
            QAbstractItemView.wheelEvent(self, event)

        item = self.item_at(event.pos())
        self.item_update_event(item, event)

    def keyPressEvent(self, event):
        """
        Triggered when user key press events for the current viewport
        :param event: QKeyEvent
        """

        item = self.selectedItems()
        if item:
            self.item_key_press_event(item, event)

        valid_keys = [Qt.Key_Up, Qt.Key_Left, Qt.Key_Down, Qt.Key_Right]
        if event.isAccepted() and event.key() in valid_keys:
            QAbstractItemView.keyPressEvent(event)

    def mousePressEvent(self, event):
        """
        Triggered on user mouse press events for the current viewport
        :param event: QMouseEvent
        """

        self._mouse_press_button = event.button()
        item = self.item_at(event.pos())
        if item:
            self.item_mouse_press_event(item, event)
        QAbstractItemView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        """
        Triggered on user mouse release events for the current viewport
        :param event: QMouseEvent
        """

        self._mouse_press_button = None
        item = self.selected_item()
        if item:
            self.item_mouse_release_event(item, event)

    def mouseMoveEvent(self, event):
        """
        Triggered on user mouse move events for the current viewport
        :param event: QMouseEvent
        """

        if self._mouse_press_button == Qt.MiddleButton:
            item = self.selected_item()
        else:
            item = self.item_at(event.pos())

        self.item_update_event(item, event)

    def mouse_press_button(self):
        """
        Returns the mouse button that has been pressed
        :return: Qt.MouseButton
        """

        return self._mouse_press_button

    def clean_dirty_objects(self):
        """
        Removes any obejct that may have been deleted
        """

        if self._current_item:
            try:
                self._current_item.text(0)
            except RuntimeError:
                self._hover_item = None
                self._current_item = None
                self._current_selection = None

    def items_widget(self):
        """
        Returns parent widget of the library widget
        :return:
        """

        return self.parent()

    def is_control_modifier(self):
        """
        Returns whether control modifier is active or not
        :return: bool
        """

        modifiers = QApplication.keyboardModifiers()
        is_alt_modifier = modifiers == Qt.AltModifier
        is_ctrl_modifier = modifiers == Qt.ControlModifier
        return is_alt_modifier or is_ctrl_modifier






class LibraryTreeWidget(LibraryViewWidgetMixin, QTreeWidget):
    """
    Class that implemented library tree viewer widget
    This class is used by LibraryViewer class
    """

    def __init__(self, parent=None):
        QTreeWidget.__init__(self, parent)
        LibraryViewWidgetMixin.__init__(self)

        self._header_labels = list()
        self._hidden_columns = dict()

        self.setAutoScroll(False)
        self.setMouseTracking(True)
        self.setSortingEnabled(False)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        header = self.header()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self._on_show_header_menu)

        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    """
    ##########################################################################################
    MIXIN
    ##########################################################################################
    """

    def mouseMoveEvent(self, event):
        """
        Triggered when the user moves the mouse over the current viewport
        :param event: QMouseEvent
        """

        LibraryViewWidgetMixin.mouseMoveEvent(self, event)
        QTreeWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        """
        Triggerd when the user releases the mouse button on the viewport
        :param event: QMouseEvent
        """

        LibraryViewWidgetMixin.mouseReleaseEvent(self, event)
        QTreeWidget.mouseReleaseEvent(self, event)

    """
    ##########################################################################################
    BASE
    ##########################################################################################
    """

    def drawRow(self, painter, options, index):
        """
        Overrides base QTreeWidget drawDrow function
        :param painter: QPainter
        :param options: QStyleOption
        :param index: QModelIndex
        """

        item = self.itemFromIndex(index)
        item.paint_row(painter, options, index)

    def setColumnHidden(self, column, value):
        """
        Overrides base QTreeWidget setColumnHidden function
        :param column: int or str
        :param value: bool
        """

        if isinstance(column, (unicode, str)):
            column = self.column_from_label(column)

        label = self.label_from_column(column)
        self._hidden_columns[label] = value

        super(LibraryTreeWidget, self).setColumnHidden(column, value)

        width = self.columnWidth(column)
        if width < LibraryConsts.TREE_MINIMUM_WIDTH:
            width = LibraryConsts.TREE_DEFAULT_WIDTH
            self.setColumnWidth(column, width)

    def resizeColumnToContents(self, column):
        """
        Overrides base QTreeWidget resizeColumnToContents function
        Resize the given column to the data of that column
        :param column: int or str
        """

        width = 0
        for item in self.items():
            text = item.text(column)
            font = item.font(column)
            metrics = QFontMetrics(font)
            text_width = metrics.width(text) + item.padding()
            width = max(width, text_width)

        self.setColumnWidth(column, width)

    def setHeaderLabels(self, labels):
        """
        Overrides base QTreeWidget setHeaderLabels function
        :param labels: list(str)
        """

        labels = self._remove_duplicates(labels)
        column_settings = self.column_settings()
        super(LibraryTreeWidget, self).setHeaderLabels(labels)
        self._header_labels = labels
        self.update_column_hidden()
        self.set_column_settings(column_settings)

    def items(self):
        """
        Overrides base QTreeWidget items function
        Return a list of all items in the tree widget
        :return: list(LibraryItem)
        """

        items = list()
        for item in self._items():
            if not isinstance(item, LibraryGroupItem):
                items.append(item)

        return items

    def selectedItems(self):
        """
        Overrides base QTreeWidget selectedItems function
        Returns all selected items
        :return: list(LibraryItem)
        """

        items = list()
        items_ = super(LibraryTreeWidget, self).selectedItems()

        for item in items_:
            if not isinstance(item, LibraryGroupItem):
                items.append(item)

        return items

    def clear(self, *args):
        """
        Clear tree items
        """

        super(LibraryTreeWidget, self).clear(*args)
        self.clean_dirty_objects()

    def set_items(self, items):
        """
        Add given items to the tree, clearing the tree first
        :param items: list(LibraryItem)
        """

        selected_items = self.selectedItems()
        self.take_top_level_items()
        self.addTopLevelItems(items)
        self.set_items_selected(selected_items, True)

    def set_items_selected(self, items, value, scroll_to=True):
        """
        Selects the given library items
        :param items: list(LibraryItem)
        :param value: bool, Whether to select or deselect the items
        :param scroll_to: bool, Whether to scroll or not to selected items
        """

        for item in items:
            self.setItemSelected(item, value)
        if scroll_to:
            self.items_widget().scroll_to_selected_item()

    def selected_item(self):
        """
        Returns the last non-hidden selected item
        :return: LibraryItem
        """

        items = self.selectedItems()
        if items:
            return items[-1]

    def settings(self):
        """
        Returns the current widget settings
        :return: dict
        """

        settings = dict()
        settings['columnSettings'] = self.column_settings()

        return settings

    def set_settings(self, settings):
        """
        Sets the current widget settings
        :param settings: dict
        :return: dict
        """

        column_settings = settings.get('columnSettings', dict())
        self.set_column_settings(column_settings)

        return settings

    def column_from_label(self, label):
        """
        Returns the column for the given label
        :param label: str
        :return: int
        """

        try:
            return self._header_labels.index(label)
        except ValueError:
            return -1

    def label_from_column(self, column):
        """
        Returns the column label for the given column
        :param column: int
        :return: str
        """

        if column is not None:
            return self.headerItem().text(column)

    def item_row(self, item):
        """
        Returns the row for the given item
        :param item: LibraryItem
        :return: int
        """

        index = self.indexFromItem(item)
        return index.row()

    def row_at(self, pos):
        """
        Returns the row for the given position
        :param pos: QPoint
        :return: int
        """

        item = self.itemAt(pos)
        return self.item_row(item)

    def take_top_level_items(self):
        """
        Returns all items from the tree widget
        :return: list(LibraryItem)
        """

        items = list()
        for item in self._items():
            items.append(self.takeTopLevelItem(1))
        items.append(self.takeTopLevelItem(0))

        return items

    def text_from_items(self, items, column, split=None, duplicates=False):
        """
        Returns all the text data for the given items and column
        :param items: list(LibraryItem)
        :param column: int or str
        :param split: str
        :param duplicates: bool
        :return: list(str)
        """

        results = list()

        for item in items:
            text = item.text(column)
            if text and split:
                results.extend(text.split(split))
            elif text:
                results.append(text)
        if not duplicates:
            results = list(set(results))

        return results

    def text_from_column(self, column, split=None, duplicates=False):
        """
        Returns all data for the given column
        :param column: int or str
        :param split: str
        :param duplicates: bool
        :return: list(str)
        """

        items = self.items()
        results = self.text_from_items(items, column, split=split, duplicates=duplicates)

        return results

    def header_labels(self):
        """
        Returns all header labels
        :return: list(str)
        """

        return self._header_labels

    def is_header_label(self, label):
        """
        Returns whether given label is a valid header label or not
        :param label: str
        :return: bool
        """

        return label in self._header_labels

    def column_labels(self):
        """
        Returns all header labels for the tree widget
        :return: list(str)
        """

        return self.header_labels()

    def label_from_column(self, column):
        """
        Returns the column label for the given column
        :param column: int
        :return: str
        """

        if column is not None:
            return self.headerItem().text(column)

    def column_from_label(self, label):
        """
        Returns the column for the given label
        :param label: str
        :return: int
        """

        try:
            return self._header_labels.index(label)
        except ValueError:
            return -1

    def show_all_columns(self):
        """
        Show all available columns
        """

        for column in range(self.columnCount()):
            self.setColumnHidden(column, False)

    def hide_all_columns(self):
        """
        Hide all available columns
        """

        for column in range(1, self.columnCount()):
            self.setColumnHidden(column, True)

    def update_column_hidden(self):
        """
        Updates the hidden state for all the current columns
        """

        self.show_all_columns()
        column_labels = self._hidden_columns.keys()
        for column_label in column_labels:
            self.setColumnHidden(column_label, self._hidden_columns[column_label])

    def _items(self):
        """
        Internal function that returns a list of all items in the tree widget
        :return: list(LibraryItem)
        """

        return self.findItems('*', Qt.MatchWildcard | Qt.MatchRecursive)

    def _remove_duplicates(self, labels):
        """
        Internal function that removes dupñlicates from a list (preserving its order)
        :param labels: list(str)
        :return: list(str)
        """

        s = set()
        sadd = s.add
        return [x for x in labels if x.strip() and not (x in s or sadd(x))]

    """
    ##########################################################################################
    SETTINGS
    ##########################################################################################
    """

    def column_settings(self):
        """
        Returns the settings for each column
        :return: dict
        """

        column_settings = dict()

        for column in range(self.columnCount()):
            label = self.label_from_column(column)
            hidden = self.isColumnHidden(column)
            width = self.columnWidth(column)
            column_settings[label] = {
                'index': column,
                'hidden': hidden,
                'width': width
            }

        return column_settings

    def set_column_settings(self, settings):
        """
        Set the settings for each column
        :param settings: dict
        """

        for label in settings:
            if self.is_header_label(label):
                column = self.column_from_label(label)
                width = settings[label].get('width', 100)
                if width < 5:
                    width = 100
                self.setColumnWidth(column, width)
                hidden = settings[label].et('hidden', False)
                self.setColumnHidden(column, hidden)
            else:
                tpQtLib.logger.debug('Cannot set the column setting for header label: {}'.format(label))

    """
    ##########################################################################################
    MENUS
    ##########################################################################################
    """

    def show_header_menu(self, pos):
        """
        Creates and show the header menu at the cursor position
        :param pos: QPoint
        :return: QMenu
        """

        header = self.header()
        column = header.logicalIndexAt(pos)
        menu = self._create_header_menu(column)
        menu.addSeparator()
        sub_menu = self._create_hide_column_menu()
        menu.addMenu(sub_menu)
        menu.exec_(QCursor.pos())

    def _create_header_menu(self, column):
        """
        Internal function that creates a new header menu
        :param column, iht
        :return: QMenu
        """

        menu = QMenu(self)
        label = self.label_from_column(column)
        hide_action = menu.addAction('Hide "{}"'.format(label))
        hide_action.triggered.connect(partial(self.setColumnHidden, column, True))
        menu.addSeparator()
        resize_action = menu.addAction('Resize to Contents')
        resize_action.triggered.connect(partial(self.resizeColumnToContents, column))

        return menu

    def _create_hide_column_menu(self):
        """
        Internal function that creates the hide column menu
        :return: QMenu
        """

        menu = QMenu('Show/Hide Column', self)
        show_all_action = menu.addAction('Show All')
        show_all_action.triggered.connect(self.show_all_columns)
        hide_all_action = menu.addAction('Hide All')
        hide_all_action.triggered.connect(self.hide_all_columns)
        menu.addSeparator()
        for column in range(self.columnCount()):
            label = self.label_from_column(column)
            is_hidden = self.isColumnHidden(column)
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(not is_hidden)
            action.triggered.connect(partial(self.setColumnHidden, column, not is_hidden))

        return menu

    """
    ##########################################################################################
    CLIPBOARD
    ##########################################################################################
    """

    def copy_text(self, column):
        """
        Copy the given column text to clipboard
        :param column: int or text
        """

        items = self.selectedItems()
        text = '\n'.join([item.text(column) for item in items])
        clipboard = QApplication.clipboard()
        clipboard.setText(text, QClipboard.Clipboard)

    def _create_copy_text_men(self):
        """
        Creates a menu to cpoy the selected item data to the clipboard
        :return: QMenu
        """

        menu = QMenu('Copy Text', self)
        if self.selectedItems():
            for column in range(self.columnCount()):
                label = self.label_from_column(column)
                action = menu.addAction(label)
                action.triggered.connect(partial(self.copy_text, column))
        else:
            action = menu.addAction('No items selected')
            action.setEnabled(False)

        return menu

    """
    ##########################################################################################
    CALLBACKS
    ##########################################################################################
    """

    def _on_show_header_menu(self):
        """
        Internal callback function that is called when the user right click TreeWidget
        header
        """

        print('Showing Header Menu ...')

    def _on_item_clicked(self, item):
        """
        Internal callback function that is called when an item of the tree is clicked
        """

        item.clicked()

    def _on_item_double_clicked(self, item):
        """
        Internal callback function that is called when an item of the tree is double clicked
        """

        item.double_clicked()


class LibraryListView(LibraryViewWidgetMixin, QListView):
    """
    Class that implemented library list view widget
    This class is used by LibraryViewer class
    """

    DEFAULT_DRAG_THRESHOLD = LibraryConsts.LIST_DEFAULT_DRAG_THRESHOLD

    itemMoved = Signal(object)
    itemDropped = Signal(object)
    itemClicked = Signal(object)
    itemDoubleClicked = Signal(object)

    def __init__(self, *args):
        QListView.__init__(self, *args)
        LibraryViewWidgetMixin.__init__(self)

        self.setSpacing(5)
        self.setMouseTracking(True)
        self.setSelectionRectVisible(True)
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setSelectionMode(QListView.ExtendedSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)

        self._tree_widget = None
        self._rubber_band = None
        self._rubber_band_start_pos = None
        self._rubber_band_color = QColor(Qt.white)
        self._custom_sort_order = list()

        self._drag = None
        self._drag_start_pos = None
        self._drag_start_index = None
        self._drop_enabled = True

        self.clicked.connect(self._on_index_clicked)
        self.itemDoubleClicked.connect(self._on_index_double_clicked)

    """
    ##########################################################################################
    BASE
    ##########################################################################################
    """

    def scroll_to_item(self, item, pos=None):
        """
        Ensures that the item is visible
        :param item: LibraryItem
        :param pos: QPoint or None
        """

        index = self.index_from_item(item)
        pos = pos or QAbstractItemView.PositionAtCenter

        self.scrollTo(index, pos)

    """
    ##########################################################################################
    TREE WIDGET
    ##########################################################################################
    """

    def tree_widget(self):
        """
        Return the tree widget that contains the items
        :return: LibraryTreeWidget
        """

        return self._tree_widget

    def set_tree_widget(self, tree_widget):
        """
        Set the tree widget that contains the items
        :param tree_widget: LibraryTreeWidget
        """

        self._tree_widget = tree_widget
        self.setModel(tree_widget.model())
        self.setSelectionModel(tree_widget.selectionModel())

    def items(self):
        """
        Return all the items
        :return: list(LibraryItem)
        """

        return self.tree_widget().items()

    def item_at(self, pos):
        """
        Returns a pointer to the item at the coordinates p
        The coordinates are relative to the tree widget's viewport
        :param pos: QPoint
        :return: LibraryItem
        """

        index = self.indexAt(pos)
        return self.item_from_index(index)

    def index_from_item(self, item):
        """
        Returns QModelIndex associated with the given item
        :param item: LibraryItem
        :return: QModelIndex
        """

        return self.tree_widget().index_from_item(item)

    def item_from_index(self, index):
        """
        Return a pointer to the LibraryItem associated with the given model index
        :param index: QModelIndex
        :return: LibraryItem
        """

        return self.tree_widget().item_from_index(index)

    """
    ##########################################################################################
    CALLBACKS
    ##########################################################################################
    """

    def _on_index_clicked(self, index):
        """
        Callback function that is called when the user clicks on an item
        :param index: QModelIndex
        """

        item = self.item_from_index(index)
        item.clicked()
        self.set_items_selected([item], True)
        self.itemClicked.emit(item)

    def _on_index_double_clicked(self, index):
        """
        Callback function that is called when the user double clicks on an item
        :param index: QModelIndex
        """

        item = self.item_from_index(index)
        self.set_item_selected([item], True)
        item.doubleClicked()
        self.itemDoubleClicked.emit(item)


class LibraryImageSequenceWidget(QToolButton, object):

    DEFAULT_PLAYHEAD_COLOR = QColor(255, 255, 255, 220)

    DEFAULT_STYLE = """
    QToolBar {
        border: 0px solid black; 
        border-radius:2px;
        background-color: rgb(0,0,0,100);
    }
    
    QToolButton {
        background-color: transparent;
    }
    """

    def __init__(self, *args):
        super(LibraryImageSequenceWidget, self).__init__(*args)

        self.setMouseTracking(True)

        self._image_sequence = image.ImageSequence('')
        self._image_sequence.frameChanged.connect(self._on_frame_changed)

        self._toolbar = QToolBar(self)
        self._toolbar.setStyleSheet(self.DEFAULT_STYLE)
        animation.fade_out_widget(self._toolbar, duration=0)

        spacer = QWidget()
        spacer.setMaximumWidth(4)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._toolbar.addWidget(spacer)

        spacer1 = QWidget()
        spacer1.setMaximumWidth(4)
        spacer1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._first_spacer = self._toolbar.addWidget(spacer1)

        self.set_size(150, 150)

    def set_size(self, w, h):
        """
        Set the size of the widget and updates icon size at the same time
        :param w: int
        :param h: int
        """

        self._size = QSize(w, h)
        self.setIconSize(self._size)
        self.setFixedSize(self._size)

    def _on_frame_changed(self, frame):
        pass


class LibraryViewer(base.BaseWidget, object):
    """
    Class that implements library viewer widget
    """

    IconMode = LibraryConsts.DEFAULT_ICON_MODE
    TableMode = LibraryConsts.DEFAULT_TABLE_MODE

    DEFAULT_PADDING = LibraryConsts.VIEWER_DEFAULT_PADDING
    DEFAULT_ZOOM_AMOUNT = LibraryConsts.VIEWER_DEFAULT_ZOOM_AMOUNT
    DEFAULT_TEXT_HEIGHT = LibraryConsts.VIEWER_DEFAULT_TEXT_HEIGHT
    DEFAULT_WHEEL_SCROLL_STEP = LibraryConsts.VIEWER_DEFAULT_WHEEL_SCROLL_STEP
    DEFAULT_MIN_SPACING = LibraryConsts.VIEWER_DEFAULT_MIN_SPACING
    DEFAULT_MAX_SPACING = LibraryConsts.VIEWER_DEFAULT_MAX_SPACING
    DEFAULT_MIN_LIST_SIZE = LibraryConsts.VIEWER_DEFAULT_MIN_LIST_SIZE
    DEFAULT_MIN_ICON_SIZE = LibraryConsts.VIEWER_DEFAULT_MIN_ICON_SIZE

    DEFAULT_TEXT_COLOR = LibraryConsts.VIEWER_DEFAULT_TEXT_COLOR
    DEFAULT_SELECTED_TEXT_COLOR = LibraryConsts.VIEWER_DEFAULT_SELECTED_TEXT_COLOR
    DEFAULT_BACKGROUND_COLOR = LibraryConsts.VIEWER_DEFAULT_BACKGROUND_COLOR
    DEFAULT_BACKGORUND_HOVER_COLOR = LibraryConsts.VIEWER_DEFAULT_BACKGROUND_HOVER_COLOR
    DEFAULT_BACKGROUND_SELECTED_COLOR = LibraryConsts.VIEWER_DEFAULT_BACKGROUND_SELECTED_COLOR

    TREE_WIDGET_CLASS = LibraryTreeWidget
    LIST_VIEW_CLASS = LibraryListView
    DELEGATE_CLASS = LibraryItemDelegate


    itemClicked = Signal(object)
    itemDoubleClicked = Signal(object)
    zoomChanged = Signal(object)
    spacingChanged = Signal(object)
    groupClicked = Signal(object)

    def __init__(self, parent=None):

        self._dpi = 1
        self._padding = self.DEFAULT_PADDING

        self._library = None
        self._tree_widget = None
        self._list_widget = None
        self._delegate = None
        self._is_item_text_visible = True
        self._toast_enabled = True

        self._zoom_amount = self.DEFAULT_ZOOM_AMOUNT
        self._icon_size = QSize(self._zoom_amount, self._zoom_amount)
        self._item_size_hint = QSize(self._zoom_amount, self._zoom_amount)

        self._text_color = self.DEFAULT_TEXT_COLOR
        self._text_selected_color = self.DEFAULT_SELECTED_TEXT_COLOR
        self._background_color = self.DEFAULT_BACKGROUND_COLOR
        self._background_hover_color = self.DEFAULT_BACKGORUND_HOVER_COLOR
        self._background_selected_color = self.DEFAULT_BACKGROUND_SELECTED_COLOR

        super(LibraryViewer, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        return main_layout

    def ui(self):
        super(LibraryViewer, self).ui()

        self._tree_widget = self.TREE_WIDGET_CLASS(self)

        self._list_view = self.LIST_VIEW_CLASS(self)
        self._list_view.set_tree_widget(self._tree_widget)

        self._delegate = self.DELEGATE_CLASS()

        self._toast_widget = toast.ToastWidget(self)
        self._toast_widget.hide()

        self.main_layout.addWidget(self._tree_widget)
        self.main_layout.addWidget(self._list_view)

        header = self.tree_widget().header()

    """
    ##########################################################################################
    BASE
    ##########################################################################################
    """

    def library(self):
        """
        Returns the library attached to the viewer
        :return: variant
        """

        return self._library

    def set_library(self, library):
        """
        Sets the data that will be showed in viewer
        :param library:
        """

        self._library = library
        self.set_column_labels(library.Fields)
        library.searchFinished.connect(self._on_update_items)

    def is_icon_view(self):
        """
        Returns whether widget is in icon mode or not
        :return: bool
        """

        return not self._list_view.isHidden()

    def is_table_view(self):
        """
        Returns whether widget is in list mode or not
        :return: bool
        """

        return not self._tree_widget.isHidden()

    def set_view_mode(self, mode):
        """
        Sets the view mode for this widget
        :param mode: str
        """

        if mode == self.IconMode:
            self.set_zoom_amount(self.DEFAULT_MIN_ICON_SIZE)
        elif mode == self.TableMode:
            self.set_zoom_amount(self.DEFAULT_MIN_ICON_SIZE)

    def set_list_mode(self):
        """
        Sets the tree widget visible
        """

        self._list_view.hide()
        self._tree_widget.show()
        self._tree_widget.setFocus()

    def set_icon_mode(self):
        """
        Sets the list view visible
        """

        self._tree_widget.hide()
        self._list_view.show()
        self._list_view.setFocus()

    def zoom_amount(self):
        """
        Returns the zoom amount for the widget
        :return: int
        """

        return self._zoom_amount

    def set_zoom_amount(self, value):
        """
        Sets the zoom amount for the widget
        :param value: int
        """

        if value < self.DEFAULT_MIN_LIST_SIZE:
            value = self.DEFAULT_MIN_LIST_SIZE

        self._zoom_amount = value
        size = QSize(value * self.dpi(), value * self.dpi())
        self.set_icon_size(size)
        if value >= self.DEFAULT_MIN_LIST_SIZE:
            self._set_view_mode(self.IconMode)
        else:
            self._set_view_mode(self.TableMode)
        column_width = value * self.dpi() + self.item_text_height()
        self._tree_widget.setIndentation(0)
        self._tree_widget.setColumnWidth(0, column_width)
        self.scroll_to_selected_item()
        self.show_toast_message('Size: {}%'.format(value))

    def vertical_scrollbar(self):
        """
        Returns the active vertical scroll bar
        :return: QScrollBar
        """

        if self.is_table_view():
            return self.tree_widget().verticalScrollBar()
        else:
            return self.list_view().verticalScrollBar()

    def visual_item_rect(self, item):
        """
        Returns the visual rect for the item
        :param item: LibraryItem
        :return: QRect
        """

        if self.is_table_view():
            visual_rect = self.tree_widget().visual_item_rect(item)
        else:
            index = self.tree_widget().index_from_item(item)
            visual_rect = self.list_view().visualRect(index)

        return visual_rect

    def is_item_visible(self, item):
        """
        Returns whether given item is visible or not
        :param item: LibraryItem
        :return: bool
        """

        height = self.height()
        item_rect = self.visual_item_rect(item)
        scroll_bar_y = self.vertical_scrollbar().value()
        y = (scroll_bar_y - item_rect.y()) + height

        return y > scroll_bar_y and y < scroll_bar_y + height

    def scroll_to_item(self, item):
        """
        Ensures the given item is visible
        :param item: LibraryItem
        """

        position = QAbstractItemView.PositionAtCenter
        if self.is_table_view():
            self.tree_widget().scroll_to_item(item, position)
        elif self.is_icon_view():
            self.list_view().scroll_to_item(item, position)

    def scroll_to_selected_item(self):
        """
        Ensures that selected item is visible
        """

        item = self.selected_item()
        if item:
            self.scroll_to_item(item)

    def item_at(self, pos):
        """
        Returns the current item at the given position
        :param pos: QPoint
        :return: LibraryItem
        """

        if self.is_icon_view():
            return self.list_view().item_at(pos)
        else:
            return self.tree_widget().item_at(pos)

    def create_group_item(self, text, children=None):
        """
        Internal function that creates a new item for the given text and children
        :param text: str
        :param children: list(LibraryItem)
        """

        group_item = LibraryGroupItem()
        group_item.set_name(text)
        group_item.set_stretch_to_widget(self)
        group_item.set_children(children)

        return group_item

    def _set_view_mode(self, mode):
        """
        Internal function that sets the view mode ro this widget
        :param mode: str
        :return: str
        """

        if mode == self.IconMode:
            self.set_icon_mode()
        elif mode == self.TableMode:
            self.set_list_mode()

    """
    ##########################################################################################
    DPI
    ##########################################################################################
    """

    def dpi(self):
        """
        Returns zoom multiplier
        :return: int
        """

        return self._dpi

    def set_dpi(self, dpi):
        """
        Sets the zoom multiplier
        :param dpi: int
        """

        self._dpi = dpi
        self.refresh_size()

    """
    ##########################################################################################
    TOAST WIDGET
    ##########################################################################################
    """

    def toast_enabled(self):
        """
        Returns whether toast message widget is enabled or not
        :return: bool
        """

        return self._toast_enabled

    def set_toast_enabled(self, flag):
        """
        Sets whether toast widget is enabled or not
        :param flag: bool
        """

        self._toast_enabled = flag

    def show_toast_message(self, text, duration=300):
        """
        Shows a toast with the given text for the given duration
        :param text: str
        :param duration: None or int
        """

        if self.toast_enabled():
            self._toast_widget.set_duration(duration)
            self._toast_widget.setText(text)
            self._toast_widget.show()

    """
    ##########################################################################################
    TREE WIDGET
    ##########################################################################################
    """

    def tree_widget(self):
        """
        Returns the list view that contains the items
        :return: TreeWidget
        """

        return self._tree_widget

    def column_from_label(self, *args):
        """
        Returns column from given label text
        :return: int
        """

        return self.tree_widget().column_from_label(*args)

    def set_column_hidden(self, column, hidden):
        """
        Hides/Shows specific column in tree widget
        :param column: int
        :param hidden: bool
        """

        self.tree_widget().setColumnHidden(column, hidden)

    def set_column_labels(self, labels):
        """
        Set the columns for the viewer
        :param labels: list(str)
        """

        labels_set = set()
        set_add = labels_set.add
        labels = [x for x in labels if x.strip() and not (x in labels_set or set_add(x))]
        self.tree_widget().setHeaderLabels(labels)

    def index_from_item(self, item):
        """
        Returns the QModelIndex associated with the given item
        :param item: LibraryItem
        :return: QModelIndex
        """

        return self._tree_widget.index_from_item(item)

    def items(self):
        """
        Returns all the items in the tree widget
        :return: list(Item)
        """

        return self._tree_widget.items()

    def add_item(self, item):
        """
        Add the item to the tree widget
        :param item: LibraryItem
        """

        self.add_items([item])

    def add_items(self, items):
        """
        Add the given items to the items widget
        :param items: list(LibraryItem)
        """

        self._tree_widget.addTopLevelItems(items)

    def selected_item(self):
        """
        Returns the last non-hidden selected item
        :return: LibraryItem
        """

        return self._tree_widget.selected_item()

    def selected_items(self):
        """
        Returns a list with all selected non-hiden items
        :return: list(QTreeWidgetItem)
        """

        return self._tree_widget.selectedItems()

    def clear_selection(self):
        """
        Cleras the user selection
        """

        self._tree_widget.clearSelection()

    def selection_model(self):
        """
        Returns the current selection model
        :return: QItemSelectionModel
        """

        return self._tree_widget.selectionModel()

    def model(self):
        """
        Returns the model the viewer is representing
        :return: QAbstractItemModel
        """

        return self._tree_widget.model()

    def update_items(self):
        """
        Sets the items to the viewer
        """

        selected_items = self.selected_items()
        self.clear_selection()

        results = self.library().grouped_results()

        items = list()

        for group in results:
            if group != 'None':
                group_item = self.create_group_item(group)
                items.append(group_item)
            items.extend(results[group])

        self.tree_widget().set_items(items)

        if selected_items:
            self.select_items(selected_items)
            self.scroll_to_selected_item()

    def clear(self):
        """
        Clear all elements in tree widget
        """

        self.tree_widget().clear()

    def _on_update_items(self):
        self.update_items()

    """
    ##########################################################################################
    LIST WIDGET
    ##########################################################################################
    """

    def list_view(self):
        """
        Returns the list view that contains the items
        :return: LibraryListView
        """

        return self._list_view

    def set_locked(self, value):
        """
        Disables drag and drop
        :param value: bool
        """

        self.list_view().setDragEnabled(not value)
        self.list_view().setDropEnabled(not value)






class LibrarySearchWidget(QLineEdit, object):

    SPACE_OPEARTOR = 'and'
    PLACEHOLDER_TEXT = 'Search'

    def __init__(self, *args):
        super(LibrarySearchWidget, self).__init__(*args)

        tip = 'Search all current items'
        self.setToolTip(tip)
        self.setStatusTip(tip)


class LibraryStatusWidget(statusbar.StatusWidget, object):

    DEFAULT_DISPLAY_TIME = 10000

    INFO_CSS = ''

    WARNING_CSS = """
        color: rgb(240, 240, 240);
        background-color: rgb(240, 170, 0);
    """

    ERROR_CSS = """
        color: rgb(240, 240, 240);
        background-color: rgb(220, 40, 40);
        selection-color: rgb(220, 40, 40);
        selection-background-color: rgb(240, 240, 240);
    """

    def __init__(self, *args):
        super(LibraryStatusWidget, self).__init__(*args)

        self.setFixedHeight(19)
        self.setMinimumWidth(5)

        self.main_layout.setContentsMargins(1, 0, 0, 0)

        self._progress_bar = progressbar.ProgressBar(self)
        self._progress_bar.hide()
        self.main_layout.addWidget(self._progress_bar)

    def show_info_message(self, message, msecs=None):
        """
        Overrides progressbar.ProgressBar show_info_message function
        Set an info message to be displayed in the status widget
        :param message: str
        :param msecs: float
        """

        self.setStyleSheet('')
        super(LibraryStatusWidget, self).show_info_message(message, msecs)

    def show_warning_message(self, message, msecs=None):
        """
        Overrides progressbar.ProgressBar show_warning_message function
        Set a warning message to be displayed in the status widget
        :param message: str
        :param msecs: float
        """

        if self.is_blocking():
            return

        self.setStyleSheet(self.WARNING_CSS)
        super(LibraryStatusWidget, self).show_warning_message(message, msecs)

    def show_error_message(self, message, msecs=None):
        """
        Overrides progressbar.ProgressBar show_error_message function
        Set an error message to be displayed in the status widget
        :param message: str
        :param msecs: float
        """

        self.setStyleSheet(self.ERROR_CSS)
        super(LibraryStatusWidget, self).show_error_message(message, msecs)

    def progress_bar(self):
        """
        Returns the progress bar widget
        :return:  progressbar.ProgressBar
        """

        return self._progress_bar


class LibraryToolbarWidget(toolbar.ToolBar, object):

    def __init__(self, *args):
        super(LibraryToolbarWidget, self).__init__(*args)

        self._dpi = 1

    def dpi(self):
        """
        Returns the zoom multiplier
        :return: float
        """

        return self._dpi

    def set_dpi(self, dpi):
        """
        Set the zoom multiplier
        :param dpi: float
        """

        self._dpi = dpi

    def expand_height(self):
        """
        Overrides base toolbar.Toolbar expand_height function
        Returns the height of menu bar when is expanded
        :return: int
        """

        return int(self._expanded_height * self.dpi())

    def collapse_height(self):
        """
        Overrides base toolbar.Toolbar collapse_height function
        Returns the height of widget when collapsed
        :return: int
        """

        return int(self._collapsed_height * self.dpi())


class LibrarySidebarWidget(QWidget, object):
    def __init__(self, *args):
        super(LibrarySidebarWidget, self).__init__(*args)


class LibraryWindow(tpQtLib.MainWindow, object):

    LIBRARY_CLASS = Library
    VIEWER_CLASS = LibraryViewer
    SEARCH_WIDGET_CLASS = LibrarySearchWidget
    STATUS_WIDGET_CLASS = LibraryStatusWidget
    MENUBAR_WIDGET_CLASS = LibraryToolbarWidget
    SIDEBAR_WIDGET_CLASS = LibrarySidebarWidget

    class PreviewFrame(QFrame):
        pass

    class SidebarFrame(QFrame):
        pass

    def __init__(self, parent=None, name='', path='', **kwargs):

        self._dpi = 1.0
        self._items = list()
        self._name = name or LibraryConsts.LIBRARY_DEFAULT_NAME
        self._is_debug = False
        self._is_locked = False
        self._is_loaded = False
        self._preview_widget = None
        self._progress_bar = None
        self._current_item = None
        self._library = None
        self._refresh_enabled = False

        self._trash_enabled = LibraryConsts.TRASH_ENABLED
        self._recursive_search_enabled = LibraryConsts.DEFAULT_RECURSIVE_SEARCH_ENABLED

        self._items_hidden_count = 0
        self._items_visible_count = 0

        self._is_trash_folder_visible = False
        self._sidebar_widget_visible = True
        self._preview_widget_visible = True
        self._status_widget_visible = True

        super(LibraryWindow, self).__init__(name=name, parent=parent, **kwargs)

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

        self._status_widget = self.STATUS_WIDGET_CLASS(self)
        self._menubar_widget = self.MENUBAR_WIDGET_CLASS(self)
        self._sidebar_widget = self.SIDEBAR_WIDGET_CLASS(self)

        self._search_widget = self.SEARCH_WIDGET_CLASS(self)
        self._menubar_widget.addWidget(self._search_widget)

        self._splitter = QSplitter(Qt.Horizontal, self)
        self._splitter.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self._splitter.setHandleWidth(2)
        self._splitter.setChildrenCollapsible(False)

        self._splitter.insertWidget(0, self._sidebar_frame)
        self._splitter.insertWidget(1, self._viewer)
        self._splitter.insertWidget(2, self._preview_frame)

        self._splitter.setStretchFactor(0, False)
        self._splitter.setStretchFactor(1, True)
        self._splitter.setStretchFactor(2, False)

        self.main_layout.addWidget(self._menubar_widget)
        self.main_layout.addWidget(self._splitter)
        self.main_layout.addWidget(self._status_widget)

        self.set_library(lib)
        self._viewer.set_library(lib)

    def setup_signals(self):
        self._viewer.customContextMenuRequested.connect(self._on_show_items_context_menu)

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

    def icon_color(self):
        """
        Returns the icon color
        :return: Color
        """

        return LibraryConsts.ICON_COLOR


    """
    ##########################################################################################
    SETTINGS
    ##########################################################################################
    """

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

    def set_settings(self, settings):
        """
        Set the library window settings from the given dictionary
        :param settings: dict
        """

        defaults = copy.deepcopy(LibraryConsts.DEFAULT_SETTINGS)
        settings = LibraryUtils.update(defaults, settings)

        is_refresh_enabled = self.is_refresh_enabled()

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
            self.set_folders_widget_visible(sidebar_visible)

        menubar_visible = settings.get('menuBarWidgetVisible')
        if menubar_visible:
            self.set_menubar_widget_visible(menubar_visible)

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

    def reset_settings(self):
        """
        Reset the settings to the default settings
        """

        self.set_settings(self.DEFAULT_SETTINGS)

    def update(self):
        """
        Overrides base QMainWindow update function
        Update the library widget and the data
        """

        self.refresh_sidebar()
        self.update_window_title()

    def name(self):
        """
        Return the name of the library
        :return: str
        """

        if not self._library:
            return

        return self._library.name

    def path(self):
        """
        Returns the path being used by the library
        :return: str
        """

        if not self._library:
            return

        return self._library.path

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

        self.refresh()
        self.library().search()
        self.update_preview_widget()

    def set_create_widget(self, create_widget):
        """
        Set the widget that should be showed when creating a new item
        :param create_widget: QWidget
        """

        self.set_preview_widget_visible(True)
        self.viewer().clear_selection()

        fsize, rsize, psize = self._splitter.sizes()
        if psize < 150:
            self.set_sizes((fsize, rsize, 180))

        self.set_preview_widget(create_widget)

    def refresh(self):
        """
        Refresh all necessary items
        """

        if self.is_refresh_enabled():
            self.update()

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

        return LibraryConsts.TRASH_NAME in path.lower()

    def trash_path(self):
        """
        Returns the trash path for the library
        :return: str
        """

        path = self.path()
        return '{}/{}'.format(path, LibraryConsts.TRASH_NAME.title())

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

        if not LibraryConsts.DPI_ENABLED:
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

        name = self.name()

        title = 'Welcome'
        # title = title.format(self.manager().)

        print('SHOWING HELLO DILA')

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
                action_icon =icon.Icon(action.icon())
                action_icon.set_color(self.icon_color())
                action.setIcon(icon)
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

        if LibraryConsts.SETTINGS_DIALOG_ENABLED:
            action = context_menu.addAction('Settings')
            action.triggered.connect(self._on_show_settings_dialog)

        sync_action = context_menu.addAction('Sync')
        sync_action.triggered.connect(self.sync)


        context_menu.addSeparator()

        return context_menu

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
