#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager object for libraries
"""

from __future__ import print_function, division, absolute_import

import os
from collections import OrderedDict

from tpDcc.core import scripts
from tpDcc.libs import qt
from tpDcc.libs.python import fileio, folder, settings, osplatform, path as path_utils
from tpDcc.libs.qt.widgets.library import items

try:
    from tpDcc.libs.python.externals.scandir import walk
except ImportError:
    from os import walk


class LibraryManager(object):
    """
    Class that manages library items registration
    """

    def __init__(self, settings=None):
        super(LibraryManager, self).__init__()

        self._library_window = None
        self._settings = settings
        self._item_classes = OrderedDict()

        self.register_item(items.LibraryFolderItem)

    def library_window(self):
        """
        Returns library window
        :return: LibraryWindow
        """

        return self._library_window

    def set_library_window(self, library_window):
        """
        Sets library window
        :param window: LibraryWindow
        """

        self._library_window = library_window

    def settings(self):
        """
        Returns LibraryManager settings
        :return: JSONSettings
        """

        return self._settings

    def set_settings(self, settings):
        """
        Sets LibraryManager settings
        :param settings: JSONSettings
        """

        self._settings = settings

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

    def is_type_registered(self, data_type):
        """
        Returns whether there are classes that supports given data type
        :param data_type: str
        :return: bool
        """

        for cls in self.registered_items():
            if data_type == cls.DataType:
                return True

        return False

    def item_from_data_type(self, path, data_type):
        """
        Returns a new item instance given
        :param path: str
        :param data_type: str
        :return: LibraryItem or None
        """

        if not self.is_type_registered(data_type):
            return None

        valid_items = list()

        for cls in self.registered_items():
            if data_type == cls.DataType:
                valid_items.append(cls)

        if len(valid_items) > 1:
            qt.logger.warning(
                'Multiple data file supports data type {}:\n{}'.format(data_type, '\n'.join(valid_items)))
        valid_item = valid_items[0]

        return self.item_from_path(path, valid_item.Extension)

    def item_from_path(self, path, extension=None, **kwargs):
        """
        Return a new item instance for the given path
        :param path: str
        :param extension: str
        :param kwargs: dict
        :return: LibraryItem or None
        """

        if extension:
            full_path = path_utils.normalize_path(path + extension)
        else:
            full_path = path_utils.normalize_path(path)
        path = path_utils.normalize_path(path)
        for ignore in self.get_ignore_paths():
            if ignore in full_path:
                return None

        for cls in self.registered_items():
            if cls.match(full_path):
                lib_win = kwargs.get('library_window', self.library_window())
                kwargs['library_window'] = lib_win
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
                yield item

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
                qt.logger.warning(msg)

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
                if remove and filename in dirs:
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


class LibraryDataFolder(fileio.FileManager, object):
    def __init__(self, name, file_path, data_path=None):
        super(LibraryDataFolder, self).__init__(file_path=file_path)

        self.settings = None
        new_path = path_utils.join_path(file_path, name)
        self.file_path = path_utils.get_dirname(new_path)
        self.name = path_utils.get_basename(new_path)
        self.data_type = None

        # if data_path:
        #     tp.data_manager.add_directory(data_path)

        # Check if the given file path is a folder or not (and create folder if necessary)
        test_path = path_utils.join_path(self.file_path, self.name)
        is_folder = path_utils.is_dir(test_path)
        if is_folder:
            self.folder_path = test_path
        else:
            self._create_folder()

    def get_manager(self):
        """
        Returns LibraryManager that should used to create data folder instance
        :return: LibraryManager
        """

        raise NotImplementedError('get_manager not implemented in LibraryDataFolder')

    def get_data_type(self):
        """
        Returns the type of data stored in this data folder
        :return: str
        """

        if self.settings:
            self.settings.reload()
        else:
            self._load_folder()

        return self.settings.get('data_type')

    def set_data_type(self, data_type):
        """
        Set the type of data stored in this data folder
        :param data_type: str
        """

        if not self.settings:
            self._load_folder()

        self.data_type = data_type
        self.settings.set('data_type', str(data_type))

    def get_sub_folder(self, name=None):
        """
        Returns sub folder of this data folder
        :param name: str, name of the sub folder
        :return: str
        """

        if name:
            sub_folder = name
        else:
            if not self.settings:
                self._load_folder()
            sub_folder = self.settings.get('sub_folder')

        if self.folder_path:
            if not path_utils.is_dir(path_utils.join_path(self.folder_path, '.sub/{}'.format(sub_folder))):
                return

        return folder

    def set_sub_folder(self, name):
        """
        Sets the sub folder of this data folder
        :param name: str, name of the sub folder
        """

        if not name:
            return

        if not self.settings:
            self._load_folder()

        self.settings.set('sub_folder', name)
        sub_folder = path_utils.join_path(self.folder_path, '.sub/{}'.format(name))
        folder.create_folder(sub_folder)
        self.settings.set('data_type', str(self.data_type))

    def get_current_sub_folder(self):
        """
        Return current sub folder of data folder
        :return: str
        """

        sub_folder = self.get_sub_folder()
        return sub_folder

    def rename(self, new_name):
        """
        Rename this data folder
        :param new_name: str
        :return: str, new folder name
        """

        base_name = path_utils.get_basename(new_name)
        data_inst = self.get_folder_data_instance()
        data_inst.rename(base_name)
        renamed_folder = folder.rename_folder(self.folder_path, new_name)
        if not renamed_folder:
            return

        self.folder_path = renamed_folder
        self._set_settings_path(renamed_folder)
        self._set_name(base_name)

        return self.folder_path

    def delete(self):
        """
        Removes data folder from disk
        """

        folder_name = path_utils.get_basename(self.folder_path)
        data_directory = path_utils.get_dirname(self.folder_path)

        folder.delete_folder(folder_name, data_directory)

    def get_folder_data_instance(self):
        """
        Returns the data instance for this data
        Depending on the data type this folder contains a differnet object is created
        :return: variant
        """

        if not self.settings:
            self._load_folder()

        if not self.name:
            return

        data_type = self.settings.get('data_type')
        if not data_type:
            data_type = self.data_type

        if data_type is None:
            test_file = os.path.join(self.folder_path, '{}.{}'.format(self.name, scripts.ScriptExtensions.Python))
            if path_utils.is_file(test_file):
                data_type = scripts.ScriptTypes.Python
                self.settings.set('data_type', data_type)
        if not data_type:
            qt.logger.warning(
                'Impossible to instantiate Data Folder because given Data Type: {} is not valid!'.format(data_type))
            return

        data_manager = self.get_manager()
        if not data_manager:
            qt.logger.warning('Impossible to instantiate Data Folder because LibraryManager is not defined!')
            return

        data_inst = data_manager.get_type_instance(data_type)
        if data_inst:
            data_inst.set_directory(self.folder_path)
            data_inst.set_name(self.name)

        return data_inst

    def _load_folder(self):
        """
        Internal function that load settings with the current contents of the data folder
        """

        self._set_default_settings()

    def _set_name(self, name):
        """
        Internal function that stores given name into the data folder settings file
        :param name: str, new name
        """

        if not self.settings:
            self._load_folder()

        self.name = name
        self.settings.set('name', self.name)

    def _set_settings_path(self, folder_path):
        """
        Internal function that stores the given path into the data folder settings file
        :param folder_path: str, folder path
        """

        if not self.settings:
            self._load_folder()

        self.settings.set_directory(folder_path, 'data.json')

    def _set_default_settings(self):
        """
        Internal function that initializes the settings of the data folder
        """

        self.settings = settings.JSONSettings()
        self._set_settings_path(self.folder_path)
        self.settings.set('name', self.name)
        self.data_type = self.settings.get('data_type')

    def _create_folder(self):
        """
        Internal function that creates data folder
        """

        data_path = folder.create_folder(self.name, self.file_path)
        self.folder_path = data_path

        self._set_default_settings()
