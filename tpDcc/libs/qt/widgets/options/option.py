#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains core classes for options
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

import tpDcc as tp
from tpDcc.libs.python import name as name_utils
from tpDcc.libs.qt.core import base, qtutils
from tpDcc.libs.qt.widgets import layouts


class Option(base.BaseWidget, object):
    updateValues = Signal(object)
    widgetClicked = Signal(object)

    def __init__(self, name, parent=None, main_widget=None, *args, **kwargs):

        self._name = name
        self._option_object = None
        self._parent = main_widget

        super(Option, self).__init__(parent=parent)

        self._original_background_color = self.palette().color(self.backgroundRole())
        self._option_type = self.get_option_type()
        self._option_widget = self.get_option_widget()
        if self._option_widget:
            self.main_layout.addWidget(self._option_widget)
        self._setup_option_widget_value_change()

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_item_menu)
        self._context_menu = None

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout()
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

        # We cannot use this because of import problems
        # if parent.__class__ == optionlist.OptionList:

        if parent.__class__.__name__ == 'OptionList':
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

        move_up_action.triggered.connect(self.move_up)
        move_down_action.triggered.connect(self.move_down)
        rename_action.triggered.connect(self.rename)
        remove_action.triggered.connect(self.remove)

    def _on_item_menu(self, pos):
        if not self._parent or not self._parent.is_edit_mode():
            return

        if not self._context_menu:
            self._create_context_menu()

        self._context_menu.exec_(self.mapToGlobal(pos))

    def _on_value_changed(self):
        self.updateValues.emit(False)
