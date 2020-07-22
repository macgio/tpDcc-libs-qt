#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains list option implementation
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import label, layouts, buttons, dividers
from tpDcc.libs.qt.widgets.options import option, text


class ListOption(option.Option, object):
    def __init__(self, name, parent=None, main_widget=None):
        super(ListOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'list'

    def get_option_widget(self):
        return GetListWidget(name=self._name)

    def get_value(self):
        list_value = self._option_widget.get_value()

        return list_value

    def set_value(self, value):
        self._option_widget.set_value(value)

    def _setup_option_widget_value_change(self):
        self._option_widget.list_widget.listChanged.connect(self._on_value_changed)


class GetListWidget(base.BaseWidget, object):
    valueChanged = Signal(object)

    def __init__(self, name, parent=None):
        self._name = name
        super(GetListWidget, self).__init__(parnet=parent)

    @property
    def list_widget(self):
        return self._list_widget

    def get_main_layout(self):
        main_layout = layouts.VerticalLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)

        return main_layout

    def ui(self):
        super(GetListWidget, self).ui()

        self._label = label.BaseLabel(self._name)
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._list_widget = self.get_list_widget()

        self.main_layout.addWidget(self._label)
        self.main_layout.addWidget(self._list_widget)

    def get_list_widget(self):
        return ListWidget()

    def get_value(self):
        return self._list_widget.get_list()

    def set_value(self, value_list):
        for value in value_list:
            self._list_widget.add_entry(value)

    def get_label_text(self):
        return str(self._label.text())

    def set_label_text(self, text):
        self._label.setText(text)

    def _on_value_changed(self, list_value):
        self.set_value(list_value)


class ListWidget(base.BaseWidget, object):
    listChanged = Signal(object)

    def __init__(self):
        self._list = list()
        self._garbage_items = list()
        super(ListWidget, self).__init__()

    def get_main_layout(self):
        main_layout = layouts.VerticalLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)

        return main_layout

    def ui(self):
        super(ListWidget, self).ui()

        widget_layout = layouts.VerticalLayout()
        btn_layout = layouts.HorizontalLayout()
        add_btn = buttons.BaseToolButton().image('plus').icon_only()
        add_btn.clicked.connect(self._on_add_default_entry)
        add_btn.setMinimumWidth(25)
        btn_layout.addStretch()
        btn_layout.addWidget(add_btn)
        widget_layout.addWidget(dividers.Divider())
        widget_layout.addLayout(btn_layout)

        self.main_layout.addLayout(widget_layout)

    def get_list(self):
        self._list = list()
        child_count = self.main_layout.count()
        if not child_count:
            return self._list
        for i in range(child_count):
            widget = self.main_layout.itemAt(i).widget()
            if not hasattr(widget, 'main_layout'):
                continue
            value = widget.get_value()
            self._list.append(value)

        self._garbage_items = list()

        return self._list

    def add_entry(self, entry_value):
        entry = self._build_entry(entry_value)
        count = self.main_layout.count()
        self.main_layout.insertWidget(count - 1, entry)

    def _build_entry(self, entry_name=None):
        item_name = entry_name or 'item1'
        index = 1
        while item_name in self.get_list():
            index += 1
            item_name = 'item{}'.format(index)

        entry_widget = self._get_entry_widget(item_name)
        entry_widget.itemRemoved.connect(self._cleanup_garbage)
        entry_widget.valueChanged.connect(self._on_value_changed)

        return entry_widget

    def _get_entry_widget(self, name):
        return ListItemWidget(name)

    def _cleanup_garbage(self, widget):
        value = widget.get_value()
        if value in self._list:
            self._list.remove(value)
        widget.hide()
        self.main_layout.removeWidget(widget)
        widget.deleteLater()
        self.update()
        self.listChanged.emit(self._list)

    def _on_add_default_entry(self):
        entry = self._build_entry()
        count = self.main_layout.count()
        self.main_layout.insertWidget(count - 1, entry)
        self.listChanged.emit(self.get_list())

    def _on_value_changed(self):
        self.listChanged.emit(self.get_list())


class ListItemWidget(base.BaseWidget, object):
    valueChanged = Signal(object)
    itemRemoved = Signal(object)

    def __init__(self, name=None, parent=None):
        self._value = name
        self._garbage = None
        super(ListItemWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout()
        main_layout.setAlignment(Qt.AlignRight)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(ListItemWidget, self).ui()

        self._value_str = text.TextWidget()
        self._value_str.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._value_str.set_use_button(False)
        if self._value is not None:
            self._value_str.set_text(str(self._value))
        self._value_str.set_placeholder('Set a value')

        self._remove_btn = buttons.BaseToolButton().image('delete').icon_only()

        self.main_layout.addWidget(self._value_str)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self._remove_btn)

    def setup_signals(self):
        self._value_str.textChanged.connect(self.valueChanged.emit)
        self._remove_btn.clicked.connect(self._on_remove_item)

    def get_value(self):
        return self._value_str.get_text()

    def _on_remove_item(self):
        self._garbage = True
        self.itemRemoved.emit(self)
