#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains main library object implementation
"""

from __future__ import print_function, division, absolute_import

import os
import time
import copy
from collections import OrderedDict

from Qt.QtCore import *

from tpDcc.libs import qt
from tpDcc.libs.python import decorators, path as path_utils
from tpDcc.libs.qt.widgets.library import consts, utils


class Library(QObject, object):

    Name = consts.LIBRARY_DEFAULT_NAME

    Fields = [
        'icon',
        'name',
        'path',
        'type',
        'folder',
        'category'
    ]

    SortFields = [
        'name',
        'path',
        'type',
        'folder',
        'category'
    ]

    GroupFields = [
        'type',
        'category'
    ]

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

        qt.logger.debug('Sort by: {}'.format(sort_by))
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
        qt.logger.debug('Sort items took {}'.format(time.time() - t))

        return items

    @staticmethod
    def group_items(items, fields):
        """
        Group the given items by the given field
        :param items: list(LibraryItem)
        :param fields: list(str)
        :return: dict
        """

        qt.logger.debug('Group by: {}'.format(fields))

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

        qt.logger.debug('Group Items Took {}'.format(time.time() - t))

        return results

    def manager(self):
        """
        Returns data manager used by this library
        :return: LibraryDataManager
        """

        if not self._library_window:
            return None

        return self._library_window.manager()

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

    def settings(self):
        """
        Returns the stetins for the data
        :return: dict
        """

        return {
            'sortBy': self.sort_by(),
            'groupBy': self.group_by()
        }

    def set_settings(self, settings):
        """
        Set the settings for the data
        :param settings: dict
        """

        value = settings.get('sortBy')
        if value:
            self.set_sort_by(value)
        value = settings.get('groupBy')
        if value:
            self.set_group_by(value)

    def distinct(self, field, queries=None, sort_by='name'):
        """
        Returns all values for the given field
        :param field: str
        :param queries: variant, None or list(dict)
        :param sort_by: str
        :return: list
        """

        results = dict()
        queries = queries or list()
        queries.extend(self._global_queries.values())

        items = self.create_items()
        if not items:
            return results

        for item in items:
            value = item.item_data().get(field)
            if value:
                results.setdefault(value, {'count': 0, 'name': value})
                match = self.match(item.item_data(), queries)
                if match:
                    results[value]['count'] += 1

        def sort_key(facet):
            return facet.get(sort_by)

        return sorted(results.values(), key=sort_key)

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

    def set_sort_by(self, fields):
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
            qt.logger.info('No path set for reading the data from disk')
            return self._data

        if self.is_dirty():
            self._data = utils.read_json(self.data_path())
            self.set_dirty(False)

        return self._data

    def save(self, data):
        """
        Write the given data dict object to the data on disk
        :param data: dict
        """

        if not self.path():
            qt.logger.info('No path set for saving the data to disk')

        utils.save_json(self.data_path(), data)
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

        return consts.DEFAULT_RECURSIVE_DEPTH

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

        qt.logger.debug('Saving Items: {}'.format(items))

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

        qt.logger.debug('Loading item data: {}'.format(items))

        data = self.read()
        for item in items:
            key = item.id()
            if key in data:
                item.set_item_data(data[key])

    def update_paths(self, paths, data):
        """
        Updates the given paths with the given data in the data
        :param paths: list(str)
        :param data: dict
        """

        data_ = self.read()
        paths = path_utils.normalize_paths(paths)
        for path in paths:
            if path in data_:
                data_[path].update(data)
            else:
                data_[path] = data

        self.save(data_)

    def add_paths(self, paths, data=None):
        """
        Add the given paths and the given data to the data
        :param paths: list(str)
        :param data: dict or None
        """

        data = data or dict()
        self.update_paths(paths, data)

    def copy_path(self, source, target):
        """
        Copy the given source path to the given target path
        :param source: str
        :param target:str
        :return: str
        """

        self.add_paths([target])
        return target

    def rename_item(self, item, target, extension=None):
        """
        Renames given item
        :param item: LibraryItem
        :param target: str
        :param extension: str
        """

        extension = extension or item.extension()
        if target and extension not in target:
            target += extension

        source = item.path()

        target = utils.rename_path(source, target)
        self.rename_path(source, target)

        item.set_path(target)
        item.save_item_data()

        return target

    def rename_path(self, source, target):
        """
        Renames the suorce path to the given target name
        :param source: str
        :param target: str
        :return: str
        """

        utils.rename_path_in_file(self.data_path(), source, target)
        self.set_dirty(True)

        return target

    def remove_path(self, path):
        """
        Removes the given path from the data
        :param path: str
        """

        self.remove_paths([path])

    def remove_paths(self, paths):
        """
        Removes the given paths from the data
        :param paths: list(str)
        """

        data = self.read()
        paths = path_utils.normalize_paths(paths)
        for path in paths:
            if path in data:
                del data[path]

        self.save(data)

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
        if not items:
            return results

        for item in items:
            match = self.match(item.item_data(), queries)
            if match:
                results.append(item)
            fields.extend(item.item_data().keys())

        self._fields = list(set(fields))

        if self.sort_by():
            results = self.sorted(results, self.sort_by())

        return results

    def find_items_by_path(self, item_path):
        """
        Returns item with given path
        :param item_path: str
        """

        found_items = list()

        items = self.create_items()
        if not items:
            return found_items

        for item in items:
            if item.path() == item_path:
                found_items.append(item)

        return found_items

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
        qt.logger.debug('Searching items ...')
        self.searchStarted.emit()
        self._results = self.find_items(self.queries())
        self._grouped_results = self.group_items(self._results, self.group_by())
        self.searchFinished.emit()
        self._search_time = time.time() - t
        self.searchTimeFinished.emit()
        qt.logger.debug('Search time: {}'.format(self._search_time))

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
            qt.logger.warning('No path set for syncing data')
            return

        data = self.read()

        for path in data.keys():
            if not os.path.exists(path):
                del data[path]

        depth = self.recursive_depth()
        items = list(self._library_window.manager().find_items(self.path(), depth=depth))
        count = len(items)
        for i, item in enumerate(items):
            percent = (float(i + 1) / float(count))
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
            data = self.read()
            # if not data:
            #     return
            paths = data.keys()
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
