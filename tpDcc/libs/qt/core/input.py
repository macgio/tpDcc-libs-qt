#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for input manager
"""

from __future__ import print_function, division, absolute_import

import logging
import traceback

from Qt.QtCore import *
from Qt.QtGui import *

from tpDcc.libs.python import python
if python.is_python2():
    from aenum import Enum
else:
    from enum import Enum

LOGGER = logging.getLogger()


class InputActionType(Enum):
    Mouse = 1
    Keyboard = 2


class InputAction(object):
    def __init__(self, name='defaultName', action_type=InputActionType.Keyboard, group='default',
                 mouse=Qt.NoButton, key=None, modifiers=Qt.NoModifier):
        self._action_type = action_type
        self._name = name
        self._group = group
        self._data = {'mouse': mouse, 'key': key, 'modifiers': modifiers}

    def __str__(self):
        return '{} {} {}'.format(
            QKeySequence(self.get_modifiers()).toString(), self.get_mouse_button().name.encode('utf-8'),
            QKeySequence(self.get_key().toString())
        )

    def __eq__(self, other):
        current_mouse = self._data['mouse']
        current_key = self._data['key']
        current_mods = self._data['modifiers']
        other_mouse = other.get_data()['mouse']
        other_key = other.get_data()['key']
        other_mods = other.get_data()['modifiers']

        return all([current_mouse == other_mouse, current_key == other_key, current_mods == other_mods])

    def __ne__(self, other):
        current_mouse = self._data['mouse']
        current_key = self._data['key']
        current_mods = self._data['modifiers']
        other_mouse = other.get_data()['mouse']
        other_key = other.get_data()['key']
        other_mods = other.get_data()['modifiers']

        return not all([current_mouse == other_mouse, current_key == other_key, current_mods == other_mods])

    @property
    def group(self):
        return self._group

    @property
    def action_type(self):
        return self._action_type

    def get_name(self):
        return self._name

    def get_data(self):
        return self._data

    def get_mouse_button(self):
        return self._data['mouse']

    def set_mouse_button(self, btn):
        assert(isinstance(btn, Qt.MouseButton))
        self._data['mouse'] = btn

    def get_key(self):
        return self._data['key']

    def set_key(self, key):
        assert(isinstance(key, Qt.Key))
        self._data['key'] = key

    def get_modifiers(self):
        return self._data['modifiers']

    def set_modifiers(self, modifiers):
        self._data['modifiers'] = modifiers

    def to_dict(self):
        save_data = dict()
        save_data['name'] = self._name
        save_data['group'] = self._group
        save_data['mouse'] = int(self._data['mouse'])
        save_data['actionType'] = self._action_type.value
        key = self._data['key']
        save_data['key'] = int(key) if key is not None else None
        modifiers_list = self._modifiers_to_list(self._data['modifiers'])
        save_data['modifiers'] = [int(i) for i in modifiers_list]

        return save_data

    def from_dict(self, dict_data):
        try:
            self._name = dict_data['name']
            self._group = dict_data['group']
            self._data['mouse'] = Qt.MouseButton(dict_data['mouse'])
            key_index = dict_data['key']
            self._data['key'] = Qt.Key(key_index) if isinstance(key_index, int) else None
            self._data['modifiers'] = self._list_of_modifiers_to_enum(
                [Qt.KeyboardModifier(i) for i in dict_data['modifiers']])
            self._action_type = InputActionType(dict_data['actionType'])
            return self
        except Exception as exc:
            LOGGER.error(
                'Impossible to load Input Action from given dictionary: {} | {}'.format(
                    exc, traceback.format_exc()))
            return None

    def _modifiers_to_list(self, mods):
        result = list()

        if mods & Qt.ShiftModifier:
            result.append(Qt.ShiftModifier)
        if mods & Qt.ControlModifier:
            result.append(Qt.ControlModifier)
        if mods & Qt.AltModifier:
            result.append(Qt.AltModifier)
        if mods & Qt.MetaModifier:
            result.append(Qt.MetaModifier)
        if mods & Qt.KeypadModifier:
            result.append(Qt.KeypadModifier)
        if mods & Qt.GroupSwitchModifier:
            result.append(Qt.GroupSwitchModifier)

        return result

    def _list_of_modifiers_to_enum(self, modifiers_list):
        result = Qt.NoModifier
        for mod in modifiers_list:
            result = result | mod

        return result
