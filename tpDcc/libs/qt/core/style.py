#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains style implementation
"""

from __future__ import print_function, division, absolute_import

import os
import re

import tpDcc
from tpDcc.libs.python import color, python
from tpDcc.libs.qt.core import qtutils


class StyleSheet(object):

    EXTENSION = 'css'

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
    def format(data=None, options=None, dpi=1, **kwargs):
        """
        Returns style with proper format
        :param data: str
        :param options: dict
        :param dpi: float
        :return: str
        """

        if options:
            keys = options.keys()
            if python.is_python2():
                keys.sort(key=len, reverse=True)
            else:
                keys = sorted(keys, key=len, reverse=True)
            for key in keys:
                key_value = options[key]
                str_key_value = str(key_value)
                option_value = str(key_value)
                if str_key_value.startswith('@^'):
                    option_value = str(qtutils.dpi_scale(int(str_key_value[2:])))
                elif str_key_value.startswith('^'):
                    option_value = str(qtutils.dpi_scale(int(str_key_value[1:])))
                elif 'icon' in key:
                    theme_name = kwargs.get('theme_name', 'default') or 'default'
                    resource_path = tpDcc.ResourcesMgr().get('icons', theme_name, str(key_value))
                    if resource_path and os.path.isfile(resource_path):
                        option_value = resource_path
                elif color.string_is_hex(str_key_value):
                    try:
                        color_list = color.hex_to_rgba(str_key_value)
                        option_value = 'rgba({}, {}, {}, {})'.format(
                            color_list[0], color_list[1], color_list[2], color_list[3])
                    except ValueError:
                        # This exception will be raised if we try to convert an attribute that is not a color.
                        option_value = key_value

                data = data.replace('@{}'.format(key), option_value)

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
