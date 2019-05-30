#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager object for libraries
"""

from __future__ import print_function, division, absolute_import

import os
from collections import OrderedDict

from tpPyUtils import osplatform, path as path_utils

import tpQtLib

try:
    from tpPyUtils.externals.scandir import walk
except ImportError:
    from os import walk


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
            path = url.toLocalFile()

            if osplatform.is_windows():
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
                remove = False
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

    def find_items_in_folders(self, folders, depth=3, **kwargs):
        """
        Find and create new item instances by walking the given paths
        :param folders: list(str)
        :param depth: int
        :param kwargs: dict
        :return: Iterable(LibraryItem)
        """

        for folder in folders:
            for item in self.find_items(folder, depth=depth, **kwargs):
                yield item
