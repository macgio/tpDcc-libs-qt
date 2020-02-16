#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for settings manager
"""

from __future__ import print_function, division, absolute_import

from collections import OrderedDict

import os
import shutil
import logging

from pathlib2 import Path

LOGGER = logging.getLogger()


class SettingsManager(object):

    EXTENSION = 'json'

    def __init__(self):
        self._roots = OrderedDict()

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def root(self, name):
        """
        Returns root with given name if exists. Otherwise exception is raised
        :param name: str
        :return: str
        """

        if name not in self._roots:
            raise RootDoesnExistsException('Root with name: "{}" does not exist!'.format(name))

        return self._resolve_root(self._roots[name])

    def root_name_from_path(self, path):
        """
        Returns root settings name from given path
        :param path: str
        :return: str or None
        """

        for name, root in self._roots.items():
            if str(root).startswith(str(path)):
                return name

        return None

    def add_root(self, full_path, name):
        """
        Adds a new root settinsg path to the settings manager
        :param full_path: str
        :param name: str
        """

        if name in self._roots:
            raise RootAlreadyExistsException('Root already exists: "{}"'.format(name))

        self._roots[str(name)] = Path(full_path)

    def delete_root(self, root):
        """
        Removes settings root folder location and all files
        :param root: str
        :return: bool
        """

        root_path = str(self.root(root))
        try:
            shutil.rmtree(root_path)
        except OSError as exc:
            LOGGER.error('Failed to remove the settings root: "{}" | {}'.format(root_path, exc))
            return False

        return True

    # ============================================================================================================
    # INTERNAL
    # ============================================================================================================

    def _resolve_root(self, root):
        """
        Internal function that resolves final path of the given settings root path
        :param root: str
        :return: str
        """

        return Path(os.path.expandvars(os.path.expanduser(str(root)))).resolve()


class RootAlreadyExistsException(Exception):
    pass


class RootDoesnExistsException(Exception):
    pass


class InvalidSettingsPath(Exception):
    pass


class InvalidRootError(Exception):
    pass