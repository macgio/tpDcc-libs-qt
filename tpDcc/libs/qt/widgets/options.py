#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget to handle editable options
"""

from __future__ import print_function, division, absolute_import

import string
import traceback

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc as tp
from tpDcc.libs import qt
from tpDcc.libs.python import name as name_utils
from tpDcc.libs.qt.core import base, qtutils
from tpDcc.libs.qt.widgets import buttons, splitters, spinbox, code, directory


class GroupStyles(object):
    Boxed = 0
    Rounded = 1
    Square = 2
    Maya = 3


class OptionObject(object):
    def __init__(self):
        super(OptionObject, self).__init__()

    def has_options(self):
        return False

    def get_options(self):
        return dict()

    def add_option(self, name, value, group=None, option_type=None):
        pass

    def clear_options(self):
        pass


class OptionsWidget(base.BaseWidget, object):

    editModeChanged = Signal(bool)

    def __init__(self, option_object=None, settings=None, parent=None):

        self._option_object = option_object
        self._settings = settings
        self._edit_mode = False
        self._current_widgets = list()
        self._widget_to_copy = None

        super(OptionsWidget, self).__init__(parent)

        policy = self.sizePolicy()
        policy.setHorizontalPolicy(policy.Expanding)
        policy.setVerticalPolicy(policy.Expanding)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(policy)

    def ui(self):
        super(OptionsWidget, self).ui()

        edit_mode_icon = tp.ResourcesMgr().icon('edit')
        move_up_icon = tp.ResourcesMgr().icon('sort_up')
        move_down_icon = tp.ResourcesMgr().icon('sort_down')
        remove_icon = tp.ResourcesMgr().icon('delete')

        self._edit_widget = QWidget()
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        self._edit_widget.setLayout(top_layout)
        self.main_layout.addWidget(self._edit_widget)
        self._edit_mode_btn = buttons.IconButton(
            icon=edit_mode_icon, icon_padding=2, button_style=buttons.ButtonStyles.FlatStyle)
        self._edit_mode_btn.setCheckable(True)
        self._edit_mode_btn.setMaximumWidth(45)
        self._edit_mode_btn.setMinimumHeight(15)
        top_layout.addWidget(self._edit_mode_btn)

        horizontal_separator = QFrame()
        horizontal_separator.setFrameShape(QFrame.VLine)
        horizontal_separator.setFrameShadow(QFrame.Sunken)
        top_layout.addWidget(horizontal_separator)

        self._move_up_btn = buttons.IconButton(
            icon=move_up_icon, icon_padding=0, button_style=buttons.ButtonStyles.FlatStyle)
        self.move_down_btn = buttons.IconButton(
            icon=move_down_icon, icon_padding=0, button_style=buttons.ButtonStyles.FlatStyle)
        self.remove_btn = buttons.IconButton(
            icon=remove_icon, icon_padding=0, button_style=buttons.ButtonStyles.FlatStyle)
        self._move_up_btn.setEnabled(False)
        self.move_down_btn.setEnabled(False)
        self.remove_btn.setEnabled(False)
        top_layout.addWidget(self._move_up_btn)
        top_layout.addWidget(self.move_down_btn)
        top_layout.addWidget(self.remove_btn)
        self._edit_splitter = QWidget()
        edit_splitter_layout = splitters.SplitterLayout()
        self._edit_splitter.setLayout(edit_splitter_layout)
        self.main_layout.addWidget(self._edit_splitter)

        self._scroll = QScrollArea()
        self._scroll.setFocusPolicy(Qt.NoFocus)
        self._scroll.setWidgetResizable(True)
        self.setFocusPolicy(Qt.NoFocus)
        self._options_list = OptionList(parent=self)
        self._scroll.setWidget(self._options_list)

        self.main_layout.addWidget(self._scroll)

    def setup_signals(self):
        self._edit_mode_btn.toggled.connect(self._on_edit_mode)
        self._move_up_btn.clicked.connect(self._on_move_up)
        self.move_down_btn.clicked.connect(self._on_move_down)
        self.remove_btn.clicked.connect(self._on_remove)

    def settings(self):
        """
        Returns settings object
        :return: JSONSettings
        """

        return self._settings

    def set_settings(self, settings):
        """
        Sets save widget settings
        :param settings: JSONSettings
        """

        self._settings = settings

    def get_option_object(self):
        """
        Returns the option object linked to this widget
        :return: object
        """

        return self._option_object

    def set_option_object(self, option_object):
        """
        Sets option_object linked to this widget
        :param option_object: object
        """

        self._option_object = option_object
        self._options_list.set_option_object(option_object)

    def get_option_type(self):
        """
        Returns option widget type
        :return: str
        """

        return self._option_type

    def is_edit_mode(self):
        """
        Returns whether current option is editable or not
        :return: bool
        """

        return self._edit_mode

    def set_edit_mode(self, flag):
        """
        Sets whether the current option is editable or not
        :param flag: bool
        """

        self._on_edit_mode(flag)

    def is_widget_to_copy(self):
        """
        Returns whether an option widget is being copied or not
        :return: bool
        """

        return self._widget_to_copy

    def set_widget_to_copy(self, widget_to_copy):
        """
        Sets widget that we want to copy
        :param QWidget
        """

        self._widget_to_copy = widget_to_copy

    def show_edit_widget(self):
        self._edit_widget.setVisible(True)
        self._edit_splitter.setVisible(True)

    def hide_edit_widget(self):
        self._edit_widget.setVisible(False)
        self._edit_splitter.setVisible(False)

    def update_options(self):
        """
        Function that updates the current options of the selected task
        """

        self._options_list.clear_widgets()

        if not self._option_object:
            qt.logger.warning('Impossible to update options because option object is not defined!')
            return

        self._options_list.update_options()

    def clear_options(self):
        """
        Clears all the options
        """

        self._options_list.clear_widgets()
        if self._option_object:
            self._option_object = None

    def has_options(self):
        """
        Checks if the current task has options or not
        :return: bool
        """

        if not self._option_object:
            qt.logger.warning('Impossible to check options because option object is not defined!')
            return

        return self._option_object.has_options()

    def _edit_activate(self, edit_value):
        """
        Internal function that updates widget states when edit button is pressed
        :param edit_value: bool
        """

        self._edit_mode = edit_value
        self.move_down_btn.setEnabled(edit_value)
        self._move_up_btn.setEnabled(edit_value)
        self.remove_btn.setEnabled(edit_value)
        if not edit_value:
            self._options_list.clear_selection()
        self._options_list.set_edit(edit_value)

    def _on_edit_mode(self, edit_value):
        """
        Internal callback function that is called when the user presses edit mode button
        :param edit_value: bool
        """

        self._edit_activate(edit_value)
        self.editModeChanged.emit(edit_value)

    def _on_move_up(self):
        """
        Internal callback function that is called when the user pressed move up button
        Move selected items up in the list
        """

        widgets = self._current_widgets
        if not widgets:
            return

        widgets = self._options_list.sort_widgets(widgets, widgets[0].get_parent())
        if not widgets:
            return
        for w in widgets:
            w.move_up()

    def _on_move_down(self):
        """
        Internal callback function that is called when the user pressed move down button
        Move selected items down in the list
        """

        widgets = self._current_widgets
        if not widgets:
            return

        widgets = self._options_list.sort_widgets(widgets, widgets[0].get_parent())
        if not widgets:
            return
        for w in widgets:
            w.move_down()

    def _on_remove(self):
        """
        Internal callback function that is called when the user pressed remove button
        Remove selected options
        """

        widgets = self._current_widgets
        if not widgets:
            return

        widgets = self._options_list.sort_widgets(widgets, widgets[0].get_parent())
        if not widgets:
            return
        for w in widgets:
            w.remove()


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
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        self.child_layout = QVBoxLayout()
        self.child_layout.setContentsMargins(0, 0, 0, 0)
        self.child_layout.setSpacing(0)
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

    def add_title(self, name='title', parent=None):
        """
        Adds new title property to the group box
        :param name: str
        :param parent: QWidget
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

    def add_directory(self, name='file', value='', parent=None):
        """
        Adds new directory property to the group box
        :param name: str
        :param value: str, default value of the property
        :param parent: QWidget
        """

        if type(name) == bool:
            name = 'file'

        name = self._get_unique_name(name, parent)
        directory_option = DirectoryOption(name=name, parent=parent, main_widget=self._parent)
        directory_option.set_value(value)
        self._handle_parenting(directory_option, parent)
        self._write_options(clear=False)

    def add_non_editable_text(self, name='string', value='', parent=None):
        """
        Adds new non editable string property to the group box
        :param name: str
        :param value: str, default value of the property
        :param parent: QWidget
        """

        ame = self._get_unique_name(name, parent)
        string_option = NonEditTextOption(name=name, parent=parent, main_widget=self._parent)
        string_option.set_value(value)
        self._handle_parenting(string_option, parent)
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
        self._context_menu = QMenu()
        self._context_menu.setTearOffEnabled(True)

        plus_icon = tp.ResourcesMgr().icon('plus')
        string_icon = tp.ResourcesMgr().icon('rename')
        directory_icon = tp.ResourcesMgr().icon('folder')
        integer_icon = tp.ResourcesMgr().icon('number_1')
        float_icon = tp.ResourcesMgr().icon('float_1')
        bool_icon = tp.ResourcesMgr().icon('true_false')
        group_icon = tp.ResourcesMgr().icon('group_objects')
        script_icon = tp.ResourcesMgr().icon('source_code')
        title_icon = tp.ResourcesMgr().icon('label')
        clear_icon = tp.ResourcesMgr().icon('clean')
        copy_icon = tp.ResourcesMgr().icon('copy')
        paste_icon = tp.ResourcesMgr().icon('paste')

        create_menu = self._context_menu.addMenu(plus_icon, 'Add Options')
        add_string_action = QAction(string_icon, 'Add String', create_menu)
        create_menu.addAction(add_string_action)
        add_directory_action = QAction(directory_icon, 'Add Directory', create_menu)
        create_menu.addAction(add_directory_action)
        add_integer_action = QAction(integer_icon, 'Add Integer', create_menu)
        create_menu.addAction(add_integer_action)
        add_float_action = QAction(float_icon, 'Add Float', create_menu)
        create_menu.addAction(add_float_action)
        add_bool_action = QAction(bool_icon, 'Add Bool', create_menu)
        create_menu.addAction(add_bool_action)
        add_group_action = QAction(group_icon, 'Add Group', create_menu)
        create_menu.addAction(add_group_action)
        add_script_action = QAction(script_icon, 'Add Script', create_menu)
        create_menu.addAction(add_script_action)
        add_title_action = QAction(title_icon, 'Add Title', create_menu)
        create_menu.addAction(add_title_action)
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

        add_string_action.triggered.connect(self.add_string)
        add_directory_action.triggered.connect(self.add_directory)
        add_integer_action.triggered.connect(self.add_integer)
        add_float_action.triggered.connect(self.add_float)
        add_bool_action.triggered.connect(self.add_boolean)
        add_group_action.triggered.connect(self.add_group)
        add_title_action.triggered.connect(self.add_title)
        add_script_action.triggered.connect(self.add_script)
        clear_action.triggered.connect(self._clear_action)

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
                if sub_parent.__class__ == OptionList:
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

        self.setHidden(True)
        self.setUpdatesEnabled(False)
        self._supress_update = True
        self._disable_auto_expand = True
        self._auto_rename = False

        try:
            for option in options:
                option_type = None
                if type(option[1]) == list:
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
                    if type(option[1]) == int:
                        self.add_integer(name, value, widget)
                    if type(option[1]) == bool:
                        self.add_boolean(name, value, widget)
                    if type(option[1]) == dict:
                        self.add_dictonary(name, [value, []], widget)
                    elif option[1] is None:
                        self.add_title(name, widget)

                if option_type == 'script':
                    self.add_script(name, value, widget)
                if option_type == 'dictionary':
                    self.add_dictonary(name, value, widget)
                if option_type == 'nonedittext':
                    self.add_non_editable_text(name, value, widget)
                if option_type == 'directory':
                    self.add_directory(name, value, widget)

        except Exception:
            qt.logger.error(traceback.format_exc())

        self._disable_auto_expand = False
        self.setVisible(True)
        self.setUpdatesEnabled(True)
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
        Intenal function that writes current options into disk
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
    # endregion


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
        main_group_layout = QVBoxLayout()
        main_group_layout.setContentsMargins(0, 0, 0, 0)
        main_group_layout.setSpacing(1)
        self.group = OptionGroup(self._name)
        self.child_layout = self.group.child_layout

        self.main_layout = QVBoxLayout()
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

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        self.child_layout = QVBoxLayout()
        self.child_layout.setContentsMargins(0, 2, 0, 3)
        self.child_layout.setSpacing(0)
        self.child_layout.setAlignment(Qt.AlignTop)

        self.header_layout = QHBoxLayout()

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


