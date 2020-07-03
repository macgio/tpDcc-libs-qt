#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains core classes for option lists
"""

from __future__ import print_function, division, absolute_import

import string
import traceback
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc as tp
from tpDcc.libs import qt
from tpDcc.libs.python import python, name as name_utils
from tpDcc.libs.qt.core import qtutils
from tpDcc.libs.qt.widgets import layouts


class OptionList(QGroupBox, object):
    editModeChanged = Signal(bool)
    valueChanged = Signal()

    def __init__(self, parent=None, option_object=None):
        super(OptionList, self).__init__(parent)
        self._option_object = option_object
        self._parent = parent

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_item_menu)
        self._context_menu = None
        self._create_context_menu()

        self._has_first_group = False
        self._disable_auto_expand = False
        self._supress_update = False
        self._central_list = self
        self._itemClass = OptionListGroup
        self._auto_rename = False

        self.setup_ui()

    def mousePressEvent(self, event):
        """
        Overrides base QGroupBox mousePressEvent function
        :param event: QMouseEvent
        """

        widget_at_mouse = qtutils.get_widget_at_mouse()
        if widget_at_mouse == self:
            self.clear_selection()
        super(OptionList, self).mousePressEvent(event)

    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)
        self.setLayout(self.main_layout)

        self.child_layout = QVBoxLayout()
        self.child_layout.setContentsMargins(5, 5, 5, 5)
        self.child_layout.setSpacing(5)
        self.child_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addLayout(self.child_layout)
        self.main_layout.addSpacing(30)

    def get_option_object(self):
        """
        Returns the option object linked to this widget
        :return: object
        """

        return self._option_object

    def set_option_object(self, option_object):
        """
        Sets option object linked to this widget
        :param option_object: object
        """

        self._option_object = option_object

    def update_options(self):
        """
        Updates current widget options
        """

        if not self._option_object:
            qt.logger.warning('Impossible to update options because option object is not defined!')
            return

        options = self._option_object.get_options()

        self._load_widgets(options)

    def get_parent(self):
        """
        Returns parent Option
        """

        parent = self.parent()
        grand_parent = parent.parent()
        if hasattr(grand_parent, 'group'):
            parent = grand_parent
        if not hasattr(parent, 'child_layout'):
            return

        if parent.__class__ == OptionList:
            return parent

        return parent

    def add_group(self, name='group', value=True, parent=None):
        """
        Adds new group property to the group box
        :param name: str
        :param value: bool, default value
        :param parent: Option
        """

        if type(name) == bool:
            name = 'group'

        name = self._get_unique_name(name, parent)
        option_object = self.get_option_object()
        group = OptionListGroup(name=name, option_object=option_object, parent=self._parent)
        group.set_expanded(value)
        if self.__class__ == OptionListGroup or parent.__class__ == OptionListGroup:
            if tp.is_maya():
                group.group.set_inset_dark()
        self._handle_parenting(group, parent)
        self._write_options(clear=False)
        self._has_first_group = True

        return group

    def add_custom(self, option_type, name, value=None, parent=None, **kwargs):
        """
        Function that is called when a custom widget is added (is not a default one)
        :param option_type: str
        :param name: str
        :param value:
        :param parent:
        """

        pass

    def add_title(self, name='title', parent=None):
        """
        Adds new title property to the group box
        :param name: str
        :param parent: QWidget
        :param write_options: bool
        """

        if type(name) == bool:
            name = 'title'

        name = self._get_unique_name(name, parent)
        title = TitleOption(name=name, parent=parent, main_widget=self._parent)
        self._handle_parenting(title, parent)
        self._write_options(clear=False)

    def add_boolean(self, name='boolean', value=False, parent=None):
        """
        Adds new boolean property to the group box
        :param name: str
        :param value: bool, default value of the property
        :param parent: Option
        :param write_options: bool
        """

        if type(name) == bool:
            name = 'boolean'

        name = self._get_unique_name(name, parent)
        bool_option = BooleanOption(name=name, parent=parent, main_widget=self._parent)
        bool_option.set_value(value)
        self._handle_parenting(bool_option, parent)
        self._write_options(clear=False)

    def add_float(self, name='float', value=0.0, parent=None):
        """
        Adds new float property to the group box
        :param name: str
        :param value: float, default value of the property
        :param parent: Option
        """

        if type(name) == bool:
            name = 'float'

        name = self._get_unique_name(name, parent)
        float_option = FloatOption(name=name, parent=parent, main_widget=self._parent)
        float_option.set_value(value)
        self._handle_parenting(float_option, parent)
        self._write_options(clear=False)

    def add_integer(self, name='integer', value=0.0, parent=None):
        """
        Adds new integer property to the group box
        :param name: str
        :param value: int, default value of the property
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'integer'

        name = self._get_unique_name(name, parent)
        int_option = IntegerOption(name=name, parent=parent, main_widget=self._parent)
        int_option.set_value(value)
        self._handle_parenting(int_option, parent)
        self._write_options(clear=False)

    def add_list(self, name='list', value=None, parent=None):
        """
        Adds new list property to the group box
        :param name: str
        :param value: list(dict, list)
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'list'

        value = python.force_list(value)

        name = self._get_unique_name(name, parent)
        list_option = ListOption(name=name, parent=parent, main_widget=self._parent)
        list_option.set_value(value)
        self._handle_parenting(list_option, parent)
        self._write_options(False)

    def add_dictionary(self, name='dictionary', value=[{}, []], parent=None):
        """
        Adds new dictionary property to the group box
        :param name: str
        :param value: list(dict, list)
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'dictionary'

        if type(value) == type(dict):
            keys = dict.keys()
            if keys:
                keys.sort()
            value = [dict, keys]

        name = self._get_unique_name(name, parent)
        dict_option = DictOption(name=name, parent=parent, main_widget=self._parent)
        dict_option.set_value(value)
        self._handle_parenting(dict_option, parent)
        self._write_options(False)

    def add_string(self, name='string', value='', parent=None):
        """
        Adds new string property to the group box
        :param name: str
        :param value: str, default value of the property
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'string'

        name = self._get_unique_name(name, parent)
        string_option = TextOption(name=name, parent=parent, main_widget=self._parent)
        string_option.set_value(value)
        self._handle_parenting(string_option, parent)
        self._write_options(clear=False)

    def add_directory(self, name='directory', value='', parent=None):
        """
        Adds new directory property to the group box
        :param name: str
        :param value: str, default value of the property
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'directory'

        name = self._get_unique_name(name, parent)
        directory_option = DirectoryOption(name=name, parent=parent, main_widget=self._parent)
        directory_option.set_value(value)
        self._handle_parenting(directory_option, parent)
        self._write_options(clear=False)

    def add_file(self, name='file', value='', parent=None):
        """
        Adds new file property to the group box
        :param name: str
        :param value: str, default value of the property
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'file'

        name = self._get_unique_name(name, parent)
        file_option = FileOption(name=name, parent=parent, main_widget=self._parent)
        file_option.set_value(value)
        self._handle_parenting(file_option, parent)
        self._write_options(clear=False)

    def add_non_editable_text(self, name='string', value='', parent=None):
        """
        Adds new non editable string property to the group box
        :param name: str
        :param value: str, default value of the property
        :param parent: QWidget
        """

        name = self._get_unique_name(name, parent)
        string_option = NonEditTextOption(name=name, parent=parent, main_widget=self._parent)
        string_option.set_value(value)
        self._handle_parenting(string_option, parent)
        self._write_options(clear=False)

    def add_color(self, name='color', value=None, parent=None):
        """
        Adds new color property to the group box
        :param name: str
        :param value: list
        :param parent: QWidget
        """

        if value is None:
            value = [1.0, 1.0, 1.0, 1.0]

        name = self._get_unique_name(name, parent)
        color_option = ColorOption(name=name, parent=parent, main_widget=self._parent)
        color_option.set_value(value)
        self._handle_parenting(color_option, parent)
        self._write_options(clear=False)

    def add_vector3_float(self, name='vector3f', value=None, parent=None):
        """
        Adds new vector3 property to the group box
        :param name: str
        :param value: list
        :param parent: QWidget
        """

        if value is None:
            value = [0.0, 0.0, 0.0]

        name = self._get_unique_name(name, parent)
        color_option = Vector3FloatOption(name=name, parent=parent, main_widget=self._parent)
        color_option.set_value(value)
        self._handle_parenting(color_option, parent)
        self._write_options(clear=False)

    def add_combo(self, name='combo', value=None, parent=None):
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

        name = self._get_unique_name(name, parent)
        combo_option = ComboOption(name=name, parent=parent, main_widget=self._parent)
        combo_option.set_value(value)
        self._handle_parenting(combo_option, parent)
        self._write_options(clear=False)

    def add_script(self, name='script', value='', parent=None):
        """
        Adds new script property to the group box
        :param name: str
        :param value: bool, default value of the property
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'script'

        name = self._get_unique_name(name, parent)
        button = ScriptOption(name=name, parent=parent, main_widget=self._parent)
        button.set_option_object(self._option_object)
        button.set_value(value)
        self._handle_parenting(button, parent)
        self._write_options(False)

    def update_current_widget(self, widget=None):
        """
        Function that updates given widget status
        :param widget: QWidget
        """

        if self._parent.is_edit_mode() is False:
            return

        if widget:
            if self.is_selected(widget):
                self.deselect_widget(widget)
                return
            else:
                self.select_widget(widget)
                return

    def is_selected(self, widget):
        """
        Returns whether property widget is selected or not
        :param widget: QWidget
        :return: bool
        """

        if widget in self._parent._current_widgets:
            return True

        return False

    def select_widget(self, widget):
        """
        Selects given Option widget
        :param widget: Option
        """

        if hasattr(widget, 'child_layout'):
            self._deselect_children(widget)

        parent = widget.get_parent()
        if not parent:
            parent = widget.parent()

        out_of_scope = None
        if parent:
            out_of_scope = self.sort_widgets(self._parent._current_widgets, parent, return_out_of_scope=True)
        if out_of_scope:
            for sub_widget in out_of_scope:
                self.deselect_widget(sub_widget)

        self._parent._current_widgets.append(widget)
        self._fill_background(widget)

    def deselect_widget(self, widget):
        """
        Deselects given Option widget
        :param widget: Option
        """

        if not self.is_selected(widget):
            return

        widget_index = self._parent._current_widgets.index(widget)
        self._parent._current_widgets.pop(widget_index)
        self._unfill_background(widget)

    def clear_selection(self):
        """
        Clear current selected Option widgets
        """

        for widget in self._parent._current_widgets:
            self._unfill_background(widget)

        self._parent._current_widgets = list()

    def sort_widgets(self, widgets, parent, return_out_of_scope=False):
        """
        Sort current Option widgets
        :param widgets: list(Option)
        :param parent: Options
        :param return_out_of_scope: bool
        :return: list(Option)
        """

        if not hasattr(parent, 'child_layout'):
            return

        item_count = parent.child_layout.count()
        found = list()

        for i in range(item_count):
            item = parent.child_layout.itemAt(i)
            if item:
                widget = item.widget()
                for sub_widget in widgets:
                    if sub_widget == widget:
                        found.append(widget)

        if return_out_of_scope:
            other_found = list()
            for sub_widget in widgets:
                if sub_widget not in found:
                    other_found.append(sub_widget)

            found = other_found

        return found

    def clear_widgets(self):
        """
        Removes all widgets from current group
        """

        self._has_first_group = False
        item_count = self.child_layout.count()
        for i in range(item_count, -1, -1):
            item = self.child_layout.itemAt(i)
            if item:
                widget = item.widget()
                self.child_layout.removeWidget(widget)
                widget.deleteLater()

        self._parent._current_widgets = list()

    def set_edit(self, flag):
        """
        Set the edit mode of the group
        :param flag: bool
        """

        self.editModeChanged.emit(flag)

    def _create_context_menu(self):
        from tpDcc.libs.qt.widgets.options import factory

        self._context_menu = QMenu()
        self._context_menu.setTearOffEnabled(True)

        plus_icon = tp.ResourcesMgr().icon('plus')
        string_icon = tp.ResourcesMgr().icon('rename')
        directory_icon = tp.ResourcesMgr().icon('folder')
        file_icon = tp.ResourcesMgr().icon('file')
        integer_icon = tp.ResourcesMgr().icon('number_1')
        float_icon = tp.ResourcesMgr().icon('float_1')
        bool_icon = tp.ResourcesMgr().icon('true_false')
        dict_icon = tp.ResourcesMgr().icon('dictionary')
        list_icon = tp.ResourcesMgr().icon('list')
        group_icon = tp.ResourcesMgr().icon('group_objects')
        script_icon = tp.ResourcesMgr().icon('source_code')
        title_icon = tp.ResourcesMgr().icon('label')
        color_icon = tp.ResourcesMgr().icon('palette')
        clear_icon = tp.ResourcesMgr().icon('clean')
        copy_icon = tp.ResourcesMgr().icon('copy')
        paste_icon = tp.ResourcesMgr().icon('paste')

        create_menu = self._context_menu.addMenu(plus_icon, 'Add Options')
        add_string_action = QAction(string_icon, 'Add String', create_menu)
        create_menu.addAction(add_string_action)
        add_directory_action = QAction(directory_icon, 'Add Directory', create_menu)
        create_menu.addAction(add_directory_action)
        add_file_action = QAction(file_icon, 'Add File', create_menu)
        create_menu.addAction(add_file_action)
        add_integer_action = QAction(integer_icon, 'Add Integer', create_menu)
        create_menu.addAction(add_integer_action)
        add_float_action = QAction(float_icon, 'Add Float', create_menu)
        create_menu.addAction(add_float_action)
        add_bool_action = QAction(bool_icon, 'Add Bool', create_menu)
        create_menu.addAction(add_bool_action)
        add_list_action = QAction(list_icon, 'Add List', create_menu)
        create_menu.addAction(add_list_action)
        add_dict_action = QAction(dict_icon, 'Add Dictionary', create_menu)
        create_menu.addAction(add_dict_action)
        add_group_action = QAction(group_icon, 'Add Group', create_menu)
        create_menu.addAction(add_group_action)
        add_script_action = QAction(script_icon, 'Add Script', create_menu)
        create_menu.addAction(add_script_action)
        add_title_action = QAction(title_icon, 'Add Title', create_menu)
        create_menu.addAction(add_title_action)
        add_color_action = QAction(color_icon, 'Add Color', create_menu)
        create_menu.addAction(add_color_action)
        add_vector3f_action = QAction(color_icon, 'Add Vector 3 float', create_menu)
        create_menu.addAction(add_vector3f_action)
        self._context_menu.addSeparator()
        self.copy_action = QAction(copy_icon, 'Copy', self._context_menu)
        self._context_menu.addAction(self.copy_action)
        self.copy_action.setVisible(False)
        self.paste_action = QAction(paste_icon, 'Paste', self._context_menu)
        self._context_menu.addAction(self.paste_action)
        self.paste_action.setVisible(False)
        self._context_menu.addSeparator()
        clear_action = QAction(clear_icon, 'Clear', self._context_menu)
        self._context_menu.addAction(clear_action)

        factory_inst = factory.OptionsFactorySingleton()

        add_string_action.triggered.connect(partial(factory_inst.add_option, 'string'))
        add_directory_action.triggered.connect(partial(factory_inst.add_option, 'directory'))
        add_file_action.triggered.connect(partial(factory_inst.add_option, 'file'))
        add_integer_action.triggered.connect(partial(factory_inst.add_option, 'integer'))
        add_float_action.triggered.connect(partial(factory_inst.add_option, 'float'))
        add_bool_action.triggered.connect(partial(factory_inst.add_option, 'bool'))
        add_list_action.triggered.connect(partial(factory_inst.add_option, 'list'))
        add_dict_action.triggered.connect(partial(factory_inst.add_option, 'dict'))
        add_group_action.triggered.connect(partial(factory_inst.add_option, 'group'))
        add_title_action.triggered.connect(partial(factory_inst.add_option, 'title'))
        add_color_action.triggered.connect(partial(factory_inst.add_option, 'color'))
        add_vector3f_action.triggered.connect(partial(factory_inst.add_option, 'vector3f'))
        add_script_action.triggered.connect(partial(factory_inst.add_option, 'script'))
        clear_action.triggered.connect(_clear_action)

        return create_menu

    def _get_widget_names(self, parent=None):
        """
        Internal function that returns current stored widget names
        :param parent: Option
        :return: list(str)
        """

        if parent:
            scope = parent
        else:
            scope = self

        item_count = scope.child_layout.count()
        found = list()
        for i in range(item_count):
            item = scope.child_layout.itemAt(i)
            widget = item.widget()
            label = widget.get_name()
            found.append(label)

        return found

    def _get_unique_name(self, name, parent):
        """
        Internal function that returns unique name for the new group
        :param name: str
        :param parent: QWidget
        :return: str
        """

        found = self._get_widget_names(parent)
        while name in found:
            name = name_utils.increment_last_number(name)

        return name

    def _handle_parenting(self, widget, parent):
        """
        Internal function that handles parenting of given widget and its parent
        :param widget: Options
        :param parent: Options
        """

        widget.widgetClicked.connect(self.update_current_widget)
        # widget.editModeChanged.connect(self._on_activate_edit_mode)

        if parent:
            parent.child_layout.addWidget(widget)
            if hasattr(widget, 'updateValues'):
                widget.updateValues.connect(parent._write_options)
        else:
            self.child_layout.addWidget(widget)
            if hasattr(widget, 'updateValues'):
                widget.updateValues.connect(self._write_options)

        if self._auto_rename:
            widget.rename()

    def _get_path(self, widget):
        """
        Internal function that return option path of given option
        :param widget: Options
        :return: str
        """

        parent = widget.get_parent()
        path = ''
        parents = list()
        if parent:
            sub_parent = parent
            while sub_parent:
                if issubclass(sub_parent.__class__, OptionList) and not sub_parent.__class__ == OptionListGroup:
                    break
                name = sub_parent.get_name()
                parents.append(name)
                sub_parent = sub_parent.get_parent()

        parents.reverse()

        for sub_parent in parents:
            path += '{}.'.format(sub_parent)

        if hasattr(widget, 'child_layout'):
            path = path + widget.get_name() + '.'
        else:
            path = path + widget.get_name()

        return path

    def _load_widgets(self, options):
        """
        Internal function that loads widget with given options
        :param options: dict
        """

        self.clear_widgets()
        if not options:
            return

        # self.setHidden(True)
        # self.setUpdatesEnabled(False)
        self._supress_update = True
        self._disable_auto_expand = True
        self._auto_rename = False

        try:
            for option in options:
                option_type = None
                if type(option[1]) == list:
                    if option[0] == 'list':
                        value = option[1]
                        option_type = 'list'
                    else:
                        value = option[1][0]
                        option_type = option[1][1]
                else:
                    value = option[1]

                split_name = option[0].split('.')
                if split_name[-1] == '':
                    search_group = string.join(split_name[:-2], '.')
                    name = split_name[-2]
                else:
                    search_group = string.join(split_name[:-1], '.')
                    name = split_name[-1]

                widget = self._find_group_widget(search_group)
                if not widget:
                    widget = self

                is_group = False
                if split_name[-1] == '':
                    is_group = True
                    parent_name = string.join(split_name[:-1], '.')
                    group = self._find_group_widget(parent_name)
                    if not group:
                        self.add_group(name, value, widget)

                if len(split_name) > 1 and split_name[-1] != '':
                    search_group = string.join(split_name[:-2], '.')
                    after_search_group = string.join(split_name[:-1], '.')
                    group_name = split_name[-2]
                    group_widget = self._find_group_widget(search_group)
                    widget = self._find_group_widget(after_search_group)
                    if not widget:
                        self.add_group(group_name, value, group_widget)
                        widget = self._find_group_widget(after_search_group)

                if not option_type and not is_group:
                    if type(value) == unicode or type(value) == str:
                        self.add_string(name, value, widget)
                    elif type(value) == float:
                        self.add_float(name, value, widget)
                    elif type(option[1]) == int:
                        self.add_integer(name, value, widget)
                    elif type(option[1]) == bool:
                        self.add_boolean(name, value, widget)
                    elif type(option[1]) == dict:
                        self.add_dictionary(name, [value, []], widget)
                    elif type(option[1]) == list:
                        self.add_list(name, value, widget)
                    elif option[1] is None:
                        self.add_title(name, widget)
                    else:
                        self.add_custom(name, value, widget)
                else:
                    if option_type == 'script':
                        self.add_script(name, value, widget)
                    elif option_type == 'list':
                        self.add_list(name, value, widget)
                    elif option_type == 'dictionary':
                        self.add_dictionary(name, value, widget)
                    elif option_type == 'nonedittext':
                        self.add_non_editable_text(name, value, widget)
                    elif option_type == 'directory':
                        self.add_directory(name, value, widget)
                    elif option_type == 'file':
                        self.add_file(name, value, widget)
                    elif option_type == 'color':
                        self.add_color(name, value, widget)
                    elif option_type == 'vector3f':
                        self.add_vector3_float(name, value, widget)
                    elif option_type == 'combo':
                        self.add_combo(name, value, widget)
                    else:
                        self.add_custom(option_type, name, value, widget)
        except Exception:
            qt.logger.error(traceback.format_exc())
        finally:
            self._disable_auto_expand = False
            # self.setVisible(True)
            # self.setUpdatesEnabled(True)
            self._supress_update = False
            self._auto_rename = True

    def _find_list(self, widget):
        if widget.__class__ == OptionList:
            return widget

        parent = widget.get_parent()
        if not parent:
            return

        while parent.__class__ != OptionList:
            parent = parent.get_parent()

        return parent

    def _find_group_widget(self, name):
        """
        Internal function that returns OptionList with given name (if exists)
        :param name: str, name of the group to find
        :return: variant, OptionList or None
        """

        split_name = name.split('.')
        sub_widget = None
        for name in split_name:
            if not sub_widget:
                sub_widget = self
            found = False
            item_count = sub_widget.child_layout.count()
            for i in range(item_count):
                item = sub_widget.child_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    label = widget.get_name()
                    if label == name:
                        sub_widget = widget
                        found = True
                        break
                else:
                    break
            if not found:
                return

        return sub_widget

    def _deselect_children(self, widget):
        """
        Internal function that deselects all the children widgets of the given Option
        :param widget: Option
        """

        children = widget.get_children()
        for child in children:
            self.deselect_widget(child)

    def _clear_action(self):
        """
        Internal function that clears all widgets
        """

        if self.__class__ == OptionList:
            name = 'the list?'
        else:
            name = 'group: {}?'.format(self.get_name())

        item_count = self.child_layout.count()
        if item_count <= 0:
            qt.logger.debug('No widgets to clear ...')
            return

        permission = qtutils.get_permission('Clear all the widgets in {}'.format(name), parent=self)
        if permission:
            self.clear_widgets()
            self._write_options(clear=True)

    def _write_options(self, clear=True):
        """
        Internal function that writes current options into disk
        :param clear: bool
        """

        if not self._option_object:
            qt.logger.warning('Impossible to write options because option object is not defined!')
            return

        if self._supress_update:
            return

        if clear:
            self._write_all()
        else:
            item_count = self.child_layout.count()
            for i in range(0, item_count):
                item = self.child_layout.itemAt(i)
                widget = item.widget()
                widget_type = widget.get_option_type()
                name = self._get_path(widget)
                value = widget.get_value()

                self._option_object.add_option(name, value, None, widget_type)

        self.valueChanged.emit()

    def _write_widget_options(self, widget):
        if not widget:
            return

        if not self._option_object:
            qt.logger.warning('Impossible to write options because option object is not defined!')
            return

        item_count = widget.child_layout.count()
        for i in range(item_count):
            item = widget.child_layout.itemAt(i)
            if item:
                sub_widget = item.widget()
                sub_widget_type = sub_widget.get_option_type()
                name = self._get_path(sub_widget)
                value = sub_widget.get_value()

                self._option_object.add_option(name, value, None, sub_widget_type)

                if hasattr(sub_widget, 'child_layout'):
                    self._write_widget_options(sub_widget)

    def _write_all(self):

        if not self._option_object:
            qt.logger.warning('Impossible to write options because option object is not defined!')
            return

        self._option_object.clear_options()

        options_list = self._find_list(self)
        self._write_widget_options(options_list)

    def _fill_background(self, widget):
        """
        Internal function used to paint the background color of the group
        :param widget: Option
        """

        palette = widget.palette()
        if not tp.Dcc.get_name() == tp.Dccs.Maya:
            palette.setColor(widget.backgroundRole(), Qt.gray)
        else:
            palette.setColor(widget.backgroundRole(), QColor(35, 150, 245, 255))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)

    def _unfill_background(self, widget):
        """
        Internal function that clears the background color of the group
        :param widget: Option
        """

        palette = widget.palette()
        palette.setColor(widget.backgroundRole(), widget._original_background_color)
        widget.setAutoFillBackground(False)
        widget.setPalette(palette)

    def _on_item_menu(self, pos):
        """
        Internal callback function that is is called when the user right click on an Option
        Pop ups item menu on given position
        :param pos: QPoint
        """

        if not self._parent.is_edit_mode():
            return

        if self._parent.is_widget_to_copy():
            self.paste_action.setVisible(True)

        self._context_menu.exec_(self.mapToGlobal(pos))

    def _on_activate_edit_mode(self):
        """
        Internal callback function that is called when the user presses edit mode button
        """

        self.editModeChanged.emit(True)

    def _on_copy_widget(self):
        """
        Internal callback function that is called when the user copy a Option
        """

        self._parent.set_widget_to_copy(self)

    def _on_paste_widget(self):
        """
        Internal callback function that is called when the user paste a Option
        """

        self.paste_action.setVisible(False)
        widget_to_copy = self._parent.is_widget_to_copy()
        if widget_to_copy.task_option_type == 'group':
            widget_to_copy.copy_to(self)


