#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains factory class to create options
"""

from __future__ import print_function, division, absolute_import

from tpDcc.libs.python import decorators, python
from tpDcc.libs.qt.widgets.options import title, bool, float, integer, list, dictionary, text, directory, file, color
from tpDcc.libs.qt.widgets.options import vector3, combo, script


class OptionsFactory(object):
    def __init__(self):
        super(OptionsFactory, self).__init__()

    def add_option(self, option_type, name=None, value=None, parent=None, main_widget=None, option_object=None):
        new_option = None
        if option_type == 'title':
            new_option = self._add_title(name=name, parent=parent, main_widget=main_widget)
        elif option_type == 'boolean':
            new_option = self._add_boolean(name=name, parent=parent, value=value, main_widget=main_widget)
        elif option_type == 'float':
            new_option = self._add_float(name=name, parent=parent, value=value, main_widget=main_widget)
        elif option_type == 'integer':
            new_option = self._add_integer(name=name, parent=parent, value=value, main_widget=main_widget)
        elif option_type == 'list':
            new_option = self._add_list(name=name, parent=parent, value=value, main_widget=main_widget)
        elif option_type == 'dictionary':
            new_option = self._add_dictionary(name=name, parent=parent, value=value, main_widget=main_widget)
        elif option_type in ['string', 'text']:
            new_option = self._add_string(name=name, parent=parent, value=value, main_widget=main_widget)
        elif option_type == 'directory':
            new_option = self._add_directory(name=name, parent=parent, value=value, main_widget=main_widget)
        elif option_type == 'file':
            new_option = self._add_file(name=name, parent=parent, value=value, main_widget=main_widget)
        elif option_type == 'nonedittext':
            new_option = self._add_non_editable_text(name=name, parent=parent, value=value, main_widget=main_widget)
        elif option_type == 'color':
            new_option = self._add_color(name=name, parent=parent, value=value, main_widget=main_widget)
        elif option_type == 'vector3f':
            new_option = self._add_vector3_float(name=name, parent=parent, value=value, main_widget=main_widget)
        elif option_type == 'combo':
            new_option = self._add_combo(name=name, parent=parent, value=value, main_widget=main_widget)
        elif option_type == 'script':
            new_option = self._add_script(
                name=name, parent=parent, value=value, main_widget=main_widget, option_object=option_object)

        return new_option

    def _add_title(self, name='title', parent=None, main_widget=None):
        """
        Adds new title property to the group box
        :param name: str
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'title'

        return title.TitleOption(name=name, parent=parent, main_widget=main_widget)

    def _add_boolean(self, name='boolean', value=None, parent=None, main_widget=None):
        """
        Adds new boolean property to the group box
        :param name: str
        :param value: bool, default value of the property
        :param parent: Option
        """

        if type(name) == bool:
            name = 'boolean'

        value = value if value is not None else False

        bool_option = bool.BooleanOption(name=name, parent=parent, main_widget=main_widget)
        bool_option.set_value(value)

        return bool_option

    def _add_float(self, name='float', value=None, parent=None, main_widget=None):
        """
        Adds new float property to the group box
        :param name: str
        :param value: float, default value of the property
        :param parent: Option
        """

        if type(name) == bool:
            name = 'float'

        value = value if value is not None else 0.0

        float_option = float.FloatOption(name=name, parent=parent, main_widget=main_widget)
        float_option.set_value(value)

        return float_option

    def _add_integer(self, name='integer', value=None, parent=None, main_widget=None):
        """
        Adds new integer property to the group box
        :param name: str
        :param value: int, default value of the property
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'integer'

        value = value if value is not None else 0.0

        int_option = integer.IntegerOption(name=name, parent=parent, main_widget=main_widget)
        int_option.set_value(value)

        return int_option

    def _add_list(self, name='list', value=None, parent=None, main_widget=None):
        """
        Adds new list property to the group box
        :param name: str
        :param value: list(dict, list)
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'list'

        if value is None:
            value = []
        else:
            value = python.force_list(value)

        list_option = list.ListOption(name=name, parent=parent, main_widget=main_widget)
        list_option.set_value(value)

        return list_option

    def _add_dictionary(self, name='dictionary', value=None, parent=None, main_widget=None):
        """
        Adds new dictionary property to the group box
        :param name: str
        :param value: list(dict, list)
        :param parent: QWidget
        """

        if value is None:
            value = [{}, []]

        if type(name) == bool:
            name = 'dictionary'

        if type(value) == type(dictionary):
            keys = dictionary.keys()
            if keys:
                keys.sort()
            value = [dictionary, keys]

        dict_option = dictionary.DictOption(name=name, parent=parent, main_widget=main_widget)
        dict_option.set_value(value)

        return dict_option

    def _add_string(self, name='string', value=None, parent=None, main_widget=None):
        """
        Adds new string property to the group box
        :param name: str
        :param value: str, default value of the property
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'string'

        value = value if value is not None else ''

        string_option = text.TextOption(name=name, parent=parent, main_widget=main_widget)
        string_option.set_value(value)

        return string_option

    def _add_directory(self, name='directory', value=None, parent=None, main_widget=None):
        """
        Adds new directory property to the group box
        :param name: str
        :param value: str, default value of the property
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'directory'

        value = value if value is not None else ''

        directory_option = directory.DirectoryOption(name=name, parent=parent, main_widget=main_widget)
        directory_option.set_value(value)

        return directory_option

    def _add_file(self, name='file', value=None, parent=None, main_widget=None):
        """
        Adds new file property to the group box
        :param name: str
        :param value: str, default value of the property
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'file'

        value = value if value is not None else ''

        file_option = file.FileOption(name=name, parent=parent, main_widget=main_widget)
        file_option.set_value(value)

        return file_option

    def _add_non_editable_text(self, name='string', value=None, parent=None, main_widget=None):
        """
        Adds new non editable string property to the group box
        :param name: str
        :param value: str, default value of the property
        :param parent: QWidget
        """

        value = value if value is not None else ''

        string_option = text.NonEditTextOption(name=name, parent=parent, main_widget=main_widget)
        string_option.set_value(value)

        return string_option

    def _add_color(self, name='color', value=None, parent=None, main_widget=None):
        """
        Adds new color property to the group box
        :param name: str
        :param value: list
        :param parent: QWidget
        """

        value = value if value is not None else [1.0, 1.0, 1.0, 1.0]

        color_option = color.ColorOption(name=name, parent=parent, main_widget=main_widget)
        color_option.set_value(value)

        return color_option

    def _add_vector3_float(self, name='vector3f', value=None, parent=None, main_widget=None):
        """
        Adds new vector3 property to the group box
        :param name: str
        :param value: list
        :param parent: QWidget
        """

        value = value if value is not None else [0.0, 0.0, 0.0]

        vector_option = vector3.Vector3FloatOption(name=name, parent=parent, main_widget=main_widget)
        vector_option.set_value(value)

        return vector_option

    def _add_combo(self, name='combo', value=None, parent=None, main_widget=None):
        """
        Adds new color property to the group box
        :param name: str
        :param value: list
        :param parent: QWidget
        """

        if value is None:
            value = [[], []]

        if not isinstance(value[0], list):
            value = [value, []]

        combo_option = combo.ComboOption(name=name, parent=parent, main_widget=main_widget)
        combo_option.set_value(value)

        return combo_option

    def _add_script(self, option_object, name='script', value=None, parent=None, main_widget=None):
        """
        Adds new script property to the group box
        :param name: str
        :param value: bool, default value of the property
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'script'

        value = value if value is not None else ''

        script_option = script.ScriptOption(name=name, parent=parent, main_widget=main_widget)
        script_option.set_option_object(option_object)
        script_option.set_value(value)

        return script_option


@decorators.Singleton
class OptionsFactorySingleton(OptionsFactory, object):
    def __init__(self):
        OptionsFactory.__init__(self)