class Option(base.BaseWidget, object):
    updateValues = Signal(object)
    widgetClicked = Signal(object)

    def __init__(self, name, parent=None, main_widget=None):

        self._option_object = None

        super(Option, self).__init__(parent=parent)

        self._parent = main_widget

        self._name = name
        self._original_background_color = self.palette().color(self.backgroundRole())
        self._option_type = self.get_option_type()
        self._option_widget = self.get_option_widget()
        if self._option_widget:
            self.main_layout.addWidget(self._option_widget)
        self._setup_option_widget_value_change()

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_item_menu)
        self._context_menu = None
        self._create_context_menu()

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        return main_layout

    def ui(self):
        super(Option, self).ui()

    def mousePressEvent(self, event):
        super(Option, self).mousePressEvent(event)
        if not event.button() == Qt.LeftButton:
            return
        parent = self.get_parent()
        if parent:
            parent.supress_select = True
        self.widgetClicked.emit(self)

    def get_option_type(self):
        return None

    def get_option_widget(self):
        return None

    def get_name(self):
        name = self._option_widget.get_label_text()
        return name

    def set_name(self, name):
        self._option_widget.set_label_text(name)

    def set_value(self, value):
        pass

    def get_value(self):
        pass

    def get_parent(self):
        parent = self.parent()
        grand_parent = parent.parent()
        if hasattr(grand_parent, 'group'):
            parent = grand_parent
        if not hasattr(parent, 'child_layout'):
            return

        if parent.__class__ == OptionList:
            return parent

        return parent

    def rename(self):
        title = self.get_name()
        new_name = qtutils.get_string_input('Rename Option', old_name=title)
        found = self._get_widget_names()
        if new_name == title or new_name is None or new_name == '':
            return

        while new_name in found:
            new_name = name_utils.increment_last_number(new_name)
        self.set_name(new_name)
        self.updateValues.emit(True)

    def remove(self):
        parent = self.get_parent()
        if self in self._parent._current_widgets:
            remove_index = self._parent._current_widgets.index(self)
            self._parent._current_widgets.pop(remove_index)
        parent.child_layout.removeWidget(self)
        self.deleteLater()
        self.updateValues.emit(True)

    def move_up(self):
        parent = self.get_parent()
        if not parent:
            parent = self.parent()
        layout = parent.child_layout
        index = layout.indexOf(self)
        if index == 0:
            return
        index -= 1
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)
        self.updateValues.emit(True)

    def move_down(self):
        parent = self.get_parent()
        if not parent:
            parent = self.parent()
        layout = parent.child_layout
        index = layout.indexOf(self)
        if index == 0:
            return
        index += 1
        parent.child_layout.removeWidget(self)
        layout.insertWidget(index, self)
        self.updateValues.emit(True)

    def copy_to(self, parent):
        name = self.get_name()
        value = self.get_value()
        new_inst = self.__class__(name)
        new_inst.set_value(value)
        parent.child_layout.addWidget(new_inst)

    def set_option_object(self, option_object):
        self._option_object = option_object

    def _setup_option_widget_value_change(self):
        pass

    def _copy(self):
        self._parent.set_widget_to_copy(self)

    def _get_widget_names(self):
        item_count = self.parent().child_layout.count()
        found = list()
        for i in range(item_count):
            item = self.parent().child_layout.itemAt(i)
            widget = item.widget()
            widget_label = widget.get_name()
            found.append(widget_label)

        return found

    def _create_context_menu(self):
        self._context_menu = QMenu()

        move_up_icon = tp.ResourcesMgr().icon('sort_up')
        move_down_icon = tp.ResourcesMgr().icon('sort_down')
        rename_icon = tp.ResourcesMgr().icon('rename')
        remove_icon = tp.ResourcesMgr().icon('delete')
        copy_icon = tp.ResourcesMgr().icon('copy')

        move_up_action = QAction(move_up_icon, 'Move Up', self._context_menu)
        self._context_menu.addAction(move_up_action)
        move_down_action = QAction(move_down_icon, 'Move Down', self._context_menu)
        self._context_menu.addAction(move_down_action)
        self._context_menu.addSeparator()
        copy_action = QAction(copy_icon, 'Copy', self._context_menu)
        self._context_menu.addAction(copy_action)
        rename_action = QAction(rename_icon, 'Rename', self._context_menu)
        self._context_menu.addAction(rename_action)
        remove_action = QAction(remove_icon, 'Remove', self._context_menu)
        self._context_menu.addAction(remove_action)

        rename_action.triggered.connect(self.rename)
        remove_action.triggered.connect(self.remove)

    def _on_item_menu(self, pos):
        if not self._parent or not self._parent.is_edit_mode():
            return

        self._context_menu.exec_(self.mapToGlobal(pos))

    def _on_value_change(self):
        self.updateValues.emit(False)


