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
from tpDcc.libs.python import name as name_utils
from tpDcc.libs.qt.core import qtutils
from tpDcc.libs.qt.widgets import layouts
from tpDcc.libs.qt.widgets.options import factory


class GroupStyles(object):
    Boxed = 0
    Rounded = 1
    Square = 2
    Maya = 3


class OptionList(QGroupBox, object):
    editModeChanged = Signal(bool)
    valueChanged = Signal()

    FACTORY_CLASS = factory.OptionsFactorySingleton

    def __init__(self, parent=None, option_object=None):
        super(OptionList, self).__init__(parent)
        self._option_object = option_object
        self._parent = parent

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_item_menu)
        self._context_menu = QMenu()
        self._context_menu.setTearOffEnabled(True)
        self._create_context_menu(self._context_menu, parent=self)

        self._has_first_group = False
        self._disable_auto_expand = False
        self._supress_update = False
        self._central_list = self
        self._option_group_class = OptionListGroup
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

        if parent.__class__.__name__.endswith('OptionList'):
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
        self._option_group_class.FACTORY_CLASS = self.FACTORY_CLASS
        group = self._option_group_class(name=name, option_object=option_object, parent=self._parent)
        self._create_group_context_menu(group, group._context_menu)
        group.set_expanded(value)
        if self.__class__.__name__.endswith('OptionListGroup') or parent.__class__.__name__.endswith('OptionListGroup'):
            if tp.is_maya():
                group.group.set_inset_dark()
        self._handle_parenting(group, parent)
        self._write_options(clear=False)
        self._has_first_group = True

        return group

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

    def _create_context_menu(self, menu, parent):

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

        create_menu = menu.addMenu(plus_icon, 'Add Options')
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
        menu.addSeparator()
        parent.copy_action = QAction(copy_icon, 'Copy', menu)
        menu.addAction(parent.copy_action)
        parent.copy_action.setVisible(False)
        parent.paste_action = QAction(paste_icon, 'Paste', menu)
        menu.addAction(parent.paste_action)
        parent.paste_action.setVisible(False)
        menu.addSeparator()
        clear_action = QAction(clear_icon, 'Clear', menu)
        menu.addAction(clear_action)

        add_string_action.triggered.connect(partial(parent._add_option, 'string'))
        add_directory_action.triggered.connect(partial(parent._add_option, 'directory'))
        add_file_action.triggered.connect(partial(parent._add_option, 'file'))
        add_integer_action.triggered.connect(partial(parent._add_option, 'integer'))
        add_float_action.triggered.connect(partial(parent._add_option, 'float'))
        add_bool_action.triggered.connect(partial(parent._add_option, 'boolean'))
        add_list_action.triggered.connect(partial(parent._add_option, 'list'))
        add_dict_action.triggered.connect(partial(parent._add_option, 'dictionary'))
        add_group_action.triggered.connect(parent.add_group)
        add_title_action.triggered.connect(partial(parent._add_option, 'title'))
        add_color_action.triggered.connect(partial(parent._add_option, 'color'))
        add_vector3f_action.triggered.connect(partial(parent._add_option, 'vector3f'))
        add_script_action.triggered.connect(partial(parent._add_option, 'script'))
        clear_action.triggered.connect(parent._clear_action)

        return create_menu

    def _create_group_context_menu(self, group, menu):
        self._create_context_menu(menu=menu, parent=group)

        group.copy_action.setVisible(False)

        string_icon = tp.ResourcesMgr().icon('rename')
        remove_icon = tp.ResourcesMgr().icon('trash')

        rename_action = QAction(string_icon, 'Rename', menu)
        menu.addAction(rename_action)
        remove_action = QAction(remove_icon, 'Remove', menu)
        menu.addAction(remove_action)

        rename_action.triggered.connect(group.rename)
        remove_action.triggered.connect(group.remove)

        return menu

    def _add_option(self, option_type, name=None, value=None, parent=None):
        if option_type is None:
            return

        if option_type == 'group':
            new_option = self.add_group('group')
        else:
            option_object = self.get_option_object()
            name = self._get_unique_name(name or option_type, parent=parent)
            new_option = self.FACTORY_CLASS().add_option(
                option_type, name=name, value=value, parent=parent,
                main_widget=self._parent, option_object=option_object)
            if new_option:
                self._handle_parenting(new_option, parent=parent)
                self._write_options(clear=False)
            else:
                qt.logger.warning('Option of type "{}" is not supported!'.format(option_type))

        return new_option

    def _add_custom_option(self, optiontype, name=None, value=None, parent=None):
        pass

    def _get_unique_name(self, name, parent=None):
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
                if issubclass(sub_parent.__class__, OptionList) and not \
                        sub_parent.__class__.__name__.endswith('OptionListGroup'):
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
                    # value = option[1][0]
                    # option_type = option[1][1]
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

                if not is_group:
                    if not option_type:
                        if type(value) == unicode or type(value) == str:
                            option_type = 'string'
                        elif type(value) == float:
                            option_type = 'float'
                        elif type(option[1]) == int:
                            option_type = 'integer'
                        elif type(option[1]) == bool:
                            option_type = 'boolean'
                        elif type(option[1]) == dict:
                            option_type = 'dictionary'
                        elif type(option[1]) == list:
                            option_type = 'list'
                        elif option[1] is None:
                            option_type = 'title'

                    new_option = self._add_custom_option(option_type, name, value, widget)
                    if not new_option:
                        self._add_option(option_type, name, value, widget)

        except Exception:
            qt.logger.error(traceback.format_exc())
        finally:
            self._disable_auto_expand = False
            # self.setVisible(True)
            # self.setUpdatesEnabled(True)
            self._supress_update = False
            self._auto_rename = True

    def _find_list(self, widget):
        if widget.__class__.__name__.endswith('OptionList'):
            return widget

        parent = widget.get_parent()
        if not parent:
            return

        while not parent.__class__.__name__.endswith('OptionList'):
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

    def _create_context_menu(self, menu, parent):
        pass

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


