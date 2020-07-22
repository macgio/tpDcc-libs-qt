#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains dictionary option implementation
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import layouts, label, buttons, dividers
from tpDcc.libs.qt.widgets.options import float, text


class DictOption(float.FloatOption, object):
    def __init__(self, name, parent=None, main_widget=None):
        super(DictOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

    def get_option_type(self):
        return 'dictionary'

    def get_option_widget(self):
        return GetDictWidget(name=self._name)

    def get_label(self):
        return self._option_widget.get_label()

    def get_value(self):
        order = self._option_widget.get_order()
        dictionary = self._option_widget.get_value()

        return [dictionary, order]

    def set_value(self, dictionary_value):
        self._option_widget.set_value(dictionary_value[0])
        self._option_widget.set_order(dictionary_value[1])

    def _setup_option_widget_value_change(self):
        self._option_widget.dictionary_widget.dictChanged.connect(self._on_value_changed)


class GetDictWidget(base.BaseWidget, object):
    valueChanged = Signal(object)

    def __init__(self, name, parent=None):
        self._name = name
        self._order = list()
        super(GetDictWidget, self).__init__(parent=parent)

    @property
    def dictionary_widget(self):
        return self._dict_widget

    def get_main_layout(self):
        main_layout = layouts.VerticalLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)

        return main_layout

    def ui(self):
        super(GetDictWidget, self).ui()

        self._label = label.BaseLabel(self._name)
        self._dict_widget = DictWidget()

        self.main_layout.addWidget(self._label)
        self.main_layout.addWidget(self._dict_widget)

    def get_value(self):
        return self._dict_widget.get_dictionary()

    def set_value(self, dictionary):
        keys = self._order
        if not keys:
            keys = dictionary.keys()
            keys.sort()
        for key in keys:
            self._dict_widget.add_entry(key, dictionary[key])

    def get_order(self):
        self._dict_widget.get_dictionary()
        order = self._dict_widget.order

        return order

    def set_order(self, order):
        self._order = order

    def get_label_text(self):
        return str(self._label.text())

    def set_label_text(self, text):
        self._label.setText(text)

    def _on_value_change(self, dictionary):
        self.set_value(dictionary)


class DictWidget(base.BaseWidget, object):
    dictChanged = Signal(object)

    def __init__(self):
        self._dict = dict()
        self._order = list()
        self._garbage_items = list()
        super(DictWidget, self).__init__()

    @property
    def dictionary(self):
        return self._dict

    @property
    def order(self):
        return self._order

    def get_main_layout(self):
        main_layout = layouts.VerticalLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)

        return main_layout

    def ui(self):
        super(DictWidget, self).ui()

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

    def get_dictionary(self):
        self._order = list()
        self._dict = dict()
        child_count = self.main_layout.count()
        if not child_count:
            return self._dict
        for i in range(child_count):
            widget = self.main_layout.itemAt(i).widget()
            if not hasattr(widget, 'main_layout'):
                continue
            item_count = widget.main_layout.count()
            if item_count < 3:
                continue
            key = widget.get_entry()
            value = widget.get_value()
            self._order.append(key)
            self._dict[key] = value

        self._garbage_items = list()

        return self._dict

    def add_entry(self, entry_string, value=None):
        entry = self._build_entry(entry_string, value)
        count = self.main_layout.count()
        self.main_layout.insertWidget(count - 1, entry)

    def _build_entry(self, entry_name=None, value=None):
        key_name = entry_name or 'key1'
        index = 1
        while key_name in self.get_dictionary().keys():
            index += 1
            key_name = 'key{}'.format(index)

        entry_widget = DictItemWidget(key_name, value)
        entry_widget.itemRemoved.connect(self._cleanup_garbage)
        entry_widget.entryChanged.connect(self._on_entry_changed)
        entry_widget.valueChanged.connect(self._on_value_changed)

        return entry_widget

    def _cleanup_garbage(self, widget):
        key = widget.get_entry()
        if key in self._dict:
            self._dict.pop(key)
        widget.hide()
        self.main_layout.removeWidget(widget)
        widget.deleteLater()
        self.update()
        self.dictChanged.emit(self._dict)

    def _on_add_default_entry(self):
        entry = self._build_entry()
        count = self.main_layout.count()
        self.main_layout.insertWidget(count - 1, entry)
        self.dictChanged.emit(self.get_dictionary())

    def _on_value_changed(self):
        self.dictChanged.emit(self.get_dictionary())

    def _on_entry_changed(self):
        self.dictChanged.emit(self.get_dictionary())


class DictItemWidget(base.BaseWidget, object):

    entryChanged = Signal(object)
    valueChanged = Signal(object)
    itemRemoved = Signal(object)

    def __init__(self, name=None, value=None, parent=None):
        self._name = name
        self._value = value
        self._garbage = None
        super(DictItemWidget, self).__init__(parent=parent)

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout()
        main_layout.setAlignment(Qt.AlignRight)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        return main_layout

    def ui(self):
        super(DictItemWidget, self).ui()

        current_theme = self.theme()
        separator_color = current_theme.accent_color if current_theme else '#E2AC2C'
        separator = "<span style='color:{}'> &#9656; </span>".format(separator_color)

        self._entry_str = text.TextWidget()
        self._entry_str.set_use_button(False)
        if self._name is not None:
            self._entry_str.set_text(self._name)
        self._entry_str.set_placeholder('Set a key name')

        self._value_str = text.TextWidget()
        self._value_str.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._value_str.set_use_button(False)
        if self._value is not None:
            self._value_str.set_text(str(self._value))
        self._value_str.set_placeholder('Set a value')

        self._remove_btn = buttons.BaseToolButton().image('delete').icon_only()

        self.main_layout.addWidget(self._entry_str)
        self.main_layout.addWidget(label.BaseLabel(separator).secondary())
        self.main_layout.addWidget(self._value_str)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self._remove_btn)

    def setup_signals(self):
        self._entry_str.textChanged.connect(self.entryChanged.emit)
        self._value_str.textChanged.connect(self.valueChanged.emit)
        self._remove_btn.clicked.connect(self._on_remove_item)

    def get_entry(self):
        return self._entry_str.get_text()

    def get_value(self):
        return self._value_str.get_text()

    def _on_remove_item(self):
        self._garbage = True
        self.itemRemoved.emit(self)
