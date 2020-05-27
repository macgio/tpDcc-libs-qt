#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains extended functionality for QMenus
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.python import python
from tpDcc.libs.qt.core import mixin, qtutils, formatters


@mixin.theme_mixin
# @mixin.property_mixin
class BaseMenu(QMenu, object):

    valueChanged = Signal(list)

    def __init__(self, exclusive=True, cascader=False, title='', parent=None):
        super(BaseMenu, self).__init__(title=title, parent=parent)

        self._load_data_fn = None

        self._action_group = QActionGroup(self)
        self._action_group.setExclusive(exclusive)
        self._action_group.triggered.connect(self._on_action_triggered)

        self.setProperty('cascader', cascader)
        self.setCursor(Qt.PointingHandCursor)

        self.set_value('')
        self.set_data([])
        self.set_separator('/')

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_separator(self, separator_character):
        """
        Sets menu separator character
        :param separator_character: str
        """
        self.setProperty('separator', separator_character)

    def set_value(self, data):
        """
        Sets menu value
        :param data:  str, int or float
        """

        assert isinstance(data, (list, str, unicode, int, float))
        if self.property('cascader') and isinstance(data, (str, unicode)):
            data = data.split(self.property('separator'))
        self.setProperty('value', data)

    def set_data(self, option_list):
        """
        Sets menu data
        :param option_list: list
        """

        assert isinstance(option_list, list)
        if option_list:
            if all(isinstance(i, (str, unicode)) for i in option_list):
                option_list = python.from_list_to_nested_dict(option_list, separator=self.property('separator'))
            if all(isinstance(i, (int, float)) for i in option_list):
                option_list = [{'value': i, 'label': str(i)} for i in option_list]
        self.setProperty('data', option_list)

    def set_loader(self, fn):
        """
        Sets menu loader
        :param fn: function
        """

        self._load_data_fn = fn

    def set_load_callback(self, fn):
        """
        Sets menu load callback
        :param fn: function
        """

        assert callable(fn)
        self._load_data_fn = fn
        self.aboutToShow.connect(self._on_fetch_data)

    # =================================================================================================================
    # PROPERTY MIXIN SETTERS
    # =================================================================================================================

    def _set_value(self, value):
        data_list = value if isinstance(value, list) else [value]
        flag = False
        for act in self._action_group.actions():
            checked = act.property('value') in data_list
            if act.isChecked() != checked:
                act.setChecked(checked)
                flag = True

        if flag:
            self.valueChanged.emit(value)

    def _set_data(self, option_list):
        self.clear()
        for act in self._action_group.actions():
            self._action_group.removeAction(act)
        for data_dict in option_list:
            self._add_menu(self, data_dict)

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _add_menu(self, parent_menu, data_dict):
        if 'children' in data_dict:
            menu = BaseMenu(title=data_dict.get('label'), parent=self)
            menu.setProperty('value', data_dict.get('value'))
            parent_menu.addMenu(menu)
            if parent_menu is not self:
                menu.setProperty('parent_menu', parent_menu)
            for i in data_dict.get('children'):
                self._add_menu(menu, i)
        else:
            action = self._action_group.addAction(formatters.display_formatter(data_dict.get('label')))
            action.setProperty('value', data_dict.get('value'))
            action.setCheckable(True)
            action.setProperty('parent_menu', parent_menu)
            parent_menu.addAction(action)

    def _get_parent(self, result, obj):
        if obj.property('parent_menu'):
            parent_menu = obj.property('parent_menu')
            result.insert(0, parent_menu.title())
            self._get_parent(result, parent_menu)

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_action_triggered(self, action):
        current_data = action.property('value')
        if self.property('cascader'):
            selected_data = [current_data]
            self._get_parent(selected_data, action)
        else:
            if self._action_group.isExclusive():
                selected_data = current_data
            else:
                selected_data = [act.property('value') for act in self._action_group.actions() if act.isChecked()]
        self.set_value(selected_data)
        self.valueChanged.emit(selected_data)

    def _on_fetch_data(self):
        data_list = self._load_data_fn()
        self.set_data(data_list)