class OptionGroup(QGroupBox, object):
    expand = Signal(bool)

    def __init__(self, name, parent=None):
        super(OptionGroup, self).__init__(parent)

        if tp.is_maya():
            if tp.Dcc.get_version() < 2016:
                # self.setFrameStyle(self.Panel | self.Raised)
                palette = self.palette()
                palette.setColor(self.backgroundRole(), QColor(80, 80, 80))
                self.setAutoFillBackground(True)
                self.setPalette(palette)
            # else:
            #     self.setFrameStyle(self.NoFrame)

        if tp.Dcc.get_name() == tp.Dccs.Maya:
            self._rollout_style = GroupStyles.Maya
        else:
            self._rollout_style = GroupStyles.Square

        self._expanded = True
        self._clicked = False
        self._collapsible = True

        self.close_height = 28
        self.setMinimumHeight(self.close_height)
        self.background_shade = 80

        self.main_layout = layouts.VerticalLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        self.child_layout = layouts.VerticalLayout()
        self.child_layout.setContentsMargins(0, 2, 0, 3)
        self.child_layout.setSpacing(0)
        self.child_layout.setAlignment(Qt.AlignTop)

        self.header_layout = layouts.HorizontalLayout()

        self.main_layout.addSpacing(4)
        self.main_layout.addLayout(self.child_layout)

        self.setObjectName(name)
        self.setTitle(name)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._expand_collapse_rect().contains(event.pos()):
            self._clicked = True
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        if self._clicked and self._expand_collapse_rect().contains(event.pos()):
            self.toggle_collapsed()
            self.expand.emit(False)
            event.accept()
        else:
            event.ignore()
        self._clicked = False

    def mouseMoveEvent(self, event):
        event.ignore()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(painter.Antialiasing)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        x = self.rect().x()
        y = self.rect().y()
        w = self.rect().width() - 1
        h = self.rect().height() - 1
        r = 8
        if self._rollout_style == GroupStyles.Rounded:
            painter.drawText(x + 33, y + 3, w, 16, Qt.AlignLeft | Qt.AlignTop, self.title())
            self._draw_triangle(painter, x, y)
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.6)
            painter.setPen(pen)
            painter.drawRoundedRect(x + 1, y + 1, w - 1, h - 1, r, r)
            pen.setColor(self.palette().color(QPalette.Shadow))
            painter.setPen(pen)
            painter.drawRoundedRect(x, y, w - 1, h - 1, r, r)
        if self._rollout_style == GroupStyles.Square:
            painter.drawText(x + 33, y + 3, w, 16, Qt.AlignLeft | Qt.AlignTop, self.title())
            self._draw_triangle(painter, x, y)
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.6)
            painter.setPen(pen)
            painter.drawRect(x + 1, y + 1, w - 1, h - 1)
            pen.setColor(self.palette().color(QPalette.Shadow))
            painter.setPen(pen)
            painter.drawRect(x, y, w - 1, h - 1)
        if self._rollout_style == GroupStyles.Maya:
            # painter.drawText(
            # x + (45 if self.dragDropMode() == ExpanderDragDropModes.InternalMove else 25),
            # y + 3, w, 16, Qt.AlignLeft | Qt.AlignTop, self.title())
            painter.drawText(x + 25, y + 3, w, 16, Qt.AlignLeft | Qt.AlignTop, self.title())
            painter.setRenderHint(QPainter.Antialiasing, False)
            self._draw_triangle(painter, x, y)
            header_height = 20
            header_rect = QRect(x + 1, y + 1, w - 1, header_height)
            header_rect_shadow = QRect(x - 1, y - 1, w + 1, header_height + 2)
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.4)
            painter.setPen(pen)
            painter.drawRect(header_rect)
            painter.fillRect(header_rect, QColor(255, 255, 255, 18))
            pen.setColor(self.palette().color(QPalette.Dark))
            painter.setPen(pen)
            painter.drawRect(header_rect_shadow)
            if not self.is_collapsed():
                pen = QPen(self.palette().color(QPalette.Dark))
                pen.setWidthF(0.8)
                painter.setPen(pen)
                offSet = header_height + 3
                body_rect = QRect(x, y + offSet, w, h - offSet)
                body_rect_shadow = QRect(x + 1, y + offSet, w + 1, h - offSet + 1)
                painter.drawRect(body_rect)
                pen.setColor(self.palette().color(QPalette.Light))
                pen.setWidthF(0.4)
                painter.setPen(pen)
                painter.drawRect(body_rect_shadow)
        elif self._rollout_style == GroupStyles.Boxed:
            if self.isCollapsed():
                arect = QRect(x + 1, y + 9, w - 1, 4)
                brect = QRect(x, y + 8, w - 1, 4)
                text = '+'
            else:
                arect = QRect(x + 1, y + 9, w - 1, h - 9)
                brect = QRect(x, y + 8, w - 1, h - 9)
                text = '-'
            pen = QPen(self.palette().color(QPalette.Light))
            pen.setWidthF(0.6)
            painter.setPen(pen)
            painter.drawRect(arect)
            pen.setColor(self.palette().color(QPalette.Shadow))
            painter.setPen(pen)
            painter.drawRect(brect)
            painter.setRenderHint(painter.Antialiasing, False)
            painter.setBrush(self.palette().color(QPalette.Window).darker(120))
            painter.drawRect(x + 10, y + 1, w - 20, 16)
            painter.drawText(x + 16, y + 1, w - 32, 16, Qt.AlignLeft | Qt.AlignVCenter, text)
            painter.drawText(x + 10, y + 1, w - 20, 16, Qt.AlignCenter, self.title())
        # if self.dragDropMode():
        #     rect = self.dragDropRect()
        #     l = rect.left()
        #     r = rect.right()
        #     cy = rect.center().y()
        #     pen = QPen(self.palette().color(self.isCollapsed() and QPalette.Shadow or QPalette.Mid))
        #     painter.setPen(pen)
        #     for y in (cy - 3, cy, cy + 3):
        #         painter.drawLine(l, y, r, y)
        painter.end()

    def is_collapsible(self):
        return self._collapsible

    def is_collapsed(self):
        return not self._expanded

    def set_collapsed(self, state):
        if self.is_collapsible():
            self._expanded = not state
            if state:
                self.setMinimumHeight(22)
                self.setMaximumHeight(22)
            else:
                self.setMinimumHeight(0)
                self.setMaximumHeight(1000000)

    def toggle_collapsed(self):
        self.set_collapsed(not self.is_collapsed())

    def expand_group(self):
        self.set_collapsed(False)

    def collapse_group(self):
        self.set_collapsed(True)

    def set_inset_dark(self):
        value = self.background_shade
        value -= 15
        if tp.Dcc.get_name() == tp.Dccs.Maya:
            if tp.Dcc.get_version() < 2016:
                self.setFrameStyle(self.Panel | self.Sunken)

        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(value, value, value))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

    def _draw_triangle(self, painter, x, y):
        if self._rollout_style == GroupStyles.Maya:
            brush = QBrush(QColor(255, 0, 0, 160), Qt.SolidPattern)
        else:
            brush = QBrush(QColor(255, 255, 255, 160), Qt.SolidPattern)
        if not self.is_collapsed():
            tl, tr, tp = QPoint(x + 9, y + 8), QPoint(x + 19, y + 8), QPoint(x + 14, y + 13)
            points = [tl, tr, tp]
            triangle = QPolygon(points)
        else:
            tl, tr, tp = QPoint(x + 11, y + 5), QPoint(x + 16, y + 10), QPoint(x + 11, y + 15)
            points = [tl, tr, tp]
            triangle = QPolygon(points)
        current_pen = painter.pen()
        current_brush = painter.brush()
        painter.setPen(Qt.NoPen)
        painter.setBrush(brush)
        painter.drawPolygon(triangle)
        painter.setPen(current_pen)
        painter.setBrush(current_brush)

    def _expand_collapse_rect(self):
        return QRect(0, 0, self.width(), 20)