class TitleOption(Option, object):
    def __init__(self, name, parent, main_widget):
        super(TitleOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

        self.main_layout.setContentsMargins(0, 2, 0, 2)
        self.main_layout.setAlignment(Qt.AlignCenter)

    def get_option_widget(self):
        return QLabel(self._name)

    def get_option_type(self):
        return 'title'

    def get_name(self):
        name = self._option_widget.text()
        return name

    def set_name(self, name):
        self._option_widget.setText(name)


class TextOption(Option, object):
    def __init__(self, name, parent, main_widget):
        super(TextOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'text'

    def get_option_widget(self):
        return TextWidget(self._name)

    def get_value(self):
        value = self._option_widget.get_text()
        if not value:
            value = ''

        return value

    def set_value(self, value):
        value = str(value)
        self._option_widget.set_text(value)

    def _setup_option_widget_value_change(self):
        self._option_widget.textChanged.connect(self._on_value_change)


class NonEditTextOption(TextOption, object):
    def __init__(self, name, parent, main_widget):
        super(NonEditTextOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'nonedittext'

    def get_option_widget(self):
        text_widget = super(NonEditTextOption, self).get_option_widget()
        text_widget.text_widget.setReadOnly(True)
        text_widget.insert_button.setVisible(False)
        return text_widget


class DirectoryOption(Option, object):
    def __init__(self, name, parent, main_widget):
        super(DirectoryOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'directory'

    def get_option_widget(self):
        return DirectoryWidget(self._name)

    def get_value(self):
        value = self._option_widget.get_directory()
        if not value:
            value = ''

        return value

    def set_value(self, value):
        value = str(value)
        self._option_widget.set_directory(value)

    def _setup_option_widget_value_change(self):
        self._option_widget.directoryChanged.connect(self._on_value_change)


class FloatOption(Option, object):

    def __init__(self, name, parent, main_widget):
        super(FloatOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'float'

    def get_option_widget(self):
        return spinbox.BaseDoubleSpinBox(self._name)

    def get_value(self):
        return self._option_widget.get_value()

    def set_value(self, value):
        self._option_widget.set_value(value)

    def _setup_option_widget_value_change(self):
        self._option_widget.valueChanged.connect(self._on_value_change)
    # endregion


class IntegerOption(FloatOption, object):

    def __init__(self, name, parent, main_widget):
        super(IntegerOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'integer'

    def get_option_widget(self):
        return spinbox.BaseSpinBox(self._name)


class BooleanOption(FloatOption, object):

    def __init__(self, name, parent, main_widget):
        super(BooleanOption, self).__init__(name=name, parent=parent, main_widget=main_widget)
        self.main_layout.setContentsMargins(0, 2, 0, 2)

    def get_option_type(self):
        return 'boolean'

    def get_option_widget(self):
        return BoolWidget(self._name)


class ScriptOption(Option, object):
    def __init__(self, name, parent, main_widget):
        super(ScriptOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

        self.main_layout.setContentsMargins(0, 2, 0, 2)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.main_layout.setAlignment(Qt.AlignCenter | Qt.AlignTop)

    def get_option_type(self):
        return 'script'

    def _setup_option_widget_value_change(self):
        self._option_widget.textChanged.connect(self._on_value_change)

    def get_name(self):
        name = self._option_widget.insert_button.text()
        return name

    def set_name(self, name):
        self._option_widget.set_option_object(self._option_object)
        self._option_widget.set_button_text(name)

    def get_value(self):
        value = self._option_widget.get_text()
        if not value:
            value = ''

        return value

    def set_value(self, value):
        self._option_widget.set_option_object(self._option_object)
        self._option_widget.set_text(str(value))

    def set_option_object(self, option_object):
        super(ScriptOption, self).set_option_object(option_object)
        self._option_widget.set_option_object(option_object)

    def set_edit_mode(self, flag):
        super(ScriptOption, self).set_edit_mode(flag)

        if flag:
            self._option_widget.text_widget.show()
            self.main_layout.setContentsMargins(0, 2, 0, 15)
            self._option_widget.set_minimum()
        else:
            self._option_widget.text_widget.hide()
            self.main_layout.setContentsMargins(0, 2, 0, 2)

        self._option_widget.set_option_object(self._option_object)

    def run_script(self):
        value = self.get_value()
        self._option_object.run_code_snippet(value)
        parent = self.get_parent()
        if hasattr(parent, 'refresh'):
            parent.refresh()

    def get_option_widget(self):
        btn = ScriptWidget(name='option script')
        btn.set_label_text('')
        btn.set_use_button(True)
        btn.set_button_text(self._name)
        btn.set_button_to_first()
        btn.text_label.hide()
        btn.set_supress_button_command(True)
        btn.insert_button.clicked.connect(self.run_script)
        # if not self.edit_mode:
        #     btn.text_widget.hide()
        btn.set_completer(code.CodeCompleter)
        if self._option_object:
            btn.set_option_object(self._option_object)

        return btn


class TextWidget(base.BaseWidget, object):
    textChanged = Signal(str)

    def __init__(self, name, parent=None):
        self._name = name
        super(TextWidget, self).__init__(parent=parent)

        self._use_button = False
        self._suppress_button_command = False

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignTop)
        return main_layout

    def get_text_widget(self):
        return QLineEdit()

    def setup_text_widget(self):
        self.text_widget.textChanged.connect(self._on_text_changed)

    def ui(self):
        super(TextWidget, self).ui()

        self.text_widget = self.get_text_widget()
        self.text_label = QLabel(self._name)
        self.text_label.setAlignment(Qt.AlignLeft)
        self.text_label.setMinimumWidth(100)
        self.setup_text_widget()

        self.main_layout.addWidget(self.text_label)
        self.main_layout.addSpacing(5)
        self.main_layout.addWidget(self.text_widget)

        self.insert_button = QPushButton('<')
        self.insert_button.setMaximumWidth(20)
        # self.insert_button.hide()
        self.main_layout.addWidget(self.insert_button)

    def setup_signals(self):
        self.insert_button.clicked.connect(self._on_button_command)

    def get_label_text(self):
        return self.text_label.text()

    def set_label_text(self, text):
        self.text_label.setText(text)

    def get_text(self):
        return self.text_widget.text()

    def set_text(self, text):
        self.text_widget.setText(text)

    def set_placeholder(self, text):
        self.text_widget.setPlaceholderText(text)

    def set_password_mode(self, flag):
        if flag:
            self.text_widget.setEchoMode(QLineEdit.Password)
        else:
            self.text_widget.setEchoMode(QLineEdit.Normal)

    def set_use_button(self, flag):
        if flag:
            self.insert_button.show()
        else:
            self.insert_button.hide()

    def get_button_text(self):
        return self.insert_button.text()

    def set_button_text(self, text):
        self.insert_button.setText(text)

    def set_button_to_first(self):
        self.main_layout.insertWidget(0, self.insert_button)

    def set_supress_button_command(self, flag):
        self._suppress_button_command = flag

    def get_text_as_list(self):
        text = str(self.text_widget.text())
        if text.find('[') > -1:
            try:
                text = eval(text)
                return text
            except Exception:
                pass

        if text:
            return [text]

    def _remove_unicode(self, list_or_tuple):
        new_list = list()
        for sub in list_or_tuple:
            new_list.append(str(sub))

    def _on_button_command(self):
        if self._suppress_button_command:
            return

        if tp.is_maya():
            import maya.cmds as cmds
            selection = cmds.ls(sl=True)
            if len(selection) > 1:
                selection = self._remove_unicode(selection)
                selection = str(selection)
            elif len(selection) == 1:
                selection = str(selection[0])
            else:
                selection = ''

            self.set_text(selection)

    def _on_text_changed(self):
        self.textChanged.emit(self.text_widget.text())


class BoolWidget(base.BaseNumberWidget, object):
    def __init__(self, name, parent=None):
        super(BoolWidget, self).__init__(name, parent)
        self._number_widget.stateChanged.connect(self._on_value_changed)

    def get_number_widget(self):
        return QCheckBox()

    def get_value(self):
        value = self._number_widget.isChecked()
        if value is None:
            value = False

        return value

    def set_value(self, new_value):
        if new_value:
            state = Qt.CheckState.Checked
        else:
            state = Qt.CheckState.Unchecked
        self._number_widget.setCheckState(state)

    def _on_value_changed(self):
        self.valueChanged.emit(self.get_value())


class DirectoryWidget(base.BaseWidget, object):

    directoryChanged = Signal(object)

    def __init__(self, name, parent=None):
        self._name = name
        super(DirectoryWidget, self).__init__(parent=parent)

    def ui(self):
        super(DirectoryWidget, self).ui()

        self.directory_widget = directory.GetDirectoryWidget()
        self.main_layout.addWidget(self.directory_widget)

    def setup_signals(self):
        self.directory_widget.directoryChanged.connect(self.directoryChanged.emit)

    def get_directory(self):
        return self.directory_widget.get_directory()

    def set_directory(self, value):
        self.directory_widget.set_directory(value)

    def get_label_text(self):
        return self._name


class ScriptWidget(TextWidget, object):
    def __init__(self, name, parent=None):
        super(ScriptWidget, self).__init__(name, parent)

    def get_main_layout(self):
        return QVBoxLayout()

    def get_text_widget(self):
        code_text = code.CodeTextEdit()
        code_text.setMaximumHeight(30)
        code_text.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum))
        code_text.mousePressed.connect(self._on_resize_on_press)

        return code_text

    def get_text(self):
        return self.text_widget.toPlainText()

    def set_text(self, text):
        self.text_widget.setPlainText(text)

    def set_option_object(self, option_object):
        self.text_widget.set_option_object(option_object)

    def set_completer(self, completer):
        self.text_widget.set_completer(completer)

    def set_minimum(self):
        self.text_widget.setMaximumHeight(30)

    def _on_resize_on_press(self):
        self.text_widget.setMaximumHeight(500)

    def _on_text_changed(self):
        self.textChanged.emit(self.text_widget.toPlainText())
