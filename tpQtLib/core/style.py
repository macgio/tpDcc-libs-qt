#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains style implementation
"""

from __future__ import print_function, division, absolute_import

import os
import re


class StyleSheet(object):

    @classmethod
    def from_path(cls, path, **kwargs):
        """
        Returns stylesheet from given path
        :param path: str
        :param kwargs: dict
        :return: StyleSheet
        """

        stylesheet = cls()
        data = stylesheet.read(path)
        data = StyleSheet.format(data, **kwargs)
        stylesheet.set_data(data)

        return stylesheet

    @classmethod
    def from_text(cls, text, options=None):
        """
        Returns stylesheet from given text and options
        :param text: str
        :param options: dict
        :return: StyleSheet
        """

        stylesheet = cls()
        data = stylesheet.format(text, options=options)
        stylesheet.set_data(data)

        return stylesheet

    @staticmethod
    def read(path):
        """
        Reads style data from given path
        :param path: str
        :return: str
        """

        data = ''
        if os.path.isfile(path):
            with open(path, 'r') as f:
                data = f.read()

        return data

    @staticmethod
    def format(data=None, options=None, dpi=1):
        """
        Returns style with proper format
        :param data: str
        :param options: dict
        :param dpi: float
        :return: str
        """

        if options:
            keys = options.keys()
            keys.sort(key=len, reverse=True)
            for key in keys:
                data = data.replace(key, options[key])

        re_dpi = re.compile('[0-9]+[*]DPI')
        new_data = list()

        for line in data.split('\n'):
            dpi_ = re_dpi.search(line)
            if dpi_:
                new = dpi_.group().replace('DPI', str(dpi))
                val = int(eval(new))
                line = line.replace(dpi_.group(), str(val))
            new_data.append(line)

        data = '\n'.join(new_data)

        return data

    def __init__(self):
        super(StyleSheet, self).__init__()

        self._data = ''

    def data(self):
        """
        Returns style data
        :return: str
        """

        return self._data

    def set_data(self, data):
        """
        Sets style data
        :param data: str
        """

        self._data = data

