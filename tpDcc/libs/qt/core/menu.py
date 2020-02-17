#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains extended functionality for QMenus
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.qt.core import qtutils


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
