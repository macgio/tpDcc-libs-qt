#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains extended functionality for QMenus
"""

from __future__ import print_function, division, absolute_import

from Qt.QtWidgets import *


class Menu(QMenu, object):
    def __init__(self, *args, **kwargs):
        super(Menu, self).__init__(*args, **kwargs)

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