class Menu(QMenu, object):

    mouseButtonClicked = Signal(object, object)     # mouseButton, QAction

    def __init__(self, *args, **kwargs):
        super(Menu, self).__init__(*args, **kwargs)

    def mouseReleaseEvent(self, event):
        """
        Extends mouseReleaseEvent QMenu function
        :param event: QMouseEvent
        """

        self.mouseButtonClicked.emit(event.button(), self.actionAt(event.pos()))

        return super(Menu, self).mouseReleaseEvent(event)

    def insertAction(self, before, *args):
        """
        Extends insertAction QMenu function
        Add supports for finding the before action by the given string
        :param before: str or QAction
        :param args: list
        :return: QAction
        """

        if isinstance(before, (unicode, str)):
            before = self.find_action(before)

        return super(Menu, self).insertAction(before, *args)

    def insertMenu(self, before, menu):
        """
        Extends insertMenu QMenu function
        Add supports for finding the before action by the given string
        :param before: str or QAction
        :param menu: QMenu
        :return: QAction
        """

        if isinstance(before, (unicode, str)):
            before = self.find_action(before)

        return super(Menu, self).insertMenu(before, menu)

    def insertSeparator(self, before):
        """
        Extends insertSeparator QMenu function
        :param before: str or QAction
        :return: QAction
        """

        if isinstance(before, (unicode, str)):
            before = self.find_action(before)

        return super(Menu, self).insertSeparator(before)

    def find_action(self, text):
        """
        Returns the action that contains the given text
        :param text: str
        :return: QAction
        """

        for child in self.children():
            action = None
            if isinstance(child, QMenu):
                action = child.menuAction()
            elif isinstance(child, QAction):
                action = child
            if action and action.text().lower() == text.lower():
                return action


class SearchableTaggedAction(QAction, object):
    def __init__(self, label, icon=None, parent=None):
        super(SearchableTaggedAction, self).__init__(label, parent)

        self._tags = set()

        if icon:
            self.setIcon(icon)

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, new_tags):
        self._tags = new_tags

    def has_tag(self, tag):
        """
        Searches this instance tags. Returns True if the tag is valid or False otherwise
        :param str tag: partial or full tag to search for
        :return: bool
        """

        for t in self._tags:
            if tag in t:
                return True

        return False

    def has_any_tag(self, tags):
        """
        Returns True if current action has some of the given tags or False otherwise
        :param tags: list(str)
        :return: bool
        """

        for t in tags:
            for i in self._tags:
                if t in i:
                    return True

        return False


class SearchableMenu(Menu, object):
    """
    Extends standard QMenu to make it searchable. First action is a QLineEdit used to recursively search on all actions
    """

    def __init__(self, **kwargs):
        super(SearchableMenu, self).__init__(**kwargs)

        self._search_action = None
        self._search_edit = None

        self.setObjectName(kwargs.get('objectName'))
        self.setTitle(kwargs.get('title'))
        self._init_search_edit()

    def clear(self):
        """
        Extends QMenu clear function
        """

        super(SearchableMenu, self).clear()

        self._init_search_edit()

    def set_search_visible(self, flag):
        """
        Sets the visibility of the search edit
        :param flag: bool
        """

        self._search_action.setVisible(flag)

    def search_visible(self):
        """
        Returns whether or not search edit is visible
        :return: bool
        """

        return self._search_action.isVisible()

    def update_search(self, search_string=None):
        """
        Search all actions for a string tag
        :param str search_string: tag names separated by spaces (for example, "elem1 elem2"
        :return: str
        """

        def _recursive_search(menu, search_str):
            for action in menu.actions():
                sub_menu = action.menu()
                if sub_menu:
                    _recursive_search(sub_menu, search_str)
                    continue
                elif action.isSeparator():
                    continue
                elif isinstance(action, SearchableTaggedAction) and not action.has_tag(search_str):
                    action.setVisible(False)

            menu_vis = any(action.isVisible() for action in menu.actions())
            menu.menuAction().setVisible(menu_vis)

        def _recursive_search_by_tags(menu, tags):
            for action in menu.actions():
                sub_menu = action.menu()
                if sub_menu:
                    _recursive_search_by_tags(sub_menu, tags)
                    continue
                elif action.isSeparator():
                    continue
                elif isinstance(action, SearchableTaggedAction):
                    action.setVisible(action.has_any_tag(tags))

            menu_vis = any(action.isVisible() for action in menu.actions())
            menu.menuAction().setVisible(menu_vis)

        search_str = search_string or ''
        split = search_str.split()
        if not split:
            qtutils.recursively_set_menu_actions_visibility(menu=self, state=True)
            return
        elif len(split) > 1:
            _recursive_search_by_tags(menu=self, tags=split)
            return

        _recursive_search(menu=self, search_str=split[0])

    def _init_search_edit(self):
        """
        Internal function that adds a QLineEdit as the first action in the menu
        """

        self._search_action = QWidgetAction(self)
        self._search_action.setObjectName('SearchAction')
        self._search_edit = QLineEdit(self)
        self._search_edit.setPlaceholderText('Search ...')
        self._search_edit.textChanged.connect(self._on_update_search)
        self._search_action.setDefaultWidget(self._search_edit)
        self.addAction(self._search_action)
        self.addSeparator()

    def _on_update_search(self, search_string):
        """
        Internal callback function that is called when the user interacts with the search line edit
        """

        self.update_search(search_string)
