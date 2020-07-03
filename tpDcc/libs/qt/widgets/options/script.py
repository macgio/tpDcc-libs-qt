#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains script option implementation
"""

from __future__ import print_function, division, absolute_import

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.qt.widgets import layouts, code
from tpDcc.libs.qt.widgets.options import option, text


class ScriptOption(option.Option, object):
    def __init__(self, name, parent, main_widget):
        super(ScriptOption, self).__init__(name=name, parent=parent, main_widget=main_widget)

        self.main_layout.setContentsMargins(0, 2, 0, 2)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.main_layout.setAlignment(Qt.AlignCenter | Qt.AlignTop)

    def get_option_type(self):
        return 'script'

    def _setup_option_widget_value_change(self):
        self._option_widget.textChanged.connect(self._on_value_changed)

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


class ScriptWidget(text.TextWidget, object):
    def __init__(self, name, parent=None):
        super(ScriptWidget, self).__init__(name, parent)

    def get_main_layout(self):
        return layouts.VerticalLayout()

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