class OptionListGroup(OptionList, object):
    updateValues = Signal(object)
    widgetClicked = Signal(object)

    def __init__(self, name, option_object, parent=None):
        self._name = name
        super(OptionListGroup, self).__init__(option_object=option_object, parent=parent)

        self.setObjectName(name)
        self._original_background_color = self.palette().color(self.backgroundRole())
        self._option_type = self.get_option_type()
        self.supress_select = False
        self.copy_action.setVisible(False)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

    def mousePressEvent(self, event):
        super(OptionListGroup, self).mousePressEvent(event)

        if not event.button() == Qt.LeftButton:
            return

        half = self.width() * 0.5
        if event.y() > 25 and event.x() > (half - 50) and event.x() < (half + 50):
            return

        parent = self.get_parent()
        if parent:
            parent.supress_select = True
        if self.supress_select:
            self.supress_select = False
            return

        self.widgetClicked.emit(self)

    def setup_ui(self):
        main_group_layout = layouts.VerticalLayout()
        main_group_layout.setContentsMargins(0, 0, 0, 0)
        main_group_layout.setSpacing(1)
        self.group = OptionGroup(self._name)
        self.child_layout = self.group.child_layout

        self.main_layout = layouts.VerticalLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addSpacing(2)
        self.main_layout.addWidget(self.group)
        self.setLayout(self.main_layout)

        self.group.expand.connect(self._on_expand_updated)

    def _create_context_menu(self):
        """
        Internal function that creates context menu of the group
        """

        super(OptionListGroup, self)._create_context_menu()

        string_icon = tp.ResourcesMgr().icon('rename')
        remove_icon = tp.ResourcesMgr().icon('trash')

        rename_action = QAction(string_icon, 'Rename', self._context_menu)
        self._context_menu.addAction(rename_action)
        remove_action = QAction(remove_icon, 'Remove', self._context_menu)
        self._context_menu.addAction(remove_action)

        rename_action.triggered.connect(self.rename)
        remove_action.triggered.connect(self.remove)

    def get_name(self):
        """
        Returns option group name
        :return: str
        """

        return self.group.title()

    def set_name(self, name):
        """
        Sets option group name
        :param name: str
        """

        self.group.setTitle(name)

    def get_option_type(self):
        """
        Returns the type of the option
        :return: str
        """

        return 'group'

    def get_value(self):
        """
        Returns whether group is expanded or not
        :return: bool
        """

        expanded = not self.group.is_collapsed()
        return expanded

    def get_children(self):
        """
        Returns all group Options
        :return: list(Option)
        """

        item_count = self.child_layout.count()
        found = list()
        for i in range(item_count):
            item = self.child_layout.itemAt(i)
            widget = item.widget()
            found.append(widget)

        return found

    def set_expanded(self, flag):
        """
        Sets the expanded/collapsed state of the group
        :param flag: bool
        """

        if flag:
            self.expand_group()
        else:
            self.collapse_group()

    def expand_group(self):
        """
        Expands group
        """

        self.group.expand_group()

    def collapse_group(self):
        """
        Collapse gorup
        """

        self.group.collapse_group()

    def save(self):
        """
        Function that saves the current state of the group option
        :return:
        """
        self._write_options(clear=False)

    def rename(self, new_name=None):
        """
        Function that renames group
        :param new_name: variant, str or None
        """

        found = self._get_widget_names()
        title = self.group.title()
        if not new_name:
            new_name = qtutils.get_string_input('Rename Group', old_name=title)
        if new_name is None or new_name == title:
            return

        while new_name in found:
            new_name = name_utils.increment_last_number(new_name)

        self.group.setTitle(new_name)
        self._write_all()

    def move_up(self):
        """
        Function that moves up selected Options
        """

        parent = self.parent()
        layout = parent.child_layout
        index = layout.indexOf(self)
        if index == 0:
            return
        index -= 1
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)

        self._write_all()

    def move_down(self):
        """
        Function that moves down selected options
        """

        parent = self.parent()
        layout = parent.child_layout
        index = layout.indexOf(self)
        if index == (layout.count() - 1):
            return
        index += 1
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)

        self._write_all()

    def copy_to(self, parent):
        """
        Function that copy selected options into given parent
        :param parent: Option
        """

        group = parent.add_group(self.get_name(), parent)
        children = self.get_children()
        for child in children:
            if child == group:
                continue
            child.copy_to(group)

    def remove(self):
        """
        Function that removes selected options
        :return:
        """
        parent = self.parent()
        if self in self._parent._current_widgets:
            remove_index = self._parent._current_widgets.index(self)
            self._parent._current_widgets.pop(remove_index)
        parent.child_layout.removeWidget(self)
        self.deleteLater()
        self._write_all()

    def _on_expand_updated(self, value):
        self.updateValues.emit(False)
