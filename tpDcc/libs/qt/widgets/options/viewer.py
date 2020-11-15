#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that viewer widget for options
"""

from __future__ import print_function, division, absolute_import

import logging

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QSizePolicy, QWidget, QFrame, QScrollArea

from tpDcc.managers import resources
from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import layouts, buttons, dividers
from tpDcc.libs.qt.widgets.options import optionlist

LOGGER = logging.getLogger('tpDcc-core')


class OptionsViewer(base.BaseWidget):

    OPTION_LIST_CLASS = optionlist.OptionList

    editModeChanged = Signal(bool)

    def __init__(self, option_object=None, settings=None, parent=None):

        self._option_object = None
        self._settings = settings
        self._edit_mode = False
        self._current_widgets = list()
        self._widget_to_copy = None

        super(OptionsViewer, self).__init__(parent)

        policy = self.sizePolicy()
        policy.setHorizontalPolicy(policy.Expanding)
        policy.setVerticalPolicy(policy.Expanding)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(2)
        self.setSizePolicy(policy)

        if option_object:
            self.set_option_object(option_object=option_object)

    def ui(self):
        super(OptionsViewer, self).ui()

        edit_mode_icon = resources.icon('edit')
        move_up_icon = resources.icon('sort_up')
        move_down_icon = resources.icon('sort_down')
        remove_icon = resources.icon('delete')

        self._edit_widget = QWidget()
        top_layout = layouts.HorizontalLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        self._edit_widget.setLayout(top_layout)
        self.main_layout.addWidget(self._edit_widget)
        self._edit_mode_btn = buttons.BaseButton(parent=self)
        self._edit_mode_btn.setIcon(edit_mode_icon)
        self._edit_mode_btn.setCheckable(True)
        top_layout.addWidget(self._edit_mode_btn)

        horizontal_separator = QFrame()
        horizontal_separator.setFrameShape(QFrame.VLine)
        horizontal_separator.setFrameShadow(QFrame.Sunken)
        top_layout.addWidget(horizontal_separator)

        self._move_up_btn = buttons.BaseButton(parent=self)
        self.move_down_btn = buttons.BaseButton(parent=self)
        self.remove_btn = buttons.BaseButton(parent=self)
        self._move_up_btn.setIcon(move_up_icon)
        self.move_down_btn.setIcon(move_down_icon)
        self.remove_btn.setIcon(remove_icon)
        self._move_up_btn.setVisible(False)
        self.move_down_btn.setVisible(False)
        self.remove_btn.setVisible(False)
        top_layout.addWidget(self._move_up_btn)
        top_layout.addWidget(self.move_down_btn)
        top_layout.addWidget(self.remove_btn)
        top_layout.addStretch()
        self.main_layout.addWidget(dividers.Divider())

        self._scroll = QScrollArea()
        self._scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._scroll.setFocusPolicy(Qt.NoFocus)
        self._scroll.setWidgetResizable(True)
        self.setFocusPolicy(Qt.NoFocus)
        self._options_list = self.OPTION_LIST_CLASS(parent=self)
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

    def set_option_object(self, option_object, force_update=True):
        """
        Sets option_object linked to this widget
        :param option_object: object
        :param force_update: bool
        """

        self._option_object = option_object
        self._options_list.set_option_object(option_object)
        if option_object and force_update:
            self.update_options()

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

        if not self._option_object:
            self._options_list.clear_widgets()
            LOGGER.warning('Impossible to update options because option object is not defined!')
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
            LOGGER.warning('Impossible to check options because option object is not defined!')
            return

        return self._option_object.has_options()

    def _edit_activate(self, edit_value):
        """
        Internal function that updates widget states when edit button is pressed
        :param edit_value: bool
        """

        self._edit_mode = edit_value
        self.move_down_btn.setVisible(edit_value)
        self._move_up_btn.setVisible(edit_value)
        self.remove_btn.setVisible(edit_value)
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
